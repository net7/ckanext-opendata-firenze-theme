"""Serie e revisioni temporali: risoluzione, membri e contesto del panel.

Un comportamento solo, con una sola interfaccia pubblica per la scheda:
`odf_series_context`. Restano private la forma della voce, l’identità delle
revisioni (`dct:isVersionOf`), la precedenza dell’anno e l’esclusione del
dataset corrente. I nomi `odf_series_info`, `odf_dataset_series` e
`odf_dataset_revisions` restano come API Python (usata dai test e da eventuali
consumer), ma la scheda passa dal contesto.
"""

import re

import ckan.plugins.toolkit as toolkit

from . import _common, query
from .dataset import odf_dataset_formats, odf_pkg_extra
from .format import odf_filesize
from .resource import odf_resource_download_url

_SERIES_SORT = "title_string asc"
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def _series_item(result):
    """Voce del pannello serie/revisioni.

    Oltre a nome/titolo/formati include l'anno (`year`, per l'etichetta "Anno …")
    e il primo file scaricabile (`download`, `size`): i risultati di
    `package_search` portano già `resources`.
    """
    resources = result.get("resources") or []
    first = resources[0] if resources else {}
    return {
        "name": result.get("name"),
        "title": result.get("title") or result.get("name"),
        "formats": odf_dataset_formats(result),
        "year": _revision_year_from(result),
        "download": odf_resource_download_url(result, first) if first else "",
        "size": odf_filesize(first.get("size")),
    }


def _members_from_search(pkg, data, limit):
    """Voci del pannello dai risultati di una ricerca, escluso il dataset stesso.

    È l'unico punto che applica la regola "salta sé stesso, fermati a `limit`":
    serie e revisioni la condividono.
    """
    items = []
    for result in data.get("results") or []:
        if result.get("id") == pkg.get("id"):
            continue
        items.append(_series_item(result))
        if len(items) >= limit:
            break
    return items


def _series_siblings(pkg, fq, limit):
    """Altri dataset che soddisfano `fq`, escluso sé stesso (via package_search).

    Nel caso delle revisioni `fq` cita `extras_is_version_of`: il filtro del
    catalogo (vedi `helpers.query.hide_revisions`) le lascia passare proprio
    perché la ricerca le nomina esplicitamente.
    """
    data = _common._search(rows=limit + 1, fq=fq, sort=_SERIES_SORT)
    return _members_from_search(pkg, data, limit)


def odf_series_info(pkg, limit=20):
    """Serie del dataset in una sola ricerca: nome, totale e membri.

    `count` è il totale della serie (incluso il dataset corrente), `members`
    sono al massimo `limit` voci pronte per il pannello (escluso sé stesso).
    """
    serie = odf_pkg_extra(pkg, "serie")
    if not serie:
        return {"serie": "", "count": 0, "members": []}
    data = _common._search(rows=limit + 1, fq=query.series_member(serie), sort=_SERIES_SORT)
    return {
        "serie": serie,
        "count": data.get("count", 0),
        "members": _members_from_search(pkg, data, limit),
    }


def odf_dataset_series(pkg, limit=20):
    """Altri dataset della stessa serie (extra `serie`), escluso sé stesso.

    Alimenta il ramo "Altri dataset della serie" della SeriePanel: una voce per
    dataset che condivide la stessa serie, con `name`, `title` e i `formats`
    (da Solr, dove non c'è `resources`). Lista vuota se il dataset non ha serie
    o è l'unico della serie.

    Scelta **provvisoria** in attesa di DP07: si resta su DCAT-AP 2.0 con
    l'extra custom `serie` (ADR 0012 nel repo `opendata-firenze-config`); il
    ramo temporale usa già lo standard `is_version_of`
    (vedi `odf_dataset_revisions`).
    """
    serie = odf_pkg_extra(pkg, "serie")
    if not serie:
        return []
    return _series_siblings(pkg, query.series_member(serie), limit)


def _is_version_of_roots(pkg):
    """Valori di `is_version_of` (dct:isVersionOf): lista o stringa CSV."""
    raw = odf_pkg_extra(pkg, "is_version_of")
    if not raw:
        return []
    values = raw if isinstance(raw, (list, tuple)) else str(raw).split(",")
    return [str(value).strip() for value in values if str(value).strip()]


def _dataset_uris(pkg):
    """URI con cui un altro dataset può riferirsi a questo (per `is_version_of`).

    Copre le convenzioni più probabili: il campo `uri`, la URL della scheda
    (`<site_url>/dataset/<nome>`) e la forma con l'id usata dall'export RDF di
    ckanext-dcat (`<site_url>/dataset/<id>`).
    """
    base = (toolkit.config.get("ckan.site_url") or "").rstrip("/")
    uris = []
    if pkg.get("uri"):
        uris.append(str(pkg["uri"]).strip())
    if base:
        for key in ("name", "id"):
            if pkg.get(key):
                uris.append(f"{base}/dataset/{pkg[key]}")
    return list(dict.fromkeys(uri for uri in uris if uri))


def _dataset_name_from_uri(uri):
    """Nome/id del dataset a partire dal suo URI di scheda (`.../dataset/<x>`)."""
    marker = "/dataset/"
    if marker in uri:
        return uri.rsplit(marker, 1)[-1].strip("/") or None
    return None


def _dataset_by_uri_root(root):
    """Risolve il dataset "corrente" dall'`is_version_of` di una revisione."""
    for value in root if isinstance(root, (list, tuple)) else [root]:
        name = _dataset_name_from_uri(str(value))
        if not name:
            continue
        try:
            return toolkit.get_action("package_show")({"ignore_auth": True}, {"id": name})
        except Exception:
            continue
    return None


def _revision_year(*texts):
    """Anno a 4 cifre contenuto nel titolo/nome, o None (per l'etichetta "Anno…")."""
    for text in texts:
        if not text:
            continue
        match = _YEAR_RE.search(str(text))
        if match:
            return match.group(0)
    return None


def _year_in(value):
    """Anno a 4 cifre contenuto in un valore (es. '01-01-2024' -> '2024')."""
    if not value:
        return None
    match = _YEAR_RE.search(str(value))
    return match.group(0) if match else None


def _revision_year_from(result):
    """Anno della revisione, dalla fonte più affidabile alla meno affidabile.

    1. periodo di riferimento `temporal_start`/`temporal_end` (dcatapit): è il
       posto semanticamente giusto per l'annualità;
    2. `version`, se contiene un anno;
    3. titolo/nome (ultima spiaggia: il titolo può avere un range o un anno non
       di edizione, quindi non è affidabile).
    """
    for key in ("temporal_start", "temporal_end"):
        year = _year_in(odf_pkg_extra(result, key))
        if year:
            return year
    year = _year_in(result.get("version"))
    if year:
        return year
    return _revision_year(result.get("title"), result.get("name"))


def _revision_items(pkg, limit=20):
    """Revisioni temporali (`dct:isVersionOf`) per il pannello della scheda.

    Convenzione: il dataset **corrente** non ha `is_version_of` ed è quello
    visibile in catalogo; le **revisioni** precedenti lo puntano con
    `is_version_of = <URL della sua scheda>`. Così il catalogo mostra una sola
    voce per indicatore (vedi `before_dataset_search` nel plugin) e le revisioni
    restano raggiungibili dal pannello.

    - Sul corrente: elenca le revisioni che lo puntano.
    - Su una revisione: elenca il corrente + le altre revisioni.
    L'`year` (da `temporal_start`, poi `version`, poi il titolo) dà l'etichetta
    "Anno <anno>"; `download`/`size` vengono dal primo file di ogni revisione.
    """
    roots = _is_version_of_roots(pkg)
    items = []
    fqs = []
    if roots:
        canonical = _dataset_by_uri_root(roots)
        if canonical and canonical.get("id") != pkg.get("id"):
            items.append(_series_item(canonical))
        fqs = [query.revision(root) for root in roots]
    else:
        uris = _dataset_uris(pkg)
        if not uris:
            return []
        fqs = [query.revision(uri) for uri in uris]
    # Una query per URI: con `OR` nel fq il parser Solr scavalca i filtri che
    # CKAN antepone (`+capacity:public`, `+state:(active)`) e matcha tutto.
    seen = {pkg.get("id")} | {item.get("name") for item in items}
    for fq in fqs:
        for item in _series_siblings(pkg, fq, limit):
            if item.get("name") in seen:
                continue
            seen.add(item.get("name"))
            items.append(item)
            if len(items) >= limit:
                break
        if len(items) >= limit:
            break
    return items[:limit]


def odf_dataset_revisions(pkg, limit=20):
    """Revisioni temporali (`dct:isVersionOf`) del dataset (vedi `_revision_items`)."""
    return _revision_items(pkg, limit)


def odf_series_context(pkg, info=None, limit=20):
    """Contesto del pannello serie/revisioni della scheda, in una sola risoluzione.

    Ritorna `{kind, label, total, entries, serie, serie_total}`:
    - `kind`: "revisions" (il ramo temporale ha la precedenza, come il mockup),
      "series" oppure None;
    - `label`: nome della serie mostrata dal pannello (`kind="series"`);
    - `total`: totale dei dataset del ramo attivo, incluso quello corrente;
    - `entries`: voci pronte per il pannello, escluso il dataset corrente;
    - `serie`/`serie_total`: la serie dichiarata dall'extra e il suo totale,
      indipendenti dal ramo, per il badge e la tabella metadati della testata.

    `info` permette di riusare un `odf_series_info` già calcolato dalla scheda
    per il badge: così la serie non viene cercata due volte. La chiave si chiama
    `entries` e non `items` perché in Jinja `context.items` sarebbe il metodo
    dei dict, non la chiave.
    """
    info = info if info is not None else odf_series_info(pkg, limit)
    revisions = _revision_items(pkg, limit)
    context = {
        "serie": info["serie"],
        "serie_total": info["count"],
        "label": "",
        "total": 0,
        "entries": [],
        "kind": None,
    }
    if revisions:
        context.update(kind="revisions", total=len(revisions) + 1, entries=revisions)
    elif info["members"]:
        context.update(
            kind="series",
            label=info["serie"],
            total=info["count"],
            entries=info["members"],
        )
    return context


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_series_info": odf_series_info,
    "odf_dataset_series": odf_dataset_series,
    "odf_dataset_revisions": odf_dataset_revisions,
    "odf_series_context": odf_series_context,
}
