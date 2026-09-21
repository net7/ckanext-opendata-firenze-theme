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
