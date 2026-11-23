"""Stato dei repository GitHub: pull request aperte e ultima CI."""
import urllib.error

from . import config
from .http import request_json

API = "https://api.github.com"


def _headers():
    headers = {"Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28",
               "User-Agent": "alexa-jarvis"}
    token = config.env("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _short(repo):
    return repo.split("/")[-1]


def open_pull_requests():
    repos = config.repos()
    if not repos:
        return "Non ho repository configurati. Imposta la variabile GITHUB_REPOS."
    parts, total = [], 0
    try:
        for repo in repos:
            prs = request_json(f"{API}/repos/{repo}/pulls?state=open&per_page=100",
                               headers=_headers())
            n = len(prs)
            total += n
            if n:
                parts.append(f"{n} su {_short(repo)}")
    except (urllib.error.URLError, TimeoutError):
        return "Non riesco a contattare GitHub in questo momento."
    if total == 0:
        return "Non hai pull request aperte."
    intro = "Hai una pull request aperta" if total == 1 else f"Hai {total} pull request aperte"
    return f"{intro}: " + ", ".join(parts) + "."


_CONCLUSIONS = {
    "success": "è passata",
    "failure": "è fallita",
    "cancelled": "è stata annullata",
    "timed_out": "è andata in timeout",
    "skipped": "è stata saltata",
    "action_required": "richiede un'azione",
}


def latest_ci():
    repos = config.repos()
    if not repos:
        return "Non ho repository configurati. Imposta la variabile GITHUB_REPOS."
    parts = []
    try:
        for repo in repos:
            data = request_json(f"{API}/repos/{repo}/actions/runs?per_page=1",
                                headers=_headers())
            runs = (data or {}).get("workflow_runs") or []
            if not runs:
                parts.append(f"{_short(repo)} non ha esecuzioni di CI")
                continue
            run = runs[0]
            if run.get("status") != "completed":
                esito = "è ancora in corso"
            else:
                esito = _CONCLUSIONS.get(run.get("conclusion"), "è terminata")
            parts.append(f"su {_short(repo)}, {run.get('name', 'la CI')} "
                         f"sul branch {run.get('head_branch', 'sconosciuto')} {esito}")
    except (urllib.error.URLError, TimeoutError):
        return "Non riesco a contattare GitHub in questo momento."
    return "Ultima CI: " + "; ".join(parts) + "."
