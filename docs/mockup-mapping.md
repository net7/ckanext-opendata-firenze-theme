# Mappa mockup → tema CKAN

Riferimento di lavoro: come tradurre il prototipo React del portale in questo
tema CKAN (Jinja2 + WebAssets). Prototipo: repo `design-repo`, percorso
`prototypes/opendata-firenze/sites/opendata-firenze-0209` (file per schermata in
`screens/*.jsx`, contenuti di esempio in `data.js`, design system in `ds/`).

Non è un piano di implementazione vincolante: è la mappa dei template/snippet
da toccare, i dati da collegare e le decisioni ancora aperte.

## Regola generale

- Il mockup è una **SPA React**: i componenti di `ds/_ds_bundle.js` **non** si
  riusano. Si riusa il design system come **CSS/token** (`ds/styles.css`,
  variabili `--rtt-*`, font Titillium Web) e le immagini in `assets/`.
- I componenti vanno reimplementati come **snippet Jinja2**; le interazioni
  (tab, drawer, carousel, header a scomparsa, reveal-on-scroll) come **moduli JS**
  in `assets/js/` (+ stili in `assets/css/`).
- Il routing del mockup diventa **routing CKAN** (URL reali).
- Override sempre via `{% ckan_extends %}` + `{% block %}`, mai copiando l'intero
  albero dei template (vedi `README.md`).
- I numeri di `data.js` sono di esempio: i valori veri vanno presi da CKAN/Solr
  (facets, `package_search`, helper).

## Schermata → route/template

| Mockup (`screens/`) | Route CKAN | Template principale |
|---|---|---|
| `shell.jsx` | tutte | `base.html`, `header.html`, `footer.html` |
| `home.jsx` | `/` | `home/index.html` |
| `catalogo.jsx` | `/dataset` | `package/search.html` |
| `dataset.jsx` | `/dataset/<name>` | `package/read.html` |
| `risorsa.jsx` | `/dataset/<name>/resource/<id>` | `package/resource_read.html` |
| `annuario.jsx` | pagina (`/pages/...`) | `ckanext-pages` |
| `sviluppatori.jsx` | pagina (`/pages/...`) | `ckanext-pages` |
| `partecipa.jsx` | `/contact` | `ckanext-contact` |
| stati globali (404/errore) | — | `error_document_template.html` |

## Dettaglio per schermata

### Shell — `screens/shell.jsx`

- Header (logo Comune + logo OpenData, nav `Catalogo`/`Annuario Statistico`/
  `Sviluppatori & LOD`/`Collaborazione`, ricerca, selettore lingua, CTA "Segnala
  un dataset", variante mobile) → override **`header.html`**.
  - Nav verso pagine non-core → menu di `ckanext-pages` o snippet nav custom.
  - Ricerca → `snippets/search_form.html` (o `snippets/simple_search.html`).
  - Lingua → `snippets/language_selector.html` (esistente).
  - CTA "Segnala" → `/contact`.
- Footer (contatti Comune, colonne link, legal) → **`footer.html`**.
- TabBar mobile → snippet custom (solo <1024px).
- Comportamenti (hide-on-scroll, reveal) → JS in `assets/js/` + classi CSS.
- Snippet riusabili da creare: `Section`, `PageHead` (breadcrumb+titolo+lead),
  `TemaOverline` (icona per tema), `StatusScreen`.

### Home — `screens/home.jsx` → `home/index.html`

`home/index.html` (estende `page.html`) espone i block: `promoted`, `search`,
`featured_group`, `featured_organization` (più `content`/`primary_content`).
In CKAN 2.12 **non** esiste `home/layout*.html`: si override `home/index.html`
e/o gli snippet `home/snippets/*`.

- Hero + SearchBar + suggerimenti → `home/snippets/search.html`.
  Conteggio dataset: `h.get_site_statistics().dataset_count` o
  `package_search?rows=0`.
- KpiStrip (4 KPI) → snippet custom + helper del tema (`package_search` a
  `rows=0` per totali/facets: alfanumerici vs geodati, capitoli/tavole).
- In evidenza (feature + carousel HVD) → snippet custom + helper (dataset HVD).
- Esplora per tema (13 temi DCAT-AP_IT) → snippet custom; dati dal vocabolario
  `ckanext-dcatapit`, facet `theme`.
- I più consultati → snippet custom + helper (ordinamento per viste/download).
- News → `ckanext-pages`; snippet custom.

### Catalogo — `screens/catalogo.jsx` → `package/search.html`

- `package/search.html`: `primary_content` → `package/snippets/search_results.html`;
  `secondary_content` → `package/snippets/search_facets.html`. Faccette native da
  Solr (`c.search_facets`); lista faccette: `snippets/facet_list.html`.
- Result row (tema, titolo, descrizione, chip formati, data) →
  `snippets/package_item.html`.
- Paginazione → dentro `package/snippets/search_results.html`.
- No results ("forse cercavi", filtri attivi, più richiesti) → stato vuoto di
  `search_results.html` + snippet custom.
- Facet bar orizzontale / faccette laterali / drawer mobile → snippet + JS.
- Sort → ordinamento nativo di `package/search.html`.
- Gruppi faccette: `Temi` (theme), `Formato` (`res_format`), `Aggiornamento`
  (`frequency`), `Chi pubblica` (organization), `Tipo di geometria` (spatial),
  `Caratteristiche` (HVD/geodati/serie), `Classificazione geografica` (ISO 19115
  → campo spatial, **da verificare**).

### Dataset — `screens/dataset.jsx` → `package/read.html`

`package/read.html` estende `package/read_base.html`; `primary_content_inner`
include `package/snippets/resources_list.html`, `package/snippets/tags.html`,
`package/snippets/additional_info.html`. `read_base.html` espone
`content_action` (bottone Download), `content_primary_nav`,
`secondary_content` (`package_info` → `package/snippets/info.html`,
`package_organization`, `package_social`, `package_license`).

- Testata (TemaOverline, badge HVD/Geodati/realtime, h1, descrizione troncata,
  "Scarica", QualityGauge) → block di `read.html`/`read_base.html`.
  - QualityGauge = openness di `ckanext-qa` (0–5) → helper da esporre.
  - `hvd` → dcatapit; `geometria`/`geo` → spatial; `realtime`/`uso`/`serie` →
    extras custom (vedi "Dati").
- Tab "Vista essenziale / Metadati avanzati" → JS + override `read.html`.
- Descrizione → campo `notes`.
- Risorse scaricabili → `package/snippets/resources_list.html` /
  `resource_item.html`.
- Anteprima risorsa (modale) → resource views: `package/snippets/resource_view.html`,
  `resource_views_list.html`; tabella con `datatables_view`/datastore, mappa con
  `geoview`.
- Metadati DCAT-AP_IT / extras → `package/snippets/additional_info.html` (+ campi
  dcatapit); form → `package/snippets/package_metadata_fields.html`.
- API + console SQL → action API + `datastore_search_sql`; snippet custom.
- Aside "In sintesi" / Titolare → `secondary_content` + `package/snippets/info.html`.
- Dataset correlati → helper (serie dcatapit / `isVersionOf`).

### Risorsa — `screens/risorsa.jsx` → `package/resource_read.html`

`package/resource_read.html` estende `package/base.html`; block `resource_actions`,
`resource_content`, `download_resource_button`. Anteprima tabellare → Data
Explorer (`datatables_view`/datastore); mappa → `geoview` + `ckanext-spatial`
(layer WMS).

### Annuario — `screens/annuario.jsx` → pagina `ckanext-pages`

SideNav 13 capitoli + lista dataset per capitolo. Il campo `capitolo` **non è
nativo** (extra custom/tag/serie); ogni capitolo = query salvata sul catalogo
(`package_search` con filtro).

### Sviluppatori — `screens/sviluppatori.jsx` → pagina `ckanext-pages`

Contenuto editoriale + endpoint reali: action API (`package_search`,
`package_show`, `datastore_search`, `datastore_search_sql`) e RDF di `ckanext-dcat`
(`catalog.rdf`, `package_metadata_rdf_dcat_ap_it`, `package_show_dcatap_it`).
SPARQL e MCP server **non nativi** (fuori scope tema).

### Partecipa — `screens/partecipa.jsx` → `ckanext-contact`

Adattare il form di `ckanext-contact` ai 3 tipi (chiarimenti / segnalazione /
riuso), con validazione e informativa privacy.

## Dati: nativo vs custom

- `identificatore`, `tema`, `titolare`/`rights_holder`, `email` contatto,
  `licenza`, `frequency`, `pubblicato`/`modified`, `lingua`, `parole chiave`,
  `hvd`, `serie` → **dcatapit** / campi DCAT (in gran parte già presenti).
- `geometria`/geodati, ISO 19115 → **spatial** (facet da configurare/verificare).
- `capitolo` (Annuario), `realtime`, `uso`, `fratelli` → **extras custom**
  (`ckanext-scheming` **non** installato).
- `qualita` (openness) → **ckanext-qa**.
- `download`/`viste` → tracking CKAN (da abilitare) o `ckanext-googleanalytics`.
- `news` → **ckanext-pages**.
- Faccette "temi" (13) → vocabolario dcatapit + facet `theme`.

## Decisioni aperte

- Facet "Classificazione geografica" (ISO 19115): quale campo Solr esporre.
- `capitolo` Annuario: extra custom vs tag vs serie.
- Qualità del metadato: metrica MQA vs openness di `ckanext-qa`.
- "Forse cercavi": Solr `spellcheck` vs Levenshtein lato client (mockup).
- Download/viste: abilitare il tracking nativo o analytics.
- Header hide-on-scroll e reveal-on-scroll: portarli o semplificare.
- Faccette: solo barra orizzontale, solo laterali, o entrambe.
- Lingua: i18n UI nativa; metadati multilingua bloccati (`ckanext-multilang`).
- SPARQL endpoint / MCP server: richiedono backend, fuori dal tema.
- "Segnala un dataset": `ckanext-contact` (scelta attuale) vs `ckanext-issues`
  (scartata).

## Ordine di lavoro suggerito

1. Asset/design system: token CSS, font, logo/immagini (`assets/`, `public/`).
2. Shell: `header.html`, `footer.html`, tab bar + JS.
3. Snippet base riusabili (`Section`, `PageHead`, `TemaOverline`, chip).
4. Home (helper KPI/temi/consultati/news).
5. Catalogo (`search.html` + facet bar + result row + no-results).
6. Dataset (`read.html`: tab, risorse, metadati, QA, aside).
7. Risorsa (`resource_read.html` + view tabella/mappa).
8. Pagine editoriali (annuario, sviluppatori, partecipa).
9. Test di rendering + accessibilità.
