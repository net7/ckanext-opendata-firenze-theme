# 4. Scheda risorsa: tutte le viste come pannelli

## Stato

Accettata

## Contesto

Il mockup della scheda risorsa (step 7) mostra, in un'unica colonna, un
pannello "Anteprima dei dati" (tabella) e, per i dati geografici, un pannello
"Mappa". Il core CKAN invece rende **una sola** vista selezionata
(`current_resource_view`) con una nav a tab per cambiarla
(`resource_views_list`), più la tabella "Additional Information" e la sidebar
con le altre risorse del dataset.

## Decisione

- `package/resource_read.html` (override) rende **tutte** le viste della
  risorsa, un pannello per vista, titolato per tipo (`Mappa`,
  `Anteprima dei dati`, `Grafico`, altrimenti il titolo della vista). Le viste
  iframed → `<iframe>` (con `title`), le inline →
  `h.rendered_resource_view`; stessa logica del core.
- Titoli duplicati disambiguati col titolo della vista (`Mappa`,
  `Mappa · GeoJSON`).
- Ripristino delle affordance editoriali nella testata: "Gestisci"
  (`_resource.edit`) e "Viste" (`_resource.views`) con `package_update`.
- La tabella "Additional Information" del core è sostituita da un pannello
  **"Dettagli della risorsa"** (formato, dimensione, date, licenza, URL); le
  altre risorse restano raggiungibili dalla scheda del dataset (nota in fondo).

## Verifica fatta

- Pagina risorsa `200`; verificata su `https://opendata-firenze.test` (gli
  iframe usano URL `qualified` = `site_url`): la vista `datatables_view` rende
  la tabella, `geojson_view` la mappa Leaflet.
- Test: rendering senza viste, con vista inline (`image_view`), helper dei
  titoli.

## Conseguenze

- Una risorsa con molte viste le mostra tutte (pagina più pesante) e non si
  può più deep-linkare una vista specifica via `view_id`: se servisse, andrà
  reintrodotta la nav a tab.
- "Additional Information" non è più la tabella del core: eventuali campi
  extra del core non sono mostrati.
