"""Tablas listas para mostrar a aficionados (nombres de columna de medio deportivo mexicano)."""

from __future__ import annotations

import pandas as pd

from football_analytics.cleaning import ordenar_torneos
from football_analytics.formato import ICONO_RESULTADO, forma_con_iconos, record
from football_analytics.metrics import (
    calcular_evolucion_puntos,
    calcular_tabla_posiciones,
    racha_mas_larga,
    ultimos_resultados,
)
from football_analytics.reglamento import asignar_zona

# Nombres usados en la prensa deportiva en México.
COLUMNAS_PRENSA = {"equipo": "Equipo", "PJ": "JJ", "PG": "JG", "PE": "JE", "PP": "JP", "DG": "DIF", "Pts": "PTS"}

TEXTO_RESULTADO = {"G": "Ganó", "E": "Empató", "P": "Perdió"}


def tabla_aficionado(partidos: pd.DataFrame, torneo: str, condicion: str | None = None) -> pd.DataFrame:
    """Tabla con Pos, columnas de prensa, últimos 5 con íconos y zona (solo en la tabla general).

    Con `condicion` ("local"/"visitante") la racha también se limita a esos partidos.
    """
    tabla = calcular_tabla_posiciones(partidos, condicion=condicion)
    evolucion = calcular_evolucion_puntos(partidos)
    if condicion is not None:
        evolucion = evolucion[evolucion["condicion"] == condicion]
    ultimos = ultimos_resultados(evolucion)

    vista = tabla.rename(columns=COLUMNAS_PRENSA)
    vista.insert(0, "Pos", range(1, len(vista) + 1))
    vista["Últimos 5"] = vista["Equipo"].map(lambda e: forma_con_iconos(ultimos.get(e, [])))
    if condicion is None:
        vista["Zona"] = asignar_zona(vista, torneo)
    # PTS junto al equipo: en celular es lo primero que se ve sin deslizar la tabla.
    return vista[["Pos", "Equipo", "PTS"] + [c for c in vista.columns if c not in ("Pos", "Equipo", "PTS")]]


def ficha_equipo(partidos: pd.DataFrame, equipo: str) -> dict:
    """Resumen de un equipo en la fase regular: posición, puntos, distancia al líder, récords y rachas."""
    tabla = calcular_tabla_posiciones(partidos).set_index("equipo")
    if equipo not in tabla.index:
        raise ValueError(f"{equipo} no jugó en estos partidos.")
    local = calcular_tabla_posiciones(partidos, condicion="local").set_index("equipo")
    visita = calcular_tabla_posiciones(partidos, condicion="visitante").set_index("equipo")

    def record_de(t: pd.DataFrame) -> str:
        if equipo not in t.index:
            return record(0, 0, 0)
        return record(t.at[equipo, "PG"], t.at[equipo, "PE"], t.at[equipo, "PP"])

    resultados = calcular_evolucion_puntos(partidos).query("equipo == @equipo")["resultado"].tolist()
    return {
        "posicion": int(tabla.index.get_loc(equipo)) + 1,
        "equipos": len(tabla),
        "puntos": int(tabla.at[equipo, "Pts"]),
        "puntos_del_lider": int(tabla["Pts"].iloc[0]),
        "lider": tabla.index[0],
        "record": record_de(tabla),
        "record_local": record_de(local),
        "record_visita": record_de(visita),
        "ultimos_5": forma_con_iconos(resultados[-5:]),
        "racha_victorias": racha_mas_larga(resultados, {"G"}),
        "racha_sin_perder": racha_mas_larga(resultados, {"G", "E"}),
    }


def calendario_equipo(partidos: pd.DataFrame, equipo: str) -> pd.DataFrame:
    """Partidos del equipo como en un calendario: fecha, rival, dónde, marcador y resultado."""
    evolucion = calcular_evolucion_puntos(partidos)
    del_equipo = evolucion[evolucion["equipo"] == equipo]
    return pd.DataFrame({
        "Fecha": del_equipo["fecha"].dt.strftime("%d/%m/%Y"),
        "Rival": del_equipo["rival"],
        "Dónde": del_equipo["condicion"].map({"local": "🏠 Local", "visitante": "✈️ Visita"}),
        "Marcador": del_equipo["GF"].astype(str) + "-" + del_equipo["GC"].astype(str),
        "Resultado": del_equipo["resultado"].map(lambda r: f"{ICONO_RESULTADO[r]} {TEXTO_RESULTADO[r]}"),
        "Puntos acumulados": del_equipo["Pts_acumulados"],
    }).reset_index(drop=True)


def historial_equipo(
    partidos: pd.DataFrame, equipo: str, campeones: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Una fila por torneo en que jugó `equipo`: posición, puntos, récord y hasta dónde llegó.

    `partidos` debe ser el dataset procesado completo (todas las fases y torneos).
    `Fase final` sale de los partidos de fase final presentes en los datos, no de la posición;
    con `campeones` (salida de `campeones.cargar_campeones`) dice además "🏆 Campeón" o "Subcampeón".
    `% puntos` = PTS / (JJ * 3); sirve para comparar torneos con distinto número de partidos.
    Si se pasan `campeones`, `attrs["con_campeones"]` es True (lo usa `insights.datos_historial`).
    """
    filas = []
    for torneo in ordenar_torneos(partidos["torneo"]):
        del_torneo = partidos[partidos["torneo"] == torneo]
        regular = del_torneo[del_torneo["fase"] == "regular"]
        tabla = calcular_tabla_posiciones(regular).set_index("equipo")
        if equipo not in tabla.index:
            continue
        final = del_torneo[del_torneo["fase"] == "final"]
        jugo_final = bool(((final["equipo_local"] == equipo) | (final["equipo_visitante"] == equipo)).any())
        fase_final = "✅ Sí" if jugo_final else "—"
        if campeones is not None and torneo in campeones.index:
            if campeones.at[torneo, "campeon"] == equipo:
                fase_final = "🏆 Campeón"
            elif campeones.at[torneo, "subcampeon"] == equipo:
                fase_final = "Subcampeón"
        fila = tabla.loc[equipo]
        filas.append({
            "Torneo": torneo,
            "Pos": int(tabla.index.get_loc(equipo)) + 1,
            "Equipos": len(tabla),
            "PTS": int(fila["Pts"]),
            "JJ": int(fila["PJ"]),
            "Récord": record(fila["PG"], fila["PE"], fila["PP"]),
            "DIF": int(fila["DG"]),
            "% puntos": round(100 * fila["Pts"] / (fila["PJ"] * 3)),
            "Fase final": fase_final,
            "Completo": bool(del_torneo["regular_completa"].iloc[0]),
        })
    historial = pd.DataFrame(filas, columns=["Torneo", "Pos", "Equipos", "PTS", "JJ", "Récord", "DIF",
                                             "% puntos", "Fase final", "Completo"])
    historial.attrs["con_campeones"] = campeones is not None
    return historial


# Clásicos de Liga MX con los nombres que usa la fuente.
CLASICOS = {
    "Clásico Nacional": ("Club America", "Guadalajara Chivas"),
    "Clásico Regio": ("Tigres UANL", "Monterrey"),
    "Clásico Capitalino": ("Club America", "UNAM Pumas"),
    "Clásico Joven": ("Club America", "Cruz Azul"),
}


def enfrentamientos(partidos: pd.DataFrame, equipo: str, rival: str) -> pd.DataFrame:
    """Partidos entre `equipo` y `rival` (todas las fases), del más reciente al más antiguo.

    `Resultado` es desde la perspectiva de `equipo`.
    """
    entre = partidos[
        ((partidos["equipo_local"] == equipo) & (partidos["equipo_visitante"] == rival))
        | ((partidos["equipo_local"] == rival) & (partidos["equipo_visitante"] == equipo))
    ].sort_values("fecha", ascending=False)

    es_local = entre["equipo_local"] == equipo
    goles_equipo = entre["goles_local"].where(es_local, entre["goles_visitante"])
    goles_rival = entre["goles_visitante"].where(es_local, entre["goles_local"])
    resultado = pd.Series("E", index=entre.index)
    resultado = resultado.mask(goles_equipo > goles_rival, "G").mask(goles_equipo < goles_rival, "P")

    return pd.DataFrame({
        "Fecha": entre["fecha"],
        "Torneo": entre["torneo"],
        "Fase": entre["fase"].map({"regular": "Regular", "final": "Liguilla / fase final"}),
        "Local": entre["equipo_local"],
        "Marcador": entre["goles_local"].astype(str) + "-" + entre["goles_visitante"].astype(str),
        "Visitante": entre["equipo_visitante"],
        "goles_equipo": goles_equipo,
        "goles_rival": goles_rival,
        "resultado": resultado,
    }).reset_index(drop=True)


def resumen_enfrentamientos(cara: pd.DataFrame) -> dict:
    """Totales de un cara a cara (salida de `enfrentamientos`)."""
    if cara.empty:
        return {"partidos": 0}
    diferencia = cara["goles_equipo"] - cara["goles_rival"]
    return {
        "partidos": len(cara),
        "victorias": int((cara["resultado"] == "G").sum()),
        "empates": int((cara["resultado"] == "E").sum()),
        "derrotas": int((cara["resultado"] == "P").sum()),
        "goles_a_favor": int(cara["goles_equipo"].sum()),
        "goles_en_contra": int(cara["goles_rival"].sum()),
        "ultimos_5": forma_con_iconos(cara["resultado"].iloc[:5].iloc[::-1]),  # del más antiguo al más nuevo
        "ultimo": cara.iloc[0],
        "mayor_victoria": cara.loc[diferencia.idxmax()] if diferencia.max() > 0 else None,
        "mayor_derrota": cara.loc[diferencia.idxmin()] if diferencia.min() < 0 else None,
    }


def tabla_enfrentamientos(cara: pd.DataFrame) -> pd.DataFrame:
    """Versión para mostrar: fecha legible y resultado con ícono."""
    return cara.assign(
        Fecha=cara["Fecha"].dt.strftime("%d/%m/%Y"),
        Resultado=cara["resultado"].map(lambda r: f"{ICONO_RESULTADO[r]} {TEXTO_RESULTADO[r]}"),
    ).drop(columns=["goles_equipo", "goles_rival", "resultado"])
