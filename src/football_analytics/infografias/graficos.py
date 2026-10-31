"""Infografías de un partido: mapa de tiros, redes de pases y mapa de pases fallidos.

Este archivo solo maneja DATOS y composición. Colores, líneas y efectos viven en estilo.py.
Cada gráfico responde una pregunta:
- mapa_de_tiros: ¿quién generó más peligro y desde dónde? (tamaño = xG)
- red_de_pases: ¿cómo circulaba el balón entre los titulares?
- mapa_pases_fallidos: ¿dónde perdía el balón el equipo?
"""

from __future__ import annotations

import pandas as pd

from football_analytics.infografias import config, estilo


def tramo_hasta_primer_cambio(d: pd.DataFrame) -> pd.DataFrame:
    """Eventos de un equipo antes de su primera sustitución (solo titulares). Sin cambios: todos."""
    subs = d[d.tipo == "Substitution"]
    if subs.empty:
        return d
    corte = subs.iloc[0]
    return d[(d.periodo < corte.periodo) | ((d.periodo == corte.periodo) & (d.minuto < corte.minuto))]


def conexiones_de_pases(
    df: pd.DataFrame, equipo: str, completados: bool = True, minimo: int = 4, cortar_en_primer_cambio: bool = True
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(posiciones, pares) de la red de pases de `equipo`.

    posiciones: índice jugador, columnas x, y (posición promedio) y n (pases intentados). Usa TODOS los
    pases del jugador para que la posición sea la misma en la red de completados y la de fallidos.
    pares: jugador, receptor, n (pases completados o fallidos de jugador a receptor), solo n >= minimo.
    """
    d = df[df.equipo == equipo]
    if cortar_en_primer_cambio:
        d = tramo_hasta_primer_cambio(d)
    todos = d[d.tipo == "Pass"]
    pases = todos[todos.pase_ok == completados].dropna(subset=["receptor"])
    posiciones = todos.groupby("jugador").agg(x=("x", "mean"), y=("y", "mean"), n=("x", "size"))
    pares = (pases.groupby(["jugador", "receptor"]).size()
             .reset_index(name="n").query("n >= @minimo").reset_index(drop=True))
    return posiciones, pares


def mapa_de_tiros(df, equipos, titulo, ruta, T):
    pitch, fig, ax = estilo.nueva_cancha(T)
    tiros = df[df.tipo == "Shot"]
    colores = [T["tiro_a"], T["tiro_b"]]

    for i, eq in enumerate(equipos):
        t = tiros[tiros.equipo == eq].copy()
        if i == 1:  # espejo: el 2º equipo ataca hacia la izquierda
            t["x"], t["y"] = 120 - t.x, 80 - t.y
        gol = t.resultado == "Goal"
        pitch.scatter(t[~gol].x, t[~gol].y, s=t[~gol].xg * 1500 + 40, ax=ax,
                      color=colores[i], alpha=0.6, edgecolors=T["texto"], linewidth=0.8, zorder=2)
        pitch.scatter(t[gol].x, t[gol].y, s=t[gol].xg * 1500 + 250, ax=ax,
                      color=colores[i], marker="*", edgecolors=T["texto"], linewidth=1.2, zorder=3)
        ax.text(5 if i == 1 else 115, -3, f"{eq}\n{len(t)} tiros · xG {t.xg.sum():.2f}",
                color=colores[i], ha="left" if i == 1 else "right",
                va="top", fontsize=13, fontweight="semibold")

    estilo.titulo(fig, ax, titulo, T)
    estilo.pie(fig, f"Tamaño = xG (goles esperados) · ★ = gol · {config.ATRIBUCION}", T)
    estilo.guardar(fig, ruta)


def red_de_pases(df, equipo, titulo, ruta, T, completados=True, minimo=4, direccional=True,
                 cortar_en_primer_cambio=True):
    """Posición promedio y conexiones (por defecto hasta el primer cambio del equipo).
    completados=False dibuja la red de pases FALLIDOS (hacia el receptor previsto).
    direccional=True: una flecha curva por sentido (A->B y B->A por separado, con su número).
    direccional=False: líneas simples (si hay pases en ambos sentidos se encimarían)."""
    pos, pares = conexiones_de_pases(df, equipo, completados, minimo, cortar_en_primer_cambio)

    pitch, fig, ax = estilo.nueva_cancha(T)
    color_lineas = T["ok"] if completados else T["fallido"]
    nmax = max(pares.n.max(), 1) if len(pares) else 1

    def radio(j):  # radio del nodo en puntos
        return (pos.loc[j, "n"] * 8 + 100) ** 0.5 / 3.14159 ** 0.5 + 2

    for _, r in pares.iterrows():
        if r.jugador in pos.index and r.receptor in pos.index:
            a, b = pos.loc[r.jugador], pos.loc[r.receptor]
            rel = r.n / nmax  # grosor y opacidad relativos al par más frecuente
            if direccional:
                estilo.flecha_curva(ax, a, b, color_lineas, 1 + 6 * rel, 0.55 + 0.4 * rel,
                                    radio(r.jugador), radio(r.receptor))
                estilo.etiqueta_flecha(ax, a, b, str(int(r.n)), color_lineas, T)
            else:
                estilo.linea(pitch, ax, a, b, color_lineas, 1.5 + 7 * rel, 0.35 + 0.55 * rel, T)
    estilo.nodos(pitch, ax, pos.x, pos.y, pos.n * 8 + 100, T["ok"], T)
    for nombre, r in pos.iterrows():
        pitch.annotate(nombre, (r.x, r.y - 4.5), ax=ax, color=T["texto"],
                       ha="center", va="center", fontsize=9.5, fontweight="semibold", zorder=5)

    tipo = "completados" if completados else "fallidos (hacia el receptor previsto)"
    if direccional:
        tipo += " · flecha = sentido, número = cantidad"
    tramo = "hasta el primer cambio" if cortar_en_primer_cambio else "todo el partido"
    estilo.titulo(fig, ax, titulo, T)
    estilo.pie(fig, f"Pases {tipo} · mín. {minimo} · {tramo} · {config.ATRIBUCION}", T)
    estilo.guardar(fig, ruta)


def mapa_pases_fallidos(df, equipo, titulo, ruta, T):
    """Flechas origen -> destino de cada pase fallido (¿dónde perdemos el balón?)."""
    f = df[(df.equipo == equipo) & (df.tipo == "Pass") & (df.pase_ok == False)]  # noqa: E712
    f = f.dropna(subset=["x", "y", "x_fin", "y_fin"])
    pitch, fig, ax = estilo.nueva_cancha(T)
    pitch.arrows(f.x, f.y, f.x_fin, f.y_fin, ax=ax, color=T["fallido"], alpha=0.75,
                 width=1.6, headwidth=4, headlength=4, zorder=2)
    pitch.scatter(f.x, f.y, s=20, ax=ax, color=T["texto"], alpha=0.8, zorder=3)
    estilo.titulo(fig, ax, f"{titulo} ({len(f)})", T)
    estilo.pie(fig, f"Cada flecha: dónde se perdió el balón y hacia dónde iba · {config.ATRIBUCION}", T)
    estilo.guardar(fig, ruta)
