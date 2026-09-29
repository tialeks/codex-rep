import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('palettes.py')


class PalettesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = self.root / 'store'

    def run_cli(self, *args, root=None, success=True):
        env = dict(os.environ, REFERENCE_STYLE_3D_DATA_DIR=str(root or self.store))
        p = subprocess.run([sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0 if success else 1, p.stdout + p.stderr)
        result = json.loads(p.stdout)
        self.assertEqual(result['ok'], success)
        return result

    def add(self, name='Моя', *colors):
        return self.run_cli('add', '--name', name, '--colors', *(colors or ('aabbcc', '#123456')))

    def test_data_directory_inside_plugin_is_rejected_without_writes(self):
        target=SCRIPT.resolve().parents[1]/'forbidden-personal-data'
        self.assertFalse(target.exists())
        result=self.run_cli('add','--name','Blocked','--colors','#123456',root=target,success=False)
        self.assertIn('outside the plugin',result['error'])
        self.assertFalse(target.exists())

    def test_persistent_add_list_normalization_remove(self):
        row = self.add()['palettes'][0]
        self.assertEqual(row['colors'], ['#AABBCC', '#123456'])
        self.assertEqual(self.run_cli('list')['palettes'], [row])
        self.assertTrue(self.run_cli('remove', '--id', row['id'])['changed'])
        self.assertEqual(self.run_cli('list')['palettes'], [])
        self.assertFalse(self.run_cli('remove', '--id', row['id'])['changed'])

    def test_duplicate_and_explicit_replace(self):
        first = self.add()['palettes'][0]
        self.assertFalse(self.add()['changed'])
        self.run_cli('add', '--name', 'моя', '--colors', '#FFFFFF', success=False)
        r = self.run_cli('add', '--name', 'Моя', '--colors', 'FFFFFF', '--replace')['palettes'][0]
        self.assertEqual(r['id'], first['id'])
        self.assertEqual(r['colors'], ['#FFFFFF'])

    def test_invalid_data_does_not_write(self):
        for name, colors in [('', ['FFFFFF']), ('x'*61, ['FFFFFF']), ('x', ['red']), ('x', ['12345']), ('x', ['123456']*9)]:
            self.run_cli('add', '--name', name, '--colors', *colors, success=False)
        self.assertFalse((self.store / 'palettes.json').exists())

    def test_corruption_preserved(self):
        self.store.mkdir()
        path = self.store / 'palettes.json'
        for content in ('{broken', '{"schemaVersion":2,"palettes":[]}', '{"schemaVersion":1,"palettes":[{}]}'):
            path.write_text(content)
            self.run_cli('add', '--name', 'x', '--colors', '123456', success=False)
            self.run_cli('list', success=False)
            self.assertEqual(path.read_text(), content)

    def test_import_validates_every_row_before_write(self):
        self.add()
        store = self.store / 'palettes.json'
        before = store.read_bytes()
        source = self.root / 'bad.json'
        source.write_text(json.dumps({'schemaVersion': 1, 'palettes': [{'id':'x','name':'Good','colors':['123456']}, {'id':'y','name':'Bad','colors':['no']}]}))
        self.run_cli('import', '--file', str(source), success=False)
        self.assertEqual(store.read_bytes(), before)

    def test_portable_export_import_and_conflict(self):
        original = self.add()['palettes']
        export = self.root / 'portable.json'
        self.run_cli('export', '--output', str(export))
        data = json.loads(export.read_text())
        self.assertEqual(set(data), {'schemaVersion', 'palettes'})
        other = self.root / 'other'
        self.assertEqual(self.run_cli('import', '--file', str(export), root=other)['palettes'], original)
        self.assertFalse(self.run_cli('import', '--file', str(export), root=other)['changed'])
        data['palettes'][0]['colors'] = ['#000000']
        export.write_text(json.dumps(data))
        self.run_cli('import', '--file', str(export), root=other, success=False)
        self.assertTrue(self.run_cli('import', '--file', str(export), '--replace', root=other)['changed'])

    def test_export_preserves_corrupt_existing_file(self):
        self.add()
        dest = self.root / 'bad.json'
        dest.write_text('not json')
        self.run_cli('export', '--output', str(dest), success=False)
        self.assertEqual(dest.read_text(), 'not json')

    def test_cap_and_duplicate_ids(self):
        source = self.root / 'many.json'
        rows = [{'id': str(i), 'name': str(i), 'colors':['123456']} for i in range(128)]
        source.write_text(json.dumps({'schemaVersion':1,'palettes':rows}))
        self.run_cli('import', '--file', str(source))
        self.run_cli('add', '--name', 'Overflow', '--colors', '123456', success=False)
        self.assertEqual(len(self.run_cli('list')['palettes']), 128)
        rows[1]['id'] = rows[0]['id']
        source.write_text(json.dumps({'schemaVersion':1,'palettes':rows}))
        self.run_cli('import', '--file', str(source), success=False)

    def test_concurrent_writers_do_not_lose_updates(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda i: self.add(str(i)), range(16)))
        self.assertEqual(len(self.run_cli('list')['palettes']), 16)

    def test_empty_list_and_export_do_not_create_store(self):
        self.assertEqual(self.run_cli('list')['palettes'], [])
        self.assertFalse(self.store.exists())
        self.run_cli('export', '--output', str(self.root/'export.json'))
        self.assertFalse(self.store.exists())

    def test_list_and_render_work_with_unwritable_lock(self):
        self.add()
        lock = self.store/'palettes.lock'
        lock.unlink()
        lock.mkdir()  # Any attempt to open this for writing must fail.
        self.assertEqual(len(self.run_cli('list')['palettes']), 1)
        env = dict(os.environ, REFERENCE_STYLE_3D_DATA_DIR=str(self.store))
        output = self.root/'controls.html'
        r = subprocess.run([sys.executable,str(SCRIPT.with_name('render_controls.py')),
                            '--output',str(output)],env=env,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn('"loaded": true',output.read_text())
        import re
        catalog=json.loads(re.search(r'<script id="r-catalog" type="application/json">(.*?)</script>',output.read_text(),re.S)[1])
        source=json.loads((SCRIPT.parents[1]/'skills/reference-style-3d/references/effects.json').read_text())
        self.assertEqual(catalog['effects'],source)


if __name__ == '__main__':
    unittest.main()
