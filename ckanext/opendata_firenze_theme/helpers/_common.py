"""Helper condivisi del package: query Solr difensive e utility di base.

Privato. `_search` e' il punto in cui i test sostituiscono le query:
`mock.patch.object(helpers._common, "_search")`.
"""

import logging

import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)


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


def _pkg_extras(pkg):
    """{chiave: valore} degli extras del package (lista o dict)."""
    extras = pkg.get("extras") or []
    if isinstance(extras, dict):
        return extras
    return {e.get("key"): e.get("value") for e in extras if e.get("key")}


def pkg_field(pkg, key, default=None):
    """Valore di un campo/extra del dataset, qualunque sia la forma del dict.

    Il valore può stare in tre posti:
    - in `extras` (lista o dict), per gli extra "liberi" (es. `serie`, `hvd`);
    - **in cima al package**, per i campi dello schema dcatapit che
      `package_show` sposta lì con `convert_from_extras` (es. `is_version_of`);
    - con la chiave rinominata con l'etichetta leggibile: ckanext-dcat, nelle
      viste (`for_view`), rinomina gli extra (es. `theme` -> `Theme`), quindi il
      confronto sugli extras è case-insensitive.

    Inoltre il dict di `package_search` appiattisce gli extra in
    `extras_<chiave>`. Questo è l'unico punto che conosce le tre forme: gli
    helper del tema passano tutti da qui.
    """
    extras = _pkg_extras(pkg)
    if key in extras:
        return extras.get(key, default)
    value = pkg.get(key)
    if value is not None and value != "":
        return value
    target = str(key).lower()
    for name, extra_value in extras.items():
        if str(name).lower() == target:
            return extra_value
    flat = pkg.get(f"extras_{key}")
    if flat is not None and flat != "":
        return flat
    return default


def _truthy(value):
    """Vero solo per i valori booleani espliciti ("true", "1", "sì", …)."""
    return str(value).strip().lower() in ("1", "true", "yes", "si", "sì", "y")


# Valori che significano "assente/negativo" quando il campo è libero (es.
# `spatial` con una WKT o `geometria` con "punto"): tutto il resto è presenza.
_FALSE_TEXT = frozenset(("", "0", "false", "no", "n", "none", "null", "-"))


def _present(value):
    """Vero se il campo è valorizzato con qualcosa che non sia un "no" esplicito.

    Serve ai campi descrittivi (`geometria`, `spatial`, `spatial_geometry`):
    `_truthy` li tratterebbe come falsi perché non sono parole booleane.
    """
    if value is None:
        return False
    return str(value).strip().lower() not in _FALSE_TEXT


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_number": odf_number,
}
