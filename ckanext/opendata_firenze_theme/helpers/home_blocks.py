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

I campi hanno un tipo (`text` o `url`) e un default dichiarati nel registro
(`BLOCKS`). Il form parte dai default; un campo vuoto significa "non mostrare
quel testo/link". Un campo assente da un valore salvato (config parziale o
vecchia) usa il default. Supporta anche il vecchio formato (lista di soli id).

I blocchi sono definiti qui: aggiungerne uno richiede solo una voce in `BLOCKS`
e il template relativo.
"""

import json
import logging
from urllib.parse import urlparse

import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)

OPTION = "ckanext.opendata_firenze_theme.homepage_blocks"

ENTRY_FIELDS = ("title", "subtitle", "cta_label", "cta_url")

FIELD_LABELS = {
    "title": "Titolo",
    "subtitle": "Sottotitolo",
    "cta_label": "Testo del link",
    "cta_url": "URL del link",
}

# id, etichetta per l'admin, template da includere in home/index.html,
# campi modificabili (nome -> tipo + default).
BLOCKS = (
    {
        "id": "hero",
        "label": "Ricerca e introduzione",
        "template": "home/blocks/hero.html",
        "fields": {},
    },
    {
        "id": "kpi",
        "label": "Indicatori di sintesi",
        "template": "home/blocks/kpi.html",
        "fields": {},
    },
    {
        "id": "featured",
        "label": "Dataset in evidenza",
        "template": "home/blocks/featured.html",
        "fields": {
            "title": {"type": "text", "default": "In evidenza"},
            "subtitle": {"type": "text", "default": ""},
            "cta_label": {"type": "text", "default": "Vedi tutti"},
            "cta_url": {"type": "url", "default": "/dataset"},
        },
    },
    {
        "id": "themes",
        "label": "Esplora per tema",
        "template": "home/blocks/themes.html",
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
        "id": "most_viewed",
        "label": "I più consultati",
        "template": "home/blocks/most_viewed.html",
        "fields": {
            "title": {"type": "text", "default": "I più consultati"},
            "subtitle": {"type": "text", "default": ""},
            "cta_label": {"type": "text", "default": "Tutto il catalogo"},
            "cta_url": {"type": "url", "default": "/dataset"},
        },
    },
    {
        "id": "news",
        "label": "News",
        "template": "home/blocks/news.html",
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
    """Dedup per id, preserva l'ordine, aggiunge i blocchi mancanti (disattivi)."""
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
    """Errori per blocco/campo (solo campi `url` non validi)."""
    errors = {}
    for entry in entries:
        for field, meta in _BY_ID[entry["id"]]["fields"].items():
            if meta["type"] != "url":
                continue
            value = entry.get(field, "")
            if value and not _valid_url(value):
                errors.setdefault(entry["id"], {})[field] = toolkit._(
                    "Inserisci un percorso che inizia con / oppure un URL http(s)."
                )
    return errors


def _field_meta(block_id):
    return {
        name: {"type": meta["type"], "label": toolkit._(FIELD_LABELS[name])}
        for name, meta in _BY_ID[block_id]["fields"].items()
    }


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
        for field in _BY_ID[block_id]["fields"]:
            value = texts.get(field)
            entry[field] = value.strip() if isinstance(value, str) else ""
        rows.append((order, position.get(block_id, len(current)), block_id, entry))
    rows.sort()
    return [row[3] for row in rows]
