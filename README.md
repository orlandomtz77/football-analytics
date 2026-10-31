# Football Analytics

Dashboard de análisis de fútbol (competición objetivo: Liga MX), construido por módulos:
resultados y tabla de posiciones → rendimiento de equipos → jugadores → eventos → xG → dashboard web.

> Estado: dashboard publicado en https://ligamx-analytics.streamlit.app/ (vista para aficionados: titular del torneo y pestañas Tabla, Lo destacado, Mi equipo, Cara a cara y Partidos) con datos de Liga MX 2012-2026; ver `progreso.md`.

## Instalación (Windows)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Obtener y procesar los datos

Los datos no están en Git. **El dashboard los descarga y procesa solo la primera vez** que se abre
si no encuentra `data/processed/liga_mx_partidos.csv` (desactívalo con `LIGA_MX_DESCARGA=0`).

Para hacerlo a mano (detalles en `data/README.md`):

```powershell
curl.exe -L -o data/raw/football-data_MEX_2026-10-30.csv https://www.football-data.co.uk/new/MEX.csv
$env:PYTHONPATH = "src"
python -m football_analytics.ingest data/raw/football-data_MEX_2026-10-30.csv data/processed/liga_mx_partidos.csv
```

## Abrir el dashboard

Con los datos procesados listos:

```powershell
streamlit run dashboard/app.py
```

Se abre en http://localhost:8501. Para usar otro archivo procesado, define la variable
de entorno `LIGA_MX_DATOS` con su ruta.

## Infografías de partido (StatsBomb)

Mapa de tiros con xG, redes de pases completados y fallidos, y mapa de pases fallidos de un partido,
con el estilo del dashboard. Usa eventos de **StatsBomb Open Data**, que no incluye Liga MX (sí el Mundial
2022, con los partidos de México). Detalles y condiciones de uso en `data/README.md`.

```powershell
pip install -r requirements-infografias.txt
$env:PYTHONPATH = "src"
python -m football_analytics.infografias 3857260                  # Arabia Saudita 1-2 México (Mundial 2022)
python -m football_analytics.infografias 3869685 --tema rayados   # final del Mundial 2022
python -m football_analytics.infografias --help                   # temas, mínimos de pases, --lineas
```

Los PNG se guardan en `salida/` (no se versiona). Los ajustes frecuentes están en
`src/football_analytics/infografias/config.py`; colores y tipografía en `estilo.py`.

## Ejecutar pruebas

```powershell
python -m pytest -q
```

## Estructura

```text
data/raw/            datos originales (no se versionan)
data/processed/      datos limpios generados (no se versionan)
data/reference/      campeones y resultados administrativos (segunda fuente, sí se versionan)
data/README.md       documentación de fuentes
dashboard/app.py     interfaz Streamlit (solo presentación)
src/football_analytics/
  ingest.py          carga del CSV de football-data.co.uk
  cleaning.py        torneo (Apertura/Clausura) y fase (regular/final)
  metrics.py         tabla de posiciones, local/visitante, evolución y rachas
  charts.py          gráficos con Plotly
  reglamento.py      zonas de clasificación por torneo
  insights.py        titular del torneo y datos en frases
  formato.py         récords y racha con íconos
  vistas.py          tablas listas para la interfaz
  campeones.py       campeones por torneo (Wikipedia) validados contra las finales
  correcciones.py    resultados administrativos aplicados al cargar los datos
  infografias/       infografías de partido con StatsBomb (config, estilo, statsbomb, graficos)
tests/               pruebas con pytest
progreso.md          bitácora del proyecto
```

## Uso rápido

```python
import pandas as pd
from football_analytics.metrics import calcular_tabla_posiciones

partidos = pd.DataFrame({
    "equipo_local": [...], "equipo_visitante": [...],
    "goles_local": [...], "goles_visitante": [...],
})
tabla = calcular_tabla_posiciones(partidos, puntos_victoria=3, puntos_empate=1)
```

Los puntos por victoria/empate son parámetros: verifica el reglamento de la temporada.
