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
    assert indicadores["Partidos jugados"] == "3"
    # 2-0, 1-1, 0-3 -> 7 goles en 3 partidos.
    assert indicadores["Goles por partido"] == "2.3"
    textos = " ".join(m.value for m in at.markdown)
    assert "**Mejor local:**" in textos
    assert "**Ataque más goleador:** Equipo A, 5 goles." in textos


def test_dashboard_sin_archivo_muestra_error_amigable(tmp_path, monkeypatch):
    monkeypatch.setenv("LIGA_MX_DATOS", str(tmp_path / "no_existe.csv"))
    monkeypatch.setenv("LIGA_MX_DESCARGA", "0")  # sin red en las pruebas
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert "No se encontró" in at.error[0].value


def test_dashboard_ficha_de_equipo(datos_procesados):
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.selectbox[0].set_value("Apertura 2025").run()
    selector_equipo = at.selectbox[1]
    # Tabla Apertura 2025 de prueba: A 6 pts, B 1 (DIF -2), C 1 (DIF -3).
    assert selector_equipo.options == ["Equipo A", "Equipo B", "Equipo C"]
    for equipo in selector_equipo.options:
        at.selectbox[1].set_value(equipo).run()
        assert not at.exception, equipo
    at.selectbox[1].set_value("Equipo B").run()
    indicadores = {m.label: m.value for m in at.metric}
    assert indicadores["Posición"] == "2.º de 3"
    assert indicadores["Puntos"] == "1"
    assert indicadores["Del líder"] == "A 5 puntos"
    assert indicadores["Récord"] == "0G-1E-1P"
    textos = " ".join(m.value for m in at.markdown)
    assert "**Últimos 5:** ❌ ➖" in textos


def test_dashboard_historial(datos_procesados):
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.selectbox[0].set_value("Apertura 2025").run()
    at.selectbox[1].set_value("Equipo A").run()
    assert not at.exception
    assert any("Historial de Equipo A" in h.value for h in at.subheader)
    textos = " ".join(m.value for m in at.markdown)
    # Datos de prueba: A jugó Apertura 2025 (6 pts) y Clausura 2026 (1 partido, 3 pts).
    assert "**Torneos en los datos:** 2 (desde Apertura 2025)." in textos


def test_dashboard_cara_a_cara(datos_procesados):
    at = AppTest.from_file(APP, default_timeout=60).run()
    # Los clásicos no existen en los datos de prueba: mensaje claro, sin error.
    assert not at.exception
    assert any("no se enfrentaron" in i.value for i in at.info)

    at.selectbox[2].set_value("Elegir dos equipos…").run()
    at.selectbox[3].set_value("Equipo A").run()
    at.selectbox[4].set_value("Equipo B").run()
    assert not at.exception
    indicadores = {m.label: m.value for m in at.metric}
    # Datos de prueba: A 2-0 B (regular), B 1-0 A y A 2-2 B (fase final).
    assert indicadores["Ganó Equipo A"] == "1"
    assert indicadores["Empates"] == "1"
    assert indicadores["Ganó Equipo B"] == "1"
