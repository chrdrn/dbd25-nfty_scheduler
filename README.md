# ntfy Survey Reminder (Seminar-Version)

Dieses Projekt plant und verschickt **3 Push-Erinnerungen** (via **ntfy**) für eine Umfrage.
Die Zeitpunkte werden **randomisiert** im Zeitraum **20.01–22.01** gewählt – unter folgenden Regeln:

- Nachricht 1: zwischen **08:00 und 10:00**
- Nachricht 2: zwischen **12:00 und 14:00**
- Nachricht 3: zwischen **16:00 und 18:00**

Das Repo ist bewusst „seminarfreundlich“ aufgebaut:
- Studierende müssen **keine Python-Expert*innen** sein
- es gibt einen **super-simple Modus** über `make`
- es gibt einen **Erklärmodus** (`--explain`)
- es gibt einen **Trockenlauf** (`--dry-run`)
- optional kann das Ganze mit **systemd** geplant/ausgeführt werden (für Lehrende / Admin)

---

## Voraussetzungen

- Linux / Ubuntu (empfohlen) oder macOS  
  (Windows funktioniert über WSL ebenfalls gut)
- `python3`
- `make` (oft bereits vorhanden)

Prüfen:
```bash
python3 --version
make --version
```

---

## (Empfohlen) Virtuelle Python-Umgebung (.venv)

Auch wenn dieses Projekt **keine zusätzlichen Python-Pakete** benötigt, ist eine `.venv` sinnvoll:

- gleiche Umgebung für alle im Seminar
- weniger „bei mir geht’s nicht“-Probleme
- sauberer Standard in Python-Projekten
- später problemlos erweiterbar (falls doch Pakete dazukommen)

### `.venv` erstellen
```bash
python3 -m venv .venv
```

### `.venv` aktivieren
```bash
source .venv/bin/activate
```

### `.venv` deaktivieren
```bash
deactivate
```

> Hinweis: In diesem Projekt ist `.venv` optional.  
> Das Makefile nutzt automatisch `.venv/bin/python`, wenn die `.venv` existiert.

---

## Schnellstart (für Studierende)

### 1) Repo klonen
```bash
git clone <REPO-URL>
cd ntfy-reminder
```

### 2) Virtuelle Umgebung anlegen (empfohlen)
```bash
make venv
```

### 3) Konfiguration anlegen
```bash
make setup
```

Das erzeugt `config/ntfy.env` (nicht im Git, wegen `.gitignore`).
Öffne diese Datei und setze die Werte:

- `NTFY_TOPIC`
- `NTFY_TITLE`
- `NTFY_MESSAGE`

In `NTFY_TITLE` und `NTFY_MESSAGE` darf `{n}` vorkommen, z.B.:
- Titel: `Umfrage-Erinnerung {n}/3`
- Message: `Bitte nimm kurz an der Umfrage teil. (Reminder {n}/3)`

### 4) Trockenlauf (Erklärmodus + kein Versand)
```bash
make dry-plan
```

### 5) Randomisiert planen
```bash
make plan
```

Die geplanten Zeitpunkte stehen danach in:
- `out/schedule.json`

### 6) Test: Nachricht 1 wirklich senden
```bash
make test-send
```

---

## Reproduzierbare Randomisierung (Seed)

Wenn alle im Kurs denselben Plan generieren sollen:

```bash
make plan SEED=123
```

---

## Erklärmodus & Trockenlauf

### Erklärmodus
Erklärt Schritt für Schritt, was passiert (ideal fürs Seminar):

```bash
make plan-explain
```

### Trockenlauf (sendet nichts)
```bash
make dry-plan
make dry-send
```

---

## Manuelle Nutzung ohne Makefile (optional)

Plan erzeugen:
```bash
PYTHONPATH=src python3 -m 00_run plan --start 2026-01-20 --end 2026-01-22 --explain
```

Nachricht senden:
```bash
PYTHONPATH=src python3 -m 00_run send 1 --env-file config/ntfy.env --explain
```

---

## Projektstruktur (didaktisch)

Die Dateien sind nummeriert, damit man sie im Seminar nacheinander erklären kann:

- `src/10_config.py`  
  Parameter / Regeln: Zeitraum & Zeitfenster

- `src/20_schedule.py`  
  Randomisierung + Erzeugung der 3 Zeitpunkte

- `src/30_send.py`  
  Versand an ntfy über HTTP

- `src/00_run.py`  
  Einstiegspunkt (steuert alles)

---

## Git / Sicherheit

Die Datei `config/ntfy.env` enthält Konfiguration und wird **nicht committed**.
Sie steht absichtlich in `.gitignore`.

Vorlage:
- `config/ntfy.env.example`

---

## Optional: systemd (für Lehrende / Admin)

Im Ordner `systemd/` liegen Beispiel-Dateien, um die Erinnerungen über systemd Timer auszuführen.

Typischer Admin-Workflow:
1) `make plan` → erzeugt `out/schedule.json`
2) Timer-Zeitpunkte daraus übernehmen
3) systemd Timer aktivieren

Logs ansehen (Beispiel):
```bash
journalctl --user -u ntfy-survey@1.service -n 50 --no-pager
```

---

## Makefile Targets (Übersicht)

```bash
make help
```

Wichtige Targets:

- `make venv` – erzeugt `.venv`
- `make setup` – erstellt `config/ntfy.env`
- `make plan` – randomisiert planen
- `make plan-explain` – planen mit Erklärung
- `make dry-plan` – planen ohne Versand
- `make test-send` – Nachricht 1 senden
- `make dry-send` – zeigt nur, was gesendet würde
```

---

## Hinweise / typische Stolpersteine

### 1) Cron vs. systemd
In diesem Repo ist **systemd optional**.
Für Studierende reicht es normalerweise, Nachrichten „manuell“ oder als Demo zu senden.

### 2) Zeitzone
Zeitpunkte orientieren sich an der lokalen Zeitzone des Rechners.
Prüfen unter Linux:
```bash
timedatectl
```

### 3) Netzwerk / Firewall
Für den Versand muss der Rechner den ntfy-Server erreichen können (`https://ntfy.sh` oder eigener Server.
