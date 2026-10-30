"""Carga de datos crudos de football-data.co.uk (archivo MEX.csv de Liga MX)."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

FUENTE_NOMBRE = "football-data.co.uk"
FUENTE_URL = "https://www.football-data.co.uk/mexico.php"

# Columnas de la fuente -> nombres del proyecto. Las cuotas de apuestas se descartan.
COLUMNAS_FUENTE = {
    "Season": "temporada",
    "Date": "fecha",
    "Time": "hora_fuente",
    "Home": "equipo_local",
    "Away": "equipo_visitante",
    "HG": "goles_local",
    "AG": "goles_visitante",
    "Res": "resultado",
}


def cargar_partidos_football_data(ruta: str | Path) -> pd.DataFrame:
    """Lee el CSV de football-data.co.uk y devuelve partidos con columnas del proyecto.

    `hora_fuente` se deja tal cual: la fuente no documenta la zona horaria
    (parece ser hora del Reino Unido).
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo de datos: {ruta}")

    crudo = pd.read_csv(ruta, encoding="utf-8-sig")
    faltantes = [c for c in COLUMNAS_FUENTE if c not in crudo.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas en {ruta.name}: {faltantes}")

    partidos = crudo[list(COLUMNAS_FUENTE)].rename(columns=COLUMNAS_FUENTE)
    partidos["fecha"] = pd.to_datetime(partidos["fecha"], format="%d/%m/%Y")
    _validar_resultado(partidos)
    return partidos


def _validar_resultado(partidos: pd.DataFrame) -> None:
    """Comprueba que la columna `resultado` (H/D/A) coincida con el marcador."""
    esperado = pd.Series("D", index=partidos.index)
    esperado = esperado.mask(partidos["goles_local"] > partidos["goles_visitante"], "H")
    esperado = esperado.mask(partidos["goles_local"] < partidos["goles_visitante"], "A")
    incoherentes = (esperado != partidos["resultado"]).sum()
    if incoherentes:
        raise ValueError(f"{incoherentes} partidos con resultado incoherente con el marcador.")


def ruta_metadatos(ruta_procesado: str | Path) -> Path:
    """Archivo JSON que acompaña al CSV procesado (misma carpeta y nombre)."""
    return Path(ruta_procesado).with_suffix(".meta.json")


def crear_metadatos(partidos: pd.DataFrame, ruta_crudo: Path) -> dict:
    """Describe de dónde salieron los datos y qué cubren."""
    return {
        "fuente": FUENTE_NOMBRE,
        "url": FUENTE_URL,
        "archivo_crudo": ruta_crudo.name,
        # La fecha de modificación del archivo crudo es la fecha de descarga.
        "fecha_obtencion": date.fromtimestamp(ruta_crudo.stat().st_mtime).isoformat(),
        "fecha_procesado": date.today().isoformat(),
        "partidos": int(len(partidos)),
        "fecha_min": partidos["fecha"].min().date().isoformat(),
        "fecha_max": partidos["fecha"].max().date().isoformat(),
    }


def cargar_partidos_procesados(ruta: str | Path) -> tuple[pd.DataFrame, dict | None]:
    """Lee el CSV procesado y sus metadatos (None si no existe el JSON)."""
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo procesado: {ruta}")
    partidos = pd.read_csv(ruta, parse_dates=["fecha"])
    meta = ruta_metadatos(ruta)
    metadatos = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else None
    return partidos, metadatos


def main() -> None:
    from football_analytics.cleaning import preparar_partidos

    parser = argparse.ArgumentParser(description="Procesa MEX.csv de football-data.co.uk.")
    parser.add_argument("entrada", type=Path, help="CSV crudo en data/raw/")
    parser.add_argument("salida", type=Path, help="CSV procesado en data/processed/")
    args = parser.parse_args()

    partidos = preparar_partidos(cargar_partidos_football_data(args.entrada))
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    partidos.to_csv(args.salida, index=False)
    metadatos = crear_metadatos(partidos, args.entrada)
    ruta_metadatos(args.salida).write_text(json.dumps(metadatos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(partidos)} partidos guardados en {args.salida}")


if __name__ == "__main__":
    main()
