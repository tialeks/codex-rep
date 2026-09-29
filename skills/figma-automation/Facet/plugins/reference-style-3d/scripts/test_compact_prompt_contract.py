"""Regression coverage for required controls retained by the compact v3 prompt."""
import copy
from pathlib import Path
import tempfile
import unittest
from compile_settings import compile_settings
from prepare_generation import ROOT, prepare, verify

class CompactPromptContractTest(unittest.TestCase):
    def settings(self, **overrides):
        return dict(settingsVersion=3, topic='Tools', graphicType='icon',
                    detailLevel='minimal', arrangement='auto', count=9,
                    camera='front', creativity=2, whiteBase=False,
                    background='white', palette='custom', colors=['#2455F5','#B6E62E'],
                    recognizable=False, materials=dict(mode='auto',base=None,accents=[]),
                    effects=[], **overrides)

    def test_custom_palette_remains_dominant_in_actual_prepared_prompt(self):
        s=self.settings()
        before=copy.deepcopy(s)
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'execution'
            manifest=prepare(ROOT,dict(settings=s,prompt='Nine different tools.'),out)
            prompt=verify(out,manifest['manifestSha256'])['prompt']
        self.assertIn('#2455F5, #B6E62E dominate colorable surfaces',prompt)
        self.assertIn('Do not invent unrelated manufactured colors',prompt)
        self.assertIn('Abstract interpretation allowed.',prompt)
        self.assertIn('rendering quality must not add geometry, texture or realism',prompt)
        self.assertEqual(s,before)

    def test_effects_apply_per_composition_and_keep_material_identity(self):
        s=self.settings();s['effects']=[dict(id='bend',strength=75,target='')]
        prompt=compile_settings(ROOT,s)
        self.assertIn('Apply selected effects in every composition',prompt)
        self.assertIn('preserving assigned materials, palette and semantic subject count',prompt)
        self.assertEqual(prompt.count('Effect (priority 1)'),1)
        self.assertNotIn('Separated structural pieces',prompt)

    def test_separated_pieces_do_not_override_single_subject_type(self):
        for effect in ('explode','scatter','slice'):
            with self.subTest(effect=effect):
                s=self.settings();s['effects']=[dict(id=effect,strength=75,target='')]
                prompt=compile_settings(ROOT,s)
                self.assertIn('Separated structural pieces of one source remain one semantic subject',prompt)
                self.assertIn('unrelated added props count separately',prompt)

    def test_unused_rules_are_omitted(self):
        s=self.settings();s.update(palette='natural',effects=[dict(id='bend',strength=0,target='')])
        prompt=compile_settings(ROOT,s)
        self.assertNotIn('dominate colorable surfaces',prompt)
        self.assertNotIn('Apply selected effects',prompt)
        self.assertNotIn('Separated structural pieces',prompt)

if __name__=='__main__': unittest.main()
