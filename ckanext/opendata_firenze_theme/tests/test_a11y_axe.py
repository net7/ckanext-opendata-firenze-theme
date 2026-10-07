"""Audit di accessibilità con axe-core sulle pagine chiave (CI).

Gira solo se `A11Y_BASE_URL` è impostata (job `a11y` del workflow, con un CKAN
in esecuzione): così non parte nella suite unitaria, che non ha un server né
Playwright. `axe-core` è quello bundled in `axe-playwright-python` (versione
pinnata nei requirements), nessuna fetch a runtime.

`prefers-reduced-motion: reduce` è attivo di proposito: disattiva l'animazione
reveal-on-scroll del tema, che altrimenti lascia il testo a opacità intermedia e
genera falsi positivi di contrasto.
"""

import json
import os

import pytest

sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright
Axe = pytest.importorskip("axe_playwright_python.sync_playwright").Axe

BASE_URL = os.environ.get("A11Y_BASE_URL", "").rstrip("/")

# Pagine chiave rendibili con il solo plugin del tema (il job CI usa test.ini
# con `ckan.plugins = opendata_firenze_theme`). Le schede dataset/risorsa e
# /contact richiedono lo stack completo (dati + altre estensioni): restano
# coperte dall'audit locale/manuale.
PAGES = ["/", "/dataset", "/annuario-statistico", "/sviluppatori-e-lod"]

# Solo i criteri WCAG (niente best-practice di axe).
AXE_OPTIONS = {
    "runOnly": {
        "type": "tag",
        "values": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"],
    }
}

pytestmark = pytest.mark.skipif(not BASE_URL, reason="A11Y_BASE_URL non impostata")


@pytest.mark.parametrize("path", PAGES)
def test_axe_no_wcag_violations(path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(reduced_motion="reduce")
        response = page.goto(BASE_URL + path, wait_until="load")
        # Playwright NON solleva su 404/500: senza questo controllo una route
        # rotta verrebbe scansionata come pagina d'errore e passerebbe.
        status = response.status if response else None
        if not (response and response.ok):
            browser.close()
            pytest.fail(f"{path} ha risposto {status} (atteso 200)")
        page.wait_for_timeout(500)
        results = Axe().run(page, options=AXE_OPTIONS)
        browser.close()

    violations = results.response.get("violations", [])
    report = [
        {
            "id": v["id"],
            "impact": v["impact"],
            "help": v["help"],
            "nodes": [node["target"] for node in v["nodes"]],
        }
        for v in violations
    ]
    assert not violations, f"Violazioni axe su {path}:\n" + json.dumps(report, ensure_ascii=False, indent=2)
