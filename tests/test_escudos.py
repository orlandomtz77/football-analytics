"""Pruebas de los escudos de TheSportsDB (sin red: buscador falso)."""

from football_analytics import escudos
from football_analytics.escudos import EQUIPOS_THESPORTSDB, actualizar_escudos, cargar_escudos


def test_ids_verificados_unicos_y_sin_equipos_dudosos():
    ids = [i for _, i in EQUIPOS_THESPORTSDB.values()]
    assert len(ids) == len(set(ids)) == 23
    assert "Monarcas" not in EQUIPOS_THESPORTSDB and "Lobos BUAP" not in EQUIPOS_THESPORTSDB


def test_actualizar_solo_acepta_el_id_verificado(tmp_path):
    def buscar_falso(busqueda, clave):
        assert clave == "clave-prueba"
        # Para "Atlas" llega primero otro equipo con el mismo nombre: no debe usarse.
        return [
            {"idTeam": "999", "strTeam": "Atlas (otro país)", "strBadge": "https://ejemplo.org/otro.png"},
            {"idTeam": EQUIPOS_THESPORTSDB.get("Atlas")[1] if busqueda == "Atlas" else "000",
             "strTeam": "Atlas", "strBadge": "https://r2.thesportsdb.com/atlas.png"},
        ]

    ruta = tmp_path / "escudos.csv"
    tabla = actualizar_escudos(ruta, clave="clave-prueba", buscar=buscar_falso, pausa=0)
    fila = tabla.set_index("equipo").loc["Atlas"]
    assert fila["escudo_url"] == "https://r2.thesportsdb.com/atlas.png"
    assert tabla.set_index("equipo").loc["Toluca", "escudo_url"] == ""  # no apareció su id verificado
    assert ruta.exists()


def test_cargar_escudos_ignora_vacios_y_archivo_faltante(tmp_path):
    ruta = tmp_path / "escudos.csv"
    ruta.write_text("equipo,id_thesportsdb,nombre_thesportsdb,escudo_url\n"
                    "Atlas,134195,Atlas,https://r2.thesportsdb.com/atlas.png\nToluca,134204,Toluca,\n", encoding="utf-8")
    assert cargar_escudos.__wrapped__(ruta) == {"Atlas": "https://r2.thesportsdb.com/atlas.png"}
    assert cargar_escudos.__wrapped__(tmp_path / "no_existe.csv") == {}


def test_tabla_real_y_html():
    reales = cargar_escudos()
    assert len(reales) == 23 and all(u.startswith("https://r2.thesportsdb.com/") for u in reales.values())
    assert escudos.escudo("Monarcas") is None and escudos.escudo_html("Monarcas") == ""
    assert 'alt="Toluca"' in escudos.escudo_html("Toluca")
