"""Combine up to three scoped original material crops without resampling.

Spec JSON: {"panels": [{"source": "/path/original.png",
"crop_xyxy": [0,0,100,100], "scope": "silver surface only"}]}
This is one bounded CATEGORY image, not STYLE, CONTENT or a new reference.
Review every original and resulting crop before sending it to imagegen.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def run(spec_path, output_path):
    output = Path(output_path)
    report_path = output.with_suffix('.provenance.json')
    if output.exists() or report_path.exists():
        raise ValueError('Preserve previous boards; choose new output paths')
    spec = json.loads(Path(spec_path).read_text())
    panels = spec['panels']
    if not 1 <= len(panels) <= 3:
        raise ValueError('Use only 1–3 essential scoped material panels')
    crops, records, profiles = [], [], []
    for panel in panels:
        source = Path(panel['source'])
        if source.name.startswith('style-') or not panel.get('scope', '').strip():
            raise ValueError('Mandatory STYLE inputs remain separate; a material scope is required')
        original = Image.open(source)
        profiles.append(original.info.get('icc_profile'))
        box = panel['crop_xyxy']
        if len(box) != 4 or not all(isinstance(v, int) for v in box):
            raise ValueError('Crop uses integer original pixel coordinates')
        x0, y0, x1, y1 = box
        if not (0 <= x0 < x1 <= original.width and 0 <= y0 < y1 <= original.height):
            raise ValueError('Crop outside original')
        crop = original.crop(box).convert('RGBA')
        crops.append(crop)
        records.append({'source': str(source.resolve()), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'crop_xyxy': box, 'scope': panel['scope'], 'original_mode': original.mode})
    width = sum(c.width for c in crops) + 20 * (len(crops) - 1)
    height = max(c.height for c in crops)
    if width * height > 4000000:
        raise ValueError('Board too broad; select native fragments, not a catalog')
    if any(p != profiles[0] for p in profiles):
        raise ValueError('Original profiles differ; do not silently harmonize reference colors')
    board = Image.new('RGBA', (width, height), '#535353')
    x = 0
    for crop, record in zip(crops, records):
        board.paste(crop, (x, 0))
        exact = np.array_equal(np.array(board.crop((x, 0, x + crop.width, crop.height))), np.array(crop))
        if not exact:
            raise ValueError('Native crop pixels changed')
        record.update({'position': [x, 0], 'rgba_crop_exact': True})
        x += crop.width + 20
    output.parent.mkdir(parents=True, exist_ok=True)
    board.save(output, icc_profile=profiles[0])
    report_path.write_text(json.dumps({'role': 'CATEGORY essential scoped original material fragments only', 'panels': records, 'resampling': False, 'color_adjustment': False, 'profile_preserved': True, 'limits': 'No new STYLE or geometry authority; preserve all three original STYLEs as separate direct inputs. Originals remain authority; material/color still need a visual gate.'}, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('spec'); p.add_argument('output')
    args = p.parse_args()
    run(args.spec, args.output)
