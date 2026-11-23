"""Configurazione letta dalle variabili d'ambiente della Lambda."""
import os


def env(name, default=""):
    return os.environ.get(name, default).strip()


def repos():
    return [r.strip() for r in env("GITHUB_REPOS").split(",") if r.strip()]
