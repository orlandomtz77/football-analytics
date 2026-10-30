"""Dashboard de Liga MX: tabla de posiciones y rendimiento local vs. visitante.

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

from football_analytics.charts import grafico_evolucion_puntos, grafico_local_visitante  # noqa: E402
from football_analytics.cleaning import ordenar_torneos  # noqa: E402
from football_analytics.ingest import asegurar_datos, cargar_partidos_procesados  # noqa: E402
from football_analytics.metrics import (  # noqa: E402
    calcular_evolucion_puntos,
    calcular_rendimiento_local_visitante,
    calcular_tabla_posiciones,
    racha_mas_larga,
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
st.title("Liga MX: tabla, local vs. visitante y evolución por equipo")

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

# --- Indicadores ---
goles_por_partido = (regular["goles_local"] + regular["goles_visitante"]).mean()
pct_local = (regular["resultado"] == "H").mean() * 100
pct_empate = (regular["resultado"] == "D").mean() * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("Partidos (fase regular)", len(regular))
col2.metric("Goles por partido", f"{goles_por_partido:.2f}",
            help="Goles totales (local + visitante) divididos entre partidos jugados.")
col3.metric("Victorias locales", f"{pct_local:.1f} %",
            help="Porcentaje de partidos de fase regular que ganó el equipo local.")
col4.metric("Empates", f"{pct_empate:.1f} %")

# --- Tabla de posiciones ---
st.subheader("Tabla de posiciones (fase regular)")
tabla = calcular_tabla_posiciones(regular)
tabla.insert(0, "Pos", range(1, len(tabla) + 1))
tabla = tabla.rename(columns={"equipo": "Equipo"})
# Alto suficiente para ver todos los equipos sin barra de desplazamiento (~35 px por fila).
st.dataframe(tabla, hide_index=True, width="stretch", height=35 * (len(tabla) + 1) + 3)
st.caption(
    "PJ: jugados · PG/PE/PP: ganados, empatados, perdidos · GF/GC: goles a favor/en contra · "
    "DG: diferencia · Pts: 3 por victoria, 1 por empate. Desempate mostrado: Pts, DG, GF "
    "(provisional; el reglamento oficial puede usar otros criterios)."
)

# --- Local vs. visitante ---
st.subheader("¿Quién depende más de jugar en casa?")
rendimiento = calcular_rendimiento_local_visitante(regular)
pj = pd.concat([rendimiento["PJ_local"], rendimiento["PJ_visitante"]])
fig = grafico_local_visitante(
    rendimiento,
    titulo=f"{torneo}: PPP local vs. visitante",
    nota=(
        "PPP = puntos / partidos jugados en esa condición. "
        f"Cada equipo tiene entre {pj.min()} y {pj.max()} partidos por condición: muestra pequeña. "
        "Si solo ves un punto, local y visitante coinciden."
    ),
)
# theme=None conserva los colores validados del gráfico.
st.plotly_chart(fig, theme=None, width="stretch")

with st.expander("Ver datos del gráfico"):
    st.dataframe(rendimiento.round(2), hide_index=True, width="stretch")

# --- Evolución por equipo ---
st.subheader("¿Cómo fue el torneo de cada equipo?")
evolucion = calcular_evolucion_puntos(regular)
orden_tabla = tabla["Equipo"].tolist()  # del líder al último
equipo = st.selectbox("Equipo", orden_tabla, index=0)
# Se compara contra el líder; si el equipo es el líder, contra el segundo lugar.
referencia = orden_tabla[0] if equipo != orden_tabla[0] else (orden_tabla[1] if len(orden_tabla) > 1 else None)

del_equipo = evolucion[evolucion["equipo"] == equipo]
resultados = del_equipo["resultado"].tolist()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Puntos", int(del_equipo["Pts_acumulados"].iloc[-1]))
col2.metric("Últimos 5", " ".join(resultados[-5:]),
            help="Resultados más recientes, del más antiguo al más nuevo. G: ganó · E: empató · P: perdió.")
col3.metric("Mejor racha de victorias", racha_mas_larga(resultados, {"G"}),
            help="Mayor número de partidos seguidos ganados en esta fase regular.")
col4.metric("Mejor racha sin perder", racha_mas_larga(resultados, {"G", "E"}),
            help="Mayor número de partidos seguidos ganados o empatados.")

fig_evolucion = grafico_evolucion_puntos(
    evolucion,
    equipo,
    referencia=referencia,
    titulo=f"{torneo}: puntos acumulados de {equipo}" + (f" vs. {referencia}" if referencia else ""),
    nota="El eje es el número de partido del equipo por fecha, no la jornada oficial (la fuente no trae jornadas).",
)
st.plotly_chart(fig_evolucion, theme=None, width="stretch")

with st.expander(f"Partidos de {equipo}"):
    st.dataframe(del_equipo.drop(columns="equipo"), hide_index=True, width="stretch")

# --- Partidos ---
with st.expander(f"Partidos de {torneo} ({len(del_torneo)})"):
    vista = del_torneo[["fecha", "fase", "equipo_local", "goles_local", "goles_visitante", "equipo_visitante"]]
    st.dataframe(vista.sort_values("fecha"), hide_index=True, width="stretch")
    st.caption("Fecha según la fuente (la zona horaria no está documentada; parece hora del Reino Unido).")

st.divider()
st.caption(
    "Datos: football-data.co.uk (\"My data is free\"; sin licencia formal de redistribución). "
    "Torneo y fase se derivan por fecha en `cleaning.py`. Solo resultados: no incluye jugadores ni xG."
)
