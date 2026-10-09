import importlib.util
from pathlib import Path
import tempfile
import unittest
import sys

SPEC = importlib.util.spec_from_file_location('capture_sections', Path(__file__).with_name('capture_sections.py'))
captures = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(captures)


class CaptureTests(unittest.TestCase):
    def test_missing_images_do_not_create_broken_image_links(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            text = '\n'.join(captures.render_api_captures(root) + captures.render_locust_captures(root))
            self.assertNotIn('![', text)
            self.assertNotIn('Captura pendiente', text)
            self.assertNotIn('GUIA.md', text)
            self.assertIn('reports/locust-estadisticas.png', text)

    def test_user_images_are_included_in_order_and_not_modified(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / 'reports'
            folder.mkdir()
            for name, _, _ in captures.API_IMAGES:
                (folder / name).write_bytes(b'test-fixture')
            first = '\n'.join(captures.render_api_captures(root))
            self.assertEqual(first, '\n'.join(captures.render_api_captures(root)))
            self.assertEqual(5, first.count('!['))
            self.assertIn('Filtro de edad', first)
            for name, _, _ in captures.API_IMAGES:
                self.assertIn(f']({name})', first)
                self.assertEqual(b'test-fixture', (folder / name).read_bytes())

    def test_client_images_are_separate_from_previous_measurements(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / 'reports'
            folder.mkdir()
            for name in ['locust-estadisticas.png', 'locust-graficos.png']:
                (folder / name).write_bytes(b'test-fixture')
            text = '\n'.join(captures.render_locust_captures(root))
            self.assertEqual(2, text.count('!['))
            self.assertIn('no al cierre de la ejecución', text)
            self.assertNotIn('Para completar esta sección', text)
            self.assertNotIn('](locust-fallos.png)', text)

    def test_user_runs_survive_regeneration_without_inventing_thousand_users(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / 'reports'
            folder.mkdir()
            for name in ['image-6.png', 'image-7.png']:
                (folder / name).write_bytes(b'test-fixture')
            text = '\n'.join(captures.render_locust_captures(root))
            self.assertIn('84 peticiones, 0 fallos', text)
            self.assertIn('47 peticiones, 5 fallos', text)
            self.assertIn('no hay una captura disponible', text)
            self.assertEqual(2, text.count('!['))

    def test_readme_sync_rebases_links_and_preserves_setup_instructions(self):
        sys.path.insert(0, str(Path(__file__).parent))
        spec = importlib.util.spec_from_file_location('write_report', Path(__file__).with_name('write-report.py'))
        report_module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(report_module)
        finally:
            sys.path.pop(0)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            readme = root / 'README.md'
            original = '# Project\n\n<!-- BEGIN LOCUST REPORT -->\nold\n<!-- END LOCUST REPORT -->\n\n## Installation\nPreserve me.\n'
            readme.write_text(original, encoding='utf-8')
            report = '# Report\n\n![Screenshot](image-6.png)\n\n[Evidence](evidence/results.json)\n\n[Setup](../README.md)\n'
            report_module.sync_readme(root, report)
            first = readme.read_text(encoding='utf-8')
            report_module.sync_readme(root, report)
            self.assertEqual(first, readme.read_text(encoding='utf-8'))
            self.assertIn('](reports/image-6.png)', first)
            self.assertIn('](reports/evidence/results.json)', first)
            self.assertIn('](#inicio-rapido)', first)
            self.assertIn('## Installation\nPreserve me.', first)
            self.assertNotIn('\nold\n', first)


if __name__ == '__main__':
    unittest.main()
