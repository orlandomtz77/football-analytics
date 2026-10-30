"""Pruebas de gráficos.

DATOS DE PRUEBA: equipos y valores ficticios.
"""

import numpy as np
import pandas as pd

from football_analytics.charts import grafico_local_visitante

RENDIMIENTO_PRUEBA = pd.DataFrame({
    "equipo": ["Equipo A", "Equipo B", "Equipo C"],
    "PJ_local": [2, 1, 0], "Pts_local": [6, 1, 0], "PPP_local": [3.0, 1.0, np.nan],
    "GF_local": [4, 1, 0], "GC_local": [0, 1, 0],
    "PJ_visitante": [1, 2, 1], "Pts_visitante": [0, 3, 1], "PPP_visitante": [0.0, 1.5, 1.0],
    "GF_visitante": [0, 2, 1], "GC_visitante": [1, 1, 1],
    "dif_PPP": [3.0, -0.5, np.nan],
})


def test_grafico_tiene_conector_y_dos_series():
    fig = grafico_local_visitante(RENDIMIENTO_PRUEBA, "Prueba")
    assert [t.name for t in fig.data] == [None, "Local", "Visitante"]
    assert fig.layout.title.text == "Prueba"


def test_grafico_omite_equipos_sin_dato_y_ordena_por_diferencia():
    fig = grafico_local_visitante(RENDIMIENTO_PRUEBA, "Prueba")
    # C no tiene PPP local; A (mayor diferencia) queda al final = arriba en el gráfico.
    assert list(fig.data[1].y) == ["Equipo B", "Equipo A"]


def test_grafico_con_tabla_vacia_no_falla():
    fig = grafico_local_visitante(RENDIMIENTO_PRUEBA.iloc[0:0], "Vacío")
    assert len(fig.data[1].x) == 0


def test_grafico_muestra_nota_de_fuente():
    fig = grafico_local_visitante(RENDIMIENTO_PRUEBA, "Prueba", nota="Fuente: prueba")
    assert fig.layout.annotations[0].text == "Fuente: prueba"
