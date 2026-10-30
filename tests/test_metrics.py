"""Pruebas de la tabla de posiciones.

DATOS DE PRUEBA: los equipos y marcadores son ficticios, solo para verificar el cálculo.
"""

import pandas as pd
import pytest

from football_analytics.metrics import calcular_tabla_posiciones

# Equipo A gana 2-0 a B; B empata 1-1 con C. D no juega.
PARTIDOS_PRUEBA = pd.DataFrame({
    "equipo_local": ["Equipo A", "Equipo B"],
    "equipo_visitante": ["Equipo B", "Equipo C"],
    "goles_local": [2, 1],
    "goles_visitante": [0, 1],
})
EQUIPOS_PRUEBA = ["Equipo A", "Equipo B", "Equipo C", "Equipo D"]


def fila(tabla: pd.DataFrame, equipo: str) -> dict:
    return tabla.set_index("equipo").loc[equipo].to_dict()


def test_victoria_empate_derrota_y_equipo_sin_partidos():
    tabla = calcular_tabla_posiciones(PARTIDOS_PRUEBA, equipos=EQUIPOS_PRUEBA)

    assert fila(tabla, "Equipo A") == {"PJ": 1, "PG": 1, "PE": 0, "PP": 0, "GF": 2, "GC": 0, "DG": 2, "Pts": 3}
    assert fila(tabla, "Equipo B") == {"PJ": 2, "PG": 0, "PE": 1, "PP": 1, "GF": 1, "GC": 3, "DG": -2, "Pts": 1}
    assert fila(tabla, "Equipo C") == {"PJ": 1, "PG": 0, "PE": 1, "PP": 0, "GF": 1, "GC": 1, "DG": 0, "Pts": 1}
    assert fila(tabla, "Equipo D") == {"PJ": 0, "PG": 0, "PE": 0, "PP": 0, "GF": 0, "GC": 0, "DG": 0, "Pts": 0}


def test_orden_por_puntos_y_diferencia():
    tabla = calcular_tabla_posiciones(PARTIDOS_PRUEBA, equipos=EQUIPOS_PRUEBA)
    # C y B empatan en puntos; C va arriba por mejor DG.
    assert tabla["equipo"].tolist() == ["Equipo A", "Equipo C", "Equipo B", "Equipo D"]


def test_coherencia_global():
    tabla = calcular_tabla_posiciones(PARTIDOS_PRUEBA, equipos=EQUIPOS_PRUEBA)
    assert tabla["PJ"].sum() == 2 * len(PARTIDOS_PRUEBA)
    assert tabla["GF"].sum() == tabla["GC"].sum()
    assert tabla["PG"].sum() == tabla["PP"].sum()


def test_reglamento_de_puntos_configurable():
    tabla = calcular_tabla_posiciones(PARTIDOS_PRUEBA, puntos_victoria=2, puntos_empate=1)
    assert fila(tabla, "Equipo A")["Pts"] == 2


def test_sin_partidos_devuelve_tabla_vacia():
    vacio = PARTIDOS_PRUEBA.iloc[0:0]
    tabla = calcular_tabla_posiciones(vacio)
    assert tabla.empty
    assert list(tabla.columns) == ["equipo", "PJ", "PG", "PE", "PP", "GF", "GC", "DG", "Pts"]


def test_rechaza_goles_negativos():
    malos = PARTIDOS_PRUEBA.copy()
    malos.loc[0, "goles_local"] = -1
    with pytest.raises(ValueError, match="negativos"):
        calcular_tabla_posiciones(malos)


def test_rechaza_columnas_faltantes():
    with pytest.raises(ValueError, match="Faltan columnas"):
        calcular_tabla_posiciones(PARTIDOS_PRUEBA.drop(columns="goles_local"))
