"""Cálculo de métricas de fútbol a partir de resultados de partidos."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

COLUMNAS_PARTIDOS = ["equipo_local", "equipo_visitante", "goles_local", "goles_visitante"]
COLUMNAS_TABLA = ["equipo", "PJ", "PG", "PE", "PP", "GF", "GC", "DG", "Pts"]


def _validar_partidos(partidos: pd.DataFrame) -> None:
    """Lanza ValueError si faltan columnas o hay goles inválidos."""
    faltantes = [c for c in COLUMNAS_PARTIDOS if c not in partidos.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas en partidos: {faltantes}")

    goles = partidos[["goles_local", "goles_visitante"]]
    if goles.isna().any().any():
        raise ValueError("Hay partidos sin marcador (goles nulos).")
    if (goles < 0).any().any():
        raise ValueError("Hay goles negativos.")


def calcular_tabla_posiciones(
    partidos: pd.DataFrame,
    equipos: Iterable[str] | None = None,
    puntos_victoria: int = 3,
    puntos_empate: int = 1,
) -> pd.DataFrame:
    """Calcula la tabla de posiciones (PJ, PG, PE, PP, GF, GC, DG, Pts).

    Cada partido aporta un registro al local y otro al visitante.
    `equipos` permite incluir equipos sin partidos (aparecen con ceros).
    Los puntos por victoria/empate son parámetros porque dependen del reglamento.
    """
    _validar_partidos(partidos)

    # Una fila por equipo y partido: primero desde la perspectiva del local, luego del visitante.
    local = pd.DataFrame({
        "equipo": partidos["equipo_local"],
        "GF": partidos["goles_local"],
        "GC": partidos["goles_visitante"],
    })
    visitante = pd.DataFrame({
        "equipo": partidos["equipo_visitante"],
        "GF": partidos["goles_visitante"],
        "GC": partidos["goles_local"],
    })
    registros = pd.concat([local, visitante], ignore_index=True)

    registros["PJ"] = 1
    registros["PG"] = (registros["GF"] > registros["GC"]).astype(int)
    registros["PE"] = (registros["GF"] == registros["GC"]).astype(int)
    registros["PP"] = (registros["GF"] < registros["GC"]).astype(int)

    tabla = registros.groupby("equipo")[["PJ", "PG", "PE", "PP", "GF", "GC"]].sum()

    if equipos is not None:
        tabla = tabla.reindex(tabla.index.union(list(equipos)), fill_value=0)

    tabla["DG"] = tabla["GF"] - tabla["GC"]
    tabla["Pts"] = tabla["PG"] * puntos_victoria + tabla["PE"] * puntos_empate

    tabla = tabla.reset_index(names="equipo")
    tabla = tabla.sort_values(["Pts", "DG", "GF", "equipo"], ascending=[False, False, False, True])
    return tabla[COLUMNAS_TABLA].reset_index(drop=True).astype({c: int for c in COLUMNAS_TABLA[1:]})
