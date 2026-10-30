# Progreso — Football Analytics

## Estado actual
- Fase: 0 — estructura inicial y primera métrica
- Última actualización: 2026-10-29
- Objetivo activo: elegir una fuente de datos de Liga MX con cobertura y licencia verificadas

## Completado
- [x] Repositorio Git inicializado (sin commits todavía)
- [x] Estructura de carpetas, `.gitignore`, `.env.example`, `requirements.txt`, `README.md`, `data/README.md`
- [x] `calcular_tabla_posiciones` en `src/football_analytics/metrics.py` — implementado y probado
- [x] `tests/test_metrics.py`: victoria, empate, derrota, equipo sin partidos, orden, coherencia, reglamento configurable, tabla vacía y validaciones

## En curso
- Tarea: ninguna
- Bloqueos: no hay datos reales todavía

## Decisiones técnicas
- Decisión: puntos por victoria/empate como parámetros (3-1 por defecto).
- Motivo: CLAUDE.md pide no asumir 3-1-0 sin verificar el reglamento.
- Decisión: desempate provisional por Pts, DG, GF y nombre.
- Motivo: falta verificar los criterios oficiales de desempate de Liga MX por temporada.
- Decisión: dependencias mínimas (pandas, pytest); Streamlit/Plotly se agregan cuando se usen.
- Motivo: evitar dependencias sin uso.

## Fuentes de datos
- Fuente: ninguna todavía
- Competición/temporada: —
- Cobertura y limitaciones: —

## Pruebas
- Comando: `.venv\Scripts\python -m pytest -q` (Python 3.12.3, pandas 3.1.0, pytest 9.2.0)
- Resultado: 7 passed (2026-10-29)
- Pendientes: pruebas de ingestión/limpieza cuando exista un dataset

## Próximo paso
- Investigar y elegir una fuente de resultados de Liga MX (cobertura, licencia, formato), descargar una temporada a `data/raw/` y documentarla en `data/README.md`.
