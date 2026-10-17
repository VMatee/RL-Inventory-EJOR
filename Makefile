PYTHON ?= $(shell if [ -x ../code/.venv/bin/python ]; then echo ../code/.venv/bin/python; else echo python3; fi)

.PHONY: check test smoke manuscript m1-reference data-status
check:
	$(PYTHON) scripts/check_project.py

test:
	$(PYTHON) -m unittest discover -s tests -v

smoke:
	$(PYTHON) scripts/run_experiment.py --config experiments/configs/smoke.json --seed 0

m1-reference:
	$(PYTHON) scripts/run_m1_reference.py

data-status:
	$(PYTHON) scripts/fetch_m5.py --verify-only
	$(PYTHON) scripts/fetch_favorita.py --status

manuscript:
	@command -v latexmk >/dev/null 2>&1 || { echo "latexmk missing; see manuscript/README.md"; exit 1; }
	cd manuscript && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
