#!/usr/bin/env python3
"""Load configured profile names and discover profiles from the Hermes CLI."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

VALID = re.compile(r"[A-Za-z][A-Za-z0-9_-]*\Z")
ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / 'config.json'
CONFIG_SIZE_LIMIT = 65536
DEFAULT_PROFILES = ['support', 'developer', 'qa']
DEFAULT_CONFIG = {
    'watcher': {
        'profiles': DEFAULT_PROFILES,
        'dependencies': ['watchdog>=4,<7'],
    },
    'team': {'profiles': DEFAULT_PROFILES},
}


def load_config():
    if CONFIG_FILE.is_symlink() or not CONFIG_FILE.is_file():
        raise RuntimeError('Missing config.json; run sh bots init')
    if CONFIG_FILE.stat().st_size > CONFIG_SIZE_LIMIT:
        raise RuntimeError('Configuration exceeds 64 KiB')
    try:
        config = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f'Invalid config.json: {exc}') from exc
    if not isinstance(config, dict):
        raise RuntimeError('config.json must contain an object')
    for section in ('watcher', 'team'):
        settings = config.get(section)
        if not isinstance(settings, dict):
            raise RuntimeError(f'config.json must contain a {section} object')
        names = settings.get('profiles')
        if not isinstance(names, list):
            raise RuntimeError(f'config.json {section}.profiles must be an array')
        if any(not isinstance(name, str) or not VALID.fullmatch(name) for name in names):
            raise RuntimeError(f'All {section}.profiles entries must be valid profile names')
        if len(names) != len(set(names)):
            raise RuntimeError(f'config.json contains duplicate {section}.profiles entries')
        if 'default' in names:
            raise RuntimeError(f'The default Hermes profile cannot be listed in {section}.profiles')
    dependencies = config['watcher'].get('dependencies')
    if not isinstance(dependencies, list):
        raise RuntimeError('config.json watcher.dependencies must be an array')
    if any(not isinstance(item, str) or not item or item != item.strip() or
           item.startswith('-') or any(char.isspace() for char in item)
           for item in dependencies):
        raise RuntimeError('All watcher.dependencies entries must be nonempty requirement strings without whitespace or leading options')
    if len(dependencies) != len(set(dependencies)):
        raise RuntimeError('config.json contains duplicate watcher.dependencies entries')
    return config


def configured_profiles(section=None):
    config = load_config()
    if section in ('watcher', 'team'):
        return list(config[section]['profiles'])
    if section not in (None, 'all'):
        raise ValueError(f'Unknown configuration section: {section}')
    names = []
    for key in ('watcher', 'team'):
        for name in config[key]['profiles']:
            if name not in names:
                names.append(name)
    return names

def discover_profiles():
    hermes = os.environ.get('HERMES_BIN') or shutil.which('hermes')
    if not hermes:
        raise RuntimeError('Hermes CLI not found in PATH')
    try:
        result = subprocess.run([hermes, 'profile', 'list'], text=True,
                                capture_output=True, check=True, timeout=40)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f'hermes profile list failed: {exc}') from exc
    found = []
    for raw in result.stdout.splitlines():
        line = raw.strip().lstrip('◆*●• ').strip()
        if not line or line.lower().startswith(('profile ', 'name ', 'available ', 'profiles:', 'active ')):
            continue
        # Profile list is typically a table whose first field is the profile name.
        # Ignore decorative table lines and any other invalid profile names.
        first = line.split()[0].strip('│|')
        if not VALID.fullmatch(first):
            continue
        if first not in found:
            found.append(first)
    if not found:
        raise RuntimeError('No Hermes profiles recognized from hermes profile list')
    return found

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configured', choices=('watcher', 'team', 'all'),
                        help='Print profiles selected in config.json instead of querying Hermes')
    parser.add_argument('--watcher-dependencies', action='store_true',
                        help='Print watcher dependency requirements from config.json')
    args = parser.parse_args()
    try:
        if args.configured and args.watcher_dependencies:
            parser.error('--configured and --watcher-dependencies are mutually exclusive')
        if args.watcher_dependencies:
            names = load_config()['watcher']['dependencies']
        else:
            names = configured_profiles(args.configured) if args.configured else discover_profiles()
        print('\n'.join(names))
    except (OSError, RuntimeError, ValueError) as exc:
        sys.exit(f'ERROR: {exc}')
