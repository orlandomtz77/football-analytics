"""Datos destacados de un torneo, en frases para aficionados.

Todas las frases salen de cálculos sobre los partidos: no hay texto inventado.
"""

from __future__ import annotations

import pandas as pd

from football_analytics.formato import cantidad, record, unir_nombres
from football_analytics.metrics import calcular_evolucion_puntos, calcular_tabla_posiciones, racha_mas_larga


def _mejores(serie: pd.Series, mayor: bool = True) -> list[str]:
    """Equipos (índice) con el valor máximo (o mínimo) de la serie; varios si empatan."""
    objetivo = serie.max() if mayor else serie.min()
    return sorted(serie[serie == objetivo].index)


def _frase_condicion(partidos: pd.DataFrame, condicion: str, icono: str, titulo: str, donde: str) -> str | None:
    tabla = calcular_tabla_posiciones(partidos, condicion=condicion).set_index("equipo")
    if tabla.empty:
        return None
    # Se compara por puntos por partido porque no todos jugaron el mismo número de veces en esa condición.
    porcentaje = tabla["Pts"] / (tabla["PJ"] * 3)
    mejores = _mejores(porcentaje)
    detalles = [
        f"{e} ({record(tabla.at[e, 'PG'], tabla.at[e, 'PE'], tabla.at[e, 'PP'])} {donde}, "
        f"{tabla.at[e, 'Pts']} de {tabla.at[e, 'PJ'] * 3} puntos posibles)"
        for e in mejores
    ]
    return f"{icono} **{titulo}:** {unir_nombres(detalles)}."


def datos_destacados(partidos: pd.DataFrame) -> list[str]:
    """Frases sobre la fase regular de un torneo. Lista vacía si no hay partidos."""
    if partidos.empty:
        return []

    frases = [
        _frase_condicion(partidos, "local", "🏠", "Mejor local", "en casa"),
        _frase_condicion(partidos, "visitante", "✈️", "Mejor visitante", "de visita"),
    ]

    evolucion = calcular_evolucion_puntos(partidos)
    rachas = evolucion.groupby("equipo")["resultado"].agg(lambda r: racha_mas_larga(r, {"G"}))
    if rachas.max() > 0:
        frases.append(
            f"🔥 **Racha más larga de victorias:** {unir_nombres(_mejores(rachas))}, "
            f"{cantidad(rachas.max(), 'partido seguido', 'partidos seguidos')}."
        )

    tabla = calcular_tabla_posiciones(partidos).set_index("equipo")
    frases.append(f"⚽ **Ataque más goleador:** {unir_nombres(_mejores(tabla['GF']))}, {cantidad(tabla['GF'].max(), 'gol', 'goles')}.")
    frases.append(
        f"🧱 **Menos goles recibidos:** {unir_nombres(_mejores(tabla['GC'], mayor=False))}, "
        f"{cantidad(tabla['GC'].min(), 'gol', 'goles')} en contra."
    )
    return [f for f in frases if f]
