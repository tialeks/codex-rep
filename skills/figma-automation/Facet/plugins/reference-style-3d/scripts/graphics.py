"""Independent composition/detail axes; v3 snapshots contain no implicit pixel cap."""
import json

def camera_prompts(root):
    catalog = json.loads((root / "skills/reference-style-3d/references/graphics.json").read_text())
    return {entry["id"]: entry["prompt"] for entry in catalog["cameras"]}


def resolve(root, settings):
    catalog = json.loads((root/'skills/reference-style-3d/references/graphics.json').read_text())
    selected = {}
    for key, group in [('graphicType','types'),('detailLevel','details'),('arrangement','arrangements'),('shot','shots')]:
        value = settings.get(key, 'auto') if key == 'shot' else settings.get(key)
        if not isinstance(value, str): raise ValueError('Missing or invalid ' + key)
        selected[key] = next((e for e in catalog[group] if e['id'] == value), None)
        if selected[key] is None: raise ValueError('Invalid ' + key)
    if settings['graphicType'] in ('icon','object') and settings['arrangement'] != 'auto':
        raise ValueError('Single-subject graphics require arrangement=auto')
    return selected
