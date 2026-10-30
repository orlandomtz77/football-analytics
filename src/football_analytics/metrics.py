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


def _registros_por_equipo(partidos: pd.DataFrame) -> pd.DataFrame:
    """Una fila por equipo y partido, con `condicion` ("local"/"visitante") y PJ/PG/PE/PP/GF/GC."""
    _validar_partidos(partidos)

    local = pd.DataFrame({
        "equipo": partidos["equipo_local"],
        "condicion": "local",
        "GF": partidos["goles_local"],
        "GC": partidos["goles_visitante"],
    })
    visitante = pd.DataFrame({
        "equipo": partidos["equipo_visitante"],
        "condicion": "visitante",
        "GF": partidos["goles_visitante"],
        "GC": partidos["goles_local"],
    })
    registros = pd.concat([local, visitante], ignore_index=True)

    registros["PJ"] = 1
    registros["PG"] = (registros["GF"] > registros["GC"]).astype(int)
    registros["PE"] = (registros["GF"] == registros["GC"]).astype(int)
    registros["PP"] = (registros["GF"] < registros["GC"]).astype(int)
    return registros


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
    registros = _registros_por_equipo(partidos)
    tabla = registros.groupby("equipo")[["PJ", "PG", "PE", "PP", "GF", "GC"]].sum()

    if equipos is not None:
        tabla = tabla.reindex(tabla.index.union(list(equipos)), fill_value=0)

    tabla["DG"] = tabla["GF"] - tabla["GC"]
    tabla["Pts"] = tabla["PG"] * puntos_victoria + tabla["PE"] * puntos_empate

    tabla = tabla.reset_index(names="equipo")
    tabla = tabla.sort_values(["Pts", "DG", "GF", "equipo"], ascending=[False, False, False, True])
    return tabla[COLUMNAS_TABLA].reset_index(drop=True).astype({c: int for c in COLUMNAS_TABLA[1:]})


def calcular_rendimiento_local_visitante(
    partidos: pd.DataFrame,
    puntos_victoria: int = 3,
    puntos_empate: int = 1,
) -> pd.DataFrame:
    """Compara a cada equipo como local y como visitante.

    Usa puntos por partido (PPP = Pts / PJ) porque un equipo puede jugar
    distinto número de partidos en casa y fuera (p. ej. 9 y 8 en 17 jornadas).
    `dif_PPP` = PPP_local - PPP_visitante: valores altos indican más dependencia de jugar en casa.
    Si un equipo no jugó en alguna condición, su PPP queda vacío (NaN) en vez de dividir entre cero.
    """
    registros = _registros_por_equipo(partidos)
    registros["Pts"] = registros["PG"] * puntos_victoria + registros["PE"] * puntos_empate

    por_condicion = registros.groupby(["equipo", "condicion"])[["PJ", "Pts", "GF", "GC"]].sum()
    por_condicion["PPP"] = por_condicion["Pts"] / por_condicion["PJ"]

    # De formato largo (una fila por equipo y condición) a ancho (una fila por equipo).
    ancho = por_condicion.unstack("condicion")
    ancho = ancho.reindex(columns=["local", "visitante"], level="condicion")
    ancho.columns = [f"{metrica}_{condicion}" for metrica, condicion in ancho.columns]
    for condicion in ["local", "visitante"]:
        for metrica in ["PJ", "Pts", "GF", "GC"]:
            ancho[f"{metrica}_{condicion}"] = ancho[f"{metrica}_{condicion}"].fillna(0).astype(int)

    ancho["dif_PPP"] = ancho["PPP_local"] - ancho["PPP_visitante"]

    columnas = ["equipo"] + [
        f"{metrica}_{condicion}"
        for condicion in ["local", "visitante"]
        for metrica in ["PJ", "Pts", "PPP", "GF", "GC"]
    ] + ["dif_PPP"]
    resultado = ancho.reset_index()
    resultado = resultado.sort_values(["dif_PPP", "equipo"], ascending=[False, True], na_position="last")
    return resultado[columnas].reset_index(drop=True)
