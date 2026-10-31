"""
estilo.py — colores, tipografía y efectos de las infografías (los datos viven en graficos.py).

Misma identidad que el dashboard de Liga MX: Barlow Condensed en títulos, Barlow en texto,
azul #3987e5 / naranja #d95926 para los dos equipos (paleta validada para daltonismo) y fondos de cancha
de noche. Las fuentes están en fuentes/ (SIL Open Font License, ver fuentes/OFL.txt).

Contraste verificado contra cada fondo de cancha con la guía de visualización:
- oscuro (#0b1310) y rayados (#14301f / #183823): todos los colores >= 3:1.
- cesped (#184528): el naranja queda en 2.8:1; por eso los marcadores llevan borde claro y etiquetas.
"""

import logging
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")  # sin ventana: solo se guardan PNG

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from mplsoccer import Pitch  # noqa: E402

# DejaVu no tiene seminegrita y matplotlib lo avisa en cada texto; el respaldo usa negrita sin problema.
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

CARPETA_FUENTES = Path(__file__).parent / "fuentes"
for _archivo in CARPETA_FUENTES.glob("*.ttf"):
    font_manager.fontManager.addfont(str(_archivo))

# DejaVu Sans (incluida en matplotlib) cubre símbolos que Barlow no trae, como ★.
FUENTE_TEXTO = ["Barlow", "DejaVu Sans"]
FUENTE_TITULO = ["Barlow Condensed", "DejaVu Sans"]

_BASE = {
    "tiro_a": "#3987e5",    # equipo 1 (local en StatsBomb)
    "tiro_b": "#d95926",    # equipo 2
    "ok": "#3987e5",        # pases completados
    "fallido": "#e66767",   # pases fallidos
    "texto": "#f0efec",
    "texto_secundario": "#c3c2b7",
}

TEMAS = {
    # Verde noche, como el modo oscuro del dashboard.
    "oscuro": {**_BASE, "fondo": "#0b1310", "cesped": "#0b1310", "franja": None, "lineas": "#3a5446"},
    # Cancha con franjas de corte de pasto.
    "rayados": {**_BASE, "fondo": "#0b1310", "cesped": "#14301f", "franja": "#183823", "lineas": "#8fa89a"},
    # Pasto verde clásico, más oscuro de lo habitual para que el azul y el naranja se distingan.
    "cesped": {**_BASE, "fondo": "#123a21", "cesped": "#184528", "franja": None, "lineas": "#d9e6dd"},
}


def nueva_cancha(T: dict):
    """Cancha StatsBomb (120 x 80) con márgenes para título y pie. Devuelve (pitch, fig, ax)."""
    plt.rcParams["font.family"] = FUENTE_TEXTO
    pitch = Pitch(
        pitch_type="statsbomb",
        pitch_color=T["cesped"],
        line_color=T["lineas"],
        stripe=T["franja"] is not None,
        stripe_color=T["franja"] or T["cesped"],
        linewidth=1.2,
        goal_type="box",
        pad_top=9,  # espacio arriba de la cancha para las etiquetas de cada equipo (y = -3)
    )
    fig, ax = pitch.draw(figsize=(12, 9))
    fig.set_facecolor(T["fondo"])
    # La cancha debajo del título (arriba) y encima del pie (abajo).
    ax.set_position([0.03, 0.07, 0.94, 0.80])
    return pitch, fig, ax


def titulo(fig, ax, texto: str, T: dict) -> None:
    """Título alineado a la izquierda, en Barlow Condensed (como el titular del dashboard)."""
    fig.text(0.04, 0.955, texto, ha="left", va="top", color=T["texto"],
             fontfamily=FUENTE_TITULO, fontweight="bold", fontsize=26)


def pie(fig, texto: str, T: dict) -> None:
    fig.text(0.04, 0.03, texto, ha="left", va="bottom", color=T["texto_secundario"],
             fontfamily=FUENTE_TEXTO, fontsize=10.5)


def guardar(fig, ruta) -> None:
    fig.savefig(ruta, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def nodos(pitch, ax, x, y, tamanos, color: str, T: dict) -> None:
    """Jugadores: círculos con borde claro para separarlos del pasto."""
    pitch.scatter(x, y, s=tamanos, ax=ax, color=color, edgecolors=T["texto"], linewidth=1.5, zorder=4)


def linea(pitch, ax, a, b, color: str, ancho: float, alpha: float, T: dict) -> None:
    """Conexión simple (sin sentido) entre dos jugadores."""
    pitch.lines(a.x, a.y, b.x, b.y, ax=ax, color=color, lw=ancho, alpha=alpha, zorder=2)


# Curvatura de las flechas: A->B y B->A quedan a lados opuestos y no se enciman.
CURVATURA = 0.18


def flecha_curva(ax, a, b, color: str, ancho: float, alpha: float, radio_a: float, radio_b: float) -> None:
    """Flecha curva de a hacia b; los radios (en puntos) evitan que la punta quede debajo del nodo."""
    ax.annotate(
        "", xy=(b.x, b.y), xytext=(a.x, a.y), zorder=3,
        arrowprops={
            "arrowstyle": "-|>", "color": color, "lw": ancho, "alpha": alpha,
            "connectionstyle": f"arc3,rad={CURVATURA}", "shrinkA": radio_a, "shrinkB": radio_b,
            "mutation_scale": 8 + ancho * 2,
        },
    )


def etiqueta_flecha(ax, a, b, texto: str, color: str, T: dict) -> None:
    """Número de pases en el punto medio de la curva (se calcula en pantalla, donde se dibuja el arco)."""
    p1 = ax.transData.transform((a.x, a.y))
    p2 = ax.transData.transform((b.x, b.y))
    dx, dy = p2 - p1
    # Punto medio de una curva cuadrática con el punto de control de arc3.
    medio = (p1 + p2) / 2 + 0.5 * CURVATURA * np.array([dy, -dx])
    x, y = ax.transData.inverted().transform(medio)
    ax.text(x, y, texto, ha="center", va="center", fontsize=8, fontweight="semibold", color=T["texto"],
            zorder=5, bbox={"boxstyle": "round,pad=0.2", "facecolor": T["cesped"], "edgecolor": color, "lw": 0.8})
