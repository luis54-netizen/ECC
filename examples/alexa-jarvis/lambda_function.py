"""Endpoint AWS Lambda della skill Alexa "Jarvis".

Instrada gli intent verso tre funzioni:
  - DomandaIntent      -> Claude (domande libere, con memoria di sessione)
  - PullRequestIntent  -> GitHub, pull request aperte
  - StatoCIIntent      -> GitHub, ultima esecuzione della CI
  - CasaIntent         -> Home Assistant (Assist)
"""
import logging

from jarvis import alexa, assistant, config, github_status, home_assistant

logger = logging.getLogger()
logger.setLevel(logging.INFO)

WELCOME = ("Ciao, sono Jarvis. Puoi farmi una domanda, chiedermi delle pull request "
           "o della CI, oppure darmi un comando per la casa.")
REPROMPT = "Cosa vuoi sapere?"
HELP = ("Puoi dire, per esempio: chiedi quanto dista la Luna; quante pull request ho; "
        "com'è andata la CI; oppure casa accendi la luce del soggiorno.")


def _skill_id(event):
    ctx = event.get("context", {}).get("System", {}).get("application", {})
    return ctx.get("applicationId") or event.get("session", {}).get("application", {}).get("applicationId")


def lambda_handler(event, _context):
    expected = config.env("ALEXA_SKILL_ID")
    if not expected or _skill_id(event) != expected:
        # Rifiuta chiamate da skill diverse dalla nostra (o configurazione mancante).
        logger.warning("Richiesta rifiutata: skill ID non valido o ALEXA_SKILL_ID non impostato")
        raise PermissionError("Invalid skill ID")

    request = event.get("request", {})
    rtype = request.get("type")
    attributes = event.get("session", {}).get("attributes") or {}

    if rtype == "LaunchRequest":
        return alexa.speak(WELCOME, end_session=False, reprompt=REPROMPT)
    if rtype == "SessionEndedRequest":
        return {"version": "1.0", "response": {}}  # Alexa non accetta parlato qui
    if rtype != "IntentRequest":
        return alexa.speak("Non ho capito.", end_session=True)

    intent = request.get("intent", {}).get("name")

    if intent == "DomandaIntent":
        question = alexa.slot_value(request, "domanda")
        if not question:
            return alexa.speak("Qual è la domanda?", end_session=False, reprompt=REPROMPT,
                               attributes=attributes)
        answer, history = assistant.ask(question, attributes.get("history"))
        return alexa.speak(answer, end_session=False, reprompt="Altro?",
                           attributes={**attributes, "history": history})

    if intent == "PullRequestIntent":
        return alexa.speak(github_status.open_pull_requests(), end_session=False,
                           reprompt="Altro?", attributes=attributes)

    if intent == "StatoCIIntent":
        return alexa.speak(github_status.latest_ci(), end_session=False,
                           reprompt="Altro?", attributes=attributes)

    if intent == "CasaIntent":
        cmd = alexa.slot_value(request, "comando")
        if not cmd:
            return alexa.speak("Cosa devo fare in casa?", end_session=False,
                               reprompt=REPROMPT, attributes=attributes)
        return alexa.speak(home_assistant.command(cmd), end_session=False,
                           reprompt="Altro?", attributes=attributes)

    if intent == "AMAZON.HelpIntent":
        return alexa.speak(HELP, end_session=False, reprompt=REPROMPT, attributes=attributes)
    if intent in ("AMAZON.StopIntent", "AMAZON.CancelIntent", "AMAZON.NavigateHomeIntent"):
        return alexa.speak("A presto.", end_session=True)
    if intent == "AMAZON.FallbackIntent":
        return alexa.speak("Non ho capito. Prova a iniziare con: chiedi.", end_session=False,
                           reprompt=REPROMPT, attributes=attributes)

    return alexa.speak("Non so ancora fare questa cosa.", end_session=False,
                       reprompt=REPROMPT, attributes=attributes)
