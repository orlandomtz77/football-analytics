"""
config.py — ajustes que cambias seguido, sin tocar la lógica de las infografías.
(Los colores y efectos visuales están en estilo.py.)
Cualquier valor se puede sobreescribir al ejecutar; ver
`python -m football_analytics.infografias --help`.
"""

# ---- Mínimo de pases para dibujar una conexión entre dos jugadores ----------
# Súbelo si el mapa se ve muy cargado; bájalo si se ve vacío (partidos con poca data).
MINIMO_PASES_COMPLETADOS = 6        # red de pases completados (con flechas)
MINIMO_PASES_FALLIDOS = 2           # red de pases fallidos (con flechas)
MINIMO_PASES_COMPLETADOS_LINEAS = 4  # red de completados cuando usas --lineas

# ---- Qué partido/tramo se analiza -------------------------------------------
# True: las redes usan solo hasta el primer cambio del equipo (solo titulares).
# False: usa todo el partido.
CORTAR_EN_PRIMER_CAMBIO = True

# ---- Salida ----------------------------------------------------------------
TEMA_POR_DEFECTO = "oscuro"         # oscuro | rayados | cesped (ver estilo.py)
CARPETA_SALIDA = "salida"
CARPETA_CRUDOS = "data/raw/statsbomb"  # JSON descargados de StatsBomb (no se modifican ni se suben a Git)

# ---- Fuente ----------------------------------------------------------------
# StatsBomb Open Data no incluye Liga MX (ver data/README.md). Al publicar, StatsBomb pide citarlos
# como fuente y usar su logo.
STATSBOMB_BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
ATRIBUCION = "Datos: StatsBomb Open Data"
