from __future__ import annotations

import datetime as dt
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class TimeWindow:
    start: dt.time  # inclusive
    end: dt.time    # exclusive

    def minutes_range(self) -> Tuple[int, int]:
        """Return (start_minute, end_minute) end exclusive, minutes since 00:00."""
        s = self.start.hour * 60 + self.start.minute
        e = self.end.hour * 60 + self.end.minute
        return s, e


def daterange(start: dt.date, end: dt.date):
    cur = start
    while cur <= end:
        yield cur
        cur += dt.timedelta(days=1)


def parse_hhmm(s: str) -> dt.time:
    """
    Parse 'HH:MM' into datetime.time.
    """
    try:
        h, m = s.split(":")
        return dt.time(int(h), int(m))
    except Exception as e:
        raise ValueError(f"Ungültiges Zeitformat '{s}'. Erwartet HH:MM (z.B. 08:30).") from e


def parse_windows(spec: str) -> List[TimeWindow]:
    """
    spec like: "08:00-10:00,12:00-14:00,16:00-18:00"
    """
    windows: List[TimeWindow] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" not in part:
            raise ValueError(f"Ungültiges Fenster '{part}'. Erwartet HH:MM-HH:MM.")
        a, b = part.split("-", 1)
        windows.append(TimeWindow(parse_hhmm(a.strip()), parse_hhmm(b.strip())))
    if not windows:
        raise ValueError("Keine gültigen Zeitfenster gefunden.")
    return windows


def windows_to_minute_slots(windows: List[TimeWindow]) -> List[int]:
    """
    Returns sorted allowed minutes-of-day (0..1439) where reminders may start.
    Minute granularity.
    """
    allowed: List[int] = []
    for w in windows:
        s, e = w.minutes_range()
        if e <= s:
            raise ValueError(f"Ungültiges Fenster (Ende <= Start): {w.start}-{w.end}")
        allowed.extend(range(s, e))
    return sorted(set(allowed))


def interval_to_windows(start: dt.time, end: dt.time) -> List[TimeWindow]:
    return [TimeWindow(start, end)]


def feasible_or_raise(allowed_minutes: List[int], per_day: int, min_gap: int):
    if per_day <= 0:
        raise ValueError("per_day muss >= 1 sein.")
    if min_gap < 0:
        raise ValueError("min_gap_minutes muss >= 0 sein.")
    if not allowed_minutes:
        raise ValueError("Keine erlaubten Minuten im Intervall/Fenstern.")

    # quick feasibility bound (necessary condition, not always sufficient but good guard)
    available = len(allowed_minutes)
    needed = per_day + (per_day - 1) * min_gap
    if needed > available:
        raise ValueError(
            f"Unmöglich: per_day={per_day} mit min_gap={min_gap}min braucht ca. {needed} Minuten Platz, "
            f"aber nur {available} Minuten sind erlaubt. "
            "=> min_gap reduzieren oder Fenster/Intervall vergrößern oder per_day reduzieren."
        )


def pick_times_for_day(
    day: dt.date,
    allowed_minutes: List[int],
    per_day: int,
    min_gap: int,
    rng: random.Random,
    explain: bool = False,
    max_attempts: int = 5000,
) -> List[dt.datetime]:
    """
    Rejection sampling with constraint check.
    Picks per_day times on 'day' such that distance between any two is >= min_gap.
    """
    feasible_or_raise(allowed_minutes, per_day, min_gap)

    def ok(candidate: int, chosen: List[int]) -> bool:
        return all(abs(candidate - c) >= min_gap for c in chosen)

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        chosen: List[int] = []
        pool = allowed_minutes[:]  # copy
        rng.shuffle(pool)

        for minute in pool:
            if ok(minute, chosen):
                chosen.append(minute)
                if len(chosen) == per_day:
                    chosen.sort()
                    if explain:
                        hhmm = ", ".join(f"{m//60:02d}:{m%60:02d}" for m in chosen)
                        print(f"[explain] {day.isoformat()}: gewählt -> {hhmm}")
                    return [
                        dt.datetime.combine(day, dt.time(minute // 60, minute % 60))
                        for minute in chosen
                    ]

        if explain and attempts % 500 == 0:
            print(f"[explain] noch kein gültiger Satz für {day.isoformat()} nach {attempts} Versuchen...")

    raise RuntimeError(
        f"Konnte für {day.isoformat()} nach {max_attempts} Versuchen keinen gültigen Schedule finden. "
        "=> min_gap reduzieren oder erlaubte Zeitfenster vergrößern."
    )


def generate_schedule(
    start_date: dt.date,
    end_date: dt.date,
    per_day: int,
    min_gap_minutes: int,
    mode: str,
    interval: Optional[Tuple[dt.time, dt.time]] = None,
    windows: Optional[List[TimeWindow]] = None,
    seed: Optional[int] = None,
    explain: bool = False,
) -> Dict[str, Any]:
    rng = random.Random(seed)
    if explain and seed is not None:
        print(f"[explain] Seed gesetzt auf: {seed}")

    if mode not in {"interval", "windows"}:
        raise ValueError("mode muss 'interval' oder 'windows' sein.")

    if mode == "interval":
        if not interval:
            raise ValueError("Für mode='interval' muss interval=(start,end) gesetzt sein.")
        win = interval_to_windows(interval[0], interval[1])
    else:
        if not windows:
            raise ValueError("Für mode='windows' muss windows=[...] gesetzt sein.")
        win = windows

    allowed = windows_to_minute_slots(win)
    if explain:
        print(f"[explain] erlaubte Minuten pro Tag: {len(allowed)} (aus {len(win)} Fenster(n))")

    items: List[Dict[str, Any]] = []
    next_id = 1

    for day in daterange(start_date, end_date):
        times = pick_times_for_day(day, allowed, per_day, min_gap_minutes, rng, explain=explain)
        # times sind sortiert (pick_times_for_day sortiert die Minuten), daher ist k stabil
        for k, t in enumerate(times, start=1):
            when = t.isoformat(timespec="minutes")
            items.append({
                "id": next_id,                    # globale ID (1..N)
                "day": day.isoformat(),           # "YYYY-MM-DD"
                "k": k,                           # 1..per_day innerhalb des Tages
                "per_day": per_day,               # für Templates
                "when": when,                     # "YYYY-MM-DDTHH:MM"
                "time": t.strftime("%H:%M"),      # "HH:MM"
            })
            next_id += 1

    return {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "per_day": per_day,
        "min_gap_minutes": min_gap_minutes,
        "mode": mode,
        "items": items,
    }


def save_schedule(schedule: Dict[str, Any], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schedule, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_schedule(path: Path) -> Dict[str, Any]:
    """
    Lädt eine zuvor gespeicherte schedule.json wieder ein.
    (Wird z.B. für `send-all` verwendet.)
    """
    return json.loads(path.read_text(encoding="utf-8"))


def pretty_print(schedule: Dict[str, Any]):
    print("Geplante Zeitpunkte:")
    for item in schedule["items"]:
        print(f"  ID {item['id']}: {item['day']} #{item['k']}/{item['per_day']} @ {item['time']} ({item['when']})")

