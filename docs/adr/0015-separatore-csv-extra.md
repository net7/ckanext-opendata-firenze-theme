# 15. Separatore CSV come extra del dataset

## Stato

Accettata

## Contesto

Il mockup della scheda dataset mostra il separatore di campo per le risorse CSV
come campo del dataset (`ds.separatore`). In catalogo l'extra `separatore` non
esiste: **1.417 dataset** lo dichiarano solo nella descrizione, con due
varianti note:

- `Il separatore delle risorse CSV è ";" (lett. punto e virgola).`
- `Il separatore delle risorse CSV è "," (lett. virgola).`

L'harvest riscrive periodicamente questi dataset, quindi l'estrazione non può
essere un intervento manuale una tantum.

## Decisione

- `helpers/separator.py` possiede la regex, la normalizzazione (simboli e nomi
  come `TAB`/`punto e virgola`) e la lettura dalla descrizione.
- `odf_resource_separator` legge, nell'ordine: extra `separatore` → descrizione.
  Se nessuno dei due lo dichiara non si inventa un valore e il campo non viene
  mostrato. Solo le risorse CSV mostrano il campo.
- `package_create` e `package_update` sono chained action del tema: prima del
  salvataggio aggiungono l'extra dalla descrizione se manca. È il
  post-processing dell'harvest (che passa dalle stesse action), senza un
  secondo `package_update` e senza ricorsione. Su `package_update` si tocca
  solo un dict che ha già `extras`, per non cancellare gli altri extra con un
  update parziale.
- `ckan odf-extract-separators` fa il backfill dei dataset già in catalogo, con
  dry-run di default, `--apply`, `--dataset` e `--limit`.

## Conseguenze

- L'extra è la fonte di verità; il campo compare solo se extra o descrizione
  dichiarano il separatore.
- I dataset nuovi/aggiornati dall'harvest non richiedono un passaggio manuale;
  il backfill serve solo per lo storico.
- Il separatore è dataset-level, come nel mockup: CSV con separatori diversi
  nello stesso dataset non sono rappresentabili (accettato).

## Verifica

- Test del parser, della precedenza extra/descrizione, delle chained action su
  create/update e del comando di backfill.
