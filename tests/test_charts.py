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


EVOLUCION_PRUEBA = pd.DataFrame({
    "equipo": ["Equipo A", "Equipo A", "Equipo B", "Equipo B"],
    "partido_n": [1, 2, 1, 2],
    "fecha": pd.to_datetime(["2025-07-01", "2025-07-08", "2025-07-01", "2025-07-08"]),
    "rival": ["Equipo B", "Equipo C", "Equipo A", "Equipo C"],
    "condicion": ["local", "visitante", "visitante", "local"],
    "GF": [2, 1, 0, 1], "GC": [0, 1, 2, 0],
    "resultado": ["G", "E", "P", "G"],
    "Pts": [3, 1, 0, 3], "Pts_acumulados": [3, 4, 0, 3],
})


def test_evolucion_con_referencia_dos_series_y_etiquetas():
    from football_analytics.charts import grafico_evolucion_puntos

    fig = grafico_evolucion_puntos(EVOLUCION_PRUEBA, "Equipo B", referencia="Equipo A")
    assert [t.name for t in fig.data] == ["Equipo B", "Equipo A"]
    assert list(fig.data[0].y) == [0, 3]
    assert fig.layout.showlegend is True
    assert {a.text for a in fig.layout.annotations} == {"Equipo B: 3", "Equipo A: 4"}


def test_evolucion_sin_referencia_o_misma_referencia_una_serie():
    from football_analytics.charts import grafico_evolucion_puntos

    fig = grafico_evolucion_puntos(EVOLUCION_PRUEBA, "Equipo A", referencia="Equipo A")
    assert len(fig.data) == 1
    assert fig.layout.showlegend is False



def test_graficos_no_fijan_fondo_ni_texto_para_respetar_el_tema():
    """El tema de Streamlit (claro u oscuro) debe poder poner fondo y textos."""
    import pandas as pd

    from football_analytics.charts import grafico_evolucion_puntos, grafico_historial_puntos

    historial = pd.DataFrame({
        "Torneo": ["Apertura 2026", "Clausura 2026"], "PTS": [10, 30], "Pos": [5, 1], "Equipos": [18, 18],
        "Récord": ["3G-1E-1P", "9G-3E-5P"], "Fase final": ["—", "✅ Sí"], "Completo": [False, True],
    })
    figuras = [
        grafico_local_visitante(RENDIMIENTO_PRUEBA, "Prueba", nota="Fuente"),
        grafico_evolucion_puntos(EVOLUCION_PRUEBA, "Equipo B", referencia="Equipo A", titulo="T", nota="N"),
        grafico_historial_puntos(historial, "Equipo A"),
    ]
    for fig in figuras:
        assert fig.layout.paper_bgcolor is None
        assert fig.layout.plot_bgcolor is None
        assert fig.layout.font.color is None
        assert fig.layout.title.font.color is None
        assert all(a.font.color is None for a in fig.layout.annotations)
