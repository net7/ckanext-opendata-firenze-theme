"""Helper della mappa: layer WMS e predicati di formato, vista e risorsa.

Il viewer WMS di `ckanext-geoview` accetta un fragment `#layer` sull'URL della
risorsa; i WMS del vecchio portale dichiarano il layer solo nella descrizione
("Il Layer di riferimento è ..."). La risoluzione sta qui, in Python, così è
testabile senza un browser e la patch JS si limita a leggere il valore già
risolto (vedi ADR 0018 nel repo `opendata-firenze-config`).
"""

import re

from .constants import GEO_FORMATS_UPPER, GEOJSON_FORMATS_UPPER, MAP_VIEW_TYPES
from .resource import odf_resource_has_map_view

# Viewer generico OpenLayers: quando c'e' anche `geojson_view` (dedicato, con
# supporto CRS) non va mostrato due volte sulla stessa risorsa. Usato dal
# comando di migrazione, non dai template.
GENERIC_MAP_VIEW_TYPES = frozenset(("geo_view", "geoview", "recline_map_view"))

# Formati tabellari che datatables_view sa leggere dal DataStore.
TABULAR_FORMATS = frozenset(("CSV", "TSV"))
# Formati che sono un collegamento a una pagina/servizio, non un file.
EXTERNAL_FORMATS = frozenset(("URL", "HTML", "WEB"))

WMS_LAYER_RE = re.compile(
    r"Layer di riferimento\s*(?:è|e'|:)\s*([A-Za-z0-9_.:-]+)",
    re.IGNORECASE,
)


def is_geo_format(fmt):
    """True se il formato ha un'anteprima su mappa (chip "geo")."""
    return (fmt or "").strip().upper() in GEO_FORMATS_UPPER


def odf_format_is_geo(fmt):
    """Alias pubblico del predicato di formato geo."""
    return is_geo_format(fmt)


def is_map_view(view_type):
    """True se il tipo di vista è una mappa."""
    return (view_type or "").lower() in MAP_VIEW_TYPES


def preview_kind(view_type):
    """Famiglia della vista: decide il titolo e la larghezza della modale."""
    view_type = (view_type or "").lower()
    if view_type in ("datatables_view", "datastore"):
        return "table"
    if is_map_view(view_type):
        return "map"
    if view_type in ("webpage_view", "web_view", "html_view"):
        return "web"
    if view_type in ("text_view", "officedocs_view", "pdf_view"):
        return "doc"
    if view_type in ("image_view", "audio_view", "video_view"):
        return "media"
    return "file"


def preview_format_kind(res):
    """Famiglia della risorsa quando non c'è una vista da cui dedurla."""
    fmt = ((res or {}).get("format") or "").strip().upper()
    if (res or {}).get("datastore_active") or fmt in TABULAR_FORMATS:
        return "table"
    if is_geo_format(fmt):
        return "map"
    if fmt in EXTERNAL_FORMATS:
        return "web"
    return "file"


def preview_reason(res):
    """Perché una risorsa senza viste non ha l'anteprima, per il messaggio."""
    fmt = ((res or {}).get("format") or "").strip().upper()
    if (res or {}).get("datastore_active"):
        return "no-view"
    if fmt in TABULAR_FORMATS:
        return "datastore"
    if is_geo_format(fmt):
        return "geo"
    if fmt in EXTERNAL_FORMATS:
        return "external"
    return "unsupported"


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

    return sorted(views, key=lambda view: 0 if is_map_view(view.get("view_type")) else 1)


def odf_wms_layer(res):
    """Layer WMS della risorsa: fragment `#layer`, poi descrizione legacy.

    Il fragment ha la precedenza perché è una scelta esplicita sull'URL; la
    descrizione è l'adattatore per i dati harvestati dal vecchio portale.
    Restituisce None quando la risorsa non dichiara un layer.
    """
    url = (res or {}).get("url") or ""
    if "#" in url:
        layer = url.split("#", 1)[1].strip()
        if layer:
            return layer

    match = WMS_LAYER_RE.search((res or {}).get("description") or "")
    return match.group(1).rstrip(".,;") if match else None


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_wms_layer": odf_wms_layer,
    "odf_format_is_geo": odf_format_is_geo,
    "odf_views_map_first": odf_views_map_first,
}
