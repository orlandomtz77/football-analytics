"""Gráficos con Plotly. Cada función recibe una tabla ya calculada en metrics.py."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

# Paleta validada (CVD y contraste) en modo claro con la guía de visualización.
COLOR_LOCAL = "#2a78d6"
COLOR_VISITANTE = "#eb6834"
COLOR_CONECTOR = "#c3c2b7"
COLOR_TEXTO = "#0b0b0b"
COLOR_TEXTO_SECUNDARIO = "#52514e"
COLOR_REJILLA = "#e6e5e0"


def grafico_local_visitante(rendimiento: pd.DataFrame, titulo: str, nota: str | None = None) -> go.Figure:
    """Gráfico de pesas (dumbbell): PPP como local vs. como visitante por equipo.

    Responde: ¿qué equipos dependen más de jugar en casa?
    `rendimiento` es la salida de `calcular_rendimiento_local_visitante`.
    Los equipos se ordenan por `dif_PPP`, el de mayor diferencia arriba.
    `nota` se muestra al pie (p. ej. fuente y fecha de los datos).
    """
    datos = rendimiento.dropna(subset=["PPP_local", "PPP_visitante"])
    # Plotly dibuja la primera categoría abajo; invertimos para que la mayor diferencia quede arriba.
    datos = datos.sort_values("dif_PPP", ascending=True)
    equipos = datos["equipo"].tolist()

    fig = go.Figure()

    # Conector gris entre los dos puntos de cada equipo (None separa los segmentos).
    xs, ys = [], []
    for _, fila in datos.iterrows():
        xs += [fila["PPP_local"], fila["PPP_visitante"], None]
        ys += [fila["equipo"], fila["equipo"], None]
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines", line={"color": COLOR_CONECTOR, "width": 2},
        hoverinfo="skip", showlegend=False,
    ))

    for condicion, color, simbolo in [
        ("local", COLOR_LOCAL, "circle"),
        ("visitante", COLOR_VISITANTE, "diamond"),
    ]:
        fig.add_trace(go.Scatter(
            x=datos[f"PPP_{condicion}"],
            y=equipos,
            mode="markers",
            name=condicion.capitalize(),
            # Forma distinta además del color, para no depender solo del color.
            marker={"color": color, "size": 11, "symbol": simbolo,
                    "line": {"color": "#fcfcfb", "width": 2}},
            customdata=datos[[f"PJ_{condicion}", f"Pts_{condicion}", f"GF_{condicion}",
                              f"GC_{condicion}", "dif_PPP"]].to_numpy(),
            hovertemplate=(
                "<b>%{y}</b> — " + condicion + "<br>"
                "PPP: %{x:.2f}<br>"
                "PJ: %{customdata[0]} · Pts: %{customdata[1]}<br>"
                "GF: %{customdata[2]} · GC: %{customdata[3]}<br>"
                "Diferencia local − visitante: %{customdata[4]:+.2f}"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        title={"text": titulo, "font": {"color": COLOR_TEXTO, "size": 16}, "x": 0, "xanchor": "left"},
        xaxis={
            "title": "Puntos por partido (PPP)",
            "range": [-0.1, 3.1],
            "dtick": 0.5,
            "gridcolor": COLOR_REJILLA,
            "zeroline": False,
        },
        yaxis={"title": None, "gridcolor": COLOR_REJILLA, "automargin": True},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.0, "xanchor": "left", "x": 0},
        font={"color": COLOR_TEXTO_SECUNDARIO},
        plot_bgcolor="#fcfcfb",
        paper_bgcolor="#fcfcfb",
        height=max(400, 28 * len(equipos) + 140),
        margin={"l": 7 * max((len(e) for e in equipos), default=0) + 20, "r": 20, "t": 90, "b": 90 if nota else 50},
        hoverlabel={"bgcolor": "#fcfcfb", "font": {"color": COLOR_TEXTO}},
    )
    if nota:
        fig.add_annotation(
            text=nota, showarrow=False, xref="paper", yref="paper", x=0, y=0, yshift=-60,
            xanchor="left", yanchor="top", font={"size": 11, "color": COLOR_TEXTO_SECUNDARIO},
        )
    return fig
