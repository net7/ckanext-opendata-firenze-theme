# 10. Dati della home raccolti da un collettore

## Stato

Accettata

## Contesto

`templates/home/index.html` includeva i blocchi configurati (ADR 0008) e ogni
template si cercava i dati da solo: il blocco chiamava un helper, lo snippet
incluso ne chiamava un altro. Ne seguivano tre problemi:

- **acquisizione sparsa**: per sapere quali dati vede un blocco bisognava
  leggere template + snippet + helper;
- **query duplicate**: hero e KPI contavano lo stesso catalogo con due
  `package_search` identiche; i limiti (7, 6, 4, 3) erano nel template, non nel
  registro;
- **test**: la home si verificava sostituendo `_search` e leggendo l'HTML, senza
  un punto unico in cui controllare i dati dei blocchi.

## Decisione

1. **Un collettore per render**: `helpers/home_sections.odf_home_sections(blocks)`
   riceve i blocchi attivi (nell'ordine configurato) e ritorna
   `{id_blocco: dati}`. `home/index.html` lo chiama una volta e include ogni
   blocco con `block_data`.
2. **Blocchi renderer**: i template dei blocchi non chiamano più `h.odf_*`;
   leggono `block_data`. Lo snippet della hero riceve `count`, quello dei KPI
   `kpis`, quello dei temi `themes`; i caroselli ricevono le liste di dataset.
3. **Limiti nel collettore**: 7 in evidenza, 6 ultimi, 6 LOD, 4 più consultati,
   3 news. Il registro dei blocchi (ordine, stato, testi) resta in
   `home_blocks.BLOCKS` e la configurazione resta quella di ADR 0008.
4. **Conteggio condiviso**: il totale del catalogo è calcolato al massimo una
   volta per render e passato a hero e KPI (`odf_home_kpis(total=…)`).
5. **Copertura obbligatoria**: un test verifica che ogni id di `BLOCKS` abbia un
   builder; un blocco nuovo senza dati fa fallire la suite invece di rompere la
   home.

## Conseguenze

- Aggiungere un blocco richiede: voce in `BLOCKS`, template e builder in
  `home_sections._BUILDERS` (e il test lo impone).
- Le query della home scendono di una (hero + KPI condividono il totale); le
  altre restano, perché i conteggi di capitoli e serie sono `[* TO *]` su campi
  tokenizzati e non si possono ricavare da una faccetta.
- I test possono verificare i dati con una sola funzione
  (`odf_home_sections`) invece di sostituire `_search` per ogni blocco.
- L'ordine, i testi e l'attivazione dei blocchi non cambiano: la home
  configurata resta identica (verificato su dev: stesse card per sezione, stessi
  KPI).

## Alternative scartate

- **Solo cache per-richiesta su `_search`**: le query duplicate erano una, e la
  cache non avrebbe dato un'interfaccia unica ai blocchi.
- **Una query con più faccette per i quattro KPI**: non è corretta per
  `extras_capitolo` e `extras_serie`, che sono campi tokenizzati: la faccetta
  conta i termini, non i dataset con il campo valorizzato.
- **Dati calcolati dentro i template**: è lo stato di partenza, con i problemi
  elencati sopra.
