"""Pruebas de ingestión y limpieza.

DATOS DE PRUEBA: equipos y marcadores ficticios, con el formato de football-data.co.uk.
"""

import pandas as pd
import pytest

from football_analytics.cleaning import asignar_fase, asignar_torneo, ordenar_torneos, preparar_partidos
from football_analytics.ingest import (
    cargar_partidos_football_data,
    cargar_partidos_procesados,
    crear_metadatos,
)

# 3 equipos -> fase regular de 3 partidos; luego una final de ida y vuelta.
CSV_PRUEBA = """﻿Country,League,Season,Date,Time,Home,Away,HG,AG,Res,PSCH,,
Mexico,Liga MX,2025/2026,05/07/2025,01:00,Equipo A,Equipo B,2,0,H,1.9,,
Mexico,Liga MX,2025/2026,12/07/2025,01:00,Equipo B,Equipo C,1,1,D,2.1,,
Mexico,Liga MX,2025/2026,19/07/2025,01:00,Equipo C,Equipo A,0,3,A,3.0,,
Mexico,Liga MX,2025/2026,10/12/2025,02:00,Equipo B,Equipo A,1,0,H,2.5,,
Mexico,Liga MX,2025/2026,14/12/2025,02:00,Equipo A,Equipo B,2,2,D,1.8,,
Mexico,Liga MX,2025/2026,10/01/2026,02:00,Equipo A,Equipo C,1,0,H,1.7,,
"""


@pytest.fixture
def ruta_csv(tmp_path):
    ruta = tmp_path / "MEX.csv"
    ruta.write_text(CSV_PRUEBA, encoding="utf-8")
    return ruta


def test_carga_renombra_columnas_y_descarta_cuotas(ruta_csv):
    partidos = cargar_partidos_football_data(ruta_csv)
    assert list(partidos.columns) == [
        "temporada", "fecha", "hora_fuente", "equipo_local", "equipo_visitante",
        "goles_local", "goles_visitante", "resultado",
    ]
    assert partidos["fecha"].iloc[0] == pd.Timestamp("2025-07-05")


def test_carga_archivo_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        cargar_partidos_football_data(tmp_path / "no_existe.csv")


def test_carga_rechaza_resultado_incoherente(tmp_path):
    ruta = tmp_path / "MEX.csv"
    ruta.write_text(CSV_PRUEBA.replace("2,0,H", "2,0,A"), encoding="utf-8")
    with pytest.raises(ValueError, match="incoherente"):
        cargar_partidos_football_data(ruta)


def test_torneo_por_mes(ruta_csv):
    torneos = asignar_torneo(cargar_partidos_football_data(ruta_csv))["torneo"]
    assert torneos.tolist() == ["Apertura 2025"] * 5 + ["Clausura 2026"]


def test_fase_regular_y_final(ruta_csv):
    partidos = preparar_partidos(cargar_partidos_football_data(ruta_csv))
    apertura = partidos[partidos["torneo"] == "Apertura 2025"]
    assert apertura["fase"].tolist() == ["regular"] * 3 + ["final"] * 2
    assert apertura["regular_completa"].all()


def test_torneo_incompleto_queda_marcado(ruta_csv):
    partidos = preparar_partidos(cargar_partidos_football_data(ruta_csv))
    clausura = partidos[partidos["torneo"] == "Clausura 2026"]
    # 2 equipos -> 1 partido regular esperado; está completo.
    assert clausura["regular_completa"].all()
    # Si quitamos un partido de un torneo de 3 equipos, ya no está completo.
    apertura = asignar_torneo(cargar_partidos_football_data(ruta_csv)).iloc[:2]
    assert not asignar_fase(apertura)["regular_completa"].any()


def test_fase_rechaza_enfrentamiento_repetido_en_regular(ruta_csv):
    partidos = asignar_torneo(cargar_partidos_football_data(ruta_csv))
    # Duplicamos A-B dentro de la fase regular.
    partidos.loc[1, ["equipo_local", "equipo_visitante"]] = ["Equipo B", "Equipo A"]
    partidos.loc[1, "fecha"] = pd.Timestamp("2025-07-06")
    with pytest.raises(ValueError, match="repetidos"):
        asignar_fase(partidos)


def test_ordenar_torneos_mas_reciente_primero():
    torneos = ["Apertura 2024", "Clausura 2025", "Apertura 2025", "Clausura 2025"]
    assert ordenar_torneos(torneos) == ["Apertura 2025", "Clausura 2025", "Apertura 2024"]


def test_procesado_ida_y_vuelta_con_metadatos(ruta_csv, tmp_path):
    import json

    partidos = preparar_partidos(cargar_partidos_football_data(ruta_csv))
    salida = tmp_path / "procesado.csv"
    partidos.to_csv(salida, index=False)
    metadatos = crear_metadatos(partidos, ruta_csv)
    salida.with_suffix(".meta.json").write_text(json.dumps(metadatos), encoding="utf-8")

    leidos, meta = cargar_partidos_procesados(salida)
    assert len(leidos) == 6
    assert leidos["fecha"].dtype.kind == "M"  # fechas como datetime
    assert meta["partidos"] == 6
    assert meta["fecha_min"] == "2025-07-05"
    assert meta["fuente"] == "football-data.co.uk"


def test_procesado_sin_metadatos_devuelve_none(ruta_csv, tmp_path):
    salida = tmp_path / "procesado.csv"
    preparar_partidos(cargar_partidos_football_data(ruta_csv)).to_csv(salida, index=False)
    _, meta = cargar_partidos_procesados(salida)
    assert meta is None


# --- Descarga automática (sin internet: se inyecta un descargador falso) ---

def test_asegurar_datos_descarga_y_procesa_si_falta(tmp_path):
    from football_analytics.ingest import asegurar_datos

    llamadas = []

    def descargador_falso(url, destino):
        llamadas.append(url)
        destino.write_text(CSV_PRUEBA, encoding="utf-8")

    procesado = tmp_path / "processed" / "liga.csv"
    crudos = tmp_path / "raw"
    assert asegurar_datos(procesado, crudos, descargar=descargador_falso) is True
    assert llamadas == ["https://www.football-data.co.uk/new/MEX.csv"]
    assert procesado.exists()
    assert len(list(crudos.glob("football-data_MEX_*.csv"))) == 1
    _, meta = cargar_partidos_procesados(procesado)
    assert meta["partidos"] == 6

    # Segunda vez: ya existe, no vuelve a descargar.
    assert asegurar_datos(procesado, crudos, descargar=descargador_falso) is False
    assert len(llamadas) == 1


def test_asegurar_datos_error_de_red_no_deja_archivos(tmp_path):
    from football_analytics.ingest import asegurar_datos

    def descargador_sin_red(url, destino):
        raise OSError("sin conexión")

    with pytest.raises(OSError, match="sin conexión"):
        asegurar_datos(tmp_path / "liga.csv", tmp_path / "raw", descargar=descargador_sin_red)
    assert list((tmp_path / "raw").iterdir()) == []
    assert not (tmp_path / "liga.csv").exists()


def test_asegurar_datos_rechaza_archivo_con_formato_inesperado(tmp_path):
    from football_analytics.ingest import asegurar_datos

    def descargador_html(url, destino):
        destino.write_text("<html>Página de error</html>\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Faltan columnas"):
        asegurar_datos(tmp_path / "liga.csv", tmp_path / "raw", descargar=descargador_html)
    assert list((tmp_path / "raw").iterdir()) == []
