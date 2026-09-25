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
