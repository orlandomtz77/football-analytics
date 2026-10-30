"""Pruebas de la vista de partidos por semana de juego.

DATOS DE PRUEBA: equipos, fechas y marcadores ficticios.
"""

import pandas as pd

from football_analytics.vistas import etiqueta_fechas, semanas_de_juego, tabla_partidos


def _partidos() -> pd.DataFrame:
    # Semana 1: jueves 23 y viernes 24 de octubre (días seguidos).
    # Semana 2: viernes 31 de octubre y sábado 1 de noviembre.
    # Semana 3: martes 4 y miércoles 5 de noviembre (media semana).
    # Semana 4: jueves 6 y viernes 7: el jueves sigue a la media semana; el viernes empieza otra semana.
    # Semana 5: miércoles 19 de noviembre (partido suelto).
    fechas = ["2025-10-23 21:00", "2025-10-24 19:00", "2025-10-31 19:00", "2025-11-01 12:00",
              "2025-11-04 19:00", "2025-11-05 21:00", "2025-11-07 19:00", "2025-11-19 20:00"]
    return pd.DataFrame({
        "fecha": pd.to_datetime(fechas),
        "hora": [f[-5:] for f in fechas],
        "fase": ["regular"] * 7 + ["final"],
        "equipo_local": ["A", "C", "B", "D", "A", "B", "C", "A"],
        "equipo_visitante": ["B", "D", "A", "C", "D", "C", "A", "C"],
        "goles_local": [1, 0, 2, 3, 0, 1, 2, 1],
        "goles_visitante": [0, 0, 2, 1, 0, 1, 0, 2],
    })


def test_semanas_de_juego():
    semanas = semanas_de_juego(_partidos())
    assert semanas["etiqueta"].tolist() == [
        "19 de noviembre (1 partido)",
        "7 de noviembre (1 partido)",
        "Del 4 al 5 de noviembre (2 partidos)",
        "Del 31 de octubre al 1 de noviembre (2 partidos)",
        "Del 23 al 24 de octubre (2 partidos)",
    ]  # la más reciente primero
    assert semanas["partidos"].tolist() == [[7], [6], [4, 5], [2, 3], [0, 1]]


def test_semanas_de_juego_separa_dias_no_seguidos():
    partidos = _partidos()
    partidos.loc[1, "fecha"] = pd.Timestamp("2025-10-25 19:00")  # jueves 23 y sábado 25: sin viernes
    assert semanas_de_juego(partidos)["etiqueta"].tolist()[-2:] == ["25 de octubre (1 partido)", "23 de octubre (1 partido)"]


def test_semanas_de_juego_jueves_tras_media_semana():
    partidos = _partidos()
    partidos.loc[6, "fecha"] = pd.Timestamp("2025-11-06 19:00")  # martes, miércoles y jueves: misma semana
    semanas = semanas_de_juego(partidos)
    assert "Del 4 al 6 de noviembre (3 partidos)" in semanas["etiqueta"].tolist()


def test_semanas_de_juego_vacio():
    assert semanas_de_juego(_partidos().iloc[0:0]).empty


def test_etiqueta_fechas():
    assert etiqueta_fechas(pd.Timestamp("2025-10-24"), pd.Timestamp("2025-10-26")) == "24 al 26 de octubre"
    assert etiqueta_fechas(pd.Timestamp("2025-10-31"), pd.Timestamp("2025-11-02")) == "31 de octubre al 2 de noviembre"
    assert etiqueta_fechas(pd.Timestamp("2025-12-30"), pd.Timestamp("2026-01-02")) == (
        "30 de diciembre de 2025 al 2 de enero de 2026"
    )
    assert etiqueta_fechas(pd.Timestamp("2025-11-12"), pd.Timestamp("2025-11-12")) == "12 de noviembre"


def test_tabla_partidos_con_dia_y_hora():
    tabla = tabla_partidos(_partidos().iloc[[2, 3]])
    assert tabla.columns.tolist() == ["Cuándo", "Local", "Marcador", "Visitante", "Fase"]
    assert tabla["Cuándo"].tolist() == ["Vie 31/10 19:00", "Sáb 01/11 12:00"]
    assert tabla["Marcador"].tolist() == ["2-2", "3-1"]
    assert tabla["Fase"].tolist() == ["Regular", "Regular"]
