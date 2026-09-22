"""Helper del tema usati dai template (registrati in plugin.py).

Forniscono i dati della home (KPI, temi, dataset in evidenza/consultati, news)
senza mettere query nei template. Tutti gli helper sono difensivi: se Solr o
un'estensione non sono disponibili, tornano valori vuoti invece di rompere la
pagina.
"""

import logging

import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)

# 13 temi DCAT-AP_IT: (codice EU, label italiana). Stessa fonte di
# templates/snippets/opendata_firenze_theme/tema-overline.html.
THEMES = (
    ("AGRI", "Agricoltura, pesca, silvicoltura e prodotti alimentari"),
    ("ECON", "Economia e finanze"),
    ("EDUC", "Istruzione, cultura e sport"),
    ("ENER", "Energia"),
    ("ENVI", "Ambiente"),
    ("GOVE", "Governo e settore pubblico"),
    ("HEAL", "Salute"),
    ("INTR", "Tematiche internazionali"),
    ("JUST", "Giustizia, sistema giuridico e sicurezza pubblica"),
    ("REGI", "Regioni e città"),
    ("SOCI", "Popolazione e società"),
    ("TECH", "Scienza e tecnologia"),
    ("TRAN", "Trasporti"),
)

# Formati con anteprima su mappa (per il chip "geo").
GEO_FORMATS = frozenset(("GeoJSON", "SHP", "KML", "WMS", "WFS"))


def _it(n):
    """Intero con separatore delle migliaia italiano (2086 -> '2.086')."""
    return format(int(n), ",d").replace(",", ".")


def _search(**params):
    """package_search difensivo (Solr spento/non configurato -> risultato vuoto)."""
    try:
        return toolkit.get_action("package_search")({"ignore_auth": True}, params)
    except Exception:
        log.warning("package_search non disponibile per la home", exc_info=True)
        return {"count": 0, "results": [], "search_facets": {}}


def _facet_items(data, field):
    return data.get("search_facets", {}).get(field, {}).get("items", [])


def odf_theme_counts():
    """{codice_tema: numero_dataset} dal facet `theme`."""
    data = _search(rows=0, **{"facet.field": ["theme"], "facet.limit": 100})
    counts = {}
    for item in _facet_items(data, "theme"):
        counts[item["name"]] = counts.get(item["name"], 0) + item["count"]
    return counts


def odf_themes():
    """I 13 temi DCAT-AP_IT con il conteggio dataset, ordinati per numero."""
    counts = odf_theme_counts()
    themes = [{"code": code, "label": label, "count": counts.get(code, 0)} for code, label in THEMES]
    themes.sort(key=lambda t: (-t["count"], t["label"]))
    return themes


def odf_dataset_count():
    """Numero di dataset pubblici nel catalogo."""
    return _search(rows=0)["count"]


def odf_home_kpis():
    """Le 4 card KPI della home."""
    base = _search(rows=0, **{"facet.field": ["organization"], "facet.limit": 100})
    total = base["count"]
    geo = _search(rows=0, fq="spatial:[* TO *]")["count"]
    n_orgs = len(_facet_items(base, "organization"))
    n_themes = len([t for t in odf_themes() if t["count"] > 0])
    return [
        {
            "value": _it(total),
            "label": toolkit._("dataset nel catalogo"),
            "delta": toolkit._("pubblicati dal Comune di Firenze"),
        },
        {
            "value": _it(geo),
            "label": toolkit._("dati geografici"),
            "delta": toolkit._("con anteprima su mappa"),
        },
        {
            "value": _it(n_orgs),
            "label": toolkit._("organizzazioni"),
            "delta": toolkit._("enti che pubblicano dati"),
        },
        {
            "value": _it(n_themes),
            "label": toolkit._("temi DCAT-AP_IT"),
            "delta": toolkit._("argomenti del catalogo"),
        },
    ]


def odf_featured_datasets(limit=3):
    """Dataset in evidenza: prima gli HVD, altrimenti i più recenti."""
    hvd = _search(rows=limit, fq="hvd:true", sort="metadata_modified desc")
    if hvd["count"]:
        return hvd["results"]
    return _search(rows=limit, sort="metadata_modified desc")["results"]


def odf_most_viewed(limit=4):
    """Dataset più consultati: per viste se il tracking è attivo, altrimenti recenti."""
    tracked = _search(rows=limit, sort="views_recent desc")
    if tracked["count"]:
        return tracked["results"]
    return _search(rows=limit, sort="metadata_modified desc")["results"]


def odf_news(limit=3):
    """Ultime news dal blog di ckanext-pages (vuoto se non disponibile)."""
    try:
        from ckanext.pages.plugin import get_recent_blog_posts

        return get_recent_blog_posts(number=limit) or []
    except Exception:
        log.warning("ckanext-pages non disponibile per le news", exc_info=True)
        return []


def get_helpers():
    return {
        "odf_dataset_count": odf_dataset_count,
        "odf_home_kpis": odf_home_kpis,
        "odf_themes": odf_themes,
        "odf_featured_datasets": odf_featured_datasets,
        "odf_most_viewed": odf_most_viewed,
        "odf_news": odf_news,
    }
