import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from prepare_generation import ROOT, prepare, verify, read, dump, sha
from compile_settings import compile_settings


class IntegrityTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.settings=dict(topic='Test',mode='icon',count=1,objects=1,camera='front',
            size=32,detailMode='auto',detail=1,creativity=3,whiteBase=False,
            metal=0,pearl=0,background='white',palette='natural',effects=[],recognizable=True)

    def test_explicit_schema_rejects_unknown_and_missing_settings_before_write(self):
        for i,request in enumerate([dict(schemaVersion=999,settings=self.settings),
            dict(schemaVersion=True,settings=self.settings),dict(schemaVersion=1),
            dict(schemaVersion=1,settings=None)]):
            out=self.base/str(i)
            with self.assertRaises(ValueError):prepare(ROOT,dict(request,prompt='A sphere'),out)
            self.assertFalse(out.exists())
        out=self.base/'legacy-request'
        m=prepare(ROOT,dict(prompt='Explicit legacy material chart'),out)
        self.assertEqual(m['schemaVersion'],2)
        verify(out,m['manifestSha256'])

    def test_trusted_pin_detects_request_version_recipe_changes(self):
        out=self.base/'run'
        m=prepare(ROOT,dict(schemaVersion=1,settings=self.settings,prompt='A heart'),out)
        original=read(out/'manifest.json')
        changes=[lambda x:x['request']['settings'].update(camera='top'),
            lambda x:x['request'].update(prompt='A car'),
            lambda x:x.update(pluginVersion='fiction'),
            lambda x:x['recipe'].update(version='fiction'),
            lambda x:x.update(schemaVersion=1)]
        for change in changes:
            altered=copy.deepcopy(original);change(altered);dump(out/'manifest.json',altered)
            with self.assertRaisesRegex(ValueError,'manifest changed'):
                verify(out,m['manifestSha256'])
        dump(out/'manifest.json',original)
        verify(out,m['manifestSha256'])

    def test_missing_pin_cannot_silently_downgrade_new_execution(self):
        out=self.base/'run';prepare(ROOT,dict(prompt='A heart'),out)
        with self.assertRaisesRegex(ValueError,'Trusted manifest SHA required'):verify(out)
        with self.assertRaisesRegex(ValueError,'Trusted manifest SHA required'):verify(out,allow_legacy=True)
        legacy=read(out/'manifest.json');legacy['schemaVersion']=1;legacy.pop('integrity');dump(out/'manifest.json',legacy)
        with self.assertRaisesRegex(ValueError,'Trusted manifest SHA required'):verify(out)
        verify(out,allow_legacy=True) # explicit compatibility, never hardened verification

    def test_receipt_binds_prepared_manifest(self):
        out=self.base/'run';m=prepare(ROOT,dict(prompt='A heart'),out)
        dump(out/'submission.json',dict(manifestSha256='incorrect'))
        with self.assertRaisesRegex(ValueError,'submission receipt'):verify(out,m['manifestSha256'])

    def test_malformed_setting_types_are_clean_validation_errors(self):
        for change in [dict(mode=[]),dict(camera={}),dict(effects=[dict(id=[],strength=50)])]:
            with self.assertRaises(ValueError):compile_settings(ROOT,dict(self.settings,**change))

    def test_reference_input_shapes_reject_before_creating_execution(self):
        changes=[dict(userReferences=value) for value in [None,{},'image.png',4]]
        changes += [dict(userReferences=[value]) for value in [None,[],4,'image.png',{},
            dict(path=4,role='STYLE REFERENCE'),dict(path='',role='STYLE REFERENCE'),
            dict(path='image.png',role=[]),dict(path='image.png',role='WRONG')]]
        changes += [dict(editSource=value) for value in [None,False,4,[],{},'', '  ']]
        changes += [dict(referenceMode=value) for value in [None,[],{},4,False]]
        for i,change in enumerate(changes):
            out=self.base/str(i)
            with self.subTest(change=change),self.assertRaises(ValueError):
                prepare(ROOT,dict(prompt='A heart',**change),out)
            self.assertFalse(out.exists())

    def test_unknown_settings_preserved_for_forward_compatibility(self):
        settings=dict(self.settings,futureControl={'enabled':True})
        out=self.base/'future'
        m=prepare(ROOT,dict(schemaVersion=1,settings=settings,prompt='A heart'),out)
        self.assertEqual(m['request']['settings'],settings)
        verify(out,m['manifestSha256'])

    def test_ui_effect_validation_agrees_with_compiler(self):
        html=(ROOT/'ui/controls.html').read_text()
        fn=html[html.index('function effectAllowed('):html.index('function normalizeEffects(')]+html[html.index('function effectiveObjects()'):html.index('function effectiveDetail()')]+html[html.index('function effectValidationError()'):html.index('async function submit()')]
        catalog=json.loads((ROOT/'skills/reference-style-3d/references/effects.json').read_text())
        cases=[dict(id='hybrid',strength=0,target=''),dict(id='hybrid',strength=50,target=''),
               dict(id='hybrid',strength=50,target='teapot'),dict(id='pearl',strength=50,target=''),
               dict(id='pearl',strength=0,target=''),dict(id='inflate',strength=1.5,target='')]
        for effect in cases:
            settings={k:v for k,v in self.settings.items() if k not in ('metal','pearl','materialIds','mode','objects','size','detailMode','detail')}
            settings.update(settingsVersion=3,graphicType='icon',detailLevel='minimal',arrangement='auto',materials={'mode':'auto','base':None,'accents':[]},effects=[effect])
            graphics=json.loads((ROOT/'skills/reference-style-3d/references/graphics.json').read_text())
            js="function usesReference(id){return (state.reference?.facets||[]).includes(id)};const graphics="+json.dumps(graphics)+';const state='+json.dumps(settings)+';const catalog='+json.dumps(dict(effects=catalog))+';'+fn+';console.log(JSON.stringify(effectValidationError()));'
            error=json.loads(subprocess.check_output(['node','-e',js],text=True))
            try:compile_settings(ROOT,settings);valid=True
            except ValueError:valid=False
            self.assertEqual(not bool(error),valid,effect)

if __name__=='__main__':unittest.main()
