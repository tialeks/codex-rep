#!/usr/bin/env python3
"""Durable visual preset library. Bundled collection is read-only; writable libraries live outside the plugin."""
import argparse
import base64
import contextlib
import copy
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile

PLUGIN = Path(__file__).resolve().parents[1]
STORY = {'topic', 'subjects', 'avoid', 'reference'}
CONTROLS = {'settingsVersion', 'count', 'camera', 'creativity', 'whiteBase', 'graphicType',
            'detailLevel', 'arrangement', 'background', 'palette', 'colors', 'effects',
            'materials', 'recognizable', 'shot'}


class PresetError(ValueError):
    pass


def data_root():
    root = Path(os.environ.get('REFERENCE_STYLE_3D_DATA_DIR', '~/.local/share/reference-style-3d')).expanduser().resolve()
    if root == PLUGIN or PLUGIN in root.parents:
        raise PresetError('Preset data must be outside the plugin.')
    return root


def settings_only(value):
    if not isinstance(value, dict):
        raise PresetError('Preset settings must be an object.')
    if isinstance(value.get('reference'), dict) and value['reference'].get('facets'):
        raise PresetError('Reference-driven generations cannot become settings-only presets.')
    settings = copy.deepcopy({k: v for k, v in value.items() if k not in STORY})
    if set(settings) - CONTROLS or settings.get('settingsVersion') != 3:
        raise PresetError('Expected current v3 controls only; scene prose is not a preset.')
    from compile_settings import compile_settings
    compile_settings(PLUGIN, dict(settings, topic='Preset validation'))
    return settings


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', value):
        raise PresetError('Invalid preset id.')
    return value


def name(value):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= 100:
        raise PresetError('Preset name must contain 1–100 characters.')
    return value.strip()


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise PresetError(f'Cannot read {path}: {error}') from error


def preview_path(root, row):
    path = (root / row['preview']).resolve()
    if not isinstance(row['preview'], str) or not re.fullmatch(r'previews/[a-f0-9]{64}\.webp', row['preview']) or root.resolve() not in path.parents:
        raise PresetError('Invalid preview path.')
    return path


def read_store(root):
    path = root / 'presets.json'
    if not path.exists():
        return {'schemaVersion': 1, 'presets': [], 'favorites': []}
    data = read_json(path)
    if not isinstance(data, dict) or set(data) != {'schemaVersion', 'presets', 'favorites'} or type(data['schemaVersion']) is not int or data['schemaVersion'] != 1:
        raise PresetError('Invalid preset store schema; file left unchanged.')
    if not isinstance(data['presets'], list) or not isinstance(data['favorites'], list):
        raise PresetError('Invalid preset library lists.')
    ids = set()
    for row in data['presets']:
        if not isinstance(row, dict) or set(row) != {'id', 'name', 'settings', 'preview', 'source', 'imageSha256'}:
            raise PresetError('Invalid stored preset fields.')
        pid = identifier(row['id'])
        if pid in ids or row['name'] != name(row['name']) or row['source'] not in ('collection', 'personal'):
            raise PresetError('Duplicate id or invalid preset metadata.')
        if not isinstance(row['imageSha256'], str) or not re.fullmatch('[a-f0-9]{64}', row['imageSha256']):
            raise PresetError('Invalid source image digest.')
        if row['settings'] != settings_only(row['settings']):
            raise PresetError('Stored preset contains scene content.')
        if not preview_path(root, row).is_file():
            raise PresetError('Preset preview is missing: ' + pid)
        ids.add(pid)
    if any(not isinstance(pid, str) or pid not in ids for pid in data['favorites']) or len(set(data['favorites'])) != len(data['favorites']):
        raise PresetError('Favorites must reference unique existing preset ids.')
    return data


@contextlib.contextmanager
def locked(root):
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'presets.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def atomic_bytes(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.preset-', delete=False) as stream:
            tmp = Path(stream.name)
            stream.write(payload)
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


def bundled_library(bundle=None):
    """Validate the entire shipped collection before allowing any library writes."""
    from PIL import Image
    bundle = Path(bundle) if bundle is not None else PLUGIN / 'assets/presets'
    catalog = read_json(bundle / 'catalog.json')
    if (not isinstance(catalog, dict) or set(catalog) != {'schemaVersion', 'presets'}
            or type(catalog['schemaVersion']) is not int or catalog['schemaVersion'] != 1
            or not isinstance(catalog['presets'], list) or not catalog['presets']):
        raise PresetError('Invalid bundled preset catalog.')
    rows, ids = catalog['presets'], set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'id', 'name', 'settings', 'preview', 'source', 'imageSha256'}:
            raise PresetError('Invalid bundled preset fields.')
        pid = identifier(row['id'])
        if pid in ids or row['name'] != name(row['name']) or row['source'] != 'collection':
            raise PresetError('Duplicate id or invalid bundled preset metadata.')
        ids.add(pid)
        if (not isinstance(row['imageSha256'], str) or not re.fullmatch('[a-f0-9]{64}', row['imageSha256'])
                or row['settings'] != settings_only(row['settings'])):
            raise PresetError('Invalid bundled preset settings or source digest: ' + pid)
        if not isinstance(row['preview'], str):
            raise PresetError('Invalid bundled preview path.')
        path = preview_path(bundle, row)
        if hashlib.sha256(path.read_bytes()).hexdigest() != path.stem:
            raise PresetError('Bundled preview digest mismatch: ' + pid)
        with Image.open(path) as image:
            if image.format != 'WEBP' or max(image.size) < 512 or max(image.size) > 1024:
                raise PresetError('Bundled preview must be a 512–1024px WebP: ' + pid)
            image.verify()
    return rows


def ensure_bundled_library(root=None, bundle=None):
    """Install additive immutable collection entries; never replace user records.

    Called at startup/render, not by queue polling or library reads. Validate all
    sources and conflicts first, copy derivatives, then atomically commit metadata.
    Interrupted copies are harmless and are completed by the next invocation.
    """
    root = Path(root) if root is not None else data_root()
    bundle = Path(bundle) if bundle is not None else PLUGIN / 'assets/presets'
    rows = bundled_library(bundle)
    with locked(root):
        before = read_store(root)
        by_id = {row['id']: row for row in before['presets']}
        additions, copies = [], {}
        for row in rows:
            existing = by_id.get(row['id'])
            if existing is not None:
                # A previously refreshed preview can differ while the original
                # image and settings still identify the exact same preset.
                if {k: v for k, v in existing.items() if k != 'preview'} != {k: v for k, v in row.items() if k != 'preview'}:
                    raise PresetError('Preset ids are immutable; bundled conflict: ' + row['id'])
                continue
            additions.append(row)
            source, target = preview_path(bundle, row), preview_path(root, row)
            payload = source.read_bytes()
            if hashlib.sha256(payload).hexdigest() != source.stem:
                raise PresetError('Bundled preview changed during installation.')
            if target.exists():
                if target.read_bytes() != payload:
                    raise PresetError('Preview digest collision or changed file.')
            else:
                copies[row['preview']] = payload
        if not additions:
            return False, before
        for relative, payload in copies.items():
            atomic_bytes(root / relative, payload)
        after = dict(before, presets=before['presets'] + additions)
        atomic_bytes(root / 'presets.json', json.dumps(after, ensure_ascii=False, indent=2).encode())
        confirmed = read_store(root)
        if confirmed != after:
            raise PresetError('Bundled preset readback mismatch.')
        return True, confirmed


def image_preview(path):
    from PIL import Image, ImageOps
    path = Path(path).expanduser()
    if not path.is_absolute() or not path.is_file():
        raise PresetError('Source PNG must be an existing absolute path.')
    raw = path.read_bytes()
    with Image.open(io.BytesIO(raw)) as source:
        if source.format != 'PNG':
            raise PresetError('Source image must be a PNG.')
        source.load()
        image = ImageOps.exif_transpose(source).convert('RGBA')
        image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        background = Image.new('RGBA', image.size, 'white')
        background.alpha_composite(image)
        buffer = io.BytesIO()
        background.convert('RGB').save(buffer, format='WEBP', quality=88, method=6)
    return hashlib.sha256(raw).hexdigest(), buffer.getvalue()


def import_rows(root, incoming, expected_images=None):
    if not isinstance(incoming, list) or not incoming:
        raise PresetError('Import requires at least one preset.')
    prepared, images, ids = [], {}, set()
    for entry in incoming:
        if not isinstance(entry, dict) or set(entry) != {'id', 'name', 'settings', 'file', 'source'}:
            raise PresetError('Import rows require id, name, settings, file and source.')
        pid = identifier(entry['id'])
        if pid in ids or entry['source'] not in ('collection', 'personal'):
            raise PresetError('Duplicate incoming id or invalid source.')
        ids.add(pid)
        clean = settings_only(entry['settings'])
        image_hash, preview = image_preview(entry['file'])
        if expected_images is not None and expected_images.get(pid) != image_hash:
            raise PresetError('Verified PNG changed before preset import.')
        preview_hash = hashlib.sha256(preview).hexdigest()
        row = dict(id=pid, name=name(entry['name']), settings=clean, source=entry['source'],
                   imageSha256=image_hash, preview=f'previews/{preview_hash}.webp')
        prepared.append(row)
        images[row['preview']] = preview
    with locked(root):
        before = read_store(root)
        after = copy.deepcopy(before)
        by_id = {r['id']: r for r in before['presets']}
        for row in prepared:
            if row['id'] in by_id:
                if {k: v for k, v in row.items() if k != 'preview'} != {k: v for k, v in by_id[row['id']].items() if k != 'preview'}:
                    raise PresetError('Preset ids are immutable; conflicting import: ' + row['id'])
            else:
                after['presets'].append(row)
        changed = after != before
        if changed:
            for relative, payload in images.items():
                dest = root / relative
                if not dest.exists():
                    atomic_bytes(dest, payload)
                elif dest.read_bytes() != payload:
                    raise PresetError('Preview digest collision or changed file.')
            atomic_bytes(root / 'presets.json', json.dumps(after, ensure_ascii=False, indent=2).encode())
        confirmed = read_store(root)
        if confirmed != after:
            raise PresetError('Preset readback mismatch; save not confirmed.')
        return changed, confirmed


def favorite(root, pid, enabled):
    identifier(pid)
    with locked(root):
        before = read_store(root)
        if pid not in {row['id'] for row in before['presets']}:
            raise PresetError('Unknown preset id: ' + pid)
        after = copy.deepcopy(before)
        if enabled and pid not in after['favorites']:
            after['favorites'].append(pid)
        elif not enabled and pid in after['favorites']:
            after['favorites'].remove(pid)
        changed = after != before
        if changed:
            atomic_bytes(root / 'presets.json', json.dumps(after, ensure_ascii=False, indent=2).encode())
        confirmed = read_store(root)
        if confirmed != after:
            raise PresetError('Favorite readback mismatch; save not confirmed.')
        return changed, confirmed


def execution_entry(execution, file, pin, label):
    from prepare_generation import verify
    execution = Path(execution).expanduser().resolve()
    if not re.fullmatch('[a-f0-9]{64}', pin):
        raise PresetError('Trusted manifest pin must be SHA256.')
    args = verify(execution, pin)
    manifest = read_json(execution / 'manifest.json')
    receipt = read_json(execution / 'submission.json')
    observed = receipt.get('observedHandle', {})
    image_hash, _ = image_preview(file)
    if receipt.get('manifestSha256') != pin or receipt.get('arguments') != args or observed.get('type') != 'generated-artifact' or observed.get('sha256') != image_hash:
        raise PresetError('PNG, settings and submission receipt do not share verified evidence.')
    settings = settings_only(manifest['request']['settings'])
    identity = hashlib.sha256((image_hash + json.dumps(settings, sort_keys=True)).encode()).hexdigest()[:24]
    return dict(id='personal-' + identity, name=name(label), settings=settings, file=str(Path(file).resolve()), source='personal'), image_hash


FILTER_DEFAULTS = dict(search='', scope='all', type='', detail='', effect='', creativity='',
                       material='', palette='', camera='', shot='', arrangement='')


def normalize_filters(filters=None):
    if filters is None:
        filters = {}
    if not isinstance(filters, dict) or set(filters) - set(FILTER_DEFAULTS):
        raise PresetError('Unknown preset filters.')
    result = dict(FILTER_DEFAULTS, **filters)
    if any(not isinstance(v, str) for v in result.values()):
        raise PresetError('Preset filters must be strings.')
    result = {k: v.strip() for k, v in result.items()}
    if len(result['search']) > 200:
        raise PresetError('Search must not exceed 200 characters.')
    refs = PLUGIN / 'skills/reference-style-3d/references'
    graphics = read_json(refs / 'graphics.json')
    allowed = {key: {r['id'] for r in graphics[catalog]} for key, catalog in
               [('type','types'), ('detail','details'), ('camera','cameras'),
                ('shot','shots'), ('arrangement','arrangements')]}
    allowed.update(scope={'all','favorites','personal'}, palette={'natural','custom'},
                   creativity={str(i) for i in range(1,6)},
                   effect={'none'} | {r['id'] for r in read_json(refs/'effects.json')},
                   material={'auto'} | {r['id'] for r in read_json(PLUGIN/'assets/materials/catalog.json')['cards']})
    for key, choices in allowed.items():
        if result[key] not in choices and not (key != 'scope' and result[key] == ''):
            raise PresetError('Unsupported preset filter: ' + key)
    return result


def public_library(root=None, page=1, filters=None, page_size=6):
    if type(page) is not int or page < 1 or page_size not in (6,9,10000) or type(page_size) is not int:
        raise PresetError('Preset page must be a positive integer; page size must be 6 or 9.')
    root = root or data_root()
    filters = normalize_filters(filters)
    data = read_store(root)
    refs = PLUGIN / 'skills/reference-style-3d/references'
    effect_labels = {r['id']: r.get('label', r['id']) for r in read_json(refs/'effects.json')}
    material_labels = {r['id']: r.get('label', r['id']) for r in read_json(PLUGIN/'assets/materials/catalog.json')['cards']}
    def matches(row):
        settings = row['settings']
        if filters['scope'] == 'favorites' and row['id'] not in data['favorites']:
            return False
        if filters['scope'] == 'personal' and row['source'] != 'personal':
            return False
        material = settings['materials']
        material_ids = [material.get('base')] + material.get('accents', []) if material['mode'] == 'selected' else []
        searchable = ' '.join([row['name'], row['id']] + [effect_labels.get(e['id'], e['id']) for e in settings['effects']] + [material_labels.get(mid, mid) for mid in material_ids if mid])
        if filters['search'].casefold() not in searchable.casefold():
            return False
        for key, control in [('type','graphicType'), ('detail','detailLevel'), ('creativity','creativity'),
                             ('palette','palette'), ('camera','camera'), ('shot','shot'), ('arrangement','arrangement')]:
            if filters[key] and filters[key] != str(settings.get(control, 'auto' if key == 'shot' else '')):
                return False
        effects = [effect['id'] for effect in settings['effects']]
        if filters['effect'] and not (not effects if filters['effect'] == 'none' else filters['effect'] in effects):
            return False
        materials = settings['materials']
        ids = [materials.get('base')] + materials.get('accents', [])
        if filters['material'] and not (materials['mode'] == 'auto' if filters['material'] == 'auto' else materials['mode'] == 'selected' and filters['material'] in ids):
            return False
        return True
    rows = [row for row in data['presets'] if matches(row)]
    page = min(page, max(1, (len(rows) + page_size - 1) // page_size))
    visible = rows[(page-1)*page_size:page*page_size]
    return {'version': 1, 'loaded': True, 'total': len(rows), 'catalogTotal': len(data['presets']),
            'page': page, 'pageSize': page_size, 'filters': filters,
            'presets': [dict(id=row['id'], name=row['name'], settings=row['settings'], source=row['source'],
                graphicType=row['settings']['graphicType'], detailLevel=row['settings']['detailLevel'],
                effectIds=[effect['id'] for effect in row['settings']['effects']],
                thumbnail=str(preview_path(root, row))) for row in visible], 'favorites': data['favorites']}


def inline_library(library, max_bytes):
    """Embed a stable page without dropping cards or reducing previews below 512px."""
    from PIL import Image
    result = copy.deepcopy(library)
    images = []
    for row in library['presets']:
        with Image.open(row['thumbnail']) as source:
            if max(source.size) < 512:
                raise PresetError('Preset preview is below 512px; refresh previews from original PNGs before rendering.')
            images.append(source.convert('RGB'))
    for size, quality in ((768,75), (640,70), (512,65)):
        for row, original in zip(result['presets'], images):
            preview = original.copy()
            preview.thumbnail((size,size), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            preview.save(buf, format='WEBP', quality=quality, method=4)
            row['thumbnail'] = 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode()
        result['previewSize'] = size
        result['previewQuality'] = quality
        if len(json.dumps(result, ensure_ascii=False).replace('<', '\\u003c').encode()) <= max_bytes:
            return result
    raise PresetError('High-quality preset page exceeds the inline budget. No preview below 512px was generated.')


def complete_inline_library(max_bytes):
    """All cards for instant local browsing; source previews stay full quality."""
    first = public_library(page_size=10000)
    rows = first['presets']
    first.update(presets=rows, navigation='local', page=1, pageSize=16)
    for row in rows:
        for key in ('graphicType','detailLevel','effectIds'): row.pop(key,None)
    import gzip
    from PIL import Image
    images=[]
    for row in rows:
        with Image.open(row['thumbnail']) as source:
            images.append(source.convert('RGB'))
    for size,quality in ((256,55),(224,45),(192,40),(160,35),(144,30),(128,25),(112,25),(96,25),(80,25),(64,25)):
        for row,original in zip(rows,images):
            preview=original.copy(); preview.thumbnail((size,size),Image.Resampling.LANCZOS)
            buf=io.BytesIO(); preview.save(buf,format='WEBP',quality=quality,method=6)
            row['thumbnail']='data:image/webp;base64,'+base64.b64encode(buf.getvalue()).decode()
        first.update(previewSize=size,previewQuality=quality)
        packed=base64.b64encode(gzip.compress(json.dumps(first,ensure_ascii=False,separators=(',',':')).encode())).decode()
        if len(packed)+50<=max_bytes:
            return first
    raise PresetError('Complete catalog exceeds inline budget.')


def refresh_previews(root, incoming):
    """Refresh only image derivatives after checking every original against the immutable store."""
    if not isinstance(incoming, list) or not incoming:
        raise PresetError('Refresh requires at least one preset.')
    prepared = {}
    for entry in incoming:
        if not isinstance(entry, dict) or set(entry) != {'id','name','settings','file','source'}:
            raise PresetError('Refresh rows require id, name, settings, file and source.')
        pid = identifier(entry['id'])
        if pid in prepared:
            raise PresetError('Duplicate refresh id.')
        image_hash, preview = image_preview(entry['file'])
        prepared[pid] = (settings_only(entry['settings']), image_hash, preview)
    with locked(root):
        before = read_store(root)
        after = copy.deepcopy(before)
        by_id = {row['id']: row for row in after['presets']}
        for pid, (settings, digest, preview) in prepared.items():
            if pid not in by_id:
                raise PresetError('Unknown refresh preset: ' + pid)
            row = by_id[pid]
            if row['imageSha256'] != digest or row['settings'] != settings:
                raise PresetError('Refresh PNG or settings do not match stored preset: ' + pid)
            row['preview'] = 'previews/' + hashlib.sha256(preview).hexdigest() + '.webp'
        changed = before != after
        if changed:
            for pid, (_, _, preview) in prepared.items():
                dest = preview_path(root, by_id[pid])
                if dest.exists() and dest.read_bytes() != preview:
                    raise PresetError('Preview digest collision or changed file.')
                if not dest.exists():
                    atomic_bytes(dest, preview)
            atomic_bytes(root/'presets.json', json.dumps(after,ensure_ascii=False,indent=2).encode())
        confirmed = read_store(root)
        if confirmed != after:
            raise PresetError('Preview readback mismatch; refresh not confirmed.')
        return changed, confirmed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    listing = sub.add_parser('list')
    listing.add_argument('--page', type=int, default=1)
    listing.add_argument('--filters', help='JSON file of preset filters')
    fav = sub.add_parser('favorite')
    fav.add_argument('--id', required=True)
    fav.add_argument('--page', type=int, default=1)
    fav.add_argument('--filters', help='JSON file of preset filters')
    toggle = fav.add_mutually_exclusive_group(required=True)
    toggle.add_argument('--on', action='store_true')
    toggle.add_argument('--off', action='store_true')
    imp = sub.add_parser('import-manifest')
    imp.add_argument('--file', required=True)
    refresh = sub.add_parser('refresh-previews')
    refresh.add_argument('--file', required=True)
    own = sub.add_parser('import-execution')
    own.add_argument('--execution', required=True)
    own.add_argument('--file', required=True)
    own.add_argument('--name', required=True)
    own.add_argument('--expected-manifest-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        root = data_root()
        ensure_bundled_library(root)
        filters = normalize_filters(read_json(args.filters) if getattr(args, 'filters', None) else None)
        page = getattr(args, 'page', 1)
        if page < 1:
            raise PresetError('Preset page must be a positive integer.')
        changed = False
        if args.command == 'favorite':
            changed, _ = favorite(root, args.id, args.on)
        elif args.command in ('import-manifest', 'refresh-previews'):
            data = read_json(Path(args.file).expanduser())
            if not isinstance(data, dict) or set(data) != {'schemaVersion', 'presets'} or type(data['schemaVersion']) is not int or data['schemaVersion'] != 1:
                raise PresetError('Expected schemaVersion 1 and presets in import manifest.')
            if not isinstance(data['presets'], list):
                raise PresetError('Manifest presets must be a list.')
            if args.command == 'import-manifest' and any(not isinstance(row, dict) or row.get('source') != 'collection' for row in data['presets']):
                raise PresetError('Seed manifest imports collection presets; personal presets require verified execution.')
            changed, _ = (refresh_previews if args.command == 'refresh-previews' else import_rows)(root, data['presets'])
        elif args.command == 'import-execution':
            entry, image_hash = execution_entry(args.execution, args.file, args.expected_manifest_sha256, args.name)
            changed, _ = import_rows(root, [entry], expected_images={entry['id']: image_hash})
        print(json.dumps({'ok': True, 'command': args.command, 'changed': changed,
                          'store': str(root / 'presets.json'), **public_library(root, page=page, filters=filters)}, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
