# Progreso — Football Analytics

## Estado actual
- Fase: 3 — dashboard publicado (MVP)
- Última actualización: 2026-10-30
- Objetivo activo: dashboard para aficionados

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
- [x] Rediseño para aficionados (2026-10-30): datos del torneo en frases (`insights.py`), tabla con pestañas General/Local/Visitante, columnas JJ/JG/JE/JP/DIF/PTS, últimos 5 con ✅➖❌ y zonas de clasificación por torneo (`reglamento.py`, verificado en Wikipedia), ficha de equipo con posición, distancia al líder, récords y calendario (`vistas.py`). Gráfico de pesas retirado de la interfaz; gráfica de puntos acumulados movida a un desplegable — implementado, probado (51 pruebas, 29 torneos sin errores) y revisado en escritorio y celular
- [x] Historial del equipo (2026-10-30): `historial_equipo` en `vistas.py`, `datos_historial` en `insights.py` (mejor/peor torneo, fase final, Apertura vs. Clausura con % de puntos y solo torneos terminados), `grafico_historial_puntos` en `charts.py` — implementado, probado (57 pruebas) y revisado en escritorio y celular
- [x] Cara a cara (2026-10-30): `enfrentamientos`, `resumen_enfrentamientos` y `CLASICOS` en `vistas.py`, `datos_cara_a_cara` en `insights.py`; sección en el dashboard con los 4 clásicos o dos equipos a elegir — implementado, probado (62 pruebas, simetría A/B verificada en los 4 clásicos) y revisado visualmente
- [x] Tema oscuro (2026-10-30): las gráficas usan `theme="streamlit"` y solo fijan los colores de las series (azul `#2a78d6`, naranja `#d95926`, gris `#8a8984`, validados contra los fondos claro `#ffffff` y oscuro `#0e1117`); las zonas de la tabla usan fondos semitransparentes sin color de texto fijo — implementado, probado (63 pruebas) y revisado visualmente en ambos temas, incluido el cambio de tema desde el menú sin recargar
- [x] Rediseño visual (2026-10-30): tema propio en `.streamlit/config.toml` (Barlow Condensed para titulares, Barlow para texto; acento azul de las gráficas; modo oscuro verde noche `#0b1310`), titular calculado con datos (`titular_torneo` en `insights.py`: terminado, en curso o cancelado; explica el desempate si hay empate en puntos), pestañas Tabla, Lo destacado, Mi equipo, Cara a cara y Partidos, e indicadores en filas que se acomodan en celular — implementado, probado (67 pruebas) y revisado en escritorio (1280 px) y celular (400 px), modo claro y oscuro
- [x] Campeones (2026-10-30): `data/reference/campeones_liga_mx.csv` (Wikipedia, 27 torneos) y `campeones.py`; validados contra las finales de los datos (27 de 27) y contra Wikipedia en español (17 torneos). Titular "X, campeón del torneo" con cómo se definió la final; historial con "🏆 Campeón"/"Subcampeón", conteo de títulos y trofeos en la gráfica — implementado, probado y revisado visualmente
- [x] Resultados administrativos (2026-10-30): `data/reference/resultados_administrativos.csv` y `correcciones.py`; Clausura 2021 Atlas-América corregido a 3-0; la tabla coincide con Wikipedia — implementado y probado
- [x] Hora de México (2026-10-30): la fuente usa hora del Reino Unido (verificado con 8 partidos de final y 2 de la noche del cambio de horario); `convertir_a_hora_mexico` en `cleaning.py` se aplica al cargar; la pestaña Partidos muestra fecha y hora del centro — implementado, probado y revisado con datos reales
- [x] Partidos por semana de juego (2026-10-30): `semanas_de_juego`, `etiqueta_fechas` y `tabla_partidos` en `vistas.py`; la pestaña Partidos muestra la semana elegida (por defecto la más reciente) con día y hora, y todos los partidos en un desplegable — implementado, probado y revisado en celular (400 px)
- [x] Campeón y subcampeón visibles (2026-10-30): indicadores "🏆 Campeón" y "Subcampeón" en el encabezado de los torneos terminados y columna `Final` en la tabla general (`tabla_aficionado(..., campeones=...)`) — implementado, probado y revisado en celular
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
- Decisión: público principal = aficionado (elegido por el usuario).
- Motivo: las gráficas técnicas (PPP, pesas) eran difíciles de leer para alguien de deportes.
- Decisión: zonas de clasificación solo por posición; no se modelan excepciones (tabla de cociente).
- Motivo: el reglamento cambia por torneo y las excepciones requieren datos que la fuente no trae.
- Decisión: el historial compara torneos con el % de puntos y excluye torneos incompletos.
- Motivo: Apertura 2019 tuvo 18 partidos; el torneo en curso y Clausura 2020 no son comparables.
- Decisión: "jugó la fase final" sale de los partidos de liguilla en los datos; no se indica campeón.
- Motivo: no está verificado cómo registra la fuente los partidos definidos en penales.
- Decisión: franquicias reubicadas (p. ej. Monarcas → Mazatlan FC) se mantienen como equipos separados.
- Motivo: decisión del usuario (2026-10-30); se respetan los nombres de la fuente y el historial de cada club por separado.
- Decisión: el cara a cara incluye fase regular y liguilla, contando cada partido por su marcador.
- Motivo: así se cuentan los clásicos; las series de liguilla definidas por global o penales no se modelan (la fuente no lo indica).
- Decisión: el fondo, los textos y la rejilla de las gráficas los pone el tema de Streamlit (`theme="streamlit"`), no el código.
- Motivo: al cambiar de tema en el menú, Streamlit no vuelve a ejecutar la app; si el código elige los colores (p. ej. con `st.context.theme`), las gráficas quedan con el tema anterior hasta la siguiente interacción (comprobado). El tema de Streamlit se aplica en el navegador y cambia al instante.
- Decisión: identidad visual de prensa deportiva: titular condensado calculado con los datos como elemento principal; el resto sobrio.
- Motivo: público aficionado; el titular dice en una línea lo que más le importa (quién va primero) sin inventar nada (no dice "campeón": la fuente no permite saberlo).
- Decisión: fuentes de Google Fonts cargadas por URL desde el tema de Streamlit.
- Motivo: no hay que subir archivos de fuentes al repo; si Google Fonts no carga, el tema usa sans-serif.
- Decisión: no deducir campeones a partir de los marcadores de la fuente.
- Motivo: verificado contra Wikipedia (2026-10-30) que la fuente no registra penales y a veces guarda el marcador a 90 minutos (Apertura 2016 y 2023) y a veces el de tiempo extra (Clausura 2023).
- Decisión: campeones y resultados administrativos desde Wikipedia, en tablas pequeñas versionadas en `data/reference/`.
- Motivo: la fuente principal no los registra; son pocos datos factuales, con fuente citada y validados contra los partidos.
- Decisión: agrupar partidos por "semana de juego" (días seguidos; el viernes empieza otra semana si hubo partidos martes o miércoles), sin llamarles jornadas.
- Motivo: la fuente no trae la jornada; con esta regla 412 de 550 semanas de fase regular tienen 9 partidos, pero los reprogramados y algunas jornadas de jueves a martes no cuadran con la jornada oficial.
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
- Resultado: 92 passed (2026-10-30)
- Pendientes: ninguno conocido

## Próximo paso
- Por decidir con el usuario. Idea: buscar otros resultados administrativos comparando las tablas completas de cada torneo con Wikipedia.
