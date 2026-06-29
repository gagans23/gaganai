.PHONY: setup validate bake daily dry-run serve

PYTHON ?= python3

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements.txt

validate:
	$(PYTHON) automation/validate_site_data.py

bake: validate
	$(PYTHON) automation/render_radar.py

daily:
	./automation/gcc-ai-newsletter/run_today.sh

dry-run:
	DRY_RUN=1 ./automation/update_daily_intelligence.sh

serve:
	python3 -m http.server 8080
