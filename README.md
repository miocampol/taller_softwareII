# Taller de rendimiento con Laravel y Locust

Proyecto personal basado en la API del taller de Ingeniería de Software II. Incluye paginación, pruebas de carga, estrés y capacidad, y un informe de las verificaciones realizadas.

<!-- BEGIN LOCUST REPORT -->

## Informe inicial: pruebas de rendimiento con Locust

Fecha: 9 de octubre de 2026 (America/Bogota). Taller de Ingeniería de Software II.

### Alcance y estado

Se configuró y ejecutó la API, se corrigieron los GET y se implementó Locust. Este informe registra verificaciones y **diagnósticos abreviados**. No equivale a una prueba formal de carga de 10–30 minutos ni a una prueba de capacidad de 60 minutos. Los perfiles completos y sus comandos están en [README.md](#inicio-rapido).

### Entorno y metodología

- Windows, Laragon; PHP 8.5.8, Laravel 9 y MySQL 8.0.30. Python 3.10.6 y Locust 2.46.0 en `.venv`.
- CPU AMD Ryzen 7 4700U: 8 núcleos y 8 procesadores lógicos; RAM física aproximada: 15,36 GiB.
- API y generador comparten el equipo. Servidor PHP integrado, un trabajador; host `http://127.0.0.1:8000`.
- Base exclusiva `locust_lab`: 10.000 filas para la verificación inicial, ampliadas después a 1.500.000 sin borrar datos. Los POST agregan tres filas y hacen crecer el dataset durante cada prueba.
- Buffer pool MySQL: 128 MiB. Se ejecutó `ANALYZE TABLE users` tras el sembrado masivo.
- GET paginados: 50 filas, páginas aleatorias de 1 a 10. Filtro por nacimiento anterior a la fecha de corte; índice existente sobre `birth_date`.
- Mezcla aleatoria esperada: 50% listado, 30% correos, 10% filtro de edad y 10% POST. Espera de 1–3 segundos entre tareas. Timeout de 30 segundos.
- `APP_DEBUG=false`, `API_RATE_LIMIT=0`: se desactivó el throttle de 60 peticiones/minuto por IP para evitar que confundiera la medición de capacidad con el límite de acceso.
- Objetivos iniciales elegidos para el laboratorio: p95 <= 1000 ms y fallos <= 1% por operación. No son SLAs suministrados por el docente. Código de salida 1 también indica un objetivo incumplido o cobertura incompleta; no significa necesariamente un error de instalación.

### Cambios y verificación funcional

Los tres GET devuelven `total`, `data` y metadatos de paginación, con `page >= 1`, `per_page` predeterminado 50 y máximo 200. Parámetros inválidos: 422. Página fuera de rango: 200 y arreglo vacío. El filtro de edad se realiza en SQL; excluye a quien cumple exactamente veinte años hoy. Las respuestas ocultan contraseñas y tokens.

Locust comprueba HTTP 200/201, JSON, tamaños de página, orden, filtro de edad y contenido del lote. Los correos usan UUID. Las respuestas 422 se contabilizan como fallos. El sembrado ahora respeta `--count` y `--chunk` y permite agregar lotes sin duplicar correos.

Pruebas automatizadas: **7 pruebas PHP, 62 aserciones**, usando SQLite en memoria; **4 pruebas Python** de contratos. Las dependencias Python pasaron `pip check`.

### Comparación funcional de paginación

Se ejecutaron dos procesos CLI separados sobre las mismas 10.000 filas, reproduciendo la consulta original y la consulta paginada. Incluyen consulta, hidratación y serialización; no son latencias HTTP ni percentiles. La memoria incluye el arranque del framework. Una sola muestra por modo sirve de demostración, no de estimación estadística.

- **all**: 10000 filas; 2195.10 ms; pico 52 MiB; respuesta 2,496,683 bytes.
- **page**: 50 filas; 20.36 ms; pico 18 MiB; respuesta 13,476 bytes.

La paginación reduce las filas cargadas y el tamaño de respuesta. El conteo exacto del total sigue recorriendo un índice: `EXPLAIN` mostró `users_birth_date_index` para `COUNT(*)`. Su coste permanece con el dataset masivo.

#### Comparación HTTP aislada para las capturas

Se verificaron dos servidores contra `locust_lab_comparison`, con 10000 filas. El antes usa el commit `afbb181` y el después usa el controlador paginado. La base masiva conserva su configuración. Las peticiones se ejecutaron secuencialmente; son muestras individuales, sin percentiles ni garantía estadística.

- Antes: HTTP 200, 10000 filas, 2866683 bytes y 2531.51 ms.
- Después: HTTP 200, 5 filas, 3077 bytes y 128.25 ms.
- La segunda página devolvió IDs 6 a 10, diferentes de la primera página.

[Comprobación HTTP y huellas de los controladores](reports/evidence/comparison-http.json). Las capturas 01–03 deben hacerse sobre esos servidores y ese dataset.

### Evidencia visual de las peticiones

Capturas reales tomadas en Postman. Los tiempos y tamaños visibles son muestras individuales; pueden diferir de las mediciones CLI y HTTP anteriores. Los indicadores rojos de Test Results en las respuestas paginadas no acreditan pruebas aprobadas: debe revisarse el script de Postman, pues la respuesta ya es un objeto y no el arreglo de la versión anterior.

#### Figura 1. Antes de paginar

![Antes de paginar](reports/image.png)

*GET /api/users en el puerto 8001. La versión original devuelve un arreglo completo. La captura muestra HTTP 200, 2,13 s y 2,73 MB; la base de comparación contiene 10000 filas.*

#### Figura 2. Después de paginar: primera página

![Después de paginar: primera página](reports/image-1.png)

*Respuesta paginada con current_page=1 y data. La captura muestra HTTP 200, 127 ms y 3,22 KB. Corresponde a la primera página de la misma base de comparación.*

#### Figura 3. Segunda página

![Segunda página](reports/image-2.png)

*GET /api/users?page=2&per_page=5 en el puerto 8002. La respuesta muestra current_page=2 y comienza en el ID 6; HTTP 200, 84 ms y 3,32 KB.*

#### Figura 4. Consulta de correos

![Consulta de correos](reports/image-3.png)

*GET /api/users/emails?page=1&per_page=5 en el puerto 8000. Los cinco registros contienen únicamente id y email; HTTP 200, 1,54 s y 2,22 KB.*

#### Figura 5. Filtro de edad

![Filtro de edad](reports/image-5.png)

*GET /api/users/over-twenty?page=1&per_page=5 en el puerto 8000. La respuesta muestra usuarios con birth_date anteriores al corte de veinte años. La captura registra HTTP 200, 573 ms y 3,29 KB.*

### Ejecuciones observadas

#### Verificación inicial

10.000 filas; 5 usuarios, spawn rate 1; 30 segundos.

Total: **69 peticiones**, **0 fallos** (0.00%); **2.35 RPS**, p95 agregado **200 ms**.

- `GET /api/users`: 39 peticiones, 0 fallos; p50 51 ms, p95 120 ms, p99 120 ms; 1.33 RPS.
- `POST /api/users/bulk`: 4 peticiones, 0 fallos; p50 220 ms, p95 250 ms, p99 250 ms; 0.14 RPS.
- `GET /api/users/emails`: 21 peticiones, 0 fallos; p50 41 ms, p95 130 ms, p99 190 ms; 0.72 RPS.
- `GET /api/users/over-twenty`: 5 peticiones, 0 fallos; p50 53 ms, p95 68 ms, p99 68 ms; 0.17 RPS.

Evidencia: [estadísticas finales](reports/evidence/smoke-small_final.json) extraídas del informe HTML y [estadísticas CSV](reports/evidence/smoke-small_stats.csv). El CSV periódico puede omitir la última petición respecto al cierre del HTML; las cifras anteriores corresponden al cierre. Los percentiles son aproximaciones de Locust; pocas muestras, especialmente de POST, limitan su precisión.

#### Verificación con dataset masivo

1.500.000 filas más altas previas; 5 usuarios, spawn rate 1; 30 segundos.

Total: **31 peticiones**, **0 fallos** (0.00%); **0.92 RPS**, p95 agregado **4400 ms**.

- `GET /api/users`: 19 peticiones, 0 fallos; p50 3700 ms, p95 4700 ms, p99 4700 ms; 0.57 RPS.
- `POST /api/users/bulk`: 5 peticiones, 0 fallos; p50 3200 ms, p95 4000 ms, p99 4000 ms; 0.15 RPS.
- `GET /api/users/emails`: 5 peticiones, 0 fallos; p50 3800 ms, p95 4400 ms, p99 4400 ms; 0.15 RPS.
- `GET /api/users/over-twenty`: 2 peticiones, 0 fallos; p50 1200 ms, p95 1200 ms, p99 1200 ms; 0.06 RPS.

Evidencia: [estadísticas finales](reports/evidence/smoke-full_final.json) extraídas del informe HTML y [estadísticas CSV](reports/evidence/smoke-full_stats.csv). El CSV periódico puede omitir la última petición respecto al cierre del HTML; las cifras anteriores corresponden al cierre. Los percentiles son aproximaciones de Locust; pocas muestras, especialmente de POST, limitan su precisión.

#### Diagnóstico de carga

Dataset masivo; 5 usuarios, spawn rate 1; 90 segundos. Duración inferior a la requerida para carga formal.

Total: **72 peticiones**, **0 fallos** (0.00%); **0.76 RPS**, p95 agregado **6700 ms**.

- `GET /api/users`: 38 peticiones, 0 fallos; p50 4400 ms, p95 6700 ms, p99 7400 ms; 0.40 RPS.
- `POST /api/users/bulk`: 9 peticiones, 0 fallos; p50 3800 ms, p95 5300 ms, p99 5300 ms; 0.10 RPS.
- `GET /api/users/emails`: 18 peticiones, 0 fallos; p50 4700 ms, p95 7100 ms, p99 7100 ms; 0.19 RPS.
- `GET /api/users/over-twenty`: 7 peticiones, 0 fallos; p50 4300 ms, p95 6000 ms, p99 6000 ms; 0.07 RPS.

Evidencia: [estadísticas finales](reports/evidence/load-diagnostic_final.json) extraídas del informe HTML y [estadísticas CSV](reports/evidence/load-diagnostic_stats.csv). El CSV periódico puede omitir la última petición respecto al cierre del HTML; las cifras anteriores corresponden al cierre. Los percentiles son aproximaciones de Locust; pocas muestras, especialmente de POST, limitan su precisión.

#### Diagnóstico de estrés

Dataset masivo; etapas de 5/10/20/40/80/160 usuarios, spawn rates 5/5/10/10/20/40. 10 segundos por etapa (`LOCUST_STAGE_SECONDS=10`); rampa abreviada, no seis minutos.

Total: **201 peticiones**, **160 fallos** (79.60%); **2.27 RPS**, p95 agregado **30000 ms**.

- `GET /api/users`: 94 peticiones, 75 fallos; p50 30000 ms, p95 30000 ms, p99 30000 ms; 1.06 RPS.
- `POST /api/users/bulk`: 28 peticiones, 23 fallos; p50 30000 ms, p95 30000 ms, p99 30000 ms; 0.32 RPS.
- `GET /api/users/emails`: 60 peticiones, 44 fallos; p50 30000 ms, p95 30000 ms, p99 30000 ms; 0.68 RPS.
- `GET /api/users/over-twenty`: 19 peticiones, 18 fallos; p50 30000 ms, p95 30000 ms, p99 30000 ms; 0.21 RPS.

Máximo observado en el historial: 160 usuarios.
- Primer p95 registrado superior a un segundo: segundo 3, 5 usuarios, 0.00 RPS de completaciones (incluyen fallos), p95 1600 ms.
- Primer intervalo con fallos registrados: segundo 57, 160 usuarios, 0.60 RPS de completaciones (incluyen fallos), p95 30000 ms.

Evidencia: [estadísticas finales](reports/evidence/stress-diagnostic_final.json) extraídas del informe HTML y [estadísticas CSV](reports/evidence/stress-diagnostic_stats.csv). El CSV periódico puede omitir la última petición respecto al cierre del HTML; las cifras anteriores corresponden al cierre. Los percentiles son aproximaciones de Locust; pocas muestras, especialmente de POST, limitan su precisión.

#### Diagnóstico sostenido

Dataset masivo; 1 usuario, spawn rate 1; 60 segundos. Comprueba el perfil de capacidad, pero no demuestra resistencia durante una hora.

Total: **19 peticiones**, **0 fallos** (0.00%); **0.32 RPS**, p95 agregado **2500 ms**.

- `GET /api/users`: 12 peticiones, 0 fallos; p50 1500 ms, p95 2500 ms, p99 2500 ms; 0.20 RPS.
- `POST /api/users/bulk`: 2 peticiones, 0 fallos; p50 310 ms, p95 310 ms, p99 310 ms; 0.03 RPS.
- `GET /api/users/emails`: 3 peticiones, 0 fallos; p50 1500 ms, p95 1500 ms, p99 1500 ms; 0.05 RPS.
- `GET /api/users/over-twenty`: 2 peticiones, 0 fallos; p50 490 ms, p95 490 ms, p99 490 ms; 0.03 RPS.

Evidencia: [estadísticas finales](reports/evidence/capacity-diagnostic_final.json) extraídas del informe HTML y [estadísticas CSV](reports/evidence/capacity-diagnostic_stats.csv). El CSV periódico puede omitir la última petición respecto al cierre del HTML; las cifras anteriores corresponden al cierre. Los percentiles son aproximaciones de Locust; pocas muestras, especialmente de POST, limitan su precisión.

### Recursos observados

Muestreo de un segundo durante los diagnósticos. CPU 100% equivale a un núcleo lógico; RSS es memoria residente. Las medias incluyen intervalos de espera entre pruebas y no son promedios por escenario.

- `php.exe` (PID 13876): CPU media 2.67%, máxima 26.10%; RSS mínima/máxima 48.36/48.42 MiB.
- `mysqld.exe` (PID 5096): CPU media 117.49%, máxima 247.60%; RSS mínima/máxima 511.71/514.50 MiB.
- `mysqld.exe` (PID 7904): CPU media 0.00%, máxima 0.00%; RSS mínima/máxima 26.39/26.39 MiB.
- `php.exe` (PID 9600): CPU media 3.91%, máxima 32.80%; RSS mínima/máxima 49.93/50.04 MiB.

[Muestras de recursos](reports/evidence/resources.csv) y [muestras posteriores](reports/evidence/resources-after-stress.csv). El servidor PHP se reinició tras estrés para vaciar la cola.

### Evidencia visual del cliente de Locust

Capturas de Statistics tomadas desde http://127.0.0.1:8089 contra la API principal. El estado visible es **RUNNING**: las cifras corresponden al instante de captura, no al cierre de la ejecución. No se registraron el spawn rate ni la duración de estas ejecuciones. No sustituyen los diagnósticos anteriores ni acreditan pruebas prolongadas.

#### Prueba con 5 usuarios

84 peticiones, 0 fallos (0%), p95 agregado 6200 ms, mediana 4000 ms y RPS actual 0,8. Se ejecutaron los cuatro endpoints.

![Statistics con 5 usuarios](reports/image-6.png)

*5 usuarios activos; host http://127.0.0.1:8000; estadísticas acumuladas al instante de captura. Spawn rate y duración no registrados.*

#### Prueba con 50 usuarios

47 peticiones, 5 fallos (10,64%; la cabecera redondea a 11%), p95 agregado 30000 ms, mediana 15000 ms y RPS actual 0,8. Se ejecutaron los cuatro endpoints. Aumentan los fallos y la latencia sin una mejora observable del throughput en estas capturas.

![Statistics con 50 usuarios](reports/image-7.png)

*50 usuarios activos; host http://127.0.0.1:8000; estadísticas acumuladas al instante de captura. Spawn rate y duración no registrados.*

**Prueba con 1000 usuarios:** fue planteada, pero no hay una captura disponible que permita documentar su resultado. Tampoco se adjuntaron gráficos de las pruebas con 5 y 50 usuarios.

### Interpretación y pendientes para la entrega formal

- Con pocas filas se verificó el funcionamiento de los cuatro endpoints. Con el dataset masivo ya se incumplió el objetivo de latencia con cinco usuarios, aun sin errores HTTP. Por tanto no se ha demostrado un máximo estable que cumpla el SLA de un segundo.
- El conteo exacto y la cola del servidor de un trabajador explican posibles cuellos de botella. Esta atribución es una interpretación del código, el plan SQL y el montaje; no una prueba causal que separe cada coste.
- En estrés debe relacionarse el historial temporal con la concurrencia y los timeouts. La rampa abreviada y el timeout de 30 segundos pueden desplazar la observación del fallo a una etapa posterior: no atribuir el primer timeout automáticamente a ese número de usuarios.
- Los fallos de estrés registrados como estado 0 representan ausencia de respuesta HTTP. Las duraciones cercanas a 30 segundos son compatibles con el timeout del cliente. El CSV original conserva esa clasificación y no permite separar todas las causas de transporte.
- Ejecutar el perfil de carga durante al menos diez minutos y el estrés de seis etapas de un minuto. Repetir en un servidor con múltiples trabajadores si se busca estimar capacidad de despliegue.
- Elegir la concurrencia de capacidad usando el máximo estable demostrado y ejecutar al menos 60 minutos. Comparar latencias, errores, RPS y memoria a lo largo del tiempo. Un minuto no permite concluir ausencia de fugas de memoria ni resistencia prolongada.
- Registrar el número de filas inicial y final en cada ejecución, porque los POST aumentan el dataset. Conservar exportaciones HTML/CSV y muestras de recursos por escenario.
- Si se optimiza después el conteo o se cambia a paginación por cursor, documentar la modificación del contrato y volver a medir. No ocultar el problema aumentando el SLA sin justificar el cambio.

### Reproducción y referencias

Los comandos, duraciones completas y pasos de navegador están en [README.md](#inicio-rapido). Los contratos están en [README-API-LOCUST.md](README-API-LOCUST.md). La comparación CLI se reproduce con `php scripts/benchmark-pagination.php all` y `page` sobre una base pequeña separada; el modo `all` se niega a ejecutar sobre más de 11.000 filas.

Material del taller: [PDF](locust_test.pdf). Referencias de implementación: [Locust](https://docs.locust.io/en/stable/writing-a-locustfile.html), [paginación Laravel 9](https://laravel.com/docs/9.x/pagination).

El trabajo y sus evidencias se publican únicamente en el fork personal. No se abre una solicitud de cambios al repositorio original.

<!-- END LOCUST REPORT -->

<a id="inicio-rapido"></a>

## Inicio rápido en Windows / Laragon

Ejecuta los comandos desde la raíz de este repositorio. Usa **PHP 8.2 o superior** para el `composer.lock` actual, Python 3.10 o superior, Composer y MySQL 8. La instalación verificada usa PHP 8.5.8, Python 3.10.6 y MySQL 8.0.30.

1. Inicia MySQL en Laragon y crea una base vacía llamada `locust_lab`.
2. Instala las dependencias:

```powershell
composer install
Copy-Item .env.example .env   # Solo si todavía no existe .env
php artisan key:generate
```

3. Configura `.env`: `DB_CONNECTION=mysql`, `DB_HOST=127.0.0.1`, `DB_PORT=3306`, `DB_DATABASE=locust_lab`, `DB_USERNAME=root` y tu contraseña local. Para Locust en este laboratorio usa `APP_DEBUG=false` y `API_RATE_LIMIT=0`. Sin esta última opción, Laravel conserva el límite predeterminado de 60 peticiones por minuto por IP.
4. Crea las tablas y los datos:

```powershell
php artisan migrate
# Para empezar, puedes poner MASS_USER_SEED_COUNT=10000 en .env.
php artisan db:seed
```

`MASS_USER_SEED_COUNT=1500000` corresponde al dataset del taller. Cada ejecución del seed **agrega** esa cantidad, no la fija como total. No vuelvas a sembrar si ya tienes los datos necesarios. `migrate:fresh --seed` elimina todas las tablas: no es necesario para iniciar este proyecto.

5. Inicia la API en una terminal:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-api.ps1
```

Abre <http://127.0.0.1:8000/api/users?page=1&per_page=50>. También puedes usar `php artisan serve --host=127.0.0.1 --port=8000`; el script incluido ejecuta el servidor de desarrollo desde `public/` y evita avisos de dependencias antiguas en PHP 8.5. No ejecutes ambos servidores sobre el mismo puerto.

## Locust en el navegador

En otra terminal, desde la misma raíz:

```powershell
python -m venv .venv                       # Solo la primera vez
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m locust -f locustfile.py --host http://127.0.0.1:8000 --web-host 127.0.0.1
```

Abre **<http://127.0.0.1:8089>**. Para comenzar, ingresa **5 usuarios**, **spawn rate 1**, host `http://127.0.0.1:8000` y duración `30s`, y pulsa **Start**. Los nombres exactos de los campos pueden variar según la interfaz. Revisa las pestañas de estadísticas, gráficos y fallos; deben aparecer las cuatro operaciones. Detén la prueba con **Stop** y descarga los datos CSV o el informe HTML desde la sección de descargas. `Ctrl+C` termina el proceso de Locust.

El host no lleva `/api`: las tareas ya incluyen ese prefijo. El archivo se llama `locustfile.py`; no lo renombres a `locust.py`, porque ocultaría el paquete instalado.

Los GET usan páginas aleatorias entre 1 y 10 y 50 filas por página. Puedes cambiarlo con `--page-count 100 --per-page 100`. La mezcla esperada es 50% listado, 30% correos, 10% mayores de veinte y 10% creación en lote; al ser aleatoria, las proporciones observadas varían. Cada POST crea tres filas y deja crecer la base.

## Escenarios y reportes automáticos

Crea la carpeta de resultados:

```powershell
New-Item -ItemType Directory -Force reports\generated
```

Ejecuta un escenario a la vez. Para verlos en el navegador, omite `--headless` y conserva `--web-host 127.0.0.1`; abre el puerto 8089 y pulsa Start. Cierra primero cualquier otra instancia de Locust que use ese puerto.

```powershell
# Verificación rápida: 5 usuarios, 1 usuario/s, 30 segundos
.\.venv\Scripts\python.exe -m locust --config loadtests\smoke.conf --headless --html reports\generated\smoke.html --csv reports\generated\smoke --csv-full-history

# Carga: 20 usuarios, 2 usuarios/s, 10 minutos de meseta + 10 segundos de arranque
.\.venv\Scripts\python.exe -m locust --config loadtests\load.conf --headless --html reports\generated\load.html --csv reports\generated\load --csv-full-history

# Estrés: 5, 10, 20, 40, 80 y 160 usuarios; un minuto por etapa
.\.venv\Scripts\python.exe -m locust --config loadtests\stress.conf --headless --html reports\generated\stress.html --csv reports\generated\stress --csv-full-history

# Capacidad: ajustar -u al máximo estable observado, por debajo del quiebre
# Ejemplo conservador: 5 usuarios, 1 usuario/s, 60 minutos + arranque
.\.venv\Scripts\python.exe -m locust --config loadtests\capacity.conf -u 5 -r 1 -t 3605s --headless --html reports\generated\capacity.html --csv reports\generated\capacity --csv-full-history
```

El perfil de capacidad usa 10 usuarios por defecto; **no representa un máximo estable ya demostrado**. Ajusta ese valor después de revisar estrés. La rampa de estrés manda sobre `-u` y `-r`. `LOCUST_STAGE_SECONDS` permite acortar cada etapa para verificar la configuración, pero un resultado abreviado debe identificarse como diagnóstico, no como prueba formal.

Se considera fallo un estado HTTP incorrecto, JSON inválido, paginación inconsistente, datos sensibles o un lote distinto al enviado. Los correos llevan UUID para evitar duplicados. El objetivo inicial, elegido para el laboratorio, es **p95 <= 1000 ms y fallos <= 1% por operación**. Locust termina con código 1 si incumple esos umbrales o no registra peticiones; en estrés esto puede ser el resultado esperado. Cambia los objetivos con `--sla-p95-ms` y `--sla-error-ratio`, y documenta la decisión.

Los resultados de `reports/generated/` se excluyen de Git. El informe y las evidencias seleccionadas están en `reports/`. Los cambios se publican únicamente en el fork personal; no se abre una PR al repositorio original.

## Verificación del código y recursos

```powershell
php -d error_reporting=8191 vendor\phpunit\phpunit\phpunit --testdox
.\.venv\Scripts\python.exe -m unittest loadtests.test_contracts
```

PHPUnit usa SQLite en memoria y no borra `locust_lab`. Para medir CPU y memoria, busca los PID de PHP y MySQL con `Get-Process php,mysqld` y ejecuta en una tercera terminal:

```powershell
.\.venv\Scripts\python.exe scripts\monitor_resources.py --pid 1234 5678 --seconds 700 --output reports\generated\resources.csv
```

Sustituye los PID por los reales. CPU 100% equivale a un núcleo lógico; RSS es memoria residente del proceso. Usa este monitor durante cada escenario y relaciona sus tiempos con el historial de Locust.

El servidor PHP integrado en Windows atiende las peticiones secuencialmente. Las mediciones describen este montaje de desarrollo y su cola de solicitudes. Para evaluar un despliegue real, repite los escenarios en un servidor con múltiples trabajadores y documenta el entorno.

Más detalles del contrato en [README-API-LOCUST.md](README-API-LOCUST.md). El informe está integrado en este README y también disponible en [reports/INFORME.md](reports/INFORME.md).

Las capturas de Postman y Locust están integradas en el informe de este README. Para agregar las del cliente de Locust, guarda Statistics como `reports/locust-estadisticas.png` y Charts como `reports/locust-graficos.png`; si hay errores, guarda Failures como `reports/locust-fallos.png`. Ejecuta `.\.venv\Scripts\python.exe scripts\write-report.py` para incorporarlas. Los resultados tomados desde la interfaz pertenecen a una ejecución adicional y deben conservar sus propios parámetros.
