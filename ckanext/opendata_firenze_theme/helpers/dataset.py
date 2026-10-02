"""Helper della scheda dataset: badge, formati, metadati, QA, risorse."""

import re

import ckan.lib.helpers as ckan_h
import ckan.plugins.toolkit as toolkit

from . import _common
from .catalog import odf_package_theme
from .constants import GEO_FORMATS_UPPER, GEOMETRY_SHAPES
from .format import odf_filesize


def odf_pkg_extra(pkg, key, default=None):
    """Valore di un extra del dataset (None se assente).

    ckanext-dcat, nelle viste (`for_view`), rinomina le chiavi degli extra con
    l'etichetta leggibile (es. `theme` -> `Theme`): il confronto è quindi
    case-insensitive, così il tema regge quella normalizzazione.
    """
    extras = _common._pkg_extras(pkg)
    if key in extras:
        return extras.get(key, default)
    target = str(key).lower()
    for name, value in extras.items():
        if str(name).lower() == target:
            return value
    return default


def odf_dataset_formats(pkg):
    """Formati distinti delle risorse, nell'ordine di pubblicazione.

    Legge sia `resources` (risultato di `package_show`) sia `res_format`
    (risultato di `package_search`, dove Solr appiattisce i formati in una
    lista): il pannello "Altri dataset della serie" lavora su risultati di
    ricerca, che non hanno `resources`, mentre la scheda dataset ha `resources`.
    """
    raw = pkg.get("res_format")
    res_format = raw if isinstance(raw, list) else ([raw] if raw else [])
    formats_raw = [res.get("format") for res in (pkg.get("resources") or [])] + list(res_format)
    seen, formats = set(), []
    for f in formats_raw:
        fmt = (f or "").strip().upper()
        if fmt and fmt not in seen:
            seen.add(fmt)
            formats.append(fmt)
    return formats


def odf_format_is_geo(fmt):
    """True se il formato ha un'anteprima su mappa (chip "geo")."""
    return (fmt or "").strip().upper() in GEO_FORMATS_UPPER


def odf_dataset_geometry(pkg):
    """Tipo di geometria normalizzato ('punto'|'area'|'linea') o None.

    Unico punto di verità per l'extra `geometria`: badge e tabella metadati
    devono mostrare lo stesso valore anche se l'extra non è in minuscolo.
    """
    value = (_common._pkg_extras(pkg).get("geometria") or "").strip().lower()
    return value if value in GEOMETRY_SHAPES else None


def odf_dataset_is_geo(pkg):
    """True se il dataset ha contenuto geografico.

    Unico punto di verità per il badge "Geodati": extra `geometria`/`spatial`
    oppure almeno una risorsa in un formato con anteprima su mappa.
    """
    extras = _common._pkg_extras(pkg)
    return bool(
        odf_dataset_geometry(pkg) is not None
        or extras.get("spatial")
        or extras.get("spatial_geometry")
        or any(odf_format_is_geo(f) for f in odf_dataset_formats(pkg))
    )


def odf_dataset_badges(pkg):
    """Badge della testata del dataset: HVD, geodati, aggiornamento continuo.

    HVD/geometria/realtime sono extras custom (ckanext-scheming non installato);
    la geometria si deduce anche dai formati geografici delle risorse.
    """
    extras = _common._pkg_extras(pkg)
    badges = []
    if _common._truthy(extras.get("hvd")) or _common._truthy(pkg.get("hvd")):
        badges.append({"kind": "hvd", "label": toolkit._("High Value Dataset")})
    geometria = odf_dataset_geometry(pkg)
    if odf_dataset_is_geo(pkg):
        shape = {"punto": "puntuale", "area": "areale", "linea": "lineare"}.get(geometria)
        label = toolkit._("Geodati · {shape}").format(shape=shape) if shape else toolkit._("Geodati")
        badges.append({"kind": "geo", "label": label})
    if _common._truthy(extras.get("realtime")):
        badges.append({"kind": "realtime", "label": toolkit._("In aggiornamento continuo")})
    return badges


def odf_dataset_openness(pkg):
    """Openness di ckanext-qa (0-5) con etichetta/tono, o None.

    `qa` è il dict che ckanext-qa aggiunge al package in after_show; assente
    finché il task di QA non è stato eseguito.
    """
    qa = pkg.get("qa") or {}
    raw = qa.get("openness_score")
    if raw is None:
        raw = _common._pkg_extras(pkg).get("openness_score")
    try:
        score = int(raw)
    except (TypeError, ValueError):
        return None
    if score >= 4:
        label, tier = toolkit._("Alta"), "high"
    elif score == 3:
        label, tier = toolkit._("Buona"), "medium"
    else:
        label, tier = toolkit._("Bassa"), "low"
    return {"score": score, "label": label, "tier": tier}


def odf_dataset_related(pkg, limit=3):
    """Dataset correlati: stesso tema DCAT-AP_IT, escluso sé stesso."""
    tema = odf_package_theme(pkg)
    if not tema:
        return []
    data = _common._search(rows=limit + 1, fq=f"dcat_theme:{tema}", sort="metadata_modified desc")
    return [r for r in data["results"] if r.get("id") != pkg.get("id")][:limit]


_SERIES_SORT = "title_string asc"
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def _series_item(result):
    """Voce del pannello serie: nome, titolo e formati (da Solr, senza `resources`)."""
    return {
        "name": result.get("name"),
        "title": result.get("title") or result.get("name"),
        "formats": odf_dataset_formats(result),
    }


def _series_siblings(pkg, fq, limit):
    """Altri dataset che soddisfano `fq`, escluso sé stesso (via package_search)."""
    data = _common._search(rows=limit + 1, fq=fq, sort=_SERIES_SORT)
    items = []
    for result in data["results"]:
        if result.get("id") == pkg.get("id"):
            continue
        items.append(_series_item(result))
        if len(items) >= limit:
            break
    return items


def odf_dataset_series(pkg, limit=20):
    """Altri dataset della stessa serie (extra `serie`), escluso sé stesso.

    Alimenta il ramo "Altri dataset della serie" della SeriePanel: una voce per
    dataset che condivide la stessa serie, con `name`, `title` e i `formats`
    (da Solr, dove non c'è `resources`). Lista vuota se il dataset non ha serie
    o è l'unico della serie.

    Soluzione **temporanea**: sarà sostituita dal modello serie di DCAT 3
    (`dcat:inSeries`), come tracciato in DP07; il ramo temporale usa già lo
    standard `is_version_of` (vedi `odf_dataset_revisions`).
    """
    serie = odf_pkg_extra(pkg, "serie")
    if not serie:
        return []
    return _series_siblings(pkg, f'extras_serie:"{serie}"', limit)


def _is_version_of_roots(pkg):
    """Valori di `is_version_of` (dct:isVersionOf): lista o stringa CSV."""
    raw = odf_pkg_extra(pkg, "is_version_of")
    if not raw:
        return []
    values = raw if isinstance(raw, (list, tuple)) else str(raw).split(",")
    return [str(value).strip() for value in values if str(value).strip()]


def _revision_year(*texts):
    """Anno a 4 cifre contenuto nel titolo/nome, o None (per l'etichetta "Anno…")."""
    for text in texts:
        if not text:
            continue
        match = _YEAR_RE.search(str(text))
        if match:
            return match.group(0)
    return None


def odf_dataset_revisions(pkg, limit=20):
    """Revisioni temporali: dataset che condividono lo stesso `is_version_of`.

    `is_version_of` (`dct:isVersionOf`) è il meccanismo **standard** di DCAT-AP
    2.0 per le annualità: le revisioni dello stesso indicatore puntano tutte
    alla stessa risorsa radice. Alimenta il ramo "Revisioni temporali" della
    SeriePanel, con l'`year` estratto dal titolo per l'etichetta "Anno <anno>".
    Lista vuota se il dataset non è una revisione o è l'unica.
    """
    roots = _is_version_of_roots(pkg)
    if not roots:
        return []
    fq = " OR ".join(f'extras_is_version_of:"{root}"' for root in roots)
    items = _series_siblings(pkg, fq, limit)
    for item in items:
        item["year"] = _revision_year(item["title"], item["name"])
    return items


def odf_dataset_contact(pkg):
    """Titolare/struttura/contatto del dataset (dcatapit o campi nativi)."""
    extras = _common._pkg_extras(pkg)
    organization = pkg.get("organization") or {}
    return {
        "holder": pkg.get("holder_name") or extras.get("rights_holder") or pkg.get("author") or "",
        "structure": organization.get("title") or pkg.get("holder_identifier") or "",
        "email": pkg.get("author_email") or pkg.get("maintainer_email") or extras.get("email") or "",
    }


def odf_dataset_downloads(pkg):
    """Una voce per formato (primo file di quel formato): menu "Scarica"."""
    seen, downloads = set(), []
    for res in pkg.get("resources") or []:
        fmt = (res.get("format") or "").strip().upper()
        if not fmt or fmt in seen:
            continue
        seen.add(fmt)
        downloads.append(
            {
                "format": fmt,
                "name": res.get("name") or res.get("id"),
                "href": _common._resource_download_url(pkg, res),
                "geo": odf_format_is_geo(fmt),
            }
        )
    return downloads


def odf_dataset_size(pkg):
    """Dimensione totale delle risorse (formattata); '' se non disponibile."""
    total = 0
    for res in pkg.get("resources") or []:
        try:
            total += int(float(res.get("size") or 0))
        except (TypeError, ValueError):
            continue
    return odf_filesize(total)


def odf_sql_console_enabled():
    """True se ckanext-datastore espone datastore_search_sql (sola lettura)."""
    helper = getattr(ckan_h, "datastore_search_sql_enabled", None)
    try:
        return bool(helper()) if helper else False
    except Exception:
        return False


def odf_datastore_resource_id(pkg):
    """Id della prima risorsa con datastore attivo (per la console SQL)."""
    for res in pkg.get("resources") or []:
        if res.get("datastore_active"):
            return res.get("id")
    return ""
