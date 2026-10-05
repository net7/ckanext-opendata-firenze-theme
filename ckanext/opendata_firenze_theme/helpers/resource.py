"""Helper della scheda risorsa: titoli dei pannelli vista, URL di download."""

import ckan.plugins.toolkit as toolkit

from . import _common
from .constants import VIEW_TITLES


def odf_resource_download_url(pkg, res):
    """URL di download di una singola risorsa (route CKAN per gli upload)."""
    return _common._resource_download_url(pkg, res)


def odf_resource_view_title(view):
    """Titolo del pannello di una vista risorsa (per tipo, o titolo della vista)."""
    view_type = (view.get("view_type") or "").lower()
    if view_type in VIEW_TITLES:
        return toolkit._(VIEW_TITLES[view_type])
    return view.get("title") or toolkit._("Anteprima")


def odf_resource_preview_url(pkg, res):
    """URL della prima vista di anteprima della risorsa, o '' se non ce ne sono.

    La modale "Vedi anteprima" della scheda dataset incorpora la prima vista
    CKAN (datatables_view/datastore per le tabelle, geoview/geojson_view per le
    mappe): lo stesso widget della scheda risorsa, senza cambiare pagina.
    """
    res_id = res.get("id")
    if not res_id:
        return ""
    try:
        views = toolkit.get_action("resource_view_list")({"ignore_auth": True}, {"id": res_id})
    except Exception:
        return ""
    if not views:
        return ""
    try:
        return toolkit.url_for(
            (pkg.get("type") or "dataset") + "_resource.view",
            id=pkg.get("name"),
            resource_id=res_id,
            view_id=views[0].get("id"),
        )
    except Exception:
        return ""
