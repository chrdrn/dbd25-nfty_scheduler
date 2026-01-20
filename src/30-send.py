from __future__ import annotations
import os
import urllib.request
from typing import Dict


def load_env_file(env_path: str) -> Dict[str, str]:
    """
    Minimaler .env Loader für Zeilen wie:
      export KEY="VALUE"
      KEY=VALUE
    Kommentare (# ...) werden ignoriert.
    """
    env: Dict[str, str] = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):].strip()
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            env[k] = v
    return env


def send_ntfy(message_id: int, env: Dict[str, str], server: str, explain: bool = False) -> None:
    """
    Sendet per HTTP POST an ntfy.
    Erwartet env keys:
      NTFY_TOPIC, NTFY_TITLE, NTFY_MESSAGE
    Unterstützt {n} in TITLE/MESSAGE.
    """
    topic = env.get("NTFY_TOPIC")
    title_tpl = env.get("NTFY_TITLE")
    msg_tpl = env.get("NTFY_MESSAGE")

    missing = [k for k in ["NTFY_TOPIC", "NTFY_TITLE", "NTFY_MESSAGE"] if not env.get(k)]
    if missing:
        raise RuntimeError(f"Fehlende Werte in env: {', '.join(missing)}")

    title = title_tpl.format(n=message_id)
    body = msg_tpl.format(n=message_id)

    url = f"{server.rstrip('/')}/{topic}"
    data = body.encode("utf-8")

    if explain:
        print(f"[explain] Sende an: {url}")
        print(f"[explain] Title: {title}")
        print(f"[explain] Body : {body}")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Title", title)
    req.add_header("Content-Type", "text/plain; charset=utf-8")

    with urllib.request.urlopen(req, timeout=20) as resp:
        _ = resp.read()
