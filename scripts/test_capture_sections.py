import importlib.util
from pathlib import Path
import tempfile
import unittest

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
            self.assertIn('ejecución adicional', text)
            self.assertNotIn('Para completar esta sección', text)
            self.assertNotIn('](locust-fallos.png)', text)


if __name__ == '__main__':
    unittest.main()
