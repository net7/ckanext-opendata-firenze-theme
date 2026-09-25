"""Helper della home: KPI, temi, dataset in evidenza/consultati, news."""

import logging

import ckan.plugins.toolkit as toolkit

from . import _common
from .constants import ANNUARIO_CHAPTERS, GEO_FORMATS, THEMES

log = logging.getLogger(__name__)


def odf_theme_counts():
    """{codice_tema: numero_dataset} dai facet tema.

    dcatapit indicizza i temi come `dcat_theme` (dal extra `theme`); `theme` e'
    il nome usato in alcune configurazioni. Si prende il primo facet popolato,
    per non contare due volte lo stesso dataset.
    """
    data = _common._search(rows=0, **{"facet.field": ["dcat_theme", "theme"], "facet.limit": 100})
    for field in ("dcat_theme", "theme"):
        items = _common._facet_items(data, field)
        if items:
            return {item["name"]: item["count"] for item in items}
    return {}


def odf_themes():
    """I 13 temi DCAT-AP_IT con il conteggio dataset, ordinati per numero."""
    counts = odf_theme_counts()
    themes = [{"code": code, "label": label, "count": counts.get(code, 0)} for code, label in THEMES]
    themes.sort(key=lambda t: (-t["count"], t["label"]))
    return themes


def odf_dataset_count():
    """Numero di dataset pubblici nel catalogo."""
    return _common._search(rows=0)["count"]


def odf_home_kpis():
    """Le 4 card KPI della home (set del mockup).

    1) dataset nel catalogo, 2) dati alfanumerici (non geografici),
    3) dati geografici, 4) capitoli dell'Annuario Statistico + tavole collegate.
    """
    base = _common._search(rows=0, **{"facet.field": ["organization"], "facet.limit": 100})
    total = base["count"]
    # "geografici" = dataset con almeno una risorsa in un formato geo: piu'
    # affidabile del campo Solr `spatial` (ckanext-spatial non indicizza gli
    # extra `spatial` impostati a mano) e coerente col badge "Geodati".
    geo_formats = " OR ".join(sorted(GEO_FORMATS))
    geo = _common._search(rows=0, fq=f"res_format:({geo_formats})")["count"]
    tavole = _common._search(rows=0, fq="extras_capitolo:[* TO *]")["count"]
    serie = _common._search(rows=0, fq="extras_serie:[* TO *]")["count"]
    return [
        {
            "value": _common._it(total),
            "label": toolkit._("dataset nel catalogo"),
            "delta": toolkit._("tutti in licenza aperta CC BY 4.0"),
        },
        {
            "value": _common._it(max(total - geo, 0)),
            "label": toolkit._("dati alfanumerici"),
            "delta": toolkit._("organizzati in {num} serie").format(num=_common._it(serie)),
        },
        {
            "value": _common._it(geo),
            "label": toolkit._("dati geografici"),
            "delta": toolkit._("con anteprima su mappa"),
        },
        {
            "value": _common._it(len(ANNUARIO_CHAPTERS)),
            "label": toolkit._("capitoli dell'Annuario Statistico"),
            "delta": toolkit.ungettext("{num} tavola statistica", "{num} tavole statistiche", tavole).format(
                num=_common._it(tavole)
            ),
        },
    ]


def odf_featured_datasets(limit=3):
    """Dataset in evidenza: prima gli HVD (`extras_hvd`), poi i più recenti.

    Gli HVD hanno la precedenza; se sono meno di `limit` si completa con i
    dataset aggiornati di recente, così il carosello ha sempre abbastanza voci.
    """
    featured = _common._search(rows=limit, fq="extras_hvd:true", sort="metadata_modified desc")["results"]
    if len(featured) >= limit:
        return featured
    recent = _common._search(rows=limit + len(featured), sort="metadata_modified desc")["results"]
    seen = {pkg["id"] for pkg in featured}
    for pkg in recent:
        if pkg["id"] not in seen:
            featured.append(pkg)
            seen.add(pkg["id"])
        if len(featured) >= limit:
            break
    return featured[:limit]


def odf_most_viewed(limit=4):
    """Dataset più consultati: per viste se il tracking è attivo, altrimenti recenti."""
    tracked = _common._search(rows=limit, sort="views_recent desc")
    if tracked["count"]:
        return tracked["results"]
    return _common._search(rows=limit, sort="metadata_modified desc")["results"]


def odf_geo_datasets(limit=12):
    """Dataset con almeno una risorsa in un formato geografico.

    Usa la stessa definizione di "dati geografici" delle KPI della home (formati
    in `GEO_FORMATS`), così conteggi e liste restano coerenti.
    """
    geo_formats = " OR ".join(sorted(GEO_FORMATS))
    return _common._search(rows=limit, fq=f"res_format:({geo_formats})", sort="metadata_modified desc")["results"]


def odf_geo_search_query():
    """Query Solr che filtra il catalogo sui formati geografici.

    Per il link "Filtra il catalogo per geodati": CKAN non sa fare l'OR tra più
    valori di una faccetta via URL (i parametri ripetuti finiscono in AND nel
    `fq`), quindi si passa la query al campo `q` della ricerca.
    """
    return "res_format:(" + " OR ".join(sorted(GEO_FORMATS)) + ")"


def odf_news(limit=3):
    """Ultime news dal blog di ckanext-pages (vuoto se non disponibile)."""
    try:
        from ckanext.pages.plugin import get_recent_blog_posts

        return get_recent_blog_posts(number=limit) or []
    except Exception:
        log.warning("ckanext-pages non disponibile per le news", exc_info=True)
        return []
