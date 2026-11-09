"""Helper della scheda dataset: badge, formati, metadati, QA, risorse."""

import ckan.lib.helpers as ckan_h
import ckan.plugins.toolkit as toolkit

from . import _common, query
from .catalog import odf_package_theme
from .constants import GEO_FORMATS_UPPER, GEOMETRY_SHAPES, LOD_FORMATS_UPPER
from .format import odf_filesize
from .resource import odf_resource_download_url


def odf_pkg_extra(pkg, key, default=None):
    """Valore di un campo/extra del dataset (None se assente).

    Adattatore sottile su `_common.pkg_field`, che è l'unico punto che conosce
    le forme del package (`extras`, cima del package, `extras_<chiave>`, chiavi
    rinominate da ckanext-dcat). Il nome resta `odf_*` perché i template lo
    chiamano come `h.odf_pkg_extra`.
    """
    return _common.pkg_field(pkg, key, default)


def odf_dataset_formats(pkg):
    """Formati distinti delle risorse, nell'ordine di pubblicazione.

    Legge sia `resources` (risultato di `package_show`) sia `res_format`
    (risultato di `package_search`, dove Solr appiattisce i formati in una
    lista): il pannello "Altri dataset della serie" lavora su risultati di
    ricerca, che non hanno `resources`, mentre la scheda dataset ha `resources`.

    La deduplica è case-insensitive ma il valore mostrato resta quello scritto
    per la prima volta ("GeoJSON", non "GEOJSON"): i chip del mockup usano la
    forma canonica del formato.
    """
    raw = pkg.get("res_format")
    res_format = raw if isinstance(raw, list) else ([raw] if raw else [])
    formats_raw = [res.get("format") for res in (pkg.get("resources") or [])] + list(res_format)
    seen, formats = set(), []
    for f in formats_raw:
        label = (f or "").strip()
        key = label.upper()
        if key and key not in seen:
            seen.add(key)
            formats.append(label)
    return formats


def odf_format_is_geo(fmt):
    """True se il formato ha un'anteprima su mappa (chip "geo")."""
    return (fmt or "").strip().upper() in GEO_FORMATS_UPPER


def odf_dataset_is_lod(pkg):
    """True se il dataset pubblica almeno una risorsa RDF.

    Come nel mockup (e come il filtro "Caratteristiche" del catalogo), LOD =
    presenza di una serializzazione RDF fra i formati delle risorse.
    """
    return odf_dataset_facts(pkg)["is_lod"]


def odf_dataset_is_series(pkg):
    """True se il dataset dichiara l'extra `serie` (badge e filtro "Serie")."""
    return bool(odf_pkg_extra(pkg, "serie"))


def odf_dataset_map_resource(pkg):
    """Prima risorsa con anteprima su mappa, o None (pulsante "Vedi su mappa")."""
    for res in pkg.get("resources") or []:
        if odf_format_is_geo(res.get("format")):
            return res
    return None


def odf_index_features(pkg):
    """Valori del campo Solr `odf_features` (faccetta "Caratteristiche").

    Usa gli stessi fatti del badge (`odf_dataset_facts`), così faccetta e
    scheda non possono dire cose diverse sullo stesso dataset. Funziona anche
    sul dict appiattito che CKAN passa a `before_dataset_index` (`extras_*`).
    """
    facts = odf_dataset_facts(pkg)
    features = [query.GEO] if facts["is_geo"] else [query.ALPHANUMERIC]
    if facts["is_lod"]:
        features.append(query.LOD)
    if facts["is_hvd"]:
        features.append(query.HVD)
    return features


def odf_index_series(pkg):
    """Valore del campo Solr `odf_series` (faccetta "Serie"), [] se assente."""
    serie = odf_pkg_extra(pkg, "serie")
    return [serie] if serie else []


def odf_dataset_geometry(pkg):
    """Tipo di geometria normalizzato ('punto'|'area'|'linea') o None.

    Unico punto di verità per l'extra `geometria`: badge e tabella metadati
    devono mostrare lo stesso valore anche se l'extra non è in minuscolo.
    """
    value = str(odf_pkg_extra(pkg, "geometria") or "").strip().lower()
    return value if value in GEOMETRY_SHAPES else None


def odf_dataset_facts(pkg):
    """Fatti derivati del dataset, calcolati una volta sola.

    Unico punto di verità per badge, faccette, card e campi indicizzati:
    formati, tema, geometria e le proprietà geo/LOD/HVD/realtime/serie. Prima
    di questo modulo la stessa domanda ("è un geodato?") aveva quattro risposte
    diverse a seconda della superficie che la chiedeva.
    """
    formats = odf_dataset_formats(pkg)
    return {
        "formats": formats,
        "theme": odf_package_theme(pkg),
        "geometry": odf_dataset_geometry(pkg),
        "is_geo": bool(
            _common._present(odf_pkg_extra(pkg, "geometria"))
            or _common._present(odf_pkg_extra(pkg, "spatial"))
            or _common._present(odf_pkg_extra(pkg, "spatial_geometry"))
            or any(odf_format_is_geo(fmt) for fmt in formats)
        ),
        "is_lod": any(fmt.upper() in LOD_FORMATS_UPPER for fmt in formats),
        "is_hvd": _common._truthy(odf_pkg_extra(pkg, "hvd")),
        "is_realtime": _common._truthy(odf_pkg_extra(pkg, "realtime")),
        "series": odf_pkg_extra(pkg, "serie") or "",
    }


def odf_dataset_is_geo(pkg):
    """True se il dataset ha contenuto geografico.

    Regola unica (vedi `odf_dataset_facts`): extra `geometria` valorizzato,
    oppure `spatial`/`spatial_geometry` valorizzati (WKT compresa), oppure una
    risorsa in un formato con anteprima su mappa. `spatial="false"` non conta.
    """
    return odf_dataset_facts(pkg)["is_geo"]


def odf_dataset_is_hvd(pkg):
    """True se il dataset è un High Value Dataset (extra `hvd`)."""
    return odf_dataset_facts(pkg)["is_hvd"]


def odf_dataset_is_realtime(pkg):
    """True se il dataset è in aggiornamento continuo (extra `realtime`)."""
    return odf_dataset_facts(pkg)["is_realtime"]


def odf_dataset_badges(pkg):
    """Badge della testata del dataset: HVD, geodati, aggiornamento continuo.

    Legge i fatti da `odf_dataset_facts`, la stessa fonte della faccetta
    "Caratteristiche": HVD/geometria/realtime sono extras custom
    (ckanext-scheming non installato), la geometria si deduce anche dai formati.
    """
    facts = odf_dataset_facts(pkg)
    badges = []
    if facts["is_hvd"]:
        badges.append({"kind": "hvd", "label": toolkit._("High Value Dataset")})
    if facts["is_lod"]:
        badges.append({"kind": "lod", "label": toolkit._("Linked Open Data")})
    if facts["is_geo"]:
        shape = {"punto": "puntuale", "area": "areale", "linea": "lineare"}.get(facts["geometry"])
        label = (
            toolkit._("Geodati · {shape}").format(shape=shape) if shape else toolkit._("Geodati")
        )
        badges.append({"kind": "geo", "label": label})
    if facts["is_realtime"]:
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
        raw = odf_pkg_extra(pkg, "openness_score")
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
    data = _common._search(rows=limit + 1, fq=query.theme(tema), sort="metadata_modified desc")
    return [r for r in data["results"] if r.get("id") != pkg.get("id")][:limit]


def odf_dataset_contact(pkg):
    """Titolare/struttura/contatto del dataset (dcatapit o campi nativi)."""
    organization = pkg.get("organization") or {}
    return {
        "holder": pkg.get("holder_name")
        or odf_pkg_extra(pkg, "rights_holder")
        or pkg.get("author")
        or "",
        "structure": organization.get("title") or pkg.get("holder_identifier") or "",
        "email": pkg.get("author_email")
        or pkg.get("maintainer_email")
        or odf_pkg_extra(pkg, "email")
        or "",
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
                "href": odf_resource_download_url(pkg, res),
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


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_pkg_extra": odf_pkg_extra,
    "odf_dataset_formats": odf_dataset_formats,
    "odf_format_is_geo": odf_format_is_geo,
    "odf_dataset_is_lod": odf_dataset_is_lod,
    "odf_dataset_is_hvd": odf_dataset_is_hvd,
    "odf_dataset_is_realtime": odf_dataset_is_realtime,
    "odf_dataset_map_resource": odf_dataset_map_resource,
    "odf_dataset_geometry": odf_dataset_geometry,
    "odf_dataset_is_geo": odf_dataset_is_geo,
    "odf_dataset_badges": odf_dataset_badges,
    "odf_dataset_openness": odf_dataset_openness,
    "odf_dataset_related": odf_dataset_related,
    "odf_dataset_contact": odf_dataset_contact,
    "odf_dataset_downloads": odf_dataset_downloads,
    "odf_sql_console_enabled": odf_sql_console_enabled,
    "odf_datastore_resource_id": odf_datastore_resource_id,
}
