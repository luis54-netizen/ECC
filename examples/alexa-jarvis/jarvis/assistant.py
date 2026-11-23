"""Domande libere a Claude, con risposte brevi adatte alla voce."""
import anthropic

from . import config

SYSTEM_PROMPT = (
    "Sei Jarvis, un assistente vocale che risponde tramite Alexa in italiano. "
    "Le tue risposte vengono lette ad alta voce: scrivi frasi semplici e naturali, "
    "senza markdown, elenchi puntati, emoji, URL o codice. "
    "Rispondi in due o tre frasi al massimo, a meno che l'utente non chieda esplicitamente "
    "più dettagli. Se non conosci la risposta o richiede dati in tempo reale che non hai, dillo."
)

MAX_TURNS = 6  # coppie domanda/risposta conservate nella sessione Alexa

_client = None


def _get_client():
    global _client
    if _client is None:
        # Alexa attende al massimo circa 8 secondi: niente retry, timeout stretto.
        _client = anthropic.Anthropic(timeout=float(config.env("CLAUDE_TIMEOUT", "6.5")),
                                      max_retries=0)
    return _client


def ask(question, history=None):
    """Restituisce (risposta, nuova_history). La history contiene solo testo."""
    history = list(history or [])[-2 * MAX_TURNS:]
    messages = history + [{"role": "user", "content": question}]
    try:
        response = _get_client().beta.messages.create(
            model=config.env("CLAUDE_MODEL", "claude-opus-5-5"),
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            output_config={"effort": config.env("CLAUDE_EFFORT", "low")},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=messages,
        )
    except anthropic.APITimeoutError:
        return "Ci sto mettendo troppo a pensare. Prova a fare una domanda più semplice.", history
    except anthropic.RateLimitError:
        return "Sono un po' sovraccarico in questo momento, riprova tra poco.", history
    except anthropic.APIStatusError:
        return "Il mio cervello non risponde in questo momento. Riprova più tardi.", history
    except anthropic.APIConnectionError:
        return "Non riesco a collegarmi al mio cervello. Riprova più tardi.", history

    if response.stop_reason == "refusal":
        return "Mi dispiace, non posso aiutarti con questa richiesta.", history

    text = " ".join(b.text for b in response.content if b.type == "text").strip()
    if not text:
        return "Non ho una risposta per questo.", history
    new_history = messages + [{"role": "assistant", "content": text}]
    return text, new_history[-2 * MAX_TURNS:]
