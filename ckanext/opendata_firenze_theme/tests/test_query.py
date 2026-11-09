"""Query per intento e policy di visibilità del catalogo (`helpers.query`)."""

import pytest

PLUGIN = "opendata_firenze_theme"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_hide_revisions_adds_filter(with_plugins):
    """La ricerca normale esclude le revisioni, mantenendo gli altri filtri."""
    from ckanext.opendata_firenze_theme.helpers import query

    params = {"q": "aria", "fq": "capacity:public"}
    assert query.hide_revisions(params) == {
        "q": "aria",
        "fq": "capacity:public -extras_is_version_of:[* TO *]",
    }
    # un fq già presente come lista viene appiattito, non perso
    assert query.hide_revisions({"fq": ["a:1", "b:2"]})["fq"] == (
        "a:1 b:2 -extras_is_version_of:[* TO *]"
    )


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_hide_revisions_bypass_when_explicit(with_plugins):
    """Chi cerca esplicitamente `is_version_of` deve vedere le revisioni."""
    from ckanext.opendata_firenze_theme.helpers import query

    explicit = {"fq": 'extras_is_version_of:"https://example.test/dataset/x"'}
    assert query.hide_revisions(dict(explicit)) == explicit
    # anche una query libera che nomina il campo non viene filtrata
    assert query.hide_revisions({"q": "extras_is_version_of:y"}) == {"q": "extras_is_version_of:y"}


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_dataset_facets_inserts_after_organization(with_plugins, with_request_context):
    """Le faccette del tema stanno subito dopo "Chi pubblica"."""
    from ckanext.opendata_firenze_theme.helpers import query

    got = query.dataset_facets({"theme": "Temi", "organization": "Chi pubblica", "tags": "Tags"})
    assert list(got) == ["theme", "organization", "odf_features", "odf_series", "tags"]
    assert got["odf_features"] == "Caratteristiche"
    assert got["odf_series"] == "Serie"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_dataset_facets_without_anchor(with_plugins, with_request_context):
    """Senza la faccetta di ancoraggio i gruppi del tema ci sono comunque."""
    from ckanext.opendata_firenze_theme.helpers import query

    got = query.dataset_facets({"tags": "Tags"})
    assert list(got) == ["tags", "odf_features", "odf_series"]


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_query_strings(with_plugins):
    """Forma delle query: un solo posto per i nomi dei campi Solr."""
    from ckanext.opendata_firenze_theme.helpers import query

    assert query.features(query.GEO) == "odf_features:geo"
    assert query.features(query.LOD) == "odf_features:lod"
    assert query.hvd() == "extras_hvd:true"
    assert query.series_member("Open Firenze") == 'extras_serie:"Open Firenze"'
    assert query.series_any() == "extras_serie:[* TO *]"
    assert query.revision("https://x/dataset/a") == 'extras_is_version_of:"https://x/dataset/a"'
    assert query.chapter("Popolazione") == 'extras_capitolo:"Popolazione"'
    assert query.chapter_any() == "extras_capitolo:[* TO *]"
