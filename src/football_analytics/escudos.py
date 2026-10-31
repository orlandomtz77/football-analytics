"""Escudos de los equipos desde TheSportsDB (decisión del usuario, 2026-10-31).

Las imágenes no se guardan en el repositorio: la tabla data/reference/escudos_thesportsdb.csv solo tiene la
dirección de cada escudo y la app las carga desde TheSportsDB, sin modificarlas.

Condiciones (https://www.thesportsdb.com/docs_terms_of_use.php, revisadas el 2026-10-31):
- La clave gratuita ("123") es para proyectos de desarrollo; las apps publicadas requieren el plan de pago.
- Los logos son marcas de cada club: la API (gratuita o de pago) no otorga permiso para usarlos y deben
  mostrarse "tal cual". El usuario decidió usarlos con esta información (ver progreso.md).

Actualizar la tabla (descarga las direcciones de los escudos):
    $env:THESPORTSDB_API_KEY = "<clave>"   # opcional; sin ella usa la gratuita "123"
    python -m football_analytics.escudos
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

import pandas as pd

RUTA_ESCUDOS = Path(__file__).resolve().parents[2] / "data" / "reference" / "escudos_thesportsdb.csv"
FUENTE_ESCUDOS = "TheSportsDB"
FUENTE_ESCUDOS_URL = "https://www.thesportsdb.com"
URL_API = "https://www.thesportsdb.com/api/v1/json"

# Equipo (nombre en football-data.co.uk) -> (búsqueda en TheSportsDB, idTeam verificado a mano el 2026-10-31).
# Sin escudo: Monarcas (TheSportsDB lo mezcla con Atlético Morelia, otro club y otro escudo) y Lobos BUAP
# (no aparece; la única coincidencia es un equipo de básquetbol).
EQUIPOS_THESPORTSDB: dict[str, tuple[str, str]] = {
    "Club America": ("America", "134193"),
    "Guadalajara Chivas": ("Guadalajara Chivas", "134206"),
    "Cruz Azul": ("Cruz Azul", "134196"),
    "UNAM Pumas": ("UNAM", "134201"),
    "Tigres UANL": ("Tigres UANL", "134197"),
    "Monterrey": ("Monterrey", "134198"),
    "Toluca": ("Toluca", "134204"),
    "Atlas": ("Atlas", "134195"),
    "Club Leon": ("Leon", "134207"),
    "Pachuca": ("Pachuca", "134191"),
    "Santos Laguna": ("Santos Laguna", "134192"),
    "Club Tijuana": ("Tijuana", "134202"),
    "Queretaro": ("Queretaro", "134194"),
    "Puebla": ("Puebla", "134199"),
    "Necaxa": ("Necaxa", "135662"),
    "Atl. San Luis": ("Atletico San Luis", "136856"),
    "Juarez": ("Juarez", "136855"),
    "Veracruz": ("Veracruz", "134306"),
    "Mazatlan FC": ("Mazatlan FC", "139995"),
    "Atlante": ("Atlante", "134203"),
    "Leones Negros": ("Leones Negros", "134622"),
    "Chiapas": ("Chiapas", "134205"),
    "Dorados de Sinaloa": ("Dorados", "135739"),
}


def _buscar_equipos(busqueda: str, clave: str) -> list[dict]:
    """Equipos de TheSportsDB para una búsqueda; reintenta si la API limita las solicitudes (429)."""
    url = f"{URL_API}/{clave}/searchteams.php?t={urllib.parse.quote(busqueda)}"
    peticion = urllib.request.Request(url, headers={"User-Agent": "football-analytics (proyecto educativo)"})
    for intento in range(4):
        try:
            with urllib.request.urlopen(peticion, timeout=30) as respuesta:
                return json.load(respuesta).get("teams") or []
        except urllib.error.HTTPError as error:
            if error.code != 429:
                raise
            time.sleep(20 * (intento + 1))
    raise OSError(f"TheSportsDB sigue limitando las solicitudes para '{busqueda}'.")


def actualizar_escudos(
    ruta: Path = RUTA_ESCUDOS,
    clave: str | None = None,
    buscar: Callable[[str, str], list[dict]] = _buscar_equipos,
    pausa: float = 6.0,
) -> pd.DataFrame:
    """Consulta TheSportsDB y guarda la tabla de escudos. Solo acepta el idTeam verificado de cada equipo."""
    clave = clave or os.environ.get("THESPORTSDB_API_KEY") or "123"
    filas = []
    for equipo, (busqueda, id_esperado) in EQUIPOS_THESPORTSDB.items():
        encontrado = next((t for t in buscar(busqueda, clave) if t.get("idTeam") == id_esperado), None)
        filas.append({
            "equipo": equipo,
            "id_thesportsdb": id_esperado,
            "nombre_thesportsdb": encontrado["strTeam"] if encontrado else "",
            "escudo_url": (encontrado or {}).get("strBadge") or "",
        })
        time.sleep(pausa)  # la clave gratuita admite pocas solicitudes por minuto
    tabla = pd.DataFrame(filas)
    tabla.to_csv(ruta, index=False)
    return tabla


@lru_cache(maxsize=1)
def cargar_escudos(ruta: str | Path = RUTA_ESCUDOS) -> dict[str, str]:
    """Equipo -> dirección del escudo. Diccionario vacío si la tabla no existe."""
    try:
        tabla = pd.read_csv(ruta, dtype=str).fillna("")
    except FileNotFoundError:
        return {}
    return {fila.equipo: fila.escudo_url for fila in tabla.itertuples() if fila.escudo_url.startswith("https://")}


def escudo(equipo: str) -> str | None:
    """Dirección del escudo del equipo, o None si no tiene (p. ej. Monarcas o Lobos BUAP)."""
    return cargar_escudos().get(equipo)


def escudo_html(equipo: str, tamano: int = 32) -> str:
    """<img> en línea con el escudo (texto alternativo: el nombre); cadena vacía si no hay escudo."""
    url = escudo(equipo)
    if not url:
        return ""
    return (f'<img src="{url}" alt="{equipo}" width="{tamano}" height="{tamano}" '
            f'style="vertical-align:middle;margin-right:0.4em;object-fit:contain">')


if __name__ == "__main__":
    resultado = actualizar_escudos()
    print(resultado.to_string(index=False))
    faltan = resultado[resultado["escudo_url"] == ""]["equipo"].tolist()
    print("Sin escudo:", faltan or "ninguno")
