#!/usr/bin/env python3
from __future__ import annotations
import argparse
import datetime as dt
from pathlib import Path

from 10_config import DEFAULT_START, DEFAULT_END, TIME_WINDOWS, DEFAULT_SERVER
from 20_schedule import generate_schedule, save_schedule, load_schedule, pretty_print
from 30_send import load_env_file, send_ntfy


def parse_date(s: str) -> dt.date:
    return dt.datetime.strptime(s, "%Y-%m-%d").date()


def main():
    ap = argparse.ArgumentParser(
        description="ntfy Umfrage-Erinnerungen: planen (randomisiert) und senden."
    )
    ap.add_argument("--start", default=DEFAULT_START.isoformat(), help="Startdatum YYYY-MM-DD")
    ap.add_argument("--end", default=DEFAULT_END.isoformat(), help="Enddatum YYYY-MM-DD")
    ap.add_argument("--seed", type=int, default=None, help="Seed für reproduzierbare Randomisierung")
    ap.add_argument("--env-file", default="config/ntfy.env", help="Pfad zur env Datei (NTFY_*)")
    ap.add_argument("--server", default=DEFAULT_SERVER, help="ntfy server URL")
    ap.add_argument("--out", default="out/schedule.json", help="Output schedule JSON")
    ap.add_argument("--explain", action="store_true", help="Erklärt jeden Schritt (Seminar-Modus)")
    ap.add_argument("--dry-run", action="store_true", help="Nichts senden, nur planen/anzeigen")

    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("plan", help="Schedule erzeugen und speichern/anzeigen")
    send_p = sub.add_parser("send", help="Eine Nachricht senden (1..3) – typischerweise über systemd/cron")
    send_p.add_argument("id", type=int, choices=[1, 2, 3])

    send_all = sub.add_parser("send-all", help="Alle 3 Nachrichten sofort senden (Demo)")
    args = ap.parse_args()

    start = parse_date(args.start)
    end = parse_date(args.end)
    out_path = Path(args.out)

    if args.cmd == "plan":
        schedule = generate_schedule(start, end, TIME_WINDOWS, seed=args.seed, explain=args.explain)
        save_schedule(schedule, out_path)
        pretty_print(schedule)
        print(f"\nGespeichert in: {out_path}")

        if args.dry_run:
            print("\n[dry-run] Kein Versand, keine systemd-Aktionen.")
        return

    # ab hier: Versand
    env = load_env_file(args.env_file)

    if args.dry_run:
        print("[dry-run] Versand deaktiviert.")
        if args.cmd == "send":
            print(f"[dry-run] Würde Nachricht {args.id} senden.")
        else:
            print("[dry-run] Würde Nachrichten 1..3 senden.")
        return

    if args.cmd == "send":
        send_ntfy(args.id, env, args.server, explain=args.explain)
        print(f"OK: Nachricht {args.id} gesendet.")
        return

    if args.cmd == "send-all":
        for i in [1, 2, 3]:
            send_ntfy(i, env, args.server, explain=args.explain)
            print(f"OK: Nachricht {i} gesendet.")
        return


if __name__ == "__main__":
    main()
