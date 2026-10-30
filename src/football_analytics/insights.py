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


def _criterio_desempate(primero: pd.Series, segundo: pd.Series) -> str:
    """Por qué `primero` va arriba de `segundo` con los mismos puntos (desempate provisional de la tabla)."""
    if primero["DG"] != segundo["DG"]:
        return "diferencia de goles"
    if primero["GF"] != segundo["GF"]:
        return "goles a favor"
    return "orden alfabético"


COMO_SE_DEFINIO = {"global": "en el marcador global", "tiempo extra": "en tiempo extra", "penales": "en penales"}


def _titular_campeon(tabla: pd.DataFrame, torneo: str, campeon: pd.Series) -> tuple[str, str]:
    lider, puntos = tabla.index[0], tabla["Pts"].iloc[0]
    if campeon["campeon"] == lider:
        regular = f"También terminó primero en la fase regular, con {cantidad(puntos, 'punto', 'puntos')}."
    else:
        regular = f"{lider} terminó primero en la fase regular con {cantidad(puntos, 'punto', 'puntos')}."
    return (
        f"{campeon['campeon']}, campeón del {torneo}",
        f"Le ganó la final a {campeon['subcampeon']} {COMO_SE_DEFINIO[campeon['definicion']]}. {regular}",
    )


def titular_torneo(
    partidos: pd.DataFrame, torneo: str, estado: str, campeon: pd.Series | None = None
) -> tuple[str, str]:
    """Titular y bajada del torneo, como en la portada de un diario deportivo.

    `partidos`: fase regular del torneo. `estado`: "terminado", "en_curso" o "cancelado".
    `campeon`: fila de `campeones.cargar_campeones` (campeon, subcampeon, definicion); solo se usa si
    el torneo terminó. Sin ella el titular habla del líder de la fase regular y no dice "campeón".
    """
    titulares = {
        "terminado": "{lider} terminó primero en la fase regular del {torneo}",
        "en_curso": "{lider} lidera el {torneo}",
        "cancelado": "{lider} iba primero cuando se canceló el {torneo}",
    }
    if estado not in titulares:
        raise ValueError(f"Estado desconocido: {estado!r}. Usa uno de {sorted(titulares)}.")

    tabla = calcular_tabla_posiciones(partidos).set_index("equipo")
    if estado == "terminado" and campeon is not None:
        return _titular_campeon(tabla, torneo, campeon)
    lider = tabla.index[0]
    primero = tabla.iloc[0]
    titular = titulares[estado].format(lider=lider, torneo=torneo)

    en_curso = estado == "en_curso"
    bajada = (
        f"{'Suma ' if en_curso else ''}{cantidad(primero['Pts'], 'punto', 'puntos')} en "
        f"{cantidad(primero['PJ'], 'partido', 'partidos')}"
    )
    if len(tabla) > 1:
        segundo = tabla.iloc[1]
        ventaja = primero["Pts"] - segundo["Pts"]
        if ventaja > 0:
            bajada += f", {ventaja} más que {tabla.index[1]}"
        else:
            verbos = ("empata", "va") if en_curso else ("empató", "quedó")
            bajada += (
                f"; {verbos[0]} en puntos con {tabla.index[1]} y {verbos[1]} arriba por "
                f"{_criterio_desempate(primero, segundo)}"
            )
    bajada = bajada[0].upper() + bajada[1:] + "."
    return titular, bajada


def datos_historial(historial: pd.DataFrame, equipo: str) -> list[str]:
    """Frases sobre el historial de un equipo (salida de `vistas.historial_equipo`).

    Mejor/peor torneo y promedios usan solo torneos completos (sin el actual ni Clausura 2020).
    """
    if historial.empty:
        return []
    completos = historial[historial["Completo"]].set_index("Torneo")
    frases = [f"📅 **Torneos en los datos:** {len(historial)} (desde {historial['Torneo'].iloc[-1]})."]
    if historial.attrs.get("con_campeones"):
        # Del más antiguo al más reciente, como se cuentan los títulos.
        titulos = historial.loc[historial["Fase final"] == "🏆 Campeón", "Torneo"].iloc[::-1].tolist()
        if titulos:
            frases.append(f"🏆 **Títulos:** {len(titulos)} ({unir_nombres(titulos)}).")
        else:
            frases.append(f"🏆 **Títulos:** ninguno desde el {historial['Torneo'].iloc[-1]}.")
    if completos.empty:
        return frases

    mejores = _mejores(completos["% puntos"])
    peores = _mejores(completos["% puntos"], mayor=False)

    def detalle(torneos: list[str]) -> str:
        return unir_nombres([
            f"{t} ({completos.at[t, 'PTS']} pts, {completos.at[t, 'Pos']}.º lugar)" for t in torneos
        ])

    frases.append(f"⭐ **Mejor torneo:** {detalle(mejores)}.")
    frases.append(f"📉 **Peor torneo:** {detalle(peores)}.")

    # Solo torneos terminados: en el actual y en Clausura 2020 nadie pudo jugar la fase final.
    con_fase_final = (completos["Fase final"] != "—").sum()  # "✅ Sí", "🏆 Campeón" o "Subcampeón"
    frases.append(f"🏟️ **Jugó la fase final:** {con_fase_final} de {cantidad(len(completos), 'torneo terminado', 'torneos terminados')}.")

    tipo = completos.index.str.split().str[0]
    promedio = completos.groupby(tipo)["% puntos"].mean().round()
    if {"Apertura", "Clausura"} <= set(promedio.index):
        a, c = int(promedio["Apertura"]), int(promedio["Clausura"])
        if a == c:
            comparacion = "rinde igual en ambos"
        else:
            comparacion = f"rinde mejor en {'Apertura' if a > c else 'Clausura'}"
        frases.append(
            f"🔁 **Apertura vs. Clausura:** {equipo} {comparacion} "
            f"(obtiene en promedio el {a} % de los puntos posibles en Apertura y el {c} % en Clausura)."
        )
    return frases


def datos_cara_a_cara(resumen: dict, equipo: str, rival: str) -> list[str]:
    """Frases del cara a cara (salida de `vistas.resumen_enfrentamientos`)."""
    if resumen["partidos"] == 0:
        return []
    v, e, d = resumen["victorias"], resumen["empates"], resumen["derrotas"]
    if v == d:
        balance = "el historial está parejo"
    else:
        lider, ventaja = (equipo, v - d) if v > d else (rival, d - v)
        balance = f"{lider} lleva ventaja por {cantidad(ventaja, 'victoria', 'victorias')}"
    frases = [
        f"📊 **Balance:** en {cantidad(resumen['partidos'], 'partido', 'partidos')}, {balance} "
        f"({equipo} {v} · empates {e} · {rival} {d}).",
        f"⚽ **Goles:** {equipo} {resumen['goles_a_favor']} · {rival} {resumen['goles_en_contra']}.",
    ]
    ultimo = resumen["ultimo"]
    frases.append(
        f"🕐 **Último partido:** {ultimo['Local']} {ultimo['Marcador']} {ultimo['Visitante']} "
        f"({ultimo['Torneo']}, {ultimo['Fecha']:%d/%m/%Y})."
    )
    for clave, quien in (("mayor_victoria", equipo), ("mayor_derrota", rival)):
        partido = resumen[clave]
        if partido is not None:
            frases.append(
                f"💥 **Victoria más amplia de {quien}:** {partido['Local']} {partido['Marcador']} {partido['Visitante']} "
                f"({partido['Torneo']})."
            )
    return frases
