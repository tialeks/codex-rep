"""Opaque-object cutout with mandatory visual review.

Requires Pillow, NumPy, OpenCV and a same-size reviewed mask proposal.
Does not support transmission of external background through glass.
A successful command is not a quality-gate PASS.
RGB stays byte-identical wherever alpha is 255. Only partial boundary pixels
can be unmatted using local source-background samples; no color propagation.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def nearest_pixels(region, values):
    # Each zero pixel receives its own label. Resolve all labels to source RGB.
    _, labels = cv2.distanceTransformWithLabels((~region).astype(np.uint8),
        cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    lut = np.zeros((labels.max()+1, 3), np.float32)
    lut[labels[region]] = values[region]
    return lut[labels]


def run(source, proposal, dest, semantic_seeds=None, matte_core_radius=1, coverage_anchors=None):
    dest = Path(dest)
    if dest.exists():
        raise ValueError('Preserve previous attempts: destination already exists')
    if matte_core_radius not in (1, 3):
        raise ValueError('Only reviewed matte core radii 1 or 3 are supported')
    original = Image.open(source)
    if original.mode not in ('RGB', 'RGBA'):
        raise ValueError('Only RGB/RGBA input supported')
    if original.mode == 'RGBA' and original.getextrema()[3] != (255, 255):
        raise ValueError('Input already has alpha; preserve separately')
    rgb = np.array(original.convert('RGB'))
    anchors = []
    if coverage_anchors is not None:
        anchors = json.loads(Path(coverage_anchors).read_text())['opaque_anchors']
        if not anchors:
            raise ValueError('Coverage anchors must name reviewed opaque interiors')
        seen = set()
        for anchor in anchors:
            name, point = anchor.get('id'), anchor.get('point_xy')
            if not isinstance(name, str) or not name.strip() or name in seen:
                raise ValueError('Coverage anchor IDs must be unique nonempty strings')
            if not isinstance(point, list) or len(point) != 2 or not all(type(v) is int for v in point):
                raise ValueError('Coverage anchors use integer source pixel coordinates')
            x, y = point
            if not (0 <= x < original.width and 0 <= y < original.height):
                raise ValueError('Coverage anchor outside source')
            seen.add(name)
    vision = np.array(Image.open(proposal).convert('L'))
    if vision.shape != rgb.shape[:2]:
        raise ValueError('Proposal must match source dimensions')
    initial = (vision > 127).astype(np.uint8)
    if not initial.any() or initial.all():
        raise ValueError('Proposal must contain foreground and background')
    forced_fg = np.zeros(initial.shape, bool)
    forced_bg = np.zeros(initial.shape, bool)
    if semantic_seeds is not None:
        seeds = np.array(Image.open(semantic_seeds).convert('L'))
        if seeds.shape != initial.shape or not np.isin(seeds, [0, 128, 255]).all():
            raise ValueError('Reviewed seeds must match source: 0 unknown, 128 background, 255 opaque interior')
        forced_fg = seeds == 255
        forced_bg = seeds == 128
        initial[forced_fg] = 1
        initial[forced_bg] = 0
    seed_kernel = np.ones((11, 11), np.uint8)
    core_seed = cv2.erode(initial, seed_kernel).astype(bool)
    outer_seed = cv2.dilate(initial, seed_kernel).astype(bool)
    labels = np.where(initial, cv2.GC_PR_FGD, cv2.GC_PR_BGD).astype(np.uint8)
    labels[core_seed] = cv2.GC_FGD
    labels[~outer_seed] = cv2.GC_BGD
    labels[forced_fg] = cv2.GC_FGD
    labels[forced_bg] = cv2.GC_BGD
    cv2.setNumThreads(2)
    cv2.setRNGSeed(123)
    bg_model = np.zeros((1, 65), np.float64)
    fg_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), labels, None,
                bg_model, fg_model, 5, cv2.GC_INIT_WITH_MASK)
    binary = ((labels == cv2.GC_FGD) | (labels == cv2.GC_PR_FGD)).astype(np.uint8)
    binary[forced_fg] = 1
    binary[forced_bg] = 0
    # One pixel outside, and the selected radius inside, are eligible.
    # A deeper foreground sample can avoid treating an antialiased gray rim
    # as definite opaque foreground. It still requires native edge review.
    kernel = np.ones((3, 3), np.uint8)
    core_kernel = np.ones((2 * matte_core_radius + 1, 2 * matte_core_radius + 1), np.uint8)
    core = cv2.erode(binary, core_kernel).astype(bool)
    core |= forced_fg
    outer = cv2.dilate(binary, kernel).astype(bool)
    band = outer & ~core
    known_bg = ~cv2.dilate(binary, np.ones((7, 7), np.uint8)).astype(bool)
    known_bg |= forced_bg
    if not core.any() or not known_bg.any():
        raise ValueError('Insufficient definite foreground/background; review mask')
    src = rgb.astype(np.float32)
    f = nearest_pixels(core, src)
    b = nearest_pixels(known_bg, src)
    direction = f - b
    denominator = np.sum(direction * direction, axis=2)
    estimate = np.sum((src - b) * direction, axis=2) / np.maximum(denominator, 1)
    alpha = binary.astype(np.float32)
    usable = band & (denominator > 100)
    alpha[usable] = np.clip(estimate[usable], 0, 1)
    aa = np.rint(alpha * 255).astype(np.uint8)
    aa[core] = 255
    aa[forced_bg] = 0
    # Unmat only genuinely partial coverage; opaque source pixels stay exact.
    partial = (aa > 0) & (aa < 255)
    pixels = rgb.copy()
    a = aa[partial].astype(np.float32)[:, None] / 255
    unmatted = (src[partial] - (1-a) * b[partial]) / a
    pixels[partial] = np.clip(np.rint(unmatted), 0, 255).astype(np.uint8)
    # Observation only: do not force a missing object opaque because it is named.
    coverage = []
    for anchor in anchors:
        x, y = anchor['point_xy']
        value = int(aa[y, x])
        coverage.append({'id': anchor['id'], 'point_xy': [x, y],
                         'source_rgb': rgb[y, x].tolist(), 'alpha': value})
        if value != 255:
            raise ValueError(f"Coverage failed: {anchor['id']} at ({x},{y}) has alpha {value}; review missing part, do not auto-fill")
    dest.mkdir(parents=True)
    profile = original.info.get('icc_profile')
    kwargs = {'icc_profile': profile} if profile else {}
    rgba = Image.fromarray(pixels)
    rgba.putalpha(Image.fromarray(aa))
    rgba.save(dest / 'alpha.png', **kwargs)
    for name, color in [('main', (83, 83, 83)), ('white', (255, 255, 255)),
                        ('black', (0, 0, 0))]:
        canvas = Image.new('RGB', original.size, color)
        canvas.paste(rgba, (0, 0), rgba.getchannel('A'))
        canvas.save(dest / (name + '.png'), **kwargs)
    Image.fromarray(vision).save(dest / 'vision-proposal.png')
    if semantic_seeds is not None:
        Image.fromarray(seeds).save(dest / 'semantic-seeds.png')
    Image.fromarray(binary*255).save(dest / 'grabcut-binary.png')
    Image.fromarray(aa).save(dest / 'mask.png')
    # Recomposition against sampled local source background estimates, for edge audit.
    recon = np.rint(pixels.astype(float)*aa[:, :, None]/255 + b*(1-aa[:, :, None]/255))
    errors = np.max(np.abs(recon-src), axis=2)
    opaque = aa == 255
    checks = {
        'source': str(Path(source).resolve()),
        'source_sha256': hashlib.sha256(Path(source).read_bytes()).hexdigest(),
        'coverage_anchors': str(Path(coverage_anchors).resolve()) if coverage_anchors else None,
        'coverage_anchors_sha256': hashlib.sha256(Path(coverage_anchors).read_bytes()).hexdigest() if coverage_anchors else None,
        'reviewed_opaque_coverage': coverage,
        'coverage_limits': 'Named native interior points only; does not certify all objects, holes, thin edges or visual quality. Anchor roles require source review.',
        'vision_proposal': str(Path(proposal).resolve()),
        'semantic_seeds': str(Path(semantic_seeds).resolve()) if semantic_seeds else None,
        'semantic_seeds_sha256': hashlib.sha256(Path(semantic_seeds).read_bytes()).hexdigest() if semantic_seeds else None,
        'reviewed_opaque_anchor_pixels': int(forced_fg.sum()),
        'reviewed_background_anchor_pixels': int(forced_bg.sum()),
        'size': list(original.size),
        'opaque_rgb_exact': bool(np.array_equal(pixels[opaque], rgb[opaque])),
        'core_alpha_255': bool(np.all(aa[core] == 255)),
        'reviewed_foreground_alpha_255': bool(np.all(aa[forced_fg] == 255)),
        'reviewed_background_alpha_0': bool(np.all(aa[forced_bg] == 0)),
        'rgb_changes_outside_partial': int(np.any(pixels != rgb, axis=2)[~partial].sum()),
        'partial_pixels': int(partial.sum()),
        'changed_pixels': int(np.any(pixels != rgb, axis=2).sum()),
        'edge_band_pixels': int(band.sum()),
        'matte_core_radius': matte_core_radius,
        'grabcut_changed_binary_pixels': int((binary != initial).sum()),
        'estimated_local_background_edge_recompose_max_error': float(errors[partial].max()) if partial.any() else 0,
        'estimated_local_background_edge_recompose_p99_error': float(np.percentile(errors[partial], 99)) if partial.any() else 0,
        'main_blank_exact_535353': bool(np.all(np.array(Image.open(dest/'main.png'))[aa==0] == 83)),
        'color_profile_preserved': Image.open(dest/'alpha.png').info.get('icc_profile') == profile,
        'visual_gate': 'UNREVIEWED: inspect holes, topology, thin details, white/black edges',
        'limits': 'Opaque visible assemblies only. Boundary alpha and local source background are estimates. No external-background transmission support.',
    }
    if not checks['opaque_rgb_exact'] or not checks['core_alpha_255'] or checks['rgb_changes_outside_partial'] or not checks['color_profile_preserved']:
        raise RuntimeError('RGB/alpha invariant failed')
    (dest / 'checks.json').write_text(json.dumps(checks, indent=2))
    print(json.dumps(checks, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source')
    p.add_argument('proposal')
    p.add_argument('dest')
    p.add_argument('--semantic-seeds', help='Reviewed same-size L PNG: 0 unknown, 128 definite background, 255 opaque interior. Never mark antialiased contour as opaque.')
    p.add_argument('--coverage-anchors', help='Reviewed source JSON: opaque_anchors=[{id,point_xy:[x,y]}]. Observation only; fails before output if any named opaque interior is lost. Does not repair mask or certify edges.')
    p.add_argument('--matte-core-radius', type=int, choices=(1, 3), default=1,
                   help='Default1. Experimental3 uses deeper opaque foreground samples for reviewed gray edge fringes. Recheck thin details/holes/materials; not automatic QA.')
    args = p.parse_args()
    run(args.source, args.proposal, args.dest, args.semantic_seeds, args.matte_core_radius, args.coverage_anchors)
