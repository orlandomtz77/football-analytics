"""Pruebas de los resultados administrativos (partidos que la liga cambió en la mesa).

DATOS DE PRUEBA: equipos y marcadores ficticios.
"""

import pandas as pd

from football_analytics.correcciones import RUTA_CORRECCIONES, aplicar_correcciones, cargar_correcciones

CSV_CORRECCIONES = """torneo,fecha_fuente,equipo_local,equipo_visitante,goles_local_cancha,goles_visitante_cancha,goles_local,goles_visitante,motivo,fuente_url
Apertura 2025,2025-07-08,Equipo A,Equipo B,0,2,3,0,Jugador no elegible,https://ejemplo.org
"""


def _partidos() -> pd.DataFrame:
    return pd.DataFrame({
        "torneo": ["Apertura 2025", "Apertura 2025"],
        "fecha": pd.to_datetime(["2025-07-01", "2025-07-08"]),
        "equipo_local": ["Equipo B", "Equipo A"],
        "equipo_visitante": ["Equipo A", "Equipo B"],
        "goles_local": [1, 0],
        "goles_visitante": [1, 2],
        "resultado": ["D", "A"],
    })


def _correcciones(tmp_path, texto=CSV_CORRECCIONES):
    ruta = tmp_path / "correcciones.csv"
    ruta.write_text(texto, encoding="utf-8")
    return cargar_correcciones(ruta)


def test_aplica_el_resultado_oficial_sin_modificar_el_original(tmp_path):
    partidos = _partidos()
    corregidos, problemas = aplicar_correcciones(partidos, _correcciones(tmp_path))
    assert problemas == []
    fila = corregidos.iloc[1]
    assert (fila["goles_local"], fila["goles_visitante"], fila["resultado"]) == (3, 0, "H")
    assert corregidos["resultado_administrativo"].tolist() == [False, True]
    assert partidos.iloc[1]["goles_visitante"] == 2  # el DataFrame original no cambia


def test_no_aplica_si_el_marcador_de_la_fuente_cambio(tmp_path):
    texto = CSV_CORRECCIONES.replace("Equipo B,0,2,3,0", "Equipo B,1,2,3,0")
    corregidos, problemas = aplicar_correcciones(_partidos(), _correcciones(tmp_path, texto))
    assert corregidos.iloc[1]["goles_visitante"] == 2
    assert not corregidos["resultado_administrativo"].any()
    assert len(problemas) == 1 and "Equipo A vs. Equipo B" in problemas[0]


def test_no_aplica_si_el_partido_no_esta_en_los_datos(tmp_path):
    texto = CSV_CORRECCIONES.replace("2025-07-08", "2025-08-01")
    _, problemas = aplicar_correcciones(_partidos(), _correcciones(tmp_path, texto))
    assert len(problemas) == 1


def test_archivo_real_del_repositorio_carga():
    correcciones = cargar_correcciones(RUTA_CORRECCIONES)
    assert len(correcciones) >= 1
    assert correcciones["fuente_url"].str.startswith("https://").all()


def test_aplica_despues_de_convertir_a_hora_de_mexico(tmp_path):
    from football_analytics.cleaning import convertir_a_hora_mexico

    # 01:00 en Reino Unido del 8 de julio = 7 de julio en México: la corrección usa la fecha de la fuente.
    partidos = convertir_a_hora_mexico(_partidos().assign(hora_fuente="01:00"))
    corregidos, problemas = aplicar_correcciones(partidos, _correcciones(tmp_path))
    assert problemas == []
    assert corregidos["resultado_administrativo"].tolist() == [False, True]
