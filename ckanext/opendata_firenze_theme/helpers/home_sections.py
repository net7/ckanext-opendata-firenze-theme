"""Dati dei blocchi della home, raccolti una volta sola per render.

I template dei blocchi non chiamano più gli helper: ricevono `block_data` con i
dati già pronti. Il collettore è l'unico punto che sa **quali** dati serve ogni
blocco e con quali limiti; i blocchi restano renderer puri e l'ordine/lo stato
dei blocchi resta quello configurato dagli operatori (ADR 0008).

Il nome `block_data` (non `section`) evita la collisione con il macro
`section` importato dai blocchi.

Il conteggio dei dataset è condiviso fra hero e KPI: senza il collettore erano
due `package_search` identici.
"""

from . import home

# Contenuto di ogni blocco: id -> costruttore. La chiave deve coprire tutti i
# blocchi di `home_blocks.BLOCKS` (test in tests/test_home_sections.py).
#
# Il costruttore riceve `cache`, condivisa fra i blocchi dello stesso render.
_BUILDERS = {
    "hero": lambda cache: {"count": _total(cache)},
    "kpi": lambda cache: {"kpis": home.odf_home_kpis(total=_total(cache))},
    "featured": lambda cache: {"datasets": home.odf_featured_datasets(7)},
    "latest": lambda cache: {"datasets": home.odf_latest_datasets(6)},
    "themes": lambda cache: {"themes": home.odf_themes_visible()},
    "lod": lambda cache: {"datasets": home.odf_lod_datasets(6)},
    "most_viewed": lambda cache: {"datasets": home.odf_most_viewed(4)},
    "news": lambda cache: {"news": home.odf_news(3)},
}


def _total(cache):
    """Numero di dataset del catalogo, calcolato al massimo una volta."""
    if "total" not in cache:
        cache["total"] = home.odf_dataset_count()
    return cache["total"]


def odf_home_sections(blocks):
    """`{id_blocco: dati}` per i blocchi attivi, nell'ordine di `blocks`."""
    cache = {}
    return {block["id"]: _BUILDERS[block["id"]](cache) for block in blocks}


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_home_sections": odf_home_sections,
}
