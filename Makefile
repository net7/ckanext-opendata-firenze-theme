# Comandi di sviluppo del tema.
#
# I test NON girano in un venv locale: richiedono il container CKAN con un DB
# e un core Solr di test (vedi README > Test). Le regole di lint sono le stesse
# del repo di configurazione `opendata-firenze-config` (vedi pyproject.toml).

.PHONY: help install lint lint-fix test

RUFF ?= $(shell if [ -x .venv/bin/ruff ]; then echo .venv/bin/ruff; else echo ruff; fi)
CKAN_CONTAINER ?= ckan-firenze-dev
TEST_DB ?= postgresql://ckandbuser:ckandbpassword@db/ckan_test
TEST_SOLR ?= http://solr:8983/solr/ckan_test

help: ## Mostra questo aiuto
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Crea .venv/ con i tool di sviluppo e attiva il git hook locale
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	# Solo il linter: i test girano nel container CKAN (`make test`), quindi
	# pytest-ckan non serve nel venv locale. La versione resta quella di
	# dev-requirements.txt, senza duplicare il pin.
	.venv/bin/pip install "$$(grep -m1 -E '^ruff' dev-requirements.txt)"
	git config core.hooksPath .githooks
	chmod +x .githooks/pre-commit
	@echo "OK: .venv/ pronto e hook attivo (.githooks/pre-commit)"

lint: ## ruff: lint + controllo formattazione
	$(RUFF) check .
	$(RUFF) format --check .

lint-fix: ## ruff: applica fix e formattazione
	$(RUFF) check --fix .
	$(RUFF) format .

test: ## pytest nel container CKAN (CKAN_CONTAINER, TEST_DB e TEST_SOLR sovrascrivibili)
	docker exec $(CKAN_CONTAINER) sh -c 'cd /srv/app/src_extensions/ckanext-opendata-firenze-theme && CKAN_SQLALCHEMY_URL=$(TEST_DB) CKAN_SOLR_URL=$(TEST_SOLR) python -m pytest --ckan-ini=/srv/app/src/ckan/test-core.ini ckanext/opendata_firenze_theme'
