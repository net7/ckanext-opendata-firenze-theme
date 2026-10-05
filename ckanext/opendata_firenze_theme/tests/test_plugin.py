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
@pytest.mark.ckan_config("ckan.locales_offered", "en fr")
@pytest.mark.usefixtures("with_plugins")
def test_language_selector_offers_only_configured_locales(app, monkeypatch):
    """Il selettore lista solo le lingue in ckan.locales_offered.

    ``ckan.lib.i18n`` tiene le lingue in cache in variabili di modulo, senza un
    reset pubblico: le azzero con ``monkeypatch`` (ripristinate a fine test)
    per rendere il test indipendente dall'ordine di esecuzione.
    """
    import ckan.lib.i18n as i18n

    for name in ("locales", "available_locales", "locales_dict", "_non_translated_locals"):
        monkeypatch.setattr(i18n, name, None)

    response = app.get("/about")
    assert response.status_code == 200
    body = response.body
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    assert 'href="/fr/about"' in body
    assert 'href="/de/about"' not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.ckan_config("ckan.locales_offered", "it en")
@pytest.mark.ckan_config("ckan.locale_default", "it")
@pytest.mark.usefixtures("with_plugins")
def test_language_selector_default_locale_has_no_prefix(app, monkeypatch):
    """La lingua di default non porta il prefisso in URL; le altre sì."""
    import ckan.lib.i18n as i18n

    for name in ("locales", "available_locales", "locales_dict", "_non_translated_locals"):
        monkeypatch.setattr(i18n, name, None)

    response = app.get("/about")
    body = response.body
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    assert 'href="/en/about"' in body
    assert 'href="/it/about"' not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.ckan_config("ckan.locales_offered", "it en")
@pytest.mark.ckan_config("ckan.locale_default", "it")
@pytest.mark.usefixtures("with_plugins")
def test_language_selector_switch_back_from_en_has_no_prefix(app, monkeypatch):
    """Dalla pagina in inglese il link italiano torna a `/…` (niente `/it/…`)."""
    import re

    import ckan.lib.i18n as i18n

    for name in ("locales", "available_locales", "locales_dict", "_non_translated_locals"):
        monkeypatch.setattr(i18n, name, None)

    response = app.get("/en/about")
    body = response.body
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    # solo i link del selettore lingua (evita falsi positivi da altri link /about)
    lang_links = re.findall(r'class="rtt-lang__item[^"]*" href="([^"]*)"', body)
    assert "/about" in lang_links
    assert "/en/about" in lang_links
    assert "/it/about" not in lang_links


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
        "odf_facet_groups",
        "odf_home_kpis",
        "odf_themes",
        "odf_featured_datasets",
        "odf_most_viewed",
        "odf_geo_datasets",
        "odf_geo_search_query",
        "odf_news",
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
        "odf_default_locale",
        "odf_dataset_openness",
        "odf_dataset_related",
        "odf_dataset_revisions",
        "odf_dataset_series",
        "odf_dataset_contact",
        "odf_dataset_downloads",
        "odf_resource_download_url",
        "odf_resource_preview_url",
        "odf_resource_view_title",
        "odf_dataset_size",
        "odf_sql_console_enabled",
        "odf_datastore_resource_id",
        "odf_date",
        "odf_frequency_label",
        "odf_filesize",
        "odf_time_ago",
    }
    assert set(helpers.get_helpers()) == expected


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
