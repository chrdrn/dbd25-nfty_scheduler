from __future__ import annotations
import datetime as dt

# === Seminar: Hier stehen die "Regeln" / Parameter ===

# Zeitraum (Default). Du kannst das auch via CLI überschreiben.
DEFAULT_START = dt.date(2026, 1, 20)
DEFAULT_END   = dt.date(2026, 1, 22)

# Drei Nachrichten mit Zeitfenstern (Start inkl., Ende exklusiv)
# Nachricht 1: 08:00–10:00
# Nachricht 2: 12:00–14:00
# Nachricht 3: 16:00–18:00
TIME_WINDOWS = {
    1: (8, 10),
    2: (12, 14),
    3: (16, 18),
}

DEFAULT_SERVER = "https://ntfy.sh"

# Welche Umgebungsvariablen wir erwarten:
ENV_KEYS = ["NTFY_TOPIC", "NTFY_TITLE", "NTFY_MESSAGE"]
