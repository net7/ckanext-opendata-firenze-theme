# 16. Nomi degli enti senza il prefisso "Comune di Firenze - "

## Stato

Accettata

## Contesto

I metadati arvestiti scrivono il nome dell'unità organizzativa come
`Comune di Firenze - Direzione Cultura`. Nel catalogo RDF di origine il
`dct:rightsHolder` è proprio l'organizzazione "Comune di Firenze - Direzione
…", che `ckanext-dcatapit` porta in `holder_name`. Il valore alimenta la card
**"Chi pubblica" → Titolare** e la riga "Titolare del dato" per i dataset non
locali; per quelli locali (owner org = Comune) dcatapit lo sostituisce con il
titolo dell'organizzazione, quindi la card continua a mostrare "Comune di
Firenze".

Nel DB di sviluppo il prefisso è presente in (1.998 dataset attivi):

- `author` e extra `creator`: 939 dataset;
- `maintainer`: 840;
- extra `publisher` / `publisher_name`: 787.

Il portale è del Comune, quindi il prefisso è ridondante quando il valore
nomina già una direzione/ufficio. Lo stesso testo compare nelle descrizioni
come attribuzione: `Fonte: Comune di Firenze - Direzione Cultura`,
`Elaborazioni del Comune di Firenze - Ufficio di Statistica`. Non compare in
nessun titolo.

L'harvest riscrive periodicamente questi campi, quindi la pulizia non può
essere un intervento manuale una tantum.

## Decisione

- `helpers/agents.py` possiede il prefisso, i campi e le regole sulle
  descrizioni.
- Si normalizzano solo i campi che contengono un ente (`author`, `maintainer`,
  `holder_name`, `publisher_name`, `creator`, `publisher`); **i titoli non si
  toccano**. Restano invariati il valore semplice `Comune di Firenze`, i
  publisher terzi e gli identificatori IPA (`c_d612`).
- Nelle descrizioni si riscrive solo l'attribuzione nota (`Fonte:`, `del`,
  `nel` seguiti da `Direzione`/`Ufficio`/`Anagrafe`/`Comparto`); `Asse V
  PIUSS` resta intatto perché non è un ente.
- `publisher_name` diventa il nome reale della direzione (es. "Direzione
  Sistemi Informativi"); l'ente resta identificabile da
  `publisher_identifier`.
- `package_create` e `package_update` sono chained action del tema: prima del
  salvataggio normalizzano il dict. È il post-processing dell'harvest, senza
  un secondo `package_update`.
- `ckan odf-normalize-agents` fa il backfill dei dataset già in catalogo, con
  dry-run di default, `--apply`, `--dataset` e `--limit`.

## Conseguenze

- L'export DCAT/API mostra "Direzione …" anche quando il dataset viene
  ri-arvestito. Per i dataset locali la card "Chi pubblica" e la riga "Titolare
  del dato" continuano invece a mostrare il titolo dell'organizzazione
  (comportamento di `ckanext-dcatapit`, non del tema).
- La normalizzazione è idempotente: un valore già pulito non cambia.
- Le descrizioni perdono il prefisso solo nelle attribuzioni riconosciute; le
  altre frasi che contengono "Comune di Firenze -" restano invariate.
- I test unitari coprono prefisso, JSON localizzato, descrizioni e hook; il
  test del comando copre dry-run e `--apply`.
