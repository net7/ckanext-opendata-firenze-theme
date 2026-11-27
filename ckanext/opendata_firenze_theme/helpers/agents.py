"""Nomi degli enti: rimozione del prefisso ridondante "Comune di Firenze - ".

I metadati arvestiti dalle fonti del Comune scrivono il nome dell'ente come
"Comune di Firenze - Direzione Cultura". Il portale è del Comune, quindi il
prefisso è ridondante quando il valore nomina già una direzione/ufficio: va
tolto dai campi che contengono un ente, non dai titoli.

Nelle descrizioni la frase compare in prosa ("Fonte: Comune di Firenze -
Direzione Cultura", "Elaborazioni del Comune di Firenze - Ufficio di
Statistica"): qui si toccano solo le attribuzioni note, per non rompere frasi
come "Beneficiario: Comune di Firenze - Asse V PIUSS".

Il modulo è l'unico punto che conosce prefisso, campi e regole sulle
descrizioni: lo usano il post-processing (package_create/package_update) e il
comando di backfill (`ckan odf-normalize-agents`). Vedi ADR 0016.
"""

import json
import re

PREFIX = "Comune di Firenze - "

# Campi stringa che contengono il nome di un ente (in cima al package o negli
# extras, a seconda della forma del dict).
TEXT_FIELDS = ("author", "maintainer", "holder_name", "publisher_name")

# Extras che contengono una lista di agenti con nome localizzato:
# extra -> chiave che contiene {"it": ..., "en": ...}.
JSON_FIELDS = {"creator": "creator_name", "publisher": "publisher_name"}

# Unità organizzative che possono seguire il prefisso. "Asse" (es. "Asse V
# PIUSS") è escluso di proposito: non è un ente e togliere il prefisso
# cambierebbe il senso della frase.
_UNIT = r"(?:Direzione|Ufficio|Anagrafe|Comparto)"
_NOTE_RE = re.compile(
    r"(?P<pre>Fonte:\s|del\s|nel\s)Comune di Firenze - (?P<unit>" + _UNIT + r")\b"
)

# Preposizione articolata corretta dopo il taglio del prefisso.
_ARTICLES = {
    ("del", "Direzione"): "della Direzione",
    ("del", "Ufficio"): "dell'Ufficio",
    ("del", "Anagrafe"): "dell'Anagrafe",
    ("del", "Comparto"): "del Comparto",
    ("nel", "Direzione"): "nella Direzione",
    ("nel", "Ufficio"): "nell'Ufficio",
    ("nel", "Anagrafe"): "nell'Anagrafe",
    ("nel", "Comparto"): "nel Comparto",
}


def strip_prefix(value):
    """Nome dell'ente senza il prefisso; invariato se non lo ha."""
    if not isinstance(value, str) or not value.startswith(PREFIX):
        return value
    # Il nome può arrivare con doppi spazi ("Direzione Generale -  Servizio"):
    # dopo il taglio li normalizziamo, così le due varianti non restano distinte.
    return " ".join(value[len(PREFIX) :].split())


def normalize_notes(notes):
    """Toglie il prefisso dalle attribuzioni nella descrizione.

    Gestisce solo le forme presenti in catalogo e sicure da riscrivere;
    "Fonte: Comune di Firenze - Asse V PIUSS" resta intatto.
    """
    if not isinstance(notes, str):
        return notes

    def _replace(match):
        pre, unit = match.group("pre").strip(), match.group("unit")
        if pre == "Fonte:":
            return f"Fonte: {unit}"
        return _ARTICLES.get((pre, unit), f"{pre} {unit}")

    return _NOTE_RE.sub(_replace, notes)


def _get_field(data_dict, key):
    """Valore del campo nella forma in cui si trova (extras o cima)."""
    extras = data_dict.get("extras")
    if isinstance(extras, dict) and key in extras:
        return extras[key]
    if isinstance(extras, list):
        for extra in extras:
            if isinstance(extra, dict) and extra.get("key") == key:
                return extra.get("value")
    return data_dict.get(key)


def _set_field(data_dict, key, value):
    """Scrive il campo dove esiste già; altrimenti in cima al package."""
    extras = data_dict.get("extras")
    if isinstance(extras, dict) and key in extras:
        extras[key] = value
        return
    if isinstance(extras, list):
        for extra in extras:
            if isinstance(extra, dict) and extra.get("key") == key:
                extra["value"] = value
                return
    data_dict[key] = value


def _normalize_names(node, name_key):
    """Normalizza i nomi dentro un agente JSON; True se qualcosa è cambiato."""
    changed = False
    if isinstance(node, list):
        for item in node:
            changed = _normalize_names(item, name_key) or changed
    elif isinstance(node, dict):
        for key, value in node.items():
            if key != name_key:
                if isinstance(value, (list, dict)):
                    changed = _normalize_names(value, name_key) or changed
                continue
            if isinstance(value, str):
                new = strip_prefix(value)
                if new != value:
                    node[key] = new
                    changed = True
            elif isinstance(value, dict):
                for lang, name in value.items():
                    if isinstance(name, str):
                        new = strip_prefix(name)
                        if new != name:
                            value[lang] = new
                            changed = True
    return changed


def _normalize_json(value, name_key):
    """Riscrive il JSON dell'extra solo se contiene il prefisso."""
    if isinstance(value, (list, dict)):
        if not _normalize_names(value, name_key):
            return value
        return json.dumps(value, ensure_ascii=False)
    if not isinstance(value, str):
        return value
    try:
        data = json.loads(value)
    except ValueError:
        return value
    if not _normalize_names(data, name_key):
        return value
    return json.dumps(data, ensure_ascii=False)


def normalize_package(data_dict):
    """Normalizza in place i campi ente e le attribuzioni nella descrizione."""
    if not isinstance(data_dict, dict):
        return data_dict

    for key in TEXT_FIELDS:
        value = _get_field(data_dict, key)
        new = strip_prefix(value)
        if new != value:
            _set_field(data_dict, key, new)

    for key, name_key in JSON_FIELDS.items():
        value = _get_field(data_dict, key)
        new = _normalize_json(value, name_key)
        if new != value:
            _set_field(data_dict, key, new)

    notes = data_dict.get("notes")
    new_notes = normalize_notes(notes)
    if new_notes != notes:
        data_dict["notes"] = new_notes

    return data_dict
