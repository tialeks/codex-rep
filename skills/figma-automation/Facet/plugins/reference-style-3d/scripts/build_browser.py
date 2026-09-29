#!/usr/bin/env python3
"""Build the local studio into an external user-owned directory."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True)
    parser.add_argument('--key', required=True)
    parser.add_argument('--settings')
    args = parser.parse_args()
    from presets import identifier
    identifier(args.key)
    target = Path(args.directory).expanduser().resolve()
    if target == ROOT or ROOT in target.parents:
        parser.error('Studio output belongs outside the plugin')
    target.mkdir(parents=True, exist_ok=True)
    fragment = target / 'controls.html'
    command = [sys.executable, str(ROOT/'scripts/render_controls.py'), '--browser', '--output', str(fragment), '--selection-key', args.key]
    if args.settings: command += ['--settings', args.settings]
    subprocess.run(command, check=True)
    shutil.copyfile(ROOT/'ui/lucide.min.js', target/'lucide.min.js')
    page = '''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark"><title>Facet — студия графики</title>
<style>html{color-scheme:dark;background:#191a1d}body{margin:0}main{max-width:1120px;margin:0 auto;padding:24px 20px 48px} @media(max-width:600px){main{padding:8px 8px 24px}}</style>
<script src="browser-bridge.js"></script><script src="lucide.min.js"></script></head><body><main>'''
    (target/'index.html').write_text(page + fragment.read_text() + '</main></body></html>')
    print(str(target/'index.html'))

if __name__ == '__main__': main()
