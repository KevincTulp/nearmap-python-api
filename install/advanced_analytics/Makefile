.PHONY: data clean env_create env_export env_activate env_build test create_kernel

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME = nearmap
ENV_NAME = nearmap-py3-advanced

SHELL=/bin/bash
CONDA_ACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Make Dataset
data:
	. activate $(ENV_NAME)
	python src/data/make_dataset.py
	@echo ">>> Data processed."

## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Build the local environment from the environment file
env:
	conda env create -f environment.yml
	($(CONDA_ACTIVATE) $(ENV_NAME) ; cd $(PROJECT_DIR) && python -m pip install -e ../..)
##	jupyter labextension install @jupyter-widgets/jupyterlab-manager -
	@echo ">>> New conda environment, $(ENV_NAME), created. Activate with: - source activate $(ENV_NAME) - make env_activate"

## Remove the Environment
env_remove:
	($(CONDA_ACTIVATE) $(ENV_NAME) ; cd $(PROJECT_DIR) && python -m pip uninstall nearmap -y)
	conda deactivate
	conda env remove --name $(ENV_NAME) -y

## Update the Environment
env_update:
	($(CONDA_ACTIVATE) $(ENV_NAME) ; cd $(PROJECT_DIR) && python -m pip uninstall nearmap -y)
	conda deactivate
	conda env remove --name $(ENV_NAME) -y
	conda env create -f environment.yml
	($(CONDA_ACTIVATE) $(ENV_NAME) ; cd $(PROJECT_DIR) && python -m pip install -e ../..)

## Create Nearmap EGG
pip_install:
	($(CONDA_ACTIVATE) $(ENV_NAME) ; cd $(PROJECT_DIR) && python -m pip install -e ../..)

## Remove Nearmap EGG
pip_remove:
	($(CONDA_ACTIVATE) $(ENV_NAME) ; cd $(PROJECT_DIR) && python -m pip uninstall nearmap -y)

## Update Nearmap EGG
pip_update:
	($(CONDA_ACTIVATE) $(ENV_NAME) ; cd $(PROJECT_DIR) && python -m pip uninstall nearmap -y)
	($(CONDA_ACTIVATE) $(ENV_NAME) ; cd $(PROJECT_DIR) && python -m pip install -e ../..)

## Export the current environment
env_export:
	conda env export --name $(ENV_NAME) > environment.yml
	@echo ">>> $(PROJECT_NAME) conda environment exported to ./environment.yml"

create_kernel:
	python -m ipykernel install --user --name $(ENV_NAME) --display-name "$(PROJECT_NAME)"

## Activate the environment - doesn't work, so commented out
# env_activate:
# 	. activate $(PROJECT_NAME)
# 	@echo ">>> $(PROJECT_NAME) conda environment activated."

## Run all tests in module
test:
	.. activate $(ENV_NAME)
	pytest

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################



#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
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
