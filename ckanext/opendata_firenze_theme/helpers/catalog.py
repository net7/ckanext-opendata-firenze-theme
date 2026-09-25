"""Helper del catalogo: tema DCAT-AP_IT di un package e faccette."""

import json
from urllib.parse import urlencode

import ckan.lib.helpers as ckan_h
import ckan.plugins.toolkit as toolkit

from .constants import FACET_ORDER, THEME_CODES


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
