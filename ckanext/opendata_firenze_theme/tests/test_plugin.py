import pytest
from ckan.plugins import plugin_loaded

PLUGIN = "opendata_firenze_theme"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_plugin():
    assert plugin_loaded(PLUGIN)


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_theme_assets_are_included(app):
    """La pagina /about include gli asset del tema (bundle CSS/JS).

    Fa da smoke test del bundle WebAssets: se la definizione in
    assets/webassets.yml o il build del bundle sono rotti, la pagina non
    renderizza o non referenzia gli asset del tema.
    """
    response = app.get("/about")
    assert response.status_code == 200
    body = response.body
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    assert PLUGIN in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_shell_header_and_footer(app):
    """L'header, il footer e la tab bar del tema sono renderizzati."""
    response = app.get("/about")
    assert response.status_code == 200
    body = response.body
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    assert 'class="rtt-header"' in body
    assert 'class="masthead"' not in body
    assert "account-masthead" not in body
    assert 'class="rtt-footer"' in body
    assert 'class="rtt-tabbar"' in body
    assert 'id="rtt-header-search"' in body
    assert 'id="rtt-mobile-search"' in body
    assert "Segnala un dataset" in body
    assert "Palazzo Vecchio" in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_no_duplicate_ids(app):
    """Nessun id duplicato nel DOM e wordmark reso 2x (header + footer).

    Il wordmark è un <img> (niente SVG inline): questo test impedisce che
    torni a essere inlinato due volte con id SVG duplicati.
    """
    import re
    from collections import Counter

    body = app.get("/about").body
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    # Un'immagine per wordmark (header + footer); l'SVG inline avrebbe dato 0.
    assert body.count("/brand/open-data.svg") == 2
    ids = re.findall(r'\sid="([^"]+)"', body)
    dupes = {i: n for i, n in Counter(ids).items() if n > 1}
    assert not dupes, f"id duplicati nel DOM: {dupes}"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_template_helpers_registered():
    """Il tema registra l'insieme completo degli helper dei template.

    Guardia sulle riorganizzazioni del package `helpers`: se un helper viene
    rinominato o non è più importato in `get_helpers()`, i template lo perdono
    in silenzio (verrebbe reso come vuoto, non come errore). L'elenco è
    esplicito: va aggiornato quando si aggiunge/rimuove un helper.
    """
    from ckanext.opendata_firenze_theme import helpers

    expected = {
        "odf_dataset_count",
        "odf_package_theme",
        "odf_facet_all_url",
        "odf_active_filters",
        "odf_facet_groups",
        "odf_home_kpis",
        "odf_home_sections",
        "odf_themes",
        "odf_themes_visible",
        "odf_featured_datasets",
        "odf_most_viewed",
        "odf_geo_datasets",
        "odf_geo_search_query",
        "odf_news",
        "odf_home_blocks",
        "odf_annuario_chapters",
        "odf_annuario_count",
        "odf_annuario_datasets",
        "odf_pkg_extra",
        "odf_dataset_formats",
        "odf_format_is_geo",
        "odf_dataset_badges",
        "odf_dataset_geometry",
        "odf_dataset_is_geo",
        "odf_number",
        "odf_dataset_openness",
        "odf_dataset_related",
        "odf_dataset_revisions",
        "odf_dataset_series",
        "odf_series_info",
        "odf_series_context",
        "odf_dataset_contact",
        "odf_dataset_downloads",
        "odf_resource_download_url",
        "odf_resource_preview_url",
        "odf_resource_view_title",
        "odf_dataset_size",
        "odf_latest_datasets",
        "odf_lod_datasets",
        "odf_resource_filename",
        "odf_resource_separator",
        "odf_dataset_is_lod",
        "odf_dataset_is_hvd",
        "odf_dataset_is_realtime",
        "odf_dataset_is_series",
        "odf_dataset_map_resource",
        "odf_views_map_first",
        "odf_sql_console_enabled",
        "odf_datastore_resource_id",
        "odf_date",
        "odf_frequency_label",
        "odf_filesize",
        "odf_time_ago",
    }
    assert set(helpers.get_helpers()) == expected


def test_helper_registry_is_derived_from_modules():
    """Il registro viene dai `HELPERS` dei moduli, non da un elenco a parte.

    Se un helper finisce in un modulo ma non nel suo `HELPERS`, il template lo
    perde in silenzio; se il nome della chiave non coincide con la funzione, il
    test lo segnala subito invece di far rendere vuoto un `h.odf_*`.
    """
    from ckanext.opendata_firenze_theme import helpers

    declared = {}
    for module in helpers.HELPER_MODULES:
        for name, function in module.HELPERS.items():
            assert function.__name__ == name, f"{module.__name__}: {name}"
            assert name not in declared, f"{name} dichiarato due volte"
            declared[name] = function

    assert set(helpers.get_helpers()) == set(declared)
    assert set(declared) <= set(helpers.__all__)


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_search_hides_revisions():
    """Il catalogo nasconde le revisioni, ma il pannello/la ricerca esplicita no."""
    from ckanext.opendata_firenze_theme.plugin import OpendataFirenzeThemePlugin

    plugin = OpendataFirenzeThemePlugin()

    # catalogo normale: esclude i dataset con `is_version_of`
    params = plugin.before_dataset_search({"q": "*:*", "fq": "x:1"})
    assert params["fq"] == "x:1 -extras_is_version_of:[* TO *]"

    # il pannello "Revisioni temporali" cita is_version_of: bypass
    params = plugin.before_dataset_search({"q": 'extras_is_version_of:"u"'})
    assert "fq" not in params
    params = plugin.before_dataset_search({"q": "*:*", "fq": 'extras_is_version_of:"u"'})
    assert params["fq"] == 'extras_is_version_of:"u"'

    # un testo generico che contiene solo la parola "is_version_of" non bypassa
    params = plugin.before_dataset_search({"q": "is_version_of senza il campo"})
    assert "-extras_is_version_of:[* TO *]" in params["fq"]


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_favicon_is_the_theme_giglio(app):
    """Senza ckan.favicon esplicita la pagina usa il giglio del tema, con le varianti PNG."""
    body = app.get("/about").body
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    assert '<link rel="shortcut icon" href="/brand/favicon.ico" />' in body
    assert "/base/images/ckan.ico" not in body
    assert "/brand/favicon-32.png" in body
    assert "/brand/apple-touch-icon.png" in body
    for path in ("/brand/favicon.ico", "/brand/favicon-32.png", "/brand/apple-touch-icon.png"):
        assert app.get(path).status_code == 200, path


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.ckan_config("ckan.favicon", "/altra.ico")
@pytest.mark.usefixtures("with_plugins")
def test_favicon_respects_explicit_config(app):
    """Una ckan.favicon impostata nella configurazione vince sul giglio del tema."""
    body = app.get("/about").body
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    assert '<link rel="shortcut icon" href="/altra.ico" />' in body
    assert "/brand/favicon-32.png" not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_dataset_facets_adds_theme_groups(with_plugins):
    """ "Caratteristiche" e "Serie" sono faccette del tema, dopo "Chi pubblica"."""
    from ckanext.opendata_firenze_theme.plugin import OpendataFirenzeThemePlugin

    facets = {"organization": "Organizzazioni", "tags": "Tag"}
    got = OpendataFirenzeThemePlugin().dataset_facets(facets, "dataset")
    assert list(got) == ["organization", "odf_features", "odf_series", "tags"]
    assert got["odf_features"] == "Caratteristiche"
    assert got["odf_series"] == "Serie"
