import base64
import hashlib
from prepare_generation import prepare, verify, ROOT
from review_result import CHECKS
from history import archive, public_history, read_entry
import io
import json
from pathlib import Path
import tempfile
import shutil
import unittest
from unittest.mock import patch
import serve_presets
from PIL import Image
from presets import import_rows
from serve_presets import enqueue, upload_reference, library_operation, queue_status, restored_state, write_json
from listen_requests import claim, transition, consumer_lease, listen, active_wait_lease

class BrowserRequests(unittest.TestCase):
    def test_personal_material_sets_persist_dedupe_and_delete(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);material={'mode':'selected','base':'matte-polymer','accents':['wood','ceramic','wood']}
            saved=library_operation(root,{'action':'save_material_set','name':'  Studio  ','materials':material})
            row=saved['materialSets'][0]
            self.assertEqual(row['name'],'Studio')
            self.assertEqual(row['materials'],{'mode':'selected','base':'matte-polymer','accents':['wood','ceramic']})
            self.assertEqual(library_operation(root,{'action':'load_material_sets'}),saved)
            self.assertEqual(library_operation(root,{'action':'save_material_set','name':'studio','materials':material}),saved)
            with self.assertRaises(ValueError):library_operation(root,{'action':'save_material_set','name':'Studio','materials':dict(material,base='silver-satin')})
            self.assertEqual(library_operation(root,{'action':'delete_material_set','id':row['id']})['materialSets'],[])
            self.assertEqual(library_operation(root,{'action':'load_material_sets'})['materialSets'],[])

    def test_personal_material_sets_reject_invalid_inputs_without_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            valid={'mode':'selected','base':'wood','accents':[]}
            library_operation(root,{'action':'save_material_set','name':'Valid','materials':valid})
            before=(root/'material-sets.json').read_bytes()
            cards=json.loads((ROOT/'assets/materials/catalog.json').read_text())['cards']
            many=[c['id'] for c in cards if c['id']!='wood'][:12]
            for material in [dict(valid,mode='auto'),dict(valid,base='unknown'),dict(valid,accents=['unknown']),dict(valid,accents=['wood']),dict(valid,accents='ceramic'),dict(valid,accents=many)]:
                with self.assertRaises(ValueError):library_operation(root,{'action':'save_material_set','name':'Invalid','materials':material})
                self.assertEqual((root/'material-sets.json').read_bytes(),before)
            (root/'material-sets.json').write_text('{broken')
            with self.assertRaises(ValueError):library_operation(root,{'action':'save_material_set','name':'New','materials':valid})
            self.assertEqual((root/'material-sets.json').read_text(),'{broken')

    def test_cli_heartbeat_after_disconnect_does_not_reconnect(self):
        import listen_requests
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);root=base/'sessions'/'test'
            consumer_lease(root,'worker');serve_presets.disconnect(root)
            before=(root/'consumer.json').read_text()
            with patch.object(listen_requests,'data_root',return_value=base),patch('sys.argv',['listen_requests.py','--key','test','--consumer','worker','--action','heartbeat']),patch('sys.stdout',new_callable=io.StringIO) as out:
                listen_requests.main()
                self.assertEqual(json.loads(out.getvalue()),{'active':False})
            self.assertEqual((root/'consumer.json').read_text(),before)

    def test_wait_renews_near_expiry_without_changing_lease_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with patch('listen_requests.time.time',return_value=100):
                first=consumer_lease(root,'worker',ttl=10)
            with patch('listen_requests.time.time',return_value=106):
                self.assertEqual(active_wait_lease(root,'worker',10,first['token']),first['token'])
                self.assertEqual(json.loads((root/'consumer.json').read_text())['expiresAt'],116)
            with patch('listen_requests.time.time',return_value=117):
                self.assertIsNone(active_wait_lease(root,'worker',10,first['token']))
                self.assertEqual(json.loads((root/'consumer.json').read_text())['expiresAt'],116)

    def test_disconnect_revokes_wait_without_cancelling_jobs(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);consumer_lease(root,'worker')
            for ident,status in [('pending','queued'),('active','running')]:
                write_json(root/'requests'/(ident+'.json'),{'id':ident,'status':status,'createdAt':1,'request':{'settings':{}}})
            token=active_wait_lease(root,'worker',120)
            self.assertEqual(serve_presets.disconnect(root),{'ok':True,'consumer':{'active':False}})
            self.assertIsNone(active_wait_lease(root,'worker',120,token))
            self.assertIsNone(claim(root,'worker',token))
            self.assertEqual(json.loads((root/'requests/pending.json').read_text())['status'],'queued')
            self.assertEqual(json.loads((root/'requests/active.json').read_text())['status'],'running')
            consumer_lease(root,'worker')
            self.assertIsNone(active_wait_lease(root,'worker',120,token))
            self.assertEqual(claim(root,'worker')['id'],'pending')

    def test_bounded_wait_times_out_and_once_never_renews(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);consumer_lease(root,'worker',ttl=10)
            original=(root/'consumer.json').read_text()
            self.assertEqual(listen(root,'worker',once=True),{'job':None})
            self.assertEqual((root/'consumer.json').read_text(),original)
            with patch('listen_requests.time.monotonic',side_effect=[0,0,0,1]),patch('listen_requests.time.sleep'):
                self.assertEqual(listen(root,'worker',wait=1),{'job':None,'reason':'wait-timeout'})
            self.assertFalse((root/'listener.json').exists())
            self.assertTrue(serve_presets.consumer_status(root)['active'])
            for duration in [0,-1,46]:
                with self.assertRaises(ValueError):listen(root,'worker',wait=duration)
            with self.assertRaises(ValueError):listen(root,'worker',wait=1,once=True)

    def test_wait_does_not_revive_expired_detached_or_replaced_lease(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);consumer_lease(root,'worker')
            token=active_wait_lease(root,'worker',120)
            consumer_lease(root,'worker','detach')
            detached=(root/'consumer.json').read_text()
            self.assertIsNone(active_wait_lease(root,'worker',120,token))
            self.assertEqual((root/'consumer.json').read_text(),detached)
            consumer_lease(root,'worker')
            self.assertIsNone(active_wait_lease(root,'worker',120,token))
            write_json(root/'requests'/'one.json',{'id':'one','status':'queued','createdAt':1,'request':{'settings':{}}})
            self.assertIsNone(claim(root,'worker',token))
            self.assertEqual(json.loads((root/'requests/one.json').read_text())['status'],'queued')
            value=json.loads((root/'consumer.json').read_text());value['expiresAt']=0;write_json(root/'consumer.json',value)
            self.assertEqual(listen(root,'worker',wait=1)['reason'],'consumer-lease-expired')
            self.assertEqual(json.loads((root/'consumer.json').read_text())['expiresAt'],0)

    def test_wait_returns_new_job_and_detach_during_sleep_stops(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);consumer_lease(root,'worker')
            def enqueue_after_sleep(_):
                write_json(root/'requests'/'new.json',{'id':'new','status':'queued','createdAt':1,'request':{'settings':{}}})
            with patch('listen_requests.time.sleep',side_effect=enqueue_after_sleep):
                self.assertEqual(listen(root,'worker',wait=1)['id'],'new')
            with patch('listen_requests.time.sleep',side_effect=lambda _:consumer_lease(root,'worker','detach')):
                self.assertEqual(listen(root,'worker',wait=1)['reason'],'consumer-lease-expired')
            self.assertFalse(serve_presets.consumer_status(root)['active'])

    def test_remove_queued_prevents_claim_and_running_is_retained(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);consumer_lease(root,'test-consumer')
            for ident,status in [('pending','queued'),('active','running')]:
                serve_presets.write_json(root/'requests'/(ident+'.json'), {'id':ident,'status':status,'createdAt':1,'request':{'settings':{'topic':'Test'}}})
            self.assertFalse(serve_presets.remove_request(root,'pending')['running'])
            self.assertIsNone(claim(root,'test-consumer'))
            self.assertTrue(serve_presets.remove_request(root,'active')['running'])
            self.assertEqual(queue_status(root)['requests'], [])
            self.assertEqual(json.loads((root/'requests/active.json').read_text())['status'],'running')

    def test_independent_requests_and_claims(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);consumer_lease(root,'test-consumer')
            settings=dict(settingsVersion=3,topic='Shopping',graphicType='group',detailLevel='balanced',arrangement='auto',count=4,camera='three-quarter',creativity=3,whiteBase=False,background='white',palette='natural',effects=[],recognizable=True,materials=dict(mode='auto',base=None,accents=[]))
            message={'prompt':'reference-style-3d: создай PNG.\n'+json.dumps({'schemaVersion':1,'settings':settings})}
            a=enqueue(root,message);b=enqueue(root,message)
            self.assertNotEqual(a['id'],b['id'])
            self.assertEqual(claim(root,'test-consumer')['id'],a['id'])
            self.assertEqual(claim(root,'test-consumer')['id'],b['id'])
            self.assertIsNone(claim(root,'test-consumer'))
            with self.assertRaises(ValueError): transition(root,a['id'],'complete')
            transition(root,a['id'],'cancel')
            with self.assertRaises(ValueError): transition(root,a['id'],'fail',error='late')
            transition(root,b['id'],'fail',error='Generation failed')
            statuses={row['status'] for row in queue_status(root)['requests']}
            self.assertEqual(statuses, {'cancelled','failed'})
    def test_completion_requires_matching_receipt_and_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);consumer_lease(root,'test-consumer')
            settings=dict(settingsVersion=3,topic='A boat',graphicType='object',detailLevel='balanced',arrangement='auto',count=4,camera='front',creativity=3,whiteBase=False,background='white',palette='natural',effects=[],recognizable=True,materials=dict(mode='auto',base=None,accents=[]))
            settings['materials']=dict(mode='selected',base='ceramic',accents=[])
            job=enqueue(root,{'prompt':'reference-style-3d: PNG.\n'+json.dumps({'schemaVersion':1,'settings':settings})})
            claim(root,'test-consumer')
            out=root/'execution';file=root/'result.png'
            Image.new('RGB',(64,64)).save(file)
            manifest=prepare(ROOT,dict(settings=settings,prompt='A boat',referenceMode='prompt'),out)
            pin=manifest['manifestSha256']
            receipt=dict(manifestSha256=pin,arguments=verify(out,pin),observedHandle=dict(type='generated-artifact',sha256='0'*64))
            (out/'submission.json').write_text(json.dumps(receipt))
            review=root/'review.json'
            with self.assertRaisesRegex(ValueError,'receipt mismatch'):transition(root,job['id'],'complete',execution=out,file=file,pin=pin,review=review)
            receipt['observedHandle']['sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
            (out/'submission.json').write_text(json.dumps(receipt))
            with self.assertRaises(OSError):transition(root,job['id'],'complete',execution=out,file=file,pin=pin,review=review)
            checks={key:dict(status='pass',observation='Test fixture: synthetic receipt validation, not visual quality approval.') for key in CHECKS}
            data=dict(status='fail',file=str(file),sha256=receipt['observedHandle']['sha256'],checks=checks)
            review.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'Failed review'):transition(root,job['id'],'complete',execution=out,file=file,pin=pin,review=review)
            data['status']='limited';review.write_text(json.dumps(data))
            done=transition(root,job['id'],'complete',execution=out,file=file,pin=pin,review=review)
            self.assertEqual(done['reviewStatus'],'limited')
            self.assertEqual(done['status'],'completed')
            history=public_history(root)
            self.assertEqual(history['total'],1)
            self.assertEqual(history['items'][0]['settings'],settings)
            archived,directory=archive(root,done,out,file,review,pin)
            self.assertEqual(public_history(root)['total'],1)
            self.assertEqual(done['result']['file'],str(directory/'result.png'))
            saved=library_operation(root,{'action':'save_history_preset','id':archived['id'],'name':'Bank objects'})
            self.assertTrue(saved['presetId'].startswith('personal-'))
            file.unlink()
            self.assertTrue(archived['evidenceSha256'])
            self.assertTrue(json.loads((directory/'evidence'/'manifest.json').read_text())['references'])
            shutil.rmtree(out)
            saved_again=library_operation(root,{'action':'save_history_preset','id':archived['id'],'name':'Bank objects'})
            self.assertEqual(saved_again['presetId'],saved['presetId'])
            request_bytes=(directory/'request.json').read_bytes()
            (directory/'request.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'request changed'):read_entry(root,archived['id'])
            (directory/'request.json').write_bytes(request_bytes)
            prompt_bytes=(directory/'evidence'/'prompt.txt').read_bytes()
            (directory/'evidence'/'prompt.txt').write_text('changed')
            with self.assertRaises(ValueError):library_operation(root,{'action':'save_history_preset','id':archived['id']})
            (directory/'evidence'/'prompt.txt').write_bytes(prompt_bytes)
            self.assertEqual(public_history(root)['total'],1)
            (directory/'result.png').write_bytes(b'corrupted')
            self.assertEqual(public_history(root)['total'],1)  # Listing verifies metadata; image route verifies PNG.
            with self.assertRaises(ValueError):read_entry(root,archived['id'])

    def test_failed_attempts_are_archived_without_completing_job(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            settings=dict(settingsVersion=3,topic='Attempts',graphicType='object',detailLevel='balanced',arrangement='auto',count=4,camera='front',creativity=3,whiteBase=False,background='transparent',palette='natural',effects=[],recognizable=True,materials=dict(mode='auto',base=None,accents=[]))
            job=dict(id='same-job',status='failed',request=dict(schemaVersion=1,settings=settings))
            ids=[]
            for index,color in enumerate(('red','blue')):
                out=root/f'execution-{index}';file=root/f'result-{index}.png';review=root/f'review-{index}.json'
                Image.new('RGB',(64,64),color).save(file)
                manifest=prepare(ROOT,dict(settings=settings,prompt='Attempts',referenceMode='prompt'),out);pin=manifest['manifestSha256'];sha=hashlib.sha256(file.read_bytes()).hexdigest()
                (out/'submission.json').write_text(json.dumps(dict(manifestSha256=pin,arguments=verify(out,pin),observedHandle=dict(type='generated-artifact',sha256=sha))))
                checks={key:dict(status='fail',observation='Synthetic failure: generated shapes did not match the requested visual hierarchy.') for key in CHECKS}
                review.write_text(json.dumps(dict(status='fail',file=str(file),sha256=sha,checks=checks)))
                from review_result import validate as strict_validate
                with self.assertRaisesRegex(ValueError,'fully opaque'):strict_validate(out,file,review,pin)
                row,directory=archive(root,job,out,file,review,pin);ids.append(row['id'])
                self.assertEqual((directory/'result.png').read_bytes(),file.read_bytes())
            self.assertEqual(job['status'],'failed')
            self.assertEqual(len(set(ids)),2)
            result=public_history(root)
            self.assertEqual(result['total'],2)
            self.assertTrue(all(item['reviewStatus']=='fail' and item['notes'] for item in result['items']))
            saved=library_operation(root,dict(action='save_history_preset',id=ids[0],name='Explicit user preference'))
            self.assertTrue(saved['presetId'].startswith('personal-'))

    def test_repeat_history_rebinds_archived_reference_in_another_session(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source';target=root/'target'
            buffer=io.BytesIO();Image.new('RGB',(32,32),'red').save(buffer,format='PNG')
            reference=upload_reference(source,dict(data=base64.b64encode(buffer.getvalue()).decode(),name='my-reference.png'))
            settings=dict(settingsVersion=3,topic='Exact original topic',graphicType='object',detailLevel='balanced',arrangement='auto',count=9,camera='front',creativity=3,whiteBase=False,background='white',palette='natural',effects=[],recognizable=True,materials=dict(mode='auto',base=None,accents=[]),reference=dict(facets=['lighting'],note='Soft',image={k:reference[k] for k in ('path','name','sha256')}))
            out=source/'execution';file=source/'result.png';Image.new('RGB',(64,64)).save(file)
            manifest=prepare(ROOT,dict(settings=settings,prompt='A boat',referenceMode='prompt'),out);pin=manifest['manifestSha256'];sha=hashlib.sha256(file.read_bytes()).hexdigest()
            (out/'submission.json').write_text(json.dumps(dict(manifestSha256=pin,arguments=verify(out,pin),observedHandle=dict(type='generated-artifact',sha256=sha))))
            review=source/'review.json';review.write_text(json.dumps(dict(status='limited',file=str(file),sha256=sha,checks={key:dict(status='pass',observation='Synthetic binding test.') for key in CHECKS|{'reference_lighting'}})))
            row,_=archive(root,dict(id='cross-session',request=dict(settings=settings)),out,file,review,pin)
            shutil.rmtree(source)
            restored=serve_presets.repeat_history(target,root,row['id'])
            image=restored['settings']['reference']['image'];self.assertEqual(Path(image['path']).read_bytes(),buffer.getvalue())
            self.assertEqual(image['sha256'],reference['sha256']);self.assertTrue(restored['referenceImage']['thumbnail'])
            expected=json.loads(json.dumps(settings));expected['reference']['image']=image
            self.assertEqual(restored['settings'],expected)
            queued=enqueue(target,dict(prompt='reference-style-3d: PNG.\n'+json.dumps(dict(schemaVersion=1,settings=restored['settings']))))
            self.assertEqual(queued['status'],'queued')
            # A corrupted archived guide must never be silently rebound.
            _,directory=read_entry(root,row['id']);guide=next(r for r in manifest['references'] if r['role']=='GUIDANCE REFERENCE')
            (directory/'evidence'/guide['file']).write_bytes(b'changed')
            with self.assertRaises(ValueError):serve_presets.repeat_history(target,root,row['id'])

    def test_corrupt_listener_does_not_hide_queue_and_plugin_output_is_rejected(self):
        import time
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            serve_presets.write_json(root/'consumer.json',dict(id='agent',expiresAt=time.time()+60))
            for listener in ({'consumer':'agent','updatedAt':None,'pid':1},{'consumer':'agent','updatedAt':time.time(),'pid':{}},{'consumer':'agent','updatedAt':time.time(),'pid':10**100}):
                serve_presets.write_json(root/'listener.json',listener)
                self.assertFalse(serve_presets.queue_status(root)['listener']['waiting'])
            serve_presets.write_json(root/'consumer.json',dict(id='agent',expiresAt=float('inf')))
            self.assertFalse(serve_presets.consumer_status(root)['active'])
        with patch('sys.argv',['serve_presets.py','--directory',str(ROOT),'--key','blocked']),patch('serve_presets.ThreadingHTTPServer') as server:
            with self.assertRaises(SystemExit):serve_presets.main()
            server.assert_not_called()

    def test_history_pagination_never_reads_pngs(self):
        import history as history_module
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for index in range(25):
                directory=root/'generations'/f'item-{index:02d}'
                directory.mkdir(parents=True)
                (directory/'settings.json').write_text(json.dumps({'topic':str(index)}))
                (directory/'review.json').write_text('{}')
                (directory/'result.png').write_bytes(b'large-image-stand-in')
                row=dict(id=directory.name,createdAt=index,topic=str(index),reviewStatus='pass',sha256=history_module.digest(directory/'result.png'),settingsSha256=history_module.digest(directory/'settings.json'),reviewSha256=history_module.digest(directory/'review.json'))
                (directory/'metadata.json').write_text(json.dumps(row))
            original_digest=history_module.digest
            def metadata_only(path):
                self.assertNotEqual(Path(path).suffix,'.png','List pagination must not read image bytes')
                return original_digest(path)
            with patch('history.digest',side_effect=metadata_only):
                result=public_history(root,2,12)
            self.assertEqual((result['total'],result['page'],len(result['items'])),(25,2,12))
            self.assertEqual(result['items'][0]['id'],'item-12')
            self.assertEqual(result['items'][-1]['id'],'item-01')
            (root/'generations'/'item-12'/'settings.json').write_text('{}')
            self.assertEqual(public_history(root)['total'],24)
            # One malformed metadata record must not break the other pages.
            for field,value in [('createdAt',None),('createdAt',float('nan')),('topic',[]),('reviewStatus','unknown')]:
                path=root/'generations'/'item-13'/'metadata.json';original=json.loads(path.read_text());broken=dict(original);broken[field]=value;path.write_text(json.dumps(broken))
                self.assertEqual(public_history(root)['total'],23)
                path.write_text(json.dumps(original))

    def test_reference_bytes_and_binding(self):
        with tempfile.TemporaryDirectory() as folder:
            raw=io.BytesIO();Image.new('RGBA',(32,32),(255,0,0,128)).save(raw,format='PNG')
            record=upload_reference(Path(folder),{'data':base64.b64encode(raw.getvalue()).decode(),'name':'test.png'})
            self.assertEqual(Path(record['path']).read_bytes(),raw.getvalue())
            with Image.open(record['path']) as image:self.assertEqual(image.mode,'RGBA')
            self.assertTrue(record['thumbnail'].startswith('data:image/jpeg;base64,'))
    def test_palettes_are_saved_without_queue(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);consumer_lease(root,'test-consumer')
            result=library_operation(root,{'action':'save_palette','name':'Test','colors':['#FF0000','#FFFFFF']})
            self.assertEqual(len(result['palettes']),1)
            self.assertEqual(library_operation(root,{'action':'load_palette_library'}),result)
            self.assertFalse((root/'requests').exists())
            with self.assertRaises(ValueError):library_operation(root,{'action':'unexpected'})

    def test_favorite_is_persistent_and_immediate(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);consumer_lease(root,'test-consumer');file=root/'result.png'
            Image.new('RGB',(64,64)).save(file)
            settings=dict(settingsVersion=3,topic='Test',graphicType='object',detailLevel='balanced',arrangement='auto',count=4,camera='front',creativity=3,whiteBase=False,background='white',palette='natural',effects=[],recognizable=True,materials=dict(mode='auto',base=None,accents=[]))
            import_rows(root,[dict(id='test',name='Test',settings=settings,file=str(file),source='collection')])
            self.assertEqual(library_operation(root,{'action':'set_favorite','id':'test','favorite':True})['favorites'],['test'])
            self.assertEqual(library_operation(root,{'action':'load_preset_library'})['favorites'],['test'])
            self.assertEqual(library_operation(root,{'action':'set_favorite','id':'test','favorite':False})['favorites'],[])
            self.assertFalse((root/'requests').exists())

    def test_port_conflict_preserves_live_bridge(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);consumer_lease(root,'test-consumer');bridge=root/'browser-bridge.js'
            bridge.write_text('existing session token')
            with patch('sys.argv',['serve_presets.py','--directory',folder,'--key','test']), patch.object(serve_presets,'ThreadingHTTPServer',side_effect=OSError('Address already in use')):
                with self.assertRaises(OSError):serve_presets.main()
            self.assertEqual(bridge.read_text(),'existing session token')

    def test_consumer_lease_expiry_overrules_live_listener(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            import os,time
            consumer_lease(root,'active')
            write_json(root/'listener.json',{'pid':os.getpid(),'updatedAt':time.time(),'consumer':'active'})
            self.assertTrue(queue_status(root)['listener']['waiting'])
            with self.assertRaises(ValueError):consumer_lease(root,'other')
            write_json(root/'consumer.json',{'id':'active','expiresAt':time.time()-1})
            status=queue_status(root)
            self.assertFalse(status['consumer']['active'])
            self.assertFalse(status['listener']['waiting'])
            self.assertIsNone(claim(root,'active'))
            consumer_lease(root,'active')
            consumer_lease(root,'active','detach')
            self.assertFalse(queue_status(root)['consumer']['active'])

    def test_server_restore_reconstructs_reference_thumbnail(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);buffer=io.BytesIO()
            Image.new('RGB',(32,32),'red').save(buffer,format='PNG')
            image=upload_reference(root,{'data':base64.b64encode(buffer.getvalue()).decode(),'name':'reference.png'})
            snapshot={'modelContent':{'panel':'reference-style-3d-v6','settings':{'reference':{'image':{k:v for k,v in image.items() if k!='thumbnail'}}}}}
            write_json(root/'state.json',snapshot)
            restored=restored_state(root)
            self.assertEqual(restored['state'],snapshot)
            self.assertEqual(restored['referenceImage']['sha256'],image['sha256'])
            self.assertTrue(restored['referenceImage']['thumbnail'].startswith('data:image/'))

    def test_old_active_jobs_survive_history_limit_and_broken_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for i in range(60):
                write_json(root/'requests'/f'job{i}.json',dict(id=f'job{i}',status='completed',createdAt=i+1,request={'settings':{'topic':'test'}}))
            write_json(root/'requests'/'pending.json',dict(id='pending',status='queued',createdAt=0,request={'settings':{'topic':'pending'}}))
            (root/'requests'/'broken.json').write_text('{')
            status=queue_status(root)
            self.assertEqual(status['unreadableRequests'],1)
            self.assertIn('pending',[row['id'] for row in status['requests']])
            self.assertEqual(len(status['requests']),51)
            consumer_lease(root,'worker')
            self.assertEqual(claim(root,'worker')['id'],'pending')

    def test_history_revision_changes_when_attempt_arrives(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'sessions'/'test'
            before=queue_status(root)['historyRevision']
            write_json(Path(folder)/'generations'/'attempt'/'metadata.json',{'id':'attempt'})
            self.assertNotEqual(queue_status(root)['historyRevision'],before)

    def test_server_token_survives_restart_without_cross_port_reuse(self):
        from serve_presets import session_token
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            token=session_token(root,4397)
            write_json(root/'server-token-4397.json',{'token':token})
            self.assertEqual(session_token(root,4397),token)
            self.assertNotEqual(session_token(root,4398),token)

    def test_non_plugin_message_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):enqueue(Path(folder),{'prompt':'other\n{}'})
if __name__=='__main__':unittest.main()
