"""Rendering della home e helper del tema."""

import re

import pytest
from ckan.tests import factories

PLUGIN = "opendata_firenze_theme"


def _body(app):
    response = app.get("/")
    assert response.status_code == 200
    body = response.body
    return body.decode("utf-8") if isinstance(body, bytes) else body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_home_renders(app):
    # almeno un dataset: le sezioni con azione ("In evidenza"…) si vedono solo
    # con del contenuto, indipendentemente dallo stato del catalogo
    factories.Dataset(title="Dataset di prova")
    body = _body(app)
    assert 'class="rtt-hero"' in body
    assert "rtt-kpistrip" in body
    assert "Esplora per tema" in body
    assert 'class="rtt-action"' in body
    # l'azione di sezione e' markup, non deve finire escapata nel DOM
    assert '&lt;a class="rtt-action"' not in body
    # i 13 temi DCAT-AP_IT sono sempre elencati
    assert body.count("rtt-tema__name") == 13


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_home_search_icon_and_section_arrow(app):
    factories.Dataset(title="Dataset di prova")
    body = _body(app)
    # la lente dell'hero e' a 24px, come SearchBar size="lg" del mockup
    assert re.search(r'class="rtt-search__icon" aria-hidden="true"><svg[^>]*width="24"', body)
    # ogni azione di sezione ("Vedi tutti"…) termina con la freccia 18px
    actions = re.findall(r'class="rtt-section__action">(.*?)</div>', body)
    assert actions
    assert all('width="18"' in action for action in actions)


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_home_helpers(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    themes = helpers.odf_themes()
    assert len(themes) == 13
    assert {t["code"] for t in themes} == {code for code, _ in helpers.THEMES}
    assert len(helpers.odf_home_kpis()) == 4
    assert helpers.odf_dataset_count() >= 0
