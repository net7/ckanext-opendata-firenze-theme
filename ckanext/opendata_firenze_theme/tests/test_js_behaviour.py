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


DEFAULT_SCRIPTS = ("header.js", "reveal.js", "dropdowns.js", "pager.js")
ALL_SCRIPTS = (
    "header.js",
    "reveal.js",
    "dropdowns.js",
    "pager.js",
    "chips.js",
    "copy.js",
    "placeholders.js",
    "line-clamp.js",
    "sql-console.js",
    "preview.js",
    "home.js",
    "contact.js",
)


def _document(body, scripts, prelude=None):
    """HTML con gli script inline in fondo al body, come nel bundle reale."""
    code = f"<script>{prelude}</script>" if prelude else ""
    code += "".join(f"<script>{(JS_DIR / name).read_text()}</script>" for name in scripts)
    return (
        "<!doctype html><html><head><meta charset='utf-8'></head><body>"
        + body
        + code
        + "</body></html>"
    )


@pytest.fixture
def open_page(browser):
    """Apre una pagina con il DOM dato e gli script del tema già eseguiti."""
    pages = []

    def _open(body, scripts=DEFAULT_SCRIPTS, init_script=None, **kwargs):
        page = browser.new_page(**kwargs)
        pages.append(page)
        page.set_content(_document(body, scripts, init_script))
        return page

    yield _open
    for page in pages:
        page.close()


def test_scripts_load_without_errors(browser):
    """Gli script si eseguono nell'ordine del bundle, senza errori."""
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_document(HEADER, ALL_SCRIPTS))
    assert errors == []
    # prova che gli script sono partiti davvero (reveal aggiunge la classe)
    assert page.evaluate("document.documentElement.classList.contains('js-reveal')")
    page.close()


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


def test_line_clamp_toggles(open_page):
    page = open_page(
        """
        <button data-rtt-line-clamp aria-controls="desc" aria-expanded="false"
                data-label-more="Mostra tutto" data-label-less="Mostra meno">
          <span data-rtt-clamp-label>Mostra tutto</span>
        </button>
        <div id="desc" class="is-clamped">testo</div>
        """,
        scripts=("line-clamp.js",),
    )
    page.click("[data-rtt-line-clamp]")
    assert not page.evaluate("document.getElementById('desc').classList.contains('is-clamped')")
    assert page.get_attribute("[data-rtt-line-clamp]", "aria-expanded") == "true"
    assert page.text_content("[data-rtt-clamp-label]") == "Mostra meno"

    page.click("[data-rtt-line-clamp]")
    assert page.evaluate("document.getElementById('desc').classList.contains('is-clamped')")
    assert page.get_attribute("[data-rtt-line-clamp]", "aria-expanded") == "false"
    assert page.text_content("[data-rtt-clamp-label]") == "Mostra tutto"


SQL_BODY = """
<button type="button" data-rtt-sql-run data-rtt-api="/api/3/action">Esegui</button>
<textarea data-rtt-sql>select 1</textarea>
<div data-rtt-sql-result data-rtt-sql-error="Errore SQL"></div>
"""


def test_sql_console_renders_rows(open_page):
    page = open_page(SQL_BODY, scripts=("sql-console.js",))
    page.evaluate(
        """window.fetch = () => Promise.resolve({ json: () => Promise.resolve({
            success: true,
            result: { fields: [{ id: "a" }, { id: "b" }],
                      records: [{ a: 1, b: 2 }, { a: 3, b: 4 }] }
        }) })"""
    )
    page.click("[data-rtt-sql-run]")
    page.wait_for_selector("[data-rtt-sql-result] table")
    assert page.locator("[data-rtt-sql-result] tbody tr").count() == 2
    assert "3" in page.text_content("[data-rtt-sql-result]")


def test_sql_console_shows_server_error(open_page):
    page = open_page(SQL_BODY, scripts=("sql-console.js",))
    page.evaluate(
        """window.fetch = () => Promise.resolve({ json: () => Promise.resolve({
            success: false, error: { message: "boom" }
        }) })"""
    )
    page.click("[data-rtt-sql-run]")
    page.wait_for_selector("[data-rtt-sql-result] .rtt-api__error")
    assert "boom" in page.text_content("[data-rtt-sql-result]")


PREVIEW_BODY = """
<button type="button" data-rtt-preview
        data-preview-name="Risorsa"
        data-preview-format="CSV"
        data-preview-geo="false"
        data-preview-view="/vista"
        data-preview-full="/dataset/x"
        data-preview-download="/file.csv">Apri</button>
<dialog data-rtt-preview-modal>
  <button type="button" data-rtt-preview-close>Chiudi</button>
  <span data-rtt-preview-chip></span>
  <h3 data-rtt-preview-title></h3>
  <iframe data-rtt-preview-iframe hidden></iframe>
  <div data-rtt-preview-empty hidden></div>
  <a data-rtt-preview-download hidden></a>
  <a data-rtt-preview-full></a>
</dialog>
"""


def test_preview_modal_opens_and_closes(open_page):
    page = open_page(PREVIEW_BODY, scripts=("preview.js",))
    page.click("[data-rtt-preview]")
    assert page.evaluate("document.querySelector('[data-rtt-preview-modal]').open")
    assert page.text_content("[data-rtt-preview-title]") == "Risorsa"
    assert page.get_attribute("[data-rtt-preview-iframe]", "src") == "/vista"
    assert page.evaluate("document.body.style.overflow") == "hidden"

    page.click("[data-rtt-preview-close]")
    assert not page.evaluate("document.querySelector('[data-rtt-preview-modal]').open")
    # l'evento `close` del <dialog> è asincrono: attende il reset
    page.wait_for_function("document.body.style.overflow === ''")
    assert page.get_attribute("[data-rtt-preview-iframe]", "src") is None


def test_carousel_pages_and_dots(open_page):
    items = "".join(
        '<div class="rtt-carousel__item" style="flex: 0 0 200px">item</div>' for _ in range(4)
    )
    page = open_page(
        f"""
        <div data-rtt-carousel data-dot-label="Vai a" style="width: 400px">
          <div class="rtt-carousel__track" style="display: flex; overflow-x: auto; width: 400px">{items}</div>
          <div data-rtt-carousel-dots></div>
          <button type="button" data-rtt-carousel-prev>prec</button>
          <button type="button" data-rtt-carousel-next>succ</button>
        </div>
        """,
        scripts=("home.js",),
    )
    page.wait_for_function(
        "document.querySelectorAll('[data-rtt-carousel-dots] button').length === 2"
    )
    assert page.locator("[data-rtt-carousel-dots] button").count() == 2
    assert page.is_disabled("[data-rtt-carousel-prev]")

    page.click("[data-rtt-carousel-next]")
    page.wait_for_function(
        "document.querySelector('[data-rtt-carousel-dots]').children[1].classList.contains('is-active')"
    )
    assert not page.is_disabled("[data-rtt-carousel-prev]")


def test_chip_remove_moves_focus(open_page):
    page = open_page(
        """
        <div class="rtt-chip"><span class="rtt-chip__label">A</span>
          <button type="button" data-rtt-chip-remove>×</button></div>
        <div class="rtt-chip"><span class="rtt-chip__label">B</span>
          <button type="button" data-rtt-chip-remove>×</button></div>
        """,
        scripts=("chips.js",),
    )
    page.evaluate(
        "window.__chipEvents = 0;"
        "document.addEventListener('rtt-chip-remove', () => window.__chipEvents++)"
    )
    page.locator("[data-rtt-chip-remove]").first.click()
    assert page.locator(".rtt-chip").count() == 1
    assert page.evaluate("window.__chipEvents") == 1
    assert page.evaluate(
        "document.activeElement === document.querySelector('[data-rtt-chip-remove]')"
    )


def test_copy_button_updates_label(open_page):
    page = open_page(
        """
        <div class="rtt-code-wrap">
          <code>curl x</code>
          <button type="button" data-rtt-copy data-label-copied="Copiato">
            <span data-rtt-copy-label>Copia</span>
          </button>
        </div>
        """,
        scripts=("copy.js",),
        init_script=(
            "Object.defineProperty(Navigator.prototype, 'clipboard', { configurable: true,"
            " get: () => ({ writeText: () => Promise.resolve() }) })"
        ),
    )
    page.click("[data-rtt-copy]")
    page.wait_for_function(
        "document.querySelector('[data-rtt-copy-label]').textContent === 'Copiato'"
    )


def test_contact_counter_and_tipo(open_page):
    page = open_page(
        """
        <input type="radio" name="tipo" data-rtt-tipo checked
               data-text-label="Richiesta A" data-placeholder="Scrivi A">
        <input type="radio" name="tipo" data-rtt-tipo
               data-text-label="Richiesta B" data-placeholder="Scrivi B">
        <label data-rtt-tipo-label>Richiesta A</label>
        <textarea data-rtt-counter-field></textarea>
        <div data-rtt-counter hidden><span data-rtt-counter-value>0</span></div>
        """,
        scripts=("contact.js",),
    )
    assert page.is_visible("[data-rtt-counter]")
    page.fill("[data-rtt-counter-field]", "ciao")
    assert page.text_content("[data-rtt-counter-value]") == "4"

    page.check('input[data-text-label="Richiesta B"]')
    assert page.text_content("[data-rtt-tipo-label]") == "Richiesta B"
    assert page.get_attribute("[data-rtt-counter-field]", "placeholder") == "Scrivi B"


def test_placeholder_links_do_not_navigate(open_page):
    page = open_page(
        '<a href="#top" data-rtt-placeholder id="ph">link</a>', scripts=("placeholders.js",)
    )
    page.evaluate(
        "window.__defaultPrevented = false;"
        "document.getElementById('ph').addEventListener('click',"
        " (event) => { window.__defaultPrevented = event.defaultPrevented; })"
    )
    page.click("#ph")
    assert page.evaluate("window.__defaultPrevented")
