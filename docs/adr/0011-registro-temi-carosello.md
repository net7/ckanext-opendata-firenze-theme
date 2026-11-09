# 11. Registro unico dei temi e carosello unico

## Stato

Accettata

## Contesto

Due duplicazioni nel tema:

- i 13 temi DCAT-AP_IT vivevano in due tabelle (`constants.THEMES` e la tabella
  `TEMA_THEMES` dentro `tema-overline.html`) più le chiavi icona in `icon.html`:
  aggiungere un tema richiedeva tre modifiche non verificate l'una contro
  l'altra;
- il markup del carosello era scritto due volte: nel macro `dataset_carousel`
  (usato da "Ultimi pubblicati" e "Linked Open Data") e a mano in
  `featured.html` per le card di "In evidenza". Cambiare frecce o indicatori
  significava toccare due file e due test.

## Decisione

1. **Un solo registro dei temi** in `helpers/constants.py`:
   `THEME_REGISTRY = ((codice, label, chiave_icona), …)`. `THEMES` (codice +
   label), `THEME_ICONS` e `THEME_CODES` sono derivate. La tabella Jinja
   `TEMA_THEMES` sparisce.
2. **Un helper per i metadati**: `odf_theme_meta(tema)` accetta codice, label o
   URI e ritorna `{code, label, icon}` (None se non è uno dei 13). I macro di
   `tema-overline.html` diventano renderer; il fallback per i temi non mappati
   resta l'icona `grid`.
3. **Un macro per il carosello**: `featured.html` usa `dataset_carousel` come
   gli altri blocchi. Sparisce la copia del markup e la classe
   `rtt-evidenza__others` (la superficie lilla delle card viene da
   `.rtt-home .rtt-carousel`).
4. **Test**: metadati del tema, presenza di ogni chiave icona del registro in
   `icon.html`, e "In evidenza" che rende il carosello condiviso.

## Conseguenze

- Aggiungere un tema = una voce in `THEME_REGISTRY`; l'icona va aggiunta in
  `icon.html` e un test fallisce se manca, invece di renderizzare un overline
  senza icona.
- Cambiare il carosello (frecce, indicatori, markup delle card) tocca un solo
  macro; il comportamento resta quello del componente `.rtt-carousel` del JS.
- La home è rimasta identica (verificato su dev: 6 card nel carosello "In
  evidenza", superficie `#F2EDF4`, stessa aria-label).

## Alternative scartate

- **Tenere la tabella Jinja e sincronizzarla a mano**: è il problema di
  partenza, senza alcun test che la leghi a `constants`.
- **Un flag in `featured.html` per evitare il macro**: manteneva due markup
  dello stesso componente.
