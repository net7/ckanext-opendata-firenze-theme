"""Ricerca fuzzy del catalogo e pagina di ricerca site-wide."""

import importlib.util
import re
from unittest import mock

import pytest
from ckan.tests import factories

from ckanext.opendata_firenze_theme import plugin
from ckanext.opendata_firenze_theme.helpers import catalog_search as catalog_search_helpers
from ckanext.opendata_firenze_theme.helpers import editorial, fuzzy, search
from ckanext.opendata_firenze_theme.helpers.query import fuzzy_query

PLUGIN = "opendata_firenze_theme"
PAGES_INSTALLED = importlib.util.find_spec("ckanext.pages") is not None


def _body(response):
    return response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body


def test_fuzzy_query_uses_auto_distance():
    assert fuzzy_query("ambinete") == "ambinete~2"
    assert fuzzy_query("Farenze") == "Farenze~2"
    assert fuzzy_query("qualita dell aria") == "qualita~2 dell~1 aria~1"
    assert fuzzy_query("qualita dell'arie") == "qualita~2 dell~1 arie~1"
    assert fuzzy_query("popolazion") == "popolazion~2"
    assert fuzzy_query("casa") == "casa~1"
    assert fuzzy_query("abc") is None


def test_fuzzy_distance_and_within_distance():
    assert fuzzy.distance_for("abc") == 0
    assert fuzzy.distance_for("data") == 1
    assert fuzzy.distance_for("farenze") == 2
    assert fuzzy.within_distance("datt", "data", 1) is True
    assert fuzzy.within_distance("ambinete", "ambiente", 1) is True
    assert fuzzy.within_distance("farenze", "firenze", 2) is True
    assert fuzzy.within_distance("datt", "casa", 1) is False


def test_fuzzy_query_leaves_advanced_queries_alone():
    assert fuzzy_query("tags:ambiente") is None
    assert fuzzy_query('"frase esatta"') is None
    assert fuzzy_query("ambiente OR aria") is None
    assert fuzzy_query("*:*") is None


def test_catalog_search_falls_back_to_fuzzy():
    calls = []

    def fake_search(context, data_dict):
        calls.append(dict(data_dict))
        if data_dict.get("defType") == "edismax":
            return {"count": 1, "results": [{"id": "dataset-fuzzy"}]}
        return {"count": 0, "results": []}

    result = catalog_search_helpers.catalog_search(
        {"user": "", "auth_user_obj": None, "for_view": True},
        {"q": "ambinete"},
        search=fake_search,
    )

    assert result["count"] == 1
    assert result["odf_fuzzy"] is True
    assert calls[0]["q"] == "ambinete"
    assert calls[1]["q"] == "ambinete~2"
    assert calls[1]["defType"] == "edismax"
    assert calls[1]["mm"] == "1"


def test_catalog_search_keeps_api_exact():
    calls = []

    def fake_search(context, data_dict):
        calls.append(dict(data_dict))
        return {"count": 0, "results": []}

    result = catalog_search_helpers.catalog_search(
        {"user": "", "auth_user_obj": None}, {"q": "ambinete"}, search=fake_search
    )

    assert result["count"] == 0
    assert len(calls) == 1


@pytest.mark.skipif(not PAGES_INSTALLED, reason="ckanext-pages non installato")
def test_recent_news_normalizes_posts(monkeypatch):
    monkeypatch.setattr(
        "ckanext.pages.plugin.get_recent_blog_posts",
        lambda number=3: [
            {
                "name": "news-recente",
                "title": "News recente",
                "publish_date": "2026-11-25",
                "content": "<p>Testo della news.</p>",
            }
        ],
    )
    monkeypatch.setattr(
        editorial.toolkit,
        "url_for",
        lambda endpoint, **kwargs: f"/{endpoint}/{kwargs.get('page', '')}",
    )

    items = editorial.recent_news(2)

    assert items[0]["kind"] == "news"
    assert items[0]["title"] == "News recente"
    assert items[0]["url"] == "/pages.blog_show/news-recente"


def test_plugin_delegates_to_catalog_search(monkeypatch):
    seen = {}

    def fake_catalog_search(context, data_dict):
        seen["context"] = context
        return {"count": 0, "results": []}

    monkeypatch.setattr(plugin, "catalog_search", fake_catalog_search)
    result = plugin.odf_package_search({"user": ""}, {"q": "ambinete"})

    assert result["count"] == 0
    assert seen["context"] == {"user": ""}


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_header_search_targets_site_search(app):
    body = _body(app.get("/"))
    # header e menu mobile puntano alla ricerca site-wide
    assert len(re.findall(r'action="/search"', body)) >= 2
    # il form del catalogo/home continua a cercare solo i dataset
    assert 'action="/dataset/"' in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_site_search_excludes_organizations(app):
    factories.Organization(title="Ente Ricerca Unica")

    body = _body(app.get("/search?q=ricerca%20unica"))

    assert "Ente Ricerca Unica" not in body
    assert 'id="site-search-organizations"' not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_site_search_collects_datasets(app):
    factories.Dataset(title="Dataset Ricerca Unica")

    response = app.get("/search?q=ricerca%20unica")
    assert response.status_code == 200
    body = _body(response)
    assert "Dataset Ricerca Unica" in body
    assert 'id="site-search-organizations"' not in body
    assert "Nessun risultato" not in body


def test_editorial_search_content_filters_news_and_pages(monkeypatch):
    monkeypatch.setattr(
        editorial,
        "_pages",
        lambda: [
            {
                "name": "news-unica",
                "title": "News unica",
                "content": "<p>Corpo della news.</p>",
                "page_type": "blog",
                "publish_date": "2026-11-25",
            },
            {
                "name": "pagina-unica",
                "title": "Pagina unica",
                "content": "<p>Corpo della pagina.</p>",
                "page_type": "page",
                "publish_date": None,
            },
            {
                "name": "altro",
                "title": "Altra pagina",
                "content": "Testo diverso.",
                "page_type": "page",
                "publish_date": None,
            },
        ],
    )
    monkeypatch.setattr(
        editorial.toolkit,
        "url_for",
        lambda endpoint, **kwargs: f"/{endpoint}/{kwargs.get('page', '')}",
    )

    items = editorial.search_content("unica")

    assert [item["name"] for item in items] == ["news-unica", "pagina-unica"]
    assert [item["kind"] for item in items] == ["news", "page"]
    assert items[0]["url"] == "/pages.blog_show/news-unica"
    assert items[1]["url"] == "/pages.show/pagina-unica"


def test_editorial_matches_handles_apostrophes():
    assert editorial.matches("Qualità dell'aria", "Qualità dell'arie") is True
    assert editorial.matches("Qualità dell'aria", "Qualità dell'aria") is True
    assert editorial.matches("Qualità dell'aria", "Qualità dell'acqua") is False


def test_editorial_search_content_tolerates_typo(monkeypatch):
    monkeypatch.setattr(
        editorial,
        "_pages",
        lambda: [
            {
                "name": "news-recente",
                "title": "Nuovi dataset nel catalogo Open Data",
                "content": "<p>Testo della news.</p>",
                "page_type": "blog",
                "publish_date": "2026-11-25",
            }
        ],
    )
    monkeypatch.setattr(
        editorial.toolkit,
        "url_for",
        lambda endpoint, **kwargs: f"/{endpoint}/{kwargs.get('page', '')}",
    )

    items = editorial.search_content("Nuovi dataset nel catalogo Open Datt")

    assert [item["name"] for item in items] == ["news-recente"]
    assert items[0]["kind"] == "news"


def test_site_search_filters_news_and_pages(monkeypatch):
    calls = []

    def fake_search(**params):
        calls.append(params)
        return {"count": 0, "results": []}

    monkeypatch.setattr(search._common, "_search", fake_search)
    monkeypatch.setattr(
        editorial,
        "search_content",
        lambda query: [
            {"name": "news-unica", "title": "News unica", "kind": "news", "url": "/blog/n"},
            {"name": "pagina-unica", "title": "Pagina unica", "kind": "page", "url": "/pages/p"},
        ],
    )
    monkeypatch.setattr(search.toolkit, "url_for", lambda endpoint, **kwargs: f"/{endpoint}")

    result = search.odf_site_search("unica")

    assert result["q"] == "unica"
    groups = {group["id"]: group for group in result["groups"]}
    assert [item["name"] for item in groups["news"]["entries"]] == ["news-unica"]
    assert [item["name"] for item in groups["pages"]["entries"]] == ["pagina-unica"]
    assert calls[0]["view"] is True


@pytest.mark.skipif(not PAGES_INSTALLED, reason="ckanext-pages non installato")
@pytest.mark.ckan_config("ckan.plugins", f"{PLUGIN} pages")
@pytest.mark.usefixtures("with_plugins")
def test_site_search_page_renders_news_and_pages(app):
    payload = {
        "q": "unica",
        "groups": [
            {
                "id": "news",
                "title": "News",
                "kind": "news",
                "entries": [
                    {
                        "name": "news-unica",
                        "title": "News titolo unico",
                        "content": "Corpo della news.",
                        "publish_date": "2026-11-25",
                        "url": "/blog/news-unica",
                    }
                ],
            },
            {
                "id": "pages",
                "title": "Pagine",
                "kind": "page",
                "entries": [{"title": "Pagina titolo unica", "url": "/pages/pagina-unica"}],
            },
        ],
    }
    with mock.patch.object(search, "odf_site_search", return_value=payload):
        response = app.get("/search?q=unica")

    assert response.status_code == 200
    body = _body(response)
    assert "News titolo unico" in body
    assert "Pagina titolo unica" in body
    assert 'id="site-search-organizations"' not in body
    assert 'href="/blog/news-unica"' in body
    assert 'href="/pages/pagina-unica"' in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_catalog_fuzzy_farenze(app):
    factories.Dataset(title="Comune di Firenze")

    body = _body(app.get("/dataset/?q=Farenze"))

    assert "Comune di Firenze" in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_site_search_empty_query(app):
    body = _body(app.get("/search"))
    assert "Inserisci un termine" in body
    assert "Nessun risultato" not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_site_search_no_results(app):
    body = _body(app.get("/search?q=zzzzzzzzzzzzzz"))
    assert "Nessun risultato per" in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_site_search_fuzzy_route(app):
    factories.Dataset(title="Ambiente e territorio")

    body = _body(app.get("/search?q=ambinete"))
    assert "Ambiente e territorio" in body
    assert "Nessun risultato esatto" in body

    # Il catalogo usa lo stesso fallback, ma non mostra la nota.
    body = _body(app.get("/dataset/?q=ambinete"))
    assert "Ambiente e territorio" in body
