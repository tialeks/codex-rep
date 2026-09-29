"""Compile submitted controls once; scene prose contains only scene content."""
import json
import re
from material_library import selection, settings_material_ids
from graphics import resolve as resolve_graphics
from reference_guidance import effective_settings, apply as apply_reference

# Compatibility export; prompts are owned by the shared graphics catalogue.
from pathlib import Path
from graphics import camera_prompts
CAMERAS = camera_prompts(Path(__file__).resolve().parents[1])

MODES = {'icon': 'one clear icon silhouette', 'object': 'one standalone object',
         'illustration-simple': 'microillustration with one dominant subject and meaningful supports',
         'illustration-complex': 'layered illustration with one dominant focus',
         'category': 'tonal icon inside a flat circular mask; nothing protrudes; no physical pedestal'}
GRIDS = {1: (1, 1), 4: (2, 2), 5: (5, 1), 8: (4, 2), 9: (3, 3), 15: (5, 3), 16: (4, 4)}


def compile_settings(root, s):
    if not isinstance(s, dict):
        raise ValueError('settings must be an object')
    s = effective_settings(root, s)
    cameras = camera_prompts(root)
    v3 = s.get('settingsVersion') == 3
    if not v3 and 'shot' in s:
        raise ValueError('shot requires settingsVersion=3')
    graphic = None
    if v3:
        forbidden = {'mode','objects','size','detailMode','detail','framing'} & s.keys()
        if forbidden: raise ValueError('Unsupported controls for settingsVersion=3: ' + ', '.join(sorted(forbidden)))
        graphic = resolve_graphics(root, s)
        # Local adapter only: the submitted snapshot remains byte-for-byte unchanged.
        s = dict(s, mode=graphic['graphicType']['mode'], objects=graphic['graphicType']['maxSubjects'],
                 size=256, detailMode='manual', detail=graphic['detailLevel']['level'])
    material_ids = settings_material_ids(root, s)
    v2 = s.get('settingsVersion') in (2, 3)
    required = {'topic', 'mode', 'count', 'objects', 'camera', 'size', 'detailMode',
                'detail', 'creativity', 'whiteBase', 'metal', 'pearl', 'background',
                'palette', 'effects', 'recognizable'}
    if v2: required -= {'metal', 'pearl'}
    if required - s.keys():
        raise ValueError('Missing settings: ' + ', '.join(sorted(required - s.keys())))
    if not isinstance(s['topic'], str) or not s['topic'].strip():
        raise ValueError('Nonempty topic required')
    for key, choices in [('mode', MODES), ('camera', cameras), ('count', GRIDS),
                         ('size', (32, 64, 96, 256)), ('detailMode', ('auto', 'manual')),
                         ('palette', ('natural', 'custom')), ('background', ('white', 'transparent'))]:
        if s[key] not in tuple(choices):
            raise ValueError('Invalid setting: ' + key)
    for key, low, high in [('count', 1, 16), ('size', 32, 256), ('objects', 1, 12 if v3 else 7),
                           ('detail', 1, 5), ('creativity', 1, 5), ('metal', 0, 100), ('pearl', 0, 100)]:
        if v2 and key in ('metal', 'pearl'): continue
        if type(s[key]) is not int or not low <= s[key] <= high:
            raise ValueError('Invalid integer: ' + key)
    for key in ('whiteBase', 'recognizable'):
        if type(s[key]) is not bool:
            raise ValueError('Invalid boolean: ' + key)
    materials = selection(root, material_ids, verify_files=False)
    detail = {32: 1, 64: 2, 96: 3, 256: 4}[s['size']] if s['detailMode'] == 'auto' else s['detail']
    detail = min(detail, {32: 2, 64: 3}.get(s['size'], 5))
    objects = 1 if s['mode'] in ('icon', 'object', 'category') else min(s['objects'], 2 if s['size'] == 32 else 7)
    if v3: objects = graphic['graphicType']['maxSubjects']
    cols, rows = GRIDS[s['count']]
    blocks = [f"Theme: {s['topic'].strip()}",
              f"One PNG sheet: exactly {s['count']} compositions, {cols} columns × {rows} rows; complete silhouettes, clean gutters and safe outer margins.",
              f"Mode: {MODES[s['mode']]}; up to {objects} objects TOTAL per composition, including every detached supporting prop. Structurally connected functional parts and fused hybrid parts form one object; touching independent props still count separately.",
              f"Camera: {cameras[s['camera']]}, consistent across the sheet.",
              f"Readability at {s['size']} CSS px per composition (not PNG resolution); detail {detail}/5; creativity {s['creativity']}/5."]
    if v3:
        blocks[1] = f"One PNG sheet: exactly {s['count']} compositions, {cols} columns × {rows} rows; entire compositions inside their cells, safe outer margins and clean gutters. Internal overlap is allowed if required subjects stay identifiable. Never crop objects at canvas or cell edges; the designer handles placement and cropping later."
        blocks[2] = 'Graphic structure: ' + graphic['graphicType']['prompt'] + ' Count semantic subjects, not every physical part: a pair of shoes, cup with saucer, wallet with cards, or banknote stack is one functional unit. Unrelated props count separately. Explicit subjects take precedence over suggested count ranges; preserve them and report a conflict rather than silently deleting them.'
        blocks[4] = f"Surface and construction detail: {s['detailLevel']} ({detail}/5); creativity {s['creativity']}/5. Detail does not add subjects, change the composition type or request photographic realism. PNG resolution is not specified by these artistic controls."
        blocks.extend(['Arrangement: ' + graphic['arrangement']['prompt']])
    detail_rendering = {
        1: 'Primary silhouette and one large recognition feature; surfaces are quiet color and light fields. Preserve requested content but do not resolve grain, fibers, pores, scratches or tiny hardware.',
        2: 'Primary volumes plus a few broad functional features. Show material differences through reflection, transparency, edge softness and sparse broad surface bands. Treat weave as broad strips and felt as a soft mass; do not resolve individual fibers, pores, scratches, screw threads or ornamental seams unless explicitly requested.',
        3: 'Clear functional construction and selective medium-scale surface cues; keep fine grain and repeated hardware subordinate, never a dense texture blanket.',
        4: 'Rich but selectively edited construction and controlled material texture; the silhouette and broad light fields remain dominant over microdetail.',
        5: 'Detailed authored construction and readable material texture; retain designed proportions and clean lighting rather than adding incidental wear or manufacturing noise.'
    }
    blocks.append('Detail rendering: ' + detail_rendering[detail])
    if s['mode'] in ('icon', 'category') and s['size'] == 32:
        blocks.append('At 32 px, prioritize one dominant silhouette and one large recognition cue. Unless explicitly requested by the user, omit nested interface panels and tiny ticks that become illegible. Preserve explicit user content; simplify its rendering, not its meaning.')
    if s['palette'] == 'natural':
        blocks.append('Palette: natural colors of each object and material.')
    else:
        colors = s.get('colors')
        if not isinstance(colors, list) or not 1 <= len(colors) <= 8 or any(not isinstance(c, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', c) for c in colors):
            raise ValueError('Custom palette requires 1–8 HEX6 colors')
        blocks.append('Palette accents: ' + ', '.join(colors) + '; make these the dominant colors of colorable surfaces across the sheet. Retain necessary natural colors only on unpainted material parts; do not invent unrelated manufactured colors.')
    if s['whiteBase']:
        blocks.append('Use a white base on suitable object surfaces.')
    if v2:
        blocks.append('Geometry: build recognizable primary volumes with a clear hierarchy of recognition cues, preserving explicitly requested details. The selected detail level governs construction and surface detail; it does not increase the number of subjects.' if v3 else 'Geometry: build recognizable primary volumes with 2–4 meaningful recognition cues per subject, preserving explicitly requested details. Choose edges and proportions appropriate to the subject; surface finish is a separate decision.')
        if materials:
            blocks.append('Main body material: ' + material_ids[0] + '. Apply this surface to the main subject’s body in each composition. Accent materials for functional details: ' + (', '.join(material_ids[1:]) or 'none selected') + '. Use accents on meaningful details and supporting objects; they do not replace the main subject’s body material. Preserve these material identities and the submitted palette through shape effects. Use only the selected surface materials, including on secondary props and small details. A natural-color exception does not authorize an unselected surface: do not invent gold on coins, leather on wallets or rubber on wheels if absent from the chosen set. Retain functional shapes without introducing habitual unselected finishes.')
        else:
            blocks.append('Materials: choose surfaces appropriate to each subject and its functional parts, following the style profile and palette.')
    else:
        budgets = []
        for key, label in [('metal', 'metal'), ('pearl', 'nacre')]:
            budgets.append(f"{label}: {s[key]}/100 local accent intensity" if s[key] else f"No {label}, including effects that require it")
        blocks.append('; '.join(budgets) + '. Intensities are artistic directions, not surface percentages or measured PBR values.')
        if s['metal'] == 0:
            blocks.append('Zero metal is authoritative over generic style examples and reference images. Use appropriate nonmetallic alternatives such as painted polymer, ceramic or rubber on functional parts, with ordinary dielectric highlights rather than metallic reflections; preserve the selected palette and subject identity.')
        if s['pearl'] == 0:
            blocks.append('Zero nacre is authoritative over generic style examples and reference images: use a plain base finish without iridescent coating or angle-dependent rainbow sheen.')
        if materials:
            blocks.append('Selected material surfaces available: ' + ', '.join(c['id'] for c in materials) + '. Use only surfaces appropriate to the requested subjects, not necessarily every sample. Submitted metal/nacre budgets, palette and simplification remain authoritative; a zero budget excludes conflicting sample finishes.')
    blocks.append('Background: ' + ('pure white' if s['background'] == 'white' else 'transparent alpha') + '; no horizon or tabletop.')
    blocks.append('Preserve recognizable subjects.' if s['recognizable'] else 'Abstract interpretation is allowed.')
    effects = s['effects']
    if not isinstance(effects, list):
        raise ValueError('effects must be an array')
    if not v3 and len(effects) > (2 if v2 else 3):
        raise ValueError('V2 allows at most one subject effect and one composition effect' if v2 else 'At most three effects')
    catalog = {e['id']: e for e in json.loads((root / 'skills/reference-style-3d/references/effects.json').read_text())}
    seen = set()
    active_effects = []
    effect_scopes = set()
    repeated_scope = False
    placement_overlap = False
    for effect in effects:
        if not isinstance(effect, dict) or not isinstance(effect.get('id'), str) or effect.get('id') not in catalog or effect['id'] in seen:
            raise ValueError('Unknown or duplicate effect')
        seen.add(effect['id'])
        entry = catalog[effect['id']]
        if (3 if v3 else 2 if v2 else 1) not in entry.get('settingsVersions', [1, 2, 3]):
            raise ValueError('V2 surface changes are selected through materials, not effect: ' + effect['id'])
        strength = effect.get('strength')
        target = effect.get('target', '')
        if type(strength) is not int or not 0 <= strength <= 100 or not isinstance(target, str):
            raise ValueError('Invalid effect strength/target')
        if v2 and strength and effect['id'] != 'none':
            effect_scope = entry.get('scope', 'subject')
            if not v3 and (effect_scope not in ('subject','composition') or effect_scope in effect_scopes):
                raise ValueError('V2 allows at most one subject effect and one composition effect')
            repeated_scope |= effect_scope in effect_scopes
            placement_overlap |= v3 and effect_scope == 'composition' and s['arrangement'] != 'auto'
            effect_scopes.add(effect_scope)
        if entry.get('needsTarget') and strength and not target.strip():
            raise ValueError('Effect requires a target')
        if not v3 and strength and objects < entry.get('minObjects',1):
            raise ValueError(f"Effect {effect['id']} requires at least {entry['minObjects']} objects; effective budget is {objects}")
        if not v2 and strength and entry.get('requiresBudget') and s[entry['requiresBudget']] == 0:
            raise ValueError('Effect conflicts with zero material budget: ' + effect['id'])
        if strength and effect['id'] != 'none':
            visibility = ('subtle localized change' if strength <= 30 else 'clearly visible change' if strength <= 70 else 'pronounced transformation')
            scope = 'Apply to the relationships between objects in each composition. ' if entry.get('scope')=='composition' else ''
            effect_prompt = entry['prompt'].replace('TARGET', target)
            if v2 and effect['id']=='inflate':
                effect_prompt = 'Give the main subject inflated geometry: bulging broad faces, swollen edges and taut transitions while keeping recognition cues. Preserve its assigned surface material; inflated geometry does not imply PVC, rubber or a material replacement.'
            elif v2 and effect['id']=='peel':
                effect_prompt = 'Peel one continuous outer layer with a legible connection; retain assigned materials on both exposed and outer surfaces.'
            elif v2 and effect['id']=='flow':
                effect_prompt = 'Show a controlled stream passing through the object and changing shape once; preserve assigned material identities.'
            elif v2 and effect['id']=='nest':
                effect_prompt = 'Use nested shapes with legible clearance and scale hierarchy; preserve assigned surfaces.'
            active_effects.append(f"Effect (priority {len(active_effects)+1}): {scope}{effect_prompt} Intensity {strength}/100: {visibility}." + (f' Target: {target}.' if target else ''))
    if not v2 and any(e.get('strength',0)>0 and e['id']=='pearl' for e in effects):
        blocks = [block.replace(f"nacre: {s['pearl']}/100 local accent intensity", f"nacre: {s['pearl']}/100 local accent distribution budget") for block in blocks]
    if active_effects:
        scope_rule = ('Apply subject effects to the main subject and composition effects to object relationships in every composition unless the user specifies a narrower scope.' if any(e.get('strength',0)>0 and catalog[e['id']].get('scope')=='composition' for e in effects) else 'Apply the selected effects to the main subject of every composition unless the user specifies a narrower scope.')
        blocks.append(scope_rule + ' For hybrid and morph, Target is the second identity, not an object to locate. Transform the ordinary construction described in SCENES as needed for the selected effect, preserving subject identity, palette and object budget. Combine effects in listed priority order; a lower-priority effect must not erase a higher-priority one.')
        if any(e.get('strength',0)>0 and e['id'] in ('explode','scatter','slice') for e in effects):
            blocks.append('Separated structural fragments of one source object retain that single object identity and count as one; unrelated added props still count toward the total object budget.')
        blocks.extend(active_effects)
    for key, label in [('subjects', 'User subjects in order'), ('avoid', 'Avoid')]:
        value = s.get(key, '')
        if not isinstance(value, str):
            raise ValueError('Invalid text: ' + key)
        if value.strip():
            blocks.append(label + ': ' + value.strip())
    blocks.append('Text: render only wording explicitly requested by the user. Keep other labels, book covers and screens free of invented slogans or brand names; simple functional symbols are allowed.')
    blocks.append('Explicit user color of a part takes precedence; reference colors are examples. Preserve optical material behavior when changing color.')
    effect_priority = len(active_effects) > 2 or repeated_scope or placement_overlap
    return compact_v3(root, s, graphic, materials, active_effects, effect_priority) if v3 else '\n'.join(blocks)


def compact_v3(root, s, graphic, material_cards, effects, effect_priority=False):
    cameras = camera_prompts(root)
    material_ids = [card['id'] for card in material_cards]
    cols, rows = GRIDS[s['count']]
    level = graphic['detailLevel']['level']
    details = {'minimal':'Broad forms and recognition features; material identity through light and edges, no microtexture.',
               'balanced':'Readable construction and selective medium-scale surface cues; quiet large surfaces.',
               'rich':'Selective seams, weave, relief and functional construction; preserve graphic proportions and clean light.'}
    blocks = [f"Theme: {s['topic'].strip()}",
              f"PNG: {s['count']} separate compositions, {cols} columns × {rows} rows. Safe margins and gutters. Never crop objects at cell/canvas edges; internal overlap is allowed.",
              'Structure: ' + graphic['graphicType']['prompt'],
              'Count semantic subjects, not functional parts or repeated contents. Explicit user subjects take precedence over suggested ranges.',
              'Arrangement: ' + graphic['arrangement']['prompt'],
              'Camera: ' + cameras[s['camera']] + ', consistent across the sheet.',
              f"Detail: {s['detailLevel']} ({level}/5). " + details[s['detailLevel']],
              f"Creativity: {s['creativity']}/5; vary form/metaphor, not subject count or required materials."]
    if graphic['shot']['id'] != 'auto':
        blocks.append('Shot: ' + graphic['shot']['prompt'])
    blocks.append('Palette: natural object/material colors.' if s['palette']=='natural' else 'Palette: '+', '.join(s['colors'])+' dominate colorable surfaces; unpainted materials retain necessary natural colors. Do not invent unrelated manufactured colors.')
    if material_ids:
        blocks.append('Main body material: '+material_ids[0]+'. Construct each main subject from '+material_cards[0]['prompt']+', even when unconventional for that object; preserve its identity, not its habitual surface. Accent materials for functional details: '+(', '.join(material_ids[1:]) or 'none selected')+'. Only these surfaces, including props and coins; natural-color exceptions do not add finishes.')
    else: blocks.append('Materials: choose appropriate, visibly distinct surfaces for each subject and its parts.')
    if s['whiteBase']: blocks.append('Suitable large surfaces have a white base.')
    blocks.append('Background: '+('pure white' if s['background']=='white' else 'transparent alpha')+'; no horizon or tabletop.')
    blocks.append('Keep subjects recognizable.' if s['recognizable'] else 'Abstract interpretation allowed.')
    if effects:
        blocks.append('Apply selected effects in every composition unless explicitly scoped otherwise. Transform the scene construction as needed, preserving assigned materials, palette and semantic subject count.')
        if any(e.get('strength', 0) > 0 and e['id'] in ('explode', 'scatter', 'slice') for e in s['effects']):
            blocks.append('Separated structural pieces of one source remain one semantic subject; unrelated added props count separately.')
    if effect_priority:
        blocks.append('Combine effects in listed priority order; preserve earlier effects and subject count. Composition effects take precedence over arrangement where they conflict.')
    blocks.extend(effects)
    for key,label in [('subjects','User subjects in order'),('avoid','Avoid')]:
        if s.get(key,'').strip():blocks.append(label+': '+s[key].strip())
    blocks.append('Text only if explicitly requested; functional symbols allowed. No invented brands. Explicit user instructions override reference examples.')
    return '\n'.join(apply_reference(root, s, blocks))

