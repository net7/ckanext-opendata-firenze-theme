"""Il manifest webassets deve includere tutti e soli gli asset su disco.

Il bundle è il contratto di produzione: un file aggiunto ma non elencato (o
rimosso dal manifest) sparisce dal sito senza che i test dei singoli moduli se
ne accorgano.
"""

from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "assets"
WEBASSETS = ASSETS / "webassets.yml"


def _bundle_contents(bundle):
    """Voci di `contents:` per il bundle indicato, nell'ordine del manifest."""
    lines = WEBASSETS.read_text().splitlines()
    start = lines.index(f"{bundle}:")
    paths = []
    in_contents = False
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped == "contents:":
            in_contents = True
            continue
        if not in_contents:
            continue
        if stripped.startswith("- "):
            paths.append(stripped[2:].strip())
        elif stripped and not line.startswith("    "):
            break
    return paths


def test_js_bundle_lists_every_module():
    listed = [Path(path).name for path in _bundle_contents("opendata_firenze_theme-js")]
    on_disk = sorted(path.name for path in (ASSETS / "js").glob("*.js"))
    assert sorted(listed) == on_disk


def test_css_bundle_lists_every_stylesheet():
    listed = _bundle_contents("opendata_firenze_theme-css")
    on_disk = sorted(str(path.relative_to(ASSETS)) for path in (ASSETS / "css").rglob("*.css"))
    assert sorted(listed) == on_disk
