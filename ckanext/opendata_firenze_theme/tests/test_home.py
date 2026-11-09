"""Rendering della home e helper del tema."""

import re
from unittest import mock

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
    assert 'class="rtt-actionlink"' in body
    # l'azione di sezione e' markup, non deve finire escapata nel DOM
    assert '&lt;a class="rtt-actionlink"' not in body
    # i temi sono elencati; senza conteggi (facet non indicizzata) si ripiega
    # su tutti e 13
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
def test_theme_counts_from_dcat_theme(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    fake = {"search_facets": {"dcat_theme": {"items": [{"name": "ENVI", "count": 2}]}}}
    with mock.patch.object(helpers._common, "_search", return_value=fake):
        assert helpers.odf_theme_counts() == {"ENVI": 2}


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_home_theme_link_uses_dcat_theme(with_plugins, with_request_context):
    """Il link "Esplora per tema" filtra con `dcat_theme`, non con `theme`."""
    from flask import render_template_string

    from ckanext.opendata_firenze_theme import helpers

    fake = {"search_facets": {"dcat_theme": {"items": [{"name": "TRAN", "count": 2}]}}}
    with mock.patch.object(helpers._common, "_search", return_value=fake):
        themes = helpers.odf_themes_visible()
        html = render_template_string(
            "{% include 'snippets/opendata_firenze_theme/home/temi.html' %}",
            themes=themes,
        )
    assert "dcat_theme=TRAN" in html
    # il vecchio parametro errato non deve comparire
    assert "?theme=TRAN" not in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_featured_datasets_hvd_then_recent(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    def fake_search(**params):
        if params.get("fq") == "extras_hvd:true":
            return {"results": [{"id": "a"}], "count": 1}
        return {"results": [{"id": "a"}, {"id": "b"}, {"id": "c"}]}

    with mock.patch.object(helpers._common, "_search", side_effect=fake_search):
        got = helpers.odf_featured_datasets(limit=3)
    # prima l'HVD, poi i recenti senza duplicati
    assert [p["id"] for p in got] == ["a", "b", "c"]


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_home_themes_visible_filters_and_falls_back(with_plugins, with_request_context):
    """Solo i temi con dataset; senza conteggi si mostrano tutti e 13."""
    from unittest import mock

    from ckanext.opendata_firenze_theme import helpers
    from ckanext.opendata_firenze_theme.helpers import home

    with mock.patch.object(
        home,
        "odf_themes",
        return_value=[
            {"code": "TRAN", "label": "Trasporti", "count": 3},
            {"code": "ENVI", "label": "Ambiente", "count": 0},
        ],
    ):
        assert [t["code"] for t in helpers.odf_themes_visible()] == ["TRAN"]

    with mock.patch.object(
        home, "odf_themes", return_value=[{"code": "TRAN", "label": "Trasporti", "count": 0}]
    ):
        assert [t["code"] for t in helpers.odf_themes_visible()] == ["TRAN"]  # fallback

    # senza conteggi (facet non indicizzata) il fallback reale è tutti e 13
    assert len(helpers.odf_themes_visible()) == 13


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_home_helpers(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    themes = helpers.odf_themes()
    assert len(themes) == 13
    assert {t["code"] for t in themes} == {code for code, _ in helpers.THEMES}
    kpis = helpers.odf_home_kpis()
    assert len(kpis) == 4
    assert [k["label"] for k in kpis] == [
        "dataset nel catalogo",
        "dataset alfanumerici",
        "dataset geografici",
        "capitoli dell'Annuario Statistico",
    ]
    assert helpers.odf_dataset_count() >= 0


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_consultati_card_shows_views_from_tracking_summary(with_plugins, app):
    """La card "I più consultati" prende le visualizzazioni da `tracking_summary`.

    `views_total`/`views_recent` esistono solo su Solr e non sono *stored*:
    `package_search` non li restituisce. Se la card li legge da li' (come faceva
    prima) il contatore "N visualizzazioni" non compare mai.
    """
    from flask import render_template_string

    src = "{% from 'snippets/opendata_firenze_theme/home/dataset-card.html' import consultati_card %}{{ consultati_card(pkg) }}"

    def render(**extra):
        pkg = {"name": "x", "title": "Dataset"}
        pkg.update(extra)
        with app.flask_app.test_request_context("/"):
            return render_template_string(src, pkg=pkg)

    assert "1.234 visualizzazioni" in render(tracking_summary={"total": 1234, "recent": 10})
    # il link-card ha come nome accessibile il titolo, non tutta la card
    html = render(tracking_summary={"total": 1234, "recent": 10})
    assert 'aria-labelledby="consultati-title-x"' in html
    assert 'id="consultati-title-x"' in html
    # senza visualizzazioni la riga sparisce
    assert "visualizzazioni" not in render(tracking_summary={"total": 0, "recent": 0})
    # il campo Solr (indicizzato ma non stored) non basta piu'
    assert "visualizzazioni" not in render(views_total=5)


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_latest_and_lod_home_lists(with_plugins, with_request_context):
    """Blocchi "Ultimi pubblicati" e "Linked Open Data": query e ordinamento."""
    from ckanext.opendata_firenze_theme import helpers

    calls = []

    def fake_search(**params):
        calls.append(params)
        return {"results": [{"id": "x"}], "count": 1}

    with mock.patch.object(helpers._common, "_search", side_effect=fake_search):
        assert helpers.odf_latest_datasets(6) == [{"id": "x"}]
        assert helpers.odf_lod_datasets(6) == [{"id": "x"}]

    assert calls[0]["sort"] == "metadata_created desc"
    assert calls[1]["fq"] == "odf_features:lod"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_home_geo_uses_indexed_features(with_plugins, with_request_context):
    """KPI e lista geodati leggono `odf_features:geo`, la stessa fonte della
    faccetta "Caratteristiche" e del badge della scheda."""
    from ckanext.opendata_firenze_theme import helpers

    calls = []

    def fake_search(**params):
        calls.append(params)
        return {"count": 3, "results": [{"id": "a"}], "search_facets": {}}

    with mock.patch.object(helpers._common, "_search", side_effect=fake_search):
        helpers.odf_home_kpis()
        helpers.odf_geo_datasets(5)

    fqs = [call.get("fq") for call in calls]
    assert fqs.count("odf_features:geo") == 2
    assert helpers.odf_geo_search_query() == "odf_features:geo"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_latest_block_renders(with_plugins, with_request_context):
    """Il blocco "Ultimi pubblicati" usa il carosello e le card del tema."""
    from flask import render_template_string

    pkg = {"id": "a", "name": "a", "title": "Alpha", "res_format": ["CSV"]}
    html = render_template_string(
        "{% include 'home/blocks/latest.html' %}",
        block={
            "title": "Ultimi pubblicati",
            "subtitle": "",
            "cta_label": "",
            "cta_url": "",
        },
        block_data={"datasets": [pkg]},
    )
    assert "Ultimi pubblicati" in html
    assert "Alpha" in html
    assert "rtt-carousel" in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_home_search_button_is_textual_and_accessible(with_plugins, with_request_context):
    """Il pulsante della home ha testo visibile e nessun aria-label che lo contraddica."""
    from flask import render_template_string

    body = render_template_string(
        "{% include 'snippets/opendata_firenze_theme/home/hero.html' %}", count=42
    )
    assert "Cerca un dataset" in body
    # il conteggio arriva dal blocco, non da una query dello snippet
    assert "Esplora 42 dataset" in body
    # niente aria-label sul pulsante testuale: il nome accessibile è il testo
    assert "rtt-search__submit rtt-search__submit--text" in body
    assert 'rtt-search__submit--text" type="submit" aria-label' not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_search_form_submit_text_has_no_conflicting_label(with_plugins, with_request_context):
    from flask import render_template_string

    html = render_template_string(
        "{% include 'snippets/opendata_firenze_theme/search_form.html' %}",
        submit_text="Cerca",
        submit_text_short="Vai",
    )
    assert "rtt-search__submit--text" in html
    assert "rtt-search__submit--has-short" in html
    assert ">Cerca<" in html
    assert ">Vai<" in html
    assert 'aria-label="Avvia la ricerca"' not in html
