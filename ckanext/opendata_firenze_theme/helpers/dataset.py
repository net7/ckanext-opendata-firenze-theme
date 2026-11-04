"""Helper della scheda dataset: badge, formati, metadati, QA, risorse."""

import re
from urllib.parse import unquote, urlsplit

import ckan.lib.helpers as ckan_h
import ckan.plugins.toolkit as toolkit

from . import _common
from .catalog import odf_package_theme
from .constants import GEO_FORMATS_UPPER, GEOMETRY_SHAPES, LOD_FORMATS_UPPER
from .format import odf_filesize


def odf_pkg_extra(pkg, key, default=None):
    """Valore di un campo/extra del dataset (None se assente).

    Il valore può stare in tre posti:
    - in `extras` (lista o dict), per gli extra "liberi" (es. `serie`, `hvd`);
    - **in cima al package**, per i campi dello schema dcatapit che
      `package_show` sposta lì con `convert_from_extras` (es. `is_version_of`);
    - con la chiave rinominata con l'etichetta leggibile: ckanext-dcat, nelle
      viste (`for_view`), rinomina gli extra (es. `theme` -> `Theme`), quindi il
      confronto sugli extras è case-insensitive.
    """
    extras = _common._pkg_extras(pkg)
    if key in extras:
        return extras.get(key, default)
    value = pkg.get(key)
    if value is not None and value != "":
        return value
    target = str(key).lower()
    for name, extra_value in extras.items():
        if str(name).lower() == target:
            return extra_value
    # dict di `package_search`: gli extra sono appiattiti in `extras_<chiave>`
    flat = pkg.get(f"extras_{key}")
    if flat is not None and flat != "":
        return flat
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


def odf_dataset_is_lod(pkg):
    """True se il dataset pubblica almeno una risorsa RDF.

    Come nel mockup (e come il filtro "Caratteristiche" del catalogo), LOD =
    presenza di una serializzazione RDF fra i formati delle risorse.
    """
    return any(fmt in LOD_FORMATS_UPPER for fmt in odf_dataset_formats(pkg))


def odf_dataset_is_series(pkg):
    """True se il dataset dichiara l'extra `serie` (badge e filtro "Serie")."""
    return bool(odf_pkg_extra(pkg, "serie"))


def odf_dataset_map_resource(pkg):
    """Prima risorsa con anteprima su mappa, o None (pulsante "Vedi su mappa")."""
    for res in pkg.get("resources") or []:
        if odf_format_is_geo(res.get("format")):
            return res
    return None


def odf_views_map_first(views):
    """Viste della risorsa con la mappa per prima (poi l'ordine originale)."""
    if not views:
        return []
    map_types = {"geoview", "geo_view", "geojson_view", "wmts_view", "shp_view", "recline_map_view"}

    def _is_map(view):
        return (view.get("view_type") or "").lower() in map_types

    return sorted(views, key=lambda view: 0 if _is_map(view) else 1)


def odf_index_features(pkg):
    """Valori del campo Solr `odf_features` (faccetta "Caratteristiche").

    La funzione lavora anche sul dict che CKAN passa a `before_dataset_index`,
    dove gli extra sono appiattiti (`extras_hvd`, `extras_spatial`, …) e non
    c'è la lista `extras`: per questo legge entrambe le forme.
    """
    extras = _common._pkg_extras(pkg)

    def extra(key):
        return extras.get(key) if extras else pkg.get(f"extras_{key}")

    formats = odf_dataset_formats(pkg)
    geo = (
        _common._truthy(extra("geometria"))
        or _common._truthy(extra("spatial"))
        or any(fmt in GEO_FORMATS_UPPER for fmt in formats)
    )
    features = ["geo"] if geo else ["alfanumerico"]
    if any(fmt in LOD_FORMATS_UPPER for fmt in formats):
        features.append("lod")
    if _common._truthy(extra("hvd")) or _common._truthy(pkg.get("hvd")):
        features.append("hvd")
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
    if odf_dataset_is_lod(pkg):
        badges.append({"kind": "lod", "label": toolkit._("Linked Open Data")})
    geometria = odf_dataset_geometry(pkg)
    if odf_dataset_is_geo(pkg):
        shape = {"punto": "puntuale", "area": "areale", "linea": "lineare"}.get(geometria)
        label = (
            toolkit._("Geodati · {shape}").format(shape=shape) if shape else toolkit._("Geodati")
        )
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
        "download": _common._resource_download_url(result, first) if first else "",
        "size": odf_filesize(first.get("size")),
    }


def _series_siblings(pkg, fq, limit):
    """Altri dataset che soddisfano `fq`, escluso sé stesso (via package_search).

    Nel caso delle revisioni `fq` cita `extras_is_version_of`: il filtro del
    catalogo (vedi `before_dataset_search` nel plugin) le lascia passare proprio
    perché la ricerca le nomina esplicitamente.
    """
    data = _common._search(rows=limit + 1, fq=fq, sort=_SERIES_SORT)
    items = []
    for result in data["results"]:
        if result.get("id") == pkg.get("id"):
            continue
        items.append(_series_item(result))
        if len(items) >= limit:
            break
    return items


def odf_series_info(pkg, limit=20):
    """Serie del dataset in una sola ricerca: nome, totale e membri.

    `count` è il totale della serie (incluso il dataset corrente), `members`
    sono al massimo `limit` voci pronte per il pannello (escluso sé stesso).
    Usato dalla scheda dataset per non fare due ricerche (conteggio + lista).
    """
    serie = odf_pkg_extra(pkg, "serie")
    if not serie:
        return {"serie": "", "count": 0, "members": []}
    data = _common._search(rows=limit + 1, fq=f'extras_serie:"{serie}"', sort=_SERIES_SORT)
    members = []
    for result in data.get("results") or []:
        if result.get("id") == pkg.get("id"):
            continue
        members.append(_series_item(result))
        if len(members) >= limit:
            break
    return {"serie": serie, "count": data.get("count", 0), "members": members}


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
    return _series_siblings(pkg, f'extras_serie:"{serie}"', limit)


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


def odf_dataset_revisions(pkg, limit=20):
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
        fqs = [f'extras_is_version_of:"{root}"' for root in roots]
    else:
        uris = _dataset_uris(pkg)
        if not uris:
            return []
        fqs = [f'extras_is_version_of:"{uri}"' for uri in uris]
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


def odf_dataset_contact(pkg):
    """Titolare/struttura/contatto del dataset (dcatapit o campi nativi)."""
    extras = _common._pkg_extras(pkg)
    organization = pkg.get("organization") or {}
    return {
        "holder": pkg.get("holder_name") or extras.get("rights_holder") or pkg.get("author") or "",
        "structure": organization.get("title") or pkg.get("holder_identifier") or "",
        "email": pkg.get("author_email")
        or pkg.get("maintainer_email")
        or extras.get("email")
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


# Estensioni di script lato server: un URL che termina cosi' non e' un nome di
# file da mostrare (es. `download.php?id=…` del vecchio portale).
_NON_FILE_EXTENSIONS = frozenset(("php", "asp", "aspx", "jsp", "cgi", "pl", "do"))


def odf_resource_filename(res):
    """Nome file della risorsa (basename dell'URL) se ne ha uno, altrimenti ''.

    Si mostra solo quando l'URL termina con un nome di file vero (estensione,
    esclusi gli script lato server): per i link generici (WMS, pagine web,
    `download.php`) il nome non esiste e non va inventato.
    """
    path = urlsplit((res or {}).get("url") or "").path
    name = unquote(path.rsplit("/", 1)[-1]) if path else ""
    if "." not in name:
        return ""
    return "" if name.rsplit(".", 1)[-1].lower() in _NON_FILE_EXTENSIONS else name


# Etichette italiane dei separatori CSV riconosciuti.
_SEPARATOR_LABELS = {
    ";": "punto e virgola",
    ",": "virgola",
    "\t": "tabulazione",
    "|": "barra verticale",
}


def odf_resource_separator(pkg, res):
    """Separatore di campo di una risorsa CSV, dall'extra `separatore` del dataset.

    Non si deduce dal contenuto: se il dataset non dichiara l'extra (o la
    risorsa non è CSV) non si mostra nulla, per non inventare un dato.
    """
    if ((res or {}).get("format") or "").strip().upper() != "CSV":
        return ""
    sep = (odf_pkg_extra(pkg, "separatore") or "").strip()
    if not sep:
        return ""
    label = _SEPARATOR_LABELS.get(sep, sep)
    return toolkit._("Separatore di campo: «{sep}» ({label})").format(
        sep="TAB" if sep == "\t" else sep, label=label
    )


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
