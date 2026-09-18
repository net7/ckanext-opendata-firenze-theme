# ckanext-opendata-firenze-theme

Tema CKAN del portale Open Data del Comune di Firenze (repo di configurazione
`opendata-firenze-config` a parte).

Scheletro iniziale. In CKAN un tema è un'estensione come le altre: registra una
cartella di template (override via `{% ckan_extends %}`) e una di asset (CSS/JS
via WebAssets).

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
