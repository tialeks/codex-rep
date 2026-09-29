import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from prepare_generation import ROOT, dump, prepare, read, select, sha, verify


class PromptProfileTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name); self.root=self.base/'plugin'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('__pycache__'))
        self.out=self.base/'execution'

    def request(self,**changes):
        return dict({'userBrief':'Кольцо в футляре','prompt':'A silver ring in a teal velvet case.',
                     'referenceMode':'prompt','materials':['metal','velvet','cork']},**changes)

    def test_prompt_mode_no_automatic_images_and_recipe_snapshot(self):
        m=prepare(self.root,self.request(),self.out); args=verify(self.out,m['manifestSha256'])
        self.assertEqual(m['references'],[])
        self.assertNotIn('referenced_image_paths',args)
        self.assertEqual(m['mode'],'prompt')
        self.assertNotIn('atlasVersion',m);self.assertNotIn('trialOnly',m)
        profile=read(self.root/'skills/reference-style-3d/references/prompt-profile.json')
        style=self.root/profile['styleBlock']
        self.assertEqual(m['recipe']['styleBlockSha256'],sha(style))
        self.assertIn(style.read_text().strip(),args['prompt'])
        self.assertEqual(m['request']['userBrief'],'Кольцо в футляре')

    def test_selected_is_exact_deduplicated_and_materials_do_not_append(self):
        m=prepare(self.root,self.request(referenceMode='selected',
            styleReferenceIds=['jewelry','jewelry'],referenceReason='Compare fine velvet response'),self.out)
        self.assertEqual([r['id'] for r in m['references']],['jewelry'])
        self.assertEqual(len(verify(self.out,m['manifestSha256'])['referenced_image_paths']),1)

    def test_ambiguous_reference_selection_is_rejected(self):
        for req in [self.request(styleReferenceIds=['jewelry']),
                    self.request(referenceMode='selected'),
                    self.request(referenceMode='selected',styleReferenceIds=['generated-probe']),
                    self.request(referenceMode='selected',styleReferenceIds='jewelry')]:
            with self.subTest(req=req),self.assertRaises(ValueError):select(self.root,req)

    def test_default_is_prompt_and_selected_needs_reason(self):
        refs,route=select(self.root,{'materials':['leather','paper']})
        self.assertEqual(refs,[]);self.assertEqual(route['mode'],'prompt')
        with self.assertRaisesRegex(ValueError,'referenceReason'):
            select(self.root,{'referenceMode':'selected','styleReferenceIds':['jewelry']})

    def test_prompt_edit_and_relocated_execution_need_no_plugin(self):
        source=self.root/'assets/originals/coin.png'
        m=prepare(self.root,self.request(editSource=str(source)),self.out)
        self.assertEqual([r['role'] for r in m['references']],['EDIT SOURCE'])
        moved=self.base/'moved';shutil.move(self.out,moved)
        shutil.rmtree(self.root)
        args=verify(moved,m['manifestSha256'])
        self.assertEqual(len(args['referenced_image_paths']),1)
        self.assertTrue(Path(args['referenced_image_paths'][0]).is_relative_to(moved.resolve()))
        self.assertTrue(Path(args['referenced_image_paths'][0]).is_file())

    def test_background_and_extra_argument_tampering_rejected(self):
        m=prepare(self.root,self.request(),self.out)
        original=read(self.out/'tool-request.json')
        for change in [{'transparent_background':True},{'num_last_images_to_include':1}]:
            dump(self.out/'tool-request.json',dict(original,**change))
            with self.assertRaises(ValueError):verify(self.out,m['manifestSha256'])

    def test_generated_artifact_receipt_has_no_fabricated_call_id(self):
        m=prepare(self.root,self.request(),self.out)
        actual=self.base/'actual.json';dump(actual,verify(self.out,m['manifestSha256']))
        generated=self.root/'assets/originals/coin.png'
        cmd=[sys.executable,str(self.root/'scripts/prepare_generation.py'),'record-submission',
             '--execution',str(self.out),'--expected-manifest-sha256',m['manifestSha256'],'--arguments',str(actual),'--generated-file',str(generated)]
        r=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        receipt=read(self.out/'submission.json')
        self.assertIsNone(receipt['imagegenCallId'])
        self.assertEqual(receipt['observedHandle']['type'],'generated-artifact')
        self.assertEqual(receipt['observedHandle']['sha256'],sha(generated))
        self.assertIn('does not independently prove',receipt['evidenceLimit'])

    def test_missing_generated_artifact_creates_no_receipt(self):
        m=prepare(self.root,self.request(),self.out)
        actual=self.base/'actual.json';dump(actual,verify(self.out,m['manifestSha256']))
        r=subprocess.run([sys.executable,str(self.root/'scripts/prepare_generation.py'),
            'record-submission','--execution',str(self.out),'--expected-manifest-sha256',m['manifestSha256'],'--arguments',str(actual),
            '--generated-file',str(self.base/'missing.png')],capture_output=True)
        self.assertNotEqual(r.returncode,0);self.assertFalse((self.out/'submission.json').exists())

    def test_material_reference_copies_hash_and_adds_one_surface_rule(self):
        maps=['silver-polished.png','short-pile.png']
        refs=[dict(path=str(self.root/'assets/materials/cards'/name),role='MATERIAL REFERENCE') for name in maps]
        m=prepare(self.root,self.request(userReferences=refs),self.out)
        args=verify(self.out,m['manifestSha256'])
        self.assertEqual(len(m['references']),2)
        self.assertEqual(len(args['referenced_image_paths']),2)
        self.assertEqual(args['prompt'].count('MATERIAL REFERENCE images supply'),1)
        self.assertNotIn('03-composition',args['prompt'])
        self.assertEqual(m['recipe']['version'],read(self.root/'skills/reference-style-3d/references/prompt-profile.json')['version'])
        for ref,original in zip(m['references'],refs):
            self.assertEqual(ref['role'],'MATERIAL REFERENCE')
            self.assertEqual(ref['referenceType'],'material')
            self.assertEqual(ref['sha256'],sha(original['path']))
            self.assertEqual(sha(self.out/ref['file']),sha(original['path']))

    def test_ordinary_style_reference_does_not_get_material_semantics(self):
        m=prepare(self.root,self.request(referenceMode='selected',
            styleReferenceIds=['jewelry'],referenceReason='Original geometry and velvet'),self.out)
        self.assertNotIn('MATERIAL REFERENCE images supply',verify(self.out,m['manifestSha256'])['prompt'])
        self.assertNotIn('referenceType',m['references'][0])
        self.assertEqual(m['references'][0]['role'],'STYLE REFERENCE')

    def test_material_reference_with_originals_retains_distinct_roles(self):
        material=self.root/'assets/materials/cards/silver-polished.png'
        request=self.request(referenceMode='selected',styleReferenceIds=['jewelry'],
            referenceReason='Original shape language',userReferences=[dict(path=str(material),role='MATERIAL REFERENCE')])
        m=prepare(self.root,request,self.out)
        self.assertEqual([r['role'] for r in m['references']],['STYLE REFERENCE','MATERIAL REFERENCE'])
        self.assertIn('Image 1: STYLE REFERENCE',verify(self.out,m['manifestSha256'])['prompt'])
        self.assertIn('Image 2: MATERIAL REFERENCE',verify(self.out,m['manifestSha256'])['prompt'])
        self.assertEqual(m['request'],request)


if __name__=='__main__':unittest.main()
