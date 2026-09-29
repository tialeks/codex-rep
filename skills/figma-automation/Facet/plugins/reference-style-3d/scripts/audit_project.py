#!/usr/bin/env python3
"""Read-only project consistency audit; never treats structural checks as visual approval."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

def audit(root=ROOT):
    errors=[]; files=sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    counts={'files':len(files),'python':0,'json':0,'images':0,'markdown':0}
    for p in files:
        try:
            if p.suffix=='.py':
                ast.parse(p.read_text());counts['python']+=1
            elif p.suffix=='.json':
                json.loads(p.read_text());counts['json']+=1
            elif p.suffix in ('.png', '.webp'):
                with Image.open(p) as im:im.verify()
                counts['images']+=1
            elif p.suffix=='.md':
                counts['markdown']+=1
                for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
                    target=target.split('#')[0].strip('<>')
                    if not target or '://' in target or target.startswith('/'):continue
                    if not (p.parent/target).exists():errors.append(str(p.relative_to(root))+': missing link '+target)
        except Exception as exc:errors.append(str(p.relative_to(root))+': '+str(exc))
    refs=root/'skills/reference-style-3d/references'
    profile=json.loads((refs/'prompt-profile.json').read_text())
    for key in ['styleBlock','evidence']:
        if not (root/profile[key]).is_file():errors.append('profile missing '+key)
    registered_images=set()
    for catalog,base,key in [(refs/'sources.json',root,'path'),(root/'assets/materials/catalog.json',root/'assets/materials','path')]:
        data=json.loads(catalog.read_text());rows=data if isinstance(data,list) else data['cards']
        if len({r['id'] for r in rows})!=len(rows):errors.append('duplicate IDs: '+str(catalog))
        for row in rows:
            path=(base/row[key]).resolve()
            registered_images.add(path)
            if not path.is_relative_to(base.resolve()) or not path.is_file():errors.append('invalid asset path: '+row['id']);continue
            if hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:errors.append('asset hash: '+row['id'])
    try:
        from presets import bundled_library, preview_path
        bundle = root / 'assets/presets'
        for row in bundled_library(bundle):
            registered_images.add(preview_path(bundle, row))
    except Exception as exc:
        errors.append('Bundled presets: ' + str(exc))
    for path in files:
        if path.suffix.lower() in ('.png','.jpg','.jpeg','.webp') and path.resolve() not in registered_images:
            errors.append('Unregistered image in package; generation outputs belong outside plugin: '+str(path.relative_to(root)))
        if path.name in ('result.png','submission.json','actual-arguments.json','tool-request.json','review.json'):
            errors.append('Execution artifact in package: '+str(path.relative_to(root)))
    effects=json.loads((refs/'effects.json').read_text())
    if len({e['id'] for e in effects})!=len(effects):errors.append('duplicate effects')
    if any(not e.get('settingsVersions') or set(e['settingsVersions'])-{1,2,3} for e in effects):errors.append('invalid effect version support')
    return {'ok':not errors,'counts':counts,'errors':errors,'visualApproval':False}

if __name__=='__main__':
    result=audit();print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(0 if result['ok'] else 1)

