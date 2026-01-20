PY?=python3
PYTHONPATH=src
RUN=$(PY) -m 00_run

ENV_FILE=config/ntfy.env
OUT=out/schedule.json

# Zeitraum defaults (kannst du überschreiben: make plan START=2026-01-20 END=2026-01-22)
START?=2026-01-20
END?=2026-01-22
SEED?=

help:
	@echo "Targets:"
	@echo "  make setup         - legt config/ntfy.env an (wenn nicht vorhanden)"
	@echo "  make plan          - randomisiert planen, out/schedule.json schreiben"
	@echo "  make plan-explain  - wie plan, aber mit Erklärmodus"
	@echo "  make dry-plan      - planen ohne Versand"
	@echo "  make test-send     - sendet Nachricht 1 sofort (echter Versand!)"
	@echo "  make dry-send      - zeigt nur, was gesendet würde"
	@echo ""
	@echo "Variablen:"
	@echo "  START=YYYY-MM-DD END=YYYY-MM-DD SEED=123"

setup:
	@test -f $(ENV_FILE) || (cp config/ntfy.env.example $(ENV_FILE) && chmod 600 $(ENV_FILE) && echo "OK: $(ENV_FILE) erstellt")
	@echo "Hinweis: Werte in $(ENV_FILE) anpassen."

plan:
	@mkdir -p out
	@PYTHONPATH=$(PYTHONPATH) $(RUN) plan --start $(START) --end $(END) $(if $(SEED),--seed $(SEED),) --env-file $(ENV_FILE) --out $(OUT)

plan-explain:
	@mkdir -p out
	@PYTHONPATH=$(PYTHONPATH) $(RUN) plan --start $(START) --end $(END) $(if $(SEED),--seed $(SEED),) --env-file $(ENV_FILE) --out $(OUT) --explain

dry-plan:
	@mkdir -p out
	@PYTHONPATH=$(PYTHONPATH) $(RUN) plan --start $(START) --end $(END) $(if $(SEED),--seed $(SEED),) --env-file $(ENV_FILE) --out $(OUT) --dry-run --explain

test-send:
	@PYTHONPATH=$(PYTHONPATH) $(RUN) send 1 --env-file $(ENV_FILE) --explain

dry-send:
	@PYTHONPATH=$(PYTHONPATH) $(RUN) send 1 --env-file $(ENV_FILE) --dry-run --explain
