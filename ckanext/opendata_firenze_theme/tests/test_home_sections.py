"""Dati dei blocchi della home raccolti dal collettore (`helpers.home_sections`)."""

import re
from pathlib import Path
from unittest import mock

import pytest

PLUGIN = "opendata_firenze_theme"
TEMPLATES = Path(__file__).resolve().parents[1] / "templates"


def test_every_block_has_a_builder():
    """Un blocco senza dati romperebbe la home: il test lo blocca prima."""
    from ckanext.opendata_firenze_theme.helpers import home_blocks

    assert all(callable(block.get("builder")) for block in home_blocks.BLOCKS)


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_sections_payload_for_every_block(with_plugins):
    """Chiavi e limiti di ogni blocco: un payload sbagliato svuota la sezione."""
    from ckanext.opendata_firenze_theme.helpers import home, home_blocks, home_sections

    with (
        mock.patch.object(home, "odf_dataset_count", return_value=7),
        mock.patch.object(home, "odf_home_kpis", return_value=["kpi"]) as kpi,
        mock.patch.object(home, "odf_featured_datasets", return_value=["f"]) as featured,
        mock.patch.object(home, "odf_latest_datasets", return_value=["l"]) as latest,
        mock.patch.object(home, "odf_themes_visible", return_value=["t"]) as themes,
        mock.patch.object(home, "odf_lod_datasets", return_value=["o"]) as lod,
        mock.patch.object(home, "odf_most_viewed", return_value=["v"]) as viewed,
        mock.patch.object(home, "odf_most_viewed_label", return_value="periodo") as label,
        mock.patch.object(home, "odf_news", return_value=["n"]) as news,
    ):
        got = home_sections.odf_home_sections([{"id": b["id"]} for b in home_blocks.BLOCKS])

    assert got["hero"] == {"count": 7}
    assert got["kpi"] == {"kpis": ["kpi"]}
    assert got["featured"] == {"datasets": ["f"], "facts": {}}
    assert got["latest"] == {"datasets": ["l"], "facts": {}}
    assert got["themes"] == {"themes": ["t"]}
    assert got["lod"] == {"datasets": ["o"], "facts": {}}
    assert got["most_viewed"] == {"datasets": ["v"], "facts": {}, "period_label": "periodo"}
    assert got["news"] == {"news": ["n"]}
    kpi.assert_called_once_with(total=7)
    featured.assert_called_once_with(7)
    latest.assert_called_once_with(6)
    lod.assert_called_once_with(6)
    viewed.assert_called_once_with(4, "year")
    label.assert_called_once_with("year")
    news.assert_called_once_with(3)
    themes.assert_called_once_with()


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_most_viewed_period_comes_from_block(with_plugins):
    from ckanext.opendata_firenze_theme.helpers import home, home_sections

    with (
        mock.patch.object(home, "odf_most_viewed", return_value=["v"]) as viewed,
        mock.patch.object(home, "odf_most_viewed_label", return_value="settimana") as label,
    ):
        got = home_sections.odf_home_sections([{"id": "most_viewed", "period": "week"}])

    assert got["most_viewed"] == {"datasets": ["v"], "facts": {}, "period_label": "settimana"}
    viewed.assert_called_once_with(4, "week")
    label.assert_called_once_with("week")


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_most_viewed_falls_back_without_period_label(with_plugins):
    """Se il tracking non risponde si mostrano i recenti, senza etichetta."""
    from ckanext.opendata_firenze_theme.helpers import home, home_sections

    recent = [{"id": "recent"}]
    with (
        mock.patch.object(home, "odf_most_viewed", return_value=None),
        mock.patch.object(home, "odf_most_viewed_fallback", return_value=recent) as latest,
        mock.patch.object(home, "odf_most_viewed_label") as label,
    ):
        got = home_sections.odf_home_sections([{"id": "most_viewed"}])

    latest.assert_called_once_with(4)
    label.assert_not_called()
    assert got["most_viewed"]["datasets"] is recent
    assert got["most_viewed"]["period_label"] == ""
    assert set(got["most_viewed"]["facts"]) == {"recent"}
    assert recent[0]["views_period"] == 0


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_sections_cover_active_blocks_in_order(with_plugins):
    from ckanext.opendata_firenze_theme.helpers import home, home_sections

    with (
        mock.patch.object(home, "odf_latest_datasets", return_value=["a"]) as latest,
        mock.patch.object(home, "odf_news", return_value=["n"]) as news,
    ):
        got = home_sections.odf_home_sections([{"id": "latest"}, {"id": "news"}])

    assert list(got) == ["latest", "news"]
    assert got["latest"] == {"datasets": ["a"], "facts": {}}
    assert got["news"] == {"news": ["n"]}
    latest.assert_called_once_with(6)
    news.assert_called_once_with(3)


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_facts_are_shared_between_blocks(with_plugins):
    """Un dataset in due blocchi calcola i fatti una volta per render."""
    from ckanext.opendata_firenze_theme.helpers import dataset, home, home_sections

    pkg = {"id": "a"}
    calls = []
    with (
        mock.patch.object(
            dataset,
            "odf_dataset_facts",
            side_effect=lambda item: calls.append(item["id"]) or {"id": item["id"]},
        ),
        mock.patch.object(home, "odf_latest_datasets", return_value=[pkg]),
        mock.patch.object(home, "odf_lod_datasets", return_value=[pkg]),
    ):
        got = home_sections.odf_home_sections([{"id": "latest"}, {"id": "lod"}])

    assert calls == ["a"]
    assert got["latest"]["facts"]["a"] is got["lod"]["facts"]["a"]


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_sections_share_the_catalog_count(with_plugins):
    """Hero e KPI usano lo stesso conteggio: una sola `package_search`."""
    from ckanext.opendata_firenze_theme.helpers import home, home_sections

    kpis = [{"value": "10"}]
    with (
        mock.patch.object(home, "odf_dataset_count", return_value=10) as count,
        mock.patch.object(home, "odf_home_kpis", return_value=kpis) as kpi,
    ):
        got = home_sections.odf_home_sections([{"id": "hero"}, {"id": "kpi"}])

    count.assert_called_once()
    kpi.assert_called_once_with(total=10)
    assert got["hero"] == {"count": 10}
    assert got["kpi"] == {"kpis": kpis}


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_sections_skip_inactive_blocks(with_plugins):
    """Un blocco disattivato non deve fare query."""
    from ckanext.opendata_firenze_theme.helpers import home, home_sections

    with (
        mock.patch.object(home, "odf_news") as news,
        mock.patch.object(home, "odf_most_viewed") as viewed,
        mock.patch.object(home, "odf_dataset_count", return_value=3),
    ):
        got = home_sections.odf_home_sections([{"id": "hero"}])

    assert got == {"hero": {"count": 3}}
    news.assert_not_called()
    viewed.assert_not_called()


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_block_templates_use_collector_payload(with_plugins):
    """Il join builder → template: ogni chiave letta esiste nel payload."""
    from ckanext.opendata_firenze_theme.helpers import home, home_blocks, home_sections

    with (
        mock.patch.object(home, "odf_dataset_count", return_value=0),
        mock.patch.object(home, "odf_home_kpis", return_value=[]),
        mock.patch.object(home, "odf_featured_datasets", return_value=[]),
        mock.patch.object(home, "odf_latest_datasets", return_value=[]),
        mock.patch.object(home, "odf_themes_visible", return_value=[]),
        mock.patch.object(home, "odf_lod_datasets", return_value=[]),
        mock.patch.object(home, "odf_most_viewed", return_value=[]),
        mock.patch.object(home, "odf_news", return_value=[]),
    ):
        payloads = home_sections.odf_home_sections([{"id": b["id"]} for b in home_blocks.BLOCKS])

    for block in home_blocks.BLOCKS:
        source = (TEMPLATES / block["template"]).read_text()
        used = set(re.findall(r"block_data\.([a-z_]+)", source))
        assert used <= set(payloads[block["id"]]), block["id"]
