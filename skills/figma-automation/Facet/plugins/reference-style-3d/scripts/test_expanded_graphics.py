import copy,json,unittest
from pathlib import Path
from compile_settings import compile_settings,CAMERAS
ROOT=Path(__file__).resolve().parents[1]
class ExpandedGraphicsTest(unittest.TestCase):
 def setUp(self):
  self.s=dict(settingsVersion=3,topic='Travel',graphicType='group',detailLevel='balanced',arrangement='auto',count=9,camera='three-quarter',creativity=3,whiteBase=False,background='white',palette='natural',effects=[],recognizable=True,materials=dict(mode='auto',base=None,accents=[]))
  self.g=json.loads((ROOT/'skills/reference-style-3d/references/graphics.json').read_text())
  self.e={e['id']:e for e in json.loads((ROOT/'skills/reference-style-3d/references/effects.json').read_text())}
 def test_auto_preserves_output(self):
  before=copy.deepcopy(self.s);p=compile_settings(ROOT,self.s)
  self.assertEqual(p,compile_settings(ROOT,dict(self.s,shot='auto')));self.assertNotIn('Shot:',p);self.assertEqual(before,self.s)
 def test_camera_distance_catalog_and_containment(self):
  self.assertEqual(CAMERAS,{c['id']:c['prompt'] for c in self.g['cameras']})
  for c in self.g['cameras']:
   for shot in self.g['shots']:
    s=dict(self.s,camera=c['id'],shot=shot['id']);before=copy.deepcopy(s);p=compile_settings(ROOT,s)
    self.assertIn(c['prompt'],p);self.assertIn('Never crop objects at cell/canvas edges',p)
    if shot['id']!='auto':self.assertIn('Shot: '+shot['prompt'],p)
    self.assertEqual(s,before)
  for field in ['camera','shot']:
   for bad in ['unknown',None,{},[]]:
    with self.assertRaises(ValueError):compile_settings(ROOT,dict(self.s,**{field:bad}))
 def test_camera_reference_owns_distance(self):
  s=dict(self.s,camera='unsupported',shot='unsupported',reference=dict(facets=['camera'],note=''));before=copy.deepcopy(s);p=compile_settings(ROOT,s)
  self.assertNotIn('Camera:',p);self.assertNotIn('Shot:',p);self.assertIn('relative composition size',p);self.assertIn('Never crop objects',p);self.assertEqual(s,before)
  fs=json.loads((ROOT/'skills/reference-style-3d/references/reference-facets.json').read_text());self.assertEqual(next(f for f in fs if f['id']=='camera')['controls'],['camera','shot'])
 def test_placement_conflicts_and_minimum(self):
  for key in ['suspended','cascade','vortex','ascending']:
   e=dict(id=key,strength=65,target='');self.assertIn(self.e[key]['prompt'],compile_settings(ROOT,dict(self.s,effects=[e])))
   self.assertIn('Composition effects take precedence',compile_settings(ROOT,dict(self.s,arrangement='diagonal',effects=[e])))
   with self.assertRaisesRegex(ValueError,'conflicts'):compile_settings(ROOT,dict(self.s,reference=dict(facets=['composition']),effects=[e]))
   self.assertIn(self.e[key]['prompt'],compile_settings(ROOT,dict(self.s,graphicType='icon',effects=[e])))
   compile_settings(ROOT,dict(self.s,graphicType='icon',effects=[dict(e,strength=0)]))
 def test_subject_effect_scope(self):
  for key in ['twist','compress','weave-form','bend','wrap','erode']:
   a=dict(id=key,strength=90,target='');b=dict(id='cascade',strength=40,target='');p=compile_settings(ROOT,dict(self.s,effects=[a,b]))
   self.assertIn(self.e[key]['prompt'],p);self.assertIn('Intensity 90/100',p)
   self.assertIn('Combine effects in listed priority order',compile_settings(ROOT,dict(self.s,effects=[a,dict(id='inflate',strength=40,target='')])))
 def test_new_arrangements(self):
  for key in ['diagonal','pyramid','vertical','radial','depth','symmetric']:
   self.assertIn(next(a['prompt'] for a in self.g['arrangements'] if a['id']==key),compile_settings(ROOT,dict(self.s,arrangement=key)))
   with self.assertRaisesRegex(ValueError,'Single-subject'):compile_settings(ROOT,dict(self.s,graphicType='icon',arrangement=key))

 def test_all_v3_effects_compile_without_truncation_or_snapshot_mutation(self):
  effects=[dict(id=e['id'],strength=65,target='teapot' if e.get('needsTarget') else '') for e in self.e.values() if 3 in e.get('settingsVersions',[1,2,3]) and e['id']!='none']
  self.assertGreater(len(effects),3)
  settings=dict(self.s,effects=effects);before=copy.deepcopy(settings)
  prompt=compile_settings(ROOT,settings)
  self.assertEqual(len(effects),prompt.count('Effect (priority '))
  for i in range(1,len(effects)+1):self.assertIn(f'Effect (priority {i}):',prompt)
  self.assertEqual(settings,before)
  self.assertIn('Combine effects in listed priority order',prompt)
 def test_priority_rule_only_for_overlapping_active_effects(self):
  fx=lambda key,strength=50:dict(id=key,strength=strength,target='')
  for effects in [[],[fx('inflate')],[fx('inflate'),fx('cascade')],[fx('inflate'),fx('fold',0),fx('cascade')]]:
   with self.subTest(effects=effects):self.assertNotIn('Combine effects in listed priority order',compile_settings(ROOT,dict(self.s,effects=effects)))
  for effects in [[fx('inflate'),fx('fold')],[fx('cascade'),fx('levitate')],[fx('inflate'),fx('cascade'),fx('fold')]]:
   with self.subTest(effects=effects):self.assertIn('Combine effects in listed priority order',compile_settings(ROOT,dict(self.s,effects=effects)))
  disabled=compile_settings(ROOT,dict(self.s,arrangement='diagonal',effects=[fx('cascade',0)]))
  self.assertNotIn('Combine effects in listed priority order',disabled)
 def test_v3_effect_validation_remains_strict(self):
  valid=dict(id='inflate',strength=50,target='')
  invalid=[None,{},'inflate',[None],[dict(id='fiction',strength=50)], [valid,valid],
           [dict(valid,strength=True)],[dict(valid,strength='50')],[dict(valid,strength=-1)],
           [dict(valid,strength=101)],[dict(valid,target=None)],
           [dict(id='hybrid',strength=50,target=' ')],[dict(id='morph',strength=50,target='')]]
  for effects in invalid:
   with self.subTest(effects=effects),self.assertRaises(ValueError):compile_settings(ROOT,dict(self.s,effects=effects))
 def test_small_structure_is_not_enlarged_for_effects(self):
  settings=dict(self.s,graphicType='icon',effects=[dict(id='vortex',strength=80,target=''),dict(id='cascade',strength=40,target='')])
  before=copy.deepcopy(settings);prompt=compile_settings(ROOT,settings)
  icon=next(g for g in self.g['types'] if g['id']=='icon')
  self.assertIn(icon['prompt'],prompt);self.assertEqual(settings,before)
