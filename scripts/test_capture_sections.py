import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('capture_sections', Path(__file__).with_name('capture_sections.py'))
captures = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(captures)


class CaptureTests(unittest.TestCase):
    def test_missing_images_have_placeholders_without_broken_image_links(self):
        with tempfile.TemporaryDirectory() as temp:
            text = '\n'.join(captures.render_captures(Path(temp)))
            self.assertEqual(15, text.count('**Captura pendiente:**'))
            self.assertNotIn('![', text)
            self.assertIn('diagnóstico abreviado', text)

    def test_existing_image_and_custom_caption_survive_repeated_rendering(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / 'reports' / 'capturas'
            folder.mkdir(parents=True)
            (folder / '09-locust-carga-estadisticas.png').write_bytes(b'test-fixture')
            data = captures.default_details()
            data['carga-estadisticas']['conclusion'] = 'Conclusión registrada por el equipo'
            (folder / 'detalles.json').write_text(json.dumps(data), encoding='utf-8')
            first = '\n'.join(captures.render_captures(root))
            self.assertEqual(first, '\n'.join(captures.render_captures(root)))
            self.assertIn('(capturas/09-locust-carga-estadisticas.png)', first)
            self.assertIn('Conclusión registrada por el equipo', first)
            self.assertTrue((folder / '09-locust-carga-estadisticas.png').exists())

    def test_formal_evidence_is_separate_and_missing_parameters_remain_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / 'reports' / 'capturas' / 'formales'
            folder.mkdir(parents=True)
            (folder / 'capacidad-graficos.png').write_bytes(b'test-fixture')
            text = '\n'.join(captures.render_captures(root))
            self.assertIn('## Evidencias de nuevas pruebas formales', text)
            self.assertIn('pendiente de registrar', text)
            self.assertIn('no reemplazan', text)


if __name__ == '__main__':
    unittest.main()
