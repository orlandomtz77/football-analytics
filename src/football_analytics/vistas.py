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


def historial_equipo(partidos: pd.DataFrame, equipo: str) -> pd.DataFrame:
    """Una fila por torneo en que jugó `equipo`: posición, puntos, récord y si jugó la fase final.

    `partidos` debe ser el dataset procesado completo (todas las fases y torneos).
    `Fase final` sale de los partidos de fase final presentes en los datos, no de la posición.
    `% puntos` = PTS / (JJ * 3); sirve para comparar torneos con distinto número de partidos.
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
            "Fase final": "✅ Sí" if jugo_final else "—",
            "Completo": bool(del_torneo["regular_completa"].iloc[0]),
        })
    return pd.DataFrame(filas, columns=["Torneo", "Pos", "Equipos", "PTS", "JJ", "Récord", "DIF",
                                        "% puntos", "Fase final", "Completo"])
