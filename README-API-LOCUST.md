# API Laravel: contrato y preparación del laboratorio

La API está en la raíz de este repositorio. Consulta [README.md](README.md) para instalarla en Laragon y abrir Locust en el navegador.

## Base de datos

- MySQL: base `locust_lab`, configurada en `.env`.
- `php artisan migrate` crea las tablas sin eliminarlas.
- `php artisan db:seed` agrega `MASS_USER_SEED_COUNT` filas (referencia: 1.500.000) en lotes de `MASS_USER_CHUNK_SIZE` (2000).
- Para agregar una cantidad concreta sin borrar datos: `php artisan users:seed-mass --count=10000 --chunk=2000`.
- Los lotes de seed usan correos con UUID; las ejecuciones sucesivas no duplican los correos de lotes anteriores. El comando agrega filas; no ajusta la tabla a un total absoluto.
- `php artisan migrate:fresh --seed` borra las tablas. Resérvalo para una base de laboratorio que puedas descartar.

## GET paginados

Host: `http://127.0.0.1:8000`. Rutas:

- `GET /api/users`: campos públicos de los usuarios.
- `GET /api/users/emails`: únicamente `id` y `email`.
- `GET /api/users/over-twenty`: usuarios nacidos antes de la fecha de corte de veinte años atrás. La persona que cumple exactamente veinte años hoy queda excluida.

Los tres endpoints aceptan `page` (entero >= 1, por defecto 1) y `per_page` (entero entre 1 y 200, por defecto 50). Parámetros inválidos reciben **422** cuando el cliente solicita JSON. Una página fuera del rango recibe **200** con `data: []`.

```http
GET /api/users?page=2&per_page=50
Accept: application/json
```

Las respuestas son objetos de paginación Laravel, con `total`, `data`, `current_page`, `per_page`, `last_page` y enlaces. Los enlaces conservan los parámetros de consulta. `over-twenty` añade `cutoff_date` en formato `YYYY-MM-DD`. Las fechas de nacimiento de los usuarios se serializan como fechas ISO según el modelo Laravel. Ninguna operación expone contraseñas ni tokens de recuerdo.

La consulta está ordenada por `id` para estabilizar las páginas. El filtro de edad se ejecuta en SQL; usa el índice `users_birth_date_index` que ya existía en la migración original. Los listados y sus conteos son consultas separadas: una escritura concurrente puede cambiar el total. La prueba no supone que el total permanezca fijo entre peticiones.

**Cambio respecto a la API inicial:** los GET devolvían arreglos completos mediante `User::all()`. Ahora devuelven un objeto paginado. Los clientes que consumían el arreglo deben leer `data`. Con el dataset masivo, la paginación limita las filas cargadas en PHP, pero el conteo `total` todavía tiene un coste que debe medirse.

## Creación en lote

```http
POST /api/users/bulk
Accept: application/json
Content-Type: application/json
```

```json
{
  "users": [
    {"name": "Ana", "email": "ana.unique@example.com", "birth_date": "1998-05-12"},
    {"name": "Bruno", "email": "bruno.unique@example.com", "birth_date": "2000-11-03", "password": "secreto123"},
    {"name": "Carla", "email": "carla.unique@example.com", "birth_date": "1995-01-20"}
  ]
}
```

Se requieren exactamente tres usuarios, nombres válidos, fechas no futuras y correos únicos tanto dentro del lote como en la base. La contraseña es opcional; si se incluye debe tener al menos seis caracteres. Éxito: **201**, `message` y `users` con los tres registros creados. Una validación rechazada responde **422**, que Locust registra como fallo.

Cada petición de prueba genera correos distintos. No vuelvas a enviar el ejemplo sin cambiarlos, porque los correos quedarían duplicados.

## Configuración para medir

`API_RATE_LIMIT=0` desactiva el throttle solo para el entorno académico controlado. Al omitir la variable se conserva el límite de 60 peticiones/minuto por IP; un valor positivo fija otro límite. Documenta su estado en el informe. Usa `php artisan config:clear` si cambias `.env` después de haber cacheado la configuración.

El servidor integrado de PHP se usa para verificar el ejercicio local. En Windows atiende secuencialmente; una cola creciente puede dominar la latencia. Un despliegue con múltiples trabajadores requiere repetir las mediciones. Los tiempos de espera, el hashing de las tres contraseñas del POST y los conteos SQL también afectan los resultados.

## Archivos de la entrega

- `locustfile.py`: mezcla HTTP, tiempos de espera y validaciones.
- `stress_locustfile.py`: rampa de estrés.
- `loadtests/*.conf`: parámetros de los escenarios.
- `requirements.txt`: versión de Locust.
- `scripts/`: servidor local, monitor de recursos y comparación CLI de paginación.
- `reports/INFORME.md`: informe de implementación y mediciones realizadas.

Referencias: [Locust](https://docs.locust.io/en/stable/writing-a-locustfile.html), [paginación Laravel 9](https://laravel.com/docs/9.x/pagination).
