"""Piccolo client JSON su urllib, per non aggiungere dipendenze alla Lambda."""
import json
import urllib.request


def request_json(url, headers=None, body=None, timeout=4.0):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {},
                                 method="POST" if data is not None else "GET")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode() or "null")
