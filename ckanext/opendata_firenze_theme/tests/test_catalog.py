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
    # lo stato vuoto (noresults.jsx): titolo con la query, azioni (svuota la
    # ricerca quando c'è una q, "chiedi un dato mancante" sempre)
    assert "rtt-noresults" in body
    assert "Nessun dataset per" in body
    assert "Svuota la ricerca" in body
    assert "Chiedi un dato mancante" in body


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
def test_catalog_facets_tutti_and_single_open(with_plugins, app):
    """ "Tutti" solo con piu' di un valore; i gruppi sono a singola apertura."""
    from flask import render_template_string

    src = "{% include 'snippets/opendata_firenze_theme/catalog/facets.html' %}"
    two = {
        "res_format": {
            "title": "res_format",
            "items": [
                {"name": "CSV", "display_name": "CSV", "count": 2},
                {"name": "SHP", "display_name": "SHP", "count": 1},
            ],
        }
    }
    one = {
        "organization": {
            "title": "organization",
            "items": [{"name": "org", "display_name": "Org", "count": 1}],
        }
    }
    with app.flask_app.test_request_context("/dataset"):
        html_two = render_template_string(src, search_facets=two, q="", sort_by_selected="")
        html_one = render_template_string(src, search_facets=one, q="", sort_by_selected="")
    assert "Tutti" in html_two
    assert 'name="rtt-facets"' in html_two
    assert "Tutti" not in html_one


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_facet_all_url_helper(with_plugins, app):
    """odf_facet_all_url sostituisce i valori della faccetta e mantiene il resto."""
    from urllib.parse import parse_qs, urlparse

    from ckanext.opendata_firenze_theme import helpers

    with app.flask_app.test_request_context("/dataset?q=aria&res_format=CSV&page=3"):
        url = helpers.odf_facet_all_url("res_format", ["CSV", "SHP"])
    assert url.startswith("/dataset")
    query = parse_qs(urlparse(url).query)
    assert query["q"] == ["aria"]
    assert query["res_format"] == ["CSV", "SHP"]
    assert "page" not in query


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
