# Volvo GenAI Hub — Intern Onboarding Guide

**Audience:** New interns setting up an AI development environment against Volvo's internal GenAI Hub  
**Purpose:** Document the real friction points encountered so you don't have to rediscover them

---

## Overview

Volvo's GenAI Hub exposes AI models (GPT-4.1 Mini and others) through an internal Azure API Management (APIM) gateway. The setup differs from the standard Azure OpenAI or OpenAI documentation in several important ways. This guide covers what the official docs won't tell you.

---

## 1. Getting Your API Key

You need a **subscription key** from the GenAI Hub portal. This is not the same as an Azure AD token or a personal account credential.

1. Log in to the internal GenAI Hub portal.
2. Navigate to your subscription and copy the **Primary Key** (or Secondary Key).
3. This is the value you will use for every API call — treat it like a password.

> **Where to find it:** The subscription key is under your profile/subscription page in the GenAI Hub portal, not in the Azure Portal or Entra ID. If you are looking in the wrong place you will not find it.

---

## 2. The Correct Endpoint

The APIM docs and some internal wikis reference endpoint formats that do not match what actually works. Use exactly this:

```
https://api.volvogenaihubqa.volvogroup.net/azure-openai/v1/chat/completions?api-version=preview
```

Key things that are easy to get wrong:

| What you might try | What actually works |
|---|---|
| Standard Azure OpenAI path (`/openai/deployments/{id}/chat/completions`) | `/azure-openai/v1/chat/completions` |
| No `api-version` param | `?api-version=preview` is required |
| Model ID in the URL path | Model ID goes in the **request body** as `"model": "..."` |

---

## 3. The Auth Header Name

The APIM documentation may say `Ocp-Apim-Subscription-Key`. **This is wrong for this gateway.** Use:

```
api-key: <your-subscription-key>
```

A minimal working request looks like this:

```python
import requests

response = requests.post(
    "https://api.volvogenaihubqa.volvogroup.net/azure-openai/v1/chat/completions?api-version=preview",
    headers={
        "api-key": "YOUR_SUBSCRIPTION_KEY",
        "Content-Type": "application/json",
    },
    json={
        "model": "gpt-41-mini_gb_2025-04-14",
        "messages": [{"role": "user", "content": "Hello"}],
    },
)
print(response.status_code, response.json())
```

If you get a `401 Unauthorized`, the header name or key value is wrong — not the endpoint.

---

## 4. Current Active Model Deployment

Model deployments are versioned and get decommissioned. Do not hardcode a deployment ID you found in an example — it may already be retired. As of mid-2026 the active deployment is:

| Field | Value |
|---|---|
| Model | GPT-4.1 Mini |
| Deployment ID | `gpt-41-mini_gb_2025-04-14` |
| API base | `https://api.volvogenaihubqa.volvogroup.net` |

If you get HTTP 500 on a request that looks correct, the deployment ID may have been decommissioned. Check the GenAI Hub portal for the current active deployments.

---

## 5. Using Claude Code (or Other AI Dev Tools) Against GenAI Hub

Claude Code and similar tools generate API requests that sometimes include **beta/experimental parameters** not supported by the APIM configuration. This causes request failures even when your credentials and connectivity are working.

Common symptoms:
- `400 Bad Request` with an error about an unknown parameter
- Requests succeed in your own code but fail when sent by the tool

**Solution: run a local Python proxy** between the tool and the APIM endpoint. The proxy strips unsupported parameters before forwarding.

---

## 6. Setting Up the Local Proxy

The proxy intercepts requests from tools like Claude Code (which send to `localhost`) and forwards them to the real APIM endpoint.

### Minimal proxy (`proxy.py`)

```python
from flask import Flask, request, jsonify, Response
import requests

APIM_BASE = "https://api.volvogenaihubqa.volvogroup.net/azure-openai/v1"
API_KEY   = "YOUR_SUBSCRIPTION_KEY"  # or load from env

# Parameters that the APIM rejects — add more as you discover them
UNSUPPORTED_PARAMS = {"stream_options", "parallel_tool_calls"}

app = Flask(__name__)

@app.route("/v1/<path:path>", methods=["GET", "POST", "HEAD", "OPTIONS"])
def proxy(path):
    if request.method in ("HEAD", "OPTIONS"):
        return Response(status=200)

    body = request.get_json(silent=True) or {}

    # Strip unsupported params
    for param in UNSUPPORTED_PARAMS:
        body.pop(param, None)

    target = f"{APIM_BASE}/{path}?api-version=preview"
    resp = requests.post(
        target,
        headers={"api-key": API_KEY, "Content-Type": "application/json"},
        json=body,
        stream=body.get("stream", False),
        timeout=120,
    )

    return Response(
        resp.iter_content(chunk_size=None) if body.get("stream") else resp.content,
        status=resp.status_code,
        content_type=resp.headers.get("Content-Type", "application/json"),
    )

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
```

Install dependencies:

```bash
pip install flask requests
```

Run:

```bash
python proxy.py
```

Then point your tool at `http://localhost:8080` instead of the APIM URL directly.

---

## 7. HTTP Method Errors (`501 Unsupported method`)

Some tools send `HEAD` or `GET` requests to the same endpoint before sending the real `POST` (for health checks or model listing). The APIM does not support these methods on the completions endpoint, so the tool may fail before even attempting a real request.

The proxy above handles this by returning `200` for `HEAD` and `OPTIONS` immediately without forwarding to APIM. If you see `501` errors, make sure your proxy covers all the methods your tool uses.

---

## 8. What the Standard Docs Won't Cover

The Azure OpenAI documentation, OpenAI SDK docs, and most online examples assume you are talking directly to Azure or OpenAI. Volvo's APIM adds a layer that changes several things:

| Standard assumption | Volvo GenAI Hub reality |
|---|---|
| Auth via Azure AD bearer token | Auth via `api-key` subscription header |
| Model in URL path | Model in request body |
| Standard endpoint path | Custom APIM path (`/azure-openai/v1/...`) |
| Stable deployment IDs in docs | Deployments are versioned and get retired |
| All OpenAI params supported | Some beta params are stripped or rejected |

When something doesn't work, check these differences first before assuming a network or credential problem.

---

## 9. Checklist Before Asking for Help

- [ ] Subscription key copied from the GenAI Hub portal (not Azure Portal)
- [ ] Header name is `api-key`, not `Ocp-Apim-Subscription-Key`
- [ ] Endpoint path is `/azure-openai/v1/chat/completions?api-version=preview`
- [ ] Model ID is in the request body, not the URL
- [ ] Deployment ID matches a currently active deployment in the portal
- [ ] If using a dev tool (Claude Code etc.), local proxy is running

---

*Last verified working: August 2026*
