"""Prepare an unreviewed critic record; validate evidence and opaque exports.

This checks recorded evidence, not human/agent identity or visual correctness.
Pillow is the only external dependency. Relative paths resolve from the report.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import uuid

from PIL import Image, ImageChops

STYLE = ('style-01-packaging.png', 'style-02-spa.png', 'style-03-basket.png')
GATES = ('geometry', 'composition', 'style_family', 'color', 'material')
LIMITS = ('Recorded author/reviewer IDs cannot establish actual independence. '
          'Saved crops cannot establish that they were inspected. Numeric checks '
          'do not certify geometry, materials, style, hidden parts or false holes; '
          'those require independent visual review.')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind(path, base):
    path = Path(path).resolve()
    base = Path(base).resolve()
    with Image.open(path) as im:
        size = list(im.size)
    return {'path': os.path.relpath(path, base), 'sha256': digest(path), 'size': size}


def checked_file(record, base):
    path = (base / record['path']).resolve()
    if digest(path) != record['sha256']:
        raise ValueError(f'Stale bytes: {path}')
    with Image.open(path) as im:
        if list(im.size) != record['size']:
            raise ValueError(f'Changed dimensions: {path}')
    return path


def exact(a, b):
    return a.mode == b.mode and a.size == b.size and a.tobytes() == b.tobytes()


def numeric_export(paths):
    """Recompute pixel invariants; never trust a report's numeric PASS flags."""
    images = {}
    for key, path in paths.items():
        with Image.open(path) as image:
            images[key] = image.copy()
    source, alpha = images['source'], images['alpha']
    if source.mode not in ('RGB', 'RGBA') or alpha.mode != 'RGBA':
        raise ValueError('Opaque source RGB/RGBA and RGBA export required')
    if source.mode == 'RGBA' and source.getchannel('A').getextrema() != (255, 255):
        raise ValueError('Source must be opaque')
    if any(im.size != source.size for im in images.values()):
        raise ValueError('Export dimensions differ')
    mask = alpha.getchannel('A')
    histogram = mask.histogram()
    if not histogram[0] or not histogram[255]:
        raise ValueError('Export needs actual transparent background and opaque foreground')
    opaque = mask.point(lambda x: 255 if x == 255 else 0)
    difference = ImageChops.difference(source.convert('RGB'), alpha.convert('RGB'))
    for channel in difference.split():
        if ImageChops.multiply(channel, opaque).getbbox():
            raise ValueError('Opaque export RGB differs from source')
    for name, color in [('main', (83, 83, 83)), ('white', (255, 255, 255)), ('black', (0, 0, 0))]:
        canvas = Image.new('RGB', source.size, color)
        canvas.paste(alpha, (0, 0), mask)
        if images[name].mode != 'RGB' or not exact(canvas, images[name]):
            raise ValueError(f'{name} does not match exact alpha recomposition')
    profile = source.info.get('icc_profile')
    if any(im.info.get('icc_profile') != profile for im in images.values()):
        raise ValueError('Export color profile differs from source')
    return {'opaque_rgb_exact': True, 'main_white_black_recomposition_exact': True,
            'transparent_pixels': histogram[0], 'opaque_pixels': histogram[255],
            'color_profile_preserved': True, 'limits': LIMITS}


def prepare(args):
    report = Path(args.output).resolve()
    if report.exists():
        raise ValueError('Preserve existing review; output already exists')
    if not args.author_id.strip() or not args.reviewer_id.strip() or args.author_id.strip() == args.reviewer_id.strip():
        raise ValueError('Distinct nonempty author and reviewer IDs required')
    supplied = {'source': args.source, 'main': args.main or args.source}
    if args.phase == 'final':
        if not all((args.main, args.alpha, args.white, args.black)):
            raise ValueError('Final prepare requires main, alpha, white and black')
        if not getattr(args, 'preview_report', None):
            raise ValueError('Final prepare requires selected preview report')
        if getattr(args, 'selection_mode', None) not in ('designer', 'delegated') or not getattr(args, 'selection_finding', '').strip():
            raise ValueError('Explicit designer/delegated selection mode and finding required')
        validate(args.preview_report, 'preview')
        supplied.update(alpha=args.alpha, white=args.white, black=args.black)
    elif any((args.alpha, args.white, args.black)):
        raise ValueError('Use final phase for alpha export review')
    base = report.parent
    assets = Path(__file__).resolve().parent.parent / 'assets'
    refs = [{'role': 'STYLE', **bind(assets / name, base)} for name in STYLE]
    for role in ('category', 'content', 'brand'):
        refs.extend({'role': role.upper(), **bind(p, base)} for p in getattr(args, role))
    record = {'schema_version': 1, 'review_id': str(uuid.uuid4()), 'phase': args.phase,
              'case_id': args.case_id, 'variant_id': args.variant_id,
              'author_id': args.author_id.strip(), 'reviewer_id': args.reviewer_id.strip(),
              'status': 'UNREVIEWED', 'assets': {k: bind(p, base) for k, p in supplied.items()},
              'references': refs, 'gates': {k: {'status': 'UNREVIEWED', 'finding': ''} for k in GATES},
              'native_100_material_review': {'status': 'UNREVIEWED', 'surfaces': []}, 'limits': LIMITS}
    if args.brand:
        record['gates']['branding'] = {'status': 'UNREVIEWED', 'finding': ''}
    if args.phase == 'final':
        preview_path = Path(args.preview_report).resolve()
        record['selected_preview'] = {'path': os.path.relpath(preview_path, base), 'sha256': digest(preview_path)}
        record['selection'] = {'mode': args.selection_mode, 'finding': args.selection_finding.strip()}
        check_preview_chain(record, base)
        record['gates']['alpha_visual'] = {'status': 'UNREVIEWED', 'finding': '',
                                         'full_boundary_sweep_checked': False, 'evidence': []}
    if args.surfaces or args.phase == 'final':
        crops = base / (report.stem + '-evidence')
        if crops.exists():
            raise ValueError('Preserve previous evidence directory')
        crops.mkdir(parents=True)
    if args.surfaces:
        surfaces = json.loads(Path(args.surfaces).read_text())
        for index, surface in enumerate(surfaces):
            key = surface.get('asset', 'main')
            with Image.open(supplied[key]) as image:
                roi = validate_roi(surface['roi'], image.size)
                crop = crops / f'{index:02d}-{key}.png'
                image.crop(roi).save(crop)
            record['native_100_material_review']['surfaces'].append({
                'material': surface['material'], 'asset': key, 'roi': list(roi),
                'light_mid_shadow_edge_checked': False, 'full_surface_sweep_checked': False,
                'finding': '', 'evidence': bind(crop, base)})
    if args.phase == 'final':
        edge_rois_path = getattr(args, 'edge_rois', None)
        edge_rois = json.loads(Path(edge_rois_path).read_text()) if edge_rois_path else None
        for key in ('main', 'white', 'black'):
            with Image.open(supplied[key]) as image:
                rois = edge_rois or [[0, 0, image.width, image.height]]
                for index, roi_spec in enumerate(rois):
                    roi = validate_roi(roi_spec, image.size)
                    crop = crops / f'edge-{key}-{index:02d}.png'
                    image.crop(roi).save(crop)
                    record['gates']['alpha_visual']['evidence'].append({
                        'asset': key, 'roi': list(roi), 'checked': False, 'finding': '',
                        'evidence': bind(crop, base)})
    base.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n')
    return {'report': str(report), 'status': 'UNREVIEWED', 'limits': LIMITS}


def validate_roi(roi, size):
    if not isinstance(roi, list) or len(roi) != 4 or not all(type(x) is int for x in roi):
        raise ValueError('ROI requires four integer native pixel coordinates')
    x0, y0, x1, y1 = roi
    if not (0 <= x0 < x1 <= size[0] and 0 <= y0 < y1 <= size[1]):
        raise ValueError('ROI outside referenced original')
    return tuple(roi)


def check_preview_chain(record, base):
    selection = record.get('selection', {})
    if selection.get('mode') not in ('designer', 'delegated') or not selection.get('finding', '').strip():
        raise ValueError('Final requires explicit selected preview decision')
    selected = record['selected_preview']
    path = (base / selected['path']).resolve()
    if digest(path) != selected['sha256']:
        raise ValueError('Selected preview report bytes changed')
    validate(path, 'preview')
    preview = json.loads(path.read_text())
    if record['reviewer_id'].strip() == preview['author_id'].strip():
        raise ValueError('Final reviewer cannot be the original selected render author')
    for identity in ('case_id', 'variant_id'):
        if preview[identity] != record[identity]:
            raise ValueError(f'Selected preview {identity} differs from final')
    if preview['assets']['source']['sha256'] != record['assets']['source']['sha256']:
        raise ValueError('Final source differs from selected preview render')
    reference_roles = lambda r: sorted((ref['role'], ref['sha256']) for ref in r['references'])
    if reference_roles(preview) != reference_roles(record):
        raise ValueError('Final reference roles/bytes differ from selected preview')


def validate(report_path, expected_phase=None):
    report_path = Path(report_path).resolve()
    base = report_path.parent
    r = json.loads(report_path.read_text())
    if r.get('schema_version') != 1 or not r.get('review_id'):
        raise ValueError('Unknown review schema or missing review ID')
    phase = r.get('phase')
    if phase not in ('preview', 'final') or expected_phase and phase != expected_phase:
        raise ValueError('Review phase mismatch; prepare a separate final record')
    for key in ('case_id', 'variant_id', 'author_id', 'reviewer_id'):
        if not str(r.get(key, '')).strip():
            raise ValueError(f'Missing {key}')
    if r['author_id'].strip() == r['reviewer_id'].strip():
        raise ValueError('Self review rejected')
    if r.get('status') != 'PASS':
        raise ValueError('Review is not PASS')
    needed = ('source', 'main', 'alpha', 'white', 'black') if phase == 'final' else ('source', 'main')
    if set(r['assets']) != set(needed):
        raise ValueError('Assets do not match phase; prepare a separate phase record')
    paths = {key: checked_file(r['assets'][key], base) for key in needed}
    if phase == 'preview' and r['assets']['source']['sha256'] != r['assets']['main']['sha256']:
        raise ValueError('Preview source and viewed main must be the same render bytes')
    if phase == 'final':
        check_preview_chain(r, base)
    assets = Path(__file__).resolve().parent.parent / 'assets'
    styles = []
    for ref in r['references']:
        path = checked_file(ref, base)
        if ref['role'] == 'STYLE':
            styles.append((path.name, ref['sha256']))
        elif ref['role'] not in ('CATEGORY', 'CONTENT', 'BRAND'):
            raise ValueError('Unknown reference role')
    if styles != [(name, digest(assets / name)) for name in STYLE]:
        raise ValueError('All three unmodified package STYLE references required in order')
    required_gates = GATES + (('alpha_visual',) if phase == 'final' else ())
    if any(ref['role'] == 'BRAND' for ref in r['references']):
        required_gates += ('branding',)
    for gate in required_gates:
        value = r['gates'][gate]
        status, finding = value.get('status'), value.get('finding', '').strip()
        if not finding or status != 'PASS':
            raise ValueError(f'Unaccepted or undocumented {gate} gate')
    material = r['native_100_material_review']
    if material.get('status') != 'PASS' or not material.get('surfaces'):
        raise ValueError('Native material surface inspection required')
    for surface in material['surfaces']:
        if not surface.get('material', '').strip() or not surface.get('finding', '').strip():
            raise ValueError('Material and native finding required')
        if surface.get('light_mid_shadow_edge_checked') is not True or surface.get('full_surface_sweep_checked') is not True:
            raise ValueError('Full surface/light/mid/shadow/edge review required')
        key = surface['asset']
        if key not in ('source', 'main'):
            raise ValueError('Native material evidence must use source or main')
        with Image.open(paths[key]) as image:
            roi = validate_roi(surface['roi'], image.size)
            with Image.open(checked_file(surface['evidence'], base)) as crop:
                if not exact(image.crop(roi), crop):
                    raise ValueError('Evidence crop is resized, altered or from different pixels')
    if phase == 'final':
        coverage = {}
        for surface in material['surfaces']:
            identity = (surface['material'], tuple(surface['roi']))
            coverage.setdefault(identity, set()).add(surface['asset'])
        if any(assets != {'source', 'main'} for assets in coverage.values()):
            raise ValueError('Each final native surface ROI requires both source and final main evidence')
        alpha_review = r['gates']['alpha_visual']
        if alpha_review.get('full_boundary_sweep_checked') is not True or not alpha_review.get('evidence'):
            raise ValueError('Native alpha evidence and complete boundary sweep required')
        edge_assets = set()
        for proof in alpha_review['evidence']:
            key = proof['asset']
            if key not in ('main', 'white', 'black') or proof.get('checked') is not True or not proof.get('finding', '').strip():
                raise ValueError('Alpha native proof needs main/white/black asset, checked flag and finding')
            with Image.open(paths[key]) as image:
                roi = validate_roi(proof['roi'], image.size)
                with Image.open(checked_file(proof['evidence'], base)) as crop:
                    if not exact(image.crop(roi), crop):
                        raise ValueError('Alpha evidence is resized, altered or from different pixels')
            edge_assets.add(key)
        if edge_assets != {'main', 'white', 'black'}:
            raise ValueError('Native alpha evidence requires all of main, white and black')
    return {'status': 'FULL_PASS' if phase == 'final' else 'PREVIEW_PASS', 'phase': phase, 'report_sha256': digest(report_path),
            'numeric_export': numeric_export(paths) if phase == 'final' else None, 'limits': LIMITS}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare', help='Write a hash-bound UNREVIEWED critic template')
    p.add_argument('--phase', choices=('preview', 'final'), required=True)
    for name in ('source', 'main', 'alpha', 'white', 'black'):
        p.add_argument('--' + name, required=name == 'source')
    for name in ('author-id', 'reviewer-id', 'case-id', 'variant-id', 'output'):
        p.add_argument('--' + name, required=True)
    for name in ('category', 'content', 'brand'):
        p.add_argument('--' + name, action='append', default=[])
    p.add_argument('--surfaces', help='JSON list of material/asset/roi; save native evidence with unchecked flags')
    p.add_argument('--edge-rois', help='Final: JSON list of native ROIs copied from main/white/black; default full frames. Critic must inspect full boundary.')
    p.add_argument('--preview-report', help='Final: selected validated PREVIEW_PASS report, hash-bound to this release')
    p.add_argument('--selection-mode', choices=('designer', 'delegated'), help='Final: explicit actual selection authority')
    p.add_argument('--selection-finding', help='Final: record actual approval/authorized delegated decision; never assume approval')
    v = commands.add_parser('validate', help='Reject missing/stale review and recompute final pixel invariants')
    v.add_argument('report')
    v.add_argument('--phase', choices=('preview', 'final'), help='Require this phase (use final for release)')
    args = parser.parse_args()
    try:
        result = prepare(args) if args.command == 'prepare' else validate(args.report, args.phase)
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as error:
        parser.exit(1, f'REJECTED: {error}\n')
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
