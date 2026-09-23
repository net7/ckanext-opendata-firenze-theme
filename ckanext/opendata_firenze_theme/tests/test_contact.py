"""Form di Collaborazione (ckanext-contact).

Estensione di deployment, non dipendenza del tema: se non è installata i test
vengono saltati (in CI il tema viene testato senza ckanext-contact).
"""

import pytest

pytest.importorskip("ckanext.contact")

PLUGIN = "opendata_firenze_theme"


def _body(response):
    return response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body


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
