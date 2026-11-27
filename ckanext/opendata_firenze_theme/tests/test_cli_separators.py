"""Backfill del separatore CSV (`ckan odf-extract-separators`)."""

import pytest
from ckan.plugins import toolkit
from ckan.tests import factories
from click.testing import CliRunner

from ckanext.opendata_firenze_theme.cli import extract_separators
from ckanext.opendata_firenze_theme.helpers import separator

PLUGIN = "opendata_firenze_theme"
NOTE = 'Il separatore delle risorse CSV è ";" (lett. punto e virgola).'


def _extra(pkg_id):
    pkg = toolkit.get_action("package_show")({"ignore_auth": True}, {"id": pkg_id})
    extras = pkg.get("extras") or {}
    if isinstance(extras, dict):
        return extras.get("separatore")
    return next((e.get("value") for e in extras if e.get("key") == "separatore"), None)


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_extract_separators_dry_run_then_apply(monkeypatch):
    # Crea il dataset senza far scattare il chained action, così il CLI ha
    # davvero qualcosa da backfillare.
    with monkeypatch.context() as patch:
        patch.setattr(separator, "ensure_extra", lambda *args, **kwargs: None)
        pkg = factories.Dataset(
            notes=NOTE,
            resources=[{"format": "CSV", "url": "http://example.com/eventi.csv"}],
        )

    runner = CliRunner()
    result = runner.invoke(extract_separators, ["--dataset", pkg["id"]])
    assert result.exit_code == 0, result.output
    assert "Da aggiornare: 1" in result.output
    assert _extra(pkg["id"]) is None

    result = runner.invoke(extract_separators, ["--dataset", pkg["id"], "--apply"])
    assert result.exit_code == 0, result.output
    assert "Aggiornati: 1" in result.output
    assert _extra(pkg["id"]) == ";"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_extract_separators_missing_dataset():
    result = CliRunner().invoke(extract_separators, ["--dataset", "dataset-che-non-esiste"])
    assert result.exit_code != 0
    assert "Dataset non trovato" in result.output
