"""
Generador de infografías de partido.
Uso:  python -m football_analytics.infografias <match_id> [--tema oscuro|rayados|cesped] [--out carpeta]
Ej.:  python -m football_analytics.infografias 3869685 --tema rayados     # final Mundial 2022 (StatsBomb)

Antes: $env:PYTHONPATH = "src" (PowerShell) y pip install -r requirements-infografias.txt
"""
import argparse
from pathlib import Path

from football_analytics.infografias import config, graficos
from football_analytics.infografias.estilo import TEMAS
from football_analytics.infografias.statsbomb import cargar_apodos, cargar_partido, marcador


def main():
    ap = argparse.ArgumentParser(description="Infografías de un partido de StatsBomb Open Data.")
    ap.add_argument("match_id", type=int, help="id del partido en StatsBomb (ver data/matches/<comp>/<temporada>.json)")
    ap.add_argument("--tema", default=config.TEMA_POR_DEFECTO, choices=TEMAS)
    ap.add_argument("--out", default=config.CARPETA_SALIDA)
    ap.add_argument("--min-ok", type=int, default=None,
                    help="mínimo de pases completados por conexión (anula config.py)")
    ap.add_argument("--min-fallidos", type=int, default=None,
                    help="mínimo de pases fallidos por conexión (anula config.py)")
    ap.add_argument("--lineas", action="store_true", help="redes con líneas simples en vez de flechas")
    ap.add_argument("--todo-el-partido", action="store_true",
                    help="redes con todo el partido, no solo hasta el primer cambio (anula config.py)")
    args = ap.parse_args()

    T = TEMAS[args.tema]
    # `is not None`: un 0 explícito también anula config.py.
    if args.min_ok is not None:
        min_ok = args.min_ok
    else:
        min_ok = config.MINIMO_PASES_COMPLETADOS_LINEAS if args.lineas else config.MINIMO_PASES_COMPLETADOS
    min_fallidos = args.min_fallidos if args.min_fallidos is not None else config.MINIMO_PASES_FALLIDOS
    cortar = config.CORTAR_EN_PRIMER_CAMBIO and not args.todo_el_partido
    salida = Path(args.out)
    salida.mkdir(parents=True, exist_ok=True)

    df = cargar_partido(args.match_id)
    cortos = cargar_apodos(args.match_id)
    for col in ("jugador", "receptor"):
        df[col] = df[col].map(cortos).fillna(df[col])

    equipos = list(dict.fromkeys(df.equipo))[:2]
    graficos.mapa_de_tiros(df, equipos, marcador(df, equipos), salida / "1_tiros.png", T)
    for i, eq in enumerate(equipos):
        n = 2 + 3 * i  # 2-4 para el primer equipo, 5-7 para el segundo
        graficos.red_de_pases(df, eq, f"Red de pases completados · {eq}",
                              salida / f"{n}_red_ok_{eq}.png", T, minimo=min_ok,
                              direccional=not args.lineas, cortar_en_primer_cambio=cortar)
        graficos.red_de_pases(df, eq, f"Red de pases fallidos · {eq}",
                              salida / f"{n + 1}_red_fallidos_{eq}.png", T, completados=False,
                              minimo=min_fallidos, direccional=not args.lineas, cortar_en_primer_cambio=cortar)
        graficos.mapa_pases_fallidos(df, eq, f"Pases fallidos · {eq}",
                                     salida / f"{n + 2}_flechas_fallidos_{eq}.png", T)
    print("Listo:", *sorted(p.name for p in salida.iterdir()), sep="\n  ")


if __name__ == "__main__":
    main()
