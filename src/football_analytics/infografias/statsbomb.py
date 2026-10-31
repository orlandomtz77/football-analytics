"""Eventos y alineaciones de StatsBomb Open Data.

La descarga y la transformación están separadas: `eventos_a_dataframe` y `apodos` trabajan con el JSON ya
leído (se prueban sin red); `cargar_partido` y `cargar_apodos` descargan una sola vez a la carpeta de
crudos y reutilizan ese archivo después. Cuando haya una fuente de eventos de Liga MX, basta con producir
las mismas columnas que `eventos_a_dataframe`.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pandas as pd

from football_analytics.infografias import config
from football_analytics.ingest import descargar_url

COLUMNAS = ["tipo", "equipo", "jugador", "minuto", "x", "y", "periodo",
            "xg", "resultado", "receptor", "pase_ok", "x_fin", "y_fin"]


def eventos_a_dataframe(eventos: list[dict]) -> pd.DataFrame:
    """Aplana los eventos a una tabla. Descarta el periodo 5 (tanda de penales)."""
    filas = []
    for e in eventos:
        loc = e.get("location") or [None, None]
        fila = {
            "tipo": e["type"]["name"],
            "equipo": e["team"]["name"],
            "jugador": (e.get("player") or {}).get("name"),
            "minuto": e["minute"],
            "x": loc[0],
            "y": loc[1],
            "periodo": e["period"],
        }
        if e["type"]["name"] == "Shot":
            s = e["shot"]
            fila.update(xg=s.get("statsbomb_xg"), resultado=s["outcome"]["name"])
        if e["type"]["name"] == "Pass":
            p = e["pass"]
            fin = p.get("end_location") or [None, None]
            fila.update(
                receptor=(p.get("recipient") or {}).get("name"),
                pase_ok="outcome" not in p,  # sin 'outcome' = pase completado
                x_fin=fin[0], y_fin=fin[1],
            )
        filas.append(fila)
    df = pd.DataFrame(filas, columns=COLUMNAS)
    return df[df.periodo <= 4].reset_index(drop=True)  # periodo 5 = tanda de penales


def apodos(lineups: list[dict]) -> dict:
    """StatsBomb usa nombres legales completos; las alineaciones traen el apodo (o se usa el apellido)."""
    return {
        j["player_name"]: j["player_nickname"] or j["player_name"].split()[-1]
        for eq in lineups for j in eq["lineup"]
    }


def marcador(df: pd.DataFrame, equipos: list[str]) -> str:
    """'A 2 - 1 B' sin la tanda de penales. Cuenta goles de tiro y autogoles a favor ('Own Goal For')."""
    goles_tiro = (df.tipo == "Shot") & (df.resultado == "Goal")
    autogol_a_favor = df.tipo == "Own Goal For"
    goles = df[goles_tiro | autogol_a_favor].groupby("equipo").size()
    return f"{equipos[0]} {goles.get(equipos[0], 0)} - {goles.get(equipos[1], 0)} {equipos[1]}"


def _json_en_cache(url: str, ruta: Path, descargar: Callable[[str, Path], None]) -> list:
    """Lee `ruta`; si no existe, descarga `url` una vez (sin dejar archivos a medias si falla)."""
    if not ruta.exists():
        ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = ruta.with_suffix(".descargando")
        try:
            descargar(url, temporal)
            json.loads(temporal.read_text(encoding="utf-8"))  # valida antes de aceptar el archivo
            temporal.replace(ruta)
        finally:
            temporal.unlink(missing_ok=True)
    return json.loads(ruta.read_text(encoding="utf-8"))


def cargar_partido(
    match_id: int, carpeta: Path = Path(config.CARPETA_CRUDOS), descargar: Callable[[str, Path], None] = descargar_url
) -> pd.DataFrame:
    eventos = _json_en_cache(f"{config.STATSBOMB_BASE}/events/{match_id}.json",
                             carpeta / "events" / f"{match_id}.json", descargar)
    return eventos_a_dataframe(eventos)


def cargar_apodos(
    match_id: int, carpeta: Path = Path(config.CARPETA_CRUDOS), descargar: Callable[[str, Path], None] = descargar_url
) -> dict:
    lineups = _json_en_cache(f"{config.STATSBOMB_BASE}/lineups/{match_id}.json",
                             carpeta / "lineups" / f"{match_id}.json", descargar)
    return apodos(lineups)
