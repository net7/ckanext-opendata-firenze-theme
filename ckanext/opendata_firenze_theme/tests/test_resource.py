"""Scheda risorsa: rendering e helper."""

import importlib.util

import pytest
from ckan.tests import factories

PLUGIN = "opendata_firenze_theme"
HAS_GEOVIEW = importlib.util.find_spec("ckanext.geoview") is not None


def _body(response):
    return response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_resource_page_renders(app):
    pkg = factories.Dataset(title="Dataset di prova")
    res = factories.Resource(package_id=pkg["id"], name="Risorsa di prova", format="CSV")
    body = _body(app.get(f"/dataset/{pkg['name']}/resource/{res['id']}"))
    assert "rtt-resource" in body
    assert "Risorsa di prova" in body
    assert "Risorsa del dataset" in body
    assert "Torna al dataset" in body
    assert "Scarica" in body
    assert "Dettagli della risorsa" in body
    # il contatore di download è stato rimosso (vedi adr/0007): il pulsante
    # "Scarica" resta, la metrica "Download: N" no.
    assert "Download:" not in body
    # ...e il link non ha la classe che il JS di CKAN usa per tracciare i click
    # sulle risorse: senza, nessun download viene registrato (adr/0007).
    assert "resource-url-analytics" not in body
    # senza viste e senza DataStore: il messaggio dice perché e invita al download
    assert "non è stata caricata nel DataStore" in body
    # l'azione editor non compare per l'anonimo
    assert "Gestisci" not in body


@pytest.mark.ckan_config("ckan.plugins", f"{PLUGIN} image_view")
@pytest.mark.usefixtures("with_plugins")
def test_resource_page_with_view(app):
    pkg = factories.Dataset(title="Dataset di prova")
    res = factories.Resource(
        package_id=pkg["id"],
        name="Risorsa di prova",
        format="PNG",
        url="http://example.com/a.png",
    )
    factories.ResourceView(resource_id=res["id"], title="Immagine", view_type="image_view")
    body = _body(app.get(f"/dataset/{pkg['name']}/resource/{res['id']}"))
    # la vista è renderizzata inline (image_view non è iframed) con il titolo
    # del pannello derivato dal tipo di vista
    assert "Nessuna anteprima disponibile" not in body
    assert "Anteprima" in body
    assert "http://example.com/a.png" in body


@pytest.mark.skipif(not HAS_GEOVIEW, reason="ckanext-geoview non installato")
@pytest.mark.ckan_config("ckan.plugins", f"{PLUGIN} shp_view")
@pytest.mark.usefixtures("with_plugins")
def test_shp_view_defaults_to_windows_1252(app):
    """I DBF del vecchio portale sono Windows-1252/Latin-1, non UTF-8."""
    pkg = factories.Dataset(title="Dataset di prova")
    res = factories.Resource(
        package_id=pkg["id"],
        name="Shapefile di prova",
        format="SHP",
        url="http://example.com/prova.zip",
    )
    view = factories.ResourceView(resource_id=res["id"], title="Shapefile", view_type="shp_view")

    body = _body(app.get(f"/dataset/{pkg['name']}/resource/{res['id']}/view/{view['id']}"))
    assert "windows-1252" in body


@pytest.mark.ckan_config("ckan.plugins", f"{PLUGIN} datatables_view")
@pytest.mark.usefixtures("with_plugins")
def test_resource_page_skips_datatables_view_without_datastore(app):
    """Una tabella senza DataStore non viene resa nella scheda risorsa."""
    pkg = factories.Dataset(title="Dataset di prova")
    res = factories.Resource(package_id=pkg["id"], name="Risorsa di prova", format="CSV")
    factories.ResourceView(resource_id=res["id"], title="Tabella", view_type="datatables_view")

    body = _body(app.get(f"/dataset/{pkg['name']}/resource/{res['id']}"))
    assert "non è stata caricata nel DataStore" in body
    assert 'data-module="data-viewer"' not in body


@pytest.mark.ckan_config("ckan.plugins", f"{PLUGIN} image_view")
@pytest.mark.usefixtures("with_plugins")
def test_resource_view_page_has_no_tracking_class(app):
    """La pagina della vista (template del core) non porta la classe di tracking.

    È la pagina che la modale "Vedi anteprima" della scheda dataset incorpora
    nell'iframe: un download da lì non deve registrare eventi `resource`
    (adr/0007). Il core la usa in `package/snippets/resource_view.html`.
    """
    pkg = factories.Dataset(title="Dataset di prova")
    res = factories.Resource(
        package_id=pkg["id"],
        name="Risorsa di prova",
        format="PNG",
        url="http://example.com/a.png",
    )
    view = factories.ResourceView(resource_id=res["id"], title="Immagine", view_type="image_view")
    body = _body(app.get(f"/dataset/{pkg['name']}/resource/{res['id']}/view/{view['id']}"))
    assert "http://example.com/a.png" in body
    assert "resource-url-analytics" not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_view_title_helper(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    assert helpers.odf_resource_view_title({"view_type": "geoview"}) == "Mappa"
    assert helpers.odf_resource_view_title({"view_type": "datatables_view"}) == "Anteprima dei dati"
    assert helpers.odf_resource_view_title({"view_type": "custom", "title": "Titolo"}) == "Titolo"
    assert helpers.odf_resource_view_title({"view_type": "custom"}) == "Anteprima"


PKG = {"name": "demo", "type": "dataset"}


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_preview_table(with_plugins, with_request_context):
    """Una vista tabellare utilizzabile finisce nella modale larga."""
    from ckanext.opendata_firenze_theme import helpers

    preview = helpers.odf_resource_preview(
        PKG,
        {"id": "r1", "format": "CSV", "datastore_active": True},
        [{"id": "v1", "view_type": "datatables_view"}],
    )
    assert preview == {
        "url": "/dataset/demo/resource/r1/view/v1",
        "view_type": "datatables_view",
        "kind": "table",
        "reason": "",
    }


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_views_filters_broken_datatables(with_plugins, with_request_context):
    """La pagina e la modale scartano una tabella senza DataStore."""
    from unittest import mock

    from ckanext.opendata_firenze_theme import helpers

    views = [
        {"id": "v1", "view_type": "datatables_view"},
        {"id": "v2", "view_type": "image_view"},
    ]
    with mock.patch.object(helpers.resource, "_datastore_available", return_value=False):
        usable = helpers.odf_resource_views(
            {"id": "r1", "format": "PNG", "datastore_active": False}, views
        )
    assert usable == [views[1]]


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_views_keeps_datatables_when_datastore_exists(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    views = [{"id": "v1", "view_type": "datatables_view"}]
    assert helpers.odf_resource_views({"id": "r1", "datastore_active": True}, views) == views


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_preview_map(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    preview = helpers.odf_resource_preview(
        PKG,
        {"id": "r1", "format": "GeoJSON"},
        [{"id": "v1", "view_type": "geojson_view"}],
    )
    assert preview["kind"] == "map"
    assert preview["view_type"] == "geojson_view"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_preview_csv_without_datastore_explains_why(with_plugins, with_request_context):
    """Il CSV fuori dal DataStore non ha tabella: il motivo è `datastore`."""
    from ckanext.opendata_firenze_theme import helpers

    preview = helpers.odf_resource_preview(
        PKG, {"id": "r1", "format": "CSV", "datastore_active": False}, []
    )
    assert preview == {"url": "", "view_type": "", "kind": "table", "reason": "datastore"}


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_preview_csv_in_datastore_without_view(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    preview = helpers.odf_resource_preview(
        PKG, {"id": "r1", "format": "CSV", "datastore_active": True}, []
    )
    assert preview["reason"] == "no-view"
    assert preview["kind"] == "table"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_preview_datastore_any_format_without_view(with_plugins, with_request_context):
    """In DataStore anche un XLSX può avere la tabella, se la vista manca."""
    from ckanext.opendata_firenze_theme import helpers

    preview = helpers.odf_resource_preview(
        PKG, {"id": "r1", "format": "XLSX", "datastore_active": True}, []
    )
    assert (preview["reason"], preview["kind"]) == ("no-view", "table")


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_preview_reason_by_format(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    cases = {
        "SHP": ("geo", "map"),
        "URL": ("external", "web"),
        "HTML": ("external", "web"),
        "RDF": ("unsupported", "file"),
    }
    for fmt, (reason, kind) in cases.items():
        preview = helpers.odf_resource_preview(PKG, {"id": "r1", "format": fmt}, [])
        assert (preview["reason"], preview["kind"]) == (reason, kind), fmt


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_preview_skips_broken_datatables_view(with_plugins, with_request_context):
    """Se la prima vista tabellare non ha DataStore, si prova la successiva."""
    from ckanext.opendata_firenze_theme import helpers

    preview = helpers.odf_resource_preview(
        PKG,
        {"id": "r1", "format": "PNG", "datastore_active": False},
        [
            {"id": "v1", "view_type": "datatables_view"},
            {"id": "v2", "view_type": "image_view"},
        ],
    )
    assert preview["view_type"] == "image_view"
    assert preview["kind"] == "media"
    assert preview["url"] == "/dataset/demo/resource/r1/view/v2"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_preview_accepts_views_without_querying(with_plugins, with_request_context):
    """La scheda risorsa passa `resource_views`: niente seconda query."""
    from unittest import mock

    from ckanext.opendata_firenze_theme import helpers

    with mock.patch.object(
        helpers.resource.toolkit, "get_action", side_effect=AssertionError("non deve chiamare")
    ):
        preview = helpers.odf_resource_preview(
            PKG,
            {"id": "r1", "format": "CSV", "datastore_active": False},
            [],
        )
    assert preview["reason"] == "datastore"
