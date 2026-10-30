"""Pruebas de reglamento, formatos e insights para la vista de aficionado.

DATOS DE PRUEBA: equipos y marcadores ficticios.
"""

import pandas as pd
import pytest

from football_analytics.formato import cantidad, forma_con_iconos, record, unir_nombres
from football_analytics.insights import datos_destacados
from football_analytics.metrics import calcular_evolucion_puntos, calcular_tabla_posiciones, ultimos_resultados
from football_analytics.reglamento import ZONAS_POR_TORNEO, asignar_zona, zonas_del_torneo

# A gana 2-0 a B (local); B empata 1-1 con C (local); C pierde 0-3 con A (A visitante).
PARTIDOS = pd.DataFrame({
    "fecha": pd.to_datetime(["2025-07-01", "2025-07-08", "2025-07-15"]),
    "equipo_local": ["Equipo A", "Equipo B", "Equipo C"],
    "equipo_visitante": ["Equipo B", "Equipo C", "Equipo A"],
    "goles_local": [2, 1, 0],
    "goles_visitante": [0, 1, 3],
})


# --- Tabla por condición ---

def test_tabla_local_solo_cuenta_partidos_en_casa():
    local = calcular_tabla_posiciones(PARTIDOS, condicion="local").set_index("equipo")
    assert local.loc["Equipo A", ["PJ", "PG", "GF", "Pts"]].tolist() == [1, 1, 2, 3]
    assert local.loc["Equipo C", ["PJ", "PP", "GC", "Pts"]].tolist() == [1, 1, 3, 0]


def test_tabla_local_mas_visitante_igual_a_general():
    general = calcular_tabla_posiciones(PARTIDOS).set_index("equipo")
    local = calcular_tabla_posiciones(PARTIDOS, condicion="local").set_index("equipo")
    visita = calcular_tabla_posiciones(PARTIDOS, condicion="visitante").set_index("equipo")
    suma = local[["PJ", "Pts", "GF", "GC"]].add(visita[["PJ", "Pts", "GF", "GC"]], fill_value=0)
    assert suma.reindex(general.index).astype(int).equals(general[["PJ", "Pts", "GF", "GC"]])


def test_tabla_condicion_invalida():
    with pytest.raises(ValueError, match="condicion"):
        calcular_tabla_posiciones(PARTIDOS, condicion="neutral")


def test_ultimos_resultados():
    ultimos = ultimos_resultados(calcular_evolucion_puntos(PARTIDOS), n=1)
    assert ultimos["Equipo A"] == ["G"]
    assert ultimos_resultados(calcular_evolucion_puntos(PARTIDOS))["Equipo B"] == ["P", "E"]


# --- Formatos ---

def test_formatos():
    assert forma_con_iconos(["G", "E", "P"]) == "✅ ➖ ❌"
    assert record(8, 4, 2) == "8G-4E-2P"
    assert unir_nombres(["A"]) == "A"
    assert unir_nombres(["A", "B", "C"]) == "A, B y C"
    assert cantidad(1, "gol", "goles") == "1 gol"
    assert cantidad(0, "gol", "goles") == "0 goles"


# --- Reglamento ---

def test_reglamento_cubre_todos_los_torneos_del_dataset():
    from football_analytics.cleaning import ordenar_torneos

    esperados = {f"{n} {a}" for a in range(2012, 2027) for n in ("Apertura", "Clausura")} - {"Clausura 2012", "Clausura 2027"}
    assert set(ZONAS_POR_TORNEO) == esperados
    assert len(ordenar_torneos(esperados)) == 29


def test_zonas_por_epoca():
    assert zonas_del_torneo("Apertura 2015") == [("Liguilla", 1, 8)]
    assert zonas_del_torneo("Clausura 2020") is None
    assert zonas_del_torneo("Clausura 2022") == [("Cuartos de final", 1, 4), ("Reclasificación", 5, 12)]
    assert zonas_del_torneo("Apertura 2025") == [("Cuartos de final", 1, 6), ("Play-in", 7, 10)]
    assert zonas_del_torneo("Apertura 2026") == [("Cuartos de final", 1, 8)]
    assert zonas_del_torneo("Torneo inventado") is None


def test_asignar_zona_por_posicion():
    tabla = pd.DataFrame({"equipo": [f"E{i}" for i in range(1, 13)]})
    zonas = asignar_zona(tabla, "Apertura 2025").tolist()
    assert zonas[:6] == ["Cuartos de final"] * 6
    assert zonas[6:10] == ["Play-in"] * 4
    assert zonas[10:] == ["", ""]
    assert asignar_zona(tabla, "Clausura 2020").tolist() == [""] * 12


# --- Datos destacados ---

def test_datos_destacados():
    frases = datos_destacados(PARTIDOS)
    texto = "\n".join(frases)
    # A: local 1G (3 de 3) y visitante 1G (3 de 3); B y C no ganan.
    assert "**Mejor local:** Equipo A (1G-0E-0P en casa, 3 de 3 puntos posibles)." in texto
    assert "**Mejor visitante:** Equipo A (1G-0E-0P de visita, 3 de 3 puntos posibles)." in texto
    assert "**Racha más larga de victorias:** Equipo A, 2 partidos seguidos." in texto
    assert "**Ataque más goleador:** Equipo A, 5 goles." in texto
    assert "**Menos goles recibidos:** Equipo A, 0 goles en contra." in texto


def test_datos_destacados_empates_y_vacio():
    empate = PARTIDOS.iloc[[1]]  # solo B 1-1 C
    texto = "\n".join(datos_destacados(empate))
    assert "Racha más larga" not in texto  # nadie ganó
    assert "**Ataque más goleador:** Equipo B y Equipo C, 1 gol." in texto
    assert datos_destacados(PARTIDOS.iloc[0:0]) == []


# --- Vistas ---

def test_tabla_aficionado_columnas_de_prensa_y_zona():
    from football_analytics.vistas import tabla_aficionado

    vista = tabla_aficionado(PARTIDOS, "Apertura 2025")
    assert list(vista.columns) == ["Pos", "Equipo", "PTS", "JJ", "JG", "JE", "JP", "GF", "GC", "DIF", "Últimos 5", "Zona"]
    assert vista["Equipo"].tolist() == ["Equipo A", "Equipo B", "Equipo C"]
    assert vista.loc[0, "Últimos 5"] == "✅ ✅"
    assert vista["Zona"].tolist() == ["Cuartos de final"] * 3


def test_tabla_aficionado_local_sin_zona_y_racha_de_local():
    from football_analytics.vistas import tabla_aficionado

    vista = tabla_aficionado(PARTIDOS, "Apertura 2025", condicion="local").set_index("Equipo")
    assert "Zona" not in vista.columns
    assert vista.at["Equipo C", "Últimos 5"] == "❌"  # C solo jugó de local una vez y perdió


def test_ficha_equipo():
    from football_analytics.vistas import ficha_equipo

    ficha = ficha_equipo(PARTIDOS, "Equipo B")
    assert ficha["posicion"] == 2 and ficha["equipos"] == 3
    assert (ficha["puntos"], ficha["puntos_del_lider"], ficha["lider"]) == (1, 6, "Equipo A")
    assert ficha["record"] == "0G-1E-1P"
    assert ficha["record_local"] == "0G-1E-0P"
    assert ficha["record_visita"] == "0G-0E-1P"
    assert ficha["ultimos_5"] == "❌ ➖"
    assert (ficha["racha_victorias"], ficha["racha_sin_perder"]) == (0, 1)
    with pytest.raises(ValueError, match="no jugó"):
        ficha_equipo(PARTIDOS, "Equipo Z")


def test_calendario_equipo():
    from football_analytics.vistas import calendario_equipo

    cal = calendario_equipo(PARTIDOS, "Equipo A")
    assert cal.to_dict("records") == [
        {"Fecha": "01/07/2025", "Rival": "Equipo B", "Dónde": "🏠 Local", "Marcador": "2-0",
         "Resultado": "✅ Ganó", "Puntos acumulados": 3},
        {"Fecha": "15/07/2025", "Rival": "Equipo C", "Dónde": "✈️ Visita", "Marcador": "3-0",
         "Resultado": "✅ Ganó", "Puntos acumulados": 6},
    ]
