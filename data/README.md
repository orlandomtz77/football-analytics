# Datos

- `raw/`: datos originales tal como se descargaron. **No se modifican.**
- `processed/`: datos limpios generados por el código.

Ninguna de las dos carpetas se sube a Git. Cada dataset se documenta aquí.

## Plantilla por dataset

- **Fuente y URL:**
- **Competición / temporada / rango de fechas:**
- **Fecha de obtención:**
- **Granularidad:** (partido, equipo, jugador, disparo, pase…)
- **Columnas:** nombre, tipo, unidad, definición
- **Faltantes y limitaciones:**
- **Licencia / condiciones de uso:**

## Datasets registrados

### football-data.co.uk — Liga MX (`MEX.csv`)

- **Fuente y URL:** football-data.co.uk, https://www.football-data.co.uk/mexico.php
  (descarga directa: https://www.football-data.co.uk/new/MEX.csv)
- **Archivo crudo:** `raw/football-data_MEX_2026-10-30.csv`
- **Competición / temporada / rango:** Liga MX, 2012/2013 a 2026/2027 (en curso);
  21/07/2012 a 29/10/2026; 4,780 partidos.
- **Fecha de obtención:** 2026-10-30
- **Granularidad:** un renglón por partido (incluye fase regular y liguilla).
- **Columnas usadas:**

  | Fuente | Proyecto | Definición |
  |---|---|---|
  | Season | temporada | Temporada de la fuente (junta Apertura + Clausura) |
  | Date | fecha | Fecha del partido (dd/mm/aaaa) |
  | Time | hora_fuente | Hora de inicio; zona horaria no documentada (parece Reino Unido) |
  | Home / Away | equipo_local / equipo_visitante | Nombres de la fuente, en inglés y sin acentos |
  | HG / AG | goles_local / goles_visitante | Goles al final del tiempo reglamentario* |
  | Res | resultado | H = gana local, D = empate, A = gana visitante |

  \*No verificado cómo registra la fuente los partidos de liguilla definidos en tiempo extra o penales.
  Las columnas de cuotas de apuestas (PSCH, B365CH, etc.) se descartan.

- **Validaciones (2026-10-30):** sin nulos en goles/resultado, sin duplicados (fecha+local+visitante),
  `Res` coherente con el marcador en todos los partidos.
- **Limitaciones:**
  - No hay columna de torneo ni de fase: se derivan en `cleaning.py` (julio-diciembre = Apertura,
    enero-junio = Clausura; los primeros n·(n−1)/2 partidos de cada torneo = fase regular).
  - Clausura 2020 quedó incompleto (90 partidos, cancelado por COVID-19) y está marcado con
    `regular_completa = False`. Apertura 2019 tuvo 19 equipos.
  - Hay franquicias reubicadas (p. ej. Monarcas → Mazatlan FC) que la fuente nombra distinto.
  - Solo resultados: no hay jugadores, tiros, eventos ni xG.
- **Licencia / condiciones:** el sitio dice "My data is free"; no hay licencia formal de
  redistribución, por eso el archivo no se sube a Git.

### Procesado: `processed/liga_mx_partidos.csv`

Generado con:

```powershell
$env:PYTHONPATH = "src"
.venv\Scripts\python -m football_analytics.ingest data/raw/football-data_MEX_2026-10-30.csv data/processed/liga_mx_partidos.csv
```

Agrega `torneo`, `fase` (`regular` / `final`) y `regular_completa`.

Si el procesado no existe, `asegurar_datos()` (usado por el dashboard) descarga `MEX.csv` una sola vez,
lo valida antes de aceptarlo y genera el procesado. No vuelve a descargar mientras el archivo exista;
para actualizar los datos, borra `processed/liga_mx_partidos.csv`.
Comprobación: la tabla de la fase regular del Apertura 2025 coincide con la de
https://en.wikipedia.org/wiki/2025–26_Liga_MX_season (18 equipos, todas las columnas y el orden).
