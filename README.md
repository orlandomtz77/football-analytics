# Football Analytics

Dashboard de análisis de fútbol (competición objetivo: Liga MX), construido por módulos:
resultados y tabla de posiciones → rendimiento de equipos → jugadores → eventos → xG → dashboard web.

> Estado: dashboard local funcional (tabla de posiciones y local vs. visitante por torneo) con datos de Liga MX 2012-2026; ver `progreso.md`.

## Instalación (Windows)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Obtener y procesar los datos

Los datos no están en Git. Descárgalos y procésalos (detalles en `data/README.md`):

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

## Ejecutar pruebas

```powershell
python -m pytest -q
```

## Estructura

```text
data/raw/            datos originales (no se versionan)
data/processed/      datos limpios generados (no se versionan)
data/README.md       documentación de fuentes
dashboard/app.py     interfaz Streamlit (solo presentación)
src/football_analytics/
  ingest.py          carga del CSV de football-data.co.uk
  cleaning.py        torneo (Apertura/Clausura) y fase (regular/final)
  metrics.py         tabla de posiciones y rendimiento local/visitante
  charts.py          gráficos con Plotly
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
