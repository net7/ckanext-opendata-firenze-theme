"""Contesto della scheda dataset: un solo punto che compone i dati della pagina.

La scheda (`templates/package/read.html`) riceve un valore con quattro
sotto-contesti: `header`, `resources`, `aside` e `series`. Ogni pannello legge
solo il proprio, invece di destrutturare un dict piatto da 18 chiavi.
"""

from . import dataset, resource, series
from . import map as map_helpers


def odf_dataset_page(pkg, tab="essenziale"):
    """Dati della scheda dataset per la vista `tab` ("essenziale"/"avanzata")."""
    facts = dataset.odf_dataset_facts(pkg)
    badges = dataset.odf_dataset_badges(pkg, facts=facts)
    info = series.odf_series_info(pkg)
    # Il pannello serie/revisioni esiste solo nella vista essenziale: sulla
    # tab avanzata non si pagano le ricerche delle revisioni.
    context = series.odf_series_context(pkg, info=info) if tab != "avanzata" else None
    # Le viste servono sia alle righe risorsa sia al pulsante mappa. Sulla tab
    # essenziale le righe ci sono: una sola acquisizione per tutte le risorse
    # (ADR 0012). Sulla tab avanzata le righe non esistono e il pulsante mappa
    # ha bisogno delle viste dei soli geodati: si usa il percorso senza snapshot.
    if tab == "avanzata":
        views_by_resource = {}
        map_resource = map_helpers.odf_dataset_map_resource(pkg)
    else:
        views_by_resource = resource.odf_resource_views_by_id(pkg)
        map_resource = map_helpers.odf_dataset_map_resource(pkg, views_by_resource)
    return {
        "header": {
            "theme": facts["theme"],
            "badges": badges,
            "is_realtime": facts["is_realtime"],
            "is_geo": facts["is_geo"],
            "serie": info["serie"],
            "serie_total": info["count"],
            "geometry": facts["geometry"],
            "uso": dataset.odf_pkg_extra(pkg, "uso"),
        },
        "resources": {
            "downloads": dataset.odf_dataset_downloads(pkg),
            "map_resource": map_resource,
            "views_by_resource": views_by_resource,
        },
        "aside": {
            "quality": dataset.odf_dataset_openness(pkg),
            "contact": dataset.odf_dataset_contact(pkg),
            "related": dataset.odf_dataset_related(pkg, theme=facts["theme"]),
        },
        "series": context,
        "tab": tab,
        "advanced": tab == "avanzata",
    }


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_dataset_page": odf_dataset_page,
}
