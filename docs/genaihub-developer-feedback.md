# GenAI Hub — Developer Integration Feedback

**From:** Document-Management-RAG-Graph-Agent project team  
**To:** GenAI Hub platform editors  
**Date:** August 2026  
**Context:** Feedback from integrating an internal desktop AI application against the GenAI Hub APIM during active development with Claude Code

---

## Summary

This document captures friction points encountered during a real integration. It is not a complaint — the platform works — but several gaps between what the documentation says and what the platform actually requires forced significant workarounds. Each section below identifies a specific problem, its impact, and a recommended improvement.

---

## 1. Auth Header Name Mismatch

**Problem:** The APIM documentation and portal indicate that the authentication header should be `Ocp-Apim-Subscription-Key`. The actual header name that the gateway accepts is `api-key`.

**Impact:** This caused 401 errors that were not clearly diagnosed. Developers following the official documentation will always get this wrong on their first attempt and have no obvious signal pointing to the header name as the cause.

**Recommendation:** Update the documentation and any code samples to use `api-key` as the header name. If both header names are intentionally accepted, document that explicitly. If not, pick one and make it consistent everywhere.

---

## 2. Endpoint URL Structure Not Documented Clearly

**Problem:** The endpoint path that works is:

```
https://api.volvogenaihubqa.volvogroup.net/azure-openai/v1/chat/completions?api-version=preview
```

This differs from the standard Azure OpenAI path (`/openai/deployments/{deployment-id}/chat/completions`) in two ways:

- The base path is `/azure-openai/v1/` not the standard Azure path
- The model/deployment ID must be passed in the **request body**, not in the URL path
- `?api-version=preview` is required and not documented alongside the URL

**Impact:** Developers copy endpoint patterns from Azure OpenAI documentation or GenAI Hub portal examples, none of which match the actual working format. This is the single largest source of integration friction.

**Recommendation:** Provide one complete, copy-pasteable working example in the documentation — including the full URL, `?api-version=preview`, and a minimal request body with the model field populated. Make this the first thing a developer sees, not buried in FAQs.

---

## 3. Active Deployment IDs Are Hard to Discover

**Problem:** There is no clear, central place to see which model deployment IDs are currently active. Deployment IDs are versioned (e.g. `gpt-41-mini_gb_2025-04-14`) and get decommissioned without always being clearly communicated to teams actively using them. When a deployment is decommissioned, the API returns HTTP 500 — an error that looks like a server fault, not a configuration problem.

**Impact:** During this project, the original deployment `gpt-5.4-mini_gb_2026-03-17` was decommissioned and began returning 500 errors. Without a documented list of active deployments or a clear error message indicating the deployment was retired, diagnosing this required manual discovery through the portal.

**Recommendation:**
- Maintain a simple, always-current page listing active deployment IDs and their status
- Return a meaningful error code or message when a deployment ID is not found or has been retired (a 404 with a descriptive body is far better than a 500)
- Notify subscribed teams when a deployment they are actively using is being decommissioned

---

## 4. No Native Cost or Usage Tracking

**Problem:** The platform provides no usage dashboard, token counter, or cost visibility for individual developers or teams during development. There is no way to see how many tokens a development session consumed or what it cost without building your own instrumentation.

**Impact:** To get any visibility into usage during this project, a local proxy server had to be built from scratch to intercept API calls, count tokens from response bodies, and log them to CSV. This was approximately two days of work that should not have been necessary.

The proxy we built (included below for reference) logs per-request input/output tokens, calculates cost estimates, writes daily and all-time CSV logs, and exposes a `/stats` endpoint. This is functionality that should be native to the platform.

**Recommendation:**
- Provide a developer usage dashboard in the GenAI Hub portal showing token consumption and estimated cost per subscription, per day, and per time range
- Expose usage data via an API endpoint (e.g. `GET /usage?from=YYYY-MM-DD`) so it can be pulled programmatically
- Even a simple daily summary email would significantly reduce the need for custom tooling

---

## 5. AI Development Tool Compatibility (Claude Code, Copilot, etc.)

**Problem:** Modern AI development tools like Claude Code send API requests that include headers and body parameters specific to the tool's API provider (Anthropic, in this case). Examples include:

- `anthropic-version` header
- `anthropic-beta` header
- Body parameters like `stream_options`, `parallel_tool_calls`

The GenAI Hub APIM does not support these and returns errors when they are present, even though the rest of the request (model, messages, API key) is valid.

**Impact:** Claude Code could not communicate directly with the GenAI Hub APIM. Every API call failed at the gateway before reaching the model. The only workaround was running the local proxy to strip these parameters before forwarding.

**Recommendation:**
- Document which headers and body parameters are unsupported and will be rejected
- Consider whether the gateway can silently ignore unknown headers and body parameters rather than returning errors for them — this is standard behavior for most API proxies and would allow tool compatibility without custom workarounds
- Alternatively, publish an official compatibility guide for commonly used AI development tools

---

## 6. HTTP Method Support on the Completions Endpoint

**Problem:** AI development tools commonly send `HEAD` or `GET` requests to API endpoints as health checks or capability probes before sending a `POST`. The GenAI Hub completions endpoint does not support these methods and returns errors.

**Impact:** Claude Code performed a `HEAD` request to the endpoint as part of its startup check. This failed, which in some configurations prevented the tool from routing requests correctly at all.

**Recommendation:**
- Add `HEAD` support to the completions endpoint (it should return `200 OK` with no body)
- Consider adding a `GET /health` or `GET /models` endpoint following the OpenAI API convention, which most tools probe automatically

---

## 7. API Keys in Documentation Examples

**Observation:** An earlier version of internal documentation and example code contained a live API key as a hardcoded default value. This is a security risk — any key in source code or documentation can be leaked through version control, screen shares, or log files.

**Recommendation:**
- Audit all documentation, code samples, and example scripts to ensure no live credentials are present
- Use obvious placeholders (`YOUR_SUBSCRIPTION_KEY`) in all examples
- Include a note reminding developers to load keys from environment variables, not hardcode them

---

## Appendix: Cost-Tracking Proxy (Reference Implementation)

The following proxy was built to work around issues 4, 5, and 6 above. It runs locally and sits between development tools and the GenAI Hub APIM. It is included here as evidence of the workaround complexity required, and as a starting point if the platform team wants to understand what developers are doing in the absence of native tooling.

**What it does:**
- Forwards `POST` requests to the GenAI Hub APIM with the correct `api-key` header
- Returns `200` for `HEAD` and `OPTIONS` requests without forwarding them
- Strips unsupported Anthropic-specific headers before forwarding
- Counts input and output tokens from response bodies
- Calculates cost estimates using configurable per-million-token prices
- Logs every request to a master CSV and a daily CSV
- Writes a `stats.json` file for a companion usage popup UI
- Exposes `/health`, `/version`, and `/stats` diagnostic endpoints

**To run:**

```bash
pip install requests
set CLAUDE_PROXY_API_KEY=your_subscription_key_here
python proxy.py
```

Then point your development tool at `http://localhost:8080` instead of the APIM URL.

```python
# proxy.py — GenAI Hub local development proxy with cost tracking
# Built as a workaround for missing platform features (see feedback above).

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import csv
from datetime import datetime
import json
import os
import platform
from pathlib import Path
import socket
import subprocess
import sys
import threading
import traceback

import requests

PROXY_VERSION = "1.1.0"
DEBUG = os.getenv("CLAUDE_PROXY_DEBUG", "false").lower() in {"1", "true", "yes"}

INPUT_PRICE_PER_M  = float(os.getenv("CLAUDE_INPUT_PRICE_PER_M", "3.00"))
OUTPUT_PRICE_PER_M = float(os.getenv("CLAUDE_OUTPUT_PRICE_PER_M", "15.00"))
TARGET_URL  = os.getenv("CLAUDE_PROXY_TARGET_URL", "https://api.volvogenaihubqa.volvogroup.net").rstrip("/")
API_KEY     = os.getenv("CLAUDE_PROXY_API_KEY", "")   # Required — never hardcode
SERVER_HOST = os.getenv("CLAUDE_PROXY_HOST", "localhost")
SERVER_PORT = int(os.getenv("CLAUDE_PROXY_PORT", "8080"))
LAUNCH_POPUP = os.getenv("CLAUDE_PROXY_LAUNCH_POPUP", "true").lower() in {"1", "true", "yes"}
CSV_FILE       = Path(os.getenv("CLAUDE_PROXY_CSV_FILE", str(Path(__file__).with_name("claude_usage_log.csv"))))
DAILY_CSV_DIR  = Path(os.getenv("CLAUDE_PROXY_DAILY_CSV_DIR", str(Path(__file__).with_name("daily_usage_logs"))))
STATS_FILE     = Path(os.getenv("CLAUDE_PROXY_STATS_FILE", str(Path(__file__).with_name("stats.json"))))
POPUP_SCRIPT   = Path(__file__).with_name("usage_popup.py")

session_input_tokens  = 0
session_output_tokens = 0
session_total_cost    = 0.0
session_requests      = 0
daily_log_date        = None
daily_total_cost      = 0.0
alltime_input_tokens  = 0
alltime_output_tokens = 0
alltime_total_cost    = 0.0
statistics_lock       = threading.Lock()

HOP_BY_HOP_HEADERS = {
    "connection", "content-encoding", "content-length", "keep-alive",
    "proxy-authenticate", "proxy-authorization", "te", "trailer",
    "transfer-encoding", "upgrade",
}
PROXY_ID_HEADER = "X-Claude-Cost-Proxy"
PROXY_ID_VALUE  = "1"

SENSITIVE_HEADER_NAMES = {
    "api-key", "authorization", "proxy-authorization", "x-api-key",
    "ocp-apim-subscription-key", "subscription-key", "cookie", "set-cookie",
}


def redact_headers(headers):
    return {k: "********" if k.lower() in SENSITIVE_HEADER_NAMES else v for k, v in headers.items()}


def classify_request_exception(error):
    if isinstance(error, requests.exceptions.Timeout):
        return f"TIMEOUT: no response from {TARGET_URL} ({error})"
    if isinstance(error, requests.exceptions.ConnectionError):
        return f"CONNECTION FAILURE reaching {TARGET_URL}: {error}"
    return f"UPSTREAM REQUEST FAILURE: {error}"


UPSTREAM_STATUS_EXPLANATIONS = {
    401: "401 Unauthorized: API key rejected.",
    403: "403 Forbidden: key valid but not permitted for this resource.",
    404: "404 Not Found: check TARGET_URL and request path.",
    429: "429 Too Many Requests: rate limited.",
}


def explain_upstream_status(status_code):
    if status_code in UPSTREAM_STATUS_EXPLANATIONS:
        return UPSTREAM_STATUS_EXPLANATIONS[status_code]
    if 500 <= status_code < 600:
        return f"Upstream {status_code}: server-side error."
    return None


def initialize_csv():
    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
    if CSV_FILE.exists():
        return
    with CSV_FILE.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["Timestamp", "Model", "Input Tokens", "Output Tokens", "Prompt Cost ($)", "Session Cost ($)"])


def load_alltime_totals():
    total_input = total_output = 0
    total_cost = 0.0
    if not CSV_FILE.exists():
        return total_input, total_output, total_cost
    with CSV_FILE.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                total_input  += int(row["Input Tokens"])
                total_output += int(row["Output Tokens"])
                total_cost   += float(row["Prompt Cost ($)"])
            except (KeyError, TypeError, ValueError):
                continue
    return total_input, total_output, total_cost


def build_stats_payload(current_date):
    return {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "alltime":  {"input_tokens": alltime_input_tokens, "output_tokens": alltime_output_tokens, "total_tokens": alltime_input_tokens + alltime_output_tokens, "cost": round(alltime_total_cost, 6)},
        "today":    {"date": current_date.isoformat(), "cost": round(daily_total_cost, 6)},
        "session":  {"requests": session_requests, "input_tokens": session_input_tokens, "output_tokens": session_output_tokens, "total_tokens": session_input_tokens + session_output_tokens, "cost": round(session_total_cost, 6)},
    }


def write_stats_file(current_date):
    tmp = STATS_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(build_stats_payload(current_date), f, indent=2)
    os.replace(tmp, STATS_FILE)


def get_daily_csv_file(log_date):
    return DAILY_CSV_DIR / f"claude_usage_{log_date.isoformat()}.csv"


def initialize_daily_csv(daily_csv_file):
    daily_csv_file.parent.mkdir(parents=True, exist_ok=True)
    if daily_csv_file.exists():
        return
    with daily_csv_file.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["Timestamp", "Model", "Input Tokens", "Output Tokens", "Prompt Cost ($)", "Daily Cost ($)"])


def load_daily_total(daily_csv_file):
    latest = 0.0
    with daily_csv_file.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                latest = float(row["Daily Cost ($)"])
            except (KeyError, TypeError, ValueError):
                continue
    return latest


def extract_usage(response_body):
    text = response_body.decode("utf-8", errors="replace")
    objects = []
    try:
        objects.append(json.loads(text))
    except json.JSONDecodeError:
        for line in text.splitlines():
            if not line.startswith("data:"):
                continue
            data = line.removeprefix("data:").strip()
            if not data or data == "[DONE]":
                continue
            try:
                objects.append(json.loads(data))
            except json.JSONDecodeError:
                continue

    model = "Unknown"
    input_tokens = output_tokens = 0
    for item in objects:
        if not isinstance(item, dict):
            continue
        message = item.get("message", {}) or {}
        item_model = item.get("model") or message.get("model")
        if item_model:
            model = item_model
        usage = item.get("usage") or message.get("usage") or {}
        if not isinstance(usage, dict):
            continue
        if usage.get("input_tokens") is not None:
            input_tokens  = int(usage["input_tokens"])
        if usage.get("output_tokens") is not None:
            output_tokens = int(usage["output_tokens"])
    return model, input_tokens, output_tokens


def record_usage(model, input_tokens, output_tokens):
    global session_input_tokens, session_output_tokens, session_total_cost
    global session_requests, daily_log_date, daily_total_cost
    global alltime_input_tokens, alltime_output_tokens, alltime_total_cost

    prompt_cost  = (input_tokens * INPUT_PRICE_PER_M + output_tokens * OUTPUT_PRICE_PER_M) / 1_000_000
    request_time = datetime.now()

    with statistics_lock:
        current_date   = request_time.date()
        daily_csv_file = get_daily_csv_file(current_date)
        if daily_log_date != current_date:
            initialize_daily_csv(daily_csv_file)
            daily_total_cost = load_daily_total(daily_csv_file)
            daily_log_date   = current_date

        session_input_tokens  += input_tokens
        session_output_tokens += output_tokens
        session_total_cost    += prompt_cost
        session_requests      += 1
        daily_total_cost      += prompt_cost
        alltime_input_tokens  += input_tokens
        alltime_output_tokens += output_tokens
        alltime_total_cost    += prompt_cost

        with CSV_FILE.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([request_time.strftime("%Y-%m-%d %H:%M:%S"), model, input_tokens, output_tokens, round(prompt_cost, 6), round(session_total_cost, 6)])

        with daily_csv_file.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([request_time.strftime("%Y-%m-%d %H:%M:%S"), model, input_tokens, output_tokens, round(prompt_cost, 6), round(daily_total_cost, 6)])

        write_stats_file(current_date)

        print(f"\n{'='*65}\nUsage Summary — {model}\n{'='*65}")
        print(f"  Prompt     : {input_tokens:,} in / {output_tokens:,} out  (${prompt_cost:.6f})")
        print(f"  Session    : {session_requests} requests  ${session_total_cost:.6f}")
        print(f"  Today      : ${daily_total_cost:.6f}")
        print(f"{'='*65}\n")


class ExclusiveThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = False

    def server_bind(self):
        if os.name == "nt":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header(PROXY_ID_HEADER, PROXY_ID_VALUE)
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
        elif self.path == "/version":
            self._send_json(200, {"version": PROXY_VERSION, "target": TARGET_URL, "debug": DEBUG})
        elif self.path == "/stats":
            with statistics_lock:
                payload = build_stats_payload(daily_log_date or datetime.now().date())
            self._send_json(200, payload)
        else:
            self.send_error(404, "Not found")

    def _send_json(self, status_code, payload):
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header(PROXY_ID_HEADER, PROXY_ID_VALUE)
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        response_started = False
        try:
            content_length = max(int(self.headers.get("Content-Length", 0)), 0)
            body    = self.rfile.read(content_length) if content_length > 0 else b""
            payload = json.loads(body)
            model   = payload.get("model", "Unknown")

            headers = {
                "Accept":           self.headers.get("Accept", "application/json"),
                "Accept-Encoding":  "identity",
                "Content-Type":     self.headers.get("Content-Type", "application/json"),
                "api-key":          API_KEY,
            }
            # Forward Anthropic-specific headers only if present — APIM will
            # reject them, but keeping this conditional makes the stripping
            # explicit and easy to adjust.
            for h in ("anthropic-version", "anthropic-beta"):
                if h in self.headers:
                    headers[h] = self.headers[h]

            final_url = TARGET_URL + self.path
            print(f"[UPSTREAM] POST {final_url}  model={model}  size={len(body)}B")
            if DEBUG:
                print(f"  headers: {redact_headers(headers)}")

            with requests.post(final_url, headers=headers, data=body, timeout=(10, 300), stream=True) as response:
                self.send_response(response.status_code)
                for key, value in response.headers.items():
                    if key.lower() not in HOP_BY_HOP_HEADERS:
                        self.send_header(key, value)
                self.send_header("Connection", "close")
                self.end_headers()
                self.close_connection = True
                response_started = True

                response_body  = bytearray()
                client_alive   = True
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    response_body.extend(chunk)
                    if client_alive:
                        try:
                            self.wfile.write(chunk)
                            self.wfile.flush()
                        except (BrokenPipeError, ConnectionResetError):
                            client_alive = False

                explanation = explain_upstream_status(response.status_code)
                if explanation:
                    print(f"  NOTE: {explanation}")

                model, input_tokens, output_tokens = extract_usage(response_body)
                record_usage(model, input_tokens, output_tokens)

        except json.JSONDecodeError as e:
            self._send_error(400, f"Invalid JSON: {e}", response_started)
        except requests.exceptions.RequestException as e:
            print(f"DIAGNOSIS: {classify_request_exception(e)}")
            self._send_error(502, f"Upstream error: {e}", response_started)
        except Exception as e:
            traceback.print_exc()
            self._send_error(500, str(e), response_started)

    def _send_error(self, status_code, message, response_started):
        print(f"ERROR {status_code}: {message}")
        if not response_started:
            self.send_error(status_code, message)


def create_server():
    try:
        return ExclusiveThreadingHTTPServer((SERVER_HOST, SERVER_PORT), ProxyHandler)
    except OSError as e:
        try:
            r = requests.head(f"http://{SERVER_HOST}:{SERVER_PORT}", timeout=2)
        except requests.RequestException:
            raise SystemExit(f"Cannot start on {SERVER_HOST}:{SERVER_PORT}: {e}") from e
        if r.headers.get(PROXY_ID_HEADER) == PROXY_ID_VALUE:
            print(f"Proxy already running at http://{SERVER_HOST}:{SERVER_PORT} — reuse it.")
            return None
        raise SystemExit(f"Port {SERVER_PORT} occupied by another service.") from e


def main():
    global alltime_input_tokens, alltime_output_tokens, alltime_total_cost
    global daily_log_date, daily_total_cost

    print(f"GenAI Hub Cost-Tracking Proxy v{PROXY_VERSION}")
    print(f"Target : {TARGET_URL}")
    print(f"Listen : http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"Debug  : {DEBUG}")
    print(f"API key: {'set' if API_KEY else 'MISSING'}\n")

    if not API_KEY:
        raise SystemExit("Set CLAUDE_PROXY_API_KEY before starting.")

    server = create_server()
    if server is None:
        return

    initialize_csv()
    with statistics_lock:
        alltime_input_tokens, alltime_output_tokens, alltime_total_cost = load_alltime_totals()
        current_date   = datetime.now().date()
        daily_csv_file = get_daily_csv_file(current_date)
        initialize_daily_csv(daily_csv_file)
        daily_total_cost = load_daily_total(daily_csv_file)
        daily_log_date   = current_date
        write_stats_file(current_date)

    if LAUNCH_POPUP and POPUP_SCRIPT.exists():
        try:
            subprocess.Popen([sys.executable, str(POPUP_SCRIPT)], cwd=str(POPUP_SCRIPT.parent))
        except OSError as e:
            print(f"Popup failed to launch: {e}")

    print(f"Proxy running. Usage log: {CSV_FILE}\nPress Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
```

---

*Submitted August 2026. Happy to discuss any of these points directly.*
