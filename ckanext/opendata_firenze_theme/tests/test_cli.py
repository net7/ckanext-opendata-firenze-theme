"""Comando di pulizia delle viste mappa duplicate."""

import pytest

pytest.importorskip("ckanext.geoview")

from ckan import model  # noqa: E402
from ckan.tests import factories  # noqa: E402
from click.testing import CliRunner  # noqa: E402

from ckanext.opendata_firenze_theme.cli import cleanup_map_views  # noqa: E402

PLUGIN = "opendata_firenze_theme"
VIEW_PLUGINS = f"{PLUGIN} geo_view geojson_view"


@pytest.mark.ckan_config("ckan.plugins", VIEW_PLUGINS)
@pytest.mark.usefixtures("with_plugins")
def test_cleanup_map_views_dry_run_then_delete():
    pkg = factories.Dataset()
    res = factories.Resource(
        package_id=pkg["id"],
        name="GeoJSON di prova",
        format="GeoJSON",
        url="http://example.com/prova.geojson",
    )
    generic = factories.ResourceView(
        resource_id=res["id"],
        title="Map viewer",
        description="",
        view_type="geo_view",
    )
    dedicated = factories.ResourceView(
        resource_id=res["id"], title="GeoJSON", view_type="geojson_view"
    )
    runner = CliRunner()

    result = runner.invoke(cleanup_map_views, ["--resource-id", res["id"]])
    assert result.exit_code == 0, result.output
    assert generic["id"] in result.output
    assert dedicated["id"] not in result.output
    assert model.ResourceView.get(generic["id"]) is not None

    result = runner.invoke(cleanup_map_views, ["--resource-id", res["id"], "--delete"])
    assert result.exit_code == 0, result.output
    assert model.ResourceView.get(generic["id"]) is None
    assert model.ResourceView.get(dedicated["id"]) is not None


def test_cleanup_refuses_without_geojson_view(monkeypatch):
    """Senza il viewer dedicato non si devono eliminare le mappe generiche."""
    from ckanext.opendata_firenze_theme import cli

    monkeypatch.setattr(cli, "get_view_plugin", lambda name: None)
    result = CliRunner().invoke(cli.cleanup_map_views, [])
    assert result.exit_code != 0
    assert "geojson_view non e' abilitato" in result.output


@pytest.mark.ckan_config("ckan.plugins", VIEW_PLUGINS)
@pytest.mark.usefixtures("with_plugins")
def test_cleanup_delete_keeps_customized_views():
    """--delete non tocca le viste personalizzate; --all sì."""
    pkg = factories.Dataset()
    res = factories.Resource(
        package_id=pkg["id"],
        name="GeoJSON di prova",
        format="GeoJSON",
        url="http://example.com/prova.geojson",
    )
    factories.ResourceView(resource_id=res["id"], title="GeoJSON", view_type="geojson_view")
    custom = factories.ResourceView(
        resource_id=res["id"],
        title="Mia mappa",
        description="Configurazione personalizzata",
        view_type="geo_view",
    )
    runner = CliRunner()

    result = runner.invoke(cleanup_map_views, ["--resource-id", res["id"], "--delete"])
    assert result.exit_code == 0, result.output
    assert model.ResourceView.get(custom["id"]) is not None
    assert "personalizzate lasciate" in result.output

    result = runner.invoke(cleanup_map_views, ["--resource-id", res["id"], "--all"])
    assert result.exit_code == 0, result.output
    assert model.ResourceView.get(custom["id"]) is None
