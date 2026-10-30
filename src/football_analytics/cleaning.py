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


# La fuente usa la hora del Reino Unido (verificado con finales de 2016, 2019 y 2023 en invierno y verano).
ZONA_FUENTE = "Europe/London"
ZONA_MEXICO = "America/Mexico_City"  # hora del centro, la de las transmisiones


def convertir_a_hora_mexico(partidos: pd.DataFrame) -> pd.DataFrame:
    """Copia con `fecha` en hora del centro de México (fecha y hora de inicio) y la columna `hora` ("HH:MM").

    La fecha original de la fuente queda en `fecha_fuente`. Los partidos de noche aparecen en la fuente
    un día después. En la noche de octubre en que el Reino Unido atrasa el reloj, la 01:00 se repite:
    se toma la de horario normal (verificado en dos partidos de 2023 y 2024). Los equipos de Tijuana
    juegan en hora del Pacífico, pero aquí se muestra la hora del centro.
    """
    inicio = pd.to_datetime(
        partidos["fecha"].dt.strftime("%Y-%m-%d") + " " + partidos["hora_fuente"].str.strip(),
        format="%Y-%m-%d %H:%M",
    )
    en_mexico = (
        inicio.dt.tz_localize(ZONA_FUENTE, ambiguous=False, nonexistent="shift_forward")
        .dt.tz_convert(ZONA_MEXICO)
        .dt.tz_localize(None)
    )
    return partidos.assign(fecha_fuente=partidos["fecha"], fecha=en_mexico, hora=en_mexico.dt.strftime("%H:%M"))
