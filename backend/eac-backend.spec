"""PyInstaller spec for the EAC backend sidecar.

Run from the backend/ directory:
    python -m PyInstaller eac-backend.spec --noconfirm --clean

Or use the build script from the repo root:
    .\\scripts\\build_sidecar.ps1
"""

import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None
datas, binaries, hiddenimports = [], [], []

# Collect native DLLs + data for packages that PyInstaller misses.
for pkg in ["onnxruntime", "fastembed", "uvicorn", "watchdog", "aiosqlite"]:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# Bundle the migration SQL files — EAC_MIGRATIONS_DIR is set to
# sys._MEIPASS/migrations in sidecar_main.py.
migrations_src = os.path.join("..", "database", "migrations")
datas += [(migrations_src, "migrations")]

a = Analysis(
    ["sidecar_main.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + [
        "enterprise_ai_companion",
        "enterprise_ai_companion.api.app",
        "enterprise_ai_companion.api.server",
        "enterprise_ai_companion.api.routers",
        "multipart",
        "aiofiles",
        "truststore",
        "python_docx",
        "pypdf",
        "qdrant_client",
        "pydantic_settings",
    ],
    excludes=["torch", "tensorflow", "cv2", "sklearn"],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="eac-backend",
    debug=False,
    strip=False,
    upx=False,
    # console=True is mandatory — the READY:port:token sentinel is written to stdout
    # and read by Tauri's start_sidecar() to discover the port and IPC token.
    console=True,
    icon=None,
)
