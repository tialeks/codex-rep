#!/usr/bin/env python3
"""Quiet request listener and explicit request lifecycle commands."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import time
import uuid
from presets import data_root, identifier
import hashlib
import re
from prepare_generation import verify
from review_result import validate as validate_review
from history import archive
from serve_presets import write_json, consumer_status


def consumer_lease(root, consumer, action='renew', ttl=120):
    identifier(consumer)
    if not 10 <= ttl <= 300:raise ValueError('Lease TTL must be 10–300 seconds')
    root.mkdir(parents=True,exist_ok=True)
    with (root/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        current=consumer_status(root)
        if current['active'] and current['id'] != consumer:raise ValueError('Another consumer owns the active lease')
        try:previous=json.loads((root/'consumer.json').read_text())
        except (OSError,ValueError):previous={}
        token=previous.get('token') if current['active'] and current['id']==consumer else None
        value={'id':consumer,'expiresAt':time.time()+ttl if action=='renew' else 0,'token':token or uuid.uuid4().hex}
        write_json(root/'consumer.json',value)
        return value


def claim(root, consumer=None, expected_token=None):
    root.mkdir(parents=True,exist_ok=True)
    with (root/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        lease=consumer_status(root)
        if not consumer or not lease['active'] or lease['id'] != consumer:return None
        if expected_token is not None and json.loads((root/'consumer.json').read_text()).get('token') != expected_token:return None
        queued=[]
        for path in (root/'requests').glob('*.json'):
            try:
                row=json.loads(path.read_text())
                if not isinstance(row,dict) or not {'id','status','createdAt','request'}.issubset(row):continue
                if not isinstance(row['createdAt'],(int,float)) or not isinstance(row['request'].get('settings'),dict):continue
                if row['status']=='queued':queued.append((row['createdAt'],path,row))
            except (OSError,ValueError,TypeError,AttributeError):continue
        if not queued:return None
        _,path,row=min(queued,key=lambda value:value[0])
        row.update(status='running',claimedAt=time.time(),workerPid=os.getpid())
        write_json(path,row)
        return dict(row,requestFile=str(path))


def transition(root, request_id, action, *, error=None, execution=None, file=None, pin=None, review=None):
    identifier(request_id)
    root.mkdir(parents=True, exist_ok=True)
    with (root/'worker.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = root/'requests'/(request_id+'.json')
        row = json.loads(path.read_text())
        if row['status'] not in ('queued', 'running'): raise ValueError('Request is already terminal')
        if action == 'complete':
            if row['status'] != 'running': raise ValueError('Claim request before completing')
            if not all((execution, file, pin, review)): raise ValueError('Completion needs execution, file, review and trusted manifest pin')
            if not re.fullmatch('[a-f0-9]{64}', pin): raise ValueError('Expected trusted SHA256 manifest pin')
            execution = Path(execution).resolve()
            arguments = verify(execution, pin)
            receipt = json.loads((execution/'submission.json').read_text())
            sha = hashlib.sha256(Path(file).read_bytes()).hexdigest()
            observed = receipt.get('observedHandle', {})
            if receipt.get('manifestSha256') != pin or receipt.get('arguments') != arguments or observed.get('type') != 'generated-artifact' or observed.get('sha256') != sha:
                raise ValueError('Output and submission receipt mismatch')
            manifest = json.loads((execution/'manifest.json').read_text())
            if manifest['request']['settings'] != row['request']['settings']:
                raise ValueError('Execution settings differ from queued snapshot')
            checked = validate_review(execution, file, review, pin)
            if checked['reviewStatus'] == 'fail': raise ValueError('Failed review cannot complete a request')
            row['reviewStatus'] = checked['reviewStatus']
            row['reviewFile'] = str(Path(review).resolve())
            storage_root=root.parent.parent if root.parent.name=='sessions' else root
            archived,directory=archive(storage_root,row,execution,file,review,pin)
            row['historyId']=archived['id']
            row.update(status='completed', result={'file': str(directory/'result.png'), 'sha256': sha, 'execution': str(Path(execution).resolve()), 'manifestSha256': pin})
        elif action == 'cancel': row['status'] = 'cancelled'
        elif action == 'fail':
            if not error: raise ValueError('Failure needs a reason')
            row.update(status='failed', error=str(error)[:1000])
        else: raise ValueError('Unknown lifecycle action')
        row['completedAt'] = time.time()
        write_json(path,row)
        return row


def active_wait_lease(root, consumer, ttl, expected_token=None):
    """Renew only the active lease captured by this bounded wait, under claim lock."""
    with (root/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        current=consumer_status(root)
        if not current['active'] or current['id'] != consumer:return None
        value=json.loads((root/'consumer.json').read_text())
        if expected_token is not None and value.get('token') != expected_token:return None
        if not value.get('token') or value['expiresAt'] < time.time()+ttl/2:
            value.setdefault('token',uuid.uuid4().hex)
            value['expiresAt']=time.time()+ttl
            write_json(root/'consumer.json',value)
        return value['token']


def listen(root, consumer, *, once=False, wait=None, ttl=120):
    if wait is not None and (once or not 0 < wait <= 45):
        raise ValueError('--wait must be greater than 0 and at most 45 seconds; cannot combine with --once')
    if not 10 <= ttl <= 300:raise ValueError('Lease TTL must be 10–300 seconds')
    root.mkdir(parents=True,exist_ok=True)
    deadline=time.monotonic()+wait if wait is not None else None
    token=None
    try:
        while True:
            if deadline is not None:
                token=active_wait_lease(root,consumer,ttl,token)
                if token is None:return {'job':None,'reason':'consumer-lease-expired'}
            else:
                lease=consumer_status(root)
                if not lease['active'] or lease['id']!=consumer:
                    return {'job':None,'reason':'consumer-lease-expired'}
            row=claim(root,consumer,token)
            if row is not None:return row
            if once:return {'job':None}
            if deadline is not None and time.monotonic()>=deadline:
                return {'job':None,'reason':'wait-timeout'}
            write_json(root/'listener.json', {'pid':os.getpid(),'updatedAt':time.time(),'consumer':consumer})
            time.sleep(min(.5,max(0,deadline-time.monotonic())) if deadline is not None else .5)
    finally:
        try:
            path=root/'listener.json'
            if json.loads(path.read_text()).get('pid')==os.getpid():path.unlink()
        except (OSError,ValueError):pass


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--key',required=True);p.add_argument('--once',action='store_true')
    p.add_argument('--action',choices=('listen','cancel','fail','complete','renew','detach','heartbeat'),default='listen')
    p.add_argument('--id');p.add_argument('--error');p.add_argument('--execution');p.add_argument('--file');p.add_argument('--manifest-sha256');p.add_argument('--review')
    p.add_argument('--consumer');p.add_argument('--ttl',type=int,default=120)
    p.add_argument('--wait',type=float,help='Quiet bounded wait, at most 45 seconds; keeps the same active lease alive')
    a=p.parse_args();root=data_root()/'sessions'/identifier(a.key)
    if a.action=='heartbeat':
        if not a.consumer:p.error('--consumer is required')
        if not 10 <= a.ttl <= 300:p.error('Lease TTL must be 10–300 seconds')
        root.mkdir(parents=True,exist_ok=True)
        active=active_wait_lease(root,a.consumer,a.ttl) is not None
        print(json.dumps({'active':active}));return
    if a.action in ('renew','detach'):
        if not a.consumer:p.error('--consumer is required')
        print(json.dumps(consumer_lease(root,a.consumer,a.action,a.ttl)));return
    if a.action != 'listen':
        if not a.id: p.error('--id is required')
        print(json.dumps(transition(root,a.id,a.action,error=a.error,execution=a.execution,file=a.file,pin=a.manifest_sha256,review=a.review),ensure_ascii=False));return
    if not a.consumer:p.error('--consumer is required for listening')
    if a.wait is not None and (a.once or not 0 < a.wait <= 45):p.error('--wait accepts 0 < seconds <= 45 and cannot combine with --once')
    print(json.dumps(listen(root,a.consumer,once=a.once,wait=a.wait,ttl=a.ttl),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
