import copy
import itertools
import tempfile
import unittest
from pathlib import Path
from compile_settings import compile_settings
from prepare_generation import ROOT, prepare, verify
from reference_guidance import catalog, effective_settings


class ReferenceGuidanceTest(unittest.TestCase):
    def setUp(self):
        self.s = dict(settingsVersion=3, topic='Camping', graphicType='group', detailLevel='rich',
                      arrangement='horizontal', count=4, camera='front', creativity=3, whiteBase=True,
                      background='white', palette='custom', colors=['#123456'], effects=[], recognizable=True,
                      materials=dict(mode='selected', base='wood', accents=['paper']))
        self.ref = dict(path=str(ROOT/'assets/originals/coin.png'), role='GUIDANCE REFERENCE')

    def test_single_and_pair_facets_have_one_owner_and_keep_snapshot(self):
        defs = catalog(ROOT)
        for size in (1, 2):
            for group in itertools.combinations(defs, size):
                s = dict(self.s, reference=dict(facets=[f['id'] for f in group], note=''))
                original = copy.deepcopy(s)
                output = compile_settings(ROOT, s)
                self.assertEqual(s, original)
                self.assertIn('PNG: 4 separate compositions, 2 columns × 2 rows.', output)
                self.assertIn('Background: pure white', output)
                self.assertIn('Never crop objects', output)
                self.assertEqual(output.count('GUIDANCE REFERENCE:'), 1)
                for f in group:
                    self.assertEqual(output.count(f['prompt']), 1)
                    for prefix in f['prefixes']:
                        self.assertFalse(any(line.startswith(prefix) for line in output.splitlines()))
                if any(f['id']=='palette' for f in group):
                    self.assertNotIn('#123456', output)
                else:
                    self.assertIn('#123456', output)

    def test_ornament_is_opt_in_and_can_combine_with_palette(self):
        plain=compile_settings(ROOT,dict(self.s,reference=dict(facets=['palette'])))
        patterned=compile_settings(ROOT,dict(self.s,reference=dict(facets=['palette','ornament'])))
        self.assertIn('Do not transfer printed patterns',plain)
        self.assertNotIn('Do not transfer printed patterns',patterned)
        self.assertIn('ornament: Transfer decorative motifs',patterned)
        ornament_only=compile_settings(ROOT,dict(self.s,reference=dict(facets=['ornament'])))
        self.assertIn('#123456',ornament_only)
        self.assertIn('Adapt the motifs to the active palette',ornament_only)

    def test_no_reference_leaves_existing_prompt_unchanged(self):
        self.assertEqual(compile_settings(ROOT,self.s), compile_settings(ROOT,dict(self.s,reference=dict(facets=[],note=''))))

    def test_invalid_reference_contracts_fail(self):
        for ref in ([], dict(facets=['bogus']), dict(facets=['palette','palette']),
                    dict(facets=[],note='orphan note'),dict(facets=['palette'],path='/old.png'),
                    dict(facets=['palette'],note='x'*501)):
            with self.assertRaises(ValueError):compile_settings(ROOT,dict(self.s,reference=ref))

    def test_conflicting_composition_effect_is_not_silently_dropped(self):
        s=dict(self.s, reference=dict(facets=['composition']), effects=[dict(id='levitate',strength=50,target='')])
        with self.assertRaisesRegex(ValueError,'conflicts'):compile_settings(ROOT,s)
        s['reference']['facets'].append('effects')
        self.assertNotIn('Effect (priority',compile_settings(ROOT,s))
        self.assertEqual(len(s['effects']),1)

    def test_inactive_values_do_not_control_reference_axes(self):
        s=dict(self.s, reference=dict(facets=['materials','palette','structure','detail','camera','composition']),
               materials=dict(mode='selected',base=None,accents=[]),graphicType='icon',arrangement='orbit')
        text=compile_settings(ROOT,s)
        self.assertNotIn('Main body material:',text)
        self.assertNotIn('Structure:',text)
        self.assertNotIn('Detail:',text)
        self.assertEqual(s['materials']['base'],None)

    def test_exactly_one_bound_guidance_image_required(self):
        s=dict(self.s,reference=dict(facets=['palette','materials']))
        for refs in ([],[dict(self.ref,role='STYLE REFERENCE')],[self.ref,self.ref]):
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaisesRegex(ValueError,'exactly one'):
                    prepare(ROOT,dict(settings=s,prompt='A backpack.',userReferences=refs),Path(tmp)/'execution')
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'exactly one'):
                prepare(ROOT,dict(settings=self.s,prompt='A backpack.',userReferences=[self.ref]),Path(tmp)/'execution')

    def test_material_sheet_suppressed_only_for_material_transfer(self):
        for facets, expected in ((['palette','materials'],1),(['palette'],2)):
            with tempfile.TemporaryDirectory() as tmp:
                s=dict(self.s,reference=dict(facets=facets))
                out=Path(tmp)/'execution'
                m=prepare(ROOT,dict(settings=s,prompt='A backpack.',userReferences=[self.ref]),out)
                args=verify(out,m['manifestSha256'])
                self.assertEqual(m['request']['settings'],s)
                self.assertEqual(len(args['referenced_image_paths']),expected)
                self.assertEqual(m['references'][0]['facets'],facets)
                self.assertEqual('materialSheet' in m,expected==2)
                Path(args['referenced_image_paths'][0]).write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError,'reference changed'):verify(out,m['manifestSha256'])


if __name__=='__main__':unittest.main()
