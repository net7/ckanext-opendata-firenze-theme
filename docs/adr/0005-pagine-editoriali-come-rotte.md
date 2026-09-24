# 5. Pagine editoriali come rotte del tema (non ckanext-pages)

## Stato

Accettata

## Contesto

Il mapping propone `ckanext-pages` per Annuario Statistico e Sviluppatori & LOD.
Ma le pagine di `ckanext-pages` sono contenuto HTML statico, mentre l'Annuario
deve elencare i **dataset per capitolo** (query sul catalogo) e Sviluppatori
espone **endpoint reali**. Inoltre nel DB dev non esiste alcuna pagina
`ckanext-pages` e i link del tema puntavano a `/pages/...` (404).

## Decisione

- Due rotte del tema via `IBlueprint` (`views.py`): `/annuario-statistico` e
  `/sviluppatori-e-lod`, con template `annuario/index.html` e
  `sviluppatori/index.html`. Niente prefisso `/pages/`, che è il catch-all di
  `ckanext-pages`: le rotte del tema sono statiche e non entrano in conflitto.
- Annuario: SideNav con i 13 capitoli; il capitolo attivo è un parametro
  `?capitolo=` (funziona senza JS). I dataset del capitolo si cercano
  sull'extra custom `capitolo`, che CKAN indicizza come `extras_capitolo`
  (decisione presa: extra custom). Il conteggio usa una query sul valore esatto,
  perché il facet `extras_capitolo` è tokenizzato e non dà il capitolo intero.
- Sviluppatori: tab (API, RDF e LOD, Servizi geografici, MCP Server) con
  endpoint reali; **SPARQL e MCP server non sono nativi** (fuori scope tema,
  come da mapping) e sono resi come nel mockup con link/endpoint segnaposto
  (vedi Aggiornamenti).
- Collaborazione: override di `contact/form.html` di `ckanext-contact` con i 3
  tipi (chiarimenti / segnala un dataset / racconta un riuso), mappati sul campo
  `subject` (unico campo libero del form). Override anche di
  `contact/success.html`.
- Link aggiornati in header, footer, tab bar e scheda dataset alle rotte nominate
  (`h.url_for('odf_pages.annuario')`, `…sviluppatori`).

## Verifica fatta

- `/annuario-statistico`, `/sviluppatori-e-lod` (e `?tab=`), `/contact` → `200`;
  resi verificati a schermo.
- Test: 13 capitoli, tab e endpoint, form con i 3 tipi.

## Conseguenze

- L'Annuario elenca i dataset il cui extra `capitolo` coincide col capitolo
  selezionato (extra custom, decisione presa).
- La conferma privacy è **imposta anche lato server** senza toccare
  `ckanext-contact`: il suo `validate()` richiede non-vuoto ogni campo inviato
  (tranne `subject`), quindi il checkbox del consenso è seguito da un hidden
  omonimo vuoto. Spuntato → arriva `privacy=on`; non spuntato → arriva `""` e il
  server rifiuta l'invio (funziona anche senza JS). L'etichetta "informativa
  privacy" è testo semplice finché la pagina non esiste (nessun link rotto).
- Il campo "tema di riferimento" del mockup è **omesso**: `ckanext-contact`
  valida come obbligatori tutti i campi inviati tranne `subject`, quindi non si
  possono aggiungere campi opzionali senza modificare l'estensione. Dettaglio e
  alternative in [`0006`](0006-campo-tema-collaborazione.md).
- Se in futuro servisse il contenuto editoriale gestibile dall'admin, si potrà
  spostare la sola parte statica su `ckanext-pages` e lasciare la parte
  dinamica su queste rotte.

## Aggiornamenti

- **Sviluppatori**: aggiunti il tab **MCP Server**, la riga `sparql` e il
  pannello "Come interrogare i Linked Open Data" nella tabella RDF, i link
  LodView/LodLive per dataset e il pannello "Dataset con estensione spaziale",
  per allinearsi al mockup. MCP, endpoint SPARQL e link LodView/LodLive non sono
  servizi attivi: i link restano segnaposto (`#`) e il pannello geo usa i
  dataset reali con formati geografici (`odf_geo_datasets`).
