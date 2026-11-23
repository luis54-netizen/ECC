"""Comandi domotici inoltrati all'API conversazionale di Home Assistant (Assist)."""
import urllib.error

from . import config
from .http import request_json


def command(text):
    base = config.env("HA_URL").rstrip("/")
    token = config.env("HA_TOKEN")
    if not base or not token:
        return "Home Assistant non è configurato. Imposta HA_URL e HA_TOKEN."
    try:
        data = request_json(
            f"{base}/api/conversation/process",
            headers={"Authorization": f"Bearer {token}"},
            body={"text": text, "language": config.env("HA_LANGUAGE", "it")},
        )
    except (urllib.error.URLError, TimeoutError):
        return "Non riesco a raggiungere Home Assistant."
    speech = (((data or {}).get("response") or {}).get("speech") or {}).get("plain") or {}
    return speech.get("speech") or "Fatto."
