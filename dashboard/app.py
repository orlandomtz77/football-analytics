"""Dashboard de Liga MX para aficionados: titular del torneo, tabla, ficha de equipo y cara a cara.

Ejecutar desde la raíz del proyecto:
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
# Permite importar el paquete sin instalarlo (el código vive en src/).
sys.path.insert(0, str(RAIZ / "src"))

# Streamlit no recarga módulos fuera de dashboard/ cuando cambian (p. ej. tras un git pull
# en Streamlit Cloud): app.py nuevo + módulos viejos en memoria = ImportError.
# Quitarlos de sys.modules obliga a importar la versión actual en cada ejecución.
for _modulo in [m for m in sys.modules if m == "football_analytics" or m.startswith("football_analytics.")]:
    del sys.modules[_modulo]

from football_analytics.campeones import (  # noqa: E402
    FUENTE_CAMPEONES,
    FUENTE_CAMPEONES_URL,
    cargar_campeones,
    validar_campeones,
)
from football_analytics.charts import grafico_evolucion_puntos, grafico_historial_puntos  # noqa: E402
from football_analytics.cleaning import convertir_a_hora_mexico, ordenar_torneos  # noqa: E402
from football_analytics.correcciones import aplicar_correcciones, cargar_correcciones  # noqa: E402
from football_analytics.formato import cantidad  # noqa: E402
from football_analytics.ingest import asegurar_datos, cargar_partidos_procesados  # noqa: E402
from football_analytics.insights import (  # noqa: E402
    COMO_SE_DEFINIO,
    datos_cara_a_cara,
    datos_destacados,
    datos_historial,
    titular_torneo,
)
from football_analytics.metrics import calcular_evolucion_puntos  # noqa: E402
from football_analytics.reglamento import zonas_del_torneo  # noqa: E402
from football_analytics.vistas import (  # noqa: E402
    CLASICOS,
    calendario_equipo,
    enfrentamientos,
    ficha_equipo,
    historial_equipo,
    resumen_enfrentamientos,
    tabla_aficionado,
    semanas_de_juego,
    tabla_enfrentamientos,
    tabla_partidos,
)

# La ruta se puede cambiar con la variable de entorno LIGA_MX_DATOS.
RUTA_DATOS = Path(os.environ.get("LIGA_MX_DATOS", RAIZ / "data" / "processed" / "liga_mx_partidos.csv"))
CARPETA_CRUDOS = RAIZ / "data" / "raw"
# Si faltan los datos se descargan una vez de la fuente; LIGA_MX_DESCARGA=0 lo desactiva.
DESCARGA_AUTOMATICA = os.environ.get("LIGA_MX_DESCARGA", "1") != "0"


@st.cache_data
def cargar_datos(ruta: str) -> tuple[pd.DataFrame, dict | None]:
    partidos, metadatos = cargar_partidos_procesados(ruta)
    # Resultados que la liga cambió en la mesa (la fuente guarda el marcador de la cancha).
    try:
        partidos, _ = aplicar_correcciones(partidos, cargar_correcciones())
    except (OSError, ValueError):
        partidos = partidos.assign(resultado_administrativo=False)
    # La fuente usa la hora del Reino Unido; se muestra la del centro de México.
    return convertir_a_hora_mexico(partidos), metadatos


def mostrar_indicadores(indicadores: list[tuple[str, object, str | None]]) -> None:
    """Indicadores en una fila que se acomoda sola: en celular pasan a la siguiente línea según quepan."""
    fila = st.container(horizontal=True, gap="large")
    for etiqueta, valor, ayuda in indicadores:
        fila.metric(etiqueta, valor, help=ayuda, width="content")


st.set_page_config(page_title="Liga MX — Análisis", page_icon="⚽", layout="wide")

if DESCARGA_AUTOMATICA and not RUTA_DATOS.exists():
    try:
        with st.spinner("Descargando datos de football-data.co.uk (solo la primera vez)..."):
            asegurar_datos(RUTA_DATOS, CARPETA_CRUDOS)
    except OSError as error:
        st.error(
            f"No se pudieron descargar los datos: {error}.\n\n"
            "Revisa tu conexión y recarga la página, o descárgalos manualmente (ver `README.md`)."
        )
        st.stop()
    except ValueError as error:
        st.error(f"El archivo descargado no tiene el formato esperado: {error}")
        st.stop()

try:
    partidos, metadatos = cargar_datos(str(RUTA_DATOS))
except FileNotFoundError:
    st.error(
        f"No se encontró el archivo de datos `{RUTA_DATOS}`.\n\n"
        "Descárgalo y procésalo siguiendo las instrucciones del `README.md` "
        "(sección *Obtener y procesar los datos*)."
    )
    st.stop()

# Campeones (segunda fuente): solo se usan los torneos cuya final coincide con los partidos.
try:
    campeones = cargar_campeones()
except (OSError, ValueError):
    campeones = None
if campeones is not None:
    campeones = campeones.drop(index=list(validar_campeones(campeones, partidos)))
    if campeones.empty:
        campeones = None

# --- Encabezado: torneo, titular e indicadores ---
torneos = ordenar_torneos(partidos["torneo"])
col_marca, col_torneo = st.columns([3, 1], vertical_alignment="bottom")
col_marca.markdown("#### ⚽ Liga MX")
torneo = col_torneo.selectbox("Torneo", torneos, index=0)

del_torneo = partidos[partidos["torneo"] == torneo]
regular = del_torneo[del_torneo["fase"] == "regular"]

if regular.empty:
    st.info(f"No hay partidos de fase regular registrados para {torneo}.")
    st.stop()

if del_torneo["regular_completa"].iloc[0]:
    estado = "terminado"
elif torneo == torneos[0]:
    estado = "en_curso"
else:
    estado = "cancelado"  # en los datos solo ocurre en Clausura 2020 (COVID-19)

# El titular es lo primero que se lee, como la portada de un diario deportivo.
campeon = campeones.loc[torneo] if campeones is not None and torneo in campeones.index else None
titular, bajada = titular_torneo(regular, torneo, estado, campeon=campeon)
st.title(titular)
st.markdown(bajada)

if estado == "en_curso":
    st.caption(
        f"El {torneo} sigue en juego: la tabla refleja los {len(regular)} partidos jugados "
        f"hasta el {regular['fecha'].max():%d/%m/%Y}."
    )
elif estado == "cancelado":
    st.warning(f"El {torneo} se canceló antes de terminar la fase regular ({len(regular)} partidos jugados).")

goles_por_partido = (regular["goles_local"] + regular["goles_visitante"]).mean()
pct_local = (regular["resultado"] == "H").mean() * 100
pct_empate = (regular["resultado"] == "D").mean() * 100

if estado == "terminado" and campeon is not None:
    # Podio: dos tarjetas, más protagonistas que las estadísticas del torneo.
    como = COMO_SE_DEFINIO[campeon["definicion"]]
    tarjeta_campeon, tarjeta_subcampeon = st.columns(2)
    with tarjeta_campeon.container(border=True):
        st.metric("🏆 Campeón", campeon["campeon"])
        st.caption(f"Ganó la final {como}.")
    with tarjeta_subcampeon.container(border=True):
        st.metric("Subcampeón", campeon["subcampeon"])
        st.caption(f"Perdió la final {como}.")

mostrar_indicadores([
    ("Partidos jugados", len(regular), "Fase regular."),
    ("Goles por partido", f"{goles_por_partido:.1f}", None),
    ("Ganó el local", f"{pct_local:.0f} %", "Porcentaje de partidos que ganó el equipo de casa."),
    ("Empates", f"{pct_empate:.0f} %", None),
])

pestana_tabla, pestana_destacado, pestana_equipo, pestana_cara, pestana_partidos = st.tabs(
    ["Tabla", "Lo destacado", "Mi equipo", "Cara a cara", "Partidos"]
)

# --- Tabla ---
# Semitransparentes: se ven bien sobre fondo claro y oscuro, y el texto conserva el color del tema.
FONDO_ZONA = {
    "Liguilla": "rgba(34, 160, 80, 0.18)", "Cuartos de final": "rgba(34, 160, 80, 0.18)",
    "Reclasificación": "rgba(237, 161, 0, 0.22)", "Play-in": "rgba(237, 161, 0, 0.22)",
}


def resaltar_zona(fila: pd.Series) -> list[str]:
    fondo = FONDO_ZONA.get(fila.get("Zona", ""), "")
    estilo = f"background-color: {fondo}" if fondo else ""
    return [estilo] * len(fila)


def mostrar_tabla(vista: pd.DataFrame) -> None:
    alto = 35 * (len(vista) + 1) + 3  # todas las filas sin barra de desplazamiento
    estilo = vista.style.apply(resaltar_zona, axis=1).map(lambda _: "font-weight: 600", subset=["Equipo", "PTS"])
    st.dataframe(
        estilo,
        hide_index=True,
        width="stretch",
        height=alto,
        # Pos y Equipo fijas al deslizar la tabla en pantallas chicas; Zona y Final sin recortar.
        column_config={"Pos": st.column_config.NumberColumn(pinned=True),
                       "Equipo": st.column_config.TextColumn(pinned=True),
                       "Zona": st.column_config.TextColumn(width="medium"),
                       "Final": st.column_config.TextColumn(width="medium")},
    )


def leyenda_zonas(zonas) -> None:
    """Fichas de color con las zonas de clasificación, arriba de la tabla."""
    fichas = [
        f'<span style="display:inline-block;width:0.8em;height:0.8em;border-radius:2px;'
        f'background:{FONDO_ZONA[nombre]};border:1px solid rgba(128,128,128,0.4);'
        f'vertical-align:-0.1em;margin-right:0.35em"></span>{nombre} ({desde}.º al {hasta}.º)'
        for nombre, desde, hasta in zonas
    ]
    st.caption("&emsp;".join(fichas), unsafe_allow_html=True)


with pestana_tabla:
    pestana_general, pestana_local, pestana_visita = st.tabs(["General", "🏠 Local", "✈️ Visitante"])
    with pestana_general:
        general = tabla_aficionado(regular, torneo, campeones=campeones)
        zonas = zonas_del_torneo(torneo)
        if zonas:
            leyenda_zonas(zonas)
        mostrar_tabla(general)
        if zonas:
            st.caption(
                "Zonas según la posición en la tabla; no considera excepciones del reglamento "
                "(por ejemplo, la tabla de cociente)."
            )
        else:
            st.caption(f"El {torneo} no tuvo fase final (se canceló por COVID-19).")
    with pestana_local:
        st.caption("Solo partidos en casa.")
        mostrar_tabla(tabla_aficionado(regular, torneo, condicion="local"))
    with pestana_visita:
        st.caption("Solo partidos de visita.")
        mostrar_tabla(tabla_aficionado(regular, torneo, condicion="visitante"))
    st.caption(
        "JJ: jugados. JG/JE/JP: ganados, empatados, perdidos. GF/GC: goles a favor y en contra. DIF: diferencia. "
        "Últimos 5: ✅ ganó, ➖ empató, ❌ perdió (del más antiguo al más reciente). "
        "Los empates en puntos se ordenan por DIF y GF; el reglamento oficial puede usar otros criterios."
    )

# --- Lo destacado ---
with pestana_destacado:
    for frase in datos_destacados(regular):
        st.markdown(f"- {frase}")

# --- Mi equipo: ficha e historial ---
with pestana_equipo:
    equipo = st.selectbox("Equipo", general["Equipo"].tolist(), index=0)
    ficha = ficha_equipo(regular, equipo)

    diferencia = ficha["puntos_del_lider"] - ficha["puntos"]
    if ficha["posicion"] == 1:
        texto_lider = "Es el líder"
    else:
        texto_lider = f"A {cantidad(diferencia, 'punto', 'puntos')}"

    mostrar_indicadores([
        ("Posición", f"{ficha['posicion']}.º de {ficha['equipos']}", None),
        ("Puntos", ficha["puntos"], None),
        ("Del líder", texto_lider, f"Líder: {ficha['lider']} con {ficha['puntos_del_lider']} puntos."),
        ("Récord", ficha["record"], "Ganados-Empatados-Perdidos."),
    ])

    st.markdown(f"**Últimos 5:** {ficha['ultimos_5']}")
    st.markdown(f"🏠 **En casa:** {ficha['record_local']}. ✈️ **De visita:** {ficha['record_visita']}.")
    st.markdown(
        f"🔥 **Mejor racha:** {cantidad(ficha['racha_victorias'], 'victoria seguida', 'victorias seguidas')} y "
        f"{cantidad(ficha['racha_sin_perder'], 'partido', 'partidos')} sin perder."
    )

    st.subheader(f"Resultados de {equipo}")
    calendario = calendario_equipo(regular, equipo)
    st.dataframe(calendario, hide_index=True, width="stretch", height=35 * (len(calendario) + 1) + 3)

    with st.expander("Ver gráfica de puntos acumulados"):
        lider = ficha["lider"]
        referencia = lider if equipo != lider else (general["Equipo"].iloc[1] if len(general) > 1 else None)
        fig = grafico_evolucion_puntos(
            calcular_evolucion_puntos(regular),
            equipo,
            referencia=referencia,
            titulo=f"Puntos acumulados: {equipo}" + (f" vs. {referencia}" if referencia else ""),
            nota="Cada punto es un partido del equipo, en orden de fecha (la fuente no indica la jornada oficial).",
        )
        # El tema de Streamlit pone fondo y textos (claro u oscuro); las series conservan sus colores validados.
        st.plotly_chart(fig, theme="streamlit", width="stretch")

    st.subheader(f"Historial de {equipo}")
    historial = historial_equipo(partidos, equipo, campeones=campeones)
    for frase in datos_historial(historial, equipo):
        st.markdown(f"- {frase}")
    st.caption(
        "Mejor y peor torneo y promedios usan el % de puntos obtenidos y solo torneos terminados. "
        "El nombre del equipo es el de la fuente: si un club cambió de nombre o de sede, aparece por separado."
    )
    st.plotly_chart(grafico_historial_puntos(historial, equipo), theme="streamlit", width="stretch")
    st.caption("Barras grises: torneo en curso o cancelado." + (" 🏆: campeón." if campeones is not None else ""))

    with st.expander("Ver tabla del historial"):
        tabla_historial = historial.assign(
            Torneo=historial["Torneo"] + historial["Completo"].map({True: "", False: " (incompleto)"}),
            Pos=historial["Pos"].astype(str) + ".º de " + historial["Equipos"].astype(str),
        ).drop(columns=["Equipos", "Completo"])
        st.dataframe(tabla_historial, hide_index=True, width="stretch")

# --- Cara a cara ---
with pestana_cara:
    OTRO = "Elegir dos equipos…"
    opciones = [f"{nombre}: {a} vs. {b}" for nombre, (a, b) in CLASICOS.items()] + [OTRO]
    eleccion = st.selectbox("Enfrentamiento", opciones, index=0)
    if eleccion == OTRO:
        todos = sorted(set(partidos["equipo_local"]) | set(partidos["equipo_visitante"]))
        col1, col2 = st.columns(2)
        equipo_a = col1.selectbox("Equipo", todos, index=todos.index(equipo) if equipo in todos else 0)
        rivales = [e for e in todos if e != equipo_a]
        equipo_b = col2.selectbox("Rival", rivales, index=0)
    else:
        equipo_a, equipo_b = CLASICOS[eleccion.split(":")[0]]

    cara = enfrentamientos(partidos, equipo_a, equipo_b)
    resumen = resumen_enfrentamientos(cara)
    if resumen["partidos"] == 0:
        st.info(f"{equipo_a} y {equipo_b} no se enfrentaron en Liga MX entre los datos disponibles (desde 2012).")
    else:
        mostrar_indicadores([
            (f"Ganó {equipo_a}", resumen["victorias"], None),
            ("Empates", resumen["empates"], None),
            (f"Ganó {equipo_b}", resumen["derrotas"], None),
        ])
        for frase in datos_cara_a_cara(resumen, equipo_a, equipo_b):
            st.markdown(f"- {frase}")
        st.markdown(f"**Últimos 5 de {equipo_a}:** {resumen['ultimos_5']}")
        with st.expander(f"Ver los {resumen['partidos']} partidos"):
            st.dataframe(tabla_enfrentamientos(cara), hide_index=True, width="stretch")
        st.caption(
            "Solo partidos de Liga MX desde el Apertura 2012, fase regular y liguilla (no incluye Copa MX, "
            "Concacaf ni amistosos). Cada partido cuenta por su marcador: en liguilla, la serie pudo definirse "
            "por global o penales."
        )

# --- Partidos del torneo ---
with pestana_partidos:
    # Por semana de juego: la fuente no trae el número de jornada.
    semanas = semanas_de_juego(del_torneo)
    eleccion_semana = st.selectbox("Semana", semanas["etiqueta"].tolist(), index=0)
    de_la_semana = del_torneo.loc[semanas.set_index("etiqueta").at[eleccion_semana, "partidos"]]
    st.dataframe(tabla_partidos(de_la_semana), hide_index=True, width="stretch")
    st.caption(
        "La fuente no indica la jornada: se agrupan los partidos jugados en las mismas fechas. "
        "Un partido reprogramado aparece en la semana en que se jugó."
    )
    with st.expander(f"Todos los partidos del {torneo} ({len(del_torneo)})"):
        st.dataframe(tabla_partidos(del_torneo), hide_index=True, width="stretch")
    administrativos = del_torneo[del_torneo["resultado_administrativo"]]
    if not administrativos.empty:
        lista = "; ".join(
            f"{f.equipo_local} {f.goles_local}-{f.goles_visitante} {f.equipo_visitante}"
            for f in administrativos.itertuples()
        )
        st.caption(
            f"Resultado administrativo (la liga cambió el marcador en la mesa; la tabla usa el oficial): {lista}."
        )
    st.caption(
        "Fecha y hora del centro de México (la fuente usa la hora del Reino Unido y se convierte). "
        "Los partidos en Tijuana se juegan en hora del Pacífico."
    )

st.divider()
if metadatos:
    st.caption(
        f"Fuente: [{metadatos['fuente']}]({metadatos['url']}), datos obtenidos el {metadatos['fecha_obtencion']} "
        f"con partidos del {partidos['fecha'].min():%d/%m/%Y} al {partidos['fecha'].max():%d/%m/%Y}."
        + (f" Campeones: [{FUENTE_CAMPEONES}]({FUENTE_CAMPEONES_URL})." if campeones is not None else "")
    )
else:
    st.caption("Fuente: football-data.co.uk, sin metadatos de fecha (vuelve a ejecutar `ingest`).")
st.caption(
    "Datos de football-data.co.uk (\"My data is free\"; sin licencia formal de redistribución). "
    "Solo resultados: no incluye goleadores, alineaciones ni estadísticas de jugadores."
)
