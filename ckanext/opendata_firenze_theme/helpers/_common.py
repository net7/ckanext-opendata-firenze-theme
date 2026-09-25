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


def _truthy(value):
    return str(value).strip().lower() in ("1", "true", "yes", "si", "sì", "y")


def _resource_download_url(pkg, res):
    """URL di download di una risorsa (route CKAN per gli upload)."""
    if res.get("url_type") == "upload":
        try:
            return toolkit.url_for("resource.download", id=pkg.get("name"), resource_id=res.get("id"))
        except Exception:
            return res.get("url") or ""
    return res.get("url") or ""
