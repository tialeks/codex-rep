import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from compile_settings import compile_settings
from prepare_generation import ROOT, prepare, verify
from reference_guidance import selected
from render_controls import initial_settings, reference_payload


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ReferenceBindingTest(unittest.TestCase):
    def setUp(self):
        self.source = ROOT / 'assets/originals/coin.png'
        self.image = dict(path=str(self.source.resolve()), name='Монета', sha256=digest(self.source))
        self.settings = dict(settingsVersion=3, topic='Camping', graphicType='group', detailLevel='rich',
                             arrangement='horizontal', count=4, camera='front', creativity=3, whiteBase=True,
                             background='white', palette='custom', colors=['#123456'], effects=[], recognizable=True,
                             materials=dict(mode='selected', base='wood', accents=['paper']),
                             reference=dict(facets=['palette'], note='', image=self.image))

    def request(self, **extra):
        return dict(settings=copy.deepcopy(self.settings), prompt='A camping backpack.', **extra)

    def test_bound_image_is_attached_once_and_snapshot_stays_immutable(self):
        request = self.request()
        before = copy.deepcopy(request)
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'execution'
            manifest = prepare(ROOT, request, out)
            self.assertEqual(request, before)
            self.assertEqual(manifest['request'], before)
            guides = [r for r in manifest['references'] if r['role'] == 'GUIDANCE REFERENCE']
            self.assertEqual(len(guides), 1)
            self.assertEqual(guides[0]['imageBinding'], self.image)
            self.assertEqual(guides[0]['sha256'], self.image['sha256'])
            self.assertEqual(guides[0]['facets'], ['palette'])
            self.assertEqual(len(verify(out, manifest['manifestSha256'])['referenced_image_paths']), 2)
            self.assertIn('materialSheet', manifest)  # materials were NOT selected for transfer
            self.assertNotIn(self.image['path'], (out / 'prompt.txt').read_text())

    def test_only_material_facet_suppresses_manual_material_sheet(self):
        for facets, expected in ((['palette'], True), (['materials'], False)):
            request = self.request()
            request['settings']['reference']['facets'] = facets
            with tempfile.TemporaryDirectory() as directory:
                out = Path(directory) / 'execution'
                manifest = prepare(ROOT, request, out)
                self.assertEqual('materialSheet' in manifest, expected)
                verify(out, manifest['manifestSha256'])

    def test_missing_and_tampered_bound_image_fail_before_execution_creation(self):
        for image, message in ((dict(self.image, path='/no-such-reference/image.png'), 'Missing bound'),
                               (dict(self.image, sha256='0' * 64), 'checksum mismatch')):
            request = self.request()
            request['settings']['reference']['image'] = image
            with tempfile.TemporaryDirectory() as directory:
                out = Path(directory) / 'execution'
                with self.assertRaisesRegex(ValueError, message):
                    prepare(ROOT, request, out)
                self.assertFalse(out.exists())

    def test_image_change_during_copy_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'execution'
            def wrong_copy(_source, target):
                Path(target).write_bytes(b'changed during copy')
            with patch('prepare_generation.shutil.copyfile', side_effect=wrong_copy):
                with self.assertRaisesRegex(ValueError, 'changed while preparing'):
                    prepare(ROOT, self.request(), out)
            self.assertFalse((out / 'manifest.json').exists())

    def test_same_explicit_guide_deduplicates_but_conflict_and_duplicate_guides_fail(self):
        guide = dict(path=self.image['path'], role='GUIDANCE REFERENCE')
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'execution'
            manifest = prepare(ROOT, self.request(userReferences=[guide]), out)
            self.assertEqual(sum(r['role'] == 'GUIDANCE REFERENCE' for r in manifest['references']), 1)
        for refs, message in (([guide, guide], 'Duplicate'),
                              ([dict(guide, path='/different.png')], 'conflicts')):
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaisesRegex(ValueError, message):
                    prepare(ROOT, self.request(userReferences=refs), Path(directory) / 'execution')

    def test_legacy_explicit_guide_remains_valid_and_unbound_submission_waits_for_image(self):
        request = self.request()
        del request['settings']['reference']['image']
        # Compiling/sending this snapshot is valid; prepare waits for an exact file.
        self.assertIn('GUIDANCE REFERENCE', compile_settings(ROOT, request['settings']))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'exactly one'):
                prepare(ROOT, request, Path(directory) / 'missing')
            request['userReferences'] = [dict(path=self.image['path'], role='GUIDANCE REFERENCE')]
            out = Path(directory) / 'legacy'
            manifest = prepare(ROOT, request, out)
            self.assertNotIn('imageBinding', manifest['references'][0])
            verify(out, manifest['manifestSha256'])

    def test_binding_without_facets_is_preserved_but_never_attached(self):
        request = self.request()
        request['settings']['reference']['facets'] = []
        request['settings']['reference']['image']['path'] = '/inactive-does-not-need-to-exist.png'
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'inactive'
            manifest = prepare(ROOT, request, out)
            self.assertFalse(any(r['role'] == 'GUIDANCE REFERENCE' for r in manifest['references']))
            self.assertEqual(manifest['request'], request)
            self.assertIn('materialSheet', manifest)
            verify(out, manifest['manifestSha256'])

    def test_binding_validation_rejects_thumbnail_relative_path_and_bad_identity(self):
        invalid = [dict(self.image, thumbnail='data:image/png;base64,AA=='),
                   dict(self.image, path='relative.png'), dict(self.image, sha256='abc'),
                   dict(self.image, name=''), dict(self.image, name='bad\nname'),
                   {'path': self.image['path'], 'sha256': self.image['sha256']}]
        for binding in invalid:
            settings = copy.deepcopy(self.settings)
            settings['reference']['image'] = binding
            with self.subTest(binding=binding), self.assertRaises(ValueError):
                selected(ROOT, settings)
        settings = copy.deepcopy(self.settings)
        settings['reference']['image'] = None
        self.assertEqual(selected(ROOT, settings), ['palette'])

    def test_copied_image_remains_portable_and_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'original.png'
            source.write_bytes(self.source.read_bytes())
            request = self.request()
            request['settings']['reference']['image']['path'] = str(source)
            out = Path(directory) / 'execution'
            manifest = prepare(ROOT, request, out)
            source.unlink()
            args = verify(out, manifest['manifestSha256'])
            Path(args['referenced_image_paths'][0]).write_bytes(b'changed after prepare')
            with self.assertRaisesRegex(ValueError, 'reference changed'):
                verify(out, manifest['manifestSha256'])


class ReferenceRendererTest(unittest.TestCase):
    setUp = ReferenceBindingTest.setUp
    request = ReferenceBindingTest.request
    def test_reference_preview_has_binding_but_state_has_no_thumbnail(self):
        image = reference_payload(str(self.source.resolve()), 'Выбранная монета')
        self.assertTrue(image['thumbnail'].startswith('data:image/png;base64,'))
        self.assertEqual(image['sha256'], self.image['sha256'])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'request.json'
            path.write_text(json.dumps(self.request()))
            restored = initial_settings(path, image)
            self.assertEqual(restored['reference']['image']['name'], 'Выбранная монета')
            self.assertNotIn('thumbnail', restored['reference']['image'])
            self.assertEqual(restored['materials'], self.settings['materials'])
            self.assertNotIn('image', initial_settings(path, None)['reference'])
            self.assertEqual(json.loads(path.read_text())['settings'], self.settings)

    def test_renderer_bootstraps_explicit_image_and_never_reuses_snapshot_image(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            request = directory / 'request.json'
            request.write_text(json.dumps(self.request()))
            for explicit in (True, False):
                output = directory / ('bound.html' if explicit else 'unbound.html')
                command = [sys.executable, str(ROOT / 'scripts/render_controls.py'), '--output', str(output), '--settings', str(request)]
                if explicit:
                    command += ['--reference', self.image['path'], '--reference-name', 'Монета </script>']
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                html = output.read_text()
                def bootstrap(ident):
                    return json.loads(re.search(r'<script id="' + ident + r'" type="application/json">(.*?)</script>', html, re.S)[1])
                library = bootstrap('r-reference-library')
                settings = bootstrap('r-initial-settings')['settings']
                self.assertEqual(library['image'] is not None, explicit)
                self.assertEqual('image' in settings['reference'], explicit)
                self.assertNotIn('thumbnail', settings['reference'].get('image', {}))
                self.assertEqual(settings['reference']['facets'], ['palette'])
                self.assertEqual(settings['materials'], self.settings['materials'])
                self.assertLess(len(html.encode()), 1_000_000)

    def test_reference_name_without_image_and_relative_path_fail(self):
        with self.assertRaisesRegex(ValueError, 'requires --reference'):
            reference_payload(None, 'orphan')
        with self.assertRaisesRegex(ValueError, 'absolute'):
            reference_payload('relative.png')


if __name__ == '__main__':
    unittest.main()
