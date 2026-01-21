from __future__ import annotations
import urllib.request
from typing import Dict, Optional


def load_env_file(env_path: str) -> Dict[str, str]:
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


def send_ntfy(
    payload: Dict[str, str],
    env: Dict[str, str],
    server: str,
    explain: bool = False,
    click_url: Optional[str] = None,
    markdown: bool = False,
) -> None:
    """
    payload: Dict mit Variablen für Templates (z.B. id/day/k/per_day/time/when/url)
    click_url: setzt den ntfy Click/X-Click Header (öffnet URL beim Tap) :contentReference[oaicite:2]{index=2}
    markdown: setzt Markdown Header (Web-App only, optional) :contentReference[oaicite:3]{index=3}
    """
    topic = env.get("NTFY_TOPIC")
    title_tpl = env.get("NTFY_TITLE")
    msg_tpl = env.get("NTFY_MESSAGE")

    missing = [k for k in ["NTFY_TOPIC", "NTFY_TITLE", "NTFY_MESSAGE"] if not env.get(k)]
    if missing:
        raise RuntimeError(f"Fehlende Werte in env: {', '.join(missing)}")

    try:
        title = title_tpl.format(**payload)
        body = msg_tpl.format(**payload)
    except KeyError as e:
        raise RuntimeError(
            f"Template-Platzhalter fehlt: {e}. Verfügbare Keys: {', '.join(sorted(payload.keys()))}"
        ) from e

    url = f"{server.rstrip('/')}/{topic}"
    data = body.encode("utf-8")

    if explain:
        print(f"[explain] POST {url}")
        print(f"[explain] Title: {title}")
        if click_url:
            print(f"[explain] Click: {click_url}")
        print(f"[explain] Body:\n{body}")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Title", title)
    req.add_header("Content-Type", "text/plain; charset=utf-8")

    # Click action (alias für X-Click) :contentReference[oaicite:4]{index=4}
    if click_url:
        req.add_header("Click", click_url)

        # Action Button (Button in der Notification) – Label bitte ASCII, sonst ggf. 400
        req.add_header("Actions", f"view, Umfrage starten, {click_url}")

    # Markdown (optional; Web-App only) :contentReference[oaicite:5]{index=5}
    if markdown:
        req.add_header("Markdown", "yes")

    with urllib.request.urlopen(req, timeout=20) as resp:
        _ = resp.read()
