"""Specializzazione viewer: GeoJSON solo su `geojson_view`.

La patch a `ckanext-geoview` toglie `geojson` dai formati del viewer generico
OpenLayers (che ignora il `crs`) e aggiunge il fallback dall'estensione URL a
`geojson_view`. Il modulo viene saltato dove geoview non e' installato.
"""

import pytest

pytest.importorskip("ckanext.geoview")

from ckan.lib import datapreview  # noqa: E402
from ckan.lib.datapreview import add_views_to_resource  # noqa: E402
from ckan.tests import factories  # noqa: E402

from ckanext.geoview.plugin import GeoJSONView, OLGeoView  # noqa: E402

SITE_URL = "http://test.ckan.net"

# La specializzazione GeoJSON vive nella patch 0003 di opendata-firenze-config,
# non nell'estensione upstream: la CI del tema installa `ckanext-geoview` non
# patchato. I test che asseriscono il comportamento specializzato si saltano
# quando la patch non c'e' (in locale c'e', perche' lo stack dev la applica).
GEOVIEW_PATCHED = "geojson" not in OLGeoView.GEOVIEW_FORMATS
requires_patch_0003 = pytest.mark.skipif(
    not GEOVIEW_PATCHED,
    reason="richiede la patch 0003 di opendata-firenze-config",
)


def _resource(url, fmt=None):
    resource = {"url": url}
    if fmt is not None:
        resource["format"] = fmt
    return {"resource": resource}


@pytest.mark.ckan_config("ckan.site_url", SITE_URL)
@requires_patch_0003
def test_geo_view_does_not_claim_geojson(with_request_context):
    """Il viewer generico lascia i GeoJSON a `geojson_view`."""
    assert OLGeoView().can_view(_resource(f"{SITE_URL}/a.geojson")) is False


@pytest.mark.ckan_config("ckan.site_url", SITE_URL)
def test_geo_view_keeps_the_other_formats(with_request_context):
    """La specializzazione non deve far sparire gli altri formati supportati."""
    view = OLGeoView()
    view.proxy_enabled = True
    assert view.can_view(_resource(f"{SITE_URL}/a", "Esri Rest")) is True
    assert view.can_view(_resource(f"{SITE_URL}/a.wms", "WMS")) is True
    assert view.can_view(_resource(f"{SITE_URL}/a.wms")) is True


@pytest.mark.ckan_config("ckan.site_url", SITE_URL)
@requires_patch_0003
def test_geojson_view_infers_the_format_from_the_url(with_request_context):
    """Un GeoJSON senza `format` ma con URL `.geojson` ha comunque la mappa."""
    view = GeoJSONView()
    view.proxy_enabled = True
    assert view.can_view(_resource(f"{SITE_URL}/a.geojson")) is True


@pytest.mark.ckan_config(
    "ckan.plugins", "opendata_firenze_theme geo_view geojson_view resource_proxy"
)
@pytest.mark.usefixtures("with_plugins")
def test_default_views_config_lists_both_plugins(monkeypatch):
    """La config dei default view alimenta entrambi i plugin."""
    monkeypatch.setitem(
        datapreview.config, "ckan.views.default_views", ["geo_view", "geojson_view"]
    )
    assert [p.info()["name"] for p in datapreview.get_default_view_plugins()] == [
        "geo_view",
        "geojson_view",
    ]


@pytest.mark.ckan_config(
    "ckan.plugins", "opendata_firenze_theme geo_view geojson_view resource_proxy"
)
@pytest.mark.usefixtures("with_plugins", "with_request_context")
@pytest.mark.parametrize(
    ("fmt", "expected"),
    (
        pytest.param("GeoJSON", "geojson_view", marks=requires_patch_0003),
        ("WMS", "geo_view"),
    ),
)
def test_default_views_creates_the_specialized_view(fmt, expected):
    """Il percorso di creazione crea una sola vista per formato."""
    pkg = factories.Dataset()
    url = f"{SITE_URL}/a.{fmt.lower()}"
    res = factories.Resource(package_id=pkg["id"], format=fmt, url=url)

    created = add_views_to_resource(
        {"user": "test", "ignore_auth": True},
        {"id": res["id"], "package_id": pkg["id"], "format": fmt, "url": url},
        dataset_dict=pkg,
        view_types=["geo_view", "geojson_view"],
    )

    assert [view["view_type"] for view in created] == [expected]
