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

from . import dataset, home
from .constants import DEFAULT_MOST_VIEWED_PERIOD


def _datasets(pkgs, cache):
    """Dati di un blocco a card: lista + fatti, condivisi fra i blocchi.

    La `cache` del collector conserva i fatti per id: un dataset che compare in
    più blocchi (es. "In evidenza" e "Ultimi pubblicati") viene calcolato una
    volta sola per render.
    """
    cached = cache.setdefault("facts", {})
    block_facts = {}
    for pkg in pkgs or []:
        if isinstance(pkg, dict):
            pkg_id = pkg.get("id")
            if pkg_id:
                if pkg_id not in cached:
                    cached[pkg_id] = dataset.odf_dataset_facts(pkg)
                block_facts[pkg_id] = cached[pkg_id]
    return {"datasets": pkgs, "facts": block_facts}


def _most_viewed(cache, block):
    """Dati di "I più consultati", con fallback se il tracking non risponde.

    `odf_most_viewed` ritorna `None` quando il DB di tracking non è
    disponibile: in quel caso si mostrano i più aggiornati, senza etichetta di
    periodo (il ranking non è quello del periodo) e senza conteggi del periodo.
    """
    period = block.get("period", DEFAULT_MOST_VIEWED_PERIOD)
    datasets = home.odf_most_viewed(4, period)
    if datasets is None:
        # Se anche la ricerca fallisce (il plugin tracking interroga lo stesso
        # DB), `_search` restituisce una lista vuota e il blocco si nasconde.
        datasets = home.odf_most_viewed_fallback(4)
        for pkg in datasets:
            pkg["views_period"] = 0
        return {**_datasets(datasets, cache), "period_label": ""}
    return {
        **_datasets(datasets, cache),
        "period_label": home.odf_most_viewed_label(period),
    }


# Contenuto di ogni blocco: id -> costruttore. La chiave deve coprire tutti i
# blocchi di `home_blocks.BLOCKS` (test in tests/test_home_sections.py).
#
# Il costruttore riceve `cache`, condivisa fra i blocchi dello stesso render,
# e il blocco configurato (per i campi che ne cambiano i dati, come il periodo).
_BUILDERS = {
    "hero": lambda cache, block: {"count": _total(cache)},
    "kpi": lambda cache, block: {"kpis": home.odf_home_kpis(total=_total(cache))},
    "featured": lambda cache, block: _datasets(home.odf_featured_datasets(7), cache),
    "latest": lambda cache, block: _datasets(home.odf_latest_datasets(6), cache),
    "themes": lambda cache, block: {"themes": home.odf_themes_visible()},
    "lod": lambda cache, block: _datasets(home.odf_lod_datasets(6), cache),
    "most_viewed": _most_viewed,
    "news": lambda cache, block: {"news": home.odf_news(3)},
}


def _total(cache):
    """Numero di dataset del catalogo, calcolato al massimo una volta."""
    if "total" not in cache:
        cache["total"] = home.odf_dataset_count()
    return cache["total"]


def odf_home_sections(blocks):
    """`{id_blocco: dati}` per i blocchi attivi, nell'ordine di `blocks`."""
    cache = {}
    return {block["id"]: _BUILDERS[block["id"]](cache, block) for block in blocks}


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_home_sections": odf_home_sections,
}
