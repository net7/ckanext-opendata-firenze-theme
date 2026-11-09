"""Costanti del tema: temi DCAT-AP_IT, formati geo, capitoli Annuario, viste."""

from . import query

# 13 temi DCAT-AP_IT: (codice EU, label italiana). Stessa fonte di
# templates/snippets/opendata_firenze_theme/tema-overline.html.
THEMES = (
    ("AGRI", "Agricoltura, pesca, silvicoltura e prodotti alimentari"),
    ("ECON", "Economia e finanze"),
    ("EDUC", "Istruzione, cultura e sport"),
    ("ENER", "Energia"),
    ("ENVI", "Ambiente"),
    ("GOVE", "Governo e settore pubblico"),
    ("HEAL", "Salute"),
    ("INTR", "Tematiche internazionali"),
    ("JUST", "Giustizia, sistema giuridico e sicurezza pubblica"),
    ("REGI", "Regioni e città"),
    ("SOCI", "Popolazione e società"),
    ("TECH", "Scienza e tecnologia"),
    ("TRAN", "Trasporti"),
)


# Formati con anteprima su mappa (per il chip "geo").
GEO_FORMATS = frozenset(("GeoJSON", "SHP", "KML", "WMS", "WFS"))
# Serializzazioni RDF: un dataset con almeno una risorsa di questo tipo è
# "Linked Open Data" (badge e filtro "Caratteristiche", come nel mockup).
LOD_FORMATS = frozenset(("RDF", "RDF/XML", "TTL", "N3"))


GEO_FORMATS_UPPER = frozenset(fmt.upper() for fmt in GEO_FORMATS)
LOD_FORMATS_UPPER = frozenset(fmt.upper() for fmt in LOD_FORMATS)


THEME_CODES = frozenset(code for code, _ in THEMES)


# Tipi di geometria riconosciuti (extra `geometria`).
GEOMETRY_SHAPES = ("punto", "area", "linea")


# Ordine di visualizzazione dei gruppi faccetta come il mockup (Temi per primo,
# poi Formato, Aggiornamento, Chi pubblica, Caratteristiche e infine le faccette
# geografiche/classificazioni e le altre). "Tipo di geometria" (2° nel mockup)
# non ha un campo Solr dedicato senza ckanext-scheming: resta non implementato.
FACET_ORDER = (
    query.THEME_ALT,
    query.THEME,
    query.RES_FORMAT,
    "frequency",
    query.FACET_ANCHOR,
    query.FEATURES,
    query.SERIES,
    "spatial",
    "groups",
    "tags",
    "license_id",
)


# 13 capitoli dell'Annuario Statistico (dal mockup). Il campo `capitolo` non è
# nativo: è un extra custom, che CKAN indicizza in Solr come `extras_capitolo`
# (decisione aperta, vedi docs/adr/0005). Senza l'extra i capitoli sono vuoti.
ANNUARIO_CHAPTERS = (
    "Ambiente e territorio",
    "Popolazione",
    "Sanità",
    "Sicurezza sociale",
    "Istruzione e cultura",
    "Giustizia",
    "Economia e lavoro",
    "Prezzi",
    "Trasporti",
    "Amministrazione comunale",
    "Quartieri",
    "Spettacolo e sport",
    "Le donne a Firenze",
)


# Titoli dei pannelli della scheda risorsa, per tipo di vista CKAN.
VIEW_TITLES = {
    "datatables_view": "Anteprima dei dati",
    "datastore": "Anteprima dei dati",
    "recline_grid_view": "Anteprima dei dati",
    "recline_graph_view": "Grafico",
    "recline_map_view": "Mappa",
    "geoview": "Mappa",
    "geo_view": "Mappa",
    "geojson_view": "Mappa",
    "wmts_view": "Mappa",
    "shp_view": "Mappa",
    "image_view": "Anteprima",
    "text_view": "Anteprima",
    "pdf_view": "Anteprima",
    "officedocs_view": "Anteprima",
    "html_view": "Anteprima",
    "web_view": "Anteprima",
}
