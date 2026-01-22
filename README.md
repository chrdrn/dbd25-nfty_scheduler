# ntfy Survey Reminder (Seminar-Version, cross-platform)

Dieses Projekt plant und verschickt **5 Push-Erinnerungen** (via **ntfy**) für eine Umfrage.
Standardmäßig werden Zeitpunkte **randomisiert** im Zeitraum **21.01–22.01** gewählt.
Der Default ist **mode=interval** mit **08:00–20:00** und **min_gap=60min**.

Optional kannst du **mode=windows** nutzen, z.B.:
- Fenster 1: **08:00–10:00**
- Fenster 2: **10:00–12:00**
- Fenster 3: **12:00–14:00**
- Fenster 4: **14:00–16:00**
- Fenster 5: **16:00–18:00**


Ziel: Studierende ohne Python-Vorkenntnisse sollen das Tool **auf Windows, macOS und Linux** nutzen können.

---

## Quickstart (funktioniert überall)

> Du brauchst nur Python und dieses Repo. Kein Makefile nötig.

Hinweis: Für eine Colab-Demo siehe `demo.ipynb`.

### 1) Repo klonen
```bash
git clone <REPO-URL>
cd ntfy-reminder
```

### 2) Virtuelle Umgebung erstellen (empfohlen)

#### Windows (PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### Windows (CMD)
```bat
py -m venv .venv
.\.venv\Scripts\activate.bat
```

#### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Prüfen:
```bash
python --version
```

### 3) Konfiguration anlegen
Kopiere die Beispiel-Konfiguration und passe sie an:

```bash
# macOS/Linux (oder Git Bash)
cp config/ntfy.env.example config/ntfy.env
```

```powershell
# Windows PowerShell
Copy-Item config\ntfy.env.example config\ntfy.env
```

Dann `config/ntfy.env` öffnen und Werte setzen:

- `NTFY_TOPIC`
- `NTFY_TITLE`
- `NTFY_MESSAGE`

In `NTFY_TITLE` und `NTFY_MESSAGE` dürfen Platzhalter vorkommen, z.B.:
- `{k}` = Reminder-Nummer innerhalb des Tages
- `{per_day}` = Reminder pro Tag
- `{id}` = globale ID
- `{url}` = Link aus `SURVEY_URL_TEMPLATE` (wenn gesetzt)
- `{n}` = Alias für `{k}` (Kompatibilität)

Beispiele:
- Titel: `Umfrage-Erinnerung {k}/{per_day}`
- Message: `Bitte nimm kurz an der Umfrage teil. (Reminder {k}/{per_day})`

### 4) Trockenlauf (Erklärmodus + kein Versand)
```bash
python run.py plan --dry-run --explain
```

### 5) Randomisiert planen
```bash
python run.py plan
```

Die geplanten Zeitpunkte stehen danach in:
- `out/schedule.json`

### 6) Test: Nachricht 1 wirklich senden
```bash
python run.py send 1 --explain
```

---

## Reproduzierbare Randomisierung (Seed)

Wenn alle im Kurs denselben Plan generieren sollen:

```bash
python run.py plan --seed 123
```

---

## Live-Demo (Jupyter / Colab)

Es gibt ein fertiges Notebook fuer eine sichere Demo ohne Versand:

- `demo.ipynb`

Local Jupyter: Notebook oeffnen und die Zellen ausfuehren.

Google Colab: Im Notebook die Clone-Zeile ausfuehren und `<REPO-URL>` ersetzen.

---

## Erklärmodus & Trockenlauf

- `--explain` erklärt Schritt für Schritt, was passiert (Seminar-Modus)
- `--dry-run` sendet nichts (nur anzeigen)

Beispiele:
```bash
python run.py plan --explain
python run.py send 2 --dry-run --explain
```

---

## Projektstruktur (didaktisch)

Empfohlenes Paket-Layout (für zuverlässige OS-Kompatibilität):

- `run.py`  
  Einstiegspunkt (CLI): planen/senden, erklärt/dry-run

- `ntfy_reminder/config.py`  
  Parameter/Regeln: Zeitraum, Zeitfenster, Defaults

- `ntfy_reminder/schedule.py`  
  Randomisierung + Erzeugung der 5 Zeitpunkte

- `ntfy_reminder/send.py`  
  Versand an ntfy über HTTP (Standardbibliothek)

---

## Git / Sicherheit

Die Datei `config/ntfy.env` enthält Konfiguration und wird **nicht committed**.
Sie steht absichtlich in `.gitignore`.

Vorlage:
- `config/ntfy.env.example`

---

## Optional: Makefile (nur macOS/Linux)

Ein Makefile ist komfortabel, aber **auf Windows nicht standardisiert**.
Wenn du Linux/macOS nutzt, kannst du (optional) Targets wie `make plan` anbieten.

Studierende auf Windows sollen stattdessen die `python run.py ...` Befehle nutzen.

---

## Optional: systemd (für Lehrende / Admin, Linux)

systemd ist Linux-spezifisch und daher **nicht Teil des studentischen Standard-Flows**.
Im Ordner `systemd/` können Beispiel-Units liegen, um Sendezeitpunkte automatisch auszuführen.

Logs ansehen (Beispiel):
```bash
journalctl --user -u ntfy-survey@1.service -n 50 --no-pager
```

---

## Häufige Stolpersteine

### Windows PowerShell: Aktivierung blockiert?
Falls die Aktivierung in PowerShell blockiert ist, nutze stattdessen CMD oder setze (einmalig) eine weniger restriktive Policy:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Zeitzone
Zeitpunkte orientieren sich an der lokalen Zeitzone des Rechners.

Linux:
```bash
timedatectl
```

Windows: Datum/Uhrzeit Einstellungen.

### Netzwerk / Firewall
Für den Versand muss der Rechner den ntfy-Server erreichen können (`https://ntfy.sh` oder eigener Server).

---

## Befehlsübersicht

Planen mit Zeitfenstern (statt Intervall):
```bash
python run.py plan --mode windows --windows "08:00-10:00,10:00-12:00,12:00-14:00,14:00-16:00,16:00-18:00"
```

Planen:
```bash
python run.py plan
python run.py plan --seed 123
python run.py plan --dry-run --explain
```

Senden:
```bash
python run.py send 1
python run.py send 2 --explain
python run.py send-all
```
