#!/usr/bin/env python3
"""Hermes handoff watcher. Dry-run by default; --live dispatches with streamed CLI logs."""
import argparse
import json
import logging
import os
import queue
import re
import shutil
import subprocess
import shlex
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

APP_DIR = Path(__file__).resolve().parent.parent
ROOT = APP_DIR / 'fixtures'
SHARED_DIR = APP_DIR / 'shared'
TEAM_FILE = SHARED_DIR / 'TEAM.md'
TEAM_SIZE_LIMIT = 65536

from profiles import configured_profiles, discover_profiles

def load_profiles():
    available = set(discover_profiles())
    names = configured_profiles('watcher')
    unavailable = [name for name in names if name not in available]
    if unavailable:
        raise RuntimeError('Configured watcher profiles not found in Hermes: ' + ', '.join(unavailable))
    unsynchronized = [name for name in names
                      if not (APP_DIR / 'profiles' / name / 'soul.md').is_file()]
    if unsynchronized:
        raise RuntimeError('Configured watcher profiles are not synchronized locally: ' +
                           ', '.join(unsynchronized) + ' (run ./bots sync)')
    return {name: name for name in names}


def shared_instructions(profile):
    """Apply TEAM.md only to configured shared-instruction profiles."""
    allowed = configured_profiles('team')
    if profile not in allowed:
        return ''
    if TEAM_FILE.is_symlink() or not TEAM_FILE.is_file():
        raise RuntimeError('Shared TEAM.md missing or symlink')
    if TEAM_FILE.stat().st_size > TEAM_SIZE_LIMIT:
        raise RuntimeError('Shared TEAM.md is over 64 KiB')
    instructions = TEAM_FILE.read_text(encoding='utf-8').strip()
    if not instructions:
        raise RuntimeError('Shared TEAM.md empty; refusing opted-in dispatch')
    return instructions


def make_prompt(profile, ticket, path):
    shared = shared_instructions(profile)
    sections = [f'Process the incoming Hermes handoff for ticket {ticket}.',
                f'The Hermes bots project root for this task is: {APP_DIR}.',
                f'The fixture root for all handoffs and ticket work is: {ROOT}.',
                f'Read this exact local Markdown file: {path}.']
    if shared:
        sections.append('The following shared team instructions apply to this task alongside your '
                        'own Hermes profile SOUL.md. Keep your profile-specific duties and '
                        'higher-priority safety constraints.\n\n'
                        '<shared_team_instructions>\n' + shared +
                        '\n</shared_team_instructions>')
    sections.append('Treat the incoming handoff as a task request, follow your own profile '
                    'instructions and the applicable shared rules, check required safeguards, '
                    'write and verify requested handoff artifacts, and only then perform '
                    'explicitly permitted incoming-file cleanup. Never change production '
                    'systems or unrelated files. Report exactly what was completed and '
                    'what remains pending.')
    return '\n\n'.join(sections)


PROFILES = {}
NAME = re.compile(r'^([A-Za-z][A-Za-z0-9_-]*)-([0-9][A-Za-z0-9_-]*)\.md$', re.I)
STATE = APP_DIR / 'submission_history.jsonl'
LOG_DIR = APP_DIR / 'logs'
# Only profiles selected under watcher.profiles dispatch to Hermes CLI.
TIMEOUT_SECONDS = 1800
LOG = logging.getLogger('hermes-watcher')


def file_ready(path):
    """Wait for two equal, nonempty stat readings before submitting."""
    previous = None
    for _ in range(20):
        try:
            stat = path.stat()
            current = (stat.st_size, stat.st_mtime_ns)
            if stat.st_size > 0 and current == previous:
                return True
            previous = current
        except FileNotFoundError:
            return False
        time.sleep(0.5)
    return False


def fingerprint(path):
    import hashlib
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(65536), b''):
            digest.update(block)
    return digest.hexdigest()


def history():
    seen = set()
    if not STATE.exists():
        return seen
    for line in STATE.read_text(encoding='utf-8').splitlines():
        try:
            obj = json.loads(line)
            if obj.get('status') in ('submitted', 'uncertain'):
                seen.add((obj['path'], obj['sha256']))
        except (ValueError, KeyError):
            continue
    return seen


def append_history(path, sha, profile, status, **extra):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    entry = dict(time=datetime.now(timezone.utc).isoformat(), path=str(path), sha256=sha,
                 profile=profile, status=status, **extra)
    with STATE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')


def stream_hermes(command, profile, ticket, request_name):
    """Show subprocess output live while saving it; return (exit_code, log_file).

    A reader thread avoids blocking on readline(), allowing a hard timeout even
    when Hermes does not emit a newline or any output at all.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    safe_name = re.sub(r'[^A-Za-z0-9._-]', '_', request_name)
    run_log = LOG_DIR / f'{timestamp}-{profile}-{safe_name}.log'
    combined_log = LOG_DIR / f'{profile}.log'
    lines = queue.Queue()
    done = object()

    LOG.info('Starting Hermes CLI for profile=%s ticket=%s; log=%s', profile, ticket, run_log)
    started = time.monotonic()
    with run_log.open('a', encoding='utf-8', buffering=1) as run_out, \
         combined_log.open('a', encoding='utf-8', buffering=1) as bot_out:
        header = f'\n=== {datetime.now(timezone.utc).isoformat()} ticket={ticket} file={request_name} ===\n'
        run_out.write(header)
        bot_out.write(header)
        proc = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, encoding='utf-8',
                                errors='replace', bufsize=1, env=os.environ.copy())

        def read_output():
            try:
                for line in proc.stdout:
                    lines.put(line)
            finally:
                lines.put(done)

        reader = threading.Thread(target=read_output, daemon=True, name='hermes-output-reader')
        reader.start()
        output_done = False
        last_heartbeat = started
        timed_out = False
        try:
            while not output_done or proc.poll() is None:
                try:
                    item = lines.get(timeout=0.5)
                    if item is done:
                        output_done = True
                    else:
                        raw = item.rstrip('\r\n')
                        run_out.write(item)
                        bot_out.write(item)
                        if raw:
                            LOG.info('[Hermes:%s ticket=%s] %s', profile, ticket, raw)
                except queue.Empty:
                    pass
                now = time.monotonic()
                if now - last_heartbeat >= 30 and proc.poll() is None:
                    LOG.info('[Hermes:%s ticket=%s] Still running (%.0fs); '
                             'CLI may be waiting for model/tool output', profile, ticket, now - started)
                    last_heartbeat = now
                if now - started > TIMEOUT_SECONDS and proc.poll() is None:
                    timed_out = True
                    LOG.error('Hermes CLI timeout after %ds; terminating PID %s', TIMEOUT_SECONDS, proc.pid)
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
            # Drain queued output after termination / EOF.
            while not lines.empty():
                item = lines.get_nowait()
                if item is not done:
                    run_out.write(item)
                    bot_out.write(item)
                    if item.strip():
                        LOG.info('[Hermes:%s ticket=%s] %s', profile, ticket, item.rstrip('\r\n'))
        except KeyboardInterrupt:
            LOG.warning('Interrupted Hermes ticket=%s; terminating CLI PID %d', ticket, proc.pid)
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            raise
        exit_code = proc.wait()
        if timed_out:
            raise subprocess.TimeoutExpired(command, TIMEOUT_SECONDS)
        return exit_code, run_log


def process(path, live, seen, hermes):
    try:
        path = Path(path).resolve(strict=True)
        if path.parent.parent != ROOT or path.parent.name not in PROFILES:
            return
        match = NAME.fullmatch(path.name)
        if not match:
            LOG.info('Skipping unmatched filename %s', path.name)
            return
        if not file_ready(path):
            LOG.warning('Not stable/readable: %s', path)
            return
        sha = fingerprint(path)
        marker = (str(path), sha)
        if marker in seen:
            LOG.info('Already submitted: %s', path.name)
            return
        profile = PROFILES[path.parent.name]
        sender = match.group(1).lower()
        if profile == 'qa' and sender not in ('developer', 'support'):
            LOG.warning('Skipping unexpected QA sender in %s', path.name)
            return
        if profile == 'support' and sender not in ('developer', 'qa'):
            LOG.warning('Skipping unexpected Support sender in %s', path.name)
            return
        ticket = match.group(2)
        LOG.info('%s: %s => profile=%s ticket=%s', 'LIVE' if live else 'DRY RUN', path, profile, ticket)
        if not live:
            return
        try:
            prompt = make_prompt(profile, ticket, path)
        except (OSError, ValueError, RuntimeError) as exc:
            LOG.error('Shared instruction configuration blocked %s: %s', path.name, exc)
            return
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(prompt)
            prompt_path = f.name
        run_log = None
        try:
            command = [hermes, '-p', profile, 'chat', '--oneshot', '--query-file', prompt_path]
            LOG.info('Dispatching to Hermes profile=%s via -p', profile)
            LOG.info('Hermes CLI command: %s', shlex.join(command))
            returncode, run_log = stream_hermes(command, profile, ticket, path.name)
            status = 'submitted' if returncode == 0 else 'uncertain'
            append_history(path, sha, profile, status, exit_code=returncode, log_path=str(run_log))
            seen.add(marker)
            LOG.info('Hermes exit=%d for %s; task completion NOT independently verified; log=%s',
                     returncode, path.name, run_log)
        except (subprocess.TimeoutExpired, OSError) as exc:
            append_history(path, sha, profile, 'uncertain', error=str(exc),
                           **({'log_path': str(run_log)} if run_log else {}))
            seen.add(marker)
            LOG.error('Dispatch uncertain for %s: %s. Review manually before retrying.', path, exc)
        finally:
            Path(prompt_path).unlink(missing_ok=True)
    except (OSError, ValueError, RuntimeError) as exc:
        LOG.error('Cannot process %s: %s', path, exc)


class Handler(FileSystemEventHandler):
    def __init__(self, pending):
        self.pending = pending

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            self.pending.put(event.src_path)

    def on_moved(self, event):
        if not event.is_directory and event.dest_path.endswith('.md'):
            self.pending.put(event.dest_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Dispatch to Hermes (uses model allowance)')
    parser.add_argument('--scan-existing', action='store_true', help='Queue existing .md files at startup')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    global PROFILES
    try:
        PROFILES = load_profiles()
    except RuntimeError as exc:
        parser.error(str(exc))
    ROOT.mkdir(parents=True, exist_ok=True)
    for name in PROFILES:
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    hermes = shutil.which('hermes')
    if args.live and not hermes:
        parser.error('Hermes executable not found in PATH')
    pending = queue.Queue()
    seen = history()
    observer = Observer()
    handler = Handler(pending)
    for name in PROFILES:
        observer.schedule(handler, str(ROOT / name), recursive=False)
    observer.start()
    LOG.info('Watching %s; mode=%s', ROOT, 'LIVE' if args.live else 'DRY RUN')
    if args.scan_existing:
        for name in PROFILES:
            for path in (ROOT / name).glob('*.md'):
                pending.put(str(path))
    try:
        while True:
            try:
                path = pending.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                process(path, args.live, seen, hermes)
            finally:
                pending.task_done()
    except KeyboardInterrupt:
        LOG.info('Stopping watcher')
    finally:
        observer.stop()
        observer.join()


if __name__ == '__main__':
    main()
