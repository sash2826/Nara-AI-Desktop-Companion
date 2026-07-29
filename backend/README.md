# Enterprise AI Companion — Backend

Python backend service for the Enterprise AI Companion.

## Responsibilities

- File indexing and text extraction
- Semantic search (Qdrant)
- Knowledge graph operations (Neo4j)
- Structured data storage (SQLite)
- AI provider integration (OpenAI via Azure API Management)
- OCR processing (PaddleOCR)
- IPC communication with the Tauri desktop application

## Status

**Phase 00 scaffold.** Directory structure and tooling are in place.
Implementation begins in Phase 01.

## Structure

```
backend/
├── src/
│   └── enterprise_ai_companion/
│       ├── capabilities/
│       │   ├── indexing/       # File scanning, metadata extraction, OCR
│       │   ├── retrieval/      # Retrieval broker, connectors
│       │   └── ai/             # LLM provider integration
│       ├── infrastructure/     # Database clients, external service adapters
│       └── api/                # IPC / HTTP endpoints exposed to Tauri
├── tests/
├── pyproject.toml
└── README.md
```

## Setup

Requires Python 3.11+.

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

## Running

```bash
# Development server (Phase 01)
python -m enterprise_ai_companion
```

## Testing

```bash
pytest
```
