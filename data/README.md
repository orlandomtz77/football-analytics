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
  | Date | fecha | Fecha del partido (dd/mm/aaaa); en partidos nocturnos va un día adelantada** |
  | Time | hora_fuente | Hora de inicio; zona horaria no documentada (parece Reino Unido) |
  | Home / Away | equipo_local / equipo_visitante | Nombres de la fuente, en inglés y sin acentos |
  | HG / AG | goles_local / goles_visitante | Goles del partido; en liguilla, inconsistente con el tiempo extra* |
  | Res | resultado | H = gana local, D = empate, A = gana visitante |

  \*Verificado el 2026-10-30 contra Wikipedia (páginas "Apertura 2016", "Apertura 2023" y
  "Clausura 2023 Liga MX final phase"): **la fuente no registra penales y trata el tiempo extra
  de forma inconsistente.**
  - Apertura 2016, vuelta Tigres-América: 1-1 tras tiempo extra (goles 95' y 119'), Tigres campeón
    en penales; la fuente registra 0-0 (marcador a 90 minutos).
  - Apertura 2023, vuelta América-Tigres: 3-0 tras tiempo extra (goles 91', 104' y 120'); la fuente
    registra 0-0 (marcador a 90 minutos).
  - Clausura 2023, vuelta Chivas-Tigres: 2-2 a los 90 minutos y 2-3 tras tiempo extra (gol 110');
    la fuente registra 2-3 (incluye el tiempo extra).

  Consecuencia: el campeón **no se puede deducir de forma confiable** con estos datos. Con el marcador
  de la fuente, 8 de las 27 finales quedan empatadas en el global, y en las demás no se puede descartar
  que el marcador incluya tiempo extra.

  \*\*La fecha de la fuente parece estar en hora del Reino Unido: Apertura 2016 ida (22/12/2016 en
  México) aparece el 23/12; Apertura 2023 vuelta (17/12/2023) aparece el 18/12; Clausura 2023 vuelta
  (28/05/2023) aparece el 29/05.
  Las columnas de cuotas de apuestas (PSCH, B365CH, etc.) se descartan.

- **Validaciones (2026-10-30):** sin nulos en goles/resultado, sin duplicados (fecha+local+visitante),
  `Res` coherente con el marcador en todos los partidos.
- **Limitaciones:**
  - No hay columna de torneo ni de fase: se derivan en `cleaning.py` (julio-diciembre = Apertura,
    enero-junio = Clausura; los primeros n·(n−1)/2 partidos de cada torneo = fase regular).
  - Clausura 2020 quedó incompleto (90 partidos, cancelado por COVID-19) y está marcado con
    `regular_completa = False`. Apertura 2019 tuvo 19 equipos.
  - Hay franquicias reubicadas (p. ej. Monarcas → Mazatlan FC) que la fuente nombra distinto.
    **Decisión (2026-10-30):** se mantienen como equipos separados, tal como los nombra la fuente;
    no se unifican historiales.
  - Solo resultados: no hay jugadores, tiros, eventos ni xG.
- **Licencia / condiciones:** el sitio dice "My data is free"; no hay licencia formal de
  redistribución, por eso el archivo no se sube a Git.

### Referencia: `reference/campeones_liga_mx.csv`

- **Fuente:** Wikipedia, «List of Mexican football champions»
  (https://en.wikipedia.org/wiki/List_of_Mexican_football_champions), consultada el 2026-10-30.
  Contenido de Wikipedia bajo licencia CC BY-SA 4.0; aquí solo se guardan datos factuales
  (campeón, subcampeón y cómo se definió la final) con la fuente citada en la interfaz.
- **Por qué existe:** football-data.co.uk no permite saber al campeón (ver arriba).
- **Cobertura:** Apertura 2012 a Clausura 2026, 27 torneos (Clausura 2020 no tuvo campeón).
  Wikipedia llama "Guardianes 2020" y "Guardianes 2021" a los que aquí son Apertura 2020 y Clausura 2021.
- **Columnas:** torneo, campeon, subcampeon (nombres de football-data.co.uk), definicion
  (`global`, `tiempo extra` o `penales`).
- **Validación (2026-10-30):**
  - Campeón y subcampeón coinciden con los dos equipos de la final en los datos en los 27 torneos
    (`campeones.validar_campeones`; la app descarta cualquier torneo que no cuadre).
  - Segunda comprobación con Wikipedia en español («Anexo:Tabla de líderes generales de la Liga MX»):
    coinciden los 17 torneos en que el líder general fue campeón o subcampeón.

### Referencia: `reference/resultados_administrativos.csv`

- **Qué es:** partidos cuyo resultado oficial cambió en la mesa. football-data.co.uk guarda el marcador
  de la cancha; la app aplica el oficial al cargar los datos (`correcciones.py`), sin modificar los
  archivos crudo ni procesado, y solo si el marcador de cancha coincide con el registrado.
- **Casos (2026-10-30):** Clausura 2021, Atlas 0-2 América (jornada 7) → 3-0 para Atlas, porque América
  alineó a un jugador no elegible (Wikipedia, «2020–21 Liga MX season»). Con la corrección, la tabla del
  Clausura 2021 coincide con la de Wikipedia (Cruz Azul 41, América 38).
- **Cómo se encontró:** al comparar el líder de la fase regular de nuestros datos con Wikipedia en los
  27 torneos, solo el Clausura 2021 no coincidía. Puede haber otros resultados administrativos que no
  cambian al líder y que no se han detectado.

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
