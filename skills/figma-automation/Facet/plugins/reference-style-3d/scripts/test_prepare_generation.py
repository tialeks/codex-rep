import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import subprocess
import sys
from prepare_generation import ROOT, dump, prepare, read, select, sha, verify

class PreparationTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name); self.root=self.base/'plugin'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('__pycache__'))
        self.out=self.base/'execution'
    def test_experimental_modes_reject_before_writing(self):
        for mode in ('auto', 'atlas', 'atlas-trial'):
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'Unsupported referenceMode'):
                prepare(self.root, {'prompt':'Test', 'referenceMode':mode}, self.out)
            self.assertFalse(self.out.exists())

    def test_originals_do_not_depend_on_experimental_routing(self):
        path = self.root/'skills/reference-style-3d/references/reference-routing.json'
        registry = read(path)
        dump(path, {'originals':registry['originals']})
        refs, route = select(self.root, {'referenceMode':'originals', 'materials':['paper']})
        self.assertEqual(route['mode'], 'originals')
        self.assertEqual([r['id'] for r in refs], ['pack-strip','payment-device','burger-kraft'])

    def test_observed_cell_receipt_and_argument_check(self):
        m=prepare(self.root,{'prompt':'x'},self.out)
        args=self.base/'actual.json';dump(args,verify(self.out,m['manifestSha256']))
        cli=[sys.executable,str(self.root/'scripts/prepare_generation.py'),'record-submission','--execution',str(self.out),'--expected-manifest-sha256',m['manifestSha256'],'--arguments',str(args)]
        both=subprocess.run(cli+['--tool-call-id','test-call','--execution-handle','152'],capture_output=True)
        self.assertNotEqual(both.returncode,0);self.assertFalse((self.out/'submission.json').exists())
        altered=read(args);altered['prompt']='different';dump(args,altered)
        bad=subprocess.run(cli+['--execution-handle','152'],capture_output=True)
        self.assertNotEqual(bad.returncode,0);self.assertFalse((self.out/'submission.json').exists())
        dump(args,verify(self.out,m['manifestSha256']))
        good=subprocess.run(cli+['--execution-handle','152'],capture_output=True)
        self.assertEqual(good.returncode,0,good.stderr)
        receipt=read(self.out/'submission.json')
        self.assertIsNone(receipt['imagegenCallId']);self.assertIsNone(receipt['toolCallId'])
        self.assertEqual(receipt['observedHandle'],{'type':'functions-exec-cell','id':'152'})
    def test_exact_refs_edit_first_and_portable_execution(self):
        user=self.base/'user.png';shutil.copyfile(self.root/'assets/originals/coin.png',user)
        m=prepare(self.root,{'prompt':'Каменная арка с пробкой.','editSource':str(user),'materials':['paper'],'referenceMode':'originals'},self.out)
        self.assertEqual(m['references'][0]['role'],'EDIT SOURCE')
        self.assertEqual([r['id'] for r in m['references'][1:]],['pack-strip','payment-device','burger-kraft'])
        moved=self.base/'moved';shutil.move(self.out,moved);tool=verify(moved,m['manifestSha256'])
        self.assertTrue(all(str(moved) in p for p in tool['referenced_image_paths']))
        profile=read(self.root/'skills/reference-style-3d/references/prompt-profile.json')
        self.assertIn((self.root/profile['styleBlock']).read_text().strip(),tool['prompt'])
        self.assertEqual(m['recipe']['id'],profile['id'])
        self.assertIn('STYLE REFERENCE: transfer simplification',tool['prompt'])
        self.assertNotIn('atlasVersion',m);self.assertNotIn('trialOnly',m)
        self.assertEqual(m['status'],'prepared-not-submitted')
    def test_no_silent_limit_truncation(self):
        with self.assertRaisesRegex(ValueError,'limit 5'):
            m=prepare(self.root,{'prompt':'x','materials':['paper','leather','pvc','pearl'],'referenceMode':'originals'},self.out)
        self.assertFalse(self.out.exists())
    def test_path_escape_rejected(self):
        p=self.root/'skills/reference-style-3d/references/sources.json'; s=read(p);next(r for r in s if r['id']=='pack-strip')['path']='../outside.png';dump(p,s)
        with self.assertRaisesRegex(ValueError,'inside plugin'):prepare(self.root,{'prompt':'x','referenceMode':'originals'},self.out)
    def test_changed_execution_cannot_submit(self):
        m=prepare(self.root,{'prompt':'x'},self.out)
        (self.out/'prompt.txt').write_text('different')
        with self.assertRaisesRegex(ValueError,'prompt changed'):verify(self.out,m['manifestSha256'])
if __name__=='__main__':unittest.main()
