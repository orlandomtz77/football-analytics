"""Zonas de clasificación a la fase final por torneo de Liga MX.

Fuente: tablas y notas de formato en Wikipedia (inglés), revisadas el 2026-10-30:
- 2019–20 Liga MX season (Apertura 2019: "The first 8 places ... qualified for the Liguilla").
- 2020–21, 2021–22, 2022–23 seasons (1.º-4.º a cuartos; 5.º-12.º a reclasificación).
- 2023–24, 2024–25, 2025–26 seasons (1.º-6.º a cuartos; 7.º-10.º a play-in; Clausura 2026 sin play-in, 1.º-8.º).
- 2026–27 season (play-in eliminado; 1.º-8.º a cuartos).
Apertura 2012 a Clausura 2019 se toman como 1.º-8.º según la descripción general del formato
(Wikipedia "Liga MX"); no se revisó torneo por torneo.

Las zonas se asignan solo por posición en la tabla. No se modelan excepciones del reglamento,
como el último lugar de la tabla de cociente, que no puede clasificar y cede su lugar.
"""

from __future__ import annotations

import pandas as pd

Zona = tuple[str, int, int]  # (nombre, posición inicial, posición final)

LIGUILLA_8: list[Zona] = [("Liguilla", 1, 8)]
CUARTOS_4_RECLASIFICACION: list[Zona] = [("Cuartos de final", 1, 4), ("Reclasificación", 5, 12)]
CUARTOS_6_PLAY_IN: list[Zona] = [("Cuartos de final", 1, 6), ("Play-in", 7, 10)]
CUARTOS_8: list[Zona] = [("Cuartos de final", 1, 8)]

ZONAS_POR_TORNEO: dict[str, list[Zona] | None] = {
    **{f"{nombre} {anio}": LIGUILLA_8
       for anio in range(2012, 2020) for nombre in ("Apertura", "Clausura")
       if (nombre, anio) != ("Clausura", 2012)},
    "Clausura 2020": None,  # cancelado por COVID-19: no hubo fase final
    **{t: CUARTOS_4_RECLASIFICACION for t in [
        "Apertura 2020", "Clausura 2021", "Apertura 2021", "Clausura 2022", "Apertura 2022", "Clausura 2023",
    ]},
    **{t: CUARTOS_6_PLAY_IN for t in [
        "Apertura 2023", "Clausura 2024", "Apertura 2024", "Clausura 2025", "Apertura 2025",
    ]},
    "Clausura 2026": CUARTOS_8,
    "Apertura 2026": CUARTOS_8,
}


def zonas_del_torneo(torneo: str) -> list[Zona] | None:
    """Zonas de clasificación del torneo, o None si no aplica o no está verificado."""
    return ZONAS_POR_TORNEO.get(torneo)


def asignar_zona(tabla: pd.DataFrame, torneo: str) -> pd.Series:
    """Nombre de la zona de cada fila de `tabla` (ordenada del 1.º al último); "" si no clasifica."""
    zonas = zonas_del_torneo(torneo) or []
    posiciones = range(1, len(tabla) + 1)
    nombres = []
    for posicion in posiciones:
        nombre = next((z for z, desde, hasta in zonas if desde <= posicion <= hasta), "")
        nombres.append(nombre)
    return pd.Series(nombres, index=tabla.index)
