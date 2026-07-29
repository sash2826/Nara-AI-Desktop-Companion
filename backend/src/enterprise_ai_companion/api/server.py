"""Uvicorn startup and shutdown for the Enterprise AI Companion backend."""

import socket
import uvicorn


def find_free_port() -> int:
    """Bind to port 0 so the OS assigns a free port, then release and return it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def run(port: int | None = None) -> None:
    """Start uvicorn on the given port (or a free OS-assigned port)."""
    resolved_port = port if port is not None else find_free_port()

    # Print the ready signal before uvicorn starts so the Tauri process can
    # capture the port from stdout before the uvicorn banner appears.
    print(f"READY:{resolved_port}", flush=True)

    uvicorn.run(
        "enterprise_ai_companion.api.app:app",
        host="127.0.0.1",
        port=resolved_port,
        log_level="warning",
    )
