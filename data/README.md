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
  | Date | fecha | Fecha del partido (dd/mm/aaaa) en hora del Reino Unido** |
  | Time | hora_fuente | Hora de inicio en hora del Reino Unido (no documentado por la fuente; verificado)** |
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

  \*\*Fecha y hora están en hora del Reino Unido (`Europe/London`, con horario de verano). Verificado
  el 2026-10-30 contra la hora oficial de inicio de 8 partidos de final en Wikipedia (Apertura 2016,
  Clausura 2019, Clausura 2023 y Apertura 2023: invierno y verano, con y sin horario de verano en México):
  al convertir a `America/Mexico_City` coinciden los 8. Por eso los partidos de noche aparecen en la fuente
  un día después. La app convierte al cargar (`cleaning.convertir_a_hora_mexico`; la fecha original queda
  en `fecha_fuente`). En la noche de octubre en que el Reino Unido atrasa el reloj, la 01:00 se repite
  (27 partidos): se toma la de horario normal, verificado con Chivas-Tigres del 28/10/2023 (19:05) y
  Pumas-Cruz Azul del 26/10/2024 (19:00, Mediotiempo). Se muestra la hora del centro de México, también
  para los partidos en Tijuana (hora del Pacífico).
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

### StatsBomb Open Data — eventos de partido (`raw/statsbomb/`)

- **Fuente y URL:** StatsBomb Open Data, https://github.com/statsbomb/open-data
  (archivos: `data/events/<id>.json`, `data/lineups/<id>.json`, `data/matches/<comp>/<temporada>.json`).
- **Uso en el proyecto:** solo las infografías de partido (`football_analytics.infografias`); el dashboard
  de Liga MX no las usa.
- **Cobertura (revisada el 2026-10-30):** 24 competiciones en `competitions.json`; **no incluye Liga MX** ni
  ninguna competición de México. Sí incluye el Mundial 2022 (competición 43, temporada 106), con los partidos
  de México: 3857265 (México 0-0 Polonia), 3857289 (Argentina 2-0 México), 3857260 (Arabia Saudita 1-2 México).
- **Granularidad:** un renglón por evento (pase, tiro, presión, cambio...) con coordenadas en una cancha de
  120 x 80 y xG de StatsBomb en los tiros.
- **Descarga:** una sola vez por partido a `raw/statsbomb/` (no se modifica después; ignorado por Git).
- **Validaciones (2026-10-30):** el marcador calculado coincide con el oficial en la final del Mundial 2022
  (3-3 sin la tanda de penales) y en Canadá 1-2 Marruecos, que incluye un autogol (`Own Goal For` cuenta para
  el equipo beneficiado).
- **Condiciones:** StatsBomb los ofrece "for public use for research projects and genuine interest in football
  analytics" y pide, al publicar, citar a StatsBomb como fuente **y usar su logo** (Media Pack). El acuerdo de
  uso (LICENSE.pdf del repositorio) no se pudo leer en línea: revisarlo antes de publicar las imágenes.
- **Limitaciones:** el periodo 5 (tanda de penales) se descarta; los nombres de equipo vienen en inglés.

### Datos de eventos de Liga MX (tiros, pases, xG): búsqueda del 2026-10-30

No se encontró ninguna fuente **abierta** con eventos de Liga MX (coordenadas de tiros y pases). Resumen:

| Opción | Qué tiene | Estado |
|---|---|---|
| StatsBomb Open Data | Eventos completos con xG | No incluye Liga MX (verificado en `competitions.json`) |
| FBref (con datos de Opta) | Páginas de Liga MX con xG por jugador y por partido | Solo páginas web, sin descarga; sus términos de uso no se pudieron leer (403). No se extrae |
| API-Football | API con plan gratuito (según terceros: 100 peticiones/día) | Cobertura de Liga MX y tipo de datos sin confirmar: la página oficial respondió 403 |
| Opta / Stats Perform, StatsBomb, Wyscout (pago) | Eventos con coordenadas | Requieren contrato comercial |
| Sofascore, FotMob | Mapas de tiros en sus apps | Sin API oficial; no se extraen datos contra sus condiciones |

Pasos siguientes posibles: crear una cuenta gratuita de API-Football y revisar en su panel si Liga MX trae
estadísticas por partido (tiros, posesión); confirmar los términos de FBref antes de usar cualquier dato suyo.
Mientras tanto, las infografías de Liga MX usan solo resultados (`football_analytics.infografias.liga_mx`).

### Referencia: `reference/escudos_thesportsdb.csv` (escudos de los equipos)

- **Fuente:** TheSportsDB (https://www.thesportsdb.com), API v1, búsqueda por nombre (`searchteams.php`).
  Generada con `python -m football_analytics.escudos` el 2026-10-31.
- **Contenido:** equipo (nombre de football-data.co.uk), id de TheSportsDB, nombre en TheSportsDB y la
  **dirección** del escudo. Las imágenes no se guardan en el repositorio: la app las carga de TheSportsDB tal cual.
- **Cobertura:** 23 de 25 equipos. Los id se verificaron a mano (país, liga y estadio). Sin escudo:
  Monarcas (TheSportsDB lo mezcla con Atlético Morelia, otro club) y Lobos BUAP (no aparece).
- **Condiciones (https://www.thesportsdb.com/docs_terms_of_use.php):** la clave gratuita ("123") es para
  proyectos de desarrollo y las apps publicadas requieren el plan de pago; los logos son marcas de cada club y
  la API no otorga permiso para usarlos (deben mostrarse sin modificar). Wikipedia trata estos escudos como
  material protegido de uso no libre. **Decisión del usuario (2026-10-31): usarlos con esta información.**
  La app cita a TheSportsDB y aclara que los escudos son marcas de cada club.

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
