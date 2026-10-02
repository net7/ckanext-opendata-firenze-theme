"""Scheda dataset: rendering delle due viste e helper dedicati."""

from unittest import mock

import pytest
from ckan.tests import factories

PLUGIN = "opendata_firenze_theme"


def _body(response):
    return response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_dataset_page_renders_essential(app):
    pkg = factories.Dataset(
        title="Dataset di prova",
        notes="Una descrizione di prova.",
        author="Comune di Firenze",
        author_email="dati@comune.fi.it",
    )
    body = _body(app.get(f"/dataset/{pkg['name']}"))
    assert "rtt-dataset" in body
    assert "Vista essenziale" in body
    assert "Metadati avanzati" in body
    assert "Risorse scaricabili" in body
    assert "In sintesi" in body
    assert "Titolare del dato" in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_dataset_page_renders_advanced(app):
    pkg = factories.Dataset(title="Dataset di prova")
    body = _body(app.get(f"/dataset/{pkg['name']}?tab=avanzata"))
    assert "Metadati DCAT-AP_IT" in body
    assert "Extras e interoperabilità" in body
    assert "API e formati semantici" in body
    # l'azione del pannello è markup, non deve finire escapata
    assert '&lt;span class="rtt-body-sm"' not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_dataset_no_editor_action_for_anonymous(app):
    pkg = factories.Dataset(title="Dataset di prova")
    body = _body(app.get(f"/dataset/{pkg['name']}"))
    assert "Gestisci" not in body
    assert f"/dataset/edit/{pkg['name']}" not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_sql_console_enabled_helper(with_plugins, with_request_context, monkeypatch):
    import ckan.lib.helpers as ckan_h

    from ckanext.opendata_firenze_theme import helpers

    monkeypatch.setattr(ckan_h, "datastore_search_sql_enabled", lambda: True, raising=False)
    assert helpers.odf_sql_console_enabled() is True

    monkeypatch.setattr(ckan_h, "datastore_search_sql_enabled", lambda: False, raising=False)
    assert helpers.odf_sql_console_enabled() is False

    # senza ckanext-datastore l'helper non esiste: niente errore
    monkeypatch.delattr(ckan_h, "datastore_search_sql_enabled", raising=False)
    assert helpers.odf_sql_console_enabled() is False


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_dataset_helpers(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    assert helpers.odf_filesize(None) == ""
    assert helpers.odf_filesize(1536) == "1,5 KB"
    assert helpers.odf_frequency_label("IRREG") == "irregolare"
    assert helpers.odf_frequency_label("XYZ") == "XYZ"
    assert helpers.odf_dataset_formats({"resources": [{"format": "csv"}, {"format": "CSV"}, {"format": "GeoJSON"}]}) == [
        "CSV",
        "GEOJSON",
    ]

    # geometria normalizzata, qualunque sia il maiuscolo dell'extra
    assert helpers.odf_dataset_geometry({"extras": [{"key": "geometria", "value": "Punto"}]}) == "punto"
    assert helpers.odf_dataset_geometry({"extras": [{"key": "geometria", "value": "x"}]}) is None

    pkg = {
        "extras": [{"key": "hvd", "value": "true"}],
        "resources": [{"format": "GeoJSON"}],
    }
    kinds = {b["kind"] for b in helpers.odf_dataset_badges(pkg)}
    assert kinds == {"hvd", "geo"}

    # ckanext-dcat rinomina le chiavi con l'etichetta nelle viste: `theme` -> `Theme`
    assert helpers.odf_pkg_extra({"extras": [{"key": "Theme", "value": "x"}]}, "theme") == "x"
    assert helpers.odf_pkg_extra({"extras": {"Theme": "y"}}, "theme") == "y"
    assert helpers.odf_pkg_extra({"extras": [{"key": "serie", "value": "S"}]}, "serie") == "S"
    assert helpers.odf_pkg_extra({"extras": []}, "serie") is None


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_realtime_badge_truthiness(with_plugins, with_request_context):
    """`realtime` segue `_truthy`: "false" non è realtime (fonte unica per
    badge e aside, altrimenti l'aside mostrerebbe "Aggiornato" a vuoto)."""
    from ckanext.opendata_firenze_theme import helpers

    def kinds(value):
        pkg = {"extras": [{"key": "realtime", "value": value}]}
        return {b["kind"] for b in helpers.odf_dataset_badges(pkg)}

    assert "realtime" in kinds("true")
    assert "realtime" in kinds("1")
    assert "realtime" not in kinds("false")
    assert "realtime" not in kinds("0")


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_dataset_series_helper(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    # senza serie non si interroga il catalogo
    assert helpers.odf_dataset_series({"id": "x"}) == []

    pkg = {"id": "self", "extras": [{"key": "serie", "value": "Open SDIAF"}]}
    found = {
        "results": [
            {"id": "self", "name": "self", "title": "Sé stesso"},
            {"id": "a", "name": "a", "title": "A", "res_format": ["CSV", "CSV", "GeoJSON"]},
            {"id": "b", "name": "b", "title": "B"},
        ]
    }
    with mock.patch.object(helpers._common, "_search", return_value=found):
        series = helpers.odf_dataset_series(pkg)
    # sé stesso escluso, formati deduplicati da Solr (res_format)
    assert [s["name"] for s in series] == ["a", "b"]
    assert series[0]["formats"] == ["CSV", "GEOJSON"]


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_dataset_revisions_helper(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    # senza is_version_of non si interroga il catalogo
    assert helpers.odf_dataset_revisions({"id": "x"}) == []

    root = "https://opendata-firenze.test/dataset/popolazione"
    pkg = {"id": "self", "extras": [{"key": "is_version_of", "value": root}]}
    found = {
        "results": [
            {"id": "self", "name": "self", "title": "Popolazione residente 2025"},
            {"id": "a", "name": "pop-2024", "title": "Popolazione residente 2024", "res_format": ["CSV"]},
            {"id": "b", "name": "pop-2023", "title": "Popolazione residente 2023"},
            {"id": "c", "name": "pop-storico", "title": "Popolazione (storico)"},
        ]
    }
    with mock.patch.object(helpers._common, "_search", return_value=found) as search:
        revisions = helpers.odf_dataset_revisions(pkg)
    # sé stesso escluso, formati da Solr e anno estratto dal titolo (None se assente)
    assert [r["name"] for r in revisions] == ["pop-2024", "pop-2023", "pop-storico"]
    assert [r["year"] for r in revisions] == ["2024", "2023", None]
    assert revisions[0]["formats"] == ["CSV"]
    assert f'extras_is_version_of:"{root}"' in search.call_args.kwargs["fq"]

    # più valori (dcatapit li serializza separati da virgola): tutti nella query
    multi = {
        "id": "self",
        "extras": [{"key": "is_version_of", "value": f"{root},https://example.test/x"}],
    }
    with mock.patch.object(helpers._common, "_search", return_value=found) as search:
        helpers.odf_dataset_revisions(multi)
    fq = search.call_args.kwargs["fq"]
    assert f'extras_is_version_of:"{root}"' in fq
    assert 'extras_is_version_of:"https://example.test/x"' in fq
    assert " OR " in fq


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_time_ago_helper(with_plugins, with_request_context):
    from datetime import datetime, timedelta, timezone

    from ckanext.opendata_firenze_theme import helpers

    now = datetime.now(timezone.utc)
    assert helpers.odf_time_ago(None) == ""
    assert helpers.odf_time_ago((now - timedelta(minutes=5)).isoformat()) == "pochi minuti fa"
    assert helpers.odf_time_ago((now - timedelta(hours=1)).isoformat()) == "1 ora fa"
    assert helpers.odf_time_ago((now - timedelta(hours=3)).isoformat()) == "3 ore fa"
    assert helpers.odf_time_ago((now - timedelta(days=1)).isoformat()) == "1 giorno fa"
    assert helpers.odf_time_ago((now - timedelta(days=2)).isoformat()) == "2 giorni fa"
    # oltre i 30 giorni ricade sulla data assoluta
    old = now - timedelta(days=400)
    assert helpers.odf_time_ago(old.isoformat()) == old.strftime("%d/%m/%Y")
    # valore non parsabile: nessun errore, resta la stringa troncata
    assert helpers.odf_time_ago("not-a-date") == "not-a-date"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_dataset_related_helper(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    # senza tema non si interroga il catalogo
    assert helpers.odf_dataset_related({"id": "x"}) == []

    pkg = {
        "id": "self",
        "extras": [{"key": "theme", "value": '[".../data-theme/ENVI"]'}],
    }
    found = {"results": [{"id": "self"}, {"id": "a"}, {"id": "b"}, {"id": "c"}]}
    with mock.patch.object(helpers._common, "_search", return_value=found):
        related = helpers.odf_dataset_related(pkg, limit=2)
    assert [r["id"] for r in related] == ["a", "b"]
