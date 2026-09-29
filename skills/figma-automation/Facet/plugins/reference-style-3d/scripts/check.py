#!/usr/bin/env python3
"""Run development checks once. Never part of the image generation path."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    if not shutil.which('node'):
        print('Node.js is required for UI development checks.', file=sys.stderr)
        return 1
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHON=sys.executable)
    commands = [
        [sys.executable, '-m', 'unittest', 'discover', '-s', 'scripts', '-p', 'test_*.py'],
        ['node', 'scripts/test_material_controls.cjs'],
        ['node', 'scripts/test_controls_focus.cjs'],
        ['node', 'scripts/test_visual_presets.cjs'],
        ['node', 'scripts/test_paged_presets.cjs'],
        ['node', 'scripts/test_browser_bridge.cjs'],
        ['node', 'scripts/test_history_refresh.cjs'],
        [sys.executable, 'scripts/audit_project.py'],
    ]
    for command in commands:
        print('Running: '+' '.join(command), flush=True)
        result = subprocess.run(command, cwd=ROOT, env=env)
        if result.returncode:
            return result.returncode
    return 0

if __name__ == '__main__':
    sys.exit(main())
