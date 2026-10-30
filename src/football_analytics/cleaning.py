"""Limpieza: separar torneos cortos (Apertura/Clausura) y fases (regular/final)."""

from __future__ import annotations

import pandas as pd


def asignar_torneo(partidos: pd.DataFrame) -> pd.DataFrame:
    """Agrega `torneo` (p. ej. "Apertura 2025") según la fecha.

    Regla: julio-diciembre = Apertura; enero-junio = Clausura.
    """
    resultado = partidos.copy()
    meses = resultado["fecha"].dt.month
    nombre = meses.map(lambda m: "Apertura" if m >= 7 else "Clausura")
    resultado["torneo"] = nombre + " " + resultado["fecha"].dt.year.astype(str)
    return resultado


def asignar_fase(partidos: pd.DataFrame) -> pd.DataFrame:
    """Agrega `fase` ("regular" o "final") y `regular_completa` por torneo.

    La fase regular es una vuelta: con n equipos hay n*(n-1)/2 partidos.
    Los primeros n*(n-1)/2 partidos del torneo (por fecha) son la fase regular;
    el resto es la fase final (liguilla y, desde 2020, repechaje/play-in).
    Lanza ValueError si en la fase regular se repite un enfrentamiento,
    porque eso indicaría que la regla no aplica a ese torneo.
    """
    resultado = partidos.sort_values(["fecha", "hora_fuente"], kind="stable").copy()
    resultado["fase"] = "final"
    resultado["regular_completa"] = False

    for torneo, grupo in resultado.groupby("torneo", sort=False):
        n_equipos = pd.unique(grupo[["equipo_local", "equipo_visitante"]].values.ravel()).size
        n_regular = n_equipos * (n_equipos - 1) // 2
        regular = grupo.index[:n_regular]

        pares = resultado.loc[regular, ["equipo_local", "equipo_visitante"]].apply(frozenset, axis=1)
        if pares.duplicated().any():
            raise ValueError(f"{torneo}: enfrentamientos repetidos en la fase regular.")

        resultado.loc[regular, "fase"] = "regular"
        resultado.loc[grupo.index, "regular_completa"] = len(grupo) >= n_regular

    return resultado.reset_index(drop=True)


def ordenar_torneos(torneos) -> list[str]:
    """Ordena nombres como "Clausura 2026" del más reciente al más antiguo.

    En un mismo año el Clausura (enero-junio) va antes que el Apertura (julio-diciembre).
    """
    def clave(torneo: str) -> tuple[int, int]:
        nombre, anio = torneo.split()
        return int(anio), 1 if nombre == "Apertura" else 0

    return sorted(set(torneos), key=clave, reverse=True)


def preparar_partidos(partidos: pd.DataFrame) -> pd.DataFrame:
    """Aplica todos los pasos de limpieza en orden."""
    return asignar_fase(asignar_torneo(partidos))
