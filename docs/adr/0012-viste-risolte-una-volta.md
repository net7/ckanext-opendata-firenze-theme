# 12. Viste risorsa risolte una volta per scheda

## Stato

Accettata

## Contesto

La scheda dataset compone i dati in `odf_dataset_page`, ma le righe risorsa
restavano fuori dal collector: `resource_row.html` chiama
`h.odf_resource_preview`, che a sua volta acquisisce `resource_view_list`
dalla propria implementazione. Il pulsante "Vedi su mappa" fa lo stesso per
ogni risorsa geo (`odf_resource_has_map_view`). Su una scheda con N risorse e
G geodati si arriva a N + G chiamate all'action, anche per la stessa risorsa;
i test devono fingere l'action CKAN.

La scheda risorsa invece passa già le viste che ha in mano
(`resource_read.html` → `h.odf_resource_views(res, resource_views)`): il
contratto esiste, manca solo alla scheda dataset.

## Decisione

- `helpers/resource.odf_resource_views_by_id(pkg)` acquisisce le viste di ogni
  risorsa una volta sola.
- `odf_dataset_page` mette lo snapshot in `resources.views_by_resource` e lo passa a
  `odf_dataset_map_resource`; `resource_row(pkg, res, views=None)` lo passa a
  `odf_resource_preview`.
- Sulla tab avanzata le righe risorsa non sono renderizzate: il pulsante mappa
  usa il percorso senza snapshot (risolve le viste dei soli geodati), così non
  si paga una `resource_view_list` per ogni risorsa non geo.
- `odf_resource_has_map_view(res, views=None)` e `odf_resource_preview` (che
  già lo faceva) accettano le viste risolte; senza argomento mantengono il
  comportamento precedente, per i call site e i test esistenti.
- Il probe `datastore_info` resta dentro `odf_resource_views`: serve solo per
  le tabelle con `datastore_active=False` e non è una seconda acquisizione
  delle viste.

## Conseguenze

- Le chiamate `resource_view_list` scendono da N + G a N; la stessa risorsa
  non viene più interrogata due volte.
- I test del collector e del pulsante mappa passano le viste come argomento,
  senza sostituire `toolkit.get_action`.
- `resource_row` resta usabile con due argomenti (default `views=None`), così
  snippet e test esistenti non cambiano.
- Il collector resta l'unico punto di composizione della scheda: aggiungere un
  consumer che ha bisogno delle viste costa una voce nel contesto, non una
  nuova acquisizione.

## Verifica

- `odf_resource_views_by_id` con due risorse: due chiamate, non quattro.
- `odf_dataset_map_resource(pkg, snapshot)` sceglie il target senza action.
- `odf_dataset_page` passa lo stesso snapshot a righe e pulsante mappa.
