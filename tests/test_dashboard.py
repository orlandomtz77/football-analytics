"""Pruebas del dashboard con AppTest de Streamlit (sin navegador).

DATOS DE PRUEBA: se usa el mismo CSV ficticio de test_cleaning.py.
"""

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from football_analytics.cleaning import preparar_partidos
from football_analytics.ingest import cargar_partidos_football_data, crear_metadatos, ruta_metadatos
from test_cleaning import CSV_PRUEBA

APP = str(Path(__file__).resolve().parents[1] / "dashboard" / "app.py")


@pytest.fixture
def datos_procesados(tmp_path, monkeypatch):
    crudo = tmp_path / "MEX.csv"
    crudo.write_text(CSV_PRUEBA, encoding="utf-8")
    partidos = preparar_partidos(cargar_partidos_football_data(crudo))
    salida = tmp_path / "procesado.csv"
    partidos.to_csv(salida, index=False)
    ruta_metadatos(salida).write_text(json.dumps(crear_metadatos(partidos, crudo)), encoding="utf-8")
    monkeypatch.setenv("LIGA_MX_DATOS", str(salida))
    return salida


def test_dashboard_carga_y_recorre_todos_los_torneos(datos_procesados):
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert at.selectbox[0].options == ["Clausura 2026", "Apertura 2025"]
    for torneo in at.selectbox[0].options:
        at.selectbox[0].set_value(torneo).run()
        assert not at.exception, torneo


def test_dashboard_muestra_indicadores(datos_procesados):
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.selectbox[0].set_value("Apertura 2025").run()
    indicadores = {m.label: m.value for m in at.metric}
    assert indicadores["Partidos (fase regular)"] == "3"
    # 2-0, 1-1, 0-3 -> 7 goles en 3 partidos.
    assert indicadores["Goles por partido"] == "2.33"


def test_dashboard_sin_archivo_muestra_error_amigable(tmp_path, monkeypatch):
    monkeypatch.setenv("LIGA_MX_DATOS", str(tmp_path / "no_existe.csv"))
    monkeypatch.setenv("LIGA_MX_DESCARGA", "0")  # sin red en las pruebas
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert "No se encontró" in at.error[0].value
