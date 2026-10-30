"""Pruebas de la tabla de campeones (segunda fuente) y su validación contra los partidos.

DATOS DE PRUEBA: equipos, torneos y marcadores ficticios.
"""

import pandas as pd
import pytest

from football_analytics.campeones import RUTA_CAMPEONES, cargar_campeones, validar_campeones

CSV_CAMPEONES = """torneo,campeon,subcampeon,definicion
Apertura 2025,Equipo A,Equipo B,penales
Clausura 2026,Equipo C,Equipo A,global
"""


def _partidos_con_finales() -> pd.DataFrame:
    """Apertura 2025: final A-B (ida y vuelta). Clausura 2026: final C-A."""
    return pd.DataFrame({
        "torneo": ["Apertura 2025"] * 3 + ["Clausura 2026"] * 2,
        "fase": ["final"] * 5,
        "fecha": pd.to_datetime(["2025-12-01", "2025-12-10", "2025-12-14", "2026-05-20", "2026-05-24"]),
        "equipo_local": ["Equipo C", "Equipo B", "Equipo A", "Equipo A", "Equipo C"],
        "equipo_visitante": ["Equipo A", "Equipo A", "Equipo B", "Equipo C", "Equipo A"],
        "goles_local": [0, 1, 0, 1, 2],
        "goles_visitante": [1, 0, 1, 1, 0],
    })


def test_cargar_campeones(tmp_path):
    ruta = tmp_path / "campeones.csv"
    ruta.write_text(CSV_CAMPEONES, encoding="utf-8")
    campeones = cargar_campeones(ruta)
    assert campeones.loc["Apertura 2025", "campeon"] == "Equipo A"
    assert campeones.loc["Clausura 2026", "definicion"] == "global"


def test_cargar_campeones_rechaza_definicion_desconocida(tmp_path):
    ruta = tmp_path / "campeones.csv"
    ruta.write_text("torneo,campeon,subcampeon,definicion\nApertura 2025,Equipo A,Equipo B,volado\n", encoding="utf-8")
    with pytest.raises(ValueError, match="volado"):
        cargar_campeones(ruta)


def test_cargar_campeones_rechaza_torneo_repetido(tmp_path):
    ruta = tmp_path / "campeones.csv"
    ruta.write_text(CSV_CAMPEONES + "Apertura 2025,Equipo B,Equipo A,global\n", encoding="utf-8")
    with pytest.raises(ValueError, match="repetido"):
        cargar_campeones(ruta)


def test_validar_campeones_sin_problemas(tmp_path):
    ruta = tmp_path / "campeones.csv"
    ruta.write_text(CSV_CAMPEONES, encoding="utf-8")
    assert validar_campeones(cargar_campeones(ruta), _partidos_con_finales()) == {}


def test_validar_campeones_detecta_finalista_equivocado(tmp_path):
    ruta = tmp_path / "campeones.csv"
    ruta.write_text(CSV_CAMPEONES.replace("Equipo C,Equipo A,global", "Equipo C,Equipo B,global"), encoding="utf-8")
    problemas = validar_campeones(cargar_campeones(ruta), _partidos_con_finales())
    assert list(problemas) == ["Clausura 2026"]
    assert "Equipo A vs. Equipo C" in problemas["Clausura 2026"]


def test_validar_campeones_detecta_torneo_sin_final_en_los_datos(tmp_path):
    ruta = tmp_path / "campeones.csv"
    ruta.write_text(CSV_CAMPEONES + "Apertura 2026,Equipo A,Equipo B,global\n", encoding="utf-8")
    problemas = validar_campeones(cargar_campeones(ruta), _partidos_con_finales())
    assert problemas == {"Apertura 2026": "no hay una final (dos partidos) en los datos."}


def test_tabla_real_del_repositorio_es_valida():
    """El archivo versionado carga sin errores y cubre de Apertura 2012 a Clausura 2026 (sin Clausura 2020)."""
    campeones = cargar_campeones(RUTA_CAMPEONES)
    assert len(campeones) == 27
    assert "Clausura 2020" not in campeones.index
    assert set(campeones["definicion"]) == {"global", "tiempo extra", "penales"}
    assert (campeones["campeon"] != campeones["subcampeon"]).all()
