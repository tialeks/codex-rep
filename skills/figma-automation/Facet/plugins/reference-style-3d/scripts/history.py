#!/usr/bin/env python3
"""Durable, verified generation archive outside the plugin package."""
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
import time
from presets import data_root, identifier, settings_only, image_preview, name
from prepare_generation import inside, verify
from review_result import validate


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_entry(root, item_id, verify_image=True):
    identifier(item_id)
    directory=(Path(root)/'generations'/item_id).resolve()
    if directory.parent != (Path(root)/'generations').resolve():raise ValueError('Invalid archive path')
    row=json.loads((directory/'metadata.json').read_text())
    if not isinstance(row,dict) or row.get('id')!=item_id:raise ValueError('Archive identity mismatch')
    created=row.get('createdAt')
    if type(created) not in (int,float) or not math.isfinite(created) or not isinstance(row.get('topic'),str) or row.get('reviewStatus') not in ('pass','limited','fail'):
        raise ValueError('Invalid archive metadata')
    for filename,key in [('settings.json','settingsSha256'),('review.json','reviewSha256')]:
        if digest(directory/filename)!=row[key]:raise ValueError('Archive metadata changed')
    if row.get('schemaVersion',1)>=2 and digest(directory/'request.json')!=row['requestSha256']:raise ValueError('Archive request changed')
    if verify_image and digest(directory/'result.png')!=row['sha256']:raise ValueError('Archive image changed')
    return row,directory


def copy_evidence(execution, destination, pin):
    execution=Path(execution).resolve()
    verify(execution,pin)
    manifest=json.loads((execution/'manifest.json').read_text())
    files={'manifest.json','prompt.txt','tool-request.json','submission.json'}
    files.update(record['file'] for record in manifest['references'])
    if manifest.get('materialSheet'):files.add(manifest['materialSheet']['file'])
    hashes={}
    for relative in sorted(files):
        source=inside(execution,relative)
        target=destination/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
        hashes[relative]=digest(target)
        if hashes[relative]!=digest(source):raise ValueError('Evidence changed while archiving')
    verify(destination,pin)
    return hashes


def verified_archive(root, item_id):
    row,directory=read_entry(root,item_id)
    if row.get('schemaVersion',1)<2:
        raise ValueError('Archive needs its original execution imported once before saving a preset')
    execution=directory/'evidence'
    for relative,expected in row['evidenceSha256'].items():
        if digest(inside(execution,relative))!=expected:raise ValueError('Archived execution evidence changed')
    verify(execution,row['manifestSha256'])
    manifest=json.loads((execution/'manifest.json').read_text())
    receipt=json.loads((execution/'submission.json').read_text())
    original_arguments=json.loads((execution/'tool-request.json').read_text())
    # Keep the submitted absolute paths as evidence. verify checks the portable
    # local copies independently; rewriting the original receipt would forge it.
    observed=receipt.get('observedHandle',{})
    image_hash,_=image_preview(directory/'result.png')
    if receipt.get('manifestSha256')!=row['manifestSha256'] or receipt.get('arguments')!=original_arguments or observed.get('type')!='generated-artifact' or observed.get('sha256')!=image_hash:
        raise ValueError('Archived PNG and original submission do not share verified evidence')
    settings=json.loads((directory/'settings.json').read_text())
    request=json.loads((directory/'request.json').read_text())
    if manifest['request']['settings']!=settings or request['settings']!=settings:raise ValueError('Archived request and execution snapshots differ')
    return row,directory,manifest,settings,image_hash


def archived_preset(root, item_id, label=None):
    row,directory,manifest,settings,image_hash=verified_archive(root,item_id)
    settings=settings_only(settings)
    identity=hashlib.sha256((image_hash+json.dumps(settings,sort_keys=True)).encode()).hexdigest()[:24]
    entry=dict(id='personal-'+identity,name=name(label or row['topic']),settings=settings,file=str(directory/'result.png'),source='personal')
    return entry,image_hash


def archive(root, job, execution, file, review, pin):
    checked=validate(execution,file,review,pin,allow_failed_output=True)
    manifest=json.loads((Path(execution)/'manifest.json').read_text())
    settings=job['request']['settings']
    if manifest['request']['settings']!=settings:raise ValueError('Queued snapshot differs from execution')
    item_id=identifier(job['id'])+'-'+checked['sha256'][:16]
    library=Path(root).resolve()/'generations';library.mkdir(parents=True,exist_ok=True)
    with (library/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        target=library/item_id
        if target.exists():
            row,directory=read_entry(root,item_id)
            if json.loads((directory/'settings.json').read_text())!=settings:raise ValueError('Immutable history settings differ')
            if row.get('schemaVersion',1)<2:
                evidence=directory/'evidence'
                evidence_hashes=copy_evidence(execution,evidence,pin)
                row.update(schemaVersion=2,sourceExecution=str(Path(execution).resolve()),execution=str(evidence),evidenceSha256=evidence_hashes,requestSha256=digest(directory/'request.json'))
                pending=directory/'metadata.pending.json'
                pending.write_text(json.dumps(row,ensure_ascii=False,indent=2))
                os.replace(pending,directory/'metadata.json')
            return row,directory
        temp=Path(tempfile.mkdtemp(prefix='.pending-',dir=library))
        try:
            shutil.copyfile(file,temp/'result.png')
            shutil.copyfile(review,temp/'review.json')
            (temp/'settings.json').write_text(json.dumps(settings,ensure_ascii=False,indent=2))
            (temp/'request.json').write_text(json.dumps(job['request'],ensure_ascii=False,indent=2))
            evidence_hashes=copy_evidence(execution,temp/'evidence',pin)
            row=dict(schemaVersion=2,evidenceSha256=evidence_hashes,requestSha256=digest(temp/'request.json'),sourceExecution=str(Path(execution).resolve()),id=item_id,jobId=job['id'],createdAt=job.get('completedAt',time.time()),topic=settings.get('topic',''),reviewStatus=checked['reviewStatus'],sha256=checked['sha256'],settingsSha256=digest(temp/'settings.json'),reviewSha256=digest(temp/'review.json'),execution=str(target/'evidence'),manifestSha256=pin,sourceFile=str(Path(file).resolve()))
            if digest(temp/'result.png')!=row['sha256']:raise ValueError('Source changed while archiving')
            (temp/'metadata.json').write_text(json.dumps(row,ensure_ascii=False,indent=2))
            os.rename(temp,target)
        finally:
            if temp.exists():shutil.rmtree(temp)
    return row,target


def public_history(root, page=1, page_size=12):
    if type(page)!=int or page<1 or page_size not in (12,16,24):raise ValueError('Invalid history page')
    entries=[]
    for directory in (Path(root)/'generations').glob('*'):
        if not directory.is_dir() or directory.name.startswith('.'):continue
        try:
            row,_=read_entry(root,directory.name,verify_image=False)
            entries.append(row)
        except (ValueError,OSError,KeyError,TypeError):continue
    entries.sort(key=lambda row:(row['createdAt'],row['id']),reverse=True)
    total=len(entries);page=min(page,max(1,(total+page_size-1)//page_size))
    items=[]
    for row in entries[(page-1)*page_size:page*page_size]:
        _,directory=read_entry(root,row['id'],False)
        review=json.loads((directory/'review.json').read_text())
        notes=[check['observation'][:300] for check in review.get('checks',{}).values() if isinstance(check,dict) and check.get('status') in ('limited','fail') and isinstance(check.get('observation'),str)]
        items.append(dict(id=row['id'],topic=row['topic'],createdAt=row['createdAt'],reviewStatus=row['reviewStatus'],notes=list(dict.fromkeys(notes))[:3],thumbnail='/history-image/'+row['id'],settings=json.loads((directory/'settings.json').read_text())))
    return dict(items=items,total=total,page=page,pageSize=page_size)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--import-job');p.add_argument('--import-attempt')
    p.add_argument('--execution');p.add_argument('--file');p.add_argument('--review');p.add_argument('--manifest-sha256')
    a=p.parse_args()
    if bool(a.import_job)==bool(a.import_attempt):p.error('Use either --import-job or --import-attempt with a job snapshot path')
    job=json.loads(Path(a.import_job or a.import_attempt).read_text())
    if a.import_attempt:
        if not all((a.execution,a.file,a.review,a.manifest_sha256)):p.error('Attempt requires execution, file, review and trusted manifest pin')
        row,directory=archive(data_root(),job,a.execution,a.file,a.review,a.manifest_sha256)
    else:
        if job['status']!='completed':raise ValueError('Import requires completed job')
        result=job['result'];row,directory=archive(data_root(),job,result['execution'],result['file'],job['reviewFile'],result['manifestSha256'])
    print(json.dumps(dict(id=row['id'],file=str(directory/'result.png'),reviewStatus=row['reviewStatus']),ensure_ascii=False))

if __name__=='__main__':main()
