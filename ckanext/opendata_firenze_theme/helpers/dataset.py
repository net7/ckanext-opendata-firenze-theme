"""Helper della scheda dataset: badge, formati, metadati, QA, risorse."""

import ckan.lib.helpers as ckan_h
import ckan.plugins.toolkit as toolkit

from . import _common
from .catalog import odf_package_theme
from .constants import GEO_FORMATS_UPPER, GEOMETRY_SHAPES
from .format import odf_filesize


def odf_pkg_extra(pkg, key, default=None):
    """Valore di un extra del dataset (None se assente)."""
    return _common._pkg_extras(pkg).get(key, default)


def odf_dataset_formats(pkg):
    """Formati distinti delle risorse, nell'ordine di pubblicazione."""
    seen, formats = set(), []
    for res in pkg.get("resources") or []:
        fmt = (res.get("format") or "").strip().upper()
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
    data = _common._search(rows=limit + 1, fq=f"theme:{tema}", sort="metadata_modified desc")
    return [r for r in data["results"] if r.get("id") != pkg.get("id")][:limit]


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
