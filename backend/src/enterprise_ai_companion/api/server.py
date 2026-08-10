"""Uvicorn startup and shutdown for the Enterprise AI Companion backend."""

import os
import secrets
import socket
import ssl
from pathlib import Path
import uvicorn


def _load_env_file() -> None:
    """Load key=value pairs from backend/.env into os.environ (if the file exists).

    Only sets variables that are not already present in the environment so that
    shell exports and Tauri-injected env vars always take precedence.
    Skips blank lines and lines starting with #.
    """
    env_path = Path(__file__).parents[3] / ".env"
    if not env_path.exists():
        return
    with env_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

# Disable HuggingFace Xet CDN — uses byte-range HTTP requests that are blocked
# by corporate proxies. Standard HTTP chunked download is used instead.
_load_env_file()

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

# Inject the Windows system certificate store (including corporate proxy CAs)
# into Python's SSL context so model downloads succeed behind SSL-inspecting proxies.
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass


def find_free_port() -> int:
    """Bind to port 0 so the OS assigns a free port, then release and return it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def run(port: int | None = None) -> None:
    """Start uvicorn on the given port (or a free OS-assigned port)."""
    resolved_port = port if port is not None else find_free_port()

    # Generate a per-session IPC shared secret and set it as an env var so
    # TokenVerificationMiddleware in app.py can read it via AppConfig.
    # The token is printed in the READY line so the Tauri host can capture it
    # and attach it to every sidecar request as X-EAC-Token.
    ipc_secret = secrets.token_hex(32)
    os.environ["EAC_IPC_SECRET"] = ipc_secret

    # Print the ready signal before uvicorn starts so the Tauri process can
    # capture the port from stdout before the uvicorn banner appears.
    print(f"READY:{resolved_port}:{ipc_secret}", flush=True)

    uvicorn.run(
        "enterprise_ai_companion.api.app:app",
        host="127.0.0.1",
        port=resolved_port,
        log_level="warning",
    )
