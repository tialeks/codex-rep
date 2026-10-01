"""Composite an imagegen-edited crop only inside a reviewed material domain.

Use only with authorization for programmatic PNG processing. This is not a
generator, automatic subject segmenter or quality gate. Mask is source-sized L:
0 preserves exact source RGB; 255 takes the registered crop; intermediate values
blend inside the reviewed edit region. Inspect geometry and seams afterward.
Requires Pillow and NumPy. Opaque RGB/RGBA sources only.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source, patch, mask, output, box, offset=(0, 0), ramp_rows=None):
    destination = Path(output)
    report = destination.with_suffix('.checks.json')
    if destination.exists() or report.exists():
        raise ValueError('Preserve prior attempts: output already exists')
    original = Image.open(source)
    if original.mode not in ('RGB', 'RGBA'):
        raise ValueError('Source must be RGB/RGBA')
    if original.mode == 'RGBA' and original.getextrema()[3] != (255, 255):
        raise ValueError('Source already has transparency; preserve separately')
    x0, y0, x1, y1 = box
    width, height = original.size
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise ValueError('Crop box must be inside source')
    matte_image = Image.open(mask)
    if matte_image.mode != 'L' or matte_image.size != original.size:
        raise ValueError('Reviewed domain mask must be source-sized L')
    matte = np.array(matte_image)
    allowed_box = np.zeros(matte.shape, bool)
    allowed_box[y0:y1, x0:x1] = True
    domain = matte > 0
    if not domain.any() or domain[~allowed_box].any():
        raise ValueError('Mask must be nonempty and confined to crop box')
    rendered = Image.open(patch)
    if rendered.mode not in ('RGB', 'RGBA'):
        raise ValueError('Edited crop must be RGB/RGBA')
    if rendered.mode == 'RGBA' and rendered.getextrema()[3] != (255, 255):
        raise ValueError('Edited crop must be opaque')
    crop_size = (x1-x0, y1-y0)
    if rendered.width < crop_size[0] or rendered.height < crop_size[1]:
        raise ValueError('Do not enlarge an undersized generated crop')
    ratio_error = abs((rendered.width/rendered.height)/(crop_size[0]/crop_size[1])-1)
    if ratio_error > 0.02:
        raise ValueError('Crop aspect ratio changed; review framing/registration')
    profile = original.info.get('icc_profile')
    patch_profile = rendered.info.get('icc_profile')
    if patch_profile is not None and patch_profile != profile:
        raise ValueError('Color profiles differ; do not silently relabel crop RGB')
    rgb = np.array(original.convert('RGB'))
    resized = rendered.convert('RGB').resize(crop_size, Image.Resampling.LANCZOS)
    replacement = np.array(resized)
    dx, dy = offset
    rows, columns = np.indices((crop_size[1], crop_size[0]))
    factor = np.ones(rows.shape, float)
    if ramp_rows is not None:
        start, end = ramp_rows
        if not (0 <= start < end < crop_size[1]):
            raise ValueError('Reviewed ramp rows must be within resized crop')
        factor = np.clip((rows-start)/(end-start), 0, 1)
    lookup_x, lookup_y = columns-dx*factor, rows-dy*factor
    valid = (lookup_x >= 0) & (lookup_x < crop_size[0]) & (lookup_y >= 0) & (lookup_y < crop_size[1])
    if np.any((matte[y0:y1, x0:x1] > 0) & ~valid):
        raise ValueError('Reviewed translation moves crop outside edited domain coverage')
    fx = np.clip(lookup_x,0,crop_size[0]-1)
    fy = np.clip(lookup_y,0,crop_size[1]-1)
    ix, iy = np.floor(fx).astype(int), np.floor(fy).astype(int)
    jx, jy = np.minimum(ix+1,crop_size[0]-1), np.minimum(iy+1,crop_size[1]-1)
    wx, wy = (fx-ix)[:,:,None], (fy-iy)[:,:,None]
    replacement = np.rint((replacement[iy,ix]*(1-wx)+replacement[iy,jx]*wx)*(1-wy)+(replacement[jy,ix]*(1-wx)+replacement[jy,jx]*wx)*wy).astype(np.uint8)
    result = rgb.copy()
    weight = matte[y0:y1, x0:x1, None].astype(float)/255
    result[y0:y1, x0:x1] = np.rint(rgb[y0:y1, x0:x1]*(1-weight)+replacement*weight).astype(np.uint8)
    if not np.array_equal(result[~domain], rgb[~domain]):
        raise RuntimeError('Immutable source RGB changed')
    destination.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {'icc_profile': profile} if profile else {}
    Image.fromarray(result).save(destination, **kwargs)
    changed = np.any(result != rgb, axis=2)
    checks = {
        'source_sha256': digest(source), 'patch_sha256': digest(patch),
        'mask_sha256': digest(mask), 'crop_box': list(box),
        'source_size': list(original.size), 'generated_crop_size': list(rendered.size),
        'aspect_ratio_error': ratio_error,
        'reviewed_offset_xy': list(offset),
        'reviewed_offset_ramp_rows': list(ramp_rows) if ramp_rows else None,
        'changed_pixels': int(changed.sum()),
        'outside_domain_changed_pixels': int(changed[~domain].sum()),
        'size_preserved': Image.open(destination).size == original.size,
        'color_profile_preserved': Image.open(destination).info.get('icc_profile') == profile,
        'visual_gate': 'UNREVIEWED: check edited material, geometry, overlaps and seams at 100%',
        'limits': 'A pixel lock outside a manually reviewed domain; not automatic registration or style acceptance.',
    }
    report.write_text(json.dumps(checks, indent=2))
    print(json.dumps(checks, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('patch')
    parser.add_argument('mask')
    parser.add_argument('output')
    parser.add_argument('--box', type=int, nargs=4, required=True, metavar=('X0','Y0','X1','Y1'))
    parser.add_argument('--offset', type=int, nargs=2, default=(0,0), metavar=('DX','DY'), help='Visually reviewed crop translation after resizing; records alignment, not automatic registration')
    parser.add_argument('--ramp-rows', type=int, nargs=2, metavar=('START','END'), help='Keep upper rows fixed; linearly apply reviewed offset between these crop rows, full offset below END. Inspect geometry afterward.')
    args = parser.parse_args()
    run(args.source, args.patch, args.mask, args.output, args.box, args.offset, args.ramp_rows)
