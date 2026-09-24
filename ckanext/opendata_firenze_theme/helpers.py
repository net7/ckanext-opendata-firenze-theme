"""Helper del tema usati dai template (registrati in plugin.py).

Forniscono i dati della home (KPI, temi, dataset in evidenza/consultati, news)
senza mettere query nei template. Tutti gli helper sono difensivi: se Solr o
un'estensione non sono disponibili, tornano valori vuoti invece di rompere la
pagina.
"""

import logging
import json
from urllib.parse import urlencode

import ckan.lib.helpers as ckan_h
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
GEO_FORMATS_UPPER = frozenset(fmt.upper() for fmt in GEO_FORMATS)

THEME_CODES = frozenset(code for code, _ in THEMES)

# Tipi di geometria riconosciuti (extra `geometria`).
GEOMETRY_SHAPES = ("punto", "area", "linea")


def odf_package_theme(pkg):
    """Codice del tema DCAT-AP_IT di un package, o None.

    Il tema arriva come URI (spesso una lista JSON) nel campo `theme` o
    nell'extra omonimo; si tiene solo se corrisponde a uno dei 13 temi
    (dcatapit usa `OP_DATPRO` = "Other" come default, che non mostriamo).
    """
    raw = pkg.get("theme")
    if not raw:
        extras = pkg.get("extras") or []
        if isinstance(extras, dict):
            raw = extras.get("theme")
        else:
            for extra in extras:
                if extra.get("key") == "theme":
                    raw = extra.get("value")
                    break
    if not raw:
        return None
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            raw = [raw]
    if isinstance(raw, (list, tuple)):
        raw = raw[0] if raw else None
    if not isinstance(raw, str) or not raw:
        return None
    code = raw.rstrip("/").rsplit("/", 1)[-1]
    return code if code in THEME_CODES else None


def odf_facet_all_url(facet, values):
    """URL che seleziona TUTTI i valori di una faccetta.

    Serve al link "Tutti" dei gruppi faccette: mantiene gli altri parametri
    correnti e sostituisce i valori della faccetta con quelli passati (parametri
    ripetuti, come fa CKAN). `h.add_url_param` non gestisce le liste.
    """
    from flask import request

    args = [(key, value) for key, value in request.args.items(multi=True) if key not in (facet, "page")]
    args.extend((facet, value) for value in values)
    query = urlencode(args)
    url = toolkit.url_for("dataset.search")
    return f"{url}?{query}" if query else url


# Ordine di visualizzazione dei gruppi faccetta come il mockup (Temi per primo,
# poi Formato, Aggiornamento, Chi pubblica, Caratteristiche e infine le faccette
# geografiche/classificazioni e le altre). "Tipo di geometria" (2° nel mockup)
# non ha un campo Solr dedicato senza ckanext-scheming: resta non implementato.
FACET_ORDER = (
    "theme",
    "dcat_theme",
    "res_format",
    "frequency",
    "organization",
    "hvd",
    "spatial",
    "groups",
    "tags",
    "license_id",
)


def odf_facet_groups(facets):
    """Gruppi faccetta del catalogo pronti per il template.

    Deduplica i gruppi con la stessa etichetta (`theme`/`dcat_theme`), li ordina
    secondo `FACET_ORDER` (poi gli eventuali altri) e calcola le voci attive.
    Ritorna `{'groups': [{'name', 'label', 'items', 'selected'}], 'active': bool}`.
    """
    if not facets:
        return {"groups": [], "active": False}
    labels = {
        "theme": toolkit._("Temi"),
        "dcat_theme": toolkit._("Temi"),
        "res_format": toolkit._("Formato dei file"),
        "frequency": toolkit._("Aggiornamento"),
        "organization": toolkit._("Chi pubblica"),
        "spatial": toolkit._("Classificazione geografica"),
        "groups": toolkit._("Gruppi"),
        "tags": toolkit._("Parole chiave"),
        "license_id": toolkit._("Licenza"),
        "hvd": toolkit._("Caratteristiche"),
    }
    seen = set()
    names = []
    for name in facets:
        label = labels.get(name, facets[name]["title"])
        if label not in seen:
            seen.add(label)
            names.append(name)
    ordered = [name for name in FACET_ORDER if name in names]
    ordered += [name for name in names if name not in ordered]
    groups = []
    active = False
    for name in ordered:
        items = ckan_h.get_facet_items_dict(name, facets)
        if not items:
            continue
        selected = len([item for item in items if item.get("active")])
        active = active or bool(selected)
        groups.append(
            {
                "name": name,
                "label": labels.get(name, facets[name]["title"]),
                "entries": items,
                "selected": selected,
            }
        )
    return {"groups": groups, "active": active}


def _it(n):
    """Intero con separatore delle migliaia italiano (2086 -> '2.086')."""
    return format(int(n), ",d").replace(",", ".")


def odf_number(value):
    """Numero per la UI (int->it-IT, con migliaia); '' se non disponibile."""
    if value is None or value == "":
        return ""
    try:
        return _it(value)
    except (TypeError, ValueError):
        return ""


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
    """{codice_tema: numero_dataset} dai facet tema.

    dcatapit indicizza i temi come `dcat_theme` (dal extra `theme`); `theme` e'
    il nome usato in alcune configurazioni. Si prende il primo facet popolato,
    per non contare due volte lo stesso dataset.
    """
    data = _search(rows=0, **{"facet.field": ["dcat_theme", "theme"], "facet.limit": 100})
    for field in ("dcat_theme", "theme"):
        items = _facet_items(data, field)
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
    return _search(rows=0)["count"]


def odf_home_kpis():
    """Le 4 card KPI della home (set del mockup).

    1) dataset nel catalogo, 2) dati alfanumerici (non geografici),
    3) dati geografici, 4) capitoli dell'Annuario Statistico + tavole collegate.
    """
    base = _search(rows=0, **{"facet.field": ["organization"], "facet.limit": 100})
    total = base["count"]
    # "geografici" = dataset con almeno una risorsa in un formato geo: piu'
    # affidabile del campo Solr `spatial` (ckanext-spatial non indicizza gli
    # extra `spatial` impostati a mano) e coerente col badge "Geodati".
    geo_formats = " OR ".join(sorted(GEO_FORMATS))
    geo = _search(rows=0, fq=f"res_format:({geo_formats})")["count"]
    tavole = _search(rows=0, fq="extras_capitolo:[* TO *]")["count"]
    serie = _search(rows=0, fq="extras_serie:[* TO *]")["count"]
    return [
        {
            "value": _it(total),
            "label": toolkit._("dataset nel catalogo"),
            "delta": toolkit._("tutti in licenza aperta CC BY 4.0"),
        },
        {
            "value": _it(max(total - geo, 0)),
            "label": toolkit._("dati alfanumerici"),
            "delta": toolkit._("organizzati in {num} serie").format(num=_it(serie)),
        },
        {
            "value": _it(geo),
            "label": toolkit._("dati geografici"),
            "delta": toolkit._("con anteprima su mappa"),
        },
        {
            "value": _it(len(ANNUARIO_CHAPTERS)),
            "label": toolkit._("capitoli dell'Annuario Statistico"),
            "delta": toolkit.ungettext("{num} tavola statistica", "{num} tavole statistiche", tavole).format(num=_it(tavole)),
        },
    ]


def odf_featured_datasets(limit=3):
    """Dataset in evidenza: prima gli HVD (`extras_hvd`), poi i più recenti.

    Gli HVD hanno la precedenza; se sono meno di `limit` si completa con i
    dataset aggiornati di recente, così il carosello ha sempre abbastanza voci.
    """
    featured = _search(rows=limit, fq="extras_hvd:true", sort="metadata_modified desc")["results"]
    if len(featured) >= limit:
        return featured
    recent = _search(rows=limit + len(featured), sort="metadata_modified desc")["results"]
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
    tracked = _search(rows=limit, sort="views_recent desc")
    if tracked["count"]:
        return tracked["results"]
    return _search(rows=limit, sort="metadata_modified desc")["results"]


def odf_geo_datasets(limit=12):
    """Dataset con almeno una risorsa in un formato geografico.

    Usa la stessa definizione di "dati geografici" delle KPI della home (formati
    in `GEO_FORMATS`), così conteggi e liste restano coerenti.
    """
    geo_formats = " OR ".join(sorted(GEO_FORMATS))
    return _search(rows=limit, fq=f"res_format:({geo_formats})", sort="metadata_modified desc")["results"]


def odf_geo_search_query():
    """Query Solr che filtra il catalogo sui formati geografici.

    Per il link "Filtra il catalogo per geodati": CKAN non sa fare l'OR tra più
    valori di una faccetta via URL (i parametri ripetuti finiscono in AND nel
    `fq`), quindi si passa la query al campo `q` della ricerca.
    """
    return "res_format:(" + " OR ".join(sorted(GEO_FORMATS)) + ")"


# 13 capitoli dell'Annuario Statistico (dal mockup). Il campo `capitolo` non è
# nativo: è un extra custom, che CKAN indicizza in Solr come `extras_capitolo`
# (decisione aperta, vedi docs/adr/0005). Senza l'extra i capitoli sono vuoti.
ANNUARIO_CHAPTERS = (
    "Ambiente e territorio",
    "Popolazione",
    "Sanità",
    "Sicurezza sociale",
    "Istruzione e cultura",
    "Giustizia",
    "Economia e lavoro",
    "Prezzi",
    "Trasporti",
    "Amministrazione comunale",
    "Quartieri",
    "Spettacolo e sport",
    "Le donne a Firenze",
)


def odf_annuario_chapters():
    """Capitoli dell'Annuario con il numero di dataset collegati.

    I conteggi arrivano dal facet `extras_capitolo` (una sola query); il campo è
    popolato solo se i dataset hanno l'extra `capitolo`.
    """
    data = _search(rows=0, **{"facet.field": ["extras_capitolo"], "facet.limit": 100})
    counts = {item["name"]: item["count"] for item in _facet_items(data, "extras_capitolo")}
    return [
        {"index": index, "name": name, "count": counts.get(name, 0)} for index, name in enumerate(ANNUARIO_CHAPTERS, start=1)
    ]


def odf_annuario_datasets(chapter, limit=12):
    """Dataset del capitolo dell'Annuario (extra `capitolo`), per titolo."""
    if not chapter:
        return []
    data = _search(rows=limit, fq=f'extras_capitolo:"{chapter}"', sort="title_string asc")
    return data["results"]


def odf_news(limit=3):
    """Ultime news dal blog di ckanext-pages (vuoto se non disponibile)."""
    try:
        from ckanext.pages.plugin import get_recent_blog_posts

        return get_recent_blog_posts(number=limit) or []
    except Exception:
        log.warning("ckanext-pages non disponibile per le news", exc_info=True)
        return []


# Etichette italiane per i codici frequenza EU (dcatapit usa il vocabolario
# `frequency` di Publications Office: ANNUAL, MONTHLY, IRREG…).
FREQUENCY_LABELS = {
    "ANNUAL": "annuale",
    "BIENNIAL": "biennale",
    "BIWEEKLY": "quindicinale",
    "CONT": "continua",
    "DAILY": "giornaliera",
    "HOURLY": "oraria",
    "IRREG": "irregolare",
    "MONTHLY": "mensile",
    "QUARTERLY": "trimestrale",
    "REALTIME": "in tempo reale",
    "SEMIANNUAL": "semestrale",
    "TRIENNIAL": "triennale",
    "UNKNOWN": "non nota",
    "WEEKLY": "settimanale",
}


def _pkg_extras(pkg):
    """{chiave: valore} degli extras del package (lista o dict)."""
    extras = pkg.get("extras") or []
    if isinstance(extras, dict):
        return extras
    return {e.get("key"): e.get("value") for e in extras if e.get("key")}


def _truthy(value):
    return str(value).strip().lower() in ("1", "true", "yes", "si", "sì", "y")


def odf_pkg_extra(pkg, key, default=None):
    """Valore di un extra del dataset (None se assente)."""
    return _pkg_extras(pkg).get(key, default)


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
    value = (_pkg_extras(pkg).get("geometria") or "").strip().lower()
    return value if value in GEOMETRY_SHAPES else None


def odf_dataset_is_geo(pkg):
    """True se il dataset ha contenuto geografico.

    Unico punto di verità per il badge "Geodati": extra `geometria`/`spatial`
    oppure almeno una risorsa in un formato con anteprima su mappa.
    """
    extras = _pkg_extras(pkg)
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
    extras = _pkg_extras(pkg)
    badges = []
    if _truthy(extras.get("hvd")) or _truthy(pkg.get("hvd")):
        badges.append({"kind": "hvd", "label": toolkit._("High Value Dataset")})
    geometria = odf_dataset_geometry(pkg)
    if odf_dataset_is_geo(pkg):
        shape = {"punto": "puntuale", "area": "areale", "linea": "lineare"}.get(geometria)
        label = toolkit._("Geodati · {shape}").format(shape=shape) if shape else toolkit._("Geodati")
        badges.append({"kind": "geo", "label": label})
    if _truthy(extras.get("realtime")):
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
        raw = _pkg_extras(pkg).get("openness_score")
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
    data = _search(rows=limit + 1, fq=f"theme:{tema}", sort="metadata_modified desc")
    return [r for r in data["results"] if r.get("id") != pkg.get("id")][:limit]


def odf_dataset_contact(pkg):
    """Titolare/struttura/contatto del dataset (dcatapit o campi nativi)."""
    extras = _pkg_extras(pkg)
    organization = pkg.get("organization") or {}
    return {
        "holder": pkg.get("holder_name") or extras.get("rights_holder") or pkg.get("author") or "",
        "structure": organization.get("title") or pkg.get("holder_identifier") or "",
        "email": pkg.get("author_email") or pkg.get("maintainer_email") or extras.get("email") or "",
    }


def _resource_download_url(pkg, res):
    """URL di download di una risorsa (route CKAN per gli upload)."""
    if res.get("url_type") == "upload":
        try:
            return toolkit.url_for("resource.download", id=pkg.get("name"), resource_id=res.get("id"))
        except Exception:
            return res.get("url") or ""
    return res.get("url") or ""


def odf_resource_download_url(pkg, res):
    """URL di download di una singola risorsa (route CKAN per gli upload)."""
    return _resource_download_url(pkg, res)


# Titoli dei pannelli della scheda risorsa, per tipo di vista CKAN.
VIEW_TITLES = {
    "datatables_view": "Anteprima dei dati",
    "datastore": "Anteprima dei dati",
    "recline_grid_view": "Anteprima dei dati",
    "recline_graph_view": "Grafico",
    "recline_map_view": "Mappa",
    "geoview": "Mappa",
    "geo_view": "Mappa",
    "geojson_view": "Mappa",
    "wmts_view": "Mappa",
    "shp_view": "Mappa",
    "image_view": "Anteprima",
    "text_view": "Anteprima",
    "pdf_view": "Anteprima",
    "officedocs_view": "Anteprima",
    "html_view": "Anteprima",
    "web_view": "Anteprima",
}


def odf_resource_view_title(view):
    """Titolo del pannello di una vista risorsa (per tipo, o titolo della vista)."""
    view_type = (view.get("view_type") or "").lower()
    if view_type in VIEW_TITLES:
        return toolkit._(VIEW_TITLES[view_type])
    return view.get("title") or toolkit._("Anteprima")


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
                "href": _resource_download_url(pkg, res),
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


def odf_date(value, fmt="%d/%m/%Y"):
    """Data ISO/datetime -> 'gg/mm/aaaa'; stringa vuota se assente."""
    if not value:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime(fmt)
    text = str(value)
    try:
        from datetime import datetime

        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime(fmt)
    except ValueError:
        return text[:10]


def odf_frequency_label(code):
    """Etichetta italiana di un codice frequenza EU (fallback: codice)."""
    if not code:
        return ""
    return FREQUENCY_LABELS.get(str(code).upper(), str(code))


def odf_filesize(size):
    """Byte -> '1,2 MB' (it-IT); stringa vuota se non disponibile."""
    if not size:
        return ""
    try:
        value = float(size)
    except (TypeError, ValueError):
        return ""
    if value <= 0:
        return ""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.1f}".replace(".", ",") + f" {unit}"
        value /= 1024
    return ""


def get_helpers():
    return {
        "odf_dataset_count": odf_dataset_count,
        "odf_package_theme": odf_package_theme,
        "odf_facet_all_url": odf_facet_all_url,
        "odf_facet_groups": odf_facet_groups,
        "odf_home_kpis": odf_home_kpis,
        "odf_themes": odf_themes,
        "odf_featured_datasets": odf_featured_datasets,
        "odf_most_viewed": odf_most_viewed,
        "odf_geo_datasets": odf_geo_datasets,
        "odf_geo_search_query": odf_geo_search_query,
        "odf_news": odf_news,
        "odf_annuario_chapters": odf_annuario_chapters,
        "odf_annuario_datasets": odf_annuario_datasets,
        "odf_pkg_extra": odf_pkg_extra,
        "odf_dataset_formats": odf_dataset_formats,
        "odf_format_is_geo": odf_format_is_geo,
        "odf_dataset_badges": odf_dataset_badges,
        "odf_dataset_geometry": odf_dataset_geometry,
        "odf_dataset_is_geo": odf_dataset_is_geo,
        "odf_number": odf_number,
        "odf_dataset_openness": odf_dataset_openness,
        "odf_dataset_related": odf_dataset_related,
        "odf_dataset_contact": odf_dataset_contact,
        "odf_dataset_downloads": odf_dataset_downloads,
        "odf_resource_download_url": odf_resource_download_url,
        "odf_resource_view_title": odf_resource_view_title,
        "odf_dataset_size": odf_dataset_size,
        "odf_sql_console_enabled": odf_sql_console_enabled,
        "odf_datastore_resource_id": odf_datastore_resource_id,
        "odf_date": odf_date,
        "odf_frequency_label": odf_frequency_label,
        "odf_filesize": odf_filesize,
    }
