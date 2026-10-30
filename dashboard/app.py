"""Dashboard de Liga MX para aficionados: datos del torneo, tabla y ficha de equipo.

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

from football_analytics.charts import grafico_evolucion_puntos, grafico_historial_puntos  # noqa: E402
from football_analytics.cleaning import ordenar_torneos  # noqa: E402
from football_analytics.formato import cantidad  # noqa: E402
from football_analytics.ingest import asegurar_datos, cargar_partidos_procesados  # noqa: E402
from football_analytics.insights import datos_cara_a_cara, datos_destacados, datos_historial  # noqa: E402
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
    tabla_enfrentamientos,
)

# La ruta se puede cambiar con la variable de entorno LIGA_MX_DATOS.
RUTA_DATOS = Path(os.environ.get("LIGA_MX_DATOS", RAIZ / "data" / "processed" / "liga_mx_partidos.csv"))
CARPETA_CRUDOS = RAIZ / "data" / "raw"
# Si faltan los datos se descargan una vez de la fuente; LIGA_MX_DESCARGA=0 lo desactiva.
DESCARGA_AUTOMATICA = os.environ.get("LIGA_MX_DESCARGA", "1") != "0"


@st.cache_data
def cargar_datos(ruta: str) -> tuple[pd.DataFrame, dict | None]:
    return cargar_partidos_procesados(ruta)


st.set_page_config(page_title="Liga MX — Análisis", page_icon="⚽", layout="wide")
st.title("⚽ Liga MX")

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

if metadatos:
    st.caption(
        f"Fuente: [{metadatos['fuente']}]({metadatos['url']}) · "
        f"datos obtenidos el {metadatos['fecha_obtencion']} · "
        f"partidos del {metadatos['fecha_min']} al {metadatos['fecha_max']}"
    )
else:
    st.caption("Fuente: football-data.co.uk · sin metadatos de fecha (vuelve a ejecutar `ingest`).")

# --- Filtros ---
torneos = ordenar_torneos(partidos["torneo"])
torneo = st.selectbox("Torneo", torneos, index=0)

del_torneo = partidos[partidos["torneo"] == torneo]
regular = del_torneo[del_torneo["fase"] == "regular"]

if regular.empty:
    st.info(f"No hay partidos de fase regular registrados para {torneo}.")
    st.stop()

if not del_torneo["regular_completa"].iloc[0]:
    st.warning(
        f"La fase regular de {torneo} está incompleta en los datos "
        f"({len(regular)} partidos). Puede estar en curso o haberse suspendido "
        "(Clausura 2020 se canceló por COVID-19). La tabla refleja solo lo jugado."
    )

# --- Indicadores del torneo ---
goles_por_partido = (regular["goles_local"] + regular["goles_visitante"]).mean()
pct_local = (regular["resultado"] == "H").mean() * 100
pct_empate = (regular["resultado"] == "D").mean() * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("Partidos jugados", len(regular), help="Fase regular.")
col2.metric("Goles por partido", f"{goles_por_partido:.1f}")
col3.metric("Ganó el local", f"{pct_local:.0f} %", help="Porcentaje de partidos que ganó el equipo de casa.")
col4.metric("Empates", f"{pct_empate:.0f} %")

# --- Datos del torneo ---
st.subheader("📰 Datos del torneo")
for frase in datos_destacados(regular):
    st.markdown(f"- {frase}")

# --- Tabla ---
st.subheader("🏆 Tabla general")
FONDO_ZONA = {
    "Liguilla": "#e6f4ea", "Cuartos de final": "#e6f4ea",
    "Reclasificación": "#fff4d6", "Play-in": "#fff4d6",
}


def resaltar_zona(fila: pd.Series) -> list[str]:
    fondo = FONDO_ZONA.get(fila.get("Zona", ""), "")
    estilo = f"background-color: {fondo}; color: #0b0b0b" if fondo else ""
    return [estilo] * len(fila)


def mostrar_tabla(vista: pd.DataFrame) -> None:
    alto = 35 * (len(vista) + 1) + 3  # todas las filas sin barra de desplazamiento
    st.dataframe(
        vista.style.apply(resaltar_zona, axis=1),
        hide_index=True,
        width="stretch",
        height=alto,
        # Pos y Equipo fijas al deslizar la tabla en pantallas chicas.
        column_config={"Pos": st.column_config.NumberColumn(pinned=True),
                       "Equipo": st.column_config.TextColumn(pinned=True)},
    )


pestana_general, pestana_local, pestana_visita = st.tabs(["General", "🏠 Local", "✈️ Visitante"])
with pestana_general:
    general = tabla_aficionado(regular, torneo)
    mostrar_tabla(general)
    zonas = zonas_del_torneo(torneo)
    if zonas:
        texto_zonas = " · ".join(f"{nombre}: {desde}.º a {hasta}.º" for nombre, desde, hasta in zonas)
        st.caption(
            f"**Clasificación ({torneo}):** {texto_zonas}. Zonas según la posición en la tabla; "
            "no considera excepciones del reglamento (por ejemplo, la tabla de cociente)."
        )
    else:
        st.caption(f"{torneo} no tuvo fase final (se canceló por COVID-19).")
with pestana_local:
    st.caption("Solo partidos en casa.")
    mostrar_tabla(tabla_aficionado(regular, torneo, condicion="local"))
with pestana_visita:
    st.caption("Solo partidos de visita.")
    mostrar_tabla(tabla_aficionado(regular, torneo, condicion="visitante"))
st.caption(
    "JJ: jugados · JG/JE/JP: ganados, empatados, perdidos · GF/GC: goles a favor/en contra · DIF: diferencia · "
    "Últimos 5: ✅ ganó · ➖ empató · ❌ perdió (del más antiguo al más reciente). "
    "Empates en puntos ordenados por DIF y GF (el reglamento oficial puede usar otros criterios)."
)

# --- Ficha de equipo ---
st.subheader("📋 Ficha de equipo")
equipo = st.selectbox("Equipo", general["Equipo"].tolist(), index=0)
ficha = ficha_equipo(regular, equipo)

diferencia = ficha["puntos_del_lider"] - ficha["puntos"]
if ficha["posicion"] == 1:
    texto_lider = "Es el líder"
else:
    texto_lider = f"A {cantidad(diferencia, 'punto', 'puntos')}"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Posición", f"{ficha['posicion']}.º de {ficha['equipos']}")
col2.metric("Puntos", ficha["puntos"])
col3.metric("Del líder", texto_lider, help=f"Líder: {ficha['lider']} con {ficha['puntos_del_lider']} puntos.")
col4.metric("Récord", ficha["record"], help="Ganados-Empatados-Perdidos.")

st.markdown(f"**Últimos 5:** {ficha['ultimos_5']}")
st.markdown(f"🏠 **En casa:** {ficha['record_local']} · ✈️ **De visita:** {ficha['record_visita']}")
st.markdown(
    f"🔥 **Mejor racha:** {cantidad(ficha['racha_victorias'], 'victoria seguida', 'victorias seguidas')} · "
    f"{cantidad(ficha['racha_sin_perder'], 'partido', 'partidos')} sin perder"
)

st.markdown("**Resultados**")
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
    # theme=None conserva los colores validados del gráfico.
    st.plotly_chart(fig, theme=None, width="stretch")

# --- Historial del equipo ---
st.subheader(f"📚 Historial de {equipo}")
historial = historial_equipo(partidos, equipo)
for frase in datos_historial(historial, equipo):
    st.markdown(f"- {frase}")
st.caption(
    "Mejor/peor torneo y promedios usan el % de puntos obtenidos y solo torneos terminados. "
    "El nombre del equipo es el de la fuente: si un club cambió de nombre o de sede, aparece por separado."
)
st.plotly_chart(grafico_historial_puntos(historial, equipo), theme=None, width="stretch")
st.caption("Barras grises: torneo en curso o cancelado.")

with st.expander("Ver tabla del historial"):
    tabla_historial = historial.assign(
        Torneo=historial["Torneo"] + historial["Completo"].map({True: "", False: " (incompleto)"}),
        Pos=historial["Pos"].astype(str) + ".º de " + historial["Equipos"].astype(str),
    ).drop(columns=["Equipos", "Completo"])
    st.dataframe(tabla_historial, hide_index=True, width="stretch")

# --- Cara a cara ---
st.subheader("⚔️ Cara a cara")
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
    col1, col2, col3 = st.columns(3)
    col1.metric(f"Ganó {equipo_a}", resumen["victorias"])
    col2.metric("Empates", resumen["empates"])
    col3.metric(f"Ganó {equipo_b}", resumen["derrotas"])
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
with st.expander(f"Todos los partidos de {torneo} ({len(del_torneo)})"):
    vista = pd.DataFrame({
        "Fecha": del_torneo["fecha"].dt.strftime("%d/%m/%Y"),
        "Fase": del_torneo["fase"].map({"regular": "Regular", "final": "Liguilla / fase final"}),
        "Local": del_torneo["equipo_local"],
        "Marcador": del_torneo["goles_local"].astype(str) + "-" + del_torneo["goles_visitante"].astype(str),
        "Visitante": del_torneo["equipo_visitante"],
    })
    st.dataframe(vista, hide_index=True, width="stretch")
    st.caption("Fecha según la fuente (no documenta la zona horaria; parece hora del Reino Unido).")

st.divider()
st.caption(
    "Datos: football-data.co.uk (\"My data is free\"; sin licencia formal de redistribución). "
    "Solo resultados: no incluye goleadores, alineaciones ni estadísticas de jugadores."
)
