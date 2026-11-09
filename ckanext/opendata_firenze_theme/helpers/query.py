"""Campi Solr e query per intento, più la policy di visibilità del catalogo.

Unico proprietario dei nomi dei campi indicizzati dal tema e del testo delle
query che li usano. `plugin.py` resta un adattatore CKAN (hook) e delega qui:
la regola "le revisioni temporali non compaiono in catalogo" e le faccette
aggiunte dal tema non vivono più sparse fra plugin, helper e template.
"""

import ckan.plugins.toolkit as toolkit

# Campi indicizzati dal tema (creati da `08_solr_dcatapit_fields.sh`) e campi
# CKAN/dcatapit usati dalle query.
FEATURES = "odf_features"
SERIES = "odf_series"
REVISION = "extras_is_version_of"
SERIES_EXTRA = "extras_serie"
CHAPTER = "extras_capitolo"
HVD_EXTRA = "extras_hvd"
THEME = "dcat_theme"
THEME_ALT = "theme"
RES_FORMAT = "res_format"

# Valori del campo `odf_features` (vedi `helpers.dataset.odf_index_features`).
GEO = "geo"
ALPHANUMERIC = "alfanumerico"
LOD = "lod"
HVD = "hvd"

# Faccette aggiunte dal tema e faccetta dopo cui inserirle (mockup).
EXTRA_FACETS = ((FEATURES, "Caratteristiche"), (SERIES, "Serie"))
FACET_ANCHOR = "organization"

# Etichette dei gruppi faccetta (nome parametro -> etichetta italiana).
FACET_LABELS = {
    THEME: "Temi",
    THEME_ALT: "Temi",
    RES_FORMAT: "Formato dei file",
    "frequency": "Aggiornamento",
    FACET_ANCHOR: "Chi pubblica",
    "spatial": "Classificazione geografica",
    "groups": "Gruppi",
    "tags": "Parole chiave",
    "license_id": "Licenza",
    FEATURES: "Caratteristiche",
    SERIES: "Serie",
}


def features(value):
    """Query sul campo delle "Caratteristiche" (`odf_features`)."""
    return f"{FEATURES}:{value}"


def series_member(serie):
    """Dataset che dichiarano la stessa serie (extra `serie`)."""
    return f'{SERIES_EXTRA}:"{serie}"'


def series_any():
    """Dataset con l'extra `serie` valorizzato."""
    return f"{SERIES_EXTRA}:[* TO *]"


def revision(uri):
    """Revisioni che puntano a `uri` con `dct:isVersionOf`."""
    return f'{REVISION}:"{uri}"'


def chapter(name):
    """Dataset dell'Annuario del capitolo indicato (valore esatto)."""
    return f'{CHAPTER}:"{name}"'


def chapter_any():
    """Dataset con un capitolo dell'Annuario dichiarato."""
    return f"{CHAPTER}:[* TO *]"


def hide_revisions(search_params):
    """Nasconde dal catalogo le revisioni temporali (dataset con `is_version_of`).

    Convenzione: il dataset **corrente** non ha `is_version_of` ed è l'unico
    visibile in catalogo; le revisioni precedenti lo puntano e qui vengono
    escluse. Restano raggiungibili dal pannello "Revisioni temporali", che
    cerca esplicitamente il campo: in quel caso il filtro non si applica.
    """
    haystack = " ".join(str(search_params.get(key) or "") for key in ("q", "fq"))
    if REVISION in haystack:
        return search_params
    fq = search_params.get("fq") or ""
    if isinstance(fq, list):
        fq = " ".join(str(part) for part in fq)
    search_params["fq"] = (fq + f" -{REVISION}:[* TO *]").strip()
    return search_params


def facet_labels():
    """Etichette dei gruppi faccetta già tradotte."""
    return {name: toolkit._(label) for name, label in FACET_LABELS.items()}


def dataset_facets(facets_dict):
    """Faccette del catalogo con i gruppi del tema dopo "Chi pubblica".

    `odf_features` ("Caratteristiche") e `odf_series` ("Serie") sono aggiunti
    anche se la faccetta di ancoraggio non c'è: il catalogo deve mostrarli
    comunque.
    """
    facets = type(facets_dict)()
    for key, value in facets_dict.items():
        facets[key] = value
        if key == FACET_ANCHOR:
            for field, label in EXTRA_FACETS:
                facets[field] = toolkit._(label)
    for field, label in EXTRA_FACETS:
        facets.setdefault(field, toolkit._(label))
    return facets
