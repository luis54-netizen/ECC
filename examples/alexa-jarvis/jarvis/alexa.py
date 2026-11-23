"""Helper per costruire le risposte nel formato JSON di Alexa."""


def speak(text, end_session=True, reprompt=None, attributes=None):
    response = {
        "outputSpeech": {"type": "PlainText", "text": text},
        "shouldEndSession": end_session,
    }
    if reprompt:
        response["reprompt"] = {"outputSpeech": {"type": "PlainText", "text": reprompt}}
    return {
        "version": "1.0",
        "sessionAttributes": attributes or {},
        "response": response,
    }


def slot_value(request, name):
    slots = request.get("intent", {}).get("slots", {}) or {}
    return (slots.get(name) or {}).get("value") or ""
