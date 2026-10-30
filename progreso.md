# Progreso — Football Analytics

## Estado actual
- Fase: 1 — datos reales de Liga MX cargados
- Última actualización: 2026-10-30
- Objetivo activo: análisis de rendimiento de equipos (local/visitante, tendencia por jornada)

## Completado
- [x] Repositorio Git inicializado (sin commits todavía)
- [x] Estructura de carpetas, `.gitignore`, `.env.example`, `requirements.txt`, `README.md`, `data/README.md`
- [x] `calcular_tabla_posiciones` en `src/football_analytics/metrics.py` — implementado y probado
- [x] Commit inicial `cbd7a4c`
- [x] Investigación de fuentes de Liga MX (ver Fuentes de datos)
- [x] `MEX.csv` descargado a `data/raw/` y documentado en `data/README.md`
- [x] `ingest.py` (carga + validación de resultado) y `cleaning.py` (torneo y fase) — implementado y probado
- [x] `data/processed/liga_mx_partidos.csv` generado (4,780 partidos)
- [x] Tabla de fase regular Apertura 2025 verificada contra Wikipedia: coincide en los 18 equipos
- [x] `calcular_rendimiento_local_visitante` en `metrics.py` (PPP local/visitante y `dif_PPP`) — implementado y probado; en Apertura 2025 los puntos local+visitante cuadran con la tabla verificada
- [x] `tests/test_metrics.py`: victoria, empate, derrota, equipo sin partidos, orden, coherencia, reglamento configurable, tabla vacía y validaciones

## En curso
- Tarea: ninguna
- Bloqueos: ninguno

## Decisiones técnicas
- Decisión: puntos por victoria/empate como parámetros (3-1 por defecto).
- Motivo: CLAUDE.md pide no asumir 3-1-0 sin verificar el reglamento.
- Decisión: desempate provisional por Pts, DG, GF y nombre.
- Motivo: falta verificar los criterios oficiales de desempate de Liga MX por temporada.
- Decisión: torneo por mes (jul-dic Apertura, ene-jun Clausura) y fase regular = primeros n·(n−1)/2 partidos por fecha.
- Motivo: la fuente no trae esas columnas; la regla se verificó en los 29 torneos (enfrentamientos únicos y pausa de 3-13 días antes de la liguilla).
- Decisión: comparar local/visitante con puntos por partido (PPP), no con puntos totales.
- Motivo: en 17 jornadas un equipo juega 9 partidos en casa y 8 fuera (o al revés).
- Decisión: dependencias mínimas (pandas, pytest); Streamlit/Plotly se agregan cuando se usen.
- Motivo: evitar dependencias sin uso.

## Fuentes de datos
- Fuente adoptada: football-data.co.uk `new/MEX.csv` — https://www.football-data.co.uk/mexico.php
- Competición/temporada: Liga MX 2012/2013 a 2026/2027 (en curso), 4,780 partidos (revisado 2026-10-30)
- Columnas: Country, League, Season, Date, Time, Home, Away, HG, AG, Res + cuotas de apuestas
- Limitaciones: sin columna Apertura/Clausura ni fase (temporada regular vs. liguilla mezcladas); hora probablemente del Reino Unido; sin licencia explícita ("My data is free"); solo resultados, sin jugadores ni eventos
- Descartadas por ahora: StatsBomb Open Data (no incluye Liga MX); openfootball/mexico (el repo da 404); FBref (requiere scraping, condiciones restrictivas)

## Pruebas
- Comando: `.venv\Scripts\python -m pytest -q` (Python 3.12.3, pandas 3.1.0, pytest 9.2.0)
- Resultado: 17 passed (2026-10-30)
- Pendientes: verificar cómo registra la fuente partidos de liguilla con tiempo extra/penales

## Próximo paso
- Crear `charts.py` con un gráfico de PPP local vs. visitante por equipo (Plotly) como primer bloque del dashboard.
