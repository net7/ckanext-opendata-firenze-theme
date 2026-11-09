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
THEME = "dcat_theme"
THEME_ALT = "theme"
RES_FORMAT = "res_format"

# Valori del campo `odf_features` (vedi `helpers.dataset.odf_index_features`).
GEO = "geo"
ALPHANUMERIC = "alfanumerico"
LOD = "lod"
HVD = "hvd"

# Faccetta dopo cui il tema inserisce i propri gruppi (mockup).
FACET_ANCHOR = "organization"

# Una sola tabella del vocabolario: campo, etichetta, ordine e (solo per le
# faccette aggiunte dal tema) la faccetta dopo cui inserirla. Le mappe derivate
# (`FACET_ORDER`, `FACET_LABELS`, `EXTRA_FACETS`) non vanno più mantenute a mano.
FACET_TABLE = (
    {"name": THEME, "label": "Temi", "order": 0},
    {"name": THEME_ALT, "label": "Temi", "order": 1},
    {"name": RES_FORMAT, "label": "Formato dei file", "order": 2},
    {"name": "frequency", "label": "Aggiornamento", "order": 3},
    {"name": FACET_ANCHOR, "label": "Chi pubblica", "order": 4},
    {"name": FEATURES, "label": "Caratteristiche", "order": 5, "insert_after": FACET_ANCHOR},
    {"name": SERIES, "label": "Serie", "order": 6, "insert_after": FACET_ANCHOR},
    {"name": "spatial", "label": "Classificazione geografica", "order": 7},
    {"name": "groups", "label": "Gruppi", "order": 8},
    {"name": "tags", "label": "Parole chiave", "order": 9},
    {"name": "license_id", "label": "Licenza", "order": 10},
)

# Valori della faccetta "Caratteristiche" e loro etichetta.
FEATURE_VALUES = (
    (GEO, "Geodati"),
    (ALPHANUMERIC, "Alfanumerici"),
    (HVD, "High Value Dataset"),
    (LOD, "Linked Open Data"),
)

FACET_ORDER = tuple(facet["name"] for facet in sorted(FACET_TABLE, key=lambda item: item["order"]))
FACET_LABELS = {facet["name"]: facet["label"] for facet in FACET_TABLE}
EXTRA_FACETS = tuple(
    (facet["name"], facet["label"]) for facet in FACET_TABLE if "insert_after" in facet
)


def features(value):
    """Query sul campo delle "Caratteristiche" (`odf_features`)."""
    return f"{FEATURES}:{value}"


def theme(value):
    """Query sul tema DCAT-AP_IT (`dcat_theme`)."""
    return f"{THEME}:{value}"


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


def feature_labels():
    """Etichette dei valori di `odf_features` ("Caratteristiche")."""
    return {value: toolkit._(label) for value, label in FEATURE_VALUES}


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
