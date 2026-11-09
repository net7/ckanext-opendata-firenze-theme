"""Contesto della scheda dataset: un solo punto che compone i dati della pagina.

La scheda (`templates/package/read.html`) non chiama più una decina di helper
in Jinja: riceve i dati già composti. La ricerca della serie è fatta una volta
e riusata dal contesto (prima era una convenzione del template).
"""

from . import catalog, dataset, series


def odf_dataset_page(pkg, tab="essenziale"):
    """Dati della scheda dataset per la vista `tab` ("essenziale"/"avanzata")."""
    badges = dataset.odf_dataset_badges(pkg)
    info = series.odf_series_info(pkg)
    # Il pannello serie/revisioni esiste solo nella vista essenziale: sulla
    # tab avanzata non si pagano le ricerche delle revisioni.
    context = series.odf_series_context(pkg, info=info) if tab != "avanzata" else None
    return {
        "theme": catalog.odf_package_theme(pkg),
        "badges": badges,
        "is_realtime": any(badge["kind"] == "realtime" for badge in badges),
        "is_geo": any(badge["kind"] == "geo" for badge in badges),
        "downloads": dataset.odf_dataset_downloads(pkg),
        "quality": dataset.odf_dataset_openness(pkg),
        "map_resource": dataset.odf_dataset_map_resource(pkg),
        "series": context,
        "serie": info["serie"],
        "serie_total": info["count"],
        "contact": dataset.odf_dataset_contact(pkg),
        "related": dataset.odf_dataset_related(pkg),
        "geometry": dataset.odf_dataset_geometry(pkg),
        "uso": dataset.odf_pkg_extra(pkg, "uso"),
        "tab": tab,
        "advanced": tab == "avanzata",
    }


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_dataset_page": odf_dataset_page,
}
