"""One image, explicit visual facets. Never mutate the submitted snapshot."""
import copy
import json
from pathlib import Path
import re


def image_binding(settings):
    """Validate identity data only; inactive images need not exist on this host."""
    if settings is not None and not isinstance(settings, dict):
        raise ValueError('settings must be an object')
    guide = (settings or {}).get('reference')
    image = guide.get('image') if isinstance(guide, dict) else None
    if image is None:
        return None
    if not isinstance(image, dict) or set(image) != {'path', 'name', 'sha256'}:
        raise ValueError('reference.image requires path, name and sha256 only; no thumbnail')
    if not isinstance(image['path'], str) or not Path(image['path']).is_absolute() or '\x00' in image['path']:
        raise ValueError('reference.image.path must be an absolute local path')
    if not isinstance(image['name'], str) or not image['name'].strip() or len(image['name']) > 255 or any(ord(c) < 32 for c in image['name']):
        raise ValueError('reference.image.name must be a nonempty display name up to 255 characters')
    if not isinstance(image['sha256'], str) or not re.fullmatch(r'[a-fA-F0-9]{64}', image['sha256']):
        raise ValueError('reference.image.sha256 must be 64 hexadecimal characters')
    return image


def catalog(root):
    return json.loads((root / 'skills/reference-style-3d/references/reference-facets.json').read_text())


def selected(root, settings):
    if settings is not None and not isinstance(settings, dict):
        raise ValueError('settings must be an object')
    guide = (settings or {}).get('reference')
    if guide is None:
        return []
    if (settings or {}).get('settingsVersion') != 3:
        raise ValueError('Reference facets require settingsVersion=3')
    if not isinstance(guide, dict) or set(guide) - {'facets', 'note', 'image'}:
        raise ValueError('reference requires facets, optional note and optional image')
    image_binding(settings)
    facets = guide.get('facets')
    allowed = {f['id'] for f in catalog(root)}
    if not isinstance(facets, list) or any(not isinstance(f, str) or f not in allowed for f in facets):
        raise ValueError('Unknown reference facet')
    if len(set(facets)) != len(facets):
        raise ValueError('Duplicate reference facet')
    note = guide.get('note', '')
    if not isinstance(note, str) or len(note) > 500:
        raise ValueError('Reference note must be text up to 500 characters')
    if note.strip() and not facets:
        raise ValueError('Select reference facets before adding a note')
    return facets


def effective_settings(root, settings):
    facets = selected(root, settings)
    if not facets:
        return settings
    s = copy.deepcopy(settings)
    # Inactive form values remain in the immutable request, but cannot control generation.
    if 'structure' in facets:
        s['graphicType'] = 'scene'
    if 'composition' in facets:
        s['arrangement'] = 'auto'
    if 'detail' in facets:
        s['detailLevel'] = 'balanced'
    if 'camera' in facets:
        s['camera'] = 'three-quarter'
        s['shot'] = 'auto'
    if 'palette' in facets:
        s.update(palette='natural', whiteBase=False)
        s.pop('colors', None)
    if 'materials' in facets:
        s['materials'] = dict(mode='auto', base=None, accents=[])
    if 'effects' in facets:
        s['effects'] = []
    if 'composition' in facets:
        if not isinstance(s.get('effects'), list):
            raise ValueError('effects must be an array')
        effects = {e['id']: e for e in json.loads((root / 'skills/reference-style-3d/references/effects.json').read_text())}
        if any(isinstance(e, dict) and e.get('strength', 0) and effects.get(e.get('id'), {}).get('scope') == 'composition' for e in s.get('effects', [])):
            raise ValueError('Composition reference conflicts with a composition effect; choose one source of placement')
    return s


def apply(root, settings, blocks):
    facets = selected(root, settings)
    if not facets:
        return blocks
    chosen = [f for f in catalog(root) if f['id'] in facets]
    prefixes = tuple(p for f in chosen for p in f['prefixes'])
    result = [b for b in blocks if not b.startswith(prefixes)]
    result.append('GUIDANCE REFERENCE: borrow only these facets. Retain the requested topic, subjects, image count, background and unselected settings; do not copy brands, text or cropping. Our shared visual language remains the foundation.')
    if 'ornament' not in facets:
        result.append('Do not transfer printed patterns or decorative motifs from the reference.')
    result.extend(f['id'] + ': ' + f['prompt'] for f in chosen)
    note = settings['reference'].get('note', '').strip()
    if note:
        result.append('User reference note (selected facets only): ' + json.dumps(note, ensure_ascii=False))
    return result
