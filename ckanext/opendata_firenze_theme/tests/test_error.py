"""Stati di errore del tema (StatusScreen del mockup su 404 e altri codici)."""

import pytest

PLUGIN = "opendata_firenze_theme"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_error_404_status_screen(app):
    response = app.get("/rotta-inesistente")
    assert response.status_code == 404
    body = response.body
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    # come StatusScreen del mockup: icona, titolo, messaggio, azioni
    assert "rtt-status" in body
    assert "Pagina non trovata" in body
    assert "Cerca nel catalogo" in body
    assert "Torna alla home" in body
    # la pagina mantiene header e footer del tema
    assert "rtt-header" in body
    assert "rtt-footer" in body
    # il messaggio di errore grezzo del core non deve comparire
    assert "The requested URL was not found on the server" not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_error_403_generic(app):
    # un 403 su una pagina HTML (creazione dataset da anonimi, vietata in
    # test-core.ini: ckan.auth.anon_create_dataset = false)
    response = app.get("/dataset/new", status=403)
    assert response.status_code == 403
    body = response.body
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    assert "rtt-status" in body
    assert "Si è verificato un problema" in body
    assert "Torna alla home" in body
