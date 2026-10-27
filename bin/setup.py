#!/usr/bin/env python3
"""Initialize the configured team using real Hermes profiles; never start services."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from profiles import DEFAULT_CONFIG, configured_profiles, discover_profiles
from sync import sync_configured_profiles

ROOT = Path(__file__).resolve().parent.parent

def safe_file(p):
    if p.is_symlink():
        raise RuntimeError(f'Refusing symlink: {p}')

def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    hermes = os.environ.get('HERMES_BIN') or shutil.which('hermes')
    if not hermes:
        parser.error('Hermes command unavailable')
    config = ROOT/'config.json'
    safe_file(config)
    if not config.exists():
        config.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + '\n', encoding='utf-8')
        print(f'Created configuration: {config}')
    else:
        print(f'Preserved configuration: {config}')
    profiles = configured_profiles('all')
    known = set(discover_profiles())
    for name in profiles:
        if name not in known:
            print(f'Creating configured Hermes profile {name}', flush=True)
            # Blank profile: does not inherit another profile's credentials, state, or instructions.
            subprocess.run([hermes, 'profile', 'create', name, '--no-alias'], check=True)
            known = set(discover_profiles())
            if name not in known:
                raise RuntimeError(f'Profile creation not verified: {name}')
    fixture_root = ROOT/'fixtures'
    safe_file(fixture_root)
    fixture_root.mkdir(exist_ok=True)
    for name in profiles:
        target = fixture_root/name
        safe_file(target)
        target.mkdir(exist_ok=True)
        print(f'Fixture: {target}')
    artifact_root = ROOT/'artifacts'
    safe_file(artifact_root)
    artifact_root.mkdir(exist_ok=True)
    print(f'Artifacts: {artifact_root}')
    shared = ROOT/'shared'
    safe_file(shared)
    shared.mkdir(exist_ok=True)
    team = shared/'TEAM.md'
    safe_file(team)
    if not team.exists():
        team.write_text('# the team — Shared Instructions\n\n'
                        'Common safety, project, communication, and operational instructions go here.\n'
                        'Role SOUL.md files contain handoff rules only.\n', encoding='utf-8')
        print(f'Created: {team}')
    else:
        print(f'Preserved: {team}')
    # Synchronize only profiles selected in config.json before importing templates.
    # Initialization synchronizes instructions only. Model routing is handled by
    # the explicit sync command and never installs a provider or downloads a model.
    sync_configured_profiles(sync_models=False)
    # Team templates live in profiles/<profile>/soul.md.
    # Profile paths are resolved from documented Hermes home layout; refuse if absent.
    hermes_home = Path(os.environ.get('HERMES_HOME', str(Path.home()/'.hermes'))).expanduser()
    for name in profiles:
        soul = hermes_home/'profiles'/name/'SOUL.md'
        safe_file(soul)
        if not soul.parent.is_dir():
            raise RuntimeError(f'Could not locate the Hermes profile home: {soul.parent}')
        template = ROOT/'profiles'/name/'soul.md'
        safe_file(template)
        content = template.read_text(encoding='utf-8')
        if soul.exists() and soul.read_text(encoding='utf-8') == content:
            print(f'Unchanged: {soul}')
            continue
        if soul.exists():
            backup = soul.with_name('SOUL.before-team-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.md')
            shutil.copy2(soul, backup)
            print(f'Backed up: {backup}')
        temp = soul.with_name('.SOUL.md.tmp-' + str(os.getpid()))
        temp.write_text(content, encoding='utf-8')
        os.chmod(temp, 0o600)
        temp.replace(soul)
        print(f'Imported handoff-only SOUL.md: {soul}')
    print('Profiles initialized: ' + (', '.join(profiles) if profiles else '(none configured)'))
    print('Other Hermes profiles and their SOUL.md files were not modified.')
    print('No services were started. Run ./bots start separately when ready.')

if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        sys.exit(f'ERROR: {exc}')
