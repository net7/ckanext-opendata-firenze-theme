# 1. Font self-hosted con URL assoluti (dipendenza dal root path)

## Stato

Accettata

## Contesto

Il tema caricava Titillium Web dalla CDN di Google (`<link>` a
`fonts.googleapis.com` in `templates/base.html`). Per il portale di una PA
questo espone l'IP dell'utente a un terzo (privacy/GDPR) e introduce una
dipendenza di rete esterna su ogni pagina. E' stato quindi sostituito con il
**self-hosting**: i file `.woff2` (soli pesi usati — 400/600/700 —, subset
`latin` e `latin-ext`) stanno in `public/fonts/titillium-web/`, con la licenza
SIL OFL 1.1 in `OFL.txt`, e gli `@font-face` sono in
`assets/css/fonts.css`, incluso come primo file del bundle CSS.

WebAssets concatena i CSS del bundle e li serve da un percorso diverso dai
sorgenti (`/webassets/...`): un `url()` **relativo** dentro il CSS verrebbe
risolto rispetto al bundle e si romperebbe. Il rimedio standard e' il filtro
`cssrewrite` di WebAssets (non un plugin CKAN: la libreria e' gia' installata,
il filtro e' disponibile ma non attivato nel tema), che riscrive i riferimenti
relativi usando i public path registrati. Nel tema pero' i font stanno in
`public/` (servito da `/`) mentre il CSS sta in `assets/`.

## Decisione

Referenziare i font con URL **assoluti** (`url(/fonts/titillium-web/...)`),
senza attivare `cssrewrite`. Questo e' corretto fintanto che il portale e'
servito **alla radice** del dominio (nessun `ckan.root_path`), che e' lo
scenario previsto e attuale.

## Verifica fatta

- `public/fonts/titillium-web/*.woff2` serviti con `200` e
  `content-type: font/woff2`; il bundle CSS contiene i 6 `@font-face`; nessun
  riferimento a `fonts.googleapis.com`/`fonts.gstatic.com` nella pagina.

## Conseguenze

- Se in futuro il portale verra' servito sotto un sottopercorso
  (`ckan.root_path` impostato), i font non si caricheranno (404 su
  `/fonts/...`). E' l'unico punto del tema non root_path-safe: i link nei
  template usano `h.url_for(...)` e sono gia' ok.
- Per renderlo root_path-safe, prima dell'adozione: (a) attivare
  `filters: cssrewrite` sul bundle CSS e passare a `url()` relativi, oppure
  (b) usare `url(../fonts/...)` relativo al bundle (che sta un livello sotto
  la radice degli asset). Entrambe da testare.
