"""Rebuild the initial Markdown report from selected local diagnostic evidence."""

import csv
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "reports" / "generated"
EVIDENCE = ROOT / "reports" / "evidence"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def final_stats(prefix):
    html = (GENERATED / f'{prefix}.html').read_text(encoding='utf-8')
    payload = json.JSONDecoder().raw_decode(html.split('window.templateArgs = ', 1)[1].lstrip())[0]
    selected = {key: payload[key] for key in ['start_time', 'end_time', 'duration',
                'requests_statistics', 'response_time_statistics', 'failures_statistics']}
    (EVIDENCE / f'{prefix}_final.json').write_text(json.dumps(selected, indent=2), encoding='utf-8')
    percentiles = {(row['method'], row['name']): row for row in payload['response_time_statistics']}
    result = []
    for row in payload['requests_statistics']:
        percent = percentiles[(row['method'], row['name'])]
        result.append({'Type': row['method'], 'Name': row['name'],
                       'Request Count': row['num_requests'], 'Failure Count': row['num_failures'],
                       'Requests/s': row['total_rps'], '50%': percent['0.5'],
                       '95%': percent['0.95'], '99%': percent['0.99']})
    return result


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Informe inicial: pruebas de rendimiento con Locust",
        "",
        "Fecha: 9 de octubre de 2026 (America/Bogota). Taller de Ingeniería de Software II.",
        "",
        "## Alcance y estado",
        "",
        "Se configuró y ejecutó la API, se corrigieron los GET y se implementó Locust. "
        "Este informe registra verificaciones y **diagnósticos abreviados**. "
        "No equivale a una prueba formal de carga de 10–30 minutos ni a una prueba de capacidad de 60 minutos. "
        "Los perfiles completos y sus comandos están en [README.md](../README.md).",
        "",
        "## Entorno y metodología",
        "",
        "- Windows, Laragon; PHP 8.5.8, Laravel 9 y MySQL 8.0.30. "
        "Python 3.10.6 y Locust 2.46.0 en `.venv`.",
        "- CPU AMD Ryzen 7 4700U: 8 núcleos y 8 procesadores lógicos; RAM física aproximada: 15,36 GiB.",
        "- API y generador comparten el equipo. Servidor PHP integrado, un trabajador; host `http://127.0.0.1:8000`.",
        "- Base exclusiva `locust_lab`: 10.000 filas para la verificación inicial, ampliadas después a "
        "1.500.000 sin borrar datos. Los POST agregan tres filas y hacen crecer el dataset durante cada prueba.",
        "- Buffer pool MySQL: 128 MiB. Se ejecutó `ANALYZE TABLE users` tras el sembrado masivo.",
        "- GET paginados: 50 filas, páginas aleatorias de 1 a 10. "
        "Filtro por nacimiento anterior a la fecha de corte; índice existente sobre `birth_date`.",
        "- Mezcla aleatoria esperada: 50% listado, 30% correos, 10% filtro de edad y 10% POST. "
        "Espera de 1–3 segundos entre tareas. Timeout de 30 segundos.",
        "- `APP_DEBUG=false`, `API_RATE_LIMIT=0`: se desactivó el throttle de 60 peticiones/minuto "
        "por IP para evitar que confundiera la medición de capacidad con el límite de acceso.",
        "- Objetivos iniciales elegidos para el laboratorio: p95 <= 1000 ms y fallos <= 1% por operación. "
        "No son SLAs suministrados por el docente. Código de salida 1 también indica un objetivo incumplido "
        "o cobertura incompleta; no significa necesariamente un error de instalación.",
        "",
        "## Cambios y verificación funcional",
        "",
        "Los tres GET devuelven `total`, `data` y metadatos de paginación, con `page >= 1`, "
        "`per_page` predeterminado 50 y máximo 200. Parámetros inválidos: 422. Página fuera de rango: "
        "200 y arreglo vacío. El filtro de edad se realiza en SQL; excluye a quien cumple exactamente "
        "veinte años hoy. Las respuestas ocultan contraseñas y tokens.",
        "",
        "Locust comprueba HTTP 200/201, JSON, tamaños de página, orden, filtro de edad y contenido del lote. "
        "Los correos usan UUID. Las respuestas 422 se contabilizan como fallos. "
        "El sembrado ahora respeta `--count` y `--chunk` y permite agregar lotes sin duplicar correos.",
        "",
        "Pruebas automatizadas: **7 pruebas PHP, 62 aserciones**, usando SQLite en memoria; "
        "**4 pruebas Python** de contratos. Las dependencias Python pasaron `pip check`.",
        "",
        "## Comparación funcional de paginación",
        "",
        "Se ejecutaron dos procesos CLI separados sobre las mismas 10.000 filas, reproduciendo "
        "la consulta original y la consulta paginada. Incluyen consulta, hidratación y serialización; "
        "no son latencias HTTP ni percentiles. La memoria incluye el arranque del framework. "
        "Una sola muestra por modo sirve de demostración, no de estimación estadística.",
        "",
    ]
    for name in ["baseline-all", "baseline-page"]:
        path = GENERATED / f"{name}.json"
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        shutil.copy2(path, EVIDENCE / path.name)
        lines.append(f"- **{data['mode']}**: {data['returned_rows']} filas; {data['elapsed_ms']:.2f} ms; "
                     f"pico {data['peak_memory_mb']} MiB; respuesta {data['response_bytes']:,} bytes.")
    lines += ["", "La paginación reduce las filas cargadas y el tamaño de respuesta. "
              "El conteo exacto del total sigue recorriendo un índice: `EXPLAIN` mostró "
              "`users_birth_date_index` para `COUNT(*)`. Su coste permanece con el dataset masivo.",
              "", "## Ejecuciones observadas", ""]
    scenarios = [
        ("smoke-small", "Verificación inicial", "10.000 filas; 5 usuarios, spawn rate 1; 30 segundos."),
        ("smoke-full", "Verificación con dataset masivo", "1.500.000 filas más altas previas; 5 usuarios, spawn rate 1; 30 segundos."),
        ("load-diagnostic", "Diagnóstico de carga", "Dataset masivo; 5 usuarios, spawn rate 1; 90 segundos. Duración inferior a la requerida para carga formal."),
        ("stress-diagnostic", "Diagnóstico de estrés", "Dataset masivo; etapas de 5/10/20/40/80/160 usuarios, spawn rates 5/5/10/10/20/40. "
         "10 segundos por etapa (`LOCUST_STAGE_SECONDS=10`); rampa abreviada, no seis minutos."),
        ("capacity-diagnostic", "Diagnóstico sostenido", "Dataset masivo; 1 usuario, spawn rate 1; 60 segundos. "
         "Comprueba el perfil de capacidad, pero no demuestra resistencia durante una hora."),
    ]
    for prefix, title, detail in scenarios:
        path = GENERATED / f"{prefix}_stats.csv"
        if not path.exists():
            continue
        stats = final_stats(prefix)
        aggregate = next(row for row in stats if row["Name"] == "Aggregated")
        count, failed = int(aggregate["Request Count"]), int(aggregate["Failure Count"])
        lines += [f"### {title}", "", detail, "",
                  f"Total: **{count} peticiones**, **{failed} fallos** "
                  f"({100 * failed / max(1, count):.2f}%); "
                  f"**{float(aggregate['Requests/s']):.2f} RPS**, "
                  f"p95 agregado **{aggregate['95%']} ms**.", ""]
        for row in stats:
            if row["Name"] != "Aggregated":
                lines.append(f"- `{row['Type']} {row['Name']}`: {row['Request Count']} peticiones, "
                             f"{row['Failure Count']} fallos; p50 {row['50%']} ms, p95 {row['95%']} ms, "
                             f"p99 {row['99%']} ms; {float(row['Requests/s']):.2f} RPS.")
        if prefix == 'stress-diagnostic':
            history = [row for row in rows(GENERATED / f'{prefix}_stats_history.csv') if row['Name'] == 'Aggregated']
            origin = int(history[0]['Timestamp'])
            first_latency = next((row for row in history if row['95%'] != 'N/A' and float(row['95%']) > 1000), None)
            first_failure = next((row for row in history if int(row['Total Failure Count']) > 0), None)
            lines += ['', f"Máximo observado en el historial: {max(int(row['User Count']) for row in history)} usuarios."]
            for label, row in [('Primer p95 registrado superior a un segundo', first_latency),
                               ('Primer intervalo con fallos registrados', first_failure)]:
                if row:
                    lines.append(f"- {label}: segundo {int(row['Timestamp']) - origin}, "
                                 f"{row['User Count']} usuarios, {float(row['Requests/s']):.2f} RPS "
                                 f"de completaciones (incluyen fallos), p95 {row['95%']} ms.")
        if len([row for row in stats if row["Name"] != "Aggregated"]) < 4:
            lines += ["", "**Cobertura incompleta:** la mezcla aleatoria no ejecutó las cuatro operaciones "
                      "en este intervalo corto. No se acepta esta ejecución como escenario completo."]
        lines += ["", f"Evidencia: [estadísticas finales](evidence/{prefix}_final.json) "
                  f"extraídas del informe HTML y [estadísticas CSV](evidence/{prefix}_stats.csv). "
                  "El CSV periódico puede omitir la última petición respecto al cierre del HTML; "
                  "las cifras anteriores corresponden al cierre. "
                  "Los percentiles son aproximaciones de Locust; pocas muestras, especialmente de POST, "
                  "limitan su precisión.", ""]
        for suffix in ["stats", "stats_history", "failures", "exceptions"]:
            source = GENERATED / f"{prefix}_{suffix}.csv"
            if source.exists():
                shutil.copy2(source, EVIDENCE / source.name)
    resource_files = [path for path in [GENERATED / 'resources.csv', GENERATED / 'resources-after-stress.csv'] if path.exists()]
    if resource_files:
        samples = [row for path in resource_files for row in rows(path)]
        lines += ["## Recursos observados", "", "Muestreo de un segundo durante los diagnósticos. "
                  "CPU 100% equivale a un núcleo lógico; RSS es memoria residente. "
                  "Las medias incluyen intervalos de espera entre pruebas y no son promedios por escenario.", ""]
        for pid in sorted({row["pid"] for row in samples}):
            group = [row for row in samples if row["pid"] == pid]
            cpu = [float(row["cpu_percent"]) for row in group]
            memory = [float(row["rss_mb"]) for row in group]
            lines.append(f"- `{group[0]['process']}` (PID {pid}): CPU media {sum(cpu)/len(cpu):.2f}%, "
                         f"máxima {max(cpu):.2f}%; RSS mínima/máxima {min(memory):.2f}/{max(memory):.2f} MiB.")
        for path in resource_files:
            shutil.copy2(path, EVIDENCE / path.name)
        lines += ["", "[Muestras de recursos](evidence/resources.csv) y "
                  "[muestras posteriores](evidence/resources-after-stress.csv). "
                  "El servidor PHP se reinició tras estrés para vaciar la cola.", ""]
    lines += [
        "## Interpretación y pendientes para la entrega formal",
        "",
        "- Con pocas filas se verificó el funcionamiento de los cuatro endpoints. Con el dataset masivo "
        "ya se incumplió el objetivo de latencia con cinco usuarios, aun sin errores HTTP. "
        "Por tanto no se ha demostrado un máximo estable que cumpla el SLA de un segundo.",
        "- El conteo exacto y la cola del servidor de un trabajador explican posibles cuellos de botella. "
        "Esta atribución es una interpretación del código, el plan SQL y el montaje; "
        "no una prueba causal que separe cada coste.",
        "- En estrés debe relacionarse el historial temporal con la concurrencia y los timeouts. "
        "La rampa abreviada y el timeout de 30 segundos pueden desplazar la observación del fallo "
        "a una etapa posterior: no atribuir el primer timeout automáticamente a ese número de usuarios.",
        "- Los fallos de estrés registrados como estado 0 representan ausencia de respuesta HTTP. "
        "Las duraciones cercanas a 30 segundos son compatibles con el timeout del cliente. "
        "El CSV original conserva esa clasificación y no permite separar todas las causas de transporte.",
        "- Ejecutar el perfil de carga durante al menos diez minutos y el estrés de seis etapas de un minuto. "
        "Repetir en un servidor con múltiples trabajadores si se busca estimar capacidad de despliegue.",
        "- Elegir la concurrencia de capacidad usando el máximo estable demostrado y ejecutar al menos "
        "60 minutos. Comparar latencias, errores, RPS y memoria a lo largo del tiempo. "
        "Un minuto no permite concluir ausencia de fugas de memoria ni resistencia prolongada.",
        "- Registrar el número de filas inicial y final en cada ejecución, porque los POST aumentan "
        "el dataset. Conservar exportaciones HTML/CSV y muestras de recursos por escenario.",
        "- Si se optimiza después el conteo o se cambia a paginación por cursor, documentar la "
        "modificación del contrato y volver a medir. No ocultar el problema aumentando el SLA "
        "sin justificar el cambio.",
        "",
        "## Reproducción y referencias",
        "",
        "Los comandos, duraciones completas y pasos de navegador están en [README.md](../README.md). "
        "Los contratos están en [README-API-LOCUST.md](../README-API-LOCUST.md). "
        "La comparación CLI se reproduce con `php scripts/benchmark-pagination.php all` y `page` "
        "sobre una base pequeña separada; el modo `all` se niega a ejecutar sobre más de 11.000 filas.",
        "",
        "Material del taller: [PDF](../locust_test.pdf). Referencias de implementación: "
        "[Locust](https://docs.locust.io/en/stable/writing-a-locustfile.html), "
        "[paginación Laravel 9](https://laravel.com/docs/9.x/pagination).",
        "",
        "Los commits son locales al fork. No se realizó push ni se abrió una solicitud al repositorio original.",
    ]
    (ROOT / "reports" / "INFORME.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Written reports/INFORME.md and selected evidence")


if __name__ == "__main__":
    main()
