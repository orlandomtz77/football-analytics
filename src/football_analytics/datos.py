"""Carga de los datos de Liga MX listos para analizar (la usan el dashboard y las infografías).

Une los pasos que se aplican al cargar: partidos procesados, resultados administrativos (correcciones.py),
hora del centro de México (cleaning.py) y campeones validados contra las finales (campeones.py).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from football_analytics.campeones import cargar_campeones, validar_campeones
from football_analytics.cleaning import convertir_a_hora_mexico, ordenar_torneos
from football_analytics.correcciones import aplicar_correcciones, cargar_correcciones
from football_analytics.ingest import cargar_partidos_procesados

RUTA_PROCESADO = Path(__file__).resolve().parents[2] / "data" / "processed" / "liga_mx_partidos.csv"


def cargar_liga_mx(ruta: str | Path = RUTA_PROCESADO) -> tuple[pd.DataFrame, dict | None]:
    """Partidos procesados con resultados oficiales y fecha/hora de México, más sus metadatos.

    Lanza FileNotFoundError si no existe el procesado (ver README: Obtener y procesar los datos).
    """
    partidos, metadatos = cargar_partidos_procesados(ruta)
    # Resultados que la liga cambió en la mesa (la fuente guarda el marcador de la cancha).
    try:
        partidos, _ = aplicar_correcciones(partidos, cargar_correcciones())
    except (OSError, ValueError):
        partidos = partidos.assign(resultado_administrativo=False)
    # La fuente usa la hora del Reino Unido; se usa la del centro de México.
    return convertir_a_hora_mexico(partidos), metadatos


def campeones_validos(partidos: pd.DataFrame) -> pd.DataFrame | None:
    """Campeones (Wikipedia) solo de los torneos cuya final coincide con los partidos; None si no hay."""
    try:
        campeones = cargar_campeones()
    except (OSError, ValueError):
        return None
    campeones = campeones.drop(index=list(validar_campeones(campeones, partidos)))
    return None if campeones.empty else campeones


def estado_torneo(partidos: pd.DataFrame, torneo: str) -> str:
    """Devuelve "terminado", "en_curso" (el más reciente sin terminar) o "cancelado" (en los datos: Clausura 2020)."""
    del_torneo = partidos[partidos["torneo"] == torneo]
    if del_torneo.empty:
        raise ValueError(f"No hay partidos de {torneo} en los datos.")
    if del_torneo["regular_completa"].iloc[0]:
        return "terminado"
    return "en_curso" if torneo == ordenar_torneos(partidos["torneo"])[0] else "cancelado"
