# Progreso — Football Analytics

## Estado actual
- Fase: 3 — dashboard publicado (MVP)
- Última actualización: 2026-10-30
- Objetivo activo: evolución por equipo (tendencia y rachas)

## Completado
- [x] Repositorio Git inicializado (sin commits todavía)
- [x] Estructura de carpetas, `.gitignore`, `.env.example`, `requirements.txt`, `README.md`, `data/README.md`
- [x] `calcular_tabla_posiciones` en `src/football_analytics/metrics.py` — implementado y probado
- [x] Commits `cbd7a4c` (estructura), `781fe3d` (datos, limpieza, local/visitante) , `b1c5daf` (gráfico) y `f312c3f` (dashboard)
- [x] Investigación de fuentes de Liga MX (ver Fuentes de datos)
- [x] `MEX.csv` descargado a `data/raw/` y documentado en `data/README.md`
- [x] `ingest.py` (carga + validación de resultado) y `cleaning.py` (torneo y fase) — implementado y probado
- [x] `data/processed/liga_mx_partidos.csv` generado (4,780 partidos)
- [x] Tabla de fase regular Apertura 2025 verificada contra Wikipedia: coincide en los 18 equipos
- [x] `calcular_rendimiento_local_visitante` en `metrics.py` (PPP local/visitante y `dif_PPP`) — implementado y probado; en Apertura 2025 los puntos local+visitante cuadran con la tabla verificada
- [x] `charts.py`: `grafico_local_visitante` (gráfico de pesas con Plotly; paleta validada para daltonismo; forma distinta por condición; nota de fuente) — implementado, probado y revisado visualmente con datos del Apertura 2025
- [x] `dashboard/app.py` (Streamlit): selector de torneo, aviso de torneo incompleto, 4 indicadores, tabla de posiciones, gráfico local/visitante, partidos del torneo, fuente y fecha visibles — implementado, probado con AppTest (29 torneos sin errores) y revisado visualmente en escritorio (1280 px) y celular (400 px)
- [x] Repositorio privado publicado en GitHub: https://github.com/orlandomtz77/football-analytics (verificado: visibilidad PRIVATE, 4 commits, sin archivos de datos)
- [x] Descarga automática (`asegurar_datos` en `ingest.py`): si falta el procesado, descarga, valida y procesa una vez; sin archivos a medias si falla — implementado, probado (3 pruebas con descargador falso) y verificado de punta a punta en una copia limpia del repo (descarga real, 29 torneos sin errores)
- [x] Dashboard publicado en Streamlit Community Cloud: https://ligamx-analytics.streamlit.app/ (verificado 2026-10-30: descarga automática OK, 29 torneos, mismos valores que en local; accesible sin iniciar sesión)
- [x] Evolución por equipo: `calcular_evolucion_puntos` y `racha_mas_larga` en `metrics.py`, `grafico_evolucion_puntos` en `charts.py`, sección en el dashboard (selector de equipo, puntos, últimos 5, mejores rachas, gráfico vs. líder) — implementado y probado; puntos finales cuadran con la tabla en los 29 torneos; revisado visualmente (local, aún no desplegado)
- [x] Metadatos de la fuente en `data/processed/liga_mx_partidos.meta.json` (generados por `ingest`)
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
- Decisión: gráfico de pesas (dumbbell) para local vs. visitante; azul = local (círculo), naranja = visitante (rombo).
- Motivo: muestra en una sola vista ambos valores y la brecha; la forma del marcador evita depender solo del color.
- Decisión: `app.py` solo presenta; cálculos en `metrics.py`, carga en `ingest.py`, orden de torneos en `cleaning.py`.
- Motivo: poder probar la lógica sin la interfaz.
- Decisión: descarga automática con `urllib` (biblioteca estándar) y una sola vez por instalación.
- Motivo: desplegar sin subir datos a Git, sin dependencias nuevas y sin cargar de peticiones a la fuente.
- Decisión: el eje de la evolución es "partido n.º del equipo" (orden por fecha), no la jornada oficial.
- Motivo: la fuente no trae jornadas; un partido pospuesto cambiaría el orden y no queremos inventar el dato.
- Decisión: `app.py` quita `football_analytics` de `sys.modules` al inicio de cada ejecución.
- Motivo: tras un `git push`, Streamlit Cloud cargó el `app.py` nuevo con módulos viejos en memoria (ImportError en producción, 2026-10-30). Mover el script a la raíz NO lo resolvía (comprobado con un experimento); limpiar los módulos sí.
- Decisión: dependencias mínimas (pandas, pytest, plotly, streamlit).
- Motivo: evitar dependencias sin uso.

## Fuentes de datos
- Fuente adoptada: football-data.co.uk `new/MEX.csv` — https://www.football-data.co.uk/mexico.php
- Competición/temporada: Liga MX 2012/2013 a 2026/2027 (en curso), 4,780 partidos (revisado 2026-10-30)
- Columnas: Country, League, Season, Date, Time, Home, Away, HG, AG, Res + cuotas de apuestas
- Limitaciones: sin columna Apertura/Clausura ni fase (temporada regular vs. liguilla mezcladas); hora probablemente del Reino Unido; sin licencia explícita ("My data is free"); solo resultados, sin jugadores ni eventos
- Descartadas por ahora: StatsBomb Open Data (no incluye Liga MX); openfootball/mexico (el repo da 404); FBref (requiere scraping, condiciones restrictivas)

## Pruebas
- Comando: `.venv\Scripts\python -m pytest -q` (Python 3.12.3, pandas 3.1.0, pytest 9.2.0)
- Resultado: 37 passed (2026-10-30)
- Pendientes: verificar cómo registra la fuente partidos de liguilla con tiempo extra/penales; revisar el gráfico con tema oscuro de Streamlit (fondo fijo claro)

## Próximo paso
- Subir los cambios para que se actualice la app publicada y verificarla en https://ligamx-analytics.streamlit.app/.
