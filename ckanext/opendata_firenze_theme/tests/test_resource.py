"""Scheda risorsa: rendering e helper."""

import pytest
from ckan.tests import factories

PLUGIN = "opendata_firenze_theme"


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
    # senza viste: messaggio + invito al download
    assert "Nessuna anteprima disponibile" in body
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


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_view_title_helper(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    assert helpers.odf_resource_view_title({"view_type": "geoview"}) == "Mappa"
    assert helpers.odf_resource_view_title({"view_type": "datatables_view"}) == "Anteprima dei dati"
    assert helpers.odf_resource_view_title({"view_type": "custom", "title": "Titolo"}) == "Titolo"
    assert helpers.odf_resource_view_title({"view_type": "custom"}) == "Anteprima"
