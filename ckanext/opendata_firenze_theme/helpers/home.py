"""Helper della home: KPI, temi, dataset in evidenza/consultati, news."""

import logging
from datetime import date, timedelta

import ckan.plugins.toolkit as toolkit
from sqlalchemy import func

from . import _common, content, query
from .constants import (
    ANNUARIO_CHAPTERS,
    DEFAULT_MOST_VIEWED_PERIOD,
    MOST_VIEWED_PERIODS,
    THEMES,
)

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
    """Dataset in evidenza: prima gli HVD (`odf_features`), poi i più recenti.

    Gli HVD hanno la precedenza; se sono meno di `limit` si completa con i
    dataset aggiornati di recente, così il carosello ha sempre abbastanza voci.
    """
    featured = _common._search(
        rows=limit, fq=query.features(query.HVD), sort="metadata_modified desc"
    )["results"]
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


def odf_most_viewed_label(period):
    """Etichetta traducibile del periodo del blocco."""
    if period not in MOST_VIEWED_PERIODS:
        period = DEFAULT_MOST_VIEWED_PERIOD
    return toolkit._(MOST_VIEWED_PERIODS[period][1])


def _period_views(period, limit):
    """(package_id, visualizzazioni) del periodo, dal DB di tracking.

    CKAN espone in Solr solo il totale e i 14 giorni: per gli altri periodi
    si sommano i conteggi giornalieri di `tracking_summary` (solo page view,
    non le risorse). None = tracking non disponibile; [] = nessuna vista.
    """
    if period not in MOST_VIEWED_PERIODS:
        period = DEFAULT_MOST_VIEWED_PERIOD
    days = MOST_VIEWED_PERIODS[period][0]
    cutoff = date.today() - timedelta(days=days - 1)
    from ckan import model

    try:
        from ckanext.tracking.model import TrackingSummary

        rows = (
            model.Session.query(
                TrackingSummary.package_id,
                func.sum(TrackingSummary.count).label("views"),
            )
            .filter(TrackingSummary.tracking_date >= cutoff)
            .filter(TrackingSummary.tracking_type == "page")
            .filter(TrackingSummary.package_id.isnot(None))
            .filter(TrackingSummary.package_id != "~~not~found~~")
            .group_by(TrackingSummary.package_id)
            .order_by(func.sum(TrackingSummary.count).desc(), TrackingSummary.package_id)
            .limit(limit)
            .all()
        )
        return [(row[0], int(row[1] or 0)) for row in rows]
    except Exception:
        log.warning("tracking non disponibile per I più consultati", exc_info=True)
        # Un errore DB lascia la sessione in una transazione fallita: senza
        # rollback il fallback sui recenti farebbe fallire il resto della home.
        try:
            model.Session.rollback()
        except Exception:
            log.warning("rollback tracking fallito", exc_info=True)
        return None


def odf_most_viewed(limit=4, period=DEFAULT_MOST_VIEWED_PERIOD):
    """Dataset più consultati nel periodo scelto.

    Il conteggio mostrato è quello del periodo (non il totale storico), così
    ordinamento e card usano la stessa grandezza. `None` = tracking non
    disponibile (il collettore ripiega sui più aggiornati); `[]` = nessuna
    vista nel periodo (il blocco si nasconde).

    Si leggono più candidati del necessario: i primi in classifica possono non
    essere più in Solr (dataset cancellati o privati) e verrebbero scartati da
    `package_search`, lasciando il blocco incompleto.
    """
    if limit <= 0:
        return []
    if period not in MOST_VIEWED_PERIODS:
        period = DEFAULT_MOST_VIEWED_PERIOD
    candidate_limit = max(limit * 5, limit)
    ranked = _period_views(period, candidate_limit)
    if ranked is None:
        return None
    if not ranked:
        return []

    # Si interroga Solr a blocchi di `limit`: nel caso normale basta una sola
    # ricerca da `limit` risultati (e quindi l'hook tracking lavora su pochi
    # dataset); se qualcuno è stato cancellato/privato si passa al blocco
    # successivo invece di mostrare un blocco incompleto.
    results = []
    for start in range(0, len(ranked), limit):
        chunk = ranked[start : start + limit]
        fq = "id:(" + " OR ".join(f'"{pkg_id}"' for pkg_id, _ in chunk) + ")"
        found = _common._search(rows=len(chunk), fq=fq)["results"]
        by_id = {pkg["id"]: pkg for pkg in found}
        for pkg_id, count in chunk:
            pkg = by_id.get(pkg_id)
            if pkg is None:
                continue
            pkg["views_period"] = count
            results.append(pkg)
            if len(results) >= limit:
                return results
    return results


def odf_most_viewed_fallback(limit=4):
    """Dataset aggiornati di recente, se il tracking non è disponibile."""
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
    """Ultime news dal blog (alias di `content.recent_news`)."""
    return content.recent_news(limit)


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_most_viewed": odf_most_viewed,
    "odf_geo_datasets": odf_geo_datasets,
    "odf_geo_search_query": odf_geo_search_query,
}
