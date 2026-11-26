"""Blocchi della homepage: struttura e testi configurabili dagli operatori.

L'ordine, i blocchi attivi e i testi (titolo, sottotitolo, testo e URL del link)
sono salvati in una opzione runtime di CKAN
(`ckanext.opendata_firenze_theme.homepage_blocks`, JSON) scritta con
`config_option_update` e quindi in `system_info` (DB): nessun file da
modificare e nessun riavvio. La lettura passa dal DB (`model.get_system_info`)
e non dalla config in-memory del processo, cosi' la modifica e' subito visibile
anche agli altri worker.

Formato del valore (lista ordinata; ordine = posizione nell'array):

    [{"id": "featured", "enabled": true, "title": "", "subtitle": "",
      "cta_label": "", "cta_url": ""}, ...]

I campi hanno un tipo (`text`, `url` o `select`) e un default dichiarati nel registro
(`BLOCKS`). Il form parte dai default; un campo vuoto significa "non mostrare
quel testo/link". Un campo assente da un valore salvato (config parziale o
vecchia) usa il default. Supporta anche il vecchio formato (lista di soli id).

I blocchi sono definiti qui: aggiungerne uno richiede una voce in `BLOCKS`
(builder, limite e campi) e il template relativo.
"""

import json
import logging
from urllib.parse import urlparse

import ckan.plugins.toolkit as toolkit

from . import dataset, home, query
from .constants import DEFAULT_MOST_VIEWED_PERIOD, MOST_VIEWED_PERIODS

log = logging.getLogger(__name__)

OPTION = "ckanext.opendata_firenze_theme.homepage_blocks"

ENTRY_FIELDS = ("title", "subtitle", "cta_label", "cta_url")

FIELD_LABELS = {
    "title": "Titolo",
    "subtitle": "Sottotitolo",
    "cta_label": "Testo del link",
    "cta_url": "URL del link",
    "period": "Periodo",
}


# Costruttori dei dati dei blocchi. Il descriptor in `BLOCKS` li possiede,
# insieme al limite: aggiungere un blocco significa una voce nel registro (più
# il template), senza un secondo mapping nel collector.
def _datasets(pkgs, cache):
    """Lista + fatti, condivisi fra i blocchi dello stesso render."""
    cached = cache.setdefault("facts", {})
    block_facts = {}
    for pkg in pkgs or []:
        if isinstance(pkg, dict):
            pkg_id = pkg.get("id")
            if pkg_id:
                if pkg_id not in cached:
                    cached[pkg_id] = dataset.odf_dataset_facts(pkg)
                block_facts[pkg_id] = cached[pkg_id]
    return {"datasets": pkgs, "facts": block_facts}


def _total(cache):
    if "total" not in cache:
        cache["total"] = home.odf_dataset_count()
    return cache["total"]


def _hero(cache, block):
    return {"count": _total(cache)}


def _kpi(cache, block):
    return {"kpis": home.odf_home_kpis(total=_total(cache))}


def _featured(cache, block):
    return _datasets(home.odf_featured_datasets(block["limit"]), cache)


def _latest(cache, block):
    return _datasets(home.odf_latest_datasets(block["limit"]), cache)


def _themes(cache, block):
    return {"themes": home.odf_themes_visible()}


def _lod(cache, block):
    return _datasets(home.odf_lod_datasets(block["limit"]), cache)


def _most_viewed(cache, block):
    """Dati di "I più consultati", con fallback se il tracking non risponde."""
    period = block.get("period", DEFAULT_MOST_VIEWED_PERIOD)
    datasets = home.odf_most_viewed(block["limit"], period)
    if datasets is None:
        datasets = home.odf_most_viewed_fallback(block["limit"])
        for pkg in datasets:
            pkg["views_period"] = 0
        return {**_datasets(datasets, cache), "period_label": ""}
    return {
        **_datasets(datasets, cache),
        "period_label": home.odf_most_viewed_label(period),
    }


def _news(cache, block):
    return {"news": home.odf_news(block["limit"])}


# id, etichetta per l'admin, template da includere in home/index.html,
# builder/limite dei dati e campi modificabili (nome -> tipo + default).
BLOCKS = (
    {
        "id": "hero",
        "label": "Ricerca e introduzione",
        "template": "home/blocks/hero.html",
        "builder": _hero,
        "fields": {},
    },
    {
        "id": "kpi",
        "label": "Indicatori di sintesi",
        "template": "home/blocks/kpi.html",
        "builder": _kpi,
        "fields": {},
    },
    {
        "id": "featured",
        "label": "Dataset in evidenza",
        "template": "home/blocks/featured.html",
        "builder": _featured,
        "limit": 7,
        "fields": {
            "title": {"type": "text", "default": "In evidenza"},
            "subtitle": {"type": "text", "default": ""},
            "cta_label": {"type": "text", "default": "Vedi tutti"},
            "cta_url": {"type": "url", "default": "/dataset"},
        },
    },
    {
        "id": "latest",
        "label": "Ultimi pubblicati",
        "template": "home/blocks/latest.html",
        "builder": _latest,
        "limit": 6,
        "fields": {
            "title": {"type": "text", "default": "Ultimi pubblicati"},
            "subtitle": {
                "type": "text",
                "default": "I dataset aggiunti più di recente al catalogo.",
            },
            "cta_label": {"type": "text", "default": "Tutto il catalogo"},
            "cta_url": {"type": "url", "default": "/dataset"},
        },
    },
    {
        "id": "themes",
        "label": "Esplora per tema",
        "template": "home/blocks/themes.html",
        "builder": _themes,
        "fields": {
            "title": {"type": "text", "default": "Esplora per tema"},
            "subtitle": {
                "type": "text",
                "default": (
                    "Sfoglia i dati per argomento: 13 temi che seguono lo standard "
                    "italiano per i dati aperti (DCAT-AP_IT). Per una ricerca più "
                    "fine, nel catalogo trovi anche i filtri INSPIRE e ISO 19115."
                ),
            },
        },
    },
    {
        "id": "lod",
        "label": "Linked Open Data",
        "template": "home/blocks/lod.html",
        "builder": _lod,
        "limit": 6,
        "fields": {
            "title": {"type": "text", "default": "Linked Open Data"},
            "subtitle": {
                "type": "text",
                "default": (
                    "Dataset con una risorsa RDF, pensati per essere collegati ad "
                    "altri dati sul web."
                ),
            },
            "cta_label": {"type": "text", "default": "Vedi tutti i Linked Open Data"},
            "cta_url": {"type": "url", "default": f"/dataset?{query.FEATURES}={query.LOD}"},
        },
    },
    {
        "id": "most_viewed",
        "label": "I più consultati",
        "template": "home/blocks/most_viewed.html",
        "builder": _most_viewed,
        "limit": 4,
        "fields": {
            "title": {"type": "text", "default": "I più consultati"},
            "subtitle": {"type": "text", "default": ""},
            "cta_label": {"type": "text", "default": "Tutto il catalogo"},
            "cta_url": {"type": "url", "default": "/dataset"},
            "period": {
                "type": "select",
                "default": DEFAULT_MOST_VIEWED_PERIOD,
                "options": {code: label for code, (_, label) in MOST_VIEWED_PERIODS.items()},
            },
        },
    },
    {
        "id": "news",
        "label": "News",
        "template": "home/blocks/news.html",
        "builder": _news,
        "limit": 3,
        "fields": {
            "title": {"type": "text", "default": "News"},
            "subtitle": {"type": "text", "default": ""},
            "cta_label": {"type": "text", "default": "Archivio"},
            "cta_url": {"type": "url", "default": "/blog"},
        },
    },
)

DEFAULT_IDS = tuple(block["id"] for block in BLOCKS)
_BY_ID = {block["id"]: block for block in BLOCKS}


def _default_entry(block_id):
    block = _BY_ID[block_id]
    entry = {"id": block_id, "enabled": True}
    for field in ENTRY_FIELDS:
        meta = block["fields"].get(field)
        default = meta["default"] if meta else ""
        entry[field] = toolkit._(default) if default else ""
    # Campi tipizzati aggiuntivi (es. il periodo de "I più consultati").
    for field, meta in block["fields"].items():
        if field in ENTRY_FIELDS:
            continue
        default = meta.get("default", "")
        entry[field] = (
            default if meta["type"] == "select" else (toolkit._(default) if default else "")
        )
    return entry


def _normalize_entry(item):
    block_id = item["id"]
    entry = _default_entry(block_id)
    entry["enabled"] = bool(item.get("enabled", True))
    for field, meta in _BY_ID[block_id]["fields"].items():
        if field not in item:
            # config parziale/vecchia: resta il default
            continue
        value = item[field]
        value = value.strip() if isinstance(value, str) else ""
        if meta["type"] == "select":
            if value not in meta["options"]:
                value = meta["default"]
            entry[field] = value
            continue
        if meta["type"] == "url" and value and not _valid_url(value):
            # difesa in profondita': un valore scritto direttamente via API o
            # da un override di config non deve finire in un href.
            log.warning(
                "URL non valido per %s.%s in %s: valore scartato",
                block_id,
                field,
                OPTION,
            )
            value = ""
        entry[field] = value
    return entry


def _complete(entries):
    """Dedup per id, preserva l'ordine, aggiunge i blocchi mancanti (disattivi).

    Nota: un blocco introdotto in una versione successiva del tema compare
    spento nelle config gia' salvate; va attivato da /ckan-admin/homepage.
    Cosi' non ricompare nulla che l'admin avesse escluso.
    """
    by_id = {}
    ordered = []
    for entry in entries:
        if entry["id"] in by_id:
            continue
        by_id[entry["id"]] = entry
        ordered.append(entry)
    for block_id in DEFAULT_IDS:
        if block_id not in by_id:
            missing = _default_entry(block_id)
            missing["enabled"] = False
            ordered.append(missing)
    return ordered


def _parse_config(raw):
    """Lista ordinata di blocchi dal valore salvato, o None se non valido."""
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(data, list):
        return None
    entries = []
    for item in data:
        if isinstance(item, str) and item in _BY_ID:
            # vecchio formato: lista di soli id abilitati
            entries.append(_default_entry(item))
        elif isinstance(item, dict) and item.get("id") in _BY_ID:
            entries.append(_normalize_entry(item))
    return _complete(entries)


def _raw_value():
    from ckan import model

    # get_system_info gestisce gia' da se' il caso "tabella assente" (ritorna
    # None); un errore DB vero deve emergere, non essere mascherato.
    raw = model.get_system_info(OPTION)
    if raw is None:
        raw = toolkit.config.get(OPTION, "")
    return raw


def _entries():
    parsed = _parse_config(_raw_value())
    if parsed is None:
        return [_default_entry(block_id) for block_id in DEFAULT_IDS]
    return parsed


def _valid_url(value):
    """Percorso assoluto (/...) o URL http(s); niente schemi tipo javascript:."""
    if not value:
        return True
    if any(ord(char) < 32 for char in value) or any(char.isspace() for char in value):
        return False
    if "\\" in value:
        return False
    if value.startswith("//"):
        return False
    if value.startswith("/"):
        return True
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def validate_entries(entries):
    """Errori per blocco/campo (URL non validi e select fuori elenco)."""
    errors = {}
    for entry in entries:
        for field, meta in _BY_ID[entry["id"]]["fields"].items():
            value = entry.get(field, "")
            if meta["type"] == "select":
                if value not in meta["options"]:
                    errors.setdefault(entry["id"], {})[field] = toolkit._(
                        "Scegli un periodo valido."
                    )
                continue
            if meta["type"] != "url":
                continue
            if value and not _valid_url(value):
                errors.setdefault(entry["id"], {})[field] = toolkit._(
                    "Inserisci un percorso che inizia con / oppure un URL http(s)."
                )
    return errors


def _field_meta(block_id):
    fields = {}
    for name, meta in _BY_ID[block_id]["fields"].items():
        field = {"type": meta["type"], "label": toolkit._(FIELD_LABELS[name])}
        if meta["type"] == "select":
            field["options"] = {code: toolkit._(label) for code, label in meta["options"].items()}
        fields[name] = field
    return fields


def admin_blocks(entries):
    """Struttura per il form admin, a partire da una lista di entry."""
    return [
        {
            "id": entry["id"],
            "label": _BY_ID[entry["id"]]["label"],
            "fields": _field_meta(entry["id"]),
            "enabled": entry["enabled"],
            "order": position,
            "title": entry.get("title", ""),
            "subtitle": entry.get("subtitle", ""),
            "cta_label": entry.get("cta_label", ""),
            "cta_url": entry.get("cta_url", ""),
            "values": {name: entry.get(name, "") for name in _BY_ID[entry["id"]]["fields"]},
        }
        for position, entry in enumerate(entries)
    ]


def odf_home_blocks():
    """Blocchi attivi, nell'ordine configurato, con i testi da mostrare."""
    return [
        {
            "id": entry["id"],
            "template": _BY_ID[entry["id"]]["template"],
            "title": entry.get("title", ""),
            "subtitle": entry.get("subtitle", ""),
            "cta_label": entry.get("cta_label", ""),
            "cta_url": entry.get("cta_url", ""),
            **{name: entry.get(name, "") for name in _BY_ID[entry["id"]]["fields"]},
        }
        for entry in _entries()
        if entry["enabled"]
    ]


def odf_home_blocks_admin():
    """Tutti i blocchi con stato, ordine, testi e campi modificabili."""
    return admin_blocks(_entries())


def entries_from_form(enabled_ids, order_values, text_values, current_ids):
    """Lista ordinata di blocchi da salvare, costruita dai campi del form.

    I testi arrivano dal form gia' precompilati con i default: un valore vuoto
    significa "non mostrare quel testo/link". `order_values` e `text_values`
    sono dict id -> valore; gli id sconosciuti e i campi non supportati vengono
    ignorati.
    """
    current = list(current_ids or DEFAULT_IDS)
    position = {block_id: n for n, block_id in enumerate(current)}
    enabled = set(enabled_ids)
    rows = []
    for block_id in DEFAULT_IDS:
        try:
            order = int(order_values.get(block_id))
        except (TypeError, ValueError):
            order = position.get(block_id, len(current))
        entry = _default_entry(block_id)
        entry["enabled"] = block_id in enabled
        texts = text_values.get(block_id) or {}
        for field, meta in _BY_ID[block_id]["fields"].items():
            value = texts.get(field)
            if meta["type"] == "select":
                # Campo assente (POST parziale): default. Valore presente ma
                # fuori elenco: lo segnala validate_entries, non lo salviamo.
                entry[field] = (
                    meta["default"]
                    if value is None
                    else (value.strip() if isinstance(value, str) else "")
                )
            else:
                entry[field] = value.strip() if isinstance(value, str) else ""
        rows.append((order, position.get(block_id, len(current)), block_id, entry))
    rows.sort()
    return [row[3] for row in rows]


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_home_blocks": odf_home_blocks,
}


def form_view(form):
    """Stato del form admin a partire dal mapping del form (una sola interfaccia).

    `views.homepage_blocks` non compone più i nomi `order_<id>`/`<field>_<id>`:
    li conosce questo modulo e restituisce voci, errori e blocchi da mostrare.
    """
    blocks = admin_blocks(_entries())
    current = [block["id"] for block in blocks]
    orders = {block["id"]: form.get(f"order_{block['id']}") for block in blocks}
    texts = {
        block["id"]: {field: form.get(f"{field}_{block['id']}") for field in block["fields"]}
        for block in blocks
    }
    entries = entries_from_form(form.getlist("enabled"), orders, texts, current)
    errors = validate_entries(entries)
    return {"entries": entries, "errors": errors, "blocks": admin_blocks(entries)}
