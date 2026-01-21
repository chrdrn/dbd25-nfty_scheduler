#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
from pathlib import Path
from typing import Optional, Tuple

from ntfy_reminder.config import (
    DEFAULT_START,
    DEFAULT_END,
    DEFAULT_SERVER,
    DEFAULT_PER_DAY,
    DEFAULT_MIN_GAP_MINUTES,
    DEFAULT_MODE,
    DEFAULT_WINDOWS_SPEC,
    DEFAULT_INTERVAL_SPEC,
)
from ntfy_reminder.schedule import (
    generate_schedule,
    save_schedule,
    pretty_print,
    parse_windows,
    parse_hhmm,
    load_schedule,
)
from ntfy_reminder.send import load_env_file, send_ntfy


def parse_date(s: str) -> dt.date:
    return dt.datetime.strptime(s, "%Y-%m-%d").date()


def parse_interval_spec(spec: str) -> Tuple[dt.time, dt.time]:
    # "HH:MM-HH:MM"
    a, b = spec.split("-", 1)
    return parse_hhmm(a.strip()), parse_hhmm(b.strip())


def derive_seed(base_seed: Optional[int], participant_id: Optional[str], explain: bool = False) -> Optional[int]:
    """
    Liefert einen stabilen Seed:
    - wenn base_seed gesetzt und participant_id gesetzt: kombiniert beide deterministisch
    - wenn nur participant_id gesetzt: Seed aus participant_id
    - wenn nur base_seed gesetzt: base_seed
    - wenn nichts gesetzt: None (echte Randomness)
    """
    if base_seed is None and not participant_id:
        return None

    if participant_id:
        h = hashlib.sha256(participant_id.encode("utf-8")).hexdigest()
        pid_int = int(h[:12], 16)  # 48-bit reichen
        if base_seed is None:
            seed = pid_int
        else:
            seed = (base_seed * 1_000_003) ^ pid_int
        if explain:
            print(f"[explain] participant_id='{participant_id}' -> pid_hash_int={pid_int}")
            print(f"[explain] final seed={seed} (base_seed={base_seed})")
        return seed

    return base_seed


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="ntfy Umfrage-Erinnerungen: planen (randomisiert) und senden."
    )

    # Allgemeine Parameter (gelten für alle Subcommands)
    ap.add_argument("--start", default=DEFAULT_START.isoformat(), help="Startdatum YYYY-MM-DD")
    ap.add_argument("--end", default=DEFAULT_END.isoformat(), help="Enddatum YYYY-MM-DD")

    ap.add_argument("--per-day", type=int, default=DEFAULT_PER_DAY, help="Anzahl Reminder pro Tag")
    ap.add_argument("--min-gap", type=int, default=DEFAULT_MIN_GAP_MINUTES, help="Mindestabstand in Minuten")

    ap.add_argument(
        "--mode",
        choices=["windows", "interval"],
        default=DEFAULT_MODE,
        help="Planungsmodus: windows (Zeitfenster) oder interval (ein großes Intervall)",
    )

    ap.add_argument(
        "--windows",
        default=DEFAULT_WINDOWS_SPEC,
        help='Zeitfenster (für mode=windows), z.B. "08:00-10:00,12:00-14:00"',
    )
    ap.add_argument(
        "--interval",
        default=DEFAULT_INTERVAL_SPEC,
        help='Intervall (für mode=interval), z.B. "08:00-18:00"',
    )

    # Randomisierung / Personalisierung
    ap.add_argument("--seed", type=int, default=None, help="Seed für reproduzierbare Randomisierung")
    ap.add_argument(
        "--participant-id",
        default=None,
        help="ID pro Versuchsperson (z.B. Probandencode). Variiert den Schedule deterministisch.",
    )

    # IO
    ap.add_argument("--env-file", default="config/ntfy.env", help="Pfad zur env Datei (NTFY_*)")
    ap.add_argument("--server", default=DEFAULT_SERVER, help="ntfy server URL")
    ap.add_argument("--out", default="out/schedule.json", help="Output schedule JSON")

    sub = ap.add_subparsers(dest="cmd", required=True)

    # plan subcommand
    plan_p = sub.add_parser("plan", help="Schedule erzeugen und speichern/anzeigen")
    plan_p.add_argument("--explain", action="store_true", help="Erklärt jeden Schritt (Seminar-Modus)")
    plan_p.add_argument("--dry-run", action="store_true", help="Nichts senden, nur planen/anzeigen")

    # send subcommand
    send_p = sub.add_parser("send", help="Eine Nachricht senden (ID)")
    send_p.add_argument("id", type=int, help="Nachrichten-ID aus dem Schedule (z.B. 1..N)")
    send_p.add_argument("--explain", action="store_true", help="Erklärt den Versand (Seminar-Modus)")
    send_p.add_argument("--dry-run", action="store_true", help="Nichts senden, nur anzeigen")

    # send-all subcommand
    sendall_p = sub.add_parser("send-all", help="Alle Reminder aus out/schedule.json senden (Demo)")
    sendall_p.add_argument("--explain", action="store_true", help="Erklärt den Versand (Seminar-Modus)")
    sendall_p.add_argument("--dry-run", action="store_true", help="Nichts senden, nur anzeigen")

    return ap


def _build_payload(schedule: dict, item: dict) -> dict:
    """
    Erzeuge ein payload Dict für Template-Platzhalter:
      {id}, {day}, {k}, {per_day}, {when}, {time}, {url}
    """
    return {
        "id": str(item.get("id", "")),
        "day": str(item.get("day", "")),
        "k": str(item.get("k", "")),
        "n": str(item.get("k", "")),
        "per_day": str(item.get("per_day", schedule.get("per_day", ""))),
        "when": str(item.get("when", "")),
        "time": str(item.get("time", "")),
        # url wird später ergänzt
        "url": "",
    }


def main():
    ap = build_parser()
    args = ap.parse_args()

    start = parse_date(args.start)
    end = parse_date(args.end)
    if start > end:
        raise SystemExit(f"Startdatum {start.isoformat()} ist nach Enddatum {end.isoformat()}.")
    out_path = Path(args.out)

    # Seed ableiten (base_seed + participant_id)
    explain_flag = bool(getattr(args, "explain", False))
    seed = derive_seed(args.seed, args.participant_id, explain=explain_flag)

    if args.cmd == "plan":
        if args.mode == "windows":
            windows = parse_windows(args.windows)
            schedule = generate_schedule(
                start_date=start,
                end_date=end,
                per_day=args.per_day,
                min_gap_minutes=args.min_gap,
                mode="windows",
                windows=windows,
                seed=seed,
                explain=args.explain,
            )
        else:
            interval = parse_interval_spec(args.interval)
            schedule = generate_schedule(
                start_date=start,
                end_date=end,
                per_day=args.per_day,
                min_gap_minutes=args.min_gap,
                mode="interval",
                interval=interval,
                seed=seed,
                explain=args.explain,
            )

        save_schedule(schedule, out_path)
        pretty_print(schedule)
        print(f"\nGespeichert in: {out_path}")

        if args.dry_run:
            print("\n[dry-run] Kein Versand.")
        return

    # ab hier: Versand
    env = load_env_file(args.env_file)
    server = args.server
    env_server = str(env.get("NTFY_SERVER", "")).strip()
    if env_server and args.server == DEFAULT_SERVER:
        server = env_server

    # Optional: Markdown für ntfy Web-App (nicht überall gerendert)
    markdown_flag = str(env.get("NTFY_MARKDOWN", "")).strip().lower() in {"1", "true", "yes", "y"}

    # Survey-Link Template aus env (empfohlen)
    # Beispiel: https://www.soscisurvey.de/DEINPROJEKT/?r={id}
    survey_tpl = str(env.get("SURVEY_URL_TEMPLATE", "")).strip()

    if getattr(args, "dry_run", False):
        if args.cmd == "send":
            print(f"[dry-run] Würde Reminder ID {args.id} senden.")
        else:
            print("[dry-run] Würde alle Reminder senden.")
        return

    if args.cmd == "send":
        schedule = load_schedule(out_path)
        item = next((it for it in schedule.get("items", []) if int(it.get("id", -1)) == int(args.id)), None)
        if not item:
            raise SystemExit(f"ID {args.id} nicht im Schedule gefunden ({out_path}).")

        payload = _build_payload(schedule, item)

        # Survey URL bauen und in payload schreiben
        survey_url = survey_tpl.format(**payload) if survey_tpl else ""
        payload["url"] = survey_url

        send_ntfy(
            payload,
            env,
            server,
            explain=args.explain,
            click_url=survey_url or None,   # Click Header setzen (öffnet URL beim Tap)
            markdown=markdown_flag,
        )
        print(f"OK: Reminder ID {args.id} gesendet.")
        return

    if args.cmd == "send-all":
        schedule = load_schedule(out_path)

        for item in schedule.get("items", []):
            payload = _build_payload(schedule, item)

            survey_url = survey_tpl.format(**payload) if survey_tpl else ""
            payload["url"] = survey_url

            send_ntfy(
                payload,
                env,
                server,
                explain=args.explain,
                click_url=survey_url or None,
                markdown=markdown_flag,
            )
            print(f"OK: Reminder ID {payload['id']} gesendet.")
        return


if __name__ == "__main__":
    main()
