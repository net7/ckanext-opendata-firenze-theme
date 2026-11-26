# 13. Module mappa: una sola regola per formato, vista e target

## Stato

Accettata

## Contesto

La regola "questa risorsa è una mappa" era sparsa in cinque punti:

- `constants.MAP_VIEW_TYPES` era derivato confrontando il titolo di
  `VIEW_TITLES` con la stringa `"Mappa"`: rinominare un'etichetta cambiava in
  silenzio la semantica di mappa di tre consumer;
- `GENERIC_MAP_VIEW_TYPES` era una seconda lista, usata solo dal comando di
  migrazione;
- `odf_format_is_geo` stava in `dataset.py`, `odf_resource_has_map_view` e
  `odf_views_map_first` in `resource.py`, `odf_dataset_map_resource` ancora in
  `dataset.py`;
- `cli.py` conosceva i tipi di vista generici per conto suo;
- l'alias `GJSON` ha richiesto di toccare `constants` e `dataset`.

Il concetto è unico — la capacità mappa di una risorsa e la scelta della
risorsa da mostrare — ma nessun module lo possedeva.

## Decisione

- `helpers/map.py` possiede i predicati di formato (`is_geo_format` /
  `odf_format_is_geo`, l'alias GeoJSON), la capacità mappa di una vista/risorsa
  (`odf_resource_has_map_view`), il target del pulsante “Vedi su mappa”
  (`odf_dataset_map_resource`) e l'ordinamento mappa-prima
  (`odf_views_map_first`).
- `helpers/map.py` possiede anche la classificazione dell'anteprima
  (`preview_kind`, `preview_format_kind`, `preview_reason`) e le costanti
  `TABULAR_FORMATS` / `EXTERNAL_FORMATS`: `helpers/resource.py` delega, così un
  nuovo formato o viewer non può aggiornare la mappa lasciando indietro la
  modale.
- `MAP_VIEW_TYPES` in `constants.py` diventa un elenco esplicito; `VIEW_TITLES`
  resta solo per i titoli dei pannelli.
- `GENERIC_MAP_VIEW_TYPES` si sposta in `map.py`; `cli.py` lo importa da lì.
- `odf_resource_has_map_view` resta implementato in `resource.py` (dove vive
  l'acquisizione `_resource_views`) ed è importato da `map.py`; la direzione a
  livello di module resta `map → resource`. `resource.odf_resource_preview`
  importa localmente i predicati di anteprima da `map` per non creare un ciclo.
- I nomi pubblici (`helpers.odf_format_is_geo`, `odf_dataset_map_resource`,
  `odf_views_map_first`) non cambiano: template e test continuano a usarli.

## Conseguenze

- Cambiare “cosa è una mappa” tocca un module solo; `constants` resta dato.
- Il comando di migrazione e la modale condividono gli stessi predicati.
- `VIEW_TITLES` non è più un input della semantica: una traduzione non può
  rompere la mappa.
- Mappa e anteprima leggono le stesse costanti: un nuovo formato o viewer si
  aggiunge in un punto solo.
- Il module mappa è anche la casa naturale di `odf_wms_layer` (ADR 0018 nel
  repo config), che è arrivato prima dei predicati.

## Verifica

- Test esistenti di formati, badge, “Vedi su mappa”, ordinamento, anteprima e
  migrazione passano senza cambiare i nomi pubblici.
- `helpers.get_helpers()` continua a esporre `odf_format_is_geo` e
  `odf_views_map_first`, ora registrati da `map.HELPERS`.
