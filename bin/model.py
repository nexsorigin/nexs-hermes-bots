#!/usr/bin/env python3
"""Guarded lifecycle helpers for configured local model services."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess

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
        yield provider, model, brew


def manage_available_model_services(action):
    """Start or stop only installed local runtimes with an installed configured model."""
    managed = set()
    for provider, model, brew in available_ollama_models():
        try:
            service = subprocess.run([brew, 'services', action, 'ollama'], check=False, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f'WARNING: Could not {action} the available Ollama service: {exc}')
            continue
        if service.returncode == 0:
            managed.add(provider)
            state = 'ready' if action == 'start' else 'stopped'
            print(f'Model service {state}: Ollama ({model}).')
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
