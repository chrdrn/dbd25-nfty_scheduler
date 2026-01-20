from __future__ import annotations
import datetime as dt
import json
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


def daterange(start: dt.date, end: dt.date):
    cur = start
    while cur <= end:
        yield cur
        cur += dt.timedelta(days=1)


def random_time_in_window(day: dt.date, start_hour: int, end_hour: int) -> dt.datetime:
    """
    Zufallszeitpunkt innerhalb [start_hour:00, end_hour:00), Ende ist exklusiv.
    Beispiel 08-10 => 08:00 bis 09:59.
    """
    start = dt.datetime.combine(day, dt.time(hour=start_hour, minute=0))
    end = dt.datetime.combine(day, dt.time(hour=end_hour, minute=0))
    minutes = int((end - start).total_seconds() // 60)
    return start + dt.timedelta(minutes=random.randrange(minutes))


def generate_schedule(
    start_date: dt.date,
    end_date: dt.date,
    windows: Dict[int, Tuple[int, int]],
    seed: Optional[int] = None,
    explain: bool = False,
) -> Dict[str, Any]:
    """
    Erzeugt 3 geplante Zeitpunkte im Zeitraum start_date..end_date (inkl.) gemäß windows.
    Zusätzlich gilt: msg2 liegt an einem Tag >= msg1, msg3 an einem Tag >= msg2.
    """
    if seed is not None:
        random.seed(seed)
        if explain:
            print(f"[explain] Seed gesetzt auf: {seed}")

    days = list(daterange(start_date, end_date))
    if not days:
        raise ValueError("Ungültiger Zeitraum: start_date > end_date")

    if explain:
        print(f"[explain] Zeitraum: {start_date.isoformat()} bis {end_date.isoformat()} ({len(days)} Tage)")

    # Nachricht 1
    d1 = random.choice(days)
    h1s, h1e = windows[1]
    t1 = random_time_in_window(d1, h1s, h1e)
    if explain:
        print(f"[explain] Nachricht 1: Tag gezogen = {d1.isoformat()}, Zeitfenster = {h1s:02d}-{h1e:02d}")

    # Nachricht 2 (Tag >= d1)
    days2 = [d for d in days if d >= d1]
    d2 = random.choice(days2)
    h2s, h2e = windows[2]
    t2 = random_time_in_window(d2, h2s, h2e)
    if explain:
        print(f"[explain] Nachricht 2: Tag gezogen = {d2.isoformat()} (>= {d1.isoformat()}), Zeitfenster = {h2s:02d}-{h2e:02d}")

    # Nachricht 3 (Tag >= d2)
    days3 = [d for d in days if d >= d2]
    d3 = random.choice(days3)
    h3s, h3e = windows[3]
    t3 = random_time_in_window(d3, h3s, h3e)
    if explain:
        print(f"[explain] Nachricht 3: Tag gezogen = {d3.isoformat()} (>= {d2.isoformat()}), Zeitfenster = {h3s:02d}-{h3e:02d}")

    schedule = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "items": [
            {"id": 1, "when": t1.isoformat(timespec="minutes")},
            {"id": 2, "when": t2.isoformat(timespec="minutes")},
            {"id": 3, "when": t3.isoformat(timespec="minutes")},
        ],
    }
    return schedule


def save_schedule(schedule: Dict[str, Any], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schedule, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_schedule(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pretty_print(schedule: Dict[str, Any]):
    print("Geplante Zeitpunkte:")
    for item in schedule["items"]:
        print(f"  Nachricht {item['id']}: {item['when']}")
