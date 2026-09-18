# ckanext-opendata-firenze-theme

Tema CKAN del portale Open Data del Comune di Firenze (repo di configurazione
`opendata-firenze-config` a parte).

Scheletro iniziale. In CKAN un tema è un'estensione come le altre: registra una
cartella di template (override via `{% ckan_extends %}`) e una di asset (CSS/JS
via WebAssets).

## Installazione (dev, dentro lo stack di `opendata-firenze-config`)

1. Clonare questa repo in `src/` del repo di configurazione:

   ```bash
   git clone <url> src/ckanext-opendata-firenze-theme
   ```

2. Aggiungere `opendata_firenze_theme` a `CKAN__PLUGINS` in `.env`.
3. `make dev up`: in dev l'estensione viene installata a runtime da `src/`
   (vedi ADR-0003 del repo di configurazione).

In prod-style va invece aggiunta a `ckan/Dockerfile` (ADR-0004).

## Struttura

```
ckanext/opendata_firenze_theme/
├── plugin.py                 IConfigurer: registra templates/, public/, assets/
├── templates/
│   └── base.html             {% ckan_extends %} + hook degli asset
├── assets/
│   ├── webassets.yml         bundle CSS/JS
│   ├── css/                  stili del tema
│   └── js/                   moduli JS (sandbox CKAN)
├── public/                   file statici non WebAssets (immagini, ...)
├── tests/
└── i18n/
```

## Riferimenti

- Mockup/UX: nel repo `design-repo`, prototipo `opendata-firenze-0209`
  (`prototypes/opendata-firenze/sites/opendata-firenze-0209`).
- Tema gemello (Toscana): `net7/ckanext-opendata-theme`.
- Documentazione CKAN: <https://docs.ckan.org/en/2.12/theming/index.html>.
