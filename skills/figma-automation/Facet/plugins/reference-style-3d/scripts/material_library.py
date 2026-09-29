"""Validated material selection and deterministic, color-preserving PNG contact sheets."""
import hashlib
from io import BytesIO
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def selection(root, ids, *, verify_files=True):
    if not isinstance(ids, list) or len(ids) > 12 or any(not isinstance(i, str) for i in ids):
        raise ValueError('materialIds must be an array of 0–12 strings')
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate materialIds')
    if not ids:
        return []
    base = Path(root) / 'assets/materials'
    catalog = json.loads((base / 'catalog.json').read_text())
    if catalog.get('schemaVersion') != 1:
        raise ValueError('Unsupported material catalog schemaVersion')
    records = {c['id']: c for c in catalog['cards']}
    if any(i not in records for i in ids):
        raise ValueError('Unknown materialIds: ' + ', '.join(i for i in ids if i not in records))
    selected = []
    for i in ids:
        card = records[i]
        path = (base / card['path']).resolve()
        if Path(card['path']).is_absolute() or not path.is_relative_to(base.resolve()):
            raise ValueError('Material card path escapes library')
        if verify_files and (not path.is_file() or digest(path) != card['sha256']):
            raise ValueError('Material card checksum mismatch: ' + i)
        selected.append(card)
    return selected


def build_sheet(root, ids, destination):
    # Pillow is needed only when selected materials are present.
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError("Selected materials require Pillow in the Python runtime") from exc
    cards = selection(root, ids, verify_files=False)
    if not cards:
        raise ValueError('Material sheet requires at least one selected material')
    cols = min(4, len(cards)); rows = (len(cards) + cols - 1) // cols
    canvas = Image.new('RGB', (cols * 512, rows * 512), 'white')
    cells = []
    for index, card in enumerate(cards):
        path = Path(root) / 'assets/materials' / card['path']
        # Decode the very bytes whose SHA is recorded; never reopen a mutable source.
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != card['sha256']:
            raise ValueError('Material card checksum mismatch: ' + card['id'])
        with Image.open(BytesIO(data)) as original:
            if original.format != 'PNG' or original.width != original.height:
                raise ValueError('Material card must be a square PNG: ' + card['id'])
            sample = original.convert('RGBA')
            sample = sample.resize((512, 512), Image.Resampling.LANCZOS)
            x, y = (index % cols) * 512, (index // cols) * 512
            canvas.paste(sample, (x, y), sample)
        cells.append({'id': card['id'], 'sha256': card['sha256'], 'x': x, 'y': y, 'width': 512, 'height': 512})
    canvas.save(destination, format='PNG', optimize=False, compress_level=6)
    return {'schemaVersion': 1, 'orderedIds': list(ids), 'cellSize': 512, 'columns': cols,
            'rows': rows, 'width': canvas.width, 'height': canvas.height, 'cells': cells,
            'sheetSha256': digest(destination)}


def settings_material_ids(root, settings):
    """Resolve submitted roles without modifying the snapshot; legacy stays literal."""
    if 'settingsVersion' not in settings:
        return settings.get('materialIds', [])
    if type(settings['settingsVersion']) is not int or settings['settingsVersion'] not in (1, 2, 3):
        raise ValueError('Unsupported settingsVersion')
    if settings['settingsVersion'] == 1:
        return settings.get('materialIds', [])
    if any(key in settings for key in ('metal', 'pearl', 'materialIds')):
        raise ValueError('settingsVersion 2/3 uses materials roles instead of metal, pearl and materialIds')
    materials = settings.get('materials')
    if not isinstance(materials, dict) or set(materials) != {'mode', 'base', 'accents'}:
        raise ValueError('materials requires exactly mode, base and accents')
    mode, base, accents = materials['mode'], materials['base'], materials['accents']
    if not isinstance(accents, list) or any(not isinstance(i, str) for i in accents):
        raise ValueError('materials.accents must be an array of material IDs')
    if mode == 'auto':
        if base is not None or accents:
            raise ValueError('Automatic materials require base=null and empty accents')
        return []
    if mode != 'selected' or not isinstance(base, str) or not base:
        raise ValueError('Selected materials require a known base material ID')
    ids = [base, *accents]
    selection(root, ids, verify_files=False)
    return ids
