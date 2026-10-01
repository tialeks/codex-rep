"""Compose an already projected RGBA graphic on the reviewed frozen puck.

This preserves the raster camera; it does not project a flat logo, recolor the
body, or support full-face/wrap graphics. A successful command is not QA PASS.
Pillow and NumPy are required. Independent visual review remains mandatory.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


EXPECTED_MASTER = 'f903e6faf401f6b9b9afe68ad5b83dfcf829d27ce7583573bd3c47fba4d39fb5'


def run(master_path, graphic_path, output_dir, width, padding=100):
    master_path, graphic_path, output_dir = map(Path, (master_path, graphic_path, output_dir))
    if output_dir.exists():
        raise ValueError('Use a new output directory; preserve earlier attempts')
    if hashlib.sha256(master_path.read_bytes()).hexdigest() != EXPECTED_MASTER:
        raise ValueError('Unreviewed master: camera and material need a new gate')
    master, graphic = Image.open(master_path), Image.open(graphic_path)
    if master.mode != 'RGBA' or graphic.mode != 'RGBA':
        raise ValueError('Both inputs require explicit RGBA; do not infer brand transparency')
    box = graphic.getchannel('A').getbbox()
    if box is None:
        raise ValueError('Empty graphic')
    graphic = graphic.crop(box)
    if width < 1 or width > graphic.width:
        raise ValueError('Do not upscale native logo pixels; obtain a better original')
    height = max(1, round(graphic.height * width / graphic.width))
    graphic = graphic.resize((width, height), Image.Resampling.LANCZOS)
    x, y = round(445 - width / 2), round(460 - height / 2)
    layer = Image.new('RGBA', master.size)
    layer.paste(graphic, (x, y))
    a = np.array(layer.getchannel('A'))
    yy, xx = np.indices(a.shape)
    inner_face = ((xx - 445) / 395) ** 2 + ((yy - 460) / 414) ** 2 < 1
    if np.any((a > 0) & ~inner_face):
        raise ValueError('Graphic touches unvalidated face/rim region; no wrap support')
    composed = Image.alpha_composite(master, layer)
    src, dst = np.array(master), np.array(composed)
    alpha_exact = np.array_equal(src[:, :, 3], dst[:, :, 3])
    outside_exact = np.array_equal(src[a == 0], dst[a == 0])
    if not alpha_exact or not outside_exact:
        raise ValueError('Frozen body invariant failed')
    if padding < 0:
        raise ValueError('Padding must be nonnegative')
    canvas = Image.new('RGBA', (master.width + padding * 2, master.height + padding * 2))
    canvas.paste(composed, (padding, padding))
    output_dir.mkdir(parents=True)
    canvas.save(output_dir / 'alpha.png', icc_profile=master.info.get('icc_profile'))
    for name, color in [('main', '#535353'), ('white', '#ffffff'), ('black', '#000000')]:
        bg = Image.new('RGBA', canvas.size, color)
        Image.alpha_composite(bg, canvas).convert('RGB').save(output_dir / f'{name}.png', icc_profile=master.info.get('icc_profile'))
    checks = {
        'master_sha256': EXPECTED_MASTER,
        'graphic_source': str(graphic_path.resolve()),
        'graphic_sha256': hashlib.sha256(graphic_path.read_bytes()).hexdigest(),
        'graphic_already_projected': True,
        'body_alpha_exact': bool(alpha_exact),
        'pixels_outside_graphic_exact': bool(outside_exact),
        'face_center_source_pixels': [445, 460],
        'width': width, 'height': height, 'padding': padding,
        'visual_gate': 'UNREVIEWED',
        'limits': 'Original body color only. No flat-logo projection, full-face or wrap. Check native brand fidelity and placement independently.',
    }
    (output_dir / 'checks.json').write_text(json.dumps(checks, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('master')
    parser.add_argument('projected_graphic')
    parser.add_argument('output_dir')
    parser.add_argument('--width', type=int, required=True)
    parser.add_argument('--padding', type=int, default=100)
    args = parser.parse_args()
    run(args.master, args.projected_graphic, args.output_dir, args.width, args.padding)
