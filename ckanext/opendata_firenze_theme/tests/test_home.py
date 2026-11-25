"""Rendering della home e helper del tema."""

import re
from datetime import date, timedelta
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
        if params.get("fq") == "odf_features:hvd":
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
def test_consultati_card_uses_period_views(with_plugins, app):
    """La card "I più consultati" mostra il conteggio del periodo scelto.

    `views_period` arriva dal DB di tracking; se manca (card usata altrove) si
    ricade su `tracking_summary`. `views_total`/`views_recent` di Solr non sono
    *stored* e non vanno letti da `package_search`.
    """
    from flask import render_template_string

    src = "{% from 'snippets/opendata_firenze_theme/home/dataset-card.html' import consultati_card %}{{ consultati_card(pkg) }}"

    def render(**extra):
        pkg = {"name": "x", "title": "Dataset"}
        pkg.update(extra)
        with app.flask_app.test_request_context("/"):
            return render_template_string(src, pkg=pkg)

    # il conteggio del periodo vince sul totale storico
    html = render(views_period=8, tracking_summary={"total": 1234, "recent": 10})
    assert "8 visualizzazioni" in html
    assert "1.234 visualizzazioni" not in html
    # il link-card ha come nome accessibile il titolo, non tutta la card
    assert 'aria-labelledby="consultati-title-x"' in html
    assert 'id="consultati-title-x"' in html
    # zero viste nel periodo: niente riga, anche se il totale storico esiste
    assert "visualizzazioni" not in render(views_period=0, tracking_summary={"total": 1234})
    # senza `views_period` (card riusata fuori dal blocco) si usa il totale
    assert "1.234 visualizzazioni" in render(tracking_summary={"total": 1234, "recent": 10})
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
def test_featured_block_uses_shared_carousel(with_plugins, with_request_context):
    """ "In evidenza" usa lo stesso macro carosello degli altri blocchi."""
    from flask import render_template_string

    pkgs = [
        {"id": "a", "name": "a", "title": "Alpha"},
        {"id": "b", "name": "b", "title": "Beta"},
    ]
    html = render_template_string(
        "{% include 'home/blocks/featured.html' %}",
        block={"title": "In evidenza", "subtitle": "", "cta_label": "", "cta_url": ""},
        block_data={"datasets": pkgs},
    )
    assert 'aria-label="Dataset in evidenza"' in html
    assert "rtt-carousel" in html
    assert "Beta" in html


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


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_period_views_aggregates_page_views_in_window(with_plugins):
    from ckan.tests import factories

    from ckanext.opendata_firenze_theme.helpers import home
    from ckanext.tracking.model import TrackingSummary

    pkg = factories.Dataset()
    package_id = pkg["id"]
    today = date.today()

    def add(url, day, count, tracking_type="page", pid=package_id):
        TrackingSummary.create(
            url=f"{url}-{pid}-{day}",
            package_id=pid,
            tracking_type=tracking_type,
            count=count,
            running_total=count,
            recent_views=count,
            tracking_date=day,
        )

    add("demo-window", today, 10)
    add("demo-window", today - timedelta(days=5), 20)
    add("demo-window", today - timedelta(days=20), 30)
    add("demo-window", today - timedelta(days=200), 40)
    # né le resource view né le righe "not found" entrano nel conteggio
    add("demo-window-resource", today, 100, tracking_type="resource")
    add("demo-window-nf", today, 100, pid="~~not~found~~")

    # il DB di test può contenere righe di run precedenti: valuto solo il
    # pacchetto creato qui, non l'ordine globale.
    def views(period):
        return dict(home._period_views(period, 100)).get(package_id)

    assert views("today") == 10
    assert views("week") == 30
    assert views("month") == 60
    assert views("quarter") == 60
    assert views("half") == 60
    assert views("year") == 100


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_period_views_window_boundaries(with_plugins):
    """Fissa i confini delle finestre: 7 giorni e 365 giorni esclusi."""
    from ckan.tests import factories

    from ckanext.opendata_firenze_theme.helpers import home
    from ckanext.tracking.model import TrackingSummary

    pkg = factories.Dataset()
    package_id = pkg["id"]
    today = date.today()

    for label, day, count in (
        ("today", today, 5),
        ("six-days", today - timedelta(days=6), 1),
        ("seven-days", today - timedelta(days=7), 10),
        ("364-days", today - timedelta(days=364), 100),
        ("365-days", today - timedelta(days=365), 1000),
    ):
        TrackingSummary.create(
            url=f"demo-boundary-{package_id}-{label}",
            package_id=package_id,
            tracking_type="page",
            count=count,
            running_total=count,
            recent_views=count,
            tracking_date=day,
        )

    def views(period):
        return dict(home._period_views(period, 100)).get(package_id)

    assert views("today") == 5
    assert views("week") == 6  # oggi + 6 giorni fa, non 7
    assert views("month") == 16  # include anche la riga di 7 giorni fa
    assert views("year") == 116  # fino a 364 giorni fa, non 365


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_period_views_rolls_back_on_error(with_plugins):
    from ckan import model
    from sqlalchemy import text

    from ckanext.opendata_firenze_theme.helpers import home

    with mock.patch.object(model.Session, "query", side_effect=RuntimeError("boom")):
        assert home._period_views("week", 4) is None

    # se la sessione fosse rimasta abortita questa query fallirebbe
    assert model.Session.execute(text("SELECT 1")).scalar() == 1


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_most_viewed_uses_period_views(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme.helpers import home

    calls = []

    def fake_search(**params):
        calls.append(params)
        return {
            "results": [{"id": "a", "tracking_summary": {"total": 5, "recent": 1}}],
            "count": 1,
        }

    with (
        mock.patch.object(home, "_period_views", return_value=[("a", 7)]) as period,
        mock.patch.object(home._common, "_search", side_effect=fake_search),
    ):
        viewed = home.odf_most_viewed(4, "week")

    assert [pkg["id"] for pkg in viewed] == ["a"]
    assert viewed[0]["views_period"] == 7
    # si leggono più candidati del limite per scartare quelli non più in Solr
    period.assert_called_once_with("week", 20)
    assert len(calls) == 1
    assert calls[0]["fq"].startswith('id:("a"')


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_most_viewed_skips_packages_missing_from_solr(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme.helpers import home

    ranked = [("cancellato", 99), ("a", 7)]

    def fake_search(**params):
        # il dataset cancellato/privato non è più nei risultati di ricerca
        return {"results": [{"id": "a"}], "count": 1}

    with (
        mock.patch.object(home, "_period_views", return_value=ranked) as period,
        mock.patch.object(home._common, "_search", side_effect=fake_search),
    ):
        viewed = home.odf_most_viewed(1, "year")

    assert [pkg["id"] for pkg in viewed] == ["a"]
    assert viewed[0]["views_period"] == 7
    period.assert_called_once_with("year", 5)


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_most_viewed_hides_when_period_has_no_views(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme.helpers import home

    with mock.patch.object(home, "_period_views", return_value=[]):
        assert home.odf_most_viewed(4, "today") == []


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_most_viewed_returns_none_when_tracking_unavailable(with_plugins):
    from ckanext.opendata_firenze_theme.helpers import home

    with mock.patch.object(home, "_period_views", return_value=None):
        assert home.odf_most_viewed(4, "year") is None


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_most_viewed_period_label(with_plugins):
    from ckanext.opendata_firenze_theme.helpers import home

    assert home.odf_most_viewed_label("year") == "Ultimi 12 mesi"
    assert home.odf_most_viewed_label("half") == "Ultimi 6 mesi"
    assert home.odf_most_viewed_label("quarter") == "Ultimi 3 mesi"
    assert home.odf_most_viewed_label("month") == "Ultimo mese"
    assert home.odf_most_viewed_label("week") == "Ultima settimana"
    assert home.odf_most_viewed_label("today") == "Oggi"
    assert home.odf_most_viewed_label("bogus") == "Ultimi 12 mesi"
