"""Pruebas de las infografías de partido (StatsBomb).

DATOS DE PRUEBA: eventos, jugadores y equipos ficticios con la forma del JSON de StatsBomb.
"""

import json

import pandas as pd
import pytest

pytest.importorskip("mplsoccer")  # dependencia opcional: requirements-infografias.txt

from football_analytics.infografias import graficos  # noqa: E402
from football_analytics.infografias.estilo import TEMAS  # noqa: E402
from football_analytics.infografias.statsbomb import (  # noqa: E402
    apodos,
    cargar_partido,
    eventos_a_dataframe,
    marcador,
)


def _evento(tipo, equipo, jugador=None, minuto=10, periodo=1, loc=(60, 40), **extra):
    e = {"type": {"name": tipo}, "team": {"name": equipo}, "minute": minuto, "period": periodo,
         "location": list(loc)}
    if jugador:
        e["player"] = {"name": jugador}
    e.update(extra)
    return e


def _pase(equipo, de, a, ok=True, minuto=10, periodo=1, loc=(50, 40), fin=(60, 30)):
    p = {"recipient": {"name": a}, "end_location": list(fin)}
    if not ok:
        p["outcome"] = {"name": "Incomplete"}
    return _evento("Pass", equipo, de, minuto, periodo, loc, **{"pass": p})


def _tiro(equipo, jugador, xg, resultado, minuto=20, periodo=1, loc=(108, 40)):
    return _evento("Shot", equipo, jugador, minuto, periodo, loc,
                   shot={"statsbomb_xg": xg, "outcome": {"name": resultado}})


EVENTOS = [
    _pase("Azules", "Ana Pérez López", "Bea", minuto=1),
    _pase("Azules", "Ana Pérez López", "Bea", minuto=2),
    _pase("Azules", "Bea", "Ana Pérez López", minuto=3),
    _pase("Azules", "Ana Pérez López", "Bea", ok=False, minuto=4),
    _tiro("Azules", "Bea", 0.4, "Goal"),
    _tiro("Rojos", "Cris", 0.1, "Saved", minuto=30),
    _evento("Own Goal Against", "Rojos", "Cris", minuto=40),
    _evento("Own Goal For", "Azules", minuto=40),
    _evento("Substitution", "Azules", "Bea", minuto=60, periodo=2),
    _pase("Azules", "Ana Pérez López", "Bea", minuto=70, periodo=2),
    _tiro("Rojos", "Cris", 0.8, "Goal", minuto=121, periodo=5),  # tanda de penales: se descarta
]


def test_eventos_a_dataframe():
    df = eventos_a_dataframe(EVENTOS)
    assert len(df) == len(EVENTOS) - 1  # sin la tanda de penales
    assert (df.periodo <= 4).all()
    tiro = df[(df.tipo == "Shot") & (df.equipo == "Azules")].iloc[0]
    assert (tiro.xg, tiro.resultado) == (0.4, "Goal")
    pases = df[df.tipo == "Pass"]
    assert pases.pase_ok.tolist() == [True, True, True, False, True]
    assert pases.iloc[0][["x_fin", "y_fin"]].tolist() == [60, 30]


def test_eventos_a_dataframe_sin_tiros_ni_pases_conserva_columnas():
    df = eventos_a_dataframe([_evento("Pressure", "Azules", "Ana")])
    assert {"xg", "resultado", "pase_ok", "receptor"} <= set(df.columns)


def test_apodos_usa_apodo_o_apellido():
    lineups = [{"lineup": [
        {"player_name": "Lionel Andrés Messi Cuccittini", "player_nickname": "Lionel Messi"},
        {"player_name": "Ana Pérez López", "player_nickname": None},
    ]}]
    assert apodos(lineups) == {"Lionel Andrés Messi Cuccittini": "Lionel Messi", "Ana Pérez López": "López"}


def test_marcador_cuenta_autogoles_y_no_la_tanda():
    df = eventos_a_dataframe(EVENTOS)
    # Azules: gol de Bea + autogol de Cris a su favor. Rojos: su gol fue en la tanda (periodo 5).
    assert marcador(df, ["Azules", "Rojos"]) == "Azules 2 - 0 Rojos"


def test_conexiones_de_pases_hasta_el_primer_cambio():
    df = eventos_a_dataframe(EVENTOS)
    pos, pares = graficos.conexiones_de_pases(df, "Azules", completados=True, minimo=2)
    # Antes del cambio (min 60, 2.º tiempo): Ana->Bea 2 completados; Bea->Ana 1 (no llega al mínimo).
    assert pares.to_dict("records") == [{"jugador": "Ana Pérez López", "receptor": "Bea", "n": 2}]
    # Las posiciones usan todos los pases (incluido el fallido): Ana intentó 3, Bea 1.
    assert pos.loc["Ana Pérez López", "n"] == 3 and pos.loc["Bea", "n"] == 1

    _, pares_todo = graficos.conexiones_de_pases(df, "Azules", minimo=2, cortar_en_primer_cambio=False)
    assert pares_todo.n.tolist() == [3]  # el pase del minuto 70 ya cuenta


def test_conexiones_de_pases_fallidos():
    df = eventos_a_dataframe(EVENTOS)
    _, pares = graficos.conexiones_de_pases(df, "Azules", completados=False, minimo=1)
    assert pares.to_dict("records") == [{"jugador": "Ana Pérez López", "receptor": "Bea", "n": 1}]


@pytest.mark.parametrize("tema", sorted(TEMAS))
def test_graficos_generan_png(tmp_path, tema):
    df = eventos_a_dataframe(EVENTOS)
    T = TEMAS[tema]
    graficos.mapa_de_tiros(df, ["Azules", "Rojos"], "Azules 2 - 0 Rojos", tmp_path / "tiros.png", T)
    graficos.red_de_pases(df, "Azules", "Red", tmp_path / "red.png", T, minimo=1)
    graficos.red_de_pases(df, "Azules", "Red", tmp_path / "red_lineas.png", T, minimo=1, direccional=False)
    graficos.mapa_pases_fallidos(df, "Azules", "Fallidos", tmp_path / "fallidos.png", T)
    for nombre in ["tiros.png", "red.png", "red_lineas.png", "fallidos.png"]:
        assert (tmp_path / nombre).stat().st_size > 10_000


def test_cargar_partido_descarga_una_sola_vez(tmp_path):
    llamadas = []

    def descargar_falso(url, destino):
        llamadas.append(url)
        destino.write_text(json.dumps(EVENTOS), encoding="utf-8")

    df1 = cargar_partido(123, tmp_path, descargar=descargar_falso)
    df2 = cargar_partido(123, tmp_path, descargar=descargar_falso)
    assert len(llamadas) == 1 and llamadas[0].endswith("/events/123.json")
    assert (tmp_path / "events" / "123.json").exists()
    pd.testing.assert_frame_equal(df1, df2)


def test_cargar_partido_no_deja_archivos_a_medias(tmp_path):
    def descargar_roto(url, destino):
        destino.write_text("{no es json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        cargar_partido(123, tmp_path, descargar=descargar_roto)
    assert not list((tmp_path / "events").iterdir())
