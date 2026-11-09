"""Comportamenti JS del tema su un DOM sintetico, senza CKAN.

I file in `assets/js/` vengono iniettati in una pagina costruita nel test: si
verifica il contratto con i template (attributi `data-rtt-*`, classi di stato)
senza dipendere da un server CKAN.

Richiede Playwright: in CI gira nel job `a11y` (che lo installa già); nella
suite unitaria il modulo viene saltato (`importorskip`), come il test axe.
"""

from pathlib import Path

import pytest

sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright

JS_DIR = Path(__file__).resolve().parents[1] / "assets" / "js"

HEADER = """
<header data-rtt-header id="hdr">
  <button type="button" data-rtt-menu-toggle
          data-label-open="Apri il menu" data-label-close="Chiudi il menu"
          aria-expanded="false" aria-label="Apri il menu">menu</button>
  <nav data-rtt-mobile-nav id="nav">voci</nav>
</header>
"""


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def open_page(browser):
    """Apre una pagina con il DOM dato e gli script del tema già eseguiti."""
    pages = []

    def _open(body, scripts=("header.js", "reveal.js", "dropdowns.js", "pager.js"), **kwargs):
        page = browser.new_page(**kwargs)
        pages.append(page)
        page.set_content(
            "<!doctype html><html><head><meta charset='utf-8'></head><body>"
            + body
            + "</body></html>"
        )
        for name in scripts:
            page.add_script_tag(content=(JS_DIR / name).read_text())
        return page

    yield _open
    for page in pages:
        page.close()


def test_scripts_load_without_errors(open_page):
    """Gli script del tema si eseguono su una pagina normale senza errori."""
    errors = []
    page = open_page(HEADER, viewport={"width": 1000, "height": 700})
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.reload()
    assert errors == []


def test_header_hides_on_scroll_and_returns(open_page):
    page = open_page(
        HEADER + '<div style="height: 3000px"></div>',
        scripts=("header.js",),
        viewport={"width": 900, "height": 400},
    )
    page.evaluate("window.scrollTo(0, 600)")
    page.wait_for_function("document.getElementById('hdr').classList.contains('is-hidden')")

    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_function("!document.getElementById('hdr').classList.contains('is-hidden')")


def test_mobile_menu_toggles_and_escape_closes(open_page):
    page = open_page(HEADER, scripts=("header.js",), viewport={"width": 390, "height": 700})
    toggle = page.locator("[data-rtt-menu-toggle]")

    toggle.click()
    assert page.evaluate("document.getElementById('nav').classList.contains('is-open')")
    assert toggle.get_attribute("aria-expanded") == "true"
    assert toggle.get_attribute("aria-label") == "Chiudi il menu"
    assert page.evaluate("document.documentElement.classList.contains('rtt-nav-open')")

    toggle.click()
    assert not page.evaluate("document.getElementById('nav').classList.contains('is-open')")
    assert toggle.get_attribute("aria-expanded") == "false"

    toggle.click()
    page.keyboard.press("Escape")
    assert not page.evaluate("document.getElementById('nav').classList.contains('is-open')")
    assert toggle.get_attribute("aria-expanded") == "false"
    assert page.evaluate(
        "document.activeElement === document.querySelector('[data-rtt-menu-toggle]')"
    )


def test_reveal_marks_visible_elements(open_page):
    page = open_page(
        '<div class="rtt-reveal" id="reveal">contenuto</div>',
        scripts=("reveal.js",),
    )
    assert page.evaluate("document.documentElement.classList.contains('js-reveal')")
    page.wait_for_function("document.getElementById('reveal').classList.contains('is-revealed')")


def test_reveal_with_reduced_motion(open_page):
    page = open_page(
        '<div class="rtt-stagger" id="reveal">contenuto</div>',
        scripts=("reveal.js",),
        reduced_motion="reduce",
    )
    page.wait_for_function("document.getElementById('reveal').classList.contains('is-revealed')")


def test_dropdown_closes_on_outside_click_and_escape(open_page):
    page = open_page(
        """
        <details class="rtt-facet" id="dropdown" open>
          <summary>Faccetta</summary>
          <div id="inside" style="padding: 8px">opzioni</div>
        </details>
        <div id="outside" style="width: 200px; height: 80px">fuori</div>
        """,
        scripts=("dropdowns.js",),
    )
    page.click("#outside")
    assert not page.evaluate("document.getElementById('dropdown').open")

    page.evaluate("document.getElementById('dropdown').open = true")
    page.keyboard.press("Escape")
    assert not page.evaluate("document.getElementById('dropdown').open")

    # un click dentro non chiude
    page.evaluate("document.getElementById('dropdown').open = true")
    page.click("#inside")
    assert page.evaluate("document.getElementById('dropdown').open")


def test_pager_labels_and_current_page(open_page):
    page = open_page(
        """
        <div data-rtt-pager-labels data-label-prev="Pagina precedente"
             data-label-next="Pagina successiva">
          <ul class="pagination">
            <li class="page-item"><a class="page-link" href="#"><i class="fa fa-chevron-left"></i></a></li>
            <li class="page-item active"><a class="page-link" href="#">2</a></li>
            <li class="page-item"><a class="page-link" href="#"><i class="fa fa-chevron-right"></i></a></li>
          </ul>
        </div>
        """,
        scripts=("pager.js",),
    )
    links = page.locator(".pagination .page-link")
    assert links.nth(0).get_attribute("aria-label") == "Pagina precedente"
    assert links.nth(1).get_attribute("aria-current") == "page"
    assert links.nth(2).get_attribute("aria-label") == "Pagina successiva"
