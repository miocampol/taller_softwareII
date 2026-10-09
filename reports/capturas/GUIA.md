# Guía para adjuntar capturas al informe

Adjunta **14 imágenes recomendadas** y, si quieres, una adicional de fallos de estrés. Usa los nombres exactos de esta guía. No necesitas capturar miles de filas: muestra el comienzo del JSON y los campos que prueban el comportamiento.

En Postman deja visibles **método, URL, código HTTP, tiempo y tamaño de respuesta**. Usa Body → Pretty → JSON para la respuesta. En el POST muestra también el cuerpo enviado. Mantén una escala que permita leer las cifras. Las imágenes deben corresponder a ejecuciones reales.

## Preparación del antes y después

Desde la raíz del proyecto, con MySQL iniciado:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare-comparison.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start-comparison.ps1
```

El primer comando crea o completa **locust_lab_comparison con exactamente 10000 filas**, exporta la versión anterior desde el commit **afbb181** y le copia sus dependencias compatibles. No elimina datos ni cambia `.env` o `locust_lab`. Si la base de comparación ya tiene más de 10000 filas, se detiene para no borrar nada.

El segundo comando inicia dos servidores locales:

- **Antes:** `http://127.0.0.1:8001`, código original sin paginación.
- **Después:** `http://127.0.0.1:8002`, código actual paginado.

Ambos consultan la misma base pequeña. Úsalos únicamente para los GET de comparación. Los PID y logs están en `reports/generated/comparison/`. Si los puertos ya están ocupados, los servidores pueden estar funcionando: comprueba las URLs antes de volver a iniciarlos. La API principal del dataset masivo continúa en el puerto **8000**.

La versión anterior devuelve un arreglo, sin `total` ni `data`. La versión actual devuelve un objeto con esos campos. Una comparación de tiempos tomada manualmente es una demostración; no sustituye las métricas de Locust ni permite atribuir una mejora estadística a una sola petición.

## Importar las peticiones en Postman

En Postman pulsa **Import** y selecciona `reports/capturas/peticiones.postman_collection.json`. Las variables de host ya apuntan a 8001, 8002 y 8000. La colección incluye comprobaciones en Test Results. Ejecuta las peticiones **01 a 07 en orden**.

Cada envío de la petición 06 genera un identificador nuevo para los correos. La petición 07 reutiliza el identificador anterior para provocar el 422. No modifiques esos correos entre ambas. El POST válido agrega tres filas a `locust_lab`; el rechazo no debe agregar ninguna. Referencia de las variables dinámicas: [documentación de Postman](https://learning.postman.com/docs/tests-and-scripts/write-scripts/variables-list/).

## Capturas de las peticiones

1. **`01-antes-users.png`** — GET `http://127.0.0.1:8001/api/users`. Muestra HTTP 200, el comienzo del arreglo, tiempo y tamaño. La comprobación de Postman debe indicar que hay **10000 usuarios**; puedes abrir Test Results para mostrarla si es necesario.
2. **`02-despues-users.png`** — GET `http://127.0.0.1:8002/api/users?page=1&per_page=5`. Muestra HTTP 200, `total: 10000`, `current_page: 1`, `per_page: 5` y cinco registros dentro de `data`. Incluye tiempo y tamaño para comparar con la captura anterior.
3. **`03-segunda-pagina.png`** — GET `http://127.0.0.1:8002/api/users?page=2&per_page=5`. Muestra `current_page: 2` y los IDs **6 a 10**, distintos de los **1 a 5** de la primera página.
4. **`04-correos.png`** — GET `http://127.0.0.1:8000/api/users/emails?page=1&per_page=5`. Muestra HTTP 200, paginación y registros que contengan únicamente `id` y `email`.
5. **`05-mayores-veinte.png`** — GET `http://127.0.0.1:8000/api/users/over-twenty?page=1&per_page=5`. Muestra HTTP 200, `cutoff_date` y `birth_date` anteriores al corte. Usa el corte de la respuesta del día de la captura.
6. **`06-bulk-201.png`** — POST válido de la colección, sobre `http://127.0.0.1:8000/api/users/bulk`. Muestra el cuerpo con tres usuarios y la respuesta **201** con los tres IDs y correos creados.
7. **`07-bulk-422.png`** — POST de correos duplicados, después del anterior. Muestra **422** y los errores de validación de los correos.
8. **`08-pruebas.png`** — Terminal con las pruebas aprobadas. Ejecuta:

```powershell
php -d error_reporting=8191 vendor\phpunit\phpunit\phpunit --testdox
.\.venv\Scripts\python.exe -m unittest loadtests.test_contracts
```

Como evidencia adicional, la colección incluye `GET /api/users?per_page=201`, que debe responder 422. Puedes adjuntar su captura aparte; no forma parte de las 14 principales.

## Capturas de Locust que coinciden con el informe actual

Para conservar las cifras ya documentadas, abre en tu navegador los **reportes HTML guardados** en `reports/evidence/html/`. Contienen las estadísticas y los gráficos del cierre de cada ejecución. Puedes abrirlos con doble clic. No hace falta volver a ejecutar Locust para fotografiar esos resultados.

- **`09-locust-carga-estadisticas.png`** y **`10-locust-carga-graficos.png`**: abre `load-diagnostic.html`. Diagnóstico de **5 usuarios**, spawn rate **1**, duración **90 segundos más cierre**. Estadísticas finales: **72 peticiones**, **0 fallos**, p95 agregado **6700 ms**.
- **`11-locust-estres-estadisticas.png`** y **`12-locust-estres-graficos.png`**: abre `stress-diagnostic.html`. Rampa de **5/10/20/40/80/160 usuarios**, spawn rates **5/5/10/10/20/40**, **10 segundos por etapa más cierre**. Estadísticas finales: **201 peticiones**, **160 fallos**, p95 **30000 ms**.
- **`13-locust-capacidad-estadisticas.png`** y **`14-locust-capacidad-graficos.png`**: abre `capacity-diagnostic.html`. Diagnóstico de **1 usuario**, spawn rate **1**, **60 segundos más cierre**. Estadísticas finales: **19 peticiones**, **0 fallos**, p95 **2500 ms**. Esta ejecución no acredita capacidad durante una hora.
- **`15-locust-estres-fallos.png`**, opcional: sección de fallos del HTML de estrés, mostrando tipos y ocurrencias. Los estados 0 representan ausencia de respuesta HTTP.

En estadísticas captura las **cuatro operaciones**, peticiones, fallos, RPS y p95; en gráficos incluye **usuarios, latencia y throughput**, con sus ejes temporales. Si no caben en una captura legible, usa una captura de página completa o agrega imágenes complementarias, sin alterar las cifras.

Los parámetros y conclusiones de los pies están en **`detalles.json`**. Ya corresponden a esos HTML. Si necesitas ampliar una explicación, edita ese archivo; regenerar el informe conservará los cambios. Conserva los CSV y el HTML como respaldo.

## Capturas de futuras pruebas formales

Para ejecutar las pruebas completas utiliza los perfiles y comandos de [README.md](../../README.md). Si quieres ver la interfaz, abre `http://127.0.0.1:8089`; si Locust está cerrado:

```powershell
.\.venv\Scripts\python.exe -m locust -f locustfile.py --host http://127.0.0.1:8000 --web-host 127.0.0.1
```

Captura Statistics y Charts al finalizar cada ejecución, antes de iniciar otra. En estrés puedes capturar también Failures. Registra la configuración de arranque, usuarios, spawn rate, duración efectiva y número de filas inicial y final. Una captura adicional de la pantalla de configuración ayuda a verificar esos parámetros.

Guarda las pruebas formales **por separado**, en `reports/capturas/formales/`, con estos nombres:

- `carga-estadisticas.png` y `carga-graficos.png`.
- `estres-estadisticas.png` y `estres-graficos.png`.
- `capacidad-estadisticas.png` y `capacidad-graficos.png`.

Para cada imagen agrega en `detalles.json` una entrada `formal-carga-estadisticas`, `formal-carga-graficos`, etc., con `tipo`, `usuarios`, `spawn_rate`, `duracion`, `dataset`, `host`, `fecha`, `fuente` y `conclusion`. `fuente` debe identificar el HTML/CSV de esa ejecución. Al regenerar, aparecerán en una sección separada. Si faltan parámetros, el pie dirá **pendiente de registrar**.

La carga formal necesita al menos **10 minutos de meseta**; el estrés completo usa **seis etapas de un minuto**; la capacidad necesita **60 minutos o más**, con una concurrencia estable justificada. Todavía no se ha demostrado una concurrencia que cumpla el objetivo de p95 de un segundo en el montaje actual.

## Adjuntar las imágenes

1. Guarda cada PNG real dentro de `reports/capturas/` con el nombre indicado. No edites el informe generado para insertar imágenes manualmente.
2. Verifica que `detalles.json` describa la ejecución de las capturas de Locust.
3. Regenera desde la raíz:

```powershell
.\.venv\Scripts\python.exe scripts\write-report.py
```

4. Abre `reports/INFORME.md` en una vista previa Markdown. Las imágenes existentes aparecerán con sus pies; los archivos ausentes conservarán el aviso **Captura pendiente**, sin enlaces de imagen rotos.

Las capturas y los pies no se sobrescriben al regenerar. Los diagnósticos también se pueden reconstruir desde las evidencias versionadas si ya no existe `reports/generated/`.
