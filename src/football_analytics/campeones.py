"""Campeones de Liga MX por torneo, desde una segunda fuente (Wikipedia).

football-data.co.uk no registra penales y trata el tiempo extra de forma inconsistente
(ver data/README.md), así que el campeón no se puede deducir de sus marcadores.
La tabla `data/reference/campeones_liga_mx.csv` usa los nombres de equipo de football-data.co.uk
y se valida contra las finales presentes en los partidos.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RUTA_CAMPEONES = Path(__file__).resolve().parents[2] / "data" / "reference" / "campeones_liga_mx.csv"
FUENTE_CAMPEONES = "Wikipedia, «List of Mexican football champions» (consultada el 2026-10-30)"
FUENTE_CAMPEONES_URL = "https://en.wikipedia.org/wiki/List_of_Mexican_football_champions"

DEFINICIONES = {"global", "tiempo extra", "penales"}


def cargar_campeones(ruta: str | Path = RUTA_CAMPEONES) -> pd.DataFrame:
    """Tabla de campeones indexada por torneo (columnas: campeon, subcampeon, definicion)."""
    campeones = pd.read_csv(ruta, dtype=str)
    faltantes = {"torneo", "campeon", "subcampeon", "definicion"} - set(campeones.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas en {ruta}: {sorted(faltantes)}")
    desconocidas = set(campeones["definicion"]) - DEFINICIONES
    if desconocidas:
        raise ValueError(f"Definición desconocida en {ruta}: {sorted(desconocidas)}")
    repetidos = campeones.loc[campeones["torneo"].duplicated(), "torneo"].tolist()
    if repetidos:
        raise ValueError(f"Torneo repetido en {ruta}: {repetidos}")
    return campeones.set_index("torneo")


def validar_campeones(campeones: pd.DataFrame, partidos: pd.DataFrame) -> dict[str, str]:
    """Problemas por torneo al comparar la tabla con los partidos; diccionario vacío si todo cuadra.

    Para cada torneo, campeón y subcampeón deben ser los dos equipos de los dos últimos
    partidos de fase final (ida y vuelta de la final).
    """
    problemas = {}
    for torneo, fila in campeones.iterrows():
        final = partidos[(partidos["torneo"] == torneo) & (partidos["fase"] == "final")].sort_values("fecha").tail(2)
        equipos = [set(final[["equipo_local", "equipo_visitante"]].iloc[i]) for i in range(len(final))]
        if len(equipos) < 2 or equipos[0] != equipos[1]:
            problemas[torneo] = "no hay una final (dos partidos) en los datos."
            continue
        if equipos[0] != {fila["campeon"], fila["subcampeon"]}:
            problemas[torneo] = (
                f"la tabla dice {fila['campeon']} vs. {fila['subcampeon']}, "
                f"pero la final en los datos es {' vs. '.join(sorted(equipos[0]))}."
            )
    return problemas
