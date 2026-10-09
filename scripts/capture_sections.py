"""Persistent screenshot slots, independent of regenerated measurements."""

import json


CAPTURES = [
    ('01-antes-users.png', 'Antes de paginar', 'GET http://127.0.0.1:8001/api/users',
     'Postman: muestra método, URL, HTTP 200, tiempo, tamaño y el comienzo del arreglo JSON. En Test Results debe comprobarse que hay 10000 filas.',
     'Versión afbb181; base locust_lab_comparison, 10000 filas. El listado original entrega todas las filas en un arreglo.'),
    ('02-despues-users.png', 'Después de paginar', 'GET http://127.0.0.1:8002/api/users?page=1&per_page=5',
     'Muestra HTTP 200, tiempo, tamaño, total=10000, current_page=1, per_page=5 y data con cinco usuarios.',
     'Versión paginada; misma base y dataset que la figura anterior. La respuesta limita data a cinco filas.'),
    ('03-segunda-pagina.png', 'Segunda página', 'GET http://127.0.0.1:8002/api/users?page=2&per_page=5',
     'Muestra current_page=2, per_page=5 y los IDs 6 a 10; compáralos con los IDs 1 a 5 de la primera página.',
     'Base de comparación de 10000 filas: las páginas contienen registros diferentes, ordenados por ID.'),
    ('04-correos.png', 'Consulta de correos', 'GET http://127.0.0.1:8000/api/users/emails?page=1&per_page=5',
     'Muestra HTTP 200, los metadatos de paginación y data con únicamente id y email.',
     'API principal, dataset masivo. El endpoint de correos devuelve únicamente los campos solicitados.'),
    ('05-mayores-veinte.png', 'Filtro de edad', 'GET http://127.0.0.1:8000/api/users/over-twenty?page=1&per_page=5',
     'Muestra HTTP 200, cutoff_date y birth_date de los usuarios devueltos; todas las fechas deben ser anteriores al corte.',
     'API principal, dataset masivo. El filtro devuelve usuarios con edad estrictamente superior a veinte años.'),
    ('06-bulk-201.png', 'Creación de tres usuarios', 'POST http://127.0.0.1:8000/api/users/bulk',
     'Usa la petición 06 de la colección. Muestra el cuerpo con tres usuarios y la respuesta 201 con sus IDs y correos.',
     'API principal. El lote válido crea exactamente tres usuarios; esta petición aumenta el dataset.'),
    ('07-bulk-422.png', 'Rechazo de correos duplicados', 'POST http://127.0.0.1:8000/api/users/bulk',
     'Envía la petición 07 después de la 06, sin cambiar los correos. Muestra HTTP 422 y errors para los correos.',
     'API principal. La validación rechaza un lote cuyos correos ya existen en la base.'),
    ('08-pruebas.png', 'Pruebas automatizadas', 'Terminal, desde la raíz del proyecto',
     'Ejecuta PHP y Python con los comandos de GUIA.md; muestra ambos resultados aprobados en una captura legible.',
     'Pruebas funcionales y de contratos aprobadas. PHPUnit utiliza SQLite en memoria.'),
]

SCENARIOS = {
    'carga': ('load-diagnostic', '5', '1', '90 segundos más cierre', 'Respuestas válidas, con incumplimiento del objetivo de latencia.'),
    'estres': ('stress-diagnostic', '5/10/20/40/80/160', '5/5/10/10/20/40', '6 etapas de 10 segundos más cierre', 'Saturación local: fallos de transporte y latencias cercanas al timeout.'),
    'capacidad': ('capacity-diagnostic', '1', '1', '60 segundos más cierre', 'Diagnóstico corto; no acredita resistencia durante una hora.'),
}


def default_details():
    details = {}
    for scenario, (prefix, users, rate, duration, conclusion) in SCENARIOS.items():
        for view in ['estadisticas', 'graficos']:
            details[f'{scenario}-{view}'] = {
                'tipo': 'diagnóstico abreviado', 'usuarios': users, 'spawn_rate': rate,
                'duracion': duration, 'dataset': 'al menos 1500000 filas; los POST agregan registros',
                'host': 'http://127.0.0.1:8000', 'fecha': '2026-10-09',
                'fuente': f'evidence/html/{prefix}.html', 'conclusion': conclusion,
            }
    details['estres-fallos'] = dict(details['estres-estadisticas'])
    return details


def slot(directory, name, caption):
    if (directory / name).is_file():
        return [f'![{caption}](capturas/{name})', '', f'*{caption}*', '']
    return [f'**Captura pendiente:** guarda `reports/capturas/{name}`.', '', f'*Pie previsto: {caption}*', '']


def metadata_caption(scenario, metadata):
    keys = ['tipo', 'usuarios', 'spawn_rate', 'duracion', 'dataset', 'host', 'fecha', 'fuente', 'conclusion']
    values = {key: metadata.get(key, 'pendiente de registrar') for key in keys}
    return (f"Escenario {scenario}; {values['tipo']}; usuarios: {values['usuarios']}; "
            f"spawn rate: {values['spawn_rate']}; duración: {values['duracion']}; "
            f"dataset: {values['dataset']}; host: {values['host']}; fecha: {values['fecha']}. "
            f"Fuente: {values['fuente']}. Conclusión: {values['conclusion']}")


def render_captures(root):
    directory = root / 'reports' / 'capturas'
    details_path = directory / 'detalles.json'
    details = json.loads(details_path.read_text(encoding='utf-8-sig')) if details_path.exists() else default_details()
    lines = ['## Capturas de evidencia', '',
             'Se recomiendan **14 capturas**, más una opcional de fallos. Las imágenes se agregan '
             'automáticamente al regenerar este informe cuando existen sus archivos. '
             'Instrucciones completas: [guía de capturas](capturas/GUIA.md).', '',
             'Las comparaciones HTTP usan 10000 filas en una base separada. '
             'Las capturas de Locust de esta sección corresponden a los diagnósticos registrados; '
             'para reproducir sus cifras, abre los HTML conservados en `evidence/html/`. '
             'No sustituyas esas imágenes por otra ejecución sin identificarla.', '']
    for name, title, request, instruction, caption in CAPTURES:
        lines += [f'### {name[:2]}. {title}', '', f'**Petición o herramienta:** `{request}`.', '', instruction, '']
        lines += slot(directory, name, caption)
    index = 9
    for scenario, (prefix, *_unused) in SCENARIOS.items():
        for view in ['estadisticas', 'graficos']:
            name = f'{index:02d}-locust-{scenario}-{view}.png'
            instruction = ('Muestra las cuatro operaciones, peticiones, fallos, RPS y p95.' if view == 'estadisticas'
                           else 'Muestra los gráficos de usuarios, latencia y peticiones por segundo con sus ejes temporales.')
            lines += [f'### {index:02d}. Locust: {scenario}, {view}', '',
                      f'Abre [el reporte de esta ejecución](evidence/html/{prefix}.html). {instruction}', '']
            lines += slot(directory, name, metadata_caption(scenario, details.get(f'{scenario}-{view}', {})))
            index += 1
    lines += ['### 15. Fallos de estrés (opcional)', '',
              'Abre la sección Failures del HTML de estrés y muestra el tipo de fallo y sus ocurrencias.', '']
    lines += slot(directory, '15-locust-estres-fallos.png', metadata_caption('estres', details.get('estres-fallos', {})))
    formal = [(scenario, view) for scenario in SCENARIOS for view in ['estadisticas', 'graficos']
              if (directory / 'formales' / f'{scenario}-{view}.png').is_file()]
    if formal:
        lines += ['## Evidencias de nuevas pruebas formales', '',
                  'Estas imágenes pertenecen a ejecuciones adicionales. Sus resultados no reemplazan '
                  'las cifras de los diagnósticos anteriores. Registra los parámetros y los HTML/CSV '
                  'correspondientes en detalles.json antes de entregar.', '']
        for scenario, view in formal:
            lines += [f'### {scenario}: {view}', '']
            lines += slot(directory, f'formales/{scenario}-{view}.png',
                          metadata_caption(scenario, details.get(f'formal-{scenario}-{view}', {})))
    return lines
