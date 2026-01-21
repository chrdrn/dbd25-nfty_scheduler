# ntfy Survey Reminder (Seminar-Version, cross-platform)

Dieses Projekt plant und verschickt **3 Push-Erinnerungen** (via **ntfy**) für eine Umfrage.
Die Zeitpunkte werden **randomisiert** im Zeitraum **20.01–22.01** gewählt – unter folgenden Regeln:

- Nachricht 1: zwischen **08:00 und 10:00**
- Nachricht 2: zwischen **12:00 und 14:00**
- Nachricht 3: zwischen **16:00 und 18:00**

Ziel: Studierende ohne Python-Vorkenntnisse sollen das Tool **auf Windows, macOS und Linux** nutzen können.

---

## Quickstart (funktioniert überall)

> Du brauchst nur Python und dieses Repo. Kein Makefile nötig.

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

In `NTFY_TITLE` und `NTFY_MESSAGE` darf `{n}` vorkommen, z.B.:
- Titel: `Umfrage-Erinnerung {n}/3`
- Message: `Bitte nimm kurz an der Umfrage teil. (Reminder {n}/3)`

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
  Randomisierung + Erzeugung der 3 Zeitpunkte

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
