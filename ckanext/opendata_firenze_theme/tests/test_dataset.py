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
    with mock.patch.object(helpers, "_search", return_value=found):
        related = helpers.odf_dataset_related(pkg, limit=2)
    assert [r["id"] for r in related] == ["a", "b"]
