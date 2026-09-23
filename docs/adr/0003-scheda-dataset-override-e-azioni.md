# 3. Scheda dataset: override del content, azioni editor e Markup delle azioni

## Stato

Accettata

## Contesto

Il mockup della scheda dataset richiede una testata custom a tutta larghezza e
una griglia "contenuto + aside", diversi dai blocchi standard di CKAN
(`toolbar`/breadcrumb, `.row.wrapper` con `primary`/`secondary`). Come per il
catalogo, il tema sostituisce integralmente `{% block content %}`.

Sostituendo `content` spariscono anche i blocchi di `package/read_base.html`
`content_action` (bottone **Gestisci** → modifica dataset) e
`content_primary_nav` (tab **Gruppi**): senza ripristino, un editor non ha più
il punto d'accesso alla modifica dalla scheda.

Inoltre le azioni dei pannelli (es. "Profilo italiano del vocabolario DCAT")
sono markup passato ai macro `panel`/`section`. Passare una stringa costruita
con `~` e filtrarla con `|safe` **non** veniva reso raw nel render di CKAN
(usciva escapata), mentre un block-set `{% set %}…{% endset %}` (che produce
`Markup`) funziona — è già il pattern usato da `section.html`/home.

## Decisione

- Override completo del `content` della scheda.
- Ripristino delle affordance editoriali nella testata: link **"Gestisci"** →
  `dataset.edit` se `h.check_access('package_update')`, e **"Gruppi"** →
  `dataset.groups` se il dataset ha gruppi.
- Le azioni dei pannelli si compongono con block-set
  `{% set action %}…{% endset %}` e si passano al macro; **non** si usano
  stringhe concatenate + `|safe`.

## Verifica fatta

- Scheda (essenziale e avanzata) → `200`; le azioni dei pannelli non risultano
  escapate (`test_dataset_page_renders_advanced`).
- Per l'anonimo nessuna azione di gestione è presente
  (`test_dataset_no_editor_action_for_anonymous`). Il ramo "editor" non è
  coperto da test: l'autenticazione via API token nei test di questo ambiente
  fallisce (`Cannot decode JWT token: Invalid header padding`) e il patch di
  `ckan.lib.helpers.check_access` non raggiunge il namespace `h` dei template.

## Conseguenze

- Chi modifica la testata deve ripristinare a mano eventuali affordance di
  `read_base.html` non presenti nel mockup.
- Convenzione del tema: le azioni di `panel`/`section` sono block-set Markup.
- Resta da coprire il ramo editor quando l'ambiente di test avrà
  un'autenticazione utilizzabile.
