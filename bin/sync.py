#!/usr/bin/env python3
"""Synchronize local editable SOUL files to configured Hermes profiles."""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
from profiles import configured_profiles, discover_profiles, load_config

ROOT = Path(__file__).resolve().parent.parent


def assert_regular_path(path):
    if path.is_symlink():
        raise RuntimeError(f'Refusing symlink: {path}')


def atomic_write(path, content):
    temporary = path.with_name(f'.{path.name}.tmp-{os.getpid()}')
    assert_regular_path(temporary)
    try:
        temporary.write_text(content, encoding='utf-8')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def sync_configured_models(names):
    """Copy declared routing values into Hermes; never install or download models."""
    hermes = os.environ.get('HERMES_BIN') or shutil.which('hermes')
    if not hermes:
        raise RuntimeError('Hermes CLI not found in PATH')
    models = load_config().get('models', {})
    for name in names:
        settings = models.get(name)
        if not settings:
            print(f'Model unchanged (not declared in config.json): {name}')
            continue
        provider = settings['provider']
        if provider == 'ollama':
            # A named providers.ollama route is required for `hermes model` to
            # recognize the stored provider. Bare `ollama` is otherwise only an
            # alias to the generic custom runtime and the picker warns about it.
            provider_values = [
                ('providers.ollama.name', 'Ollama'),
                ('providers.ollama.base_url', settings['base_url']),
                ('providers.ollama.transport', 'openai_chat'),
            ]
            for key, value in provider_values:
                subprocess.run([hermes, '-p', name, 'config', 'set', key, value], check=True)
        values = [
            ('model.provider', provider),
            ('model.default', settings['model']),
        ]
        if settings.get('base_url'):
            values.append(('model.base_url', settings['base_url']))
        for key, value in values:
            subprocess.run([hermes, '-p', name, 'config', 'set', key, value], check=True)
        print(f"Synchronized model routing: {name} -> {provider} / {settings['model']}")


def sync_configured_profiles(sync_models=True):
    directory = ROOT / 'profiles'
    assert_regular_path(directory)
    directory.mkdir(exist_ok=True)
    hermes_home = Path(os.environ.get('HERMES_HOME', str(Path.home() / '.hermes'))).expanduser()
    available = set(discover_profiles())
    names = configured_profiles('all')
    missing = [name for name in names if name not in available]
    if missing:
        raise RuntimeError('Configured profiles not found in Hermes: ' + ', '.join(missing))
    # Validate all destination paths and local content before changing any Hermes SOUL.
    plans = []
    for name in names:
        destination = directory / name
        soul = destination / 'soul.md'
        meta = destination / 'meta.json'
        hermes_dir = hermes_home / 'profiles' / name
        hermes_soul = hermes_dir / 'SOUL.md'
        for path in (destination, soul, meta, hermes_dir, hermes_soul):
            assert_regular_path(path)
        if not hermes_dir.is_dir():
            raise RuntimeError(f'Hermes profile directory missing: {hermes_dir}')
        local_content = soul.read_text(encoding='utf-8') if soul.is_file() else None
        if local_content is not None and not local_content.strip():
            raise RuntimeError(f'Refusing to publish empty local SOUL: {soul}')
        data = {}
        if meta.exists():
            data = json.loads(meta.read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                raise RuntimeError(f'Metadata must be an object: {meta}')
        plans.append((name, destination, soul, meta, hermes_soul, local_content, data))

    for name, destination, soul, meta, hermes_soul, local_content, data in plans:
        destination.mkdir(exist_ok=True)
        if local_content is None:
            if hermes_soul.is_file():
                local_content = hermes_soul.read_text(encoding='utf-8')
                print(f'Imported initial Hermes SOUL to local: {soul}')
            else:
                local_content = f'# {name}\n\n<!-- Add profile handoff instructions here. -->\n'
                print(f'Created local SOUL template: {soul}')
            atomic_write(soul, local_content)
        current = hermes_soul.read_text(encoding='utf-8') if hermes_soul.is_file() else None
        if current != local_content:
            if current is not None:
                backup = hermes_soul.with_name('SOUL.before-sync-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.md')
                assert_regular_path(backup)
                shutil.copy2(hermes_soul, backup)
                print(f'Backed up Hermes SOUL: {backup}')
            atomic_write(hermes_soul, local_content)
            print(f'Published local SOUL to Hermes: {hermes_soul}')
        else:
            print(f'Already synchronized: {name}')
        data.update({'name': name, 'source': 'hermes profile list',
                     'synced_at': datetime.now(timezone.utc).isoformat()})
        atomic_write(meta, json.dumps(data, indent=2, ensure_ascii=False) + '\n')
        print(f'Synced metadata: {meta}')
    if sync_models:
        sync_configured_models(names)
    print(f'Synchronized {len(names)} configured Hermes profile(s).')


if __name__ == '__main__':
    try:
        sync_configured_profiles()
    except (OSError, RuntimeError, ValueError, UnicodeError, subprocess.CalledProcessError) as exc:
        sys.exit(f'ERROR: {exc}')
