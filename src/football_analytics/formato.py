"""Formatos de texto para aficionados (récords, racha con íconos)."""

from __future__ import annotations

from collections.abc import Iterable

# Forma distinta además del color: no depende solo de distinguir verde/rojo.
ICONO_RESULTADO = {"G": "✅", "E": "➖", "P": "❌"}


def forma_con_iconos(resultados: Iterable[str]) -> str:
    """["G", "E", "P"] -> "✅ ➖ ❌"."""
    return " ".join(ICONO_RESULTADO[r] for r in resultados)


def record(ganados: int, empatados: int, perdidos: int) -> str:
    """Récord estilo medio deportivo: 8G-4E-2P."""
    return f"{ganados}G-{empatados}E-{perdidos}P"


def unir_nombres(nombres: list[str]) -> str:
    """["A"] -> "A"; ["A", "B"] -> "A y B"; ["A", "B", "C"] -> "A, B y C"."""
    if len(nombres) <= 1:
        return "".join(nombres)
    return ", ".join(nombres[:-1]) + " y " + nombres[-1]


def cantidad(n: int, singular: str, plural: str) -> str:
    """cantidad(1, "gol", "goles") -> "1 gol"; cantidad(3, ...) -> "3 goles"."""
    return f"{n} {singular if n == 1 else plural}"
