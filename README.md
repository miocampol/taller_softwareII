# Taller de rendimiento con Laravel y Locust

Proyecto personal basado en la API del taller de Ingeniería de Software II. Incluye paginación, pruebas de carga, estrés y capacidad, y un informe de las verificaciones realizadas.

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

Los resultados de `reports/generated/` se excluyen de Git. El informe y las evidencias seleccionadas están en `reports/`. No se ha realizado push ni se ha abierto una PR al repositorio de origen.

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

Más detalles del contrato en [README-API-LOCUST.md](README-API-LOCUST.md). El informe está en [reports/INFORME.md](reports/INFORME.md).

Para adjuntar capturas, sigue [reports/capturas/GUIA.md](reports/capturas/GUIA.md). Incluye una colección importable de Postman, los nombres de las 14 capturas recomendadas y servidores aislados para comparar antes/después con 10000 filas. Las capturas reales aparecen automáticamente al regenerar el informe.
