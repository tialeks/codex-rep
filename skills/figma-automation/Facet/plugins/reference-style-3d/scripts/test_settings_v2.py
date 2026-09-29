import copy
import json
from pathlib import Path
import tempfile
import unittest
from compile_settings import compile_settings
from material_library import settings_material_ids
from prepare_generation import ROOT, prepare, verify


class SettingsV2Test(unittest.TestCase):
    def setUp(self):
        self.s=dict(settingsVersion=2,topic='Camera',mode='illustration-simple',count=1,
            objects=3,camera='front',size=96,detailMode='auto',detail=3,creativity=3,
            whiteBase=False,background='white',palette='natural',effects=[],recognizable=True,
            materials={'mode':'auto','base':None,'accents':[]})

    def test_detail_rendering_uses_effective_level_and_preserves_snapshot(self):
        for size, mode, asked, expected in [(32,'auto',5,'Primary silhouette'),(64,'auto',4,'Primary volumes'),(64,'manual',5,'Clear functional'),(256,'manual',5,'Detailed authored')]:
            settings=dict(self.s,size=size,detailMode=mode,detail=asked)
            original=copy.deepcopy(settings)
            text=compile_settings(ROOT,settings)
            self.assertIn('Detail rendering: '+expected,text)
            self.assertEqual(settings,original)
            self.assertEqual(text.count('Detail rendering:'),1)

    def test_auto_has_no_budget_or_refs(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'auto';m=prepare(ROOT,{'schemaVersion':1,'settings':self.s,'prompt':'Camera'},out)
            args=verify(out,m['manifestSha256']);self.assertNotIn('referenced_image_paths',args)
            self.assertNotIn('local accent intensity',args['prompt']);self.assertNotIn('Zero metal',args['prompt'])
            self.assertIn('2–4 meaningful recognition cues',args['prompt'])

    def test_selected_roles_snapshot_and_sheet_order(self):
        s=dict(self.s,materials={'mode':'selected','base':'wood','accents':['ceramic','colored-glass']})
        original=copy.deepcopy(s)
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'selected';m=prepare(ROOT,{'schemaVersion':1,'settings':s,'prompt':'Camera'},out)
            args=verify(out,m['manifestSha256'])
            self.assertEqual(s,original);self.assertEqual(m['request']['settings'],original)
            self.assertIn('Main body material: wood.',args['prompt'])
            self.assertIn('Use only the selected surface materials',args['prompt'])
            self.assertIn('Accent materials for functional details: ceramic, colored-glass.',args['prompt'])
            self.assertNotIn('material budgets remain authoritative',args['prompt'])
            self.assertEqual(json.loads((out/'material-layout.json').read_text())['orderedIds'],['wood','ceramic','colored-glass'])
            self.assertEqual(len(args['referenced_image_paths']),1)
            self.assertIn('Material sheet Image 1 cells, left-to-right/top-to-bottom: 1 wood (main); 2 ceramic (details); 3 colored-glass (details).',args['prompt'])

    def test_legend_tracks_reference_position_and_legacy_has_none(self):
        with tempfile.TemporaryDirectory() as d:
            request={'settings':dict(self.s,materials={'mode':'selected','base':'ceramic','accents':['wood']}),
                'prompt':'Camera','referenceMode':'selected','styleReferenceIds':['payment-device'],
                'referenceReason':'Original form and finish.'}
            out=Path(d)/'v2';m=prepare(ROOT,request,out)
            self.assertIn('Material sheet Image 2 cells, left-to-right/top-to-bottom: 1 ceramic (main); 2 wood (details).',verify(out,m['manifestSha256'])['prompt'])
            legacy={k:v for k,v in self.s.items() if k not in ('settingsVersion','materials')}
            legacy.update(metal=20,pearl=10,materialIds=['wood'])
            out=Path(d)/'v1';m=prepare(ROOT,{'settings':legacy,'prompt':'Camera'},out)
            self.assertNotIn('cells, left-to-right/top-to-bottom:',verify(out,m['manifestSha256'])['prompt'])

    def test_bad_roles_and_versions(self):
        invalid=[{'mode':'auto','base':'wood','accents':[]},{'mode':'auto','base':None,'accents':['wood']},
            {'mode':'selected','base':None,'accents':[]},{'mode':'selected','base':'wood','accents':['wood']},
            {'mode':'selected','base':'unknown','accents':[]},{'mode':'selected','base':'wood','accents':'ceramic'},
            {'mode':'auto','base':None,'accents':[],'extra':1}]
        ids=[c['id'] for c in json.loads((ROOT/'assets/materials/catalog.json').read_text())['cards']]
        invalid.append({'mode':'selected','base':ids[0],'accents':ids[1:13]})
        for material in invalid:
            with self.subTest(material=material),self.assertRaises(ValueError):compile_settings(ROOT,dict(self.s,materials=material))
        for version in [3,True,'2',None]:
            with self.assertRaises(ValueError):compile_settings(ROOT,dict(self.s,settingsVersion=version))
        for field in ['metal','pearl','materialIds']:
            with self.assertRaisesRegex(ValueError,'instead of'):compile_settings(ROOT,dict(self.s,**{field:0}))

    def test_material_effects_rejected(self):
        for effect in ['ceramic','paper','textile','wood','rubber','pearl','inlay','contrast']:
            for strength in [0,50]:
                with self.assertRaisesRegex(ValueError,'through materials'):
                    compile_settings(ROOT,dict(self.s,effects=[{'id':effect,'strength':strength}]))

    def test_effect_scope_limits_and_geometry_surface_separation(self):
        fx=lambda i:{'id':i,'strength':60,'target':''}
        s=dict(self.s,materials={'mode':'selected','base':'ceramic','accents':[]},effects=[fx('inflate'),fx('orbit')])
        text=compile_settings(ROOT,s);self.assertIn('Main body material: ceramic',text)
        self.assertIn('inflated geometry does not imply PVC',text)
        for effects in [[fx('inflate'),fx('fold')],[fx('orbit'),fx('balance')],[fx('inflate'),fx('orbit'),fx('fold')]]:
            with self.assertRaisesRegex(ValueError,'one subject effect'):compile_settings(ROOT,dict(self.s,effects=effects))
        with self.assertRaisesRegex(ValueError,'Unknown'):compile_settings(ROOT,dict(self.s,effects=[fx('fiction')]))
        with self.assertRaisesRegex(ValueError,'requires at least'):compile_settings(ROOT,dict(s,mode='icon'))

    def test_legacy_settings_unchanged(self):
        legacy={k:v for k,v in self.s.items() if k not in ('settingsVersion','materials')}
        legacy.update(metal=20,pearl=10,materialIds=['wood'])
        self.assertEqual(settings_material_ids(ROOT,legacy),['wood'])
        text=compile_settings(ROOT,legacy)
        self.assertEqual(text,compile_settings(ROOT,dict(legacy,settingsVersion=1)))
        self.assertIn('metal: 20/100 local accent intensity',text)
        self.assertIn('Selected material surfaces available: wood',text)
        self.assertNotIn('Main body material:',text)

if __name__=='__main__':unittest.main()
