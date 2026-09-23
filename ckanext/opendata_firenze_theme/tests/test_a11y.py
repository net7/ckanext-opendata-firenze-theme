"""Struttura di accessibilità delle pagine del tema.

Verifica i punti che l'audit axe ha evidenziato: il link "salta al contenuto"
deve avere un target focusabile (`#content`), una sola h1 per pagina, la lingua
dichiarata. Il target mancava perché le pagine del tema sostituiscono il markup
di `content` della base CKAN.
"""

import pytest

PLUGIN = "opendata_firenze_theme"

PAGES = [
    "/",
    "/dataset",
    "/annuario-statistico",
    "/sviluppatori-e-lod",
]


def _body(response):
    return response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
@pytest.mark.parametrize("path", PAGES)
def test_page_a11y_structure(app, path):
    body = _body(app.get(path))
    # il skip link ha un target (lo mettiamo sul <main>)
    assert 'href="#content"' in body
    assert 'id="content"' in body
    # una sola h1 per pagina
    assert body.count("<h1") == 1
    # lingua dichiarata
    assert "<html" in body
    assert 'lang="' in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_catalog_search_landmarks_unique(app):
    # header e search del catalogo: landmark di ricerca con nomi distinti
    body = _body(app.get("/dataset"))
    assert body.count('role="search"') >= 2
    assert "Cerca nel sito" in body
    assert "Cerca nel catalogo" in body
