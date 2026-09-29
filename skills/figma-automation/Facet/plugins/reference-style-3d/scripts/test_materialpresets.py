"""Validate the separately selectable material combinations."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class MaterialPresetsTest(unittest.TestCase):
    def test_catalog_contract(self):
        presets = json.loads((ROOT / 'skills/reference-style-3d/references/material-presets.json').read_text())
        available = {card['id'] for card in json.loads((ROOT / 'assets/materials/catalog.json').read_text())['cards']}
        self.assertGreaterEqual(len(presets), 20)
        self.assertLessEqual(len(presets), 24)
        self.assertEqual(len({p['name'] for p in presets}), len(presets))
        covered = set()
        for preset in presets:
            with self.subTest(name=preset['name']):
                self.assertEqual(set(preset), {'name', 'ids'})
                self.assertTrue(preset['name'].strip())
                ids = preset['ids']
                self.assertGreaterEqual(len(ids), 2)
                self.assertLessEqual(len(ids), 12)
                self.assertEqual(len(set(ids)), len(ids))
                self.assertFalse(set(ids) - available)
                covered.update(ids)
        self.assertEqual(covered, available)

if __name__ == '__main__':
    unittest.main()
