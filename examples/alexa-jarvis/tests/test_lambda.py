import json
from types import SimpleNamespace
from unittest import mock

import pytest

import lambda_function
from jarvis import assistant, github_status, home_assistant

SKILL = "amzn1.ask.skill.test"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("ALEXA_SKILL_ID", SKILL)
    monkeypatch.setenv("GITHUB_REPOS", "acme/app,acme/api")
    monkeypatch.setenv("HA_URL", "http://ha.local:8123")
    monkeypatch.setenv("HA_TOKEN", "x")


def event(rtype="IntentRequest", intent=None, slots=None, attributes=None, skill=SKILL):
    req = {"type": rtype}
    if intent:
        req["intent"] = {"name": intent,
                         "slots": {k: {"name": k, "value": v} for k, v in (slots or {}).items()}}
    return {
        "session": {"application": {"applicationId": skill}, "attributes": attributes or {}},
        "context": {"System": {"application": {"applicationId": skill}}},
        "request": req,
    }


def speech(resp):
    return resp["response"]["outputSpeech"]["text"]


def test_rejects_wrong_skill():
    with pytest.raises(PermissionError):
        lambda_function.lambda_handler(event("LaunchRequest", skill="other"), None)


def test_rejects_when_skill_id_unset(monkeypatch):
    monkeypatch.delenv("ALEXA_SKILL_ID")
    with pytest.raises(PermissionError):
        lambda_function.lambda_handler(event("LaunchRequest"), None)


def test_launch():
    r = lambda_function.lambda_handler(event("LaunchRequest"), None)
    assert "Jarvis" in speech(r)
    assert r["response"]["shouldEndSession"] is False


def test_session_ended_has_no_speech():
    r = lambda_function.lambda_handler(event("SessionEndedRequest"), None)
    assert r["response"] == {}


def fake_message(text, stop="end_turn"):
    return SimpleNamespace(stop_reason=stop,
                           content=[SimpleNamespace(type="thinking", thinking=""),
                                    SimpleNamespace(type="text", text=text)])


def test_domanda_calls_claude_and_keeps_history():
    client = mock.MagicMock()
    client.beta.messages.create.return_value = fake_message("La Luna dista circa 384 mila km.")
    with mock.patch.object(assistant, "_client", client):
        r = lambda_function.lambda_handler(
            event(intent="DomandaIntent", slots={"domanda": "quanto dista la Luna"}), None)
    assert speech(r) == "La Luna dista circa 384 mila km."
    kwargs = client.beta.messages.create.call_args.kwargs
    assert kwargs["model"] == "claude-opus-5-5"
    assert kwargs["fallbacks"] == "default"
    assert kwargs["messages"][-1] == {"role": "user", "content": "quanto dista la Luna"}
    hist = r["sessionAttributes"]["history"]
    assert hist[-1] == {"role": "assistant", "content": "La Luna dista circa 384 mila km."}


def test_history_is_capped():
    client = mock.MagicMock()
    client.beta.messages.create.return_value = fake_message("ok")
    old = []
    for i in range(20):
        old += [{"role": "user", "content": f"q{i}"}, {"role": "assistant", "content": "a"}]
    with mock.patch.object(assistant, "_client", client):
        _, hist = assistant.ask("nuova", old)
    assert len(hist) == 2 * assistant.MAX_TURNS
    assert hist[0]["role"] == "user"


def test_refusal_is_spoken_politely():
    client = mock.MagicMock()
    client.beta.messages.create.return_value = fake_message("", stop="refusal")
    with mock.patch.object(assistant, "_client", client):
        text, hist = assistant.ask("x", [])
    assert "non posso" in text
    assert hist == []


def test_pull_requests(monkeypatch):
    calls = {"acme/app": [{}, {}], "acme/api": []}

    def fake(url, headers=None, body=None, timeout=4.0):
        repo = url.split("/repos/")[1].split("/pulls")[0]
        return calls[repo]

    monkeypatch.setattr(github_status, "request_json", fake)
    r = lambda_function.lambda_handler(event(intent="PullRequestIntent"), None)
    assert speech(r) == "Hai 2 pull request aperte: 2 su app."


def test_ci(monkeypatch):
    runs = {
        "acme/app": {"workflow_runs": [{"status": "completed", "conclusion": "failure",
                                        "name": "Tests", "head_branch": "main"}]},
        "acme/api": {"workflow_runs": [{"status": "in_progress", "name": "CI",
                                        "head_branch": "dev"}]},
    }
    monkeypatch.setattr(github_status, "request_json",
                        lambda url, **k: runs[url.split("/repos/")[1].split("/actions")[0]])
    text = speech(lambda_function.lambda_handler(event(intent="StatoCIIntent"), None))
    assert "Tests sul branch main è fallita" in text
    assert "CI sul branch dev è ancora in corso" in text


def test_casa(monkeypatch):
    seen = {}

    def fake(url, headers=None, body=None, timeout=4.0):
        seen.update(url=url, body=body)
        return {"response": {"speech": {"plain": {"speech": "Ho acceso la luce."}}}}

    monkeypatch.setattr(home_assistant, "request_json", fake)
    r = lambda_function.lambda_handler(
        event(intent="CasaIntent", slots={"comando": "accendi la luce del soggiorno"}), None)
    assert speech(r) == "Ho acceso la luce."
    assert seen["url"] == "http://ha.local:8123/api/conversation/process"
    assert seen["body"] == {"text": "accendi la luce del soggiorno", "language": "it"}


def test_interaction_model_intents_are_handled():
    model = json.load(open("interaction_model/it-IT.json"))
    names = {i["name"] for i in model["interactionModel"]["languageModel"]["intents"]}
    src = open("lambda_function.py").read()
    for n in names:
        assert f'"{n}"' in src, n
