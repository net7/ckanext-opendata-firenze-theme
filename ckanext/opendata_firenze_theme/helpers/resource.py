"""Helper della risorsa: link, nome file, separatore, viste.

Un solo punto per la regola di download (upload CKAN oppure URL esterna valida)
e per le proprietà della singola risorsa; la scheda dataset usa questi helper
anche per il menu "Scarica" e il pannello serie.
"""

from urllib.parse import unquote, urlsplit

import ckan.lib.helpers as ckan_h
import ckan.plugins.toolkit as toolkit

from . import _common
from .constants import GEO_FORMATS_UPPER, MAP_VIEW_TYPES, VIEW_TITLES


def odf_resource_download_url(pkg, res):
    """URL di download della risorsa.

    Per gli upload si usa la route CKAN (`resource.download`); per le risorse
    esterne solo un URL valido, altrimenti '' (niente link rotti).
    """
    if (res or {}).get("url_type") == "upload":
        try:
            return toolkit.url_for(
                "resource.download", id=pkg.get("name"), resource_id=res.get("id")
            )
        except Exception:
            return res.get("url") or ""
    url = (res or {}).get("url") or ""
    return url if url and ckan_h.is_url(url) else ""


def odf_resource_view_title(view):
    """Titolo del pannello di una vista risorsa (per tipo, o titolo della vista)."""
    view_type = (view.get("view_type") or "").lower()
    if view_type in VIEW_TITLES:
        return toolkit._(VIEW_TITLES[view_type])
    return view.get("title") or toolkit._("Anteprima")


# Formati tabellari che datatables_view sa leggere dal DataStore.
TABULAR_FORMATS = frozenset(("CSV", "TSV"))
# Formati che sono un collegamento a una pagina/servizio, non un file.
EXTERNAL_FORMATS = frozenset(("URL", "HTML", "WEB"))


def _preview_kind(view_type):
    """Famiglia della vista: decide il titolo e la larghezza della modale."""
    view_type = (view_type or "").lower()
    if view_type in ("datatables_view", "datastore"):
        return "table"
    if view_type in MAP_VIEW_TYPES:
        return "map"
    if view_type in ("webpage_view", "web_view", "html_view"):
        return "web"
    if view_type in ("text_view", "officedocs_view", "pdf_view"):
        return "doc"
    if view_type in ("image_view", "audio_view", "video_view"):
        return "media"
    return "file"


def _preview_format_kind(res):
    """Famiglia della risorsa quando non c'è una vista da cui dedurla."""
    fmt = ((res or {}).get("format") or "").strip().upper()
    if (res or {}).get("datastore_active") or fmt in TABULAR_FORMATS:
        return "table"
    if fmt in GEO_FORMATS_UPPER:
        return "map"
    if fmt in EXTERNAL_FORMATS:
        return "web"
    return "file"


def _preview_reason(res):
    """Perché una risorsa senza viste non ha l'anteprima, per il messaggio."""
    fmt = ((res or {}).get("format") or "").strip().upper()
    if (res or {}).get("datastore_active"):
        return "no-view"
    if fmt in TABULAR_FORMATS:
        return "datastore"
    if fmt in GEO_FORMATS_UPPER:
        return "geo"
    if fmt in EXTERNAL_FORMATS:
        return "external"
    return "unsupported"


def _resource_views(res):
    res_id = (res or {}).get("id")
    if not res_id:
        return []
    try:
        views = toolkit.get_action("resource_view_list")({"ignore_auth": True}, {"id": res_id})
    except Exception:
        return []
    return views or []


def _is_datatable_view(view):
    return (view.get("view_type") or "").lower() in ("datatables_view", "datastore")


def _datastore_available(res):
    """DataStore disponibile per una datatables_view.

    Il flag `datastore_active=True` è il contratto di CKAN e vale come prova:
    non aggiungiamo una query per ogni tabella caricata. Se invece il flag è
    `False` ma esiste una vista tabellare, il flag può essere stantio (es.
    tabella caricata fuori da xloader): in quel caso verifichiamo con
    `datastore_info`.
    """
    res_id = (res or {}).get("id")
    if not res_id:
        return False
    if (res or {}).get("datastore_active"):
        return True
    try:
        toolkit.get_action("datastore_info")(
            {"ignore_auth": True},
            {"id": res_id, "include_meta": False, "include_fields_schema": False},
        )
        return True
    except Exception:
        return False


def odf_resource_views(res, views):
    """Viste utilizzabili nella pagina/modale: scarta le tabelle senza DataStore."""
    usable = []
    datastore_ok = None
    for view in views or []:
        if _is_datatable_view(view):
            if datastore_ok is None:
                datastore_ok = _datastore_available(res)
            if not datastore_ok:
                continue
        usable.append(view)
    return usable


def odf_resource_preview(pkg, res, views=None):
    """Anteprima della risorsa: URL, tipo di vista e motivo dello stato vuoto.

    La modale "Vedi anteprima" della scheda dataset incorpora la prima vista
    CKAN utilizzabile (datatables_view/datastore per le tabelle, geoview/
    geojson_view per le mappe): lo stesso widget della scheda risorsa, senza
    cambiare pagina.

    Se non c'è una vista, `reason` dice perché: `datastore` (tabella non
    caricata), `no-view` (dati nel DataStore ma vista non configurata), `geo`
    (nessun visualizzatore geografico), `external` (solo un collegamento) o
    `unsupported` (formato senza visualizzatore). Le viste `datatables_view`
    senza DataStore non vengono incorporate: mostrerebbero un errore CKAN.
    """
    if views is None:
        views = _resource_views(res)

    usable = odf_resource_views(res, views)
    if not usable:
        if views:
            return {"url": "", "view_type": "", "kind": "table", "reason": "datastore"}
        return {
            "url": "",
            "view_type": "",
            "kind": _preview_format_kind(res),
            "reason": _preview_reason(res),
        }

    view = usable[0]
    view_type = (view.get("view_type") or "").lower()
    try:
        url = toolkit.url_for(
            (pkg.get("type") or "dataset") + "_resource.view",
            id=pkg.get("name"),
            resource_id=res.get("id"),
            view_id=view.get("id"),
        )
    except Exception:
        url = ""
    return {
        "url": url,
        "view_type": view_type,
        "kind": _preview_kind(view_type),
        "reason": "" if url else "generic",
    }


def odf_resource_preview_url(pkg, res):
    """URL della prima vista di anteprima della risorsa, o '' se non ce ne sono."""
    return odf_resource_preview(pkg, res)["url"]


def odf_views_map_first(views):
    """Viste della risorsa con la mappa per prima (poi l'ordine originale)."""
    if not views:
        return []

    def _is_map(view):
        return (view.get("view_type") or "").lower() in MAP_VIEW_TYPES

    return sorted(views, key=lambda view: 0 if _is_map(view) else 1)


# Estensioni di script lato server: un URL che termina cosi' non e' un nome di
# file da mostrare (es. `download.php?id=…` del vecchio portale).
_NON_FILE_EXTENSIONS = frozenset(("php", "asp", "aspx", "jsp", "cgi", "pl", "do"))


def odf_resource_filename(res):
    """Nome file della risorsa (basename dell'URL) se ne ha uno, altrimenti ''.

    Si mostra solo quando l'URL termina con un nome di file vero (estensione,
    esclusi gli script lato server): per i link generici (WMS, pagine web,
    `download.php`) il nome non esiste e non va inventato.
    """
    path = urlsplit((res or {}).get("url") or "").path
    name = unquote(path.rsplit("/", 1)[-1]) if path else ""
    if "." not in name:
        return ""
    return "" if name.rsplit(".", 1)[-1].lower() in _NON_FILE_EXTENSIONS else name


# Etichette italiane dei separatori CSV riconosciuti.
_SEPARATOR_LABELS = {
    ";": "punto e virgola",
    ",": "virgola",
    "\t": "tabulazione",
    "|": "barra verticale",
}


def odf_resource_separator(pkg, res):
    """Separatore di campo di una risorsa CSV, dall'extra `separatore` del dataset.

    Non si deduce dal contenuto: se il dataset non dichiara l'extra (o la
    risorsa non è CSV) non si mostra nulla, per non inventare un dato.
    """
    if ((res or {}).get("format") or "").strip().upper() != "CSV":
        return ""
    sep = (_common.pkg_field(pkg, "separatore") or "").strip()
    if not sep:
        return ""
    label = _SEPARATOR_LABELS.get(sep, sep)
    return toolkit._("Separatore di campo: «{sep}» ({label})").format(
        sep="TAB" if sep == "\t" else sep, label=label
    )


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_resource_download_url": odf_resource_download_url,
    "odf_resource_view_title": odf_resource_view_title,
    "odf_resource_preview": odf_resource_preview,
    "odf_resource_views": odf_resource_views,
    "odf_resource_filename": odf_resource_filename,
    "odf_resource_separator": odf_resource_separator,
    "odf_views_map_first": odf_views_map_first,
}
