.PHONY: help
help:
	@echo "ARTESP CKAN Theme Extension Makefile"
	@echo ""
	@echo "Usage:"
	@echo "    make help                  - Show this help message"
	@echo "    make clean                 - Remove build artifacts"
	@echo "    make dev-setup             - Set up development environment"
	@echo "    make test                  - Run tests"
	@echo "    make lint                  - Check code style with flake8"
	@echo "    make i18n-extract          - Extract translatable strings"
	@echo "    make i18n-init LANG=pt_BR  - Initialize catalog for a NEW language (WARNING: overwrites existing translations)"
	@echo "    make i18n-update           - Update translation catalogs (safe for existing languages)"
	@echo "    make i18n-compile          - Compile translation catalogs"
	@echo "    make i18n-stats            - Show translation statistics (percentage complete)"
	@echo "    make i18n-all              - Run extract, update, and compile in sequence"
	@echo "    make restart-ckan          - Restart CKAN container (requires Docker)"
	@echo "    make i18n-full             - Full i18n workflow: extract, update, compile, restart"
	@echo ""

.PHONY: clean
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf __pycache__/
	rm -f *.pyc
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

.PHONY: dev-setup
dev-setup:
	pip install -e .
	pip install -r dev-requirements.txt

.PHONY: test
test:
	pytest --ckan-ini=test.ini ckanext/artesp_theme/tests/

.PHONY: lint
lint:
	flake8 ckanext/artesp_theme/

# Internationalization targets

.PHONY: i18n-extract
i18n-extract:
	@echo "Extracting translatable strings..."
	python setup.py extract_messages
	@echo "Done. POT file updated at ckanext/artesp_theme/i18n/ckanext-artesp_theme.pot"

.PHONY: i18n-init
i18n-init:
	@if [ -z "$(LANG)" ]; then \
		echo "Error: LANG variable is required. Example: make i18n-init LANG=pt_BR"; \
		exit 1; \
	fi
	@if [ -d "ckanext/artesp_theme/i18n/$(LANG)" ]; then \
		echo "WARNING: Catalog for language $(LANG) already exists!"; \
		echo "Initializing a catalog for an existing language will OVERWRITE ALL EXISTING TRANSLATIONS."; \
		echo "If you want to update an existing catalog, use 'make i18n-update' instead."; \
		echo ""; \
		read -p "Are you sure you want to continue? (y/N): " confirm; \
		if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
			echo "Operation cancelled."; \
			exit 1; \
		fi; \
	fi
	@echo "Initializing catalog for language: $(LANG)..."
	python setup.py init_catalog -l $(LANG)
	@echo "Done. PO file created at ckanext/artesp_theme/i18n/$(LANG)/LC_MESSAGES/ckanext-artesp_theme.po"

.PHONY: i18n-update
i18n-update:
	@echo "Updating translation catalogs..."
	python setup.py update_catalog
	@echo "Done. PO files updated."

.PHONY: i18n-compile
i18n-compile:
	@echo "Compiling translation catalogs..."
	python setup.py compile_catalog
	@echo "Done. MO files compiled."

.PHONY: i18n-stats
i18n-stats:
	@python i18n_stats.py

.PHONY: i18n-all
i18n-all: i18n-extract i18n-update i18n-compile
	@echo "All i18n tasks completed successfully."

.PHONY: restart-ckan
restart-ckan:
	@echo "Restarting CKAN container..."
	cd ../../ && docker-compose restart ckan
	@echo "CKAN container restarted."

.PHONY: i18n-full
i18n-full: i18n-all restart-ckan
	@echo "Full i18n workflow completed successfully."
	@echo "Translations should now be available in the CKAN interface."

# Add specific language shortcuts for convenience

.PHONY: i18n-pt_BR
i18n-pt_BR:
	@echo "Running full i18n workflow for Brazilian Portuguese (pt_BR)..."
	@if [ ! -d "ckanext/artesp_theme/i18n/pt_BR" ]; then \
		echo "Initializing new catalog for Brazilian Portuguese..."; \
		make i18n-init LANG=pt_BR; \
	else \
		echo "Brazilian Portuguese catalog already exists. Safely updating..."; \
		make i18n-extract; \
		make i18n-update; \
	fi
	make i18n-compile
	@echo "Brazilian Portuguese translations updated. Restart CKAN to apply changes."
	@echo "Use 'make restart-ckan' to restart CKAN."
