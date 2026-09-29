#!/usr/bin/env python3
"""Local controls: immutable requests, uploaded references and settings persistence."""
import fcntl
import argparse
import base64
import hashlib
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import math
import os
from pathlib import Path
import secrets
import tempfile
import time
import uuid
from PIL import Image
from presets import data_root, identifier, favorite, read_store, import_rows, ensure_bundled_library
import palettes
from material_library import settings_material_ids
from urllib.parse import urlsplit, parse_qs
from history import public_history, read_entry, archived_preset, verified_archive


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream: json.dump(value, stream, ensure_ascii=False)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp): os.unlink(temp)


def session_token(root, port):
    """Keep open studio tabs usable across a local server restart."""
    path=root/('server-token-'+str(port)+'.json')
    try:
        value=json.loads(path.read_text())['token']
        if isinstance(value,str) and len(value)>=32:return value
    except (OSError,ValueError,KeyError,TypeError):pass
    return secrets.token_urlsafe(32)


def upload_reference(root, body):
    raw = base64.b64decode(body['data'], validate=True)
    if len(raw) > 15_000_000: raise ValueError('Изображение больше 15 МБ')
    with Image.open(io.BytesIO(raw)) as source:
        if source.format not in ('PNG','JPEG','WEBP'): raise ValueError('Нужен PNG, JPEG или WebP')
        if source.width * source.height > 40_000_000: raise ValueError('Изображение слишком большое')
        source.load()
        extension = {'PNG':'.png','JPEG':'.jpg','WEBP':'.webp'}[source.format]
        thumbnail=source.convert('RGB');thumbnail.thumbnail((256,256))
        buffer=io.BytesIO();thumbnail.save(buffer,format='JPEG',quality=80)
    sha = hashlib.sha256(raw).hexdigest()
    path = root/'references'/(sha+extension);path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists(): path.write_bytes(raw)
    return {'path':str(path),'name':Path(body.get('name','Референс')).name[:150], 'sha256':sha,
            'thumbnail':'data:image/jpeg;base64,'+base64.b64encode(buffer.getvalue()).decode()}


def enqueue(root, message):
    if not isinstance(message,dict): raise ValueError('Expected request object')
    text=message.get('prompt','')
    if not isinstance(text,str) or len(text)>100000: raise ValueError('Invalid request')
    prefix, separator, raw = text.partition('\n')
    if not separator or not prefix.startswith('reference-style-3d:'): raise ValueError('Expected plugin request')
    payload=json.loads(raw)
    if not isinstance(payload,dict): raise ValueError('Expected settings object')
    if payload.get('schemaVersion')!=1 or not isinstance(payload.get('settings'),dict): raise ValueError('Invalid settings snapshot')
    if 'operation' in payload: raise ValueError('Use library endpoint for operations')
    settings=payload['settings']
    if 'operation' not in payload:
        from compile_settings import compile_settings
        compile_settings(Path(__file__).resolve().parents[1],settings)
        ref=settings.get('reference',{})
        if ref.get('facets'):
            image=ref.get('image')
            if not image: raise ValueError('Прикрепите референс для выбранных свойств')
            file=Path(image['path']).resolve()
            if (root/'references').resolve() not in file.parents or hashlib.sha256(file.read_bytes()).hexdigest()!=image['sha256']:
                raise ValueError('Reference binding mismatch')
    request_id=uuid.uuid4().hex
    record={'id':request_id,'status':'queued','createdAt':time.time(),'message':text,'request':payload}
    write_json(root/'requests'/(request_id+'.json'),record)
    return {'id':request_id,'status':'queued'}


def repeat_history(session_root, archive_root, item_id):
    row,directory,manifest,settings,_=verified_archive(archive_root,item_id)
    image=None
    reference=settings.get('reference',{})
    if reference.get('facets'):
        guides=[entry for entry in manifest['references'] if entry.get('role')=='GUIDANCE REFERENCE']
        if len(guides)!=1:raise ValueError('В архиве нет однозначно привязанного референса. Загрузите его заново.')
        guide=guides[0]
        binding=reference.get('image')
        if not binding or guide.get('imageBinding')!=binding or guide['sha256']!=binding['sha256']:
            raise ValueError('Привязка референса в архиве не совпадает со снимком.')
        from prepare_generation import inside
        raw=inside(directory/'evidence',guide['file']).read_bytes()
        image=upload_reference(session_root,{'data':base64.b64encode(raw).decode(),'name':binding['name']})
        settings['reference']['image']={key:image[key] for key in ('path','name','sha256')}
    return {'settings':settings,'referenceImage':image}


def normalize_material_set(materials):
    if not isinstance(materials,dict) or set(materials)!={'mode','base','accents'} or materials.get('mode')!='selected':
        raise ValueError('Выберите основу и акценты для своего набора.')
    accents=materials['accents']
    if not isinstance(accents,list) or any(not isinstance(item,str) for item in accents):
        raise ValueError('В наборе есть некорректные материалы.')
    if materials['base'] in accents:raise ValueError('Основной материал не должен повторяться в акцентах.')
    value={'mode':'selected','base':materials['base'],'accents':list(dict.fromkeys(accents))}
    settings_material_ids(Path(__file__).resolve().parents[1],{'settingsVersion':3,'materials':value})
    return value


def material_set_operation(root,operation):
    root.mkdir(parents=True,exist_ok=True)
    store=root/'material-sets.json'
    with (root/'material-sets.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        try:data=json.loads(store.read_text())
        except FileNotFoundError:data={'schemaVersion':1,'materialSets':[]}
        if not isinstance(data,dict) or data.get('schemaVersion')!=1 or not isinstance(data.get('materialSets'),list):
            raise ValueError('Не удалось прочитать библиотеку наборов. Файл сохранён без изменений.')
        rows=data['materialSets'];ids=set();names=set()
        for row in rows:
            if not isinstance(row,dict) or set(row)!={'id','name','materials'}:raise ValueError('Не удалось прочитать один из сохранённых наборов.')
            identifier(row['id']);name=palettes.normalize_name(row['name'])
            if row['id'] in ids or name.casefold() in names:raise ValueError('В библиотеке есть повторяющиеся наборы.')
            ids.add(row['id']);names.add(name.casefold());normalize_material_set(row['materials'])
        action=operation['action'];changed=False
        if action=='save_material_set':
            name=palettes.normalize_name(operation['name']);materials=normalize_material_set(operation['materials'])
            same=next((r for r in rows if r['name'].casefold()==name.casefold()),None)
            if same:
                if same['materials']!=materials:raise ValueError('Набор с таким именем уже существует. Выберите другое имя.')
            else:
                rows.append({'id':uuid.uuid4().hex,'name':name,'materials':materials});changed=True
        elif action=='delete_material_set':
            ident=identifier(operation['id']);kept=[r for r in rows if r['id']!=ident]
            changed=len(kept)!=len(rows);data['materialSets']=kept
        if changed:
            write_json(store,data)
            if json.loads(store.read_text())!=data:raise ValueError('Не удалось проверить сохранение набора. Повторите попытку.')
        return {'ok':True,'materialSets':data['materialSets']}


def library_operation(root, operation):
    if not isinstance(operation,dict): raise ValueError('Expected library operation')
    action = operation.get('action')
    if action in ('save_material_set','delete_material_set','load_material_sets'):
        return material_set_operation(root,operation)
    if action == 'save_history_preset':
        row,directory=read_entry(root,operation['id'])
        entry,image_hash=archived_preset(root,operation['id'],operation.get('name'))
        changed,_=import_rows(root,[entry],expected_images={entry['id']:image_hash})
        return {'ok':True,'presetId':entry['id'],'changed':changed,'preset':{key:entry[key] for key in ('id','name','settings','source')} | {'thumbnail':'/history-image/'+row['id']}}
    if action == 'set_favorite':
        if type(operation.get('favorite')) is not bool: raise ValueError('Expected favorite boolean')
        _, data = favorite(root, operation['id'], operation['favorite'])
        return {'ok': True, 'favorites': data['favorites']}
    if action in ('save_palette', 'load_palette_library'):
        store = root / 'palettes.json'
        with palettes.locked_store(store):
            data = palettes.read_file(store, missing_ok=True)
            if action == 'save_palette':
                incoming = {'id': uuid.uuid4().hex, 'name': palettes.normalize_name(operation['name']), 'colors': palettes.normalize_colors(operation['colors'])}
                data = palettes.merge(data['palettes'], [incoming])
                palettes.atomic_write(store, data)
                if palettes.read_file(store) != data: raise ValueError('Palette readback mismatch')
        return {'ok': True, 'palettes': data['palettes']}
    if action == 'load_preset_library':
        return {'ok': True, 'favorites': read_store(root)['favorites']}
    raise ValueError('Эта операция требует выбора результата в чате')


def remove_request(root, request_id):
    identifier(request_id)
    root.mkdir(parents=True, exist_ok=True)
    with (root/'worker.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = root/'requests'/(request_id+'.json')
        row = json.loads(path.read_text())
        running = row['status'] == 'running'
        if row['status'] == 'queued':
            row.update(status='cancelled', completedAt=time.time())
        row['removedAt'] = time.time()
        write_json(path, row)
    return {'ok': True, 'running': running}


def consumer_status(root):
    try:
        value=json.loads((root/'consumer.json').read_text())
        expiry=float(value['expiresAt'])
        if not math.isfinite(expiry):raise ValueError('Invalid lease expiry')
        return {'active':expiry > time.time(), 'expiresAt':expiry, 'id':value['id']}
    except (OSError,ValueError,KeyError,TypeError):return {'active':False,'expiresAt':None,'id':None}


def disconnect(root):
    """Revoke acceptance atomically; running and queued jobs remain untouched."""
    root.mkdir(parents=True,exist_ok=True)
    with (root/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        current=consumer_status(root)
        write_json(root/'consumer.json',{'id':current['id'],'expiresAt':0,'token':uuid.uuid4().hex})
    return {'ok':True,'consumer':{'active':False}}


def validate_state(state):
    if not isinstance(state,dict):raise ValueError('Expected settings snapshot')
    model=state.get('modelContent')
    if not isinstance(model,dict) or model.get('panel')!='reference-style-3d-v6' or not isinstance(model.get('settings'),dict):
        raise ValueError('Invalid studio settings snapshot')
    if 'privateContent' in state and not isinstance(state['privateContent'],dict):raise ValueError('Invalid private settings')
    return state


def restored_state(root):
    try:state=validate_state(json.loads((root/'state.json').read_text()))
    except (OSError,ValueError):return {'state':None,'referenceImage':None}
    reference=state['modelContent']['settings'].get('reference')
    image=reference.get('image') if isinstance(reference,dict) else None
    result={'state':state,'referenceImage':None}
    if image:
        try:
            path=Path(image['path']).resolve()
            if (root/'references').resolve() not in path.parents:raise ValueError('Invalid reference path')
            raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=image['sha256']:raise ValueError('Reference changed')
            result['referenceImage']=upload_reference(root,{'data':base64.b64encode(raw).decode(),'name':image['name']})
        except (OSError,ValueError,KeyError,TypeError):pass
    return result


def queue_status(root):
    rows = []
    unreadable = 0
    for path in (root / 'requests').glob('*.json'):
        try:
            row = json.loads(path.read_text())
            if not isinstance(row,dict) or not {'id','status','createdAt','request'}.issubset(row): raise ValueError('Invalid job')
            if not isinstance(row['createdAt'],(int,float)) or not isinstance(row['request'].get('settings'),dict): raise ValueError('Invalid snapshot')
        except (OSError,ValueError,TypeError,AttributeError):
            unreadable += 1
            continue
        if row.get('removedAt'): continue
        public = {key: row[key] for key in ('id', 'status', 'createdAt', 'error', 'completedAt', 'reviewStatus') if key in row}
        public['topic'] = row['request']['settings'].get('topic', '')
        if row.get('result') and row['status']=='completed': public['resultUrl']='/result/'+row['id']
        rows.append(public)
    consumer = consumer_status(root)
    waiting = False
    try:
        listener = json.loads((root / 'listener.json').read_text())
        if consumer['active'] and listener.get('consumer') == consumer['id'] and time.time() - listener['updatedAt'] < 3:
            os.kill(listener['pid'], 0)
            waiting = True
    except (OSError, KeyError, ValueError, TypeError, OverflowError): pass
    ordered = sorted(rows, key=lambda row: row['createdAt'], reverse=True)
    active = [row for row in ordered if row['status'] in ('queued','running')]
    terminal = [row for row in ordered if row['status'] not in ('queued','running')][:50]
    storage_root = root.parent.parent if root.parent.name=='sessions' else root
    revision = []
    for path in (storage_root/'generations').glob('*/metadata.json'):
        try: revision.append((path.parent.name,path.stat().st_mtime_ns))
        except OSError: continue
    history_revision = hashlib.sha256(json.dumps(sorted(revision)).encode()).hexdigest()
    return {'requests': active+terminal, 'historyRevision':history_revision, 'unreadableRequests':unreadable, 'listener': {'waiting': waiting}, 'consumer': {'active':consumer['active'],'expiresAt':consumer['expiresAt']}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',required=True)
    parser.add_argument('--key',required=True)
    parser.add_argument('--port',type=int,default=4397)
    args=parser.parse_args();identifier(args.key)
    directory=Path(args.directory).expanduser().resolve()
    plugin=Path(__file__).resolve().parents[1]
    if directory == plugin or plugin in directory.parents:
        parser.error('Studio output belongs outside the plugin')
    ensure_bundled_library()
    root=data_root()/'sessions'/args.key
    token=session_token(root,args.port);origin=f'http://127.0.0.1:{args.port}'
    directory.mkdir(parents=True, exist_ok=True)
    script=(Path(__file__).resolve().parents[1]/'ui/browser-bridge.js').read_text().replace('__SESSION_TOKEN__',json.dumps(token)).replace('__SESSION_KEY__',json.dumps(args.key))

    class Handler(SimpleHTTPRequestHandler):
        def do_POST(self):
            if (self.path not in ('/request','/reference','/state','/library','/remove-request','/repeat-history','/disconnect') or self.headers.get('Host')!=f'127.0.0.1:{args.port}' or self.headers.get('Origin')!=origin or self.headers.get('X-Session-Token')!=token or self.headers.get('Content-Type')!='application/json'):
                self.send_error(403);return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=21_000_000: raise ValueError('Invalid request size')
                body=json.loads(self.rfile.read(length))
                if self.path=='/disconnect': result=disconnect(root)
                elif self.path=='/reference': result=upload_reference(root,body)
                elif self.path=='/repeat-history': result=repeat_history(root,data_root(),body['id'])
                elif self.path=='/remove-request': result=remove_request(root,body['id'])
                elif self.path=='/library': result=library_operation(data_root(),body)
                elif self.path=='/state':
                    if not isinstance(body,dict): raise ValueError('Expected settings object')
                    if length>100000: raise ValueError('Settings too large')
                    write_json(root/'state.json',validate_state(body));result={'ok':True}
                else: result=enqueue(root,body)
                code=200
            except (ValueError,OSError,KeyError,TypeError,palettes.PaletteError) as error:
                result={'error':str(error)};code=400
            data=json.dumps(result,ensure_ascii=False).encode();self.send_response(code)
            self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)))
            self.end_headers();self.wfile.write(data)
        def end_headers(self):
            self.send_header('Cache-Control', 'no-store' if self.path in ('/status','/browser-bridge.js') else 'no-cache')
            super().end_headers()
        def do_GET(self):
            route=urlsplit(self.path)
            if route.path=='/history':
                try:
                    query=parse_qs(route.query)
                    result=public_history(data_root(),int(query.get('page',['1'])[0]),int(query.get('pageSize',['12'])[0]))
                    data=json.dumps(result,ensure_ascii=False).encode()
                    self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
                except (ValueError,TypeError):self.send_error(400)
                return
            if route.path.startswith('/history-image/'):
                try:
                    row,folder=read_entry(data_root(),route.path.removeprefix('/history-image/'))
                    data=(folder/'result.png').read_bytes()
                    if hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('Image changed')
                    self.send_response(200);self.send_header('Content-Type','image/png');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
                except (ValueError,OSError,KeyError):self.send_error(404)
                return
            if self.path.startswith('/result/'):
                try:
                    request_id=identifier(self.path[len('/result/'):])
                    row=json.loads((root/'requests'/(request_id+'.json')).read_text())
                    if row['status']!='completed': raise ValueError('Result is not ready')
                    data=Path(row['result']['file']).read_bytes()
                    if hashlib.sha256(data).hexdigest()!=row['result']['sha256']: raise ValueError('Result changed')
                    self.send_response(200);self.send_header('Content-Type','image/png');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
                except (ValueError,OSError,KeyError):self.send_error(404)
                return
            if self.path=='/browser-bridge.js':
                data=script.replace('__SERVER_RESTORE__',json.dumps(restored_state(root),ensure_ascii=False)).encode()
                self.send_response(200);self.send_header('Content-Type','application/javascript; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
            if self.path=='/status':
                data=json.dumps(queue_status(root)).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(data);return
            super().do_GET()

    # Bind before publishing the session token; a port conflict must not invalidate a live bridge.
    server = ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(directory)))
    try:
        token_path=root/('server-token-'+str(args.port)+'.json')
        write_json(token_path,{'token':token})
        token_path.chmod(0o600)
        (directory/'browser-bridge.js').write_text(script.replace('__SERVER_RESTORE__','{"state":null,"referenceImage":null}'))
        print(json.dumps({'url':origin,'session':str(root)}),flush=True)
        server.serve_forever()
    finally:
        server.server_close()


if __name__=='__main__':main()
