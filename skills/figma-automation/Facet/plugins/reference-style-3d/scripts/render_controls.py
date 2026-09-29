#!/usr/bin/env python3
"""Prepare chat controls with durable palettes, presets and material previews."""
import argparse
import base64
import copy
import hashlib
import io
import gzip
import shutil
import json
from pathlib import Path
import re
import subprocess
import sys
from reference_guidance import image_binding


def bootstrap(html, ident, payload):
    encoded = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c')
    pattern = r'(<script\s+id="' + re.escape(ident) + r'"\s+type="application/json">).*?(</script>)'
    html, count = re.subn(pattern, lambda m: m[1] + encoded + m[2], html, flags=re.S)
    if count != 1:
        raise ValueError('Expected exactly one bootstrap slot: ' + ident)
    return html


def reference_payload(path, display_name=None):
    if path is None:
        if display_name is not None:
            raise ValueError('--reference-name requires --reference')
        return None
    if not Path(path).is_absolute():
        raise ValueError('--reference must be an absolute local image path')
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError('Reference image does not exist: ' + str(path))
    binding = dict(path=str(path), name=display_name if display_name is not None else path.name,
                   sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    image_binding({'reference': {'image': binding}})
    from PIL import Image, ImageOps
    with Image.open(path) as source:
        preview = ImageOps.exif_transpose(source).convert('RGBA')
        preview.thumbnail((256, 256), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        preview.save(buffer, format='PNG', optimize=True)
    if hashlib.sha256(path.read_bytes()).hexdigest() != binding['sha256']:
        raise ValueError('Reference image changed while rendering controls')
    return dict(binding, thumbnail='data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii'))


def initial_settings(path, image):
    if path is None:
        return None
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError('--settings must contain an object')
    settings = payload.get('settings', payload)
    if not isinstance(settings, dict) or settings.get('settingsVersion') != 3:
        raise ValueError('--settings requires a v3 settings snapshot or request with settings')
    settings = copy.deepcopy(settings)
    reference = settings.get('reference')
    if isinstance(reference, dict):
        # Reopening a saved form never implicitly selects an old attachment.
        reference.pop('image', None)
        if image:
            reference['image'] = {key: image[key] for key in ('path', 'name', 'sha256')}
    return settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--selection-key', help='Task-scoped selection identifier')
    parser.add_argument('--browser', action='store_true', help='High-quality local browser form with lazy image assets')
    parser.add_argument('--reference', help='Exact user attachment, absolute local image path')
    parser.add_argument('--reference-name', help='Optional display name for the explicitly selected image')
    parser.add_argument('--view', choices=['presets', 'settings'], help='Open a specific panel tab')
    parser.add_argument('--settings', help='v3 settings snapshot or generation request JSON to restore')
    parser.add_argument('--preset-page', type=int, default=1, help='One-based preset page')
    parser.add_argument('--preset-filters', help='JSON file of preset filters')
    args = parser.parse_args()
    plugin = Path(__file__).resolve().parents[1]
    template = plugin / 'ui' / 'controls.html'
    output = Path(args.output).expanduser().resolve()
    if output == plugin or plugin in output.parents:
        parser.error('Choose a thread-owned output outside the plugin; do not overwrite the template or add generated files to the plugin.')
    result = subprocess.run([sys.executable, str(plugin/'scripts'/'palettes.py'), 'list'], capture_output=True, text=True)
    if result.returncode:
        print(result.stdout or result.stderr, file=sys.stderr)
        return 1
    data = json.loads(result.stdout)
    if data.get('ok') is not True:
        print('Palette library could not be confirmed.', file=sys.stderr)
        return 1
    payload = json.dumps({'version': 1, 'loaded': True, 'palettes': data['palettes']}, ensure_ascii=False).replace('<', '\\u003c')
    html = template.read_text()
    try:
        reference = reference_payload(args.reference, args.reference_name)
        settings = initial_settings(args.settings, reference)
        html = bootstrap(html, 'r-reference-library', {'image': reference})
        html = bootstrap(html, 'r-initial-settings', {'settings': settings, 'view': args.view, 'surface':'browser' if args.browser else 'inline', 'selectionKey':args.selection_key})
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    pattern = r'(<script\s+id="r-plugin-palettes"\s+type="application/json">).*?(</script>)'
    html, count = re.subn(pattern, lambda m: m[1] + payload + m[2], html, flags=re.S)
    if count != 1:
        print('Expected exactly one palette bootstrap slot.', file=sys.stderr)
        return 1
    effects = json.loads((plugin/'skills/reference-style-3d/references/effects.json').read_text())
    catalog_pattern = r'(<script\s+id="r-catalog"\s+type="application/json">)(.*?)(</script>)'
    def inject_catalog(match):
        catalog = json.loads(match[2])
        catalog['effects'] = effects
        material_presets = plugin/'skills/reference-style-3d/references/material-presets.json'
        if material_presets.is_file():
            catalog['materialPresets'] = json.loads(material_presets.read_text())
        catalog['referenceFacets'] = json.loads((plugin/'skills/reference-style-3d/references/reference-facets.json').read_text())
        catalog['graphics'] = json.loads((plugin/'skills/reference-style-3d/references/graphics.json').read_text())
        data = json.dumps(catalog, ensure_ascii=False).replace('<', '\\u003c')
        return match[1] + data + match[3]
    html, count = re.subn(catalog_pattern, inject_catalog, html, flags=re.S)
    if count != 1:
        print('Expected exactly one effect catalog slot.', file=sys.stderr)
        return 1
    try:
        from PIL import Image
    except ImportError:
        print('Controls require Pillow in the Python runtime.', file=sys.stderr)
        return 1
    from material_library import selection
    materials_root = plugin / 'assets' / 'materials'
    material_catalog = json.loads((materials_root / 'catalog.json').read_text())
    materials = []
    cards = selection(plugin, [c['id'] for c in material_catalog['cards'][:12]])
    for start in range(12, len(material_catalog['cards']), 12):
        cards.extend(selection(plugin, [c['id'] for c in material_catalog['cards'][start:start+12]]))
    for card in cards:
        source = (materials_root / card['path']).resolve()
        if materials_root.resolve() not in source.parents:
            raise ValueError('Material image path escapes catalog directory')
        with Image.open(source) as image:
            image = image.convert('RGB')
            image.thumbnail((160, 160), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=78, optimize=True)
        materials.append({'id': card['id'], 'label': card['label'], 'family': card['family'],
                          'thumbnail': 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')})
    material_payload = json.dumps({'version': 1, 'materials': materials}, ensure_ascii=False).replace('<', '\\u003c')
    material_pattern = r'(<script\s+id="r-material-library"\s+type="application/json">).*?(</script>)'
    html, count = re.subn(material_pattern, lambda m: m[1] + material_payload + m[2], html, flags=re.S)
    if count != 1:
        print('Expected exactly one material bootstrap slot.', file=sys.stderr)
        return 1
    try:
        from presets import public_library, inline_library, complete_inline_library, ensure_bundled_library
        ensure_bundled_library()
        preset_filters = json.loads(Path(args.preset_filters).read_text()) if args.preset_filters else None
        # Complete catalog enables immediate local navigation.
        # The template, material cards, settings and reference thumbnail share
        # the same hard inline limit with all preset cards.
        remaining = 990_000 - len(html.encode('utf-8'))
        if args.browser:
            preset_payload = public_library(page_size=10000)
            preset_payload.update(navigation='local',page=1,pageSize=12,previewSize=1024)
            asset_dir=output.parent/'preset-previews'
            asset_dir.mkdir(parents=True,exist_ok=True)
            for row in preset_payload['presets']:
                source=Path(row['thumbnail'])
                name=hashlib.sha256(source.read_bytes()).hexdigest()+'.webp'
                target=asset_dir/name
                if not target.exists(): shutil.copyfile(source,target)
                row['thumbnail']='./preset-previews/'+name
        else:
            preset_payload = complete_inline_library(remaining)
        packed=base64.b64encode(gzip.compress(json.dumps(preset_payload,ensure_ascii=False,separators=(',',':')).encode())).decode()
        html = bootstrap(html, 'r-preset-library', {'gzip':packed})
    except (ValueError, OSError, KeyError, TypeError) as error:
        print('Preset library could not be confirmed: ' + str(error), file=sys.stderr)
        return 1
    if not args.browser and len(html.encode('utf-8')) >= 1_000_000:
        print('Controls exceed the 1 MB inline limit.', file=sys.stderr)
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html)
    print(json.dumps({'ok': True, 'output': str(output), 'paletteCount': len(data['palettes']), 'presetCount': len(preset_payload['presets']), 'presetTotal': preset_payload['total'], 'presetPage': preset_payload['page'], 'presetPageSize': preset_payload['pageSize'], 'presetCatalogTotal': preset_payload['catalogTotal'], 'materialCount': len(materials), 'bytes': len(html.encode('utf-8'))}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
