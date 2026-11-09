# Glossario

Termini del dominio del tema, come li usano codice, template e documentazione.
Niente dettagli implementativi: per le decisioni tecniche valgono gli ADR in
`docs/adr/`.

**Dataset** — una voce del catalogo CKAN (`package`), con una o più risorse.
Nel codice è il dict che arriva dai template: la sua forma cambia fra
`package_show`, `package_search` e l'indicizzazione (vedi ADR 0009).

**Scheda** — la pagina di un dataset (`templates/package/read.html`), distinta
dal catalogo e dalla scheda risorsa.

**Caratteristiche** — la faccetta che classifica un dataset come Geodati,
Alfanumerici, High Value Dataset o Linked Open Data. Nel codice è il campo Solr
`odf_features`.

**Geodato** — dataset con contenuto geografico: una geometria o un'estensione
spaziale dichiarata, oppure almeno una risorsa in un formato con anteprima su
mappa. Regola unica in `odf_dataset_facts` (ADR 0009).

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
evidenza, temi, LOD, più consultati, news), con id, ordine, stato e testi
salvati in `system_info` (ADR 0008).
