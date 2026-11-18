"""Il manifest webassets deve includere tutti e soli gli asset su disco.

I bundle sono il contratto di produzione: un file aggiunto ma non elencato (o
rimosso dal manifest) sparisce dal sito senza che i test dei singoli moduli se
ne accorgano. Ogni asset puo' stare in un bundle dedicato (es. il CRS del
viewer GeoJSON), ma deve comparire una sola volta nel manifest.
"""

from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "assets"
WEBASSETS = ASSETS / "webassets.yml"


def _manifest_contents():
    """Tutte le voci `contents:` dei bundle, nell'ordine del manifest."""
    paths = []
    in_contents = False
    for line in WEBASSETS.read_text().splitlines():
        if not line.startswith((" ", "\t")):
            in_contents = False
            continue
        stripped = line.strip()
        if stripped == "contents:":
            in_contents = True
        elif in_contents and stripped.startswith("- "):
            paths.append(stripped[2:].strip())
        elif in_contents and stripped:
            in_contents = False
    return paths


def test_js_manifest_lists_every_module():
    listed = sorted(Path(path).name for path in _manifest_contents() if path.endswith(".js"))
    on_disk = sorted(path.name for path in (ASSETS / "js").glob("*.js"))
    assert listed == on_disk


def test_css_manifest_lists_every_stylesheet():
    listed = sorted(path for path in _manifest_contents() if path.endswith(".css"))
    on_disk = sorted(str(path.relative_to(ASSETS)) for path in (ASSETS / "css").rglob("*.css"))
    assert listed == on_disk
