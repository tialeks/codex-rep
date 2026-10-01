"""Place two independently reviewed RGBA pucks without rerendering or resizing.

This is a layout/export helper, not a generator or proof that inputs passed QA.
Inputs must share reviewed camera, native canvas, alpha silhouette and profile.
No overlap, wrap, recolor, new projection or new-case audit count is implied.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(first, second, dest, first_sha, second_sha, gap=100):
    first, second, dest = map(Path, (first, second, dest))
    if dest.exists():
        raise ValueError('Use a new output directory')
    if gap < 0:
        raise ValueError('Gap must be nonnegative; overlapping pucks need a separate gate')
    if digest(first) != first_sha or digest(second) != second_sha:
        raise ValueError('Input differs from the explicitly reviewed file hash')
    a, b = Image.open(first), Image.open(second)
    if a.mode != 'RGBA' or b.mode != 'RGBA' or a.size != b.size:
        raise ValueError('Reviewed inputs must have matching native RGBA canvases')
    profile = a.info.get('icc_profile')
    if profile != b.info.get('icc_profile'):
        raise ValueError('Color profiles differ; do not silently convert materials')
    aa, bb = np.array(a), np.array(b)
    if not np.array_equal(aa[:, :, 3], bb[:, :, 3]):
        raise ValueError('Alpha silhouettes differ; shared frozen camera not established')
    w, h = a.size
    canvas = Image.new('RGBA', (2 * w + gap, h))
    canvas.paste(a, (0, 0))
    canvas.paste(b, (w + gap, 0))
    pixels = np.array(canvas)
    first_exact = np.array_equal(pixels[:, :w], aa)
    second_exact = np.array_equal(pixels[:, w + gap:], bb)
    if not first_exact or not second_exact:
        raise ValueError('Native RGBA preservation failed')
    dest.mkdir(parents=True)
    canvas.save(dest / 'alpha.png', icc_profile=profile)
    for name, color in [('main', '#535353'), ('white', '#ffffff'), ('black', '#000000')]:
        bg = Image.new('RGBA', canvas.size, color)
        Image.alpha_composite(bg, canvas).convert('RGB').save(dest / f'{name}.png', icc_profile=profile)
    report = {
        'first_source': str(first.resolve()), 'first_sha256': first_sha,
        'second_source': str(second.resolve()), 'second_sha256': second_sha,
        'native_input_size': [w, h], 'output_size': list(canvas.size),
        'positions': [[0, 0], [w + gap, 0]], 'gap': gap,
        'first_rgba_exact': bool(first_exact), 'second_rgba_exact': bool(second_exact),
        'input_alpha_equal': True, 'profile_preserved': True,
        'visual_gate': 'UNREVIEWED: compare both complete pucks, native edges and spacing',
        'count_in_generation_streak': 0,
        'limits': 'Only native non-overlapping pair layout. Reviewed inputs required; no new geometry, projection, recolor or wrap validation.',
    }
    (dest / 'checks.json').write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('first'); p.add_argument('second'); p.add_argument('dest')
    p.add_argument('--first-reviewed-sha', required=True)
    p.add_argument('--second-reviewed-sha', required=True)
    p.add_argument('--gap', type=int, default=100)
    v = p.parse_args()
    run(v.first, v.second, v.dest, v.first_reviewed_sha, v.second_reviewed_sha, v.gap)
