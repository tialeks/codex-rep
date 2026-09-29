"""Portable bundled collection installation, isolated from the user's library."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import presets


class BundledPresetsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'data'
        self.bundle = self.base / 'bundle'
        self.bundle.mkdir()
        self.shipped = presets.PLUGIN / 'assets/presets'
        self.rows = json.loads((self.shipped / 'catalog.json').read_text())['presets'][:2]
        for row in self.rows:
            target = self.bundle / row['preview']
            target.parent.mkdir(exist_ok=True)
            shutil.copyfile(self.shipped / row['preview'], target)
        self.catalog(self.rows)

    def catalog(self, rows):
        (self.bundle / 'catalog.json').write_text(json.dumps({'schemaVersion': 1, 'presets': rows}))

    def test_fresh_install_contains_all_284_bundled_presets(self):
        changed, data = presets.ensure_bundled_library(self.root)
        self.assertTrue(changed)
        self.assertEqual(len(data['presets']), 284)
        self.assertEqual(data['favorites'], [])
        self.assertTrue(all(row['source'] == 'collection' for row in data['presets']))
        for row in data['presets']:
            self.assertEqual((self.root / row['preview']).read_bytes(), (self.shipped / row['preview']).read_bytes())

    def test_existing_library_favorites_and_unrelated_data_survive_additive_update(self):
        presets.ensure_bundled_library(self.root, self.bundle)
        before = presets.read_store(self.root)
        personal = dict(copy.deepcopy(before['presets'][0]), id='personal-existing', source='personal')
        before['presets'].append(personal)
        before['favorites'] = [before['presets'][0]['id'], personal['id']]
        (self.root / 'presets.json').write_text(json.dumps(before))
        for relative in ('palettes.json', 'material-sets.json', 'generations/example/metadata.json'):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'untouched')
        new = dict(copy.deepcopy(self.rows[0]), id='collection-next-version')
        self.catalog(self.rows + [new])
        changed, after = presets.ensure_bundled_library(self.root, self.bundle)
        self.assertTrue(changed)
        self.assertEqual(after, dict(before, presets=before['presets'] + [new]))
        for relative in ('palettes.json', 'material-sets.json', 'generations/example/metadata.json'):
            self.assertEqual((self.root / relative).read_bytes(), b'untouched')
        with patch.object(presets, 'atomic_bytes', side_effect=AssertionError('No idempotent writes')):
            self.assertFalse(presets.ensure_bundled_library(self.root, self.bundle)[0])

    def test_conflicting_id_never_overwrites_existing_user_record(self):
        presets.ensure_bundled_library(self.root, self.bundle)
        before = (self.root / 'presets.json').read_bytes()
        self.catalog([dict(self.rows[0], name='Conflicting label'), dict(self.rows[1], id='new')])
        with self.assertRaisesRegex(presets.PresetError, 'immutable'):
            presets.ensure_bundled_library(self.root, self.bundle)
        self.assertEqual((self.root / 'presets.json').read_bytes(), before)

    def test_corrupt_bundle_never_commits_partial_metadata(self):
        presets.ensure_bundled_library(self.root, self.bundle)
        before = (self.root / 'presets.json').read_bytes()
        (self.bundle / self.rows[-1]['preview']).write_bytes(b'corrupt WebP')
        with self.assertRaisesRegex(presets.PresetError, 'digest'):
            presets.ensure_bundled_library(self.root, self.bundle)
        self.assertEqual((self.root / 'presets.json').read_bytes(), before)
        fresh = self.base / 'fresh-data'
        with self.assertRaisesRegex(presets.PresetError, 'digest'):
            presets.ensure_bundled_library(fresh, self.bundle)
        self.assertFalse(fresh.exists())

    def test_invalid_settings_and_path_escape_fail_before_writes(self):
        for invalid in (dict(self.rows[1], settings=dict(self.rows[1]['settings'], topic='Scene prose')),
                        dict(self.rows[1], preview='../outside.webp')):
            self.catalog([self.rows[0], invalid])
            with self.assertRaises(presets.PresetError):
                presets.ensure_bundled_library(self.root, self.bundle)
            self.assertFalse(self.root.exists())


if __name__ == '__main__':
    unittest.main()
