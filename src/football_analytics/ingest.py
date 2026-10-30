"""Carga de datos crudos de football-data.co.uk (archivo MEX.csv de Liga MX)."""

from __future__ import annotations

import argparse
import json
import urllib.request
from collections.abc import Callable
from datetime import date
from pathlib import Path

import pandas as pd

from football_analytics.cleaning import preparar_partidos

FUENTE_NOMBRE = "football-data.co.uk"
FUENTE_URL = "https://www.football-data.co.uk/mexico.php"
FUENTE_CSV_URL = "https://www.football-data.co.uk/new/MEX.csv"

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


def procesar_archivo(entrada: Path, salida: Path) -> pd.DataFrame:
    """Carga el CSV crudo, lo limpia y guarda el procesado con sus metadatos."""
    partidos = preparar_partidos(cargar_partidos_football_data(entrada))
    salida.parent.mkdir(parents=True, exist_ok=True)
    partidos.to_csv(salida, index=False)
    metadatos = crear_metadatos(partidos, entrada)
    ruta_metadatos(salida).write_text(json.dumps(metadatos, ensure_ascii=False, indent=2), encoding="utf-8")
    return partidos


def descargar_url(url: str, destino: Path, timeout: int = 30) -> None:
    """Descarga `url` a `destino`. Lanza OSError (p. ej. URLError) si falla la red."""
    peticion = urllib.request.Request(url, headers={"User-Agent": "football-analytics (proyecto educativo)"})
    with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
        destino.write_bytes(respuesta.read())


def asegurar_datos(
    ruta_procesado: Path,
    carpeta_crudos: Path,
    descargar: Callable[[str, Path], None] = descargar_url,
) -> bool:
    """Si no existe el CSV procesado, descarga MEX.csv una vez y lo procesa.

    Devuelve True si descargó, False si los datos ya existían.
    El crudo se guarda con la fecha de descarga en el nombre y no se modifica después.
    Si la descarga o la validación fallan no queda ningún archivo a medias.
    """
    if ruta_procesado.exists():
        return False

    carpeta_crudos.mkdir(parents=True, exist_ok=True)
    crudo = carpeta_crudos / f"football-data_MEX_{date.today().isoformat()}.csv"
    temporal = crudo.with_suffix(".descargando")
    try:
        descargar(FUENTE_CSV_URL, temporal)
        cargar_partidos_football_data(temporal)  # valida antes de aceptar el archivo
        temporal.replace(crudo)
    finally:
        temporal.unlink(missing_ok=True)

    procesar_archivo(crudo, ruta_procesado)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Procesa MEX.csv de football-data.co.uk.")
    parser.add_argument("entrada", type=Path, help="CSV crudo en data/raw/")
    parser.add_argument("salida", type=Path, help="CSV procesado en data/processed/")
    args = parser.parse_args()

    partidos = procesar_archivo(args.entrada, args.salida)
    print(f"{len(partidos)} partidos guardados en {args.salida}")


if __name__ == "__main__":
    main()
