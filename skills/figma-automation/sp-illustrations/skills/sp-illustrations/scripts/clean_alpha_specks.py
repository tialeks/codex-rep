"""Remove reviewed disconnected weak alpha specks on one rigid assembly.

Use only after native review confirms the islands are export artifacts.
Not for fuzzy textiles, particles, separate objects, or transmitted glass.
Does not alter RGB or the main connected assembly. This is not a QA verdict.
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def run(source_dir, output_dir):
    source_dir, output_dir = Path(source_dir), Path(output_dir)
    if output_dir.exists():
        raise ValueError('Preserve previous attempts; output directory must be new')
    source = Image.open(source_dir / 'alpha.png').convert('RGBA')
    pixels = np.array(source)
    alpha = pixels[:, :, 3]
    count, labels, stats, _ = cv2.connectedComponentsWithStats((alpha > 0).astype('uint8'), 8)
    if count <= 1:
        raise ValueError('Empty foreground')
    main_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    removed = []
    for label in range(1, count):
        if label == main_label:
            continue
        region = labels == label
        area, peak = int(stats[label, cv2.CC_STAT_AREA]), int(alpha[region].max())
        if area > 64 or peak > 127:
            raise ValueError('Detached strong/large content requires a separate review; no automatic cleanup')
        removed.append({'box_xywh': stats[label, :4].tolist(), 'area': area, 'peak_alpha': peak})
    clean = pixels.copy()
    clean[:, :, 3][labels != main_label] = 0
    assert np.array_equal(clean[:, :, :3], pixels[:, :, :3])
    assert np.array_equal(clean[labels == main_label], pixels[labels == main_label])
    result = Image.fromarray(clean)
    output_dir.mkdir(parents=True)
    result.save(output_dir / 'alpha.png', icc_profile=source.info.get('icc_profile'))
    for name, color in [('main', '#535353'), ('white', '#ffffff'), ('black', '#000000')]:
        Image.alpha_composite(Image.new('RGBA', result.size, color), result).convert('RGB').save(output_dir / f'{name}.png', icc_profile=source.info.get('icc_profile'))
    report = {'source_export': str(source_dir.resolve()), 'removed': removed,
              'rgb_exact': True, 'main_component_rgba_exact': True,
              'visual_gate': 'UNREVIEWED', 'scope': 'Reviewed single rigid connected assembly only; no geometric/material acceptance implied'}
    (output_dir / 'cleanup-checks.json').write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('reviewed_export_directory')
    p.add_argument('new_output_directory')
    args = p.parse_args()
    run(args.reviewed_export_directory, args.new_output_directory)
