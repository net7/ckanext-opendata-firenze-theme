# 8. Blocchi della homepage configurabili dagli operatori

## Stato

Accettata

## Contesto

L'issue #14 chiede che la homepage sia una struttura di blocchi
**attivabili/disattivabili, riordinabili e personalizzabili nei testi** dagli
operatori senza intervento tecnico. Fino a oggi `templates/home/index.html`
conteneva le sezioni in ordine fisso (hero, KPI, in evidenza, temi, più
consultati, news): per cambiarle serviva modificare il template e
ridistribuire.

Vincoli:

- niente migrazioni o tabelle nuove se esiste un meccanismo standard CKAN;
- la modifica deve essere visibile subito, anche con più worker (non solo nel
  processo che ha gestito la richiesta);
- i blocchi senza contenuto (news senza post, "in evidenza" senza HVD, ecc.)
  devono continuare a nascondersi da soli;
- l'interfaccia deve restare accessibile (niente drag&drop come unico modo).

## Decisione

1. **Registro dei blocchi nel tema** (`helpers/home_blocks.py`): `BLOCKS`
   elenca, per ogni blocco, id, etichetta, template e campi tipizzati (`text` o
   `url`) con il proprio default. Aggiungere un blocco = una voce qui + un
   template in `templates/home/blocks/`.
2. **Configurazione runtime standard CKAN**: ordine, blocchi attivi e testi
   (titolo, sottotitolo, testo e URL del link) sono una **lista ordinata** in
   JSON nell'opzione `ckanext.opendata_firenze_theme.homepage_blocks`,
   dichiarata in `IConfigurer.update_config_schema`/`IConfigDeclaration` e
   scritta con l'azione `config_option_update`, che la salva in `system_info`
   (nessuna migrazione, nessun file da toccare). Ogni voce è
   `{"id", "enabled", "title", "subtitle", "cta_label", "cta_url"}`. I default
   stanno nel registro e il form parte da quelli; un campo vuoto significa "non
   mostrare quel testo/link", mentre un campo assente da una config
   parziale/vecchia usa il default. Il vecchio formato (lista di soli id) resta
   accettato.
3. **Lettura dal DB, non dalla config in-memory**: `_raw_value()` legge
   `model.get_system_info(OPTION)` (con fallback a `config.get` per il default),
   così la modifica è immediata su tutti i worker, non solo su quello che ha
   servito il POST.
4. **Pagina di amministrazione** `/ckan-admin/homepage` (blueprint `odf_admin`,
   solo sysadmin tramite `check_access('config_option_update')`): tabella con
   checkbox "attivo", campo numerico "ordine" e campi tipizzati con **etichette
   visibili** per i soli attributi supportati dal blocco. Gli `url` sono
   validati lato server (percorso che inizia con `/` oppure `http(s)://`; schemi
   come `javascript:` rifiutati): se non validi, il form viene rimostrato con
   l'errore sul campo e non viene salvato nulla. Form server-side, accessibile
   da tastiera; nessun JS obbligatorio.
5. **Default = comportamento attuale**: se l'opzione non è impostata si usa
   l'ordine di `BLOCKS` con tutti i blocchi attivi e i testi predefiniti del
   registro. Un elenco vuoto esplicito (`[]`) significa "nessun blocco".
6. La home include i template nell'ordine restituito da `odf_home_blocks()`:
   ogni blocco gestisce da sé il proprio stato vuoto e il proprio wrapper
   (`section`), come prima.

Il link alla pagina è aggiunto alla navigazione di `/ckan-admin` con un
override di `admin/base.html`.

## Conseguenze

- Gli operatori gestiscono la home da browser; nessun deploy per riordinare,
  disattivare o riscrivere titoli/sottotitoli/etichette e destinazioni dei link.
- I testi predefiniti stanno nel registro e sono tradotti con `_()` al momento
  del rendering; il form li precompila. Svuotare un campo lo nasconde (titolo,
  sottotitolo o link), senza dover toccare i template.
- I link sono **validati** (percorso `/...` o `http(s)://`): niente
  `javascript:`/`data:` o URL protocol-relative. L'`href` resta comunque
  auto-escapato da Jinja.
- Restano **solo sysadmin** (stessa auth dell'azione `config_option_update`):
  se servirà un ruolo editor dedicato, va aggiunto un override delle auth
  function (come per `ckanext-pages`).
- L'ordinamento è numerico, non drag&drop: scelta deliberata per accessibilità
  e assenza di JS. Se in futuro servirà il drag&drop, va aggiunto come
  miglioramento progressivo mantenendo i campi numerici come fallback.
- I test coprono registro, parsing (nuovo e vecchio formato, config parziale),
  ordine, selezione e testi, validazione degli URL, esposizione dello schema,
  403 anonimo e rendering della home con ordine configurato, testi
  personalizzati, testi svuotati, blocco disattivato ed escaping del testo del
  link.

## Alternative scartate

- **Tabella dedicata + migrazione alembic nel tema**: più codice e un
  meccanismo di storage tutto nostro, quando CKAN ha già `system_info` per le
  opzioni runtime.
- **`ckanext-scheming`**: non installato e pensato per la metadatazione dei
  dataset, non per la configurazione del sito.
- **Salvare la configurazione dentro `ckanext-pages`**: il CMS è pensato per
  contenuti editoriali, non per una struttura JSON di configurazione.
