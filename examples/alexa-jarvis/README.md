# Jarvis per Alexa

Skill Alexa in italiano che fa tre cose:

| Cosa dici | Cosa succede |
|---|---|
| "Alexa, chiedi a Jarvis **chiedi** quanto dista la Luna" | La domanda va a Claude, che risponde in poche frasi. Ricorda il contesto per tutta la sessione. |
| "Alexa, chiedi a Jarvis **quante pull request ho**" | Conta le PR aperte sui repository in `GITHUB_REPOS`. |
| "Alexa, chiedi a Jarvis **com'è andata la CI**" | Legge l'esito dell'ultima esecuzione di GitHub Actions di ogni repository. |
| "Alexa, chiedi a Jarvis **casa** accendi la luce del soggiorno" | Inoltra il comando ad Assist di Home Assistant, in italiano. |

Puoi anche aprire la skill con "Alexa, apri Jarvis" e fare più richieste di seguito.

## Struttura

```
lambda_function.py           handler Lambda e instradamento degli intent
jarvis/assistant.py          chiamata a Claude (Messages API)
jarvis/github_status.py      PR aperte e stato CI (API REST di GitHub)
jarvis/home_assistant.py     comandi domotici (API /api/conversation/process)
interaction_model/it-IT.json modello di interazione da incollare nella console Alexa
tests/                       test con pytest, tutto simulato
build.sh                     crea lo zip per Lambda
```

## Installazione

### 1. Crea la skill

1. Vai su developer.amazon.com, sezione Alexa Developer Console, e crea una skill **Custom**, lingua **Italiano (IT)**, backend **Provision your own**.
2. In **Interaction Model → JSON Editor** incolla `interaction_model/it-IT.json`, salva e fai **Build Model**.
3. Copia lo **Skill ID** (`amzn1.ask.skill....`).

### 2. Crea la Lambda

1. `./build.sh` crea `jarvis-lambda.zip`.
2. Nella console AWS crea una funzione Lambda con runtime **Python 3.12**, regione **eu-west-1** (Irlanda: quella giusta per le skill europee). Carica lo zip.
3. **Configuration → General**: timeout **8 secondi**, memoria 256 MB.
4. **Add trigger → Alexa Skills Kit**, con la verifica dello Skill ID attiva e lo Skill ID copiato prima.
5. **Configuration → Environment variables** (sotto).
6. Copia l'ARN della Lambda e incollalo nella console Alexa in **Endpoint → AWS Lambda ARN**.

### 3. Variabili d'ambiente

| Variabile | Obbligatoria | Valore |
|---|---|---|
| `ALEXA_SKILL_ID` | sì | Lo Skill ID. Senza, la Lambda rifiuta ogni richiesta. |
| `ANTHROPIC_API_KEY` | sì | Chiave API Anthropic (console.anthropic.com). |
| `CLAUDE_MODEL` | no | Predefinito `claude-opus-5-5`. |
| `CLAUDE_EFFORT` | no | Predefinito `low`, per rispondere entro il limite di Alexa. |
| `CLAUDE_TIMEOUT` | no | Secondi, predefinito `6.5`. |
| `GITHUB_REPOS` | per GitHub | Elenco separato da virgole, es. `luis54-netizen/ECC,luis54-netizen/awesome-free-llm-apis`. |
| `GITHUB_TOKEN` | per repo privati | Token fine-grained con permessi in sola lettura su *Pull requests* e *Actions*. |
| `HA_URL` | per la casa | URL pubblico HTTPS di Home Assistant, es. via Nabu Casa. |
| `HA_TOKEN` | per la casa | *Long-lived access token* creato dal tuo profilo Home Assistant. |
| `HA_LANGUAGE` | no | Predefinito `it`. |

Le chiavi conservale in AWS Secrets Manager o almeno come variabili cifrate della Lambda: non metterle mai nel codice.

### 4. Prova

Nella console Alexa, scheda **Test**, attiva il test in *Development* e scrivi "apri jarvis".

## Note

- **Tempi.** Alexa aspetta circa 8 secondi. Per questo Claude gira con effort `low`, timeout di 6,5 secondi e nessun retry. Se una domanda impiega troppo, Jarvis te lo dice invece di restare muto.
- **Rifiuti.** Le richieste usano il fallback lato server di Anthropic (`fallbacks: "default"`). Se il modello rifiuta, la richiesta passa automaticamente a un altro modello. Se rifiutano tutti, Jarvis lo dice a voce.
- **Memoria.** La conversazione resta solo negli attributi della sessione Alexa (ultime 6 domande) e sparisce quando la skill si chiude.
- **Home Assistant** deve essere raggiungibile da Internet in HTTPS. I comandi capiti sono quelli di Assist in italiano: accendi o spegni, imposta la temperatura, apri le tapparelle e simili.

## Test

```bash
pip install -r requirements.txt pytest
python -m pytest -q
```
