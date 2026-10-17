PYTHON ?= .venv/bin/python

.PHONY: check test smoke manuscript
check:
	$(PYTHON) scripts/check_project.py

test:
	$(PYTHON) -m unittest discover -s tests -v

smoke:
	$(PYTHON) scripts/run_experiment.py --config experiments/configs/smoke.json --seed 0

manuscript:
	@command -v latexmk >/dev/null 2>&1 || { echo "latexmk missing; see manuscript/README.md"; exit 1; }
	cd manuscript && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
