# 14. Ricerca fuzzy del catalogo e ricerca site-wide nell'header

## Stato

Accettata.

## Contesto

La ricerca del catalogo è quella di CKAN (`package_search` su Solr): una
query con un refuso restituisce zero risultati. Inoltre il campo di ricerca
nell'header dichiarava “Cerca nel sito” ma puntava a `/dataset`, quindi
cercava solo i dataset e non news o pagine.

## Decisione

1. **Fuzzy solo come fallback, con distanza AUTO**: `helpers/catalog_search.py`
   esegue prima la query esatta di CKAN; solo se il conteggio è zero e la
   query è semplice (nessun operatore/campo/frase Solr) riprova con eDisMax e
   `mm=1`. La distanza è quella di `helpers/fuzzy.py`: 1 per i termini di 4-5
   caratteri, 2 per quelli di 6+, come il criterio `AUTO` dei motori di
   ricerca. Così le trasposizioni comuni (`ambinete` → `ambiente`,
   `Farenze` → `Firenze`) trovano risultati senza un secondo tentativo
   separato. L'apostrofo separa i termini come nel tokenizer
   (`dell'arie` → `dell`, `arie`), così anche le query italiane con apostrofo
   ricevono il fallback. Il testo della query fuzzy sta in `helpers/query.py`;
   `plugin.odf_package_search` resta l'adapter CKAN e applica il filtro
   qualità. Ranking e risultati normali restano quelli di CKAN; query avanzate
   non vengono riscritte. Il fallback vale solo per le viste
   (`context["for_view"]`, impostato dal catalogo e da `/search`): l'API
   pubblica `package_search` mantiene la semantica esatta. `/search` usa
   `_common._search(view=True)`, l'unico adapter difensivo a
   `package_search`; il catalogo entra nell'azione con `for_view`.
2. **Ricerca site-wide**: la rotta `/search` (endpoint
   `odf_pages.site_search`) restituisce un valore unico `{q, groups}`; la
   view lo passa al template come `results` e il template itera i gruppi.
   I gruppi aggregano:
   - dataset, via `_common._search(view=True)` (con il fallback fuzzy);
   - news e pagine, via `helpers/editorial` (unico adapter a
     `ckanext-pages`), filtrate per titolo/contenuto con la stessa policy
     fuzzy per parola (`helpers.fuzzy.within_distance`).
   I dataset restano nella site-wide perché sono la parte “evidenze” (oltre
   al catalogo, che ha la sua ricerca dedicata); gli enti no: restano nel
   catalogo (faccetta “Chi pubblica”) e nelle card dei dataset.
   Il form dell’header (desktop e mobile) punta a `/search`; i form della
   home e del catalogo restano su `/dataset`, perché lì la ricerca è
   esplicitamente sul catalogo.
3. **Nessun nuovo indice**: news e pagine sono pochi record e vengono
   filtrate in memoria; non si aggiungono campi Solr o dipendenze.

## Conseguenze

- Un refuso comune (“ambinete”, “tramviar”) produce risultati simili invece
  del vuoto; la pagina `/search` lo segnala.
- La ricerca dell’header è coerente con la sua etichetta “Cerca nel sito”:
  dataset (evidenze), news e pagine; gli enti restano nel catalogo.
- Limiti noti: il fuzzy è un fallback, non una correzione ortografica
  completa; i termini sotto i 4 caratteri restano esatti. News e pagine usano
  la stessa distanza per parola del catalogo.
