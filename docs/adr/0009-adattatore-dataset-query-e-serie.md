# 9. Adattatore del dataset, query di catalogo e contesto serie

## Stato

Accettata

## Contesto

Tre regole del tema erano sparse fra moduli e superfici diverse:

- **Forma del package**: lo stesso campo arrivava da `extras` (lista o dict), in
  cima al package (campi dcatapit spostati da `convert_from_extras`), come
  `extras_<chiave>` (risultati di `package_search`) o con la chiave rinominata
  da ckanext-dcat (`theme` → `Theme`). Ogni helper ne conosceva un sottoinsieme,
  con precedenze diverse.
- **“Geodato”**: badge, faccetta “Caratteristiche”, KPI della home, lista
  geodati e chip della card rispondevano con quattro regole diverse. Ne
  derivavano divergenze reali: `spatial="false"` contava come geo solo nel
  badge, un `spatial` con WKT non contava nella faccetta, `hvd` in
  `extras_hvd` sfuggiva al badge.
- **Policy di catalogo**: i nomi dei campi Solr e la regola “le revisioni
  temporali non compaiono in catalogo” stavano in `plugin.py`, `dataset.py`,
  `home.py` ed `editorial.py` come stringhe letterali; il bypass del filtro
  dipendeva dal testo che un helper scriveva nella query.

In più, il pannello serie/revisioni della scheda acquisiva i dati mentre
renderizzava, e la stessa raccolta di membri era scritta in tre punti.

## Decisione

1. **Un solo adattatore della forma del package**: `helpers/_common.pkg_field`
   conosce le quattro forme e la precedenza (extras esatti → cima del package →
   extras case-insensitive → `extras_<chiave>`). `odf_pkg_extra` resta come
   nome pubblico per i template e delega.
2. **Un solo insieme di fatti derivati**: `helpers/dataset.odf_dataset_facts`
   calcola formati, tema, geometria e i flag geo/LOD/HVD/realtime/serie nello
   stesso punto. Badge, faccetta, card e campi indicizzati leggono quei fatti;
   `odf_index_features` non ha più una regola propria.
3. **Una sola definizione di geodato**: `geometria`/`spatial`/
   `spatial_geometry` valorizzati (una WKT conta come valore) oppure almeno una
   risorsa in un formato con anteprima su mappa. `spatial="false"` non conta.
   Home, catalogo e schede usano il campo indicizzato `odf_features:geo`, che è
   il risultato della regola stessa.
4. **Un modulo per le query**: `helpers/query.py` possiede i nomi dei campi
   (`odf_features`, `odf_series`, `extras_is_version_of`, `extras_serie`,
   `extras_capitolo`, `dcat_theme`), le query per intento
   (`features`, `series_member`, `revision`, `chapter`, …), la policy
   `hide_revisions` e le faccette aggiunte dal tema con le loro etichette.
   `plugin.py` resta un adattatore CKAN e delega.
5. **Un contesto per serie e revisioni**: `odf_series_context(pkg, info=None)`
   risolve una volta sola `{kind, label, total, entries, serie, serie_total}`.
   Il pannello `series_panel(context)` rende soltanto; la scheda non chiama più
   due acquisizioni separate e può passare l'`odf_series_info` già letto per il
   badge, così la serie non viene cercata due volte. Il ramo “Revisioni
   temporali” ha la precedenza, come nel mockup; `serie`/`serie_total` restano
   disponibili per il badge della testata e la tabella metadati.

Le query Solr prodotte restano identiche a prima: cambia il posto in cui sono
scritte, non il testo.

## Conseguenze

- Aggiungere un helper costa la voce in `HELPERS` del modulo d'area e l'import
  in `helpers/__init__.py`; `get_helpers()` e `__all__` sono derivati. La lista
  esplicita in `tests/test_plugin.py` resta come guardia contro le rimozioni
  silenziose.
- Cambiare la definizione di geodato tocca un punto solo, ma **richiede
  `search-index rebuild`**: dopo il deploy KPI, lista e link “Filtra il catalogo
  per geodati” leggono `odf_features`. Finché l'indice non è ricostruito
  mostrano 0, mentre le schede calcolano il badge dal vivo. La procedura è in
  `docs/release.md`.
- `odf_dataset_formats` deduplica case-insensitive ma conserva la forma scritta
  (“GeoJSON”): i chip tornano quelli del mockup.
- Il pannello serie/revisioni è testabile senza fingere Solr: i test gli
  passano un contesto, mentre i test del resolver coprono le query.
- `odf_series_info`, `odf_dataset_series` e `odf_dataset_revisions` restano
  disponibili come API Python (e helper) ma non sono più il percorso della
  scheda.

## Alternative scartate

- **Tenere le quattro definizioni e documentarle**: lasciava divergenze visibili
  fra faccetta e badge sullo stesso dataset.
- **Un `DatasetView` con proprietà per ogni campo**: interfaccia più larga del
  necessario; un dict di fatti + l'adattatore bastano.
- **Fallback a `res_format` quando `odf_features` è vuoto**: due definizioni
  attive insieme e un ramo da rimuovere; si preferisce la procedura di rebuild.
- **Pannello che acquisisce i dati**: impediva di testarlo senza sostituire la
  ricerca Solr e duplicava la raccolta dei membri.
