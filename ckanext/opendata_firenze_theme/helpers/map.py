"""Helper della mappa: predicati di formato, vista e risorsa."""

from .constants import GEO_FORMATS_UPPER, GEOJSON_FORMATS_UPPER, MAP_VIEW_TYPES
from .resource import odf_resource_has_map_view

# Viewer generico OpenLayers: quando c'e' anche `geojson_view` (dedicato, con
# supporto CRS) non va mostrato due volte sulla stessa risorsa. Usato dal
# comando di migrazione, non dai template.
GENERIC_MAP_VIEW_TYPES = frozenset(("geo_view", "geoview", "recline_map_view"))


def odf_format_is_geo(fmt):
    """True se il formato ha un'anteprima su mappa (chip "geo")."""
    return (fmt or "").strip().upper() in GEO_FORMATS_UPPER


def _is_geojson(res):
    return (res.get("format") or "").strip().upper() in GEOJSON_FORMATS_UPPER


def odf_dataset_map_resource(pkg, views_by_resource=None):
    """Risorsa per il pulsante "Vedi su mappa", preferendo GeoJSON con vista.

    Prima cerca un GeoJSON che abbia davvero una vista mappa, poi una qualsiasi
    risorsa geo con vista, infine un GeoJSON/geo anche senza vista (fallback per
    non far sparire il pulsante su dati vecchi o non ancora indicizzati).
    `views_by_resource` è lo snapshot della scheda: evita una
    `resource_view_list` per ogni risorsa geo.
    """
    resources = [
        res for res in (pkg.get("resources") or []) if odf_format_is_geo(res.get("format"))
    ]

    def has_map_view(res):
        if views_by_resource is None:
            return odf_resource_has_map_view(res)
        return odf_resource_has_map_view(res, views_by_resource.get(res.get("id")))

    has_view = {id(res): has_map_view(res) for res in resources}

    for res in resources:
        if _is_geojson(res) and has_view[id(res)]:
            return res
    for res in resources:
        if has_view[id(res)]:
            return res
    for res in resources:
        if _is_geojson(res):
            return res
    return resources[0] if resources else None


def odf_views_map_first(views):
    """Viste della risorsa con la mappa per prima (poi l'ordine originale)."""
    if not views:
        return []

    def is_map(view):
        return (view.get("view_type") or "").lower() in MAP_VIEW_TYPES

    return sorted(views, key=lambda view: 0 if is_map(view) else 1)


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_format_is_geo": odf_format_is_geo,
    "odf_views_map_first": odf_views_map_first,
}
