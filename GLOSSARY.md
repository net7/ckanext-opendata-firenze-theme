# Glossario

Termini del dominio del tema, come li usano codice, template e documentazione.
Niente dettagli implementativi: per le decisioni tecniche valgono gli ADR in
`docs/adr/`.

**Dataset** — una voce del catalogo CKAN (`package`), con una o più risorse.
Nel codice è il dict che arriva dai template: la sua forma cambia fra
`package_show`, `package_search` e l'indicizzazione (vedi ADR 0009).

**Scheda** — la pagina di un dataset (`templates/package/read.html`), distinta
dal catalogo e dalla scheda risorsa. Il contesto è diviso in `header`,
`resources`, `aside` e `series`.

**Caratteristiche** — la faccetta che classifica un dataset come Geodati,
Alfanumerici, High Value Dataset o Linked Open Data. Nel codice è il campo Solr
`odf_features`.

**Geodato** — dataset con contenuto geografico: una geometria o un'estensione
spaziale dichiarata, oppure almeno una risorsa in un formato con anteprima su
mappa. Regola unica in `odf_dataset_facts` (ADR 0009).

**Vista mappa** — vista risorsa che rappresenta una mappa (`geo_view`,
`geojson_view`, `wmts_view`, `shp_view`, `recline_map_view`). Alimenta il
pulsante “Vedi su mappa”, il titolo “Mappa” dei pannelli e l'ordinamento
mappa-prima.

**Layer WMS** — nome del layer che una risorsa WMS mostra. Si legge dal
fragment `#layer` dell'URL, altrimenti dalla descrizione legacy
(“Il Layer di riferimento è ...”), e il tema lo passa già risolto al viewer
(`odf_wms_layer`, ADR 0018 nel repo config).

**Viewer dedicato / generico** — `geojson_view` è il viewer dedicato ai
GeoJSON (con supporto CRS); `geo_view`, `geoview` e `recline_map_view` sono i
viewer generici, che non vanno mostrati quando il dedicato è presente sulla
stessa risorsa.

**Serie** — insieme di dataset collegati da un indicatore comune, dichiarato
dall'extra `serie`. Scelta provvisoria in attesa di DP07 (ADR 0012 nel repo
`opendata-firenze-config`). Nel catalogo è la faccetta “Serie” (campo
`odf_series`).

**Revisione temporale** — edizione precedente di un dataset, collegata al
dataset corrente con `dct:isVersionOf` (`is_version_of`). Le revisioni non
compaiono in catalogo e si raggiungono dal pannello della scheda.

**Panel** — riquadro della scheda dataset (metadati, serie/revisioni, risorse,
API). Il pannello serie/revisioni riceve un contesto già risolto e si limita a
renderizzarlo.

**Blocco della home** — sezione configurabile della homepage (hero, KPI, in
evidenza, temi, LOD, più consultati, news), con id, ordine, stato, testi e
builder dei dati nel registro `home_blocks.BLOCKS` (ADR 0008/0010).

**Ricerca del catalogo** — la policy di ricerca dei dataset: query esatta di
CKAN e, solo per le viste web, fallback fuzzy. Vive in
`helpers/catalog_search.py`; `plugin.odf_package_search` è l'adapter CKAN e
l'API pubblica resta esatta (ADR 0014).

**Ricerca site-wide** — la pagina `/search` e il valore `{q, groups}` che
aggrega dataset (evidenze), news e pagine; gli enti restano nel catalogo.
Ogni gruppo ha la stessa forma e il template si limita a iterarlo
(ADR 0014).

**Fatti del dataset** — il dict con formati, tema, geometria e flag
(geo/LOD/HVD/realtime/serie) calcolato da `odf_dataset_facts`.
`odf_dataset_views` lo calcola una volta per una lista e le card lo ricevono
già pronto (`facts`) invece di ricalcolarlo per ogni predicato.

**Fuzzy** — fallback di ricerca per i refusi: la query esatta resta la prima;
se è vuota, i termini di 4-5 caratteri tollerano una modifica e quelli di 6+
due (Damerau-Levenshtein). L'apostrofo separa i termini come nel tokenizer.
La policy vive in `helpers/fuzzy.py` ed è usata da `query.fuzzy_query` per
Solr e da `content.matches` per news e pagine (ADR 0014).

**Contenuto editoriale** — news e pagine gestite da `ckanext-pages`. Vivono
dietro `ContentSource` in `helpers/content.py`: l'adapter di produzione usa il
plugin, quello dei test è in-memory.

**Qualità interna** — punteggio QA del metadato e regola di visibilità
(sysadmin o editor dell'organizzazione). Vive in `helpers/quality.py` e il
plugin la usa come adapter CKAN.
