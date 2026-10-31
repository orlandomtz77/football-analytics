"""
Infografías de Liga MX con los datos de resultados del proyecto (football-data.co.uk + campeones de Wikipedia).
No hay eventos abiertos de Liga MX (tiros, pases): estas láminas usan solo marcadores. Ver data/README.md.

Uso:  python -m football_analytics.infografias.liga_mx [--torneo "Apertura 2025"] [--equipo Toluca]
                                                      [--clasico "Clásico Nacional" | todos | ninguno]
                                                      [--tema oscuro|rayados|cesped] [--out carpeta]

Cada lámina responde una pregunta:
- tabla:   ¿cómo quedó (o cómo va) el torneo?
- equipo:  ¿cómo le fue a mi equipo?
- clásico: ¿quién domina el clásico desde 2012?
"""

from __future__ import annotations

import argparse
import textwrap
import unicodedata
from pathlib import Path

import pandas as pd
from matplotlib.patches import Rectangle

from football_analytics.cleaning import ordenar_torneos
from football_analytics.datos import RUTA_PROCESADO, campeones_validos, cargar_liga_mx, estado_torneo
from football_analytics.formato import cantidad, record
from football_analytics.infografias import config, estilo
from football_analytics.infografias.estilo import COLOR_RESULTADO, COLOR_ZONA, TEMAS
from football_analytics.insights import COMO_SE_DEFINIO, titular_torneo
from football_analytics.metrics import calcular_evolucion_puntos, calcular_tabla_posiciones
from football_analytics.metrics import ultimos_resultados
from football_analytics.reglamento import zonas_del_torneo
from football_analytics.vistas import CLASICOS, enfrentamientos, ficha_equipo, resumen_enfrentamientos, tabla_aficionado

FUENTE = "Datos: football-data.co.uk (resultados de Liga MX)"
FUENTE_CAMPEONES = "Campeones: Wikipedia"
TEXTO_RESULTADO = {"G": "ganó", "E": "empató", "P": "perdió"}


def nombre_archivo(*partes: str) -> str:
    """'tabla', 'Apertura 2025' -> 'tabla_apertura_2025.png' (sin acentos ni espacios)."""
    texto = "_".join(partes).lower().replace(" ", "_").replace(".", "")
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return f"{sin_acentos}.png"


def _regular(partidos: pd.DataFrame, torneo: str) -> pd.DataFrame:
    regular = partidos[(partidos["torneo"] == torneo) & (partidos["fase"] == "regular")]
    if regular.empty:
        raise ValueError(f"No hay partidos de fase regular de {torneo} en los datos.")
    return regular


def nota_de_estado(partidos: pd.DataFrame, torneo: str) -> str:
    """Aclaración si el torneo no terminó (en juego o cancelado); cadena vacía si terminó."""
    estado = estado_torneo(partidos, torneo)
    regular = _regular(partidos, torneo)
    if estado == "en_curso":
        jugados = cantidad(len(regular), "partido jugado", "partidos jugados")
        return f"Torneo en juego: {jugados} hasta el {regular['fecha'].max():%d/%m/%Y}."
    if estado == "cancelado":
        jugados = cantidad(len(regular), "partido jugado", "partidos jugados")
        return f"Torneo cancelado antes de terminar la fase regular ({jugados})."
    return ""


def _leyenda_resultados(ax, x: float, y: float, T: dict) -> None:
    for letra in "GEP":
        estilo.cuadro_resultado(ax, x, y, letra, 0.026, T)
        ax.text(x + 0.034, y, TEXTO_RESULTADO[letra], ha="left", va="center", color=T["texto_secundario"], fontsize=8.5)
        x += 0.115


# ------------------------------------------------------------------ TABLA
def infografia_tabla(partidos, torneo, ruta, T, campeones=None):
    """Tabla del torneo con zonas de clasificación, campeón/subcampeón y los últimos 5 resultados."""
    regular = _regular(partidos, torneo)
    estado = estado_torneo(partidos, torneo)
    campeon = campeones.loc[torneo] if campeones is not None and torneo in campeones.index else None
    titular, bajada = titular_torneo(regular, torneo, estado, campeon=campeon)
    tabla = tabla_aficionado(regular, torneo, campeones=campeones)
    ultimos = ultimos_resultados(calcular_evolucion_puntos(regular))

    fig, ax = estilo.nueva_lamina(T)
    nota = nota_de_estado(partidos, torneo)  # en la bajada: abajo no hay espacio junto a la leyenda
    estilo.encabezado(ax, titular, textwrap.fill(f"{bajada} {nota}".strip(), 78), T)

    arriba, abajo = 0.80, 0.115
    alto_fila = (arriba - abajo) / (len(tabla) + 1)
    columnas = {"JJ": 0.585, "DIF": 0.655, "PTS": 0.73}
    y = arriba - alto_fila / 2
    for nombre, x in columnas.items():
        ax.text(x, y, nombre, ha="center", va="center", color=T["texto_secundario"], fontsize=8.5)
    ax.text(0.785, y, "Últimos 5", ha="left", va="center", color=T["texto_secundario"], fontsize=8.5)

    for i, fila in tabla.iterrows():
        y = arriba - alto_fila * (i + 1.5)
        zona = fila.get("Zona", "")
        if zona in COLOR_ZONA:
            ax.add_patch(Rectangle((0.05, y - alto_fila * 0.46), 0.90, alto_fila * 0.92,
                                   facecolor=COLOR_ZONA[zona], edgecolor="none"))
        ax.text(0.095, y, str(fila["Pos"]), ha="right", va="center", color=T["texto_secundario"], fontsize=9.5)
        ax.text(0.12, y, fila["Equipo"], ha="left", va="center", color=T["texto"], fontsize=10.5,
                fontweight="semibold")
        final = fila.get("Final", "")
        if final:
            ax.text(0.43, y, "★ Campeón" if "Campeón" in final else "Subcampeón", ha="left", va="center",
                    color=T["tiro_a"], fontsize=9, fontweight="semibold")
        ax.text(columnas["JJ"], y, str(fila["JJ"]), ha="center", va="center", color=T["texto_secundario"], fontsize=9.5)
        ax.text(columnas["DIF"], y, f"{fila['DIF']:+d}" if fila["DIF"] else "0", ha="center", va="center",
                color=T["texto_secundario"], fontsize=9.5)
        ax.text(columnas["PTS"], y, str(fila["PTS"]), ha="center", va="center", color=T["texto"], fontsize=11,
                fontweight="bold")
        for j, resultado in enumerate(ultimos.get(fila["Equipo"], [])):
            estilo.cuadro_resultado(ax, 0.785 + j * 0.033, y, resultado, 0.027, T)

    # Leyenda: zonas y resultados.
    x = 0.06
    for nombre, desde, hasta in zonas_del_torneo(torneo) or []:
        ax.add_patch(Rectangle((x, 0.083), 0.02, 0.016, facecolor=COLOR_ZONA[nombre], edgecolor="none"))
        etiqueta = f"{nombre} ({desde}.º-{hasta}.º)"
        ax.text(x + 0.028, 0.091, etiqueta, ha="left", va="center", color=T["texto_secundario"], fontsize=8.5)
        x += 0.05 + 0.0105 * len(etiqueta)
    _leyenda_resultados(ax, 0.62, 0.091, T)

    fuentes = FUENTE + (f" · {FUENTE_CAMPEONES}" if campeon is not None else "")
    estilo.pie_lamina(ax, "Fase regular. Empates en puntos ordenados por diferencia y goles a favor "
                          f"(desempate provisional).\n{fuentes}", T)
    estilo.guardar_lamina(fig, ruta)


# ----------------------------------------------------------------- EQUIPO
def _barra_porcentaje(ax, y: float, etiqueta: str, puntos: int, posibles: int, T: dict) -> None:
    ax.text(0.06, y + 0.022, etiqueta, ha="left", va="bottom", color=T["texto"], fontsize=10.5, fontweight="semibold")
    ax.text(0.94, y + 0.022, f"{puntos} de {posibles} puntos", ha="right", va="bottom",
            color=T["texto_secundario"], fontsize=9.5)
    ax.add_patch(Rectangle((0.06, y), 0.88, 0.014, facecolor=T["panel"], edgecolor="none"))
    if posibles:
        ax.add_patch(Rectangle((0.06, y), 0.88 * puntos / posibles, 0.014, facecolor=T["tiro_a"], edgecolor="none"))


def infografia_equipo(partidos, torneo, equipo, ruta, T, campeones=None):
    """Ficha de un equipo en un torneo: posición, récord, casa/visita, puntos acumulados y sus resultados."""
    regular = _regular(partidos, torneo)
    ficha = ficha_equipo(regular, equipo)
    evolucion = calcular_evolucion_puntos(regular)

    subtitulo = f"{torneo}: {ficha['posicion']}.º de {ficha['equipos']} en la fase regular"
    if campeones is not None and torneo in campeones.index:
        if campeones.at[torneo, "campeon"] == equipo:
            subtitulo += f". Campeón: ganó la final {COMO_SE_DEFINIO[campeones.at[torneo, 'definicion']]}"
        elif campeones.at[torneo, "subcampeon"] == equipo:
            subtitulo += ". Subcampeón"
    nota = nota_de_estado(partidos, torneo)
    fig, ax = estilo.nueva_lamina(T)
    estilo.encabezado(ax, equipo, subtitulo + ".", T)

    # Cifras principales.
    diferencia = ficha["puntos_del_lider"] - ficha["puntos"]
    cifras = [("Posición", f"{ficha['posicion']}.º"), ("Puntos", str(ficha["puntos"])),
              ("Récord", ficha["record"]), ("Del líder", "Líder" if ficha["posicion"] == 1 else f"-{diferencia}")]
    for k, (etiqueta, valor) in enumerate(cifras):
        x = 0.06 + k * 0.225
        ax.text(x, 0.835, etiqueta, ha="left", va="bottom", color=T["texto_secundario"], fontsize=9.5)
        ax.text(x, 0.83, valor, ha="left", va="top", color=T["texto"], fontfamily=estilo.FUENTE_TITULO,
                fontweight="bold", fontsize=24)

    # En casa y de visita, como porcentaje de puntos posibles.
    for k, (condicion, nombre) in enumerate([("local", "En casa"), ("visitante", "De visita")]):
        t = calcular_tabla_posiciones(regular, condicion=condicion).set_index("equipo")
        if equipo in t.index:
            f = t.loc[equipo]
            _barra_porcentaje(ax, 0.70 - k * 0.07, f"{nombre}: {record(f['PG'], f['PE'], f['PP'])}",
                              int(f["Pts"]), int(f["PJ"]) * 3, T)

    # Puntos acumulados contra el líder (o el segundo, si el equipo es líder).
    tabla = calcular_tabla_posiciones(regular)
    referencia = tabla["equipo"].iloc[0] if ficha["posicion"] != 1 else (
        tabla["equipo"].iloc[1] if len(tabla) > 1 else None)
    grafica = fig.add_axes((0.09, 0.25, 0.70, 0.29))
    grafica.set_facecolor(T["fondo"])
    series = [(n, c) for n, c in [(referencia, T["tiro_b"]), (equipo, T["tiro_a"])] if n is not None]
    finales = {n: evolucion[evolucion["equipo"] == n]["Pts_acumulados"].iloc[-1] for n, _ in series}
    # Si los dos terminan a menos de 3 puntos, las etiquetas se separan: arriba el que tiene más puntos.
    separar = len(finales) == 2 and abs(finales[equipo] - finales[referencia]) < 3
    for nombre, color in series:
        datos = evolucion[evolucion["equipo"] == nombre]
        grafica.plot(datos["partido_n"], datos["Pts_acumulados"], color=color, lw=2.2, marker="o", ms=4)
        ultimo = datos.iloc[-1]
        otro = referencia if nombre == equipo else equipo
        dy = (7 if finales[nombre] >= finales[otro] else -7) if separar else 0
        if separar and finales[nombre] == finales[otro]:
            dy = 7 if nombre == equipo else -7  # empatados: el equipo de la ficha arriba
        grafica.annotate(f"{nombre} {ultimo['Pts_acumulados']}", (ultimo["partido_n"], ultimo["Pts_acumulados"]),
                         xytext=(8, dy), textcoords="offset points", va="center", color=color, fontsize=9,
                         fontweight="semibold", annotation_clip=False)
    grafica.set_title("Puntos acumulados, partido a partido", loc="left", color=T["texto"], fontsize=10.5,
                      fontweight="semibold", pad=8)
    grafica.tick_params(colors=T["texto_secundario"], labelsize=8.5, length=0)
    grafica.grid(axis="y", color=T["lineas"], lw=0.6, alpha=0.6)
    for lado in grafica.spines.values():
        lado.set_visible(False)
    grafica.set_ylim(bottom=0)

    # Resultados en orden de fecha.
    resultados = evolucion[evolucion["equipo"] == equipo]
    ax.text(0.06, 0.195, "Sus partidos, en orden de fecha", ha="left", va="center", color=T["texto"],
            fontsize=10.5, fontweight="semibold")
    lado = min(0.045, 0.88 / max(len(resultados), 1) - 0.006)
    for k, (_, r) in enumerate(resultados.iterrows()):
        estilo.cuadro_resultado(ax, 0.06 + k * (lado + 0.006), 0.15, r["resultado"], lado, T)
    rachas = (f"Mejor racha: {cantidad(ficha['racha_victorias'], 'victoria seguida', 'victorias seguidas')} y "
              f"{cantidad(ficha['racha_sin_perder'], 'partido', 'partidos')} sin perder.")
    ax.text(0.06, 0.11, rachas, ha="left", va="center", color=T["texto_secundario"], fontsize=9.5)
    _leyenda_resultados(ax, 0.62, 0.195, T)

    estilo.pie_lamina(ax, (f"{nota}\n" if nota else "") + "Fase regular; el eje de la gráfica es el partido n.º del "
                          f"equipo (la fuente no indica la jornada).\n{FUENTE}", T)
    estilo.guardar_lamina(fig, ruta)


# ---------------------------------------------------------------- CLÁSICO
def _abreviar_torneo(torneo: str) -> str:
    nombre, anio = torneo.split()
    return f"{nombre[:3]}. {anio}"


def infografia_clasico(partidos, nombre, equipo_a, equipo_b, ruta, T):
    """Historial de un clásico: victorias, empates, goles, últimos 5 y victorias más amplias."""
    cara = enfrentamientos(partidos, equipo_a, equipo_b)
    resumen = resumen_enfrentamientos(cara)
    if resumen["partidos"] == 0:
        raise ValueError(f"{equipo_a} y {equipo_b} no se enfrentaron en los datos.")
    v, e, d = resumen["victorias"], resumen["empates"], resumen["derrotas"]

    fig, ax = estilo.nueva_lamina(T)
    desde = ordenar_torneos(partidos["torneo"])[-1]
    estilo.encabezado(ax, nombre, f"{equipo_a} vs. {equipo_b}\n"
                                  f"{cantidad(resumen['partidos'], 'partido', 'partidos')} de Liga MX desde el {desde} "
                                  "(fase regular y liguilla)", T)

    # Victorias y empates: cifras grandes y una barra proporcional.
    bloques = [(f"Ganó {equipo_a}", v, T["tiro_a"]), ("Empates", e, T["texto_secundario"]),
               (f"Ganó {equipo_b}", d, T["tiro_b"])]
    for k, (etiqueta, valor, color) in enumerate(bloques):
        x = [0.06, 0.5, 0.94][k]
        alineacion = ["left", "center", "right"][k]
        ax.text(x, 0.77, str(valor), ha=alineacion, va="top", color=color, fontfamily=estilo.FUENTE_TITULO,
                fontweight="bold", fontsize=54)
        ax.text(x, 0.785, etiqueta, ha=alineacion, va="bottom", color=T["texto_secundario"], fontsize=9.5)
    x = 0.06
    for _, valor, color in bloques:
        ancho = 0.88 * valor / resumen["partidos"]
        if ancho:
            ax.add_patch(Rectangle((x, 0.645), ancho - 0.004, 0.022, facecolor=color, edgecolor="none"))
        x += ancho

    # Goles.
    ax.text(0.06, 0.585, "Goles", ha="left", va="center", color=T["texto"], fontsize=10.5, fontweight="semibold")
    ax.text(0.06, 0.545, f"{equipo_a} {resumen['goles_a_favor']}", ha="left", va="center", color=T["tiro_a"],
            fontsize=15, fontweight="semibold")
    ax.text(0.94, 0.545, f"{resumen['goles_en_contra']} {equipo_b}", ha="right", va="center", color=T["tiro_b"],
            fontsize=15, fontweight="semibold")

    # Últimos 5 (del más antiguo al más reciente), desde la perspectiva del equipo A.
    ax.text(0.06, 0.465, f"Últimos {min(5, len(cara))} partidos (resultado de {equipo_a})", ha="left", va="center",
            color=T["texto"], fontsize=10.5, fontweight="semibold")
    for k, (_, p) in enumerate(cara.iloc[:5].iloc[::-1].iterrows()):
        x = 0.06 + k * 0.178
        estilo.cuadro_resultado(ax, x, 0.405, p["resultado"], 0.16, T,
                                texto=f"{p['goles_equipo']}-{p['goles_rival']}", alto=0.055)
        ax.text(x + 0.08, 0.365, f"{_abreviar_torneo(p['Torneo'])}\n{p['Fecha']:%d/%m/%Y}", ha="center", va="top",
                color=T["texto_secundario"], fontsize=8.5, linespacing=1.3)

    # Victorias más amplias.
    ax.text(0.06, 0.235, "Victoria más amplia", ha="left", va="center", color=T["texto"], fontsize=10.5,
            fontweight="semibold")
    y = 0.195
    for clave, quien, color in [("mayor_victoria", equipo_a, T["tiro_a"]), ("mayor_derrota", equipo_b, T["tiro_b"])]:
        p = resumen[clave]
        texto = (f"{p['Local']} {p['Marcador']} {p['Visitante']} ({p['Torneo']})" if p is not None
                 else "Sin victorias en estos datos")
        ax.text(0.06, y, f"{quien}:", ha="left", va="center", color=color, fontsize=10, fontweight="semibold")
        ax.text(0.06, y - 0.03, texto, ha="left", va="center", color=T["texto_secundario"], fontsize=10)
        y -= 0.075

    estilo.pie_lamina(ax, "Cada partido cuenta por su marcador; en liguilla, la serie pudo definirse por global o "
                          f"penales.\nSolo Liga MX (sin Copa MX, Concacaf ni amistosos). {FUENTE}", T)
    estilo.guardar_lamina(fig, ruta)


# -------------------------------------------------------------------- CLI
def main(argv: list[str] | None = None) -> list[Path]:
    ap = argparse.ArgumentParser(description="Infografías de Liga MX con los resultados del proyecto.")
    ap.add_argument("--datos", default=str(RUTA_PROCESADO), help="CSV procesado (ver README)")
    ap.add_argument("--torneo", default=None, help='p. ej. "Apertura 2025" (por defecto, el más reciente)')
    ap.add_argument("--equipo", default=None, help="nombre como en la fuente (por defecto, campeón o líder)")
    ap.add_argument("--clasico", default="Clásico Nacional", choices=[*CLASICOS, "todos", "ninguno"])
    ap.add_argument("--tema", default=config.TEMA_POR_DEFECTO, choices=TEMAS)
    ap.add_argument("--out", default=str(Path(config.CARPETA_SALIDA) / "liga_mx"))
    args = ap.parse_args(argv)

    partidos, _ = cargar_liga_mx(args.datos)
    campeones = campeones_validos(partidos)
    T = TEMAS[args.tema]
    salida = Path(args.out)
    salida.mkdir(parents=True, exist_ok=True)

    torneo = args.torneo or ordenar_torneos(partidos["torneo"])[0]
    if args.equipo:
        equipo = args.equipo
    elif campeones is not None and torneo in campeones.index:
        equipo = campeones.at[torneo, "campeon"]
    else:
        equipo = calcular_tabla_posiciones(_regular(partidos, torneo))["equipo"].iloc[0]

    generadas = [salida / nombre_archivo("tabla", torneo), salida / nombre_archivo("equipo", equipo, torneo)]
    infografia_tabla(partidos, torneo, generadas[0], T, campeones=campeones)
    infografia_equipo(partidos, torneo, equipo, generadas[1], T, campeones=campeones)
    if args.clasico == "todos":
        clasicos = CLASICOS
    elif args.clasico == "ninguno":
        clasicos = {}
    else:
        clasicos = {args.clasico: CLASICOS[args.clasico]}
    for nombre, (a, b) in clasicos.items():
        ruta = salida / nombre_archivo(nombre)
        infografia_clasico(partidos, nombre, a, b, ruta, T)
        generadas.append(ruta)
    print("Listo:", *[p.name for p in generadas], sep="\n  ")
    return generadas


if __name__ == "__main__":
    main()
