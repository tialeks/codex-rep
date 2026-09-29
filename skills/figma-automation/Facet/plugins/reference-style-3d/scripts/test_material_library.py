import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from PIL import Image
from material_library import selection, build_sheet, digest
from compile_settings import compile_settings
from prepare_generation import ROOT, prepare, verify


class MaterialsTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.ids=[c['id'] for c in json.loads((ROOT/'assets/materials/catalog.json').read_text())['cards']]
        self.settings=dict(topic='Test',mode='icon',count=1,objects=1,camera='front',size=32,
            detailMode='auto',detail=1,creativity=3,whiteBase=False,metal=0,pearl=0,
            background='white',palette='natural',effects=[],recognizable=True)

    def test_catalog_complete_and_all_checksums(self):
        self.assertEqual(len(set(self.ids)),36)
        for i in self.ids:self.assertEqual(selection(ROOT,[i])[0]['id'],i)

    def test_invalid_selections(self):
        for ids in (None,'wood',[1],['missing'],['wood','wood'],self.ids[:13]):
            with self.subTest(ids=ids),self.assertRaises(ValueError):
                compile_settings(ROOT,dict(self.settings,materialIds=ids))

    def test_default_unchanged_and_zero_budgets_authoritative(self):
        self.assertEqual(compile_settings(ROOT,self.settings),compile_settings(ROOT,dict(self.settings,materialIds=[])))
        text=compile_settings(ROOT,dict(self.settings,materialIds=self.ids[:2]))
        self.assertIn('No metal',text);self.assertIn('No nacre',text)
        self.assertIn('zero budget excludes',text);self.assertIn('not necessarily every sample',text)

    def test_deterministic_layout_order_and_boundary(self):
        for n in (1,5,12):
            ids=self.ids[:n];a=build_sheet(ROOT,ids,self.base/'a.png');b=build_sheet(ROOT,ids,self.base/'b.png')
            self.assertEqual(a,b);self.assertEqual(a['orderedIds'],ids)
            self.assertEqual(a['columns'],min(4,n));self.assertEqual(a['rows'],(n+3)//4)
            with Image.open(self.base/'a.png') as im:self.assertEqual(im.size,(a['width'],a['height']))
        reverse=build_sheet(ROOT,self.ids[:12][::-1],self.base/'reverse.png')
        self.assertNotEqual(a['sheetSha256'],reverse['sheetSha256'])
        self.assertEqual(reverse['cells'][0]['id'],self.ids[11])

    def test_package_checksum_mismatch(self):
        lib=self.base/'assets/materials';(lib/'cards').mkdir(parents=True)
        catalog=json.loads((ROOT/'assets/materials/catalog.json').read_text());card=catalog['cards'][0]
        (lib/'catalog.json').write_text(json.dumps(catalog));(lib/card['path']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'checksum'):selection(self.base,[card['id']])

    def test_prepare_binding_and_tampering(self):
        s=dict(self.settings,materialIds=self.ids[:5]);request={'schemaVersion':1,'settings':s,'prompt':'A chair'}
        out=self.base/'execution';m=prepare(ROOT,request,out);args=verify(out,m['manifestSha256'])
        self.assertEqual(m['request'],request);self.assertEqual(len(args['referenced_image_paths']),1)
        self.assertEqual(m['references'][0]['role'],'MATERIAL REFERENCE')
        self.assertIn('overall realism remain governed by the style profile and submitted settings',args['prompt'])
        self.assertNotIn('coating behavior and light only',args['prompt'])
        self.assertEqual(json.loads((out/'material-layout.json').read_text())['orderedIds'],s['materialIds'])
        layout=(out/'material-layout.json').read_bytes();(out/'material-layout.json').write_bytes(layout+b' ')
        with self.assertRaisesRegex(ValueError,'layout changed'):verify(out,m['manifestSha256'])
        (out/'material-layout.json').write_bytes(layout)
        image=Path(args['referenced_image_paths'][0]);image.write_bytes(image.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'reference changed'):verify(out,m['manifestSha256'])

    def test_reference_limit_includes_sheet(self):
        refs=[{'path':str(ROOT/'assets/materials/cards/wood.png'),'role':'MATERIAL REFERENCE'}]*5
        with self.assertRaisesRegex(ValueError,'limit 5'):
            prepare(ROOT,{'settings':dict(self.settings,materialIds=['wood']),'prompt':'Chair','userReferences':refs},self.base/'bad')
        self.assertFalse((self.base/'bad').exists())

if __name__=='__main__':unittest.main()
