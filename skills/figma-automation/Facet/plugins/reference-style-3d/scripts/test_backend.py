"""Regressions from the runtime audit: malformed inputs and actual reference bytes."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
from prepare_generation import ROOT, prepare, verify
from compile_settings import compile_settings
from material_library import build_sheet


class BackendTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.settings = dict(settingsVersion=3, topic='Test', graphicType='object',
            detailLevel='balanced', arrangement='auto', count=1, camera='front',
            creativity=3, whiteBase=False, background='white', palette='natural',
            effects=[], recognizable=True, materials=dict(mode='auto',base=None,accents=[]))

    def test_malformed_reference_inputs_have_validation_errors_before_write(self):
        invalid = ['bad', 1, [], True]
        for index, settings in enumerate(invalid):
            out=self.base/str(index)
            with self.subTest(settings=settings),self.assertRaisesRegex(ValueError,'settings must be an object'):
                prepare(ROOT, dict(prompt='An apple', settings=settings), out)
            self.assertFalse(out.exists())
        for effects in (None, 'bad', {}):
            settings=dict(self.settings, effects=effects, reference={'facets':['composition'],'note':''})
            with self.subTest(effects=effects),self.assertRaisesRegex(ValueError,'effects must be an array'):
                compile_settings(ROOT, settings)

    def test_legacy_background_never_coerces_text_to_true(self):
        for i,background in enumerate(('false', 'true', 0, 1, None, [], {})):
            out=self.base/('background-'+str(i))
            with self.subTest(background=background),self.assertRaisesRegex(ValueError,'must be a boolean'):
                prepare(ROOT,dict(prompt='A box',transparentBackground=background),out)
            self.assertFalse(out.exists())

    def test_prepare_output_must_stay_outside_plugin_including_symlinks(self):
        root=self.base/'plugin';root.mkdir()
        alias=self.base/'alias';alias.symlink_to(root,target_is_directory=True)
        for out in (root,root/'outputs'/'run',alias/'run'):
            with self.subTest(out=out),self.assertRaisesRegex(ValueError,'outside the plugin'):
                prepare(root,dict(prompt='An apple'),out)
        self.assertEqual(list(root.iterdir()),[])

    def test_originals_use_current_profile_and_never_expand_selected_materials(self):
        settings=dict(self.settings,materials=dict(mode='selected',base='wood',accents=[]))
        request=dict(prompt='A wooden box',settings=settings,referenceMode='originals')
        out=self.base/'originals';manifest=prepare(ROOT,request,out)
        prompt=verify(out,manifest['manifestSha256'])['prompt']
        profile=json.loads((ROOT/'skills/reference-style-3d/references/prompt-profile.json').read_text())
        self.assertIn((ROOT/profile['styleBlock']).read_text().strip(),prompt)
        self.assertIn('Only these surfaces',prompt)
        self.assertNotIn('Use additional materials',prompt)
        self.assertNotIn('Materials are an open library',prompt)
        self.assertNotIn('atlasVersion',manifest);self.assertNotIn('trialOnly',manifest)

    def test_only_supplied_reference_roles_are_explained(self):
        from prepare_generation import REFERENCE_RULES
        request=dict(prompt='A wooden box',settings=dict(self.settings,
            materials=dict(mode='selected',base='wood',accents=[])))
        out=self.base/'materials';m=prepare(ROOT,request,out)
        prompt=verify(out,m['manifestSha256'])['prompt']
        self.assertIn('Image 1: MATERIAL REFERENCE',prompt)
        self.assertEqual(prompt.count('MATERIAL REFERENCE images supply'),1)
        for rule in REFERENCE_RULES.values():self.assertNotIn(rule,prompt)
        user_ref=str(ROOT/'assets/originals/coin.png')
        request=dict(prompt='A coin',editSource=user_ref,userReferences=[
            dict(path=user_ref,role='CONTENT REFERENCE'),dict(path=user_ref,role='COMPOSITION REFERENCE')])
        out=self.base/'roles';m=prepare(ROOT,request,out)
        prompt=verify(out,m['manifestSha256'])['prompt']
        self.assertEqual([r['role'] for r in m['references']],['EDIT SOURCE','CONTENT REFERENCE','COMPOSITION REFERENCE'])
        for role in ('EDIT SOURCE','CONTENT REFERENCE','COMPOSITION REFERENCE'):
            self.assertEqual(prompt.count(REFERENCE_RULES[role]),1)
        for role in ('STYLE REFERENCE','GUIDANCE REFERENCE'):
            self.assertNotIn(REFERENCE_RULES[role],prompt)

    def test_style_source_changed_during_copy_is_not_silently_trusted(self):
        out=self.base/'style'
        request=dict(prompt='A ring', referenceMode='selected', styleReferenceIds=['jewelry'],
                     referenceReason='Original finish')
        def changed_copy(source,destination):
            Path(destination).write_bytes(b'changed after catalog verification')
        with patch('prepare_generation.shutil.copyfile',side_effect=changed_copy):
            with self.assertRaisesRegex(ValueError,'Style reference changed'):
                prepare(ROOT,request,out)
        self.assertFalse(out.exists())

    def test_bad_material_checksum_leaves_no_partial_execution(self):
        root=self.base/'plugin'
        shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('__pycache__'))
        (root/'assets/materials/cards/wood.png').write_bytes(b'tampered')
        settings=dict(self.settings,materials=dict(mode='selected',base='wood',accents=[]))
        out=self.base/'bad'
        with self.assertRaisesRegex(ValueError,'checksum'):
            prepare(root,dict(prompt='A box',settings=settings),out)
        self.assertFalse(out.exists())

    def test_selected_cards_read_once_and_prompt_repeats_exactly(self):
        ids=['wood','ceramic']
        settings=dict(self.settings,materials=dict(mode='selected',base=ids[0],accents=ids[1:]))
        original=copy.deepcopy(settings)
        card_paths={str((ROOT/'assets/materials/cards'/f'{i}.png').resolve()):0 for i in ids}
        read_bytes=Path.read_bytes
        def counted_read(path):
            key=str(path.resolve())
            if key in card_paths:card_paths[key]+=1
            return read_bytes(path)
        out=self.base/'one'
        with patch.object(Path,'read_bytes',counted_read):
            first=prepare(ROOT,dict(prompt='A box',settings=settings),out)
        self.assertEqual(set(card_paths.values()),{1})
        second_out=self.base/'two'
        second=prepare(ROOT,dict(prompt='A box',settings=settings),second_out)
        self.assertEqual(settings,original)
        self.assertEqual(first['promptSha256'],second['promptSha256'])
        self.assertEqual(first['references'][-1]['sha256'],second['references'][-1]['sha256'])
        self.assertEqual(verify(out,first['manifestSha256'])['prompt'],verify(second_out,second['manifestSha256'])['prompt'])

    def test_sheet_preserves_sample_pixels_and_order(self):
        ids=['wood','ceramic']
        out=self.base/'sheet.png'
        layout=build_sheet(ROOT,ids,out)
        with Image.open(out) as sheet:
            for index,mid in enumerate(ids):
                with Image.open(ROOT/'assets/materials/cards'/f'{mid}.png') as card:
                    sample=card.convert('RGBA').resize((512,512),Image.Resampling.LANCZOS)
                    expected=Image.new('RGB',(512,512),'white');expected.paste(sample,(0,0),sample)
                    self.assertEqual(sheet.crop((index*512,0,(index+1)*512,512)).tobytes(),expected.tobytes())
        self.assertEqual(layout['orderedIds'],ids)


if __name__=='__main__': unittest.main()
