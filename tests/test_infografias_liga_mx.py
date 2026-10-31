"""Pruebas de las infografías de Liga MX (resultados) y de la carga compartida de datos.

DATOS DE PRUEBA: el mismo CSV ficticio de test_cleaning.py (Equipo A/B/C, Apertura 2025 y Clausura 2026).
"""

import json

import pandas as pd
import pytest

from football_analytics.cleaning import preparar_partidos
from football_analytics.datos import cargar_liga_mx, estado_torneo
from football_analytics.ingest import cargar_partidos_football_data, crear_metadatos, ruta_metadatos
from test_cleaning import CSV_PRUEBA

pytest.importorskip("mplsoccer")  # dependencia opcional: requirements-infografias.txt

from football_analytics.infografias import liga_mx  # noqa: E402
from football_analytics.infografias.estilo import TEMAS  # noqa: E402


@pytest.fixture
def procesado(tmp_path):
    crudo = tmp_path / "MEX.csv"
    crudo.write_text(CSV_PRUEBA, encoding="utf-8")
    partidos = preparar_partidos(cargar_partidos_football_data(crudo))
    salida = tmp_path / "procesado.csv"
    partidos.to_csv(salida, index=False)
    ruta_metadatos(salida).write_text(json.dumps(crear_metadatos(partidos, crudo)), encoding="utf-8")
    return salida


@pytest.fixture
def partidos(procesado):
    return cargar_liga_mx(procesado)[0]


def test_cargar_liga_mx_convierte_hora_y_marca_administrativos(procesado):
    partidos, metadatos = cargar_liga_mx(procesado)
    assert {"fecha_fuente", "hora", "resultado_administrativo"} <= set(partidos.columns)
    assert not partidos["resultado_administrativo"].any()  # la corrección real no está en los datos de prueba
    assert metadatos is not None


def test_estado_torneo(partidos):
    # Datos de prueba: las dos fases regulares están completas (Clausura 2026: 2 equipos, 1 partido).
    assert estado_torneo(partidos, "Apertura 2025") == "terminado"
    assert estado_torneo(partidos, "Clausura 2026") == "terminado"
    en_juego = partidos.assign(regular_completa=partidos["torneo"] != "Clausura 2026")
    assert estado_torneo(en_juego, "Clausura 2026") == "en_curso"
    with pytest.raises(ValueError):
        estado_torneo(partidos, "Apertura 1999")


def test_estado_torneo_cancelado():
    filas = pd.DataFrame({
        "torneo": ["Clausura 2020", "Apertura 2020"], "regular_completa": [False, False],
    })
    assert estado_torneo(filas, "Clausura 2020") == "cancelado"
    assert estado_torneo(filas, "Apertura 2020") == "en_curso"


def test_nombre_archivo():
    assert liga_mx.nombre_archivo("equipo", "Club León", "Apertura 2025") == "equipo_club_leon_apertura_2025.png"
    assert liga_mx.nombre_archivo("Clásico Nacional") == "clasico_nacional.png"


def test_nota_de_estado(partidos):
    assert liga_mx.nota_de_estado(partidos, "Apertura 2025") == ""
    en_juego = partidos.assign(regular_completa=partidos["torneo"] != "Clausura 2026")
    # Partido del 10/01/2026 a la 01:00 en Reino Unido = 9 de enero en México.
    assert liga_mx.nota_de_estado(en_juego, "Clausura 2026") == "Torneo en juego: 1 partido jugado hasta el 09/01/2026."


@pytest.mark.parametrize("tema", sorted(TEMAS))
def test_laminas_generan_png(partidos, tmp_path, tema):
    T = TEMAS[tema]
    campeones = pd.DataFrame({"campeon": ["Equipo A"], "subcampeon": ["Equipo B"], "definicion": ["penales"]},
                             index=pd.Index(["Apertura 2025"], name="torneo"))
    liga_mx.infografia_tabla(partidos, "Apertura 2025", tmp_path / "tabla.png", T, campeones=campeones)
    liga_mx.infografia_equipo(partidos, "Apertura 2025", "Equipo A", tmp_path / "equipo.png", T, campeones=campeones)
    liga_mx.infografia_clasico(partidos, "Clásico de prueba", "Equipo A", "Equipo B", tmp_path / "clasico.png", T)
    for nombre in ["tabla.png", "equipo.png", "clasico.png"]:
        assert (tmp_path / nombre).stat().st_size > 10_000


def test_clasico_sin_partidos_explica_el_error(partidos, tmp_path):
    with pytest.raises(ValueError, match="no se enfrentaron"):
        liga_mx.infografia_clasico(partidos, "X", "Equipo A", "Equipo Z", tmp_path / "x.png", TEMAS["oscuro"])


def test_main_genera_tabla_y_equipo_por_defecto(procesado, tmp_path):
    # Los clásicos reales no existen en los datos de prueba: --clasico ninguno.
    generadas = liga_mx.main(["--datos", str(procesado), "--torneo", "Apertura 2025", "--clasico", "ninguno",
                              "--out", str(tmp_path)])
    # Sin campeón de Apertura 2025 en la tabla real para estos equipos ficticios: el equipo por defecto es el líder.
    assert [p.name for p in generadas] == ["tabla_apertura_2025.png", "equipo_equipo_a_apertura_2025.png"]
    assert all(p.exists() for p in generadas)


def test_hora_mexico_en_datos_de_prueba(partidos):
    # 05/07/2025 01:00 en Reino Unido (horario de verano) = 4 de julio, 18:00 en el centro de México.
    primero = partidos.sort_values("fecha").iloc[0]
    assert (primero["fecha"].strftime("%Y-%m-%d %H:%M"), primero["hora"]) == ("2025-07-04 18:00", "18:00")
