# 2. Console SQL della scheda dataset: gating su ckanext-datastore

## Stato

Accettata

## Contesto

Il mockup della scheda dataset (step 6) mostra, nel pannello "API e formati
semantici", una **console SQL** che interroga i dati con
`datastore_search_sql`. In CKAN quell'azione viene registrata dal plugin
`datastore` **solo se il backend ha `enable_sql_search`**, cioè se
`ckan.datastore.sqlsearch.enabled = true` (default `false`); con il flag spento
l'endpoint risponde `Action name not known: datastore_search_sql`. Abilitarla
espone una console SQL pubblica (in sola lettura: CKAN rifiuta le scritture e
limita le funzioni SQL ammesse).

## Decisione

Il tema **non abilita** il flag e rende la console solo se l'helper di CKAN
`datastore_search_sql_enabled()` è `True`. L'helper del tema
`odf_sql_console_enabled()` lo chiama in modo difensivo (`getattr`), così la
pagina non va in errore quando `ckan.datastore` non è caricato (es. nei test
del tema). Senza flag il pannello mostra gli endpoint API e una nota che spiega
che la console non è abilitata.

Quando è attiva, la query è inviata in **POST** (form-encoded) e i risultati
sono scritti con `textContent` (niente `innerHTML`); le richieste precedenti
vengono annullate con `AbortController` (vince l'ultima query lanciata).

**CSRF**: CKAN disattiva la protezione CSRF solo per le richieste autenticate
via header `Authorization` (API token). Un utente loggato **via cookie di
sessione** che fa POST senza token riceve `400` (verificato: anonimo `200`,
sessione `400`, sessione + header `X-CSRFToken` `200`). Per questo il JS legge
il token dai `<meta name="csrf_field_name">` / `<meta name="<field>">` emessi
dal `base.html` di CKAN e lo invia nell'header `X-CSRFToken`. (Con GET il
problema non si porrebbe, ma si perderebbero POST e niente SQL nei log.)

## Verifica fatta

- In dev (flag assente) la scheda mostra la nota e non il form: nessun errore.
- POST form-encoded all'action API verificato su `package_search` (nessun
  token CSRF richiesto).
- La query end-to-end con `datastore_search_sql` **non** è stata verificata:
  richiede di attivare il flag, che è una scelta di ambiente.

## Conseguenze

- Per avere la console in un ambiente va impostato
  `ckan.datastore.sqlsearch.enabled = true` (dev **e** prod) e va valutata
  l'esposizione della console SQL pubblica (read-only, ma superficie aggiuntiva).
- Il tema resta neutro: nessuna configurazione è cablata nel codice, e il
  comportamento degrada con una nota quando la console non è disponibile.
