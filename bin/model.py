#!/usr/bin/env python3
"""Guarded lifecycle helpers for configured local model services."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

from profiles import load_config


def ollama_manifest_path(model):
    """Return the expected local Ollama manifest without contacting its service."""
    model = model.removeprefix('ollama/').strip()
    name, separator, tag = model.rpartition(':')
    if not separator:
        name, tag = model, 'latest'
    parts = [part for part in name.split('/') if part]
    if not parts:
        return None
    if len(parts) > 1 and ('.' in parts[0] or ':' in parts[0] or parts[0] == 'localhost'):
        registry, parts = parts[0], parts[1:]
    else:
        registry = 'registry.ollama.ai'
    if len(parts) == 1:
        parts.insert(0, 'library')
    if len(parts) < 2 or not tag:
        return None
    model_root = Path(os.environ.get('OLLAMA_MODELS', str(Path.home()/'.ollama/models'))).expanduser()
    return model_root/'manifests'/registry/Path(*parts)/tag


def ollama_generate_url(base_url):
    """Return Ollama's native generate endpoint for an OpenAI-compatible base URL."""
    parsed = urllib.parse.urlsplit(base_url)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        return None
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, '/api/generate', '', ''))


def preload_ollama_model(model, base_url):
    """Load a configured model and keep it resident until the Ollama service stops."""
    endpoint = ollama_generate_url(base_url)
    if endpoint is None:
        print(f'WARNING: Could not preload Ollama model {model}: invalid base URL {base_url!r}.')
        return False
    body = json.dumps({'model': model, 'keep_alive': -1, 'stream': False}).encode('utf-8')
    request = urllib.request.Request(endpoint, data=body, headers={'Content-Type': 'application/json'})
    deadline = time.monotonic() + 30
    while True:
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                response.read()
            print(f'Model loaded: Ollama ({model}); retained until the service stops.')
            return True
        except urllib.error.HTTPError as exc:
            print(f'WARNING: Could not preload Ollama model {model}: HTTP {exc.code}.')
            return False
        except (OSError, urllib.error.URLError) as exc:
            if time.monotonic() >= deadline:
                print(f'WARNING: Could not preload Ollama model {model}: {exc}')
                return False
            time.sleep(0.5)


def available_ollama_models():
    """Yield configured Ollama models whose runtime, formula, and manifest exist."""
    models = load_config().get('models', {})
    checked = set()
    for name, settings in models.items():
        provider = settings['provider']
        if provider != 'ollama' or provider in checked:
            continue
        model = settings['model']
        ollama = shutil.which('ollama')
        brew = shutil.which('brew')
        manifest = ollama_manifest_path(model)
        if not ollama:
            print(f'Model service skipped: {name} uses Ollama, but Ollama is not installed.')
            continue
        if manifest is None or not manifest.is_file():
            print(f'Model service skipped: Ollama model {model} is not installed locally.')
            continue
        if not brew:
            print('Model service skipped: Ollama is available, but no supported service manager was found.')
            continue
        try:
            formula = subprocess.run([brew, 'list', '--formula', 'ollama'], stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL, check=False, timeout=20)
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f'Model service skipped: could not inspect the Homebrew Ollama service: {exc}')
            continue
        if formula.returncode != 0:
            print('Model service skipped: Ollama is not installed as a Homebrew service.')
            continue
        checked.add(provider)
        yield provider, model, settings['base_url'], brew


def manage_available_model_services(action):
    """Start or stop only installed local runtimes with an installed configured model."""
    managed = set()
    for provider, model, base_url, brew in available_ollama_models():
        try:
            service = subprocess.run([brew, 'services', action, 'ollama'], check=False, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f'WARNING: Could not {action} the available Ollama service: {exc}')
            continue
        if service.returncode == 0:
            managed.add(provider)
            state = 'ready' if action == 'start' else 'stopped'
            print(f'Model service {state}: Ollama ({model}).')
            if action == 'start':
                preload_ollama_model(model, base_url)
        else:
            print(f'WARNING: Homebrew could not {action} Ollama (status {service.returncode}); continuing.')
    return managed


def start_available_model_services():
    return manage_available_model_services('start')


def stop_available_model_services():
    return manage_available_model_services('stop')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('start', 'stop'))
    args = parser.parse_args()
    manage_available_model_services(args.action)


if __name__ == '__main__':
    main()
