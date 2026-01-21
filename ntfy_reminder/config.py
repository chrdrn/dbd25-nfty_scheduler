from __future__ import annotations
import datetime as dt

DEFAULT_START = dt.date(2026, 1, 21)
DEFAULT_END = dt.date(2026, 1, 22)

DEFAULT_SERVER = "https://ntfy.sh"

# Default-Planungsparameter
DEFAULT_PER_DAY = 5
DEFAULT_MIN_GAP_MINUTES = 60

# Default-Modus: "windows" oder "interval"
DEFAULT_MODE = "interval"

# Default Zeitfenster (für mode=windows)
# Format: "HH:MM-HH:MM,HH:MM-HH:MM"
DEFAULT_WINDOWS_SPEC = "08:00-10:00,10:00-12:00,12:00-14:00,14:00-16:00,16:00-18:00"

# Default Intervall (für mode=interval)
DEFAULT_INTERVAL_SPEC = "08:00-20:00"

ENV_KEYS = ["NTFY_TOPIC", "NTFY_TITLE", "NTFY_MESSAGE"]
