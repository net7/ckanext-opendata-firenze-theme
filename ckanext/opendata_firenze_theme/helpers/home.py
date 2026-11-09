"""Helper della home: KPI, temi, dataset in evidenza/consultati, news."""

import logging

import ckan.plugins.toolkit as toolkit

from . import _common, query
from .constants import ANNUARIO_CHAPTERS, THEMES

log = logging.getLogger(__name__)


def odf_theme_counts():
    """{codice_tema: numero_dataset} dai facet tema.

    dcatapit indicizza i temi come `dcat_theme` (dal extra `theme`); `theme` e'
    il nome usato in alcune configurazioni. Si prende il primo facet popolato,
    per non contare due volte lo stesso dataset.
    """
    data = _common._search(
        rows=0, **{"facet.field": [query.THEME, query.THEME_ALT], "facet.limit": 100}
    )
    for field in (query.THEME, query.THEME_ALT):
        items = _common._facet_items(data, field)
        if items:
            return {item["name"]: item["count"] for item in items}
    return {}


def odf_themes():
    """I 13 temi DCAT-AP_IT con il conteggio dataset, ordinati per numero."""
    counts = odf_theme_counts()
    themes = [
        {"code": code, "label": label, "count": counts.get(code, 0)} for code, label in THEMES
    ]
    themes.sort(key=lambda t: (-t["count"], t["label"]))
    return themes


def odf_themes_visible():
    """Temi da mostrare in home: solo quelli con dataset (come il mockup).

    Se però non c'è alcun conteggio (facet non indicizzata / catalogo vuoto) si
    ripiega su tutti e 13, così la sezione "Esplora per tema" non resta vuota.
    """
    themes = odf_themes()
    with_data = [t for t in themes if t["count"]]
    return with_data or themes


def odf_dataset_count():
    """Numero di dataset pubblici nel catalogo."""
    return _common._search(rows=0)["count"]


def odf_home_kpis(total=None):
    """Le 4 card KPI della home (set del mockup).

    1) dataset nel catalogo, 2) dataset alfanumerici (non geografici),
    3) dataset geografici, 4) capitoli dell'Annuario Statistico + tavole collegate.

    `total` permette di riusare il conteggio già letto dal collettore della home
    (hero + KPI): senza, si fa una `package_search` in più.
    """
    if total is None:
        total = _common._search(rows=0)["count"]
    # "geografici" = campo Solr `odf_features` (faccetta "Caratteristiche"),
    # scritto da `before_dataset_index` con la stessa regola del badge
    # "Geodati": formati geo oppure extras spatial/geometria. Così conteggio,
    # badge, faccetta e lista usano un'unica definizione.
    geo = _common._search(rows=0, fq=query.features(query.GEO))["count"]
    tavole = _common._search(rows=0, fq=query.chapter_any())["count"]
    serie = _common._search(rows=0, fq=query.series_any())["count"]
    return [
        {
            "value": _common._it(total),
            "label": toolkit._("dataset nel catalogo"),
            "delta": toolkit._("pubblicati dal Comune di Firenze"),
        },
        {
            "value": _common._it(max(total - geo, 0)),
            "label": toolkit._("dataset alfanumerici"),
            "delta": toolkit._("organizzati in {num} serie").format(num=_common._it(serie)),
        },
        {
            "value": _common._it(geo),
            "label": toolkit._("dataset geografici"),
            "delta": toolkit._("con anteprima su mappa"),
        },
        {
            "value": _common._it(len(ANNUARIO_CHAPTERS)),
            "label": toolkit._("capitoli dell'Annuario Statistico"),
            "delta": toolkit.ungettext(
                "{num} tavola statistica", "{num} tavole statistiche", tavole
            ).format(num=_common._it(tavole)),
        },
    ]


def odf_featured_datasets(limit=3):
    """Dataset in evidenza: prima gli HVD (`extras_hvd`), poi i più recenti.

    Gli HVD hanno la precedenza; se sono meno di `limit` si completa con i
    dataset aggiornati di recente, così il carosello ha sempre abbastanza voci.
    """
    featured = _common._search(rows=limit, fq=query.hvd(), sort="metadata_modified desc")["results"]
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


def odf_latest_datasets(limit=6):
    """Dataset pubblicati più di recente (blocco "Ultimi pubblicati" della home)."""
    return _common._search(rows=limit, sort="metadata_created desc")["results"]


def odf_lod_datasets(limit=6):
    """Dataset Linked Open Data (campo Solr `odf_features`, blocco della home)."""
    return _common._search(rows=limit, fq=query.features(query.LOD), sort="metadata_modified desc")[
        "results"
    ]


def odf_geo_datasets(limit=12):
    """Dataset con contenuto geografico (campo Solr `odf_features`).

    Usa la stessa definizione di "dati geografici" delle KPI della home, della
    faccetta "Caratteristiche" e del badge "Geodati": così conteggi e liste
    restano coerenti.
    """
    return _common._search(rows=limit, fq=query.features(query.GEO), sort="metadata_modified desc")[
        "results"
    ]


def odf_geo_search_query():
    """Query Solr che filtra il catalogo sui geodati.

    Per il link "Filtra il catalogo per geodati": CKAN non sa fare l'OR tra più
    valori di una faccetta via URL (i parametri ripetuti finiscono in AND nel
    `fq`), quindi si passa la query al campo `q` della ricerca. Il campo
    `odf_features` è già il risultato della regola unica di geodato.
    """
    return query.features(query.GEO)


def odf_news(limit=3):
    """Ultime news dal blog di ckanext-pages (vuoto se non disponibile)."""
    try:
        from ckanext.pages.plugin import get_recent_blog_posts

        return get_recent_blog_posts(number=limit) or []
    except Exception:
        log.warning("ckanext-pages non disponibile per le news", exc_info=True)
        return []


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_themes": odf_themes,
    "odf_themes_visible": odf_themes_visible,
    "odf_dataset_count": odf_dataset_count,
    "odf_home_kpis": odf_home_kpis,
    "odf_featured_datasets": odf_featured_datasets,
    "odf_most_viewed": odf_most_viewed,
    "odf_latest_datasets": odf_latest_datasets,
    "odf_lod_datasets": odf_lod_datasets,
    "odf_geo_datasets": odf_geo_datasets,
    "odf_geo_search_query": odf_geo_search_query,
    "odf_news": odf_news,
}
