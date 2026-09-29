import copy, json, subprocess, tempfile, unittest
from pathlib import Path
from compile_settings import compile_settings
from prepare_generation import ROOT, prepare, verify

class GraphicsTest(unittest.TestCase):
    def setUp(self):
        self.s=dict(settingsVersion=3,topic='Shopping',graphicType='group',detailLevel='balanced',arrangement='auto',count=4,camera='three-quarter',creativity=3,whiteBase=False,background='white',palette='natural',effects=[],recognizable=True,materials=dict(mode='auto',base=None,accents=[]))
        self.catalog=json.loads((ROOT/'skills/reference-style-3d/references/graphics.json').read_text())

    def test_axes_cross_product_and_snapshot(self):
        checked=0
        for graphic in self.catalog['types']:
            for detail in self.catalog['details']:
                for arrangement in self.catalog['arrangements']:
                    s=dict(self.s,graphicType=graphic['id'],detailLevel=detail['id'],arrangement=arrangement['id'])
                    before=copy.deepcopy(s)
                    invalid=graphic['maxSubjects']==1 and arrangement['id']!='auto'
                    if invalid:
                        with self.assertRaises(ValueError): compile_settings(ROOT,s)
                    else:
                        prompt=compile_settings(ROOT,s)
                        self.assertIn(graphic['prompt'],prompt)
                        self.assertIn(arrangement['prompt'],prompt)
                        self.assertIn('Never crop objects',prompt)
                        self.assertIn('('+str(detail['level'])+'/5)',prompt)
                        self.assertNotIn('CSS px',prompt)
                        self.assertNotIn('objects TOTAL',prompt)
                        self.assertEqual(prompt.count('Camera:'),1)
                    self.assertEqual(s,before);checked+=1
        self.assertEqual(checked, len(self.catalog['types']) * len(self.catalog['details']) * len(self.catalog['arrangements']))

    def test_legacy_axes_rejected_in_v3(self):
        for key in ('mode','size','objects','detailMode','detail','framing'):
            with self.assertRaisesRegex(ValueError,'Unsupported controls for settingsVersion=3'):compile_settings(ROOT,dict(self.s,**{key:256}))
        for key in ('graphicType','detailLevel','arrangement'):
            s=dict(self.s);s.pop(key)
            with self.assertRaises(ValueError):compile_settings(ROOT,s)

    def test_exact_preparation_and_material_roles(self):
        s=dict(self.s,materials=dict(mode='selected',base='ceramic',accents=['wood']))
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'execution'
            m=prepare(ROOT,dict(settings=s,prompt='A tea cup with its saucer.'),out)
            args=verify(out,m['manifestSha256'])
            self.assertEqual(m['request']['settings'],s)
            self.assertIn('Main body material: ceramic.',args['prompt'])
            self.assertIn('wood (details)',args['prompt'])
            self.assertIn('Count semantic subjects',args['prompt'])
            self.assertGreater(args['prompt'].index('REQUIRED SETTINGS'), args['prompt'].index('SCENES'))
            self.assertGreater(args['prompt'].index('REQUIRED SETTINGS'), args['prompt'].index('MATERIAL REFERENCE'))
            self.assertEqual(args['prompt'].count('Theme:'),1)

    def test_ui_uses_same_axes_and_effect_rules(self):
        html=(ROOT/'ui/controls.html').read_text()
        code=html[html.index('function effectAllowed('):html.index('function normalizeEffects(')]+html[html.index('function effectiveObjects()'):html.index('function render()')]+html[html.index('function effectValidationError()'):html.index('async function submit()')]
        effects=json.loads((ROOT/'skills/reference-style-3d/references/effects.json').read_text())
        cases=[]
        for graphic in self.catalog['types']:
            for arrangement in ('auto','horizontal'):
                for effect in ('levitate','domino','orbit'):
                    for strength in (0,50):
                        if graphic['maxSubjects']==1 and arrangement!='auto':continue
                        cases.append(dict(self.s,graphicType=graphic['id'],arrangement=arrangement,effects=[dict(id=effect,strength=strength,target='')]))
        js="function usesReference(id){return (state.reference?.facets||[]).includes(id)};let state;const graphics="+json.dumps(self.catalog)+';const catalog='+json.dumps(dict(effects=effects))+';'+code+';const cases='+json.dumps(cases)+';console.log(JSON.stringify(cases.map(s=>{state=s;return [effectiveObjects(),effectiveDetail(),effectValidationError()]})));'
        result=json.loads(subprocess.check_output(['node','-e',js],text=True))
        for s,(objects,detail,error) in zip(cases,result):
            self.assertEqual(objects,next(g['maxSubjects'] for g in self.catalog['types'] if g['id']==s['graphicType']))
            self.assertEqual(detail,3)
            try:compile_settings(ROOT,s);valid=True
            except ValueError:valid=False
            self.assertEqual(not bool(error),valid,s)
