#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Set, Optional


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def floor_to_minute(t: dt.datetime) -> dt.datetime:
    return t.replace(second=0, microsecond=0)


def derive_paths_from_project(project: str) -> tuple[str, str, str]:
    """
    Konvention:
      schedule: out/<project>_schedule.json
      sent:     out/<project>_sent.json
      env:      config/<project>.env
    """
    return (
        f"out/{project}_schedule.json",
        f"out/{project}_sent.json",
        f"config/{project}.env",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Send due reminders based on schedule.json (exactly once).")

    # Komfort: ein Projektname statt drei Pfade
    ap.add_argument("--project", default=None,
                    help="Projektname; nutzt out/<p>_schedule.json, out/<p>_sent.json, config/<p>.env")

    # Explizite Pfade (optional, wenn project nicht genutzt wird)
    ap.add_argument("--schedule", default=None, help="Path to schedule.json")
    ap.add_argument("--sent", default=None, help="Path to sent-state file (sent.json)")
    ap.add_argument("--env-file", default=None, help="env file (NTFY_* + SURVEY_URL_TEMPLATE)")

    # Ausführung / Wiring
    ap.add_argument("--runpy", required=True, help="Path to run.py")
    ap.add_argument("--python", required=True, help="Python executable to use")
    ap.add_argument("--server", default=None, help="Optional ntfy server override")

    # Timing/Debug
    ap.add_argument("--grace-minutes", type=int, default=2,
                    help="Send reminders within [now-grace, now] minutes (timer drift).")
    ap.add_argument("--dry-run", action="store_true", help="Do not send, only print what would be sent.")
    ap.add_argument("--explain", action="store_true", help="Verbose output.")
    args = ap.parse_args()

    # --- Pfade auflösen ---
    schedule_s: Optional[str] = args.schedule
    sent_s: Optional[str] = args.sent
    env_s: Optional[str] = args.env_file

    if args.project:
        schedule_s, sent_s, env_s = derive_paths_from_project(args.project)

    if not schedule_s or not sent_s or not env_s:
        raise SystemExit(
            "Fehlende Pfade. Nutze entweder:\n"
            "  --project <name>\n"
            "oder gib alle drei an:\n"
            "  --schedule ... --sent ... --env-file ...\n"
        )

    schedule_path = Path(schedule_s)
    sent_path = Path(sent_s)
    env_file = env_s  # string

    if not schedule_path.exists():
        print(f"[dispatch] schedule not found: {schedule_path}")
        return 2

    schedule = load_json(schedule_path)
    items = schedule.get("items", [])

    sent_ids: Set[int] = set()
    if sent_path.exists():
        sent = load_json(sent_path)
        sent_ids = set(int(x) for x in sent.get("sent_ids", []))
    else:
        sent = {"sent_ids": [], "updated_at": ""}

    now = floor_to_minute(dt.datetime.now())
    grace = dt.timedelta(minutes=max(0, args.grace_minutes))
    earliest = now - grace

    due = []
    for it in items:
        try:
            rid = int(it["id"])
            when = floor_to_minute(dt.datetime.fromisoformat(it["when"]))
        except Exception:
            continue

        if rid in sent_ids:
            continue

        if earliest <= when <= now:
            due.append((when, rid))

    due.sort()

    if args.explain:
        proj = args.project if args.project else "(explicit paths)"
        print(f"[dispatch] project={proj}")
        print(f"[dispatch] schedule={schedule_path}")
        print(f"[dispatch] sent={sent_path}")
        print(f"[dispatch] now={now.isoformat(timespec='minutes')} earliest={earliest.isoformat(timespec='minutes')}")
        print(f"[dispatch] due_count={len(due)}")

    if not due:
        return 0

    for when, rid in due:
        # WICHTIG: globale run.py Optionen VOR dem Subcommand "send"
        cmd = [
            args.python,
            args.runpy,
            "--env-file", env_file,
            "--out", str(schedule_path),
        ]
        if args.server:
            cmd += ["--server", args.server]

        cmd += ["send", str(rid)]

        if args.explain:
            cmd += ["--explain"]

        if args.dry_run:
            print(f"[dry-run] would send id={rid} scheduled={when.isoformat(timespec='minutes')}")
            continue

        if args.explain:
            print(f"[dispatch] sending id={rid} scheduled={when.isoformat(timespec='minutes')}")
            print(f"[dispatch] cmd: {' '.join(cmd)}")

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[dispatch] ERROR sending id={rid} (rc={res.returncode})")
            if res.stdout:
                print(res.stdout.rstrip())
            if res.stderr:
                print(res.stderr.rstrip())
            continue  # nicht als sent markieren

        sent_ids.add(rid)

    sent["sent_ids"] = sorted(sent_ids)
    sent["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")
    save_json(sent_path, sent)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
