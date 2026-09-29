import concurrent.futures
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
import presets
from prepare_generation import prepare, verify


class PresetsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'data'
        self.file = self.base / 'result.png'
        Image.new('RGB', (640, 480), '#5588aa').save(self.file)
        self.settings = dict(settingsVersion=3, topic='Do not transfer', subjects='A boat', avoid='Fire',
            graphicType='object',
            detailLevel='balanced', arrangement='auto', count=9, camera='front', creativity=3,
            whiteBase=False, background='white', palette='custom', colors=['#123456','#ABCDEF'],
            effects=[], recognizable=True, materials=dict(mode='auto',base=None,accents=[]))

    def row(self, pid='preset-a'):
        return dict(id=pid, name='Визуальный пресет', settings=copy.deepcopy(self.settings),
                    file=str(self.file), source='collection')

    def test_reference_driven_generation_is_not_a_settings_only_preset(self):
        row = self.row()
        row['settings']['reference'] = dict(facets=['lighting'],note='')
        with self.assertRaises(presets.PresetError): presets.import_rows(self.root,[row])
        self.assertFalse((self.root/'presets.json').exists())

    def test_snapshot_strips_only_story_and_keeps_exact_controls(self):
        original = copy.deepcopy(self.settings)
        changed, data = presets.import_rows(self.root, [self.row()])
        self.assertTrue(changed)
        saved = data['presets'][0]
        self.assertEqual(saved['settings'], {k:v for k,v in original.items() if k not in presets.STORY})
        self.assertEqual(self.settings, original)
        preview = presets.preview_path(self.root, saved)
        self.assertTrue(preview.is_file())
        self.file.unlink()
        self.assertTrue(presets.public_library(self.root)['presets'][0]['thumbnail'])
        self.assertEqual(presets.read_store(self.root), data)

    def test_immutable_ids_atomic_import_and_idempotence(self):
        presets.import_rows(self.root, [self.row()])
        before = (self.root/'presets.json').read_bytes()
        self.assertFalse(presets.import_rows(self.root, [self.row()])[0])
        changed = self.row(); changed['settings']['creativity'] = 5
        with self.assertRaisesRegex(ValueError, 'immutable'):
            presets.import_rows(self.root, [self.row('new'), changed])
        self.assertEqual((self.root/'presets.json').read_bytes(), before)
        invalid = self.row('invalid'); invalid['file'] = '/missing.png'
        with self.assertRaises(ValueError):
            presets.import_rows(self.root, [self.row('new'), invalid])
        self.assertEqual((self.root/'presets.json').read_bytes(), before)

    def test_favorite_unknown_id_and_cross_process_persistence(self):
        presets.import_rows(self.root, [self.row()])
        env = dict(os.environ, REFERENCE_STYLE_3D_DATA_DIR=str(self.root))
        def cli(*args):
            result = subprocess.run([sys.executable, str(Path(presets.__file__)), *args], env=env, capture_output=True, text=True)
            return result.returncode, json.loads(result.stdout)
        self.assertTrue(cli('favorite', '--id', 'preset-a', '--on')[1]['changed'])
        self.assertFalse(cli('favorite', '--id', 'preset-a', '--on')[1]['changed'])
        self.assertEqual(cli('list')[1]['favorites'], ['preset-a'])
        before = (self.root/'presets.json').read_bytes()
        self.assertEqual(cli('favorite', '--id', 'unknown', '--on')[0], 1)
        self.assertEqual((self.root/'presets.json').read_bytes(), before)
        self.assertEqual(cli('favorite', '--id', 'preset-a', '--off')[1]['favorites'], [])

    def test_concurrent_favorites_do_not_lose_updates(self):
        ids = ['p'+str(i) for i in range(8)]
        presets.import_rows(self.root, [self.row(pid) for pid in ids])
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda pid: presets.favorite(self.root, pid, True), ids))
        self.assertEqual(set(presets.read_store(self.root)['favorites']), set(ids))

    def test_corrupt_store_is_never_replaced_and_path_escape_rejected(self):
        self.root.mkdir()
        path = self.root/'presets.json'; path.write_text('{broken')
        with self.assertRaises(ValueError): presets.import_rows(self.root, [self.row()])
        self.assertEqual(path.read_text(), '{broken')
        path.unlink()
        _, data = presets.import_rows(self.root, [self.row()])
        data['presets'][0]['preview'] = '../result.png'
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'preview path'): presets.read_store(self.root)

    def test_personal_requires_receipt_bound_png_and_trusted_snapshot(self):
        settings = {k:v for k,v in self.settings.items() if k != 'reference'}
        out = self.base/'execution'
        manifest = prepare(presets.PLUGIN, dict(settings=settings,prompt='A boat',referenceMode='prompt'), out)
        pin = manifest['manifestSha256']
        receipt = dict(manifestSha256=pin, arguments=verify(out,pin),
            observedHandle=dict(type='generated-artifact',sha256=hashlib.sha256(self.file.read_bytes()).hexdigest()))
        (out/'submission.json').write_text(json.dumps(receipt))
        entry, image_hash = presets.execution_entry(out, self.file, pin, 'Мой результат')
        self.assertEqual(entry['source'], 'personal')
        self.assertNotIn('topic', entry['settings'])
        with self.assertRaises(ValueError): presets.execution_entry(out,self.file,'0'*64,'Wrong pin')
        Image.new('RGB',(640,480),'red').save(self.file)
        with self.assertRaisesRegex(ValueError,'changed before'):
            presets.import_rows(self.root,[entry],expected_images={entry['id']:image_hash})
        with self.assertRaisesRegex(ValueError,'evidence'): presets.execution_entry(out,self.file,pin,'Wrong PNG')

    def test_invalid_controls_fail_before_data_creation(self):
        for patch_settings in ({'count':100},{'camera':'unknown'},{'graphicType':'unknown'},{'prompt':'hidden prose'}):
            row = self.row(); row['settings'].update(patch_settings)
            with self.assertRaises(ValueError): presets.import_rows(self.root,[row])
            self.assertFalse(self.root.exists())

    def test_catalog_is_paged_without_settings_loss(self):
        presets.import_rows(self.root,[self.row('p'+str(i)) for i in range(25)])
        library = presets.public_library(self.root, page=2)
        payload = presets.inline_library(library, 650_000)
        self.assertEqual((payload['total'], payload['catalogTotal'], payload['page'], payload['pageSize']), (25,25,2,6))
        self.assertEqual([r['id'] for r in payload['presets']], ['p'+str(i) for i in range(6,12)])
        self.assertEqual(payload['presets'][0]['settings'],library['presets'][0]['settings'])
        self.assertTrue(payload['presets'][0]['thumbnail'].startswith('data:image/webp;base64,'))
        self.assertEqual(len(presets.public_library(self.root,page=999)['presets']),1)
        self.assertEqual(presets.public_library(self.root,page=999)['page'],5)
        with self.assertRaisesRegex(ValueError,'budget'): presets.inline_library(library,100)

    def test_filters_apply_to_entire_store_before_paging(self):
        rows = [self.row('p'+str(i)) for i in range(13)]
        selected = rows[-1]
        selected['source'] = 'personal'
        selected['settings'].update(graphicType='scene',detailLevel='rich',camera='side',shot='wide',
            arrangement='depth',creativity=5,palette='natural',effects=[dict(id='inflate',strength=50,target='')],
            materials=dict(mode='selected',base='ceramic',accents=['silver-satin']))
        presets.import_rows(self.root,rows)
        presets.favorite(self.root, 'p12', True)
        filters = dict(scope='favorites',type='scene',detail='rich',camera='side',shot='wide',
            arrangement='depth',creativity='5',palette='natural',effect='inflate',material='silver-satin')
        for key, value in filters.items():
            result = presets.public_library(self.root,filters={key:value})
            self.assertEqual([r['id'] for r in result['presets']],['p12'],key)
        self.assertEqual(presets.public_library(self.root,filters=filters)['total'],1)
        self.assertEqual(presets.public_library(self.root,filters={'scope':'personal'})['total'],1)
        self.assertEqual(presets.public_library(self.root,filters={'effect':'none','material':'auto','shot':'auto'})['total'],12)
        catalog = presets.read_json(presets.PLUGIN/'assets/materials/catalog.json')
        label = next(r['label'] for r in catalog['cards'] if r['id']=='ceramic')
        self.assertEqual(presets.public_library(self.root,filters={'search':label.upper()})['total'],1)
        effect = next(r for r in presets.read_json(presets.PLUGIN/'skills/reference-style-3d/references/effects.json') if r['id']=='inflate')
        self.assertEqual(presets.public_library(self.root,filters={'search':effect['label']})['total'],1)
        empty = presets.public_library(self.root,page=99,filters={'search':'not-found'})
        self.assertEqual((empty['total'],empty['page'],empty['presets']),(0,1,[]))
        self.assertEqual(empty['catalogTotal'],13)
        for invalid in ({'camera':'bad'},{'extra':'x'},{'creativity':5},{'scope':''}):
            with self.assertRaises(ValueError): presets.public_library(self.root,filters=invalid)
        for page in (0,-1,True,'2'):
            with self.assertRaises(ValueError): presets.public_library(self.root,page=page)

    def test_store_preview_1024_and_inline_never_reduces_below_512(self):
        import base64
        import io
        Image.effect_noise((1536,1536),100).convert('RGB').save(self.file)
        presets.import_rows(self.root,[self.row('p'+str(i)) for i in range(18)])
        store = presets.read_store(self.root)
        with Image.open(presets.preview_path(self.root,store['presets'][0])) as im:
            self.assertEqual(im.size,(1024,1024))
        library = presets.public_library(self.root,page=2)
        # Quality may adapt, but page boundaries and the 512px minimum stay fixed.
        six = presets.public_library(self.root,page=2,page_size=6)
        encoded = copy.deepcopy(six)
        for row in encoded['presets']:
            with Image.open(row['thumbnail']) as source:
                preview = source.convert('RGB'); preview.thumbnail((512,512),Image.Resampling.LANCZOS)
                out = io.BytesIO(); preview.save(out,format='WEBP',quality=65,method=4)
                row['thumbnail']='data:image/webp;base64,'+base64.b64encode(out.getvalue()).decode()
        encoded.update(previewSize=512,previewQuality=65)
        budget = len(json.dumps(encoded,ensure_ascii=False).encode()) + 16
        payload = presets.inline_library(library,budget)
        self.assertEqual(payload['pageSize'],6)
        self.assertEqual([r['id'] for r in payload['presets']], ['p'+str(i) for i in range(6,12)])
        self.assertLessEqual(len(json.dumps(payload,ensure_ascii=False).encode()),budget)
        for row in payload['presets']:
            with Image.open(io.BytesIO(base64.b64decode(row['thumbnail'].split(',',1)[1]))) as im:
                self.assertGreaterEqual(max(im.size),512)
        self.assertEqual(library['pageSize'],6)
        self.assertFalse(library['presets'][0]['thumbnail'].startswith('data:'))

    def test_refresh_only_preview_preserves_all_other_data(self):
        import io
        Image.new('RGB',(1600,1200),'#5588aa').save(self.file)
        presets.import_rows(self.root,[self.row()])
        presets.favorite(self.root,'preset-a',True)
        before = presets.read_store(self.root)
        small = io.BytesIO(); Image.new('RGB',(256,192),'#5588aa').save(small,format='WEBP')
        relative = 'previews/'+hashlib.sha256(small.getvalue()).hexdigest()+'.webp'
        (self.root/relative).write_bytes(small.getvalue())
        before['presets'][0]['preview']=relative
        (self.root/'presets.json').write_text(json.dumps(before))
        # Import stays idempotent when only preview encoding/version differs.
        self.assertFalse(presets.import_rows(self.root,[self.row()])[0])
        incoming = self.row(); incoming['name']='Ignored rename'; incoming['source']='personal'
        changed, after = presets.refresh_previews(self.root,[incoming])
        self.assertTrue(changed)
        restored = copy.deepcopy(after); restored['presets'][0]['preview']=relative
        self.assertEqual(restored,before)
        with Image.open(presets.preview_path(self.root,after['presets'][0])) as im:
            self.assertEqual(im.size,(1024,768))
        self.assertFalse(presets.refresh_previews(self.root,[incoming])[0])
        self.assertTrue((self.root/relative).exists())

    def test_stale_low_resolution_preview_is_not_upscaled_or_claimed_hq(self):
        Image.new('RGB',(256,256),'red').save(self.file)
        presets.import_rows(self.root,[self.row()])
        with self.assertRaisesRegex(ValueError,'refresh previews'):
            presets.inline_library(presets.public_library(self.root),900_000)

    def test_refresh_mismatch_leaves_store_unchanged(self):
        presets.import_rows(self.root,[self.row()])
        before = (self.root/'presets.json').read_bytes()
        invalid = self.row(); invalid['settings']['creativity']=5
        for rows in ([invalid],[self.row('unknown')],[self.row(),self.row()]):
            with self.assertRaises(ValueError): presets.refresh_previews(self.root,rows)
            self.assertEqual((self.root/'presets.json').read_bytes(),before)
        Image.new('RGB',(640,480),'red').save(self.file)
        with self.assertRaisesRegex(ValueError,'do not match'): presets.refresh_previews(self.root,[self.row()])
        self.assertEqual((self.root/'presets.json').read_bytes(),before)

    def test_plugin_data_directory_is_forbidden(self):
        with patch.dict(os.environ, REFERENCE_STYLE_3D_DATA_DIR=str(presets.PLUGIN/'user-data')):
            with self.assertRaisesRegex(ValueError,'outside'): presets.data_root()


if __name__ == '__main__':
    unittest.main()
