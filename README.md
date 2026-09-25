# ckanext-opendata-firenze-theme

Tema CKAN del portale Open Data del Comune di Firenze (repo di configurazione
`opendata-firenze-config` a parte).

In CKAN un tema è un'estensione come le altre: registra una cartella di template
(override via `{% ckan_extends %}`), una di asset (CSS/JS via WebAssets), gli
helper dei template e le rotte editoriali (Annuario, Sviluppatori). Il tema
reimplementa il prototipo React del design system (`design-repo`), di cui riusa
token CSS, immagini e comportamento.

## Installazione

Il tema è già collegato dal repo di configurazione `opendata-firenze-config`:
`opendata_firenze_theme` è in `CKAN__PLUGINS` (`.env.example`) e il pin è in
`ckan/Dockerfile`. In dev `bin/clone_extensions` lo clona in `src/` se manca,
quindi basta `make dev up` (ADR-0003/0004 del config).

Per usarlo in un altro ambiente: `pip install -e .` e aggiungere
`opendata_firenze_theme` a `ckan.plugins`.

## Struttura

```
ckanext/opendata_firenze_theme/
├── plugin.py                 IConfigurer + ITemplateHelpers + IBlueprint
├── views.py                  rotte editoriali (/annuario-statistico, /sviluppatori-e-lod)
├── helpers/                  helper dei template per area (_common, catalog, home, dataset, …)
├── templates/                override (base/page/header/footer) + home/package/annuario/sviluppatori/contact
│   └── snippets/opendata_firenze_theme/   snippet riusabili (section, page-head, chip, card, sviluppatori/tab-*)
├── assets/
│   ├── webassets.yml         bundle CSS/JS
│   ├── css/                  partial per area (base/shell/snippets/home/catalog/…) + tokens del design system
│   └── js/                   moduli IIFE (shell, components, home, dataset, contact)
├── public/                   file statici non WebAssets (immagini, font, logo)
├── docs/adr/                 decisioni di progetto
├── tests/
└── i18n/
```

## Test

La CI (GitHub Actions) usa servizi Postgres/Solr dedicati. In locale **non**
eseguire i test con il DB/Solr di sviluppo: i dataset creati dai factory
resterebbero indicizzati nel catalogo dev. Servono un DB e un core Solr di test
(una volta sola: `ckan -c test-core.ini db init` su un DB di test e un core
omonimo in Solr), poi:

```bash
CKAN_SQLALCHEMY_URL=postgresql://ckandbuser:ckandbpassword@db/ckan_test \
CKAN_SOLR_URL=http://solr:8983/solr/ckan_test \
python -m pytest --ckan-ini=/srv/app/src/ckan/test-core.ini \
  ckanext/opendata_firenze_theme
```

I test che richiedono estensioni di deployment non installate (es.
`ckanext-contact`) vengono saltati.

## Traduzioni (i18n)

Le stringhe utente passano da `_()` / `ungettext()` (helper: `toolkit._`). Il
template delle traduzioni è `i18n/ckanext-opendata_firenze_theme.pot`,
rigenerabile con `python setup.py extract_messages`.

Il portale offre italiano e inglese (`CKAN__LOCALES_OFFERED="it en"`): la lingua
sorgente delle stringhe del tema è l'italiano, quindi il **catalogo inglese non è
ancora tradotto** (in EN le stringhe del tema restano in italiano). Per aggiungerlo:

```bash
python setup.py init_catalog -l en   # crea i18n/en/LC_MESSAGES/*.po
# ...tradurre il .po, poi:
python setup.py compile_catalog      # genera il .mo
```

## Riferimenti

- Mockup/UX: nel repo `design-repo`, prototipo `opendata-firenze-0209`
  (`prototypes/opendata-firenze/sites/opendata-firenze-0209`).
- Tema gemello (Toscana): `net7/ckanext-opendata-theme`.
- Documentazione CKAN: <https://docs.ckan.org/en/2.12/theming/index.html>.
