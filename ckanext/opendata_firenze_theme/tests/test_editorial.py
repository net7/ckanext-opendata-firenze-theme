"""Pagine editoriali (step 8): Annuario, Sviluppatori & LOD, Collaborazione."""

import pytest
from ckan.tests import factories

PLUGIN = "opendata_firenze_theme"


def _body(response):
    return response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_annuario_page(app):
    body = _body(app.get("/annuario-statistico"))
    assert "rtt-annuario__grid" in body
    assert "Annuario Statistico del Comune di Firenze" in body
    # 13 capitoli nella SideNav
    assert body.count("rtt-sidenav__item") == 13
    assert "Capitolo 01 di 13" in body
    # senza l'extra `capitolo` i capitoli sono vuoti
    assert "Nessun dataset di questo capitolo" in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_annuario_lists_chapter_datasets(app):
    factories.Dataset(
        title="Trasporti di prova",
        extras=[{"key": "capitolo", "value": "Trasporti"}],
    )
    body = _body(app.get("/annuario-statistico?capitolo=Trasporti"))
    assert "Trasporti di prova" in body
    assert "Nessun dataset di questo capitolo" not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_sviluppatori_page(app):
    body = _body(app.get("/sviluppatori-e-lod"))
    assert "Endpoint CKAN" in body
    assert "package_search" in body
    # le azioni dei pannelli sono markup, non devono finire escapate
    assert '&lt;span class="rtt-body-sm"' not in body
    rdf = _body(app.get("/sviluppatori-e-lod?tab=rdf"))
    assert "Risorse RDF" in rdf
    assert "package_metadata_rdf_dcat_ap_it" in rdf
    geo = _body(app.get("/sviluppatori-e-lod?tab=geo"))
    assert "GetCapabilities" in geo


@pytest.mark.ckan_config("ckan.plugins", f"{PLUGIN} contact")
@pytest.mark.usefixtures("with_plugins")
def test_contact_form(app):
    body = _body(app.get("/contact"))
    assert "rtt-contact__form" in body
    # i 3 tipi di richiesta
    assert "Segnala un dataset" in body
    assert "Racconta un riuso" in body
    assert "Chiarimenti" in body
    # i campi che ckanext-contact valida
    assert 'name="name"' in body
    assert 'name="email"' in body
    assert 'name="content"' in body


@pytest.mark.ckan_config("ckan.plugins", f"{PLUGIN} contact")
@pytest.mark.usefixtures("with_plugins")
def test_contact_form_rejects_missing_fields(app):
    # POST senza i campi obbligatori: validazione lato server, nessuna email
    resp = app.post("/contact", data={"name": "", "email": "", "content": "", "save": ""})
    assert resp.status_code == 200
    body = _body(resp)
    assert "rtt-contact__form" in body
    assert "rtt-contact__success" not in body


@pytest.mark.ckan_config("ckan.plugins", f"{PLUGIN} contact")
@pytest.mark.usefixtures("with_plugins")
def test_contact_form_requires_privacy_consent(app):
    # consenso non spuntato (hidden vuoto): il server rifiuta l'invio
    resp = app.post(
        "/contact",
        data={
            "subject": "Chiarimenti",
            "name": "Mario Rossi",
            "email": "mario.rossi@example.com",
            "content": "Una richiesta di prova.",
            "privacy": "",
            "save": "",
        },
    )
    assert resp.status_code == 200
    body = _body(resp)
    assert "rtt-contact__success" not in body
    assert "Missing Value" in body

    # consenso spuntato (checkbox + hidden, nell'ordine del DOM): la validazione
    # passa e non viene mostrato l'errore del campo privacy
    resp = app.post(
        "/contact",
        data={
            "subject": "Chiarimenti",
            "name": "Mario Rossi",
            "email": "mario.rossi@example.com",
            "content": "Una richiesta di prova.",
            "privacy": ["on", ""],
            "save": "",
        },
    )
    assert "Missing Value" not in _body(resp)
