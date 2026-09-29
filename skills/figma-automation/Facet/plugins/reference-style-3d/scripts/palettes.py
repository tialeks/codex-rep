#!/usr/bin/env python3
"""Portable personal palettes for reference-style-3d (Python stdlib only)."""
import argparse
import contextlib
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid
from presets import data_root, PresetError


class PaletteError(Exception):
    pass


def normalize_name(value):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= 60:
        raise PaletteError('Name must contain 1–60 characters.')
    return value.strip()


def normalize_colors(values):
    if not isinstance(values, list) or not 1 <= len(values) <= 8:
        raise PaletteError('Provide 1–8 HEX6 colors.')
    if any(not isinstance(v, str) or not re.fullmatch(r'#?[0-9a-fA-F]{6}', v) for v in values):
        raise PaletteError('Each color must be HEX6, with optional #.')
    return ['#' + v.lstrip('#').upper() for v in values]


def validate(data):
    if not isinstance(data, dict) or set(data) != {'schemaVersion', 'palettes'} or type(data['schemaVersion']) is not int or data['schemaVersion'] != 1:
        raise PaletteError('Expected schemaVersion 1 and palettes.')
    rows = data['palettes']
    if not isinstance(rows, list) or len(rows) > 128:
        raise PaletteError('At most 128 palettes are supported.')
    ids, names, result = set(), set(), []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'id', 'name', 'colors'}:
            raise PaletteError('Invalid palette fields.')
        pid = row['id']
        if not isinstance(pid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', pid) or pid in ids:
            raise PaletteError('Invalid or duplicate palette id.')
        name = normalize_name(row['name'])
        if name.casefold() in names:
            raise PaletteError('Duplicate palette name.')
        ids.add(pid)
        names.add(name.casefold())
        result.append({'id': pid, 'name': name, 'colors': normalize_colors(row['colors'])})
    return {'schemaVersion': 1, 'palettes': result}


def read_file(path, missing_ok=False):
    try:
        with path.open(encoding='utf-8') as stream:
            return validate(json.load(stream))
    except FileNotFoundError:
        if missing_ok:
            return {'schemaVersion': 1, 'palettes': []}
        raise PaletteError(f'File does not exist: {path}')
    except (OSError, ValueError) as error:
        raise PaletteError(f'Cannot read palette file; left unchanged: {path}: {error}') from error


def atomic_write(path, data):
    payload = validate(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, prefix='.palettes-', delete=False) as stream:
            tmp = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        tmp = None
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


@contextlib.contextmanager
def locked_store(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with (path.parent / 'palettes.lock').open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def merge(rows, incoming, replace=False):
    result = [dict(row) for row in rows]
    for row in incoming:
        same = next((r for r in result if r['name'].casefold() == row['name'].casefold()), None)
        if same:
            if same['colors'] != row['colors']:
                if not replace:
                    raise PaletteError(f"Palette name already has different colors: {row['name']}; use --replace.")
                same['colors'] = row['colors']
            continue
        if any(r['id'] == row['id'] for r in result):
            raise PaletteError(f"Palette id conflicts with another name: {row['id']}")
        result.append(row)
    return validate({'schemaVersion': 1, 'palettes': result})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('list')
    add = commands.add_parser('add')
    add.add_argument('--name', required=True)
    add.add_argument('--colors', nargs='+', required=True)
    add.add_argument('--replace', action='store_true')
    remove = commands.add_parser('remove')
    remove.add_argument('--id', required=True)
    export = commands.add_parser('export')
    export.add_argument('--output', required=True)
    imp = commands.add_parser('import')
    imp.add_argument('--file', required=True)
    imp.add_argument('--replace', action='store_true')
    args = parser.parse_args(argv)
    try:
        store = data_root() / 'palettes.json'
        incoming = None
        if args.command == 'import':
            incoming = read_file(Path(args.file).expanduser())['palettes']
        elif args.command == 'add':
            incoming = [{'id': uuid.uuid4().hex, 'name': normalize_name(args.name), 'colors': normalize_colors(args.colors)}]
        with (contextlib.nullcontext() if args.command in ('list', 'export') else locked_store(store)):
            before = read_file(store, missing_ok=True)
            after = before
            if incoming is not None:
                after = merge(before['palettes'], incoming, args.replace)
            elif args.command == 'remove':
                after = {'schemaVersion': 1, 'palettes': [row for row in before['palettes'] if row['id'] != args.id]}
            changed = after != before
            if changed:
                atomic_write(store, after)
            confirmed = before if args.command in ('list', 'export') else read_file(store, missing_ok=True)
            if confirmed != after:
                raise PaletteError('Readback mismatch; save not confirmed.')
            output = {'ok': True, 'command': args.command, 'changed': changed, 'store': str(store.resolve()), **confirmed}
            if args.command == 'export':
                dest = Path(args.output).expanduser()
                if dest.resolve() == store.resolve():
                    raise PaletteError('Export destination must differ from the active store.')
                # Never overwrite an existing unreadable or corrupt export either.
                if dest.exists():
                    read_file(dest)
                atomic_write(dest, confirmed)
                if read_file(dest) != confirmed:
                    raise PaletteError('Export readback mismatch.')
                output['output'] = str(dest.resolve())
            print(json.dumps(output, ensure_ascii=False))
        return 0
    except (PaletteError, PresetError, OSError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
