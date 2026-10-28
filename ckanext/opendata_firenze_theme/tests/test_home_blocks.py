"""Blocchi configurabili della homepage (config, ordine, testi, URL, admin)."""

import json
from unittest import mock

import pytest
from ckan.tests import factories

PLUGIN = "opendata_firenze_theme"

# SESSION_COOKIE_DOMAIN di test-core.ini: le richieste autenticate nei test
# devono usare questo host, altrimenti il cookie di sessione non viene inviato
# (nel container CKAN_SITE_URL sovrascrive ckan.site_url col dominio di sviluppo).
_TEST_BASE_URL = "http://test.ckan.net"


def _hb():
    from ckanext.opendata_firenze_theme.helpers import home_blocks

    return home_blocks


def _body(app):
    body = app.get("/").body
    return body.decode("utf-8") if isinstance(body, bytes) else body


def _response_body(response):
    body = response.body
    return body.decode("utf-8") if isinstance(body, bytes) else body


def test_default_order_and_texts():
    hb = _hb()
    with mock.patch.object(hb, "_raw_value", return_value=""):
        blocks = {block["id"]: block for block in hb.odf_home_blocks()}
    assert list(blocks) == ["hero", "kpi", "featured", "themes", "most_viewed", "news"]
    assert blocks["featured"]["title"] == "In evidenza"
    assert blocks["featured"]["cta_label"] == "Vedi tutti"
    assert blocks["featured"]["cta_url"] == "/dataset"
    assert blocks["themes"]["subtitle"].startswith("Sfoglia i dati per argomento")
    assert blocks["news"]["cta_url"] == "/blog"
    assert blocks["hero"]["title"] == ""


def test_configured_order_disabled_and_texts():
    hb = _hb()
    raw = json.dumps(
        [
            {
                "id": "featured",
                "enabled": True,
                "title": "In primo piano",
                "subtitle": "Sottotitolo",
                "cta_label": "Apri",
                "cta_url": "/dataset?q=ambiente",
            },
            {"id": "hero", "enabled": True},
            {"id": "news", "enabled": False, "title": "Notizie"},
        ]
    )
    with mock.patch.object(hb, "_raw_value", return_value=raw):
        blocks = hb.odf_home_blocks()
    assert [block["id"] for block in blocks] == ["featured", "hero"]
    assert blocks[0]["title"] == "In primo piano"
    assert blocks[0]["subtitle"] == "Sottotitolo"
    assert blocks[0]["cta_label"] == "Apri"
    assert blocks[0]["cta_url"] == "/dataset?q=ambiente"


def test_partial_entry_uses_defaults():
    """Una config parziale/vecchia (campo assente) usa il default, non lo svuota."""
    hb = _hb()
    raw = json.dumps([{"id": "featured", "enabled": True, "title": "Titolo"}])
    with mock.patch.object(hb, "_raw_value", return_value=raw):
        blocks = hb.odf_home_blocks()
    assert blocks[0]["title"] == "Titolo"
    assert blocks[0]["cta_label"] == "Vedi tutti"
    assert blocks[0]["cta_url"] == "/dataset"
    assert blocks[0]["subtitle"] == ""


def test_legacy_list_of_ids():
    hb = _hb()
    with mock.patch.object(hb, "_raw_value", return_value='["hero", "kpi"]'):
        blocks = hb.odf_home_blocks()
    assert [block["id"] for block in blocks] == ["hero", "kpi"]
    assert all(block["title"] == "" for block in blocks)


def test_parse_config():
    hb = _hb()
    assert hb._parse_config("") is None
    assert hb._parse_config("non-json") is None
    assert hb._parse_config('{"a": 1}') is None
    # elenco vuoto esplicito -> nessun blocco attivo, ma tutti presenti
    empty = hb._parse_config("[]")
    assert empty is not None
    assert len(empty) == len(hb.DEFAULT_IDS)
    assert all(not entry["enabled"] for entry in empty)


def test_admin_state_fields_and_order():
    hb = _hb()
    raw = json.dumps(
        [
            {"id": "news", "enabled": False, "title": "Notizie"},
            {"id": "hero", "enabled": True},
        ]
    )
    with mock.patch.object(hb, "_raw_value", return_value=raw):
        blocks = {block["id"]: block for block in hb.odf_home_blocks_admin()}
    assert blocks["news"]["order"] == 0 and not blocks["news"]["enabled"]
    assert blocks["news"]["title"] == "Notizie"
    assert set(blocks["news"]["fields"]) == {"title", "subtitle", "cta_label", "cta_url"}
    assert blocks["hero"]["order"] == 1 and blocks["hero"]["enabled"]
    assert blocks["hero"]["fields"] == {}


def test_entries_from_form():
    hb = _hb()
    entries = hb.entries_from_form(
        ["featured", "hero", "featured"],  # duplicato: una sola voce
        {
            "hero": "1",
            "kpi": "2",
            "featured": "0",
            "themes": "3",
            "most_viewed": "4",
            "news": "5",
        },
        {
            "featured": {
                "title": " Titolo ",
                "subtitle": "Sub",
                "cta_label": "Vai",
                "cta_url": "/dataset?q=x",
            },
            "hero": {"title": "ignorato dai blocchi senza campi"},
        },
        ["hero", "kpi", "featured", "themes", "most_viewed", "news"],
    )
    by_id = {entry["id"]: entry for entry in entries}
    assert [entry["id"] for entry in entries] == [
        "featured",
        "hero",
        "kpi",
        "themes",
        "most_viewed",
        "news",
    ]
    assert by_id["featured"] == {
        "id": "featured",
        "enabled": True,
        "title": "Titolo",
        "subtitle": "Sub",
        "cta_label": "Vai",
        "cta_url": "/dataset?q=x",
    }
    assert by_id["hero"]["enabled"] is True
    assert by_id["hero"]["title"] == ""
    assert by_id["kpi"]["enabled"] is False
    assert len(entries) == len(hb.DEFAULT_IDS)


def test_valid_url():
    hb = _hb()
    assert hb._valid_url("")
    assert hb._valid_url("/dataset")
    assert hb._valid_url("/dataset?q=a&b=c")
    assert hb._valid_url("https://example.org/x")
    for bad in ("javascript:alert(1)", "//evil.example", "dataset", "http://", "/x y", "/\\evil"):
        assert not hb._valid_url(bad), bad


def test_validate_entries():
    hb = _hb()
    assert hb.validate_entries([{"id": "featured", "cta_url": "/dataset?q=ambiente"}]) == {}
    assert hb.validate_entries([{"id": "news", "cta_url": "https://example.org/news"}]) == {}
    errors = hb.validate_entries(
        [
            {"id": "featured", "cta_url": "javascript:alert(1)"},
            {"id": "news", "cta_url": "//evil.example"},
        ]
    )
    assert "cta_url" in errors["featured"]
    assert "cta_url" in errors["news"]


def test_invalid_stored_url_is_dropped():
    """Un URL non valido scritto direttamente via API non finisce nell'href."""
    hb = _hb()
    raw = json.dumps([{"id": "featured", "enabled": True, "cta_url": "javascript:alert(1)"}])
    with mock.patch.object(hb, "_raw_value", return_value=raw):
        blocks = hb.odf_home_blocks()
    assert blocks[0]["cta_url"] == ""


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_config_schema_exposes_option():
    from ckan.logic.schema import update_configuration_schema

    assert _hb().OPTION in update_configuration_schema()


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_admin_homepage_requires_sysadmin(app):
    """Senza sessione la pagina admin risponde 403, non 500."""
    assert app.get("/ckan-admin/homepage").status_code == 403


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_admin_homepage_rejects_invalid_cta_url(app):
    """Un URL non valido non viene salvato e il form lo segnala."""
    user = factories.Sysadmin()
    app.set_session_user(user["name"])
    # base_url allineato a SESSION_COOKIE_DOMAIN dei test (nel container
    # CKAN_SITE_URL sovrascrive ckan.site_url con il dominio di sviluppo)
    response = app.post(
        "/ckan-admin/homepage",
        base_url=_TEST_BASE_URL,
        data={
            "enabled": "featured",
            "order_featured": "0",
            "title_featured": "In evidenza",
            "cta_label_featured": "Vedi tutti",
            "cta_url_featured": "javascript:alert(1)",
            "save": "1",
        },
    )
    body = _response_body(response)
    assert response.status_code == 200
    assert "Inserisci un percorso" in body
    assert 'aria-invalid="true"' in body

    from ckan import model

    assert model.get_system_info(_hb().OPTION) is None


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_admin_homepage_saves_valid_cta_url(app):
    user = factories.Sysadmin()
    app.set_session_user(user["name"])
    # base_url allineato a SESSION_COOKIE_DOMAIN dei test (nel container
    # CKAN_SITE_URL sovrascrive ckan.site_url con il dominio di sviluppo)
    response = app.post(
        "/ckan-admin/homepage",
        base_url=_TEST_BASE_URL,
        follow_redirects=False,
        data={
            "enabled": "featured",
            "order_featured": "0",
            "title_featured": "In evidenza",
            "cta_label_featured": "Vedi tutti",
            "cta_url_featured": "/dataset?q=ambiente",
            "save": "1",
        },
    )
    assert response.status_code == 302

    from ckan import model
    from ckan.common import config

    try:
        entries = json.loads(model.get_system_info(_hb().OPTION))
        featured = next(entry for entry in entries if entry["id"] == "featured")
        assert featured["cta_url"] == "/dataset?q=ambiente"
        assert featured["enabled"] is True
    finally:
        # il valore salvato resterebbe in system_info anche dopo clean_db e
        # influenzerebbe i test successivi (che non usano clean_db); inoltre
        # config_option_update aggiorna anche la config in-memory del processo.
        model.delete_system_info(_hb().OPTION)
        config[_hb().OPTION] = ""


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_home_renders_configured_order(app):
    hb = _hb()
    raw = json.dumps([{"id": "kpi", "enabled": True}, {"id": "hero", "enabled": True}])
    with mock.patch.object(hb, "_raw_value", return_value=raw):
        body = _body(app)
    assert body.index("rtt-kpistrip") < body.index("rtt-hero")


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_home_hides_disabled_block(app):
    hb = _hb()
    raw = json.dumps([{"id": "hero", "enabled": True}])
    with mock.patch.object(hb, "_raw_value", return_value=raw):
        body = _body(app)
    assert "rtt-hero" in body
    assert "rtt-kpistrip" not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_home_renders_custom_texts(app):
    factories.Dataset(title="Dataset di prova")
    hb = _hb()
    raw = json.dumps(
        [
            {
                "id": "featured",
                "enabled": True,
                "title": "Scelti per te",
                "cta_label": "Vedi la selezione",
                "cta_url": "/dataset?q=ambiente",
            },
            {
                "id": "themes",
                "enabled": True,
                "title": "Temi del catalogo",
                "subtitle": "Scegli un argomento",
            },
        ]
    )
    with mock.patch.object(hb, "_raw_value", return_value=raw):
        body = _body(app)
    assert "Scelti per te" in body
    assert "Vedi la selezione" in body
    assert 'href="/dataset?q=ambiente"' in body
    assert "Temi del catalogo" in body
    assert "Scegli un argomento" in body
    assert "Esplora per tema" not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_home_hides_cleared_texts(app):
    factories.Dataset(title="Dataset di prova")
    hb = _hb()
    raw = json.dumps([{"id": "themes", "enabled": True, "title": "", "subtitle": ""}])
    with mock.patch.object(hb, "_raw_value", return_value=raw):
        body = _body(app)
    assert "Esplora per tema" not in body
    assert "Sfoglia i dati per argomento" not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_home_escapes_custom_cta(app):
    factories.Dataset(title="Dataset di prova")
    hb = _hb()
    payload = "<script>alert(1)</script>"
    raw = json.dumps(
        [{"id": "featured", "enabled": True, "cta_label": payload, "cta_url": "/dataset"}]
    )
    with mock.patch.object(hb, "_raw_value", return_value=raw):
        body = _body(app)
    assert payload not in body
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in body
