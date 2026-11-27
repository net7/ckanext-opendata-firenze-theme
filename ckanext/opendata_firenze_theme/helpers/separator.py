"""Separatore CSV: extra del dataset, estrazione dalla descrizione e scrittura.

Il separatore è un extra del dataset (`separatore`), come nel mockup. Molti
dataset arvestiti lo dichiarano solo nella descrizione ("Il separatore delle
risorse CSV è \";\" ..."): questo module è l'unico punto che conosce la frase e
la forma dell'extra. Lo usano il render, il comando di backfill e il
post-processing dell'harvest.
"""

import re

from . import _common

LABELS = {
    ";": "punto e virgola",
    ",": "virgola",
    "\t": "tabulazione",
    "|": "barra verticale",
}
# Simboli e nomi accettati nell'extra (es. `TAB`, `punto e virgola`).
_ALIASES = {
    ";": ";",
    ",": ",",
    "\t": "\t",
    "|": "|",
    "tab": "\t",
    "tabulazione": "\t",
    "punto e virgola": ";",
    "virgola": ",",
    "barra verticale": "|",
}
_SEPARATOR_PATTERN = (
    r"(?P<sep>[;,\t|]|tab(?:ulazione)?|punto\s+e\s+virgola|virgola|barra\s+verticale)"
)
_NOTE_RE = re.compile(
    r"separatore\s+delle\s+risorse\s+CSV\s+(?:è|e'|&egrave;)\s*"
    r"[\"“”']?\s*(?:(?:il|la|lo)\s+)?" + _SEPARATOR_PATTERN + r"\s*[\"“”']?",
    re.IGNORECASE,
)


def normalize(value):
    """Simbolo canonico del separatore, o '' se non riconosciuto."""
    raw = value or ""
    # `str.strip()` rimuove anche il TAB, che è un separatore valido.
    stripped = raw.strip(" \r\n")
    if not stripped:
        return ""
    if stripped in _ALIASES:
        return _ALIASES[stripped]
    return _ALIASES.get(" ".join(stripped.split()).casefold(), "")


def from_notes(notes):
    """Separatore dichiarato nella descrizione, o ''."""
    match = _NOTE_RE.search(notes or "")
    return normalize(match.group("sep")) if match else ""


def value(pkg):
    """Separatore dichiarato: extra, poi descrizione; '' se non c'è."""
    pkg = pkg or {}
    extra = normalize(_common.pkg_field(pkg, "separatore"))
    if extra:
        return extra
    return from_notes(pkg.get("notes") or pkg.get("description"))


def label(sep):
    """Etichetta italiana del separatore."""
    return LABELS.get(sep, sep)


def ensure_extra(data_dict, create=False):
    """Aggiunge `separatore` agli extras dalla descrizione, se manca.

    `create=True` è il caso di `package_create` (gli extras possono mancare).
    Su `package_update` si tocca solo un dict che ha già `extras`, per non
    sovrascrivere gli altri extra con un update parziale.
    """
    if not isinstance(data_dict, dict):
        return

    sep = from_notes(data_dict.get("notes") or data_dict.get("description"))
    if not sep:
        return

    extras = data_dict.get("extras")
    if isinstance(extras, dict):
        if not normalize(extras.get("separatore")):
            extras["separatore"] = sep
        return
    if isinstance(extras, list):
        for extra in extras:
            if isinstance(extra, dict) and extra.get("key") == "separatore":
                if not normalize(extra.get("value")):
                    extra["value"] = sep
                return
        extras.append({"key": "separatore", "value": sep})
        return
    if create:
        data_dict["extras"] = [{"key": "separatore", "value": sep}]
