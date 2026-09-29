"""Material identity is described once and overrides habitual subject finishes."""
import copy
import json
import re
import unittest
from compile_settings import compile_settings
from prepare_generation import ROOT


class MaterialPromptTest(unittest.TestCase):
    def setUp(self):
        self.cards=json.loads((ROOT/'assets/materials/catalog.json').read_text())['cards']
        self.s=dict(settingsVersion=3,topic='A wallet',graphicType='object',
            detailLevel='balanced',arrangement='auto',count=1,camera='front',creativity=3,
            whiteBase=False,background='white',palette='natural',effects=[],recognizable=True,
            materials=dict(mode='selected',base='satin-polymer',accents=['silver-polished','thin-glass']))

    def test_all_materials_have_short_surface_descriptions(self):
        self.assertEqual(len(self.cards),36)
        for card in self.cards:
            with self.subTest(material=card['id']):
                description=card.get('prompt')
                self.assertIsInstance(description,str)
                self.assertTrue(5<=len(description.split())<=12)
                self.assertNotRegex(description,r'(?i)\b(sphere|cube|camera|background|red|blue|green|yellow|orange|pink|white|black|softbox|spotlight)\b')
                self.assertRegex(description,r'(?i)reflection|sheen|gloss|specular|refracti|iridescen|scatter|texture|grain|weave|fibers|dispersion|translucen')
                settings=copy.deepcopy(self.s)
                settings['materials']=dict(mode='selected',base=card['id'],accents=[])
                text=compile_settings(ROOT,settings)
                self.assertEqual(text.count(description),1)
                self.assertIn('Construct each main subject from '+description,text)

    def test_unconventional_main_material_keeps_identity_not_habitual_finish(self):
        original=copy.deepcopy(self.s)
        text=compile_settings(ROOT,self.s)
        self.assertIn('smooth nonporous polymer',text)
        self.assertIn('satin sheen and no grain',text)
        self.assertIn('even when unconventional for that object',text)
        self.assertIn('preserve its identity, not its habitual surface',text)
        self.assertIn('Accent materials for functional details: silver-polished, thin-glass.',text)
        self.assertIn('Only these surfaces',text)
        self.assertNotIn('leather',text)
        self.assertEqual(self.s,original)

    def test_catalog_descriptors_do_not_add_detail_or_mutate_other_axes(self):
        text=compile_settings(ROOT,dict(self.s,detailLevel='minimal'))
        self.assertIn('no microtexture',text)
        self.assertIn('Camera: frontal view',text)
        self.assertIn('Palette: natural object/material colors.',text)
        self.assertIn('One hero object or functional set',text)

    def test_auto_and_reference_materials_do_not_get_inactive_manual_descriptor(self):
        automatic=dict(self.s,materials=dict(mode='auto',base=None,accents=[]))
        referenced=dict(self.s,reference=dict(facets=['materials'],note=''))
        descriptor=next(c['prompt'] for c in self.cards if c['id']=='satin-polymer')
        for settings in (automatic,referenced):
            with self.subTest(settings=settings):
                text=compile_settings(ROOT,settings)
                self.assertNotIn(descriptor,text)
                self.assertNotIn('Construct each main subject from',text)

    def test_new_primary_instruction_is_scoped_to_v3(self):
        legacy={k:v for k,v in self.s.items() if k not in ('settingsVersion','graphicType','detailLevel','arrangement','materials')}
        legacy.update(mode='object',objects=1,size=256,detailMode='auto',detail=3)
        versions=[dict(legacy,metal=20,pearl=10,materialIds=['satin-polymer']),
                  dict(legacy,settingsVersion=2,materials=self.s['materials'])]
        for settings in versions:
            text=compile_settings(ROOT,settings)
            self.assertNotIn('Construct each main subject from',text)
            self.assertNotIn('smooth nonporous polymer',text)


if __name__=='__main__': unittest.main()
