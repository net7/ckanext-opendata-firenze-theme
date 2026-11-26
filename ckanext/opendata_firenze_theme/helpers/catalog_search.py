"""Ricerca del catalogo: query esatta di CKAN, poi fallback fuzzy.

Il module possiede la policy (quando il fuzzy è ammesso e quale diagnosi
restituire) e riceve la funzione di ricerca come dipendenza.
`plugin.odf_package_search` resta l'adapter CKAN: decide API o vista e applica
il filtro qualità. Le viste web passano da `_common._search(view=True)`, che
entra nell'azione e quindi in questo module.
"""

from copy import deepcopy

from ckan.logic.action.get import package_search as core_package_search

from . import query


def _fuzzy_data(data_dict, fuzzy):
    """Copia dei parametri con la query fuzzy e eDisMax."""
    fuzzy_data = deepcopy(data_dict)
    fuzzy_data.update({"q": fuzzy, "defType": "edismax", "mm": "1"})
    return fuzzy_data


def catalog_search(context, data_dict, search=core_package_search):
    """`package_search` esatto, con fallback fuzzy solo per le viste.

    Il fuzzy entra in gioco solo se la query esatta non trova nulla e il
    contesto è una vista web (`for_view`): la stessa chiamata resta esatta per
    l'API pubblica. La distanza per termine è quella di `fuzzy.distance_for`
    (1 per 4-5 caratteri, 2 per 6+), quindi copre anche le trasposizioni.
    `search` è iniettabile per i test.
    """
    fuzzy_data = None
    if context.get("for_view") and data_dict.get("q"):
        fuzzy = query.fuzzy_query(data_dict["q"])
        if fuzzy:
            fuzzy_data = _fuzzy_data(data_dict, fuzzy)

    result = search(context, data_dict)
    if not result.get("count") and fuzzy_data:
        fuzzy_result = search(context, fuzzy_data)
        if fuzzy_result.get("count"):
            fuzzy_result["odf_fuzzy"] = True
            result = fuzzy_result
    return result
