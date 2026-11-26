"""Regressioni CSS del tema.

Le card della home devono restare senza sottolineatura (CKAN carica Bootstrap,
che su ``a:hover`` la rimette): il mockup usa un button/pill, non un link
testuale. Qui si verifica anche che i link-pulsante non perdano il colore del
mockup nello stato ``:visited``.
"""

import re
from pathlib import Path

import pytest

CSS = Path(__file__).resolve().parents[1] / "assets" / "css"
HOME_CSS = CSS / "home.css"
SHELL_CSS = CSS / "shell.css"

HTML = """
<!doctype html><html><head><meta charset="utf-8">
<style>a:hover {{ text-decoration: underline; }}</style>
<style>{css}</style>
</head><body>
<a class="rtt-tema" href="#">Tema</a>
<a class="rtt-dcard" href="#">Dataset</a>
<a class="rtt-hero__pill" href="#">Pill</a>
</body></html>
"""


@pytest.fixture(scope="module")
def browser():
    # Playwright è installato solo nel job a11y: il test statico di questo
    # module deve girare anche nella suite normale, senza browser.
    sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


def _rule_body(css, selector):
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    return match.group(1) if match else ""


def test_visited_link_icons_keep_their_color():
    """`:visited` batte le classi: senza override le icone dei link diventano nere.

    I browser mascherano `:visited` in `getComputedStyle`, quindi qui si
    controlla la regola CSS che ripristina i colori del mockup.
    """
    css = SHELL_CSS.read_text(encoding="utf-8")
    buttons = re.search(r"\.rtt-btn--outline:visited,\s*\.rtt-btn--text:visited\s*\{([^}]*)\}", css)
    assert buttons and "color: var(--lilac-700)" in buttons.group(1)
    assert "color: var(--neutral-neutral-800)" in _rule_body(css, ".rtt-dataset__tab:visited")
    assert "color: var(--neutral-neutral-900)" in _rule_body(
        css, ".rtt-dataset__tab.is-active:visited"
    )


@pytest.mark.parametrize("selector", (".rtt-tema", ".rtt-dcard", ".rtt-hero__pill"))
def test_card_links_keep_no_underline_on_hover(browser, selector):
    page = browser.new_page()
    page.set_content(HTML.format(css=HOME_CSS.read_text(encoding="utf-8")))
    link = page.locator(selector)
    link.hover()
    assert (
        page.evaluate("(el) => getComputedStyle(el).textDecorationLine", link.element_handle())
        == "none"
    )
    page.close()
