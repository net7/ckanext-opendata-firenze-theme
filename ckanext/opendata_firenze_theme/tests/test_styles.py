"""Regressioni CSS sulle card della home.

CKAN carica Bootstrap, che su ``a:hover`` rimette l'underline. Le card del tema
devono restare senza sottolineatura (il mockup usa un button/pill, non un link
testuale): qui si verifica il cascade reale con un browser, senza un server.
"""

from pathlib import Path

import pytest

sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright

HOME_CSS = Path(__file__).resolve().parents[1] / "assets" / "css" / "home.css"

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
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


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
