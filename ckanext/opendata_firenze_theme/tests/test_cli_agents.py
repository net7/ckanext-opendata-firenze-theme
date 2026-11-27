"""Backfill dei nomi ente (`ckan odf-normalize-agents`)."""

import json
from types import SimpleNamespace

import pytest
from ckan.plugins import toolkit
from ckan.tests import factories
from click.testing import CliRunner

import ckanext.opendata_firenze_theme.plugin as theme_plugin
from ckanext.opendata_firenze_theme.cli import normalize_agents
from ckanext.opendata_firenze_theme.helpers import agents

PLUGIN = "opendata_firenze_theme"

CREATOR = json.dumps(
    [
        {
            "creator_identifier": "c_d612",
            "creator_name": {
                "it": "Comune di Firenze - Direzione Ambiente",
                "en": "Comune di Firenze - Direzione Ambiente",
            },
        }
    ]
)


def _show(pkg_id):
    return toolkit.get_action("package_show")({"ignore_auth": True}, {"id": pkg_id})


def _extras(pkg):
    extras = pkg.get("extras") or {}
    if isinstance(extras, dict):
        return extras
    return {e.get("key"): e.get("value") for e in extras if isinstance(e, dict)}


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_normalize_agents_dry_run_then_apply(monkeypatch):
    # Crea il dataset senza far scattare il chained action, così il CLI ha
    # davvero qualcosa da backfillare.
    with monkeypatch.context() as patch:
        patch.setattr(agents, "normalize_package", lambda data: data)
        pkg = factories.Dataset(
            author="Comune di Firenze - Direzione Cultura",
            notes="Fonte: Comune di Firenze - Direzione Cultura.",
        )

    runner = CliRunner()
    result = runner.invoke(normalize_agents, ["--dataset", pkg["id"]])
    assert result.exit_code == 0, result.output
    assert "Da aggiornare: 1" in result.output
    assert _show(pkg["id"])["author"] == "Comune di Firenze - Direzione Cultura"

    # Il hook del tema è disattivato: qui deve funzionare il patch del comando,
    # non la seconda normalizzazione di package_update.
    with monkeypatch.context() as patch:
        patch.setattr(
            theme_plugin,
            "agents",
            SimpleNamespace(normalize_package=lambda data: data),
        )
        result = runner.invoke(normalize_agents, ["--dataset", pkg["id"], "--apply"])
    assert result.exit_code == 0, result.output
    assert "Aggiornati: 1" in result.output
    data = _show(pkg["id"])
    assert data["author"] == "Direzione Cultura"
    assert data["notes"] == "Fonte: Direzione Cultura."


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_normalize_agents_apply_normalizes_extras(monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(agents, "normalize_package", lambda data: data)
        pkg = factories.Dataset(
            extras=[
                {"key": "holder_name", "value": "Comune di Firenze - Direzione Cultura"},
                {"key": "creator", "value": CREATOR},
            ]
        )

    with monkeypatch.context() as patch:
        patch.setattr(
            theme_plugin,
            "agents",
            SimpleNamespace(normalize_package=lambda data: data),
        )
        result = CliRunner().invoke(normalize_agents, ["--dataset", pkg["id"], "--apply"])
    assert result.exit_code == 0, result.output
    assert "Aggiornati: 1" in result.output

    extras = _extras(_show(pkg["id"]))
    assert extras["holder_name"] == "Direzione Cultura"
    assert json.loads(extras["creator"])[0]["creator_name"]["it"] == "Direzione Ambiente"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_normalize_agents_skips_clean_dataset(monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(agents, "normalize_package", lambda data: data)
        pkg = factories.Dataset(author="Direzione Cultura", notes="Nessun prefisso.")

    result = CliRunner().invoke(normalize_agents, ["--dataset", pkg["id"]])
    assert result.exit_code == 0, result.output
    assert "Da aggiornare: 0" in result.output
    assert "già puliti: 1" in result.output


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_normalize_agents_missing_dataset():
    result = CliRunner().invoke(normalize_agents, ["--dataset", "dataset-che-non-esiste"])
    assert result.exit_code != 0
    assert "Dataset non trovato" in result.output
