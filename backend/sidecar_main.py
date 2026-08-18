"""PyInstaller entry point for the EAC backend sidecar.

Must run BEFORE importing server so env vars are set before any module-level
code resolves paths. The three path env vars that default to relative-to-
__file__ locations are overridden here to point at writable user-data dirs
when running as a frozen bundle.
"""

import os
import sys

if getattr(sys, "frozen", False):
    meipass = sys._MEIPASS  # type: ignore[attr-defined]

    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    data_dir = os.path.join(appdata, "enterprise-ai-companion")
    os.makedirs(data_dir, exist_ok=True)

    os.environ.setdefault("EAC_DB_PATH", os.path.join(data_dir, "enterprise_ai_companion.db"))
    os.environ.setdefault("EAC_QDRANT_PATH", os.path.join(data_dir, "qdrant_data"))
    os.environ.setdefault("EAC_MIGRATIONS_DIR", os.path.join(meipass, "migrations"))

    # Load .env from the user data dir — survives reinstalls.
    env_file = os.path.join(data_dir, ".env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())

from enterprise_ai_companion.api.server import run  # noqa: E402

if __name__ == "__main__":
    run()
