# 7. Tracking dei download: CKAN non lo fa in modo nativo (nessun contatore)

## Stato

Accettata — nessun contatore di download (per ora)

## Contesto

CKAN ha un tracking **solo per le page view**: il plugin `tracking` registra la
visita della pagina di un dataset/risorsa (`tracking_summary`, da cui le
"Visualizzazioni"). Per i **download** non c'è nulla di nativo:

- il JS di CKAN registra un click solo sui link con la classe
  `resource-url-analytics`, e confronta l'href con `resource["url"]`
  (`TrackingSummary.get_for_resource`): il tema deve quindi mettere quella classe
  sui link e usare `res["url"]` come href;
- per le risorse **esterne** anche questo non basta: il click avvia il download e
  il browser **annulla la XHR** di tracking (Firefox: `NS_BINDING_ABORTED`, 0 B),
  quindi serve una **patch al JS di CKAN** (es. `sendBeacon`).

In altre parole: contare i download richiede **due divergenze dal core** (tema +
JS), e il risultato è comunque "visitatori distinti al giorno", non il numero di
download né i valori per periodo.

## Decisione

Nel tema **non** si abilita il tracking dei download: i link non hanno la classe
`resource-url-analytics` e i contatori di download non sono mostrati (scheda
risorsa, riga risorsa, "In sintesi"). Restano solo le **Visualizzazioni**.

Motivo e alternative (compreso il conteggio lato server) sono nel repo
`opendata-firenze-config`: ADR 0015 "Niente tracking dei download (per ora)" e la
decisione **DP03** (dashboard statistiche custom).

## Conseguenze

- Se si vorrà riattivare il contatore di CKAN servono **entrambe** le cose sopra:
  la classe/`res["url"]` nei template dei link e la patch al JS.
- Per un numero affidabile (anche con JS disattivato o blocker, e per periodo)
  serve invece una componente di conteggio **lato server** (DP03).
