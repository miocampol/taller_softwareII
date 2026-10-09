"""Render the screenshots supplied by the user without moving or editing them."""


API_IMAGES = [
    ('image.png', 'Antes de paginar',
     'GET /api/users en el puerto 8001. La versión original devuelve un arreglo completo. '
     'La captura muestra HTTP 200, 2,13 s y 2,73 MB; la base de comparación contiene 10000 filas.'),
    ('image-1.png', 'Después de paginar: primera página',
     'Respuesta paginada con current_page=1 y data. La captura muestra HTTP 200, 127 ms y 3,22 KB. '
     'Corresponde a la primera página de la misma base de comparación.'),
    ('image-2.png', 'Segunda página',
     'GET /api/users?page=2&per_page=5 en el puerto 8002. '
     'La respuesta muestra current_page=2 y comienza en el ID 6; HTTP 200, 84 ms y 3,32 KB.'),
    ('image-3.png', 'Consulta de correos',
     'GET /api/users/emails?page=1&per_page=5 en el puerto 8000. '
     'Los cinco registros contienen únicamente id y email; HTTP 200, 1,54 s y 2,22 KB.'),
    ('image-5.png', 'Filtro de edad',
     'GET /api/users/over-twenty?page=1&per_page=5 en el puerto 8000. '
     'La respuesta muestra usuarios con birth_date anteriores al corte de veinte años. '
     'La captura registra HTTP 200, 573 ms y 3,29 KB.'),
]


def render_api_captures(root):
    lines = ['## Evidencia visual de las peticiones', '',
             'Capturas reales tomadas en Postman. Los tiempos y tamaños visibles son muestras '
             'individuales; pueden diferir de las mediciones CLI y HTTP anteriores. '
             'Los indicadores rojos de Test Results en las respuestas paginadas no acreditan pruebas '
             'aprobadas: debe revisarse el script de Postman, pues la respuesta ya es un objeto y no '
             'el arreglo de la versión anterior.', '']
    for index, (name, title, caption) in enumerate(API_IMAGES, 1):
        if (root / 'reports' / name).is_file():
            lines += [f'### Figura {index}. {title}', '', f'![{title}]({name})', '', f'*{caption}*', '']
    return lines


def render_locust_captures(root):
    lines = ['## Evidencia visual del cliente de Locust', '',
             'Las siguientes capturas se toman desde http://127.0.0.1:8089. '
             'Corresponden a una ejecución adicional desde la interfaz; los parámetros y las cifras '
             'deben identificarse en la propia captura o en su pie. No sustituyen los diagnósticos '
             'anteriores ni demuestran una prueba formal prolongada.', '']
    images = [('locust-estadisticas.png', 'Statistics: peticiones, fallos, RPS y percentiles por operación'),
              ('locust-graficos.png', 'Charts: evolución de usuarios, latencia y throughput'),
              ('locust-fallos.png', 'Failures: tipos de fallos y ocurrencias, si existen')]
    for name, caption in images:
        if (root / 'reports' / name).is_file():
            lines += [f'![{caption}]({name})', '', f'*{caption}*', '']
    if not (root / 'reports' / 'locust-estadisticas.png').is_file() or not (root / 'reports' / 'locust-graficos.png').is_file():
        lines += ['Para completar esta sección, guarda las capturas de **Statistics** y **Charts** '
                  'en `reports/locust-estadisticas.png` y `reports/locust-graficos.png`. '
                  'Si hay errores, agrega `reports/locust-fallos.png`. '
                  'Al regenerar el informe se incorporarán automáticamente.', '']
    return lines
