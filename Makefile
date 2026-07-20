.PHONY: help

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME = sqlalchemy-multiple-db

SRC_PATH = src/sqlalchemy_multiple_db
LINT_PATHS = src tests

UV ?= uv

#################################################################################
# VIRTUAL ENVIRONMENT                                                           #
#################################################################################

.PHONY: venv/install/main
## Install runtime dependencies
venv/install/main:
	@echo "Installing runtime dependencies..."
	$(UV) sync --no-group dev
	@echo "done"
	@echo

.PHONY: venv/install/all
## Install runtime and development dependencies
venv/install/all:
	@echo "Installing runtime and development dependencies..."
	$(UV) sync --all-groups
	@echo "done"
	@echo

#################################################################################
# COMMANDS                                                                      #
#################################################################################

########################################
### Code style and static analysis
########################################

.PHONY: lint/ruff
## Check formatting and linting with Ruff
lint/ruff:
	@echo "Linting with Ruff..."
	$(UV) run ruff format --check $(LINT_PATHS)
	$(UV) run ruff check $(LINT_PATHS)
	@echo "done"
	@echo

.PHONY: lint/mypy
## Type-check source with mypy
lint/mypy:
	@echo "Type-checking with mypy..."
	$(UV) run mypy $(SRC_PATH)
	@echo "done"
	@echo

.PHONY: lint
## Run all static checks
lint: lint/ruff lint/mypy

.PHONY: format
## Format source code and apply safe lint fixes
format:
	@echo "Formatting source code..."
	$(UV) run ruff format $(LINT_PATHS)
	$(UV) run ruff check --fix $(LINT_PATHS)
	@echo "done"
	@echo

.PHONY: clean
## Delete generated build artifacts and caches
clean:
	@echo "Clearing generated files..."
	rm -rf .coverage .mypy_cache .pytest_cache .ruff_cache build dist
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	@echo "done"
	@echo

####################
### Tests
####################

.PHONY: test
## Run tests with coverage
test:
	$(UV) run pytest --cov=sqlalchemy_multiple_db --cov-report=term-missing

####################
### Distribution
####################

.PHONY: build
## Build source and wheel distributions
build:
	$(UV) build

#################################################################################
# SELF-DOCUMENTING COMMANDS                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
