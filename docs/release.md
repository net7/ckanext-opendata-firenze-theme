# Rilascio del tema

Il tema è una dipendenza del repo `opendata-firenze-config`: lo stack dev monta
`src/` (checkout locale), mentre l'immagine prod-style lo installa da GitHub con
il pin in `ckan/Dockerfile`:

```
pip3 install -e 'git+https://github.com/net7/ckanext-opendata-firenze-theme.git@vX.Y.Z#egg=ckanext-opendata-firenze-theme'
```

Il pin è **un tag**, mai un branch: un branch cambierebbe sotto i piedi a ogni
rebuild e renderebbe l'immagine non riproducibile. Di conseguenza una modifica
al tema arriva in produzione **solo** dopo un rilascio taggato e l'aggiornamento
del pin.

## Procedura

1. **Verifiche locali** (albero pulito, lint e test verdi):

   ```bash
   git status --short          # deve essere vuoto
   make lint
   make test
   ```

2. **Bump della versione** in `pyproject.toml` (`version = "X.Y.Z"`), con un
   commit dedicato (`chore(release): vX.Y.Z`). La versione nel file e il tag
   devono coincidere.

3. **Push di `main` e CI verde**:

   ```bash
   git push origin main
   ```

   Attendere che i job `test`, `a11y` e `lint` siano verdi su GitHub Actions.
   Il tag va creato **solo** da un commit già verde.

4. **Tag annotato e push**:

   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin vX.Y.Z
   ```

   Il workflow gira anche sul tag e ricontrolla che la versione in
   `pyproject.toml` coincida con il nome del tag.

5. **Aggiornare il pin** in `ckan/Dockerfile` del repo
   `opendata-firenze-config` (il file è gestito da quel repo, non da questo):
   sostituire `@vX.Y.Z` nella riga del tema, poi ricostruire l'immagine
   prod-style e verificare che dentro il container giri la versione attesa.
   I comandi vanno eseguiti nel repo di configurazione, **fermando prima lo
   stack dev**: dev e prod-style condividono i volumi (Postgres, Solr,
   `home_dir`, `site_packages`) e non vanno avviati insieme.

   ```bash
   make dev down
   make prod up
   docker compose -f docker-compose.yml exec ckan \
     pip show ckanext-opendata-firenze-theme | grep -i version
   make prod down   # se si torna allo stack dev
   make dev up
   ```

6. **Dev**: `bin/clone_extensions` **non** sposta un clone già presente sul tag
   del Dockerfile (salta le directory esistenti, per non perdere lavoro locale).
   Un clone esistente non riceve i tag creati dopo il clone: vanno scaricati
   esplicitamente. Per provare un rilascio in dev:

   ```bash
   git -C src/ckanext-opendata-firenze-theme fetch --tags
   git -C src/ckanext-opendata-firenze-theme checkout vX.Y.Z
   make dev restart
   ```

   Poi tornare sul branch di lavoro (es. `main`, o quello su cui stai
   lavorando) per continuare lo sviluppo:

   ```bash
   git -C src/ckanext-opendata-firenze-theme checkout main
   ```

## Rollback

Rimettere il tag precedente nel pin e ricostruire, con la stessa cautela
dev/prod-style descritta sopra (`make dev down` prima di `make prod up`). Non
serve toccare il codice del tema: i tag restano disponibili su GitHub.

## Perché non un branch

- `main` cambia a ogni merge: due rebuild della stessa immagine potrebbero
  contenere codice diverso.
- Un tag rende evidente *quale* versione è in produzione e permette il rollback.
- Il pin è l'unico punto che lega i due repo: va aggiornato nello stesso giro
  del rilascio, altrimenti la produzione resta indietro (è già successo: il pin
  è rimasto a `v0.0.1` mentre `main` è avanzato di decine di commit).

## Riferimenti

- ADR 0003 e ADR 0004 del repo `opendata-firenze-config`: installazione delle
  estensioni nei due stack (dev e prod-style).
- `ckan/Dockerfile` e `bin/clone_extensions` nel repo di configurazione.
