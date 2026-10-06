"""Struttura di accessibilità delle pagine del tema.

Verifica i punti che l'audit axe ha evidenziato: il link "salta al contenuto"
deve avere un target focusabile (`#content`), una sola h1 per pagina, la lingua
dichiarata. Il target mancava perché le pagine del tema sostituiscono il markup
di `content` della base CKAN.
"""

import re
from pathlib import Path

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
    # il skip link ha un target (lo mettiamo sul <main>) e l'id è unico
    assert 'href="#content"' in body
    assert body.count('id="content"') == 1
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
    # etichette per i link a icona del pager (applicate dal JS)
    assert "data-rtt-pager-labels" in body
    assert "Pagina successiva" in body


# Invarianti CSS che l'audit axe non copre (focus visibile, target size): un
# ritorno a `outline:none` o a un pallino da 4px non verrebbe intercettato dai
# test di struttura. Check statico sul foglio di stile, senza browser.
CSS_DIR = Path(__file__).resolve().parent.parent / "assets" / "css"


def _rule(css, selector):
    """Dichiarazioni della prima regola con quel selettore ('' se assente)."""
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    return match.group(1) if match else ""


def _px(decls, prop):
    match = re.search(prop + r"\s*:\s*(\d+(?:\.\d+)?)px", decls)
    return float(match.group(1)) if match else None


def test_a11y_css_invariants():
    """Focus visibile sulla ricerca e target ≥ 24px (WCAG 2.4.7 / 2.5.8)."""
    shell = (CSS_DIR / "shell.css").read_text(encoding="utf-8")
    components = (CSS_DIR / "components.css").read_text(encoding="utf-8")
    catalog = (CSS_DIR / "catalog.css").read_text(encoding="utf-8")

    # il campo di ricerca ha `outline:none` sull'input: l'anello di focus deve
    # stare sul contenitore (fallback) o, con :has(), sul focus nel testo.
    focus_ring = _rule(shell, ".rtt-search__field:focus-within") + _rule(
        shell, ".rtt-search__field:has(input:focus-visible)"
    )
    assert "outline" in focus_ring

    dots_height = _px(_rule(components, ".rtt-carousel__dots button"), "height")
    assert dots_height is not None and dots_height >= 24
    assert _px(_rule(catalog, ".rtt-facets__remove"), "width") >= 24
    assert _px(_rule(catalog, ".rtt-facets__remove"), "height") >= 24
