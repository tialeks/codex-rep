import copy
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from compile_settings import compile_settings
from prepare_generation import ROOT, prepare, verify


class SettingsTest(unittest.TestCase):
    def setUp(self):
        self.s = dict(topic='Workshop', mode='illustration-simple', count=16,
                      objects=3, camera='three-quarter', size=256, detailMode='auto',
                      detail=4, creativity=3, whiteBase=False, metal=37, pearl=23,
                      background='white', palette='natural', colors=['#FF687B'],
                      effects=[], recognizable=True)

    def test_form_message_roundtrip_and_no_inactive_colors(self):
        html = (ROOT/'ui/controls.html').read_text()
        code = html[html.index('function submittedSettings()'):html.index('\nasync function submit()')]
        for palette in ('natural', 'custom'):
            s = dict(self.s, palette=palette, topic='"Quoted" theme\nnext line', settingsVersion=3, graphicType='group', detailLevel='balanced', arrangement='auto', materials={'mode':'auto','base':None,'accents':[]})
            for key in ('metal', 'pearl','mode','objects','size','detailMode','detail'): s.pop(key)
            js = 'const state='+json.dumps(s)+';'+code+';console.log(prompt());'
            message = subprocess.check_output(['node', '-e', js], text=True)
            actual = json.loads(message.split('\n', 1)[1])['settings']
            expected = copy.deepcopy(s)
            if palette == 'natural': del expected['colors']
            self.assertEqual(actual, expected)
            self.assertLess(len(message), 900)

    def test_camera_and_natural_palette_compiled_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'execution'
            m=prepare(ROOT, {'settings': self.s, 'prompt': 'Pear lamp with a paper shade.'}, out)
            args = verify(out,m['manifestSha256'])
            prompt = args['prompt']
            self.assertEqual(prompt.count('Camera:'), 1)
            self.assertIn('three-quarter view', prompt)
            self.assertNotIn('mostly frontal', prompt)
            self.assertNotIn('#FF687B', prompt)
            self.assertEqual(prompt.count('Palette:'), 1)
            self.assertNotIn('referenced_image_paths', args)

    def test_all_cameras_and_grids(self):
        for camera, phrase in [('front','frontal view'), ('three-quarter','three-quarter view'), ('top','top-down view'), ('isometric','isometric view')]:
            self.assertIn(phrase, compile_settings(ROOT, dict(self.s, camera=camera)))
        for count, grid in [(1,'1 columns × 1 rows'),(4,'2 columns × 2 rows'),(5,'5 columns × 1 rows'),(8,'4 columns × 2 rows'),(9,'3 columns × 3 rows'),(15,'5 columns × 3 rows'),(16,'4 columns × 4 rows')]:
            self.assertIn(grid, compile_settings(ROOT, dict(self.s,count=count)))

    def test_detail_matches_existing_ui_rule(self):
        for size, auto, cap in [(32,1,2),(64,2,3),(96,3,5),(256,4,5)]:
            self.assertIn(f'detail {auto}/5', compile_settings(ROOT,dict(self.s,size=size)))
            self.assertIn(f'detail {cap}/5', compile_settings(ROOT,dict(self.s,size=size,detailMode='manual',detail=5)))
        self.assertIn('up to 1 objects TOTAL', compile_settings(ROOT,dict(self.s,mode='icon',objects=7)))

    def test_transparency_and_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'execution'
            r = {'settings':dict(self.s,background='transparent'),'prompt':'Pear'}
            m=prepare(ROOT,r,out)
            self.assertTrue(verify(out,m['manifestSha256'])['transparent_background'])
            with self.assertRaisesRegex(ValueError,'conflicts'):
                m=prepare(ROOT,dict(r,transparentBackground=False),Path(tmp)/'bad')
            self.assertFalse((Path(tmp)/'bad').exists())

    def test_effect_target_zero_budgets_and_invalid_values(self):
        self.assertIn('No metal',compile_settings(ROOT,dict(self.s,metal=0)))
        self.assertIn('No nacre',compile_settings(ROOT,dict(self.s,pearl=0)))
        e={'id':'hybrid','strength':50,'target':'teapot'}
        self.assertIn('Target: teapot',compile_settings(ROOT,dict(self.s,effects=[e])))
        for change in [dict(effects=[dict(e,target='')]),dict(effects=[e,e]),dict(count=7),dict(pearl=-1),dict(palette='custom',colors=['red']),dict(camera='guess')]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                compile_settings(ROOT,dict(self.s,**change))

    def test_every_catalog_effect_is_compilable_and_budget_conflicts_reject(self):
        catalog=json.loads((ROOT/'skills/reference-style-3d/references/effects.json').read_text())
        self.assertEqual(len({e['id'] for e in catalog}),len(catalog))
        for effect in catalog:
            value={'id':effect['id'],'strength':50,'target':'teapot' if effect['needsTarget'] else ''}
            with self.subTest(effect=effect['id']):
                if 1 not in effect.get('settingsVersions',[1,2,3]):
                    with self.assertRaises(ValueError):compile_settings(ROOT,dict(self.s,effects=[value]))
                    continue
                text=compile_settings(ROOT,dict(self.s,effects=[value]))
                self.assertNotIn('TARGET',text)
                if effect.get('requiresBudget'):
                    with self.assertRaisesRegex(ValueError,'conflicts'):
                        compile_settings(ROOT,dict(self.s,effects=[value],**{effect['requiresBudget']:0}))

    def test_disabled_effect_is_equivalent_to_no_effect(self):
        baseline = compile_settings(ROOT, self.s)
        for effect in ('fold', 'inflate', 'hybrid'):
            self.assertEqual(baseline, compile_settings(ROOT, dict(self.s,
                effects=[dict(id=effect, strength=0, target='')])) )

    def test_effect_scope_priority_and_target_are_unambiguous(self):
        result = compile_settings(ROOT, dict(self.s, effects=[
            dict(id='fold',strength=0,target=''),
            dict(id='hybrid',strength=65,target='teapot'),
            dict(id='inflate',strength=25,target='')]))
        self.assertIn('main subject of every composition', result)
        self.assertIn('Target is the second identity', result)
        self.assertIn('Effect (priority 1): Fuse', result)
        self.assertIn('Effect (priority 2): Inflate', result)
        self.assertIn('Intensity 65/100: clearly visible change', result)
        self.assertIn('Intensity 25/100: subtle localized change', result)
        self.assertNotIn('folded-sheet', result)

    def test_effect_preparation_preserves_scenes_and_settings(self):
        scenes = '1. A toaster. 2. Kitchen scales. 3. A grinder. 4. A mixer.'
        settings = dict(self.s, count=4, mode='object', effects=[
            dict(id='hybrid',strength=85,target='чайник')])
        original = copy.deepcopy(settings)
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'execution'
            m=prepare(ROOT, dict(settings=settings,prompt=scenes),out)
            self.assertEqual(settings,original)
            self.assertEqual(m['request']['settings'],original)
            self.assertEqual(m['request']['prompt'],scenes)
            text=verify(out,m['manifestSha256'])['prompt']
            self.assertEqual(text.count('SCENES\n'+scenes),1)
            self.assertIn('Intensity 85/100: pronounced transformation',text)
            self.assertIn('чайник',text)
            self.assertIn('detail 4/5',text)

    def test_natural_and_custom_keep_distinct_color_contracts(self):
        natural=compile_settings(ROOT,self.s)
        custom=compile_settings(ROOT,dict(self.s,palette='custom'))
        self.assertNotIn('#FF687B',natural)
        self.assertNotIn('dominant colors',natural)
        self.assertIn('#FF687B',custom)
        self.assertIn('dominant colors',custom)
        self.assertIn('unpainted material parts',custom)

    def test_object_limit_ui_matches_compiler_without_snapshot_mutation(self):
        html=(ROOT/'ui/controls.html').read_text()
        for mode in ('icon','object','category','illustration-simple','illustration-complex'):
            for size in (32,64,96,256):
                settings=dict(self.s,mode=mode,size=size,objects=7)
                snapshot=copy.deepcopy(settings)
                limit=1 if mode in ('icon','object','category') else 2 if size==32 else 7
                self.assertIn(f'up to {limit} objects TOTAL',compile_settings(ROOT,settings))
                self.assertEqual(settings,snapshot)

    def test_small_icon_rule_is_scoped_and_preserves_explicit_content(self):
        content='Calendar with exactly 7 marks and the text MONDAY'
        for mode,size,enabled in [('icon',32,True),('category',32,True),('icon',64,False),('object',32,False),('illustration-complex',256,False)]:
            settings=dict(self.s,mode=mode,size=size,subjects=content)
            text=compile_settings(ROOT,settings)
            self.assertEqual('one large recognition cue' in text,enabled)
            self.assertIn(content,text)
            if enabled:self.assertIn('Preserve explicit user content',text)

    def test_zero_material_overrides_only_when_disabled(self):
        for metal,pearl in [(0,0),(0,70),(70,0),(70,70)]:
            text=compile_settings(ROOT,dict(self.s,metal=metal,pearl=pearl))
            self.assertEqual('Zero metal is authoritative' in text,metal==0)
            self.assertEqual('Zero nacre is authoritative' in text,pearl==0)
            self.assertIn('Palette: natural colors',text)
            self.assertNotIn('#FF687B',text)

    def test_precise_camera_contracts_stay_distinct(self):
        expected={'front':'camera level and square', 'top':'90-degree overhead', 'isometric':'orthographic projection with parallel edges', 'three-quarter':'three-quarter view'}
        for camera,phrase in expected.items():
            text=compile_settings(ROOT,dict(self.s,camera=camera))
            self.assertIn(phrase,text)
            self.assertEqual(text.count('Camera:'),1)
            if camera!='top':self.assertNotIn('90-degree overhead',text)

    def test_legacy_composition_minimums(self):
        for effect in ('orbit','domino','scale','nest'):
            for mode in ('icon','object','illustration-complex'):
                for count in (1,2):
                    s=dict(self.s,mode=mode,objects=count,effects=[dict(id=effect,strength=50,target='')])
                    if mode=='illustration-complex' and count==2: compile_settings(ROOT,s)
                    else:
                        with self.assertRaisesRegex(ValueError,'requires at least 2 objects'):compile_settings(ROOT,s)

    def test_fragment_count_exception_is_only_enabled_for_fragment_effects(self):
        for effect in ('explode','scatter','slice','inflate','hybrid'):
            text=compile_settings(ROOT,dict(self.s,mode='object',effects=[dict(id=effect,strength=50,target='teapot' if effect=='hybrid' else '')]))
            self.assertEqual('fragments of one source object' in text,effect in ('explode','scatter','slice'))
            self.assertIn('up to 1 objects TOTAL',text)

    def test_effect_scope_and_pearl_controls_are_explicit(self):
        orbit=compile_settings(ROOT,dict(self.s,effects=[dict(id='orbit',strength=50,target='')]))
        self.assertIn('composition effects to object relationships',orbit)
        inflate=compile_settings(ROOT,dict(self.s,effects=[dict(id='inflate',strength=50,target='')]))
        self.assertNotIn('composition effects to object relationships',inflate)
        pearl=compile_settings(ROOT,dict(self.s,effects=[dict(id='pearl',strength=100,target='')]))
        self.assertIn('how extensively these local accents are used',pearl)
        self.assertNotIn('subtle pearlescent',pearl)


if __name__ == '__main__': unittest.main()
