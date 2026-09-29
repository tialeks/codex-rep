#!/usr/bin/env python3
"""Portable reference selection and immutable imagegen request preparation.
No model call is made. Submission receipt records exact arguments, not visual success.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from compile_settings import compile_settings
from material_library import build_sheet, settings_material_ids
from reference_guidance import selected as reference_facets, effective_settings, image_binding

ROOT = Path(__file__).resolve().parents[1]
COLOR_RULES = '''Explicit user color of a part overrides the selected palette. In custom mode apply the supplied palette to suitable colorable surfaces while preserving appropriate natural material colors. In natural mode ignore saved accent HEX values and use natural object colors. Colors of any examples are illustrative, not defaults. Preserve the material's optical behavior when changing color. Materials are an open library: use other appropriate materials when needed. Do not invent measured PBR values.'''
MATERIAL_REFERENCE_RULES = '''MATERIAL REFERENCE images supply surface response, texture scale, coating behavior and transparency only. Lighting, geometry, simplification and overall realism remain governed by the style profile and submitted settings. Build the requested subject's own functional geometry: do not copy specimen spheres, recesses, seams, sheet layout or labels. Reference colors are illustrative; submitted palette and material budgets remain authoritative. The samples are an open material library, not a requirement to use every surface.'''
REFERENCE_RULES = {
    'STYLE REFERENCE': 'STYLE REFERENCE: transfer simplification, material response and light, not subjects, layout or local colors.',
    'CONTENT REFERENCE': 'CONTENT REFERENCE: retain the depicted subject identity and relevant construction; apply the submitted style and settings.',
    'COMPOSITION REFERENCE': 'COMPOSITION REFERENCE: guide arrangement, hierarchy and relative scale within the submitted settings; do not copy subjects, colors or cropping.',
    'GUIDANCE REFERENCE': 'GUIDANCE REFERENCE: transfer only the facets listed in REQUIRED SETTINGS.',
    'EDIT SOURCE': 'EDIT SOURCE: change only requested properties and preserve the rest. A generated source does not define our style.'
}



def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p, value): Path(p).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def inside(root, relative):
    p = Path(relative)
    resolved = (root/p).resolve()
    if p.is_absolute() or not resolved.is_relative_to(root.resolve()):
        raise ValueError('Packaged path must remain inside plugin: '+str(relative))
    if not resolved.is_file(): raise ValueError('Missing packaged file: '+str(relative))
    return resolved


def select(root, request):
    mode = request.get('referenceMode', 'prompt')
    if not isinstance(mode, str):
        raise ValueError('referenceMode must be a string')
    if mode not in ('prompt', 'selected', 'originals'):
        raise ValueError('Unsupported referenceMode; use prompt, selected or originals')
    if mode in ('prompt', 'selected'):
        ids = request.get('styleReferenceIds', [])
        if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
            raise ValueError('styleReferenceIds must be strings')
        if mode == 'prompt':
            if ids:
                raise ValueError('Use selected mode for explicit style references')
            return [], {'mode': mode}
        if not ids:
            raise ValueError('Selected mode requires styleReferenceIds')
        if not isinstance(request.get('referenceReason'), str) or not request['referenceReason'].strip():
            raise ValueError('Selected mode requires a specific referenceReason')
    else:
        # Explicit legacy originals retain their established routing.
        registry = read(root/'skills/reference-style-3d/references/reference-routing.json')['originals']
        materials = request.get('materials', [])
        if not isinstance(materials, list) or not all(isinstance(m, str) for m in materials):
            raise ValueError('materials must be strings')
        ids = list(registry['base'])
        ids.extend(registry['materials'][m] for m in materials if m in registry['materials'])
    records = {e['id']: e for e in read(root/'skills/reference-style-3d/references/sources.json')}
    if any(i not in records for i in ids):
        raise ValueError('Unknown original style reference')
    return [records[i] for i in dict.fromkeys(ids)], {'mode': mode}


def prepare(root, request, out):
    if Path(out).resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('Execution output must be outside the plugin directory')
    if not isinstance(request,dict): raise ValueError('Request must be an object')
    if 'transparentBackground' in request and type(request['transparentBackground']) is not bool:
        raise ValueError('transparentBackground must be a boolean')
    if 'schemaVersion' in request:
        if type(request['schemaVersion']) is not int or request['schemaVersion'] != 1:
            raise ValueError('Unsupported request schemaVersion')
        if not isinstance(request.get('settings'),dict):
            raise ValueError('Schema version 1 requires settings object')
    if not isinstance(request.get('prompt'),str) or not request['prompt'].strip(): raise ValueError('Nonempty prompt required')
    if 'editSource' in request and (not isinstance(request['editSource'],str) or not request['editSource'].strip()):
        raise ValueError('editSource must be a nonempty path string')
    user_refs=request.get('userReferences',[])
    if not isinstance(user_refs,list): raise ValueError('userReferences must be a list')
    for index,ref in enumerate(user_refs):
        if not isinstance(ref,dict): raise ValueError(f'userReferences[{index}] must be an object')
        if not isinstance(ref.get('path'),str) or not ref['path'].strip():
            raise ValueError(f'userReferences[{index}].path must be a nonempty string')
        if not isinstance(ref.get('role'),str) or ref['role'] not in ('CONTENT REFERENCE','COMPOSITION REFERENCE','STYLE REFERENCE','MATERIAL REFERENCE','GUIDANCE REFERENCE'):
            raise ValueError(f'userReferences[{index}].role must be an explicit supported role string')
    settings=request.get('settings')
    if settings is not None and not isinstance(settings, dict):
        raise ValueError('settings must be an object')
    facets=reference_facets(root,settings)
    binding=image_binding(settings)
    guides=[r for r in user_refs if r['role']=='GUIDANCE REFERENCE']
    if facets and binding:
        bound_path=Path(binding['path']).resolve()
        if not bound_path.is_file():
            raise ValueError('Missing bound reference: '+binding['path'])
        if sha(bound_path) != binding['sha256'].lower():
            raise ValueError('Bound reference checksum mismatch; attach the current image again')
        if len(guides)>1:
            raise ValueError('Duplicate GUIDANCE REFERENCE; the bound image has exactly one guidance role')
        if guides and Path(guides[0]['path']).resolve()!=bound_path:
            raise ValueError('GUIDANCE REFERENCE conflicts with the bound image')
        if not guides:
            user_refs=[*user_refs, {'path':binding['path'],'role':'GUIDANCE REFERENCE'}]
            guides=[user_refs[-1]]
    if len(guides) != bool(facets):
        raise ValueError('Selected reference facets require exactly one attached GUIDANCE REFERENCE')
    settings_block=compile_settings(root,settings) if settings is not None else None
    if settings is not None and 'transparentBackground' in request and request['transparentBackground'] != (settings['background']=='transparent'):
        raise ValueError('Background conflicts with submitted settings')
    selected, routing=select(root,request)
    refs=[]
    expected_hashes={}
    for r in selected:
        p=inside(root,r['path'])
        if sha(p)!=r['sha256']: raise ValueError('Reference checksum mismatch: '+r['id'])
        expected_hashes[p]=r['sha256']
        refs.append((p,{'id':r['id'],'role':'STYLE REFERENCE','origin':'plugin','pluginPath':r['path']}))
    extras=[]
    if request.get('editSource'): extras.append((Path(request['editSource']).resolve(),{'id':'edit-source','role':'EDIT SOURCE','origin':'user'}))
    for i, u in enumerate(user_refs):
        role=u['role']
        if role not in ('CONTENT REFERENCE','COMPOSITION REFERENCE','STYLE REFERENCE','MATERIAL REFERENCE','GUIDANCE REFERENCE'): raise ValueError('Explicit user reference role required')
        extras.append((Path(u['path']).resolve(),{'id':'user-'+str(i+1),'role':role,'origin':'user',**({'referenceType':'material'} if role=='MATERIAL REFERENCE' else {}),**({'facets':facets} if role=='GUIDANCE REFERENCE' else {}),**({'imageBinding':dict(binding)} if role=='GUIDANCE REFERENCE' and binding else {})}))
    refs=extras[:1]+refs+extras[1:] if request.get('editSource') else refs+extras
    material_ids=settings_material_ids(root,effective_settings(root,settings)) if settings is not None else []
    if len(refs)+bool(material_ids)>5: raise ValueError('Selected references exceed verified limit 5; refine materials/references, never silently drop them')
    for p,_ in refs:
        if not p.is_file(): raise ValueError('Missing reference: '+str(p))
    if out.exists(): raise ValueError('Execution directory already exists; use a new attempt directory')
    out.mkdir(parents=True); (out/'refs').mkdir()
    try:
        actual=[]
        for i,(p,metadata) in enumerate(refs):
            dest=out/'refs'/f'{i+1:02d}-{metadata["id"]}{p.suffix}'
            shutil.copyfile(p,dest)
            checksum=sha(dest)
            if p in expected_hashes and checksum != expected_hashes[p]:
                raise ValueError('Style reference changed while preparing the execution')
            if metadata.get('imageBinding') and checksum!=metadata['imageBinding']['sha256'].lower():
                raise ValueError('Bound reference changed while preparing the execution')
            actual.append({**metadata,'file':str(dest.relative_to(out)),'sha256':checksum})
        material_sheet=None
        if material_ids:
            sheet=out/'refs'/'material-selection.png'
            layout=build_sheet(root,material_ids,sheet)
            dump(out/'material-layout.json',layout)
            material_sheet={'file':'material-layout.json','sha256':sha(out/'material-layout.json')}
            actual.append({'id':'material-selection','role':'MATERIAL REFERENCE','origin':'plugin','referenceType':'material','file':str(sheet.relative_to(out)),'sha256':sha(sheet)})
        roles='\n'.join(f'Image {i+1}: {r["role"]} ({r["id"]}).' for i,r in enumerate(actual))
        blocks=['SCENES\n'+request['prompt'].strip()]
        profile=read(root/'skills/reference-style-3d/references/prompt-profile.json')
        block=inside(root,profile['styleBlock'])
        recipe={'id':profile['id'],'version':profile['version'],'status':profile['status'],'styleBlockSha256':sha(block)}
        if facets: recipe['referenceGuidanceSha256']=sha(root/'skills/reference-style-3d/references/reference-facets.json')
        blocks.append('SHARED VISUAL LANGUAGE\n'+block.read_text().strip())
        if not settings_block: blocks.append(COLOR_RULES)
        if actual:
            blocks.extend(REFERENCE_RULES[role] for role in dict.fromkeys(r['role'] for r in actual) if role in REFERENCE_RULES)
            blocks.append(roles)
        if any(r['role']=='MATERIAL REFERENCE' for r in actual):
            material_rules=('MATERIAL REFERENCE images supply surface finish only, not sphere shape, color, lighting or extra detail. Use the listed main/detail roles.' if settings is not None and settings.get('settingsVersion')==3 else MATERIAL_REFERENCE_RULES)
            if settings is not None and settings.get('settingsVersion') in (2, 3):
                material_rules=material_rules.replace('submitted palette and material budgets remain authoritative', 'submitted palette and assigned material roles remain authoritative')
            if material_ids and settings.get('settingsVersion') in (2, 3):
                material_rules = material_rules.replace('The samples are an open material library, not a requirement to use every surface.', 'Only the selected surface identities are available for this request. Apply their main/detail roles; do not invent additional finishes or force every accent into every scene.')
            blocks.append(material_rules)
            if material_ids and settings.get('settingsVersion') in (2, 3):
                image_number=next(i+1 for i,r in enumerate(actual) if r['id']=='material-selection')
                legend='; '.join(f"{i+1} {material_id} ({'main' if i==0 else 'details'})" for i,material_id in enumerate(material_ids))
                blocks.append(f'Material sheet Image {image_number} cells, left-to-right/top-to-bottom: {legend}.')
        if settings_block: blocks.append('REQUIRED SETTINGS\n'+settings_block)
        prompt='\n\n'.join(b for b in blocks if b)
        (out/'prompt.txt').write_text(prompt)
        tool_args={'prompt':prompt,'transparent_background':(settings['background']=='transparent') if settings is not None else bool(request.get('transparentBackground',False))}
        if actual: tool_args['referenced_image_paths']=[str((out/r['file']).resolve()) for r in actual]
        dump(out/'tool-request.json',tool_args)
        manifest={'schemaVersion':2,'integrity':'external-manifest-pin-required','status':'prepared-not-submitted','pluginVersion':read(root/'.codex-plugin/plugin.json')['version'],**routing,'recipe':recipe,'request':request,'promptFile':'prompt.txt','promptSha256':sha(out/'prompt.txt'),'references':actual,'transparentBackground':tool_args['transparent_background']}
        if material_sheet: manifest['materialSheet']=material_sheet
        dump(out/'manifest.json',manifest)
        return dict(manifest,manifestSha256=sha(out/'manifest.json'))
    except Exception:
        # This directory was created above by this attempt; never leave a partial execution.
        shutil.rmtree(out)
        raise


def verify(out, expected_manifest_sha256=None, allow_legacy=False):
    manifest=read(out/'manifest.json'); tool=read(out/'tool-request.json')
    if expected_manifest_sha256 is not None:
        if sha(out/'manifest.json') != expected_manifest_sha256:
            raise ValueError('Prepared manifest changed: request, version or recipe does not match trusted pin')
    elif manifest.get('schemaVersion')==2 or not allow_legacy:
        raise ValueError('Trusted manifest SHA required; pass the pin returned by prepare, not a freshly calculated hash')
    if manifest.get('schemaVersion') not in (1,2):
        raise ValueError('Unsupported execution manifest schemaVersion')
    receipt=out/'submission.json'
    if receipt.exists() and read(receipt).get('manifestSha256') != sha(out/'manifest.json'):
        raise ValueError('Manifest no longer matches submission receipt')
    if sha(out/'prompt.txt')!=manifest['promptSha256'] or tool['prompt']!=(out/'prompt.txt').read_text(): raise ValueError('Prepared prompt changed')
    if tool.get('transparent_background')!=manifest.get('transparentBackground',bool(manifest['request'].get('transparentBackground',False))):
        raise ValueError('Prepared background setting changed')
    if set(tool)-{'prompt','transparent_background','referenced_image_paths'}: raise ValueError('Unexpected tool arguments')
    paths=[]
    for r in manifest['references']:
        p=inside(out,r['file'])
        if sha(p)!=r['sha256']: raise ValueError('Prepared reference changed')
        paths.append(str(p))
    if manifest.get('materialSheet'):
        record=manifest['materialSheet']
        layout_path=inside(out,record['file'])
        if sha(layout_path)!=record['sha256']: raise ValueError('Material layout changed')
        layout=read(layout_path)
        material_ref=next((r for r in manifest['references'] if r['id']=='material-selection'),None)
        saved_settings=manifest['request']['settings']
        saved_materials=saved_settings.get('materials',{})
        saved_ids=([saved_materials.get('base'), *saved_materials.get('accents',[])] if saved_materials.get('mode')=='selected' else []) if saved_settings.get('settingsVersion') in (2, 3) else saved_settings.get('materialIds')
        if layout.get('schemaVersion')!=1 or layout.get('orderedIds')!=saved_ids or not material_ref or layout.get('sheetSha256')!=material_ref['sha256']:
            raise ValueError('Material sheet selection/layout mismatch')
    # Resolve portable copies at their current location, including after transfer.
    if paths: tool['referenced_image_paths']=paths
    else: tool.pop('referenced_image_paths',None)
    return tool


def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('--request',required=True);p.add_argument('--output',required=True);p.add_argument('--quiet',action='store_true')
    p=sub.add_parser('verify');p.add_argument('--execution',required=True)
    p.add_argument('--expected-manifest-sha256');p.add_argument('--allow-legacy',action='store_true')
    p=sub.add_parser('record-submission');p.add_argument('--execution',required=True);p.add_argument('--arguments',required=True)
    p.add_argument('--expected-manifest-sha256');p.add_argument('--allow-legacy',action='store_true')
    handle=p.add_mutually_exclusive_group(required=True);handle.add_argument('--tool-call-id');handle.add_argument('--execution-handle')
    handle.add_argument('--generated-file',help='Actual local file returned by imagegen when no tool/cell ID was exposed')
    args=ap.parse_args()
    if args.command=='prepare': result=prepare(ROOT,read(args.request),Path(args.output).resolve())
    else:
        out=Path(args.execution).resolve(); result=verify(out,args.expected_manifest_sha256,args.allow_legacy)
        if not args.expected_manifest_sha256:
            import sys
            print('LEGACY VERIFICATION: no externally pinned request/version/recipe integrity',file=sys.stderr)
        if args.command=='record-submission':
            if read(args.arguments)!=result: raise ValueError('Actual tool arguments differ from prepared execution')
            receipt=out/'submission.json'
            if receipt.exists(): raise ValueError('Submission receipt already exists')
            observed_id=args.tool_call_id or args.execution_handle or args.generated_file
            if not observed_id or not observed_id.strip(): raise ValueError('Observed handle must not be empty')
            result={'status':'submitted-unreviewed','verificationLevel':'external-manifest-pin' if args.expected_manifest_sha256 else 'legacy-unpinned','toolCallId':args.tool_call_id,'imagegenCallId':args.tool_call_id,'observedHandle':{'type':'imagegen-tool-call' if args.tool_call_id else 'functions-exec-cell','id':observed_id},'arguments':result,'manifestSha256':sha(out/'manifest.json')}
            if args.generated_file:
                generated=Path(args.generated_file).resolve()
                if not generated.is_file(): raise ValueError('Generated file does not exist')
                result['observedHandle']={'type':'generated-artifact','id':str(generated),'sha256':sha(generated)}
                result['evidenceLimit']='Returned artifact recorded; no imagegen call ID was exposed. This receipt does not independently prove external execution or visual quality.'
            dump(receipt,result)
    if args.command=='prepare' and args.quiet:
        result={'status':result['status'],'execution':str(Path(args.output).resolve()),'promptSha256':result['promptSha256'],'referenceCount':len(result['references']),'manifestSha256':result['manifestSha256']}
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
    try: main()
    except (ValueError,KeyError,FileNotFoundError) as e: raise SystemExit(str(e))
