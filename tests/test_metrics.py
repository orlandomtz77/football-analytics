"""Pruebas de la tabla de posiciones.

DATOS DE PRUEBA: los equipos y marcadores son ficticios, solo para verificar el cálculo.
"""

import pandas as pd
import pytest

from football_analytics.metrics import (
    calcular_evolucion_puntos,
    calcular_rendimiento_local_visitante,
    calcular_tabla_posiciones,
    racha_mas_larga,
)

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


def test_local_visitante_separa_condiciones():
    rendimiento = calcular_rendimiento_local_visitante(PARTIDOS_PRUEBA).set_index("equipo")
    # B fue local (1-1 vs C) y visitante (0-2 vs A).
    b = rendimiento.loc["Equipo B"]
    assert (b["PJ_local"], b["Pts_local"], b["GF_local"], b["GC_local"]) == (1, 1, 1, 1)
    assert (b["PJ_visitante"], b["Pts_visitante"], b["GF_visitante"], b["GC_visitante"]) == (1, 0, 0, 2)
    assert b["PPP_local"] == 1.0
    assert b["PPP_visitante"] == 0.0
    assert b["dif_PPP"] == 1.0


def test_local_visitante_sin_partidos_en_una_condicion_no_divide_entre_cero():
    rendimiento = calcular_rendimiento_local_visitante(PARTIDOS_PRUEBA).set_index("equipo")
    a = rendimiento.loc["Equipo A"]  # solo jugó de local
    assert a["PJ_visitante"] == 0
    assert pd.isna(a["PPP_visitante"])
    assert pd.isna(a["dif_PPP"])


def test_local_visitante_orden_y_consistencia_con_tabla():
    rendimiento = calcular_rendimiento_local_visitante(PARTIDOS_PRUEBA)
    # B tiene dif_PPP definida; A y C (sin dato) van al final por nombre.
    assert rendimiento["equipo"].tolist() == ["Equipo B", "Equipo A", "Equipo C"]

    tabla = calcular_tabla_posiciones(PARTIDOS_PRUEBA).set_index("equipo")
    r = rendimiento.set_index("equipo").reindex(tabla.index)
    assert ((r["Pts_local"] + r["Pts_visitante"]) == tabla["Pts"]).all()
    assert ((r["PJ_local"] + r["PJ_visitante"]) == tabla["PJ"]).all()


# B: pierde 0-2 con A (día 1), empata 1-1 con C (día 8), gana 3-0 a A (día 15).
PARTIDOS_CON_FECHA = pd.DataFrame({
    "fecha": pd.to_datetime(["2025-07-15", "2025-07-01", "2025-07-08"]),  # desordenados a propósito
    "equipo_local": ["Equipo B", "Equipo A", "Equipo B"],
    "equipo_visitante": ["Equipo A", "Equipo B", "Equipo C"],
    "goles_local": [3, 2, 1],
    "goles_visitante": [0, 0, 1],
})


def test_evolucion_ordena_por_fecha_y_acumula():
    evolucion = calcular_evolucion_puntos(PARTIDOS_CON_FECHA)
    b = evolucion[evolucion["equipo"] == "Equipo B"]
    assert b["partido_n"].tolist() == [1, 2, 3]
    assert b["rival"].tolist() == ["Equipo A", "Equipo C", "Equipo A"]
    assert b["condicion"].tolist() == ["visitante", "local", "local"]
    assert b["resultado"].tolist() == ["P", "E", "G"]
    assert b["Pts_acumulados"].tolist() == [0, 1, 4]


def test_evolucion_cuadra_con_tabla():
    evolucion = calcular_evolucion_puntos(PARTIDOS_CON_FECHA)
    finales = evolucion.groupby("equipo")["Pts_acumulados"].last()
    tabla = calcular_tabla_posiciones(PARTIDOS_CON_FECHA).set_index("equipo")["Pts"]
    assert finales.reindex(tabla.index).tolist() == tabla.tolist()


def test_evolucion_requiere_fecha():
    with pytest.raises(ValueError, match="fecha"):
        calcular_evolucion_puntos(PARTIDOS_PRUEBA)


def test_racha_mas_larga():
    resultados = ["G", "G", "E", "G", "P", "G", "G", "G"]
    assert racha_mas_larga(resultados, {"G"}) == 3
    assert racha_mas_larga(resultados, {"G", "E"}) == 4
    assert racha_mas_larga(resultados, {"P"}) == 1
    assert racha_mas_larga([], {"G"}) == 0
