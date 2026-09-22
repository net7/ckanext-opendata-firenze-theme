"""Rendering del catalogo e helper del tema per i package."""

import pytest

PLUGIN = "opendata_firenze_theme"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_catalog_renders(app):
    response = app.get("/dataset")
    assert response.status_code == 200
    body = response.body
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    assert "rtt-catalog" in body
    assert "rtt-facets" in body
    assert "Catalogo" in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_catalog_no_results(app):
    response = app.get("/dataset?q=zzzznonesistedataset")
    assert response.status_code == 200
    body = response.body
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    assert "rtt-noresults" in body


def test_package_theme_helper():
    from ckanext.opendata_firenze_theme import helpers

    base = "http://publications.europa.eu/resource/authority/data-theme/"
    assert helpers.odf_package_theme({}) is None
    assert helpers.odf_package_theme({"theme": base + "ENVI"}) == "ENVI"
    assert helpers.odf_package_theme({"extras": [{"key": "theme", "value": '["%sTRAN"]' % base}]}) == "TRAN"
    # OP_DATPRO (default dcatapit = "Other") non e' uno dei 13 temi
    assert helpers.odf_package_theme({"extras": [{"key": "theme", "value": '["%sOP_DATPRO"]' % base}]}) is None


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_catalog_facets_active_and_sort(with_plugins, app):
    """Con un filtro in URL il gruppo mostra il chip attivo + "Azzera tutto"."""
    from flask import render_template_string

    facets = {
        "res_format": {
            "title": "res_format",
            "items": [
                {"name": "CSV", "display_name": "CSV", "count": 3},
                {"name": "SHP", "display_name": "SHP", "count": 1},
            ],
        }
    }
    src = "{% include 'snippets/opendata_firenze_theme/catalog/facets.html' %}"
    with app.flask_app.test_request_context("/dataset?res_format=CSV"):
        html = render_template_string(src, search_facets=facets, q="", sort_by_selected="")
    assert "Formato dei file" in html
    assert "rtt-facets__chip" in html
    assert "rtt-facets__clear" in html
    assert "rtt-sort" in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_catalog_facets_dedupe_labels(with_plugins, app):
    """`theme` e `dcat_theme` hanno la stessa etichetta: un solo gruppo."""
    from flask import render_template_string

    items = [{"name": "ENVI", "display_name": "Ambiente", "count": 1}]
    facets = {
        "theme": {"title": "theme", "items": items},
        "dcat_theme": {"title": "dcat_theme", "items": items},
    }
    src = "{% include 'snippets/opendata_firenze_theme/catalog/facets.html' %}"
    with app.flask_app.test_request_context("/dataset"):
        html = render_template_string(src, search_facets=facets, q="", sort_by_selected="")
    assert html.count("rtt-facet__trigger") == 1


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_catalog_no_add_button_anonymous(app):
    """Il pulsante "Aggiungi dataset" non compare agli anonimi (guard check_access).

    Il caso positivo (admin) e' verificato a mano: in questo setup di test
    l'autenticazione via set_session_user/set_remember_user non attecchisce.
    """
    body = app.get("/dataset").body
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    assert "rtt-catalog__add" not in body
