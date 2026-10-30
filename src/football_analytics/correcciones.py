"""Resultados administrativos: partidos cuyo resultado oficial cambió en la mesa.

football-data.co.uk guarda el marcador de la cancha. Si la liga cambió el resultado (p. ej. por
alinear a un jugador no elegible), la tabla oficial usa el resultado administrativo. La lista está en
`data/reference/resultados_administrativos.csv`, con la fuente de cada caso; los datos procesados no
se modifican: la corrección se aplica al cargarlos.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RUTA_CORRECCIONES = Path(__file__).resolve().parents[2] / "data" / "reference" / "resultados_administrativos.csv"


def cargar_correcciones(ruta: str | Path = RUTA_CORRECCIONES) -> pd.DataFrame:
    correcciones = pd.read_csv(ruta, parse_dates=["fecha_fuente"])
    esperadas = {"torneo", "fecha_fuente", "equipo_local", "equipo_visitante", "goles_local_cancha",
                 "goles_visitante_cancha", "goles_local", "goles_visitante", "motivo", "fuente_url"}
    faltantes = esperadas - set(correcciones.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas en {ruta}: {sorted(faltantes)}")
    return correcciones


def _resultado(goles_local: int, goles_visitante: int) -> str:
    if goles_local > goles_visitante:
        return "H"
    return "A" if goles_local < goles_visitante else "D"


def aplicar_correcciones(partidos: pd.DataFrame, correcciones: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Copia de `partidos` con los resultados oficiales y la columna `resultado_administrativo`.

    Solo corrige si el partido existe y su marcador coincide con el de cancha registrado en la lista;
    si no (p. ej. la fuente cambió), no lo toca y lo informa en la lista de problemas.
    """
    corregidos = partidos.copy()
    corregidos["resultado_administrativo"] = False
    # La lista usa la fecha de la fuente; si ya se convirtió a hora de México, está en `fecha_fuente`.
    fecha_fuente = corregidos["fecha_fuente"] if "fecha_fuente" in corregidos.columns else corregidos["fecha"]
    problemas = []
    for _, c in correcciones.iterrows():
        mascara = (
            (corregidos["torneo"] == c["torneo"])
            & (fecha_fuente.dt.normalize() == c["fecha_fuente"])
            & (corregidos["equipo_local"] == c["equipo_local"])
            & (corregidos["equipo_visitante"] == c["equipo_visitante"])
            & (corregidos["goles_local"] == c["goles_local_cancha"])
            & (corregidos["goles_visitante"] == c["goles_visitante_cancha"])
        )
        if mascara.sum() != 1:
            problemas.append(
                f"{c['torneo']}, {c['equipo_local']} vs. {c['equipo_visitante']} ({c['fecha_fuente']:%d/%m/%Y}): "
                "no se encontró el partido con ese marcador de cancha; no se corrigió."
            )
            continue
        corregidos.loc[mascara, ["goles_local", "goles_visitante"]] = [c["goles_local"], c["goles_visitante"]]
        corregidos.loc[mascara, "resultado"] = _resultado(c["goles_local"], c["goles_visitante"])
        corregidos.loc[mascara, "resultado_administrativo"] = True
    return corregidos, problemas
