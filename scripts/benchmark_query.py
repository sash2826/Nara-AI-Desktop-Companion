#!/usr/bin/env python3
"""Query quality benchmark for the Enterprise AI Companion.

Runs a set of natural language queries through the full RAG pipeline
(hybrid search → LLM synthesis) and scores results against expected
sources and content criteria.

Prerequisites
-------------
- Backend must NOT be running (needs exclusive SQLite/Qdrant access).
- test-drive/ must be indexed via the app.
- FILE_ORGANIZATION_GROUND_TRUTH.md and TEST_INSTRUCTIONS.md should be
  removed from test-drive/ root before running (they pollute results).

Usage (from repo root, with the backend venv activated)
-------------------------------------------------------
    cd backend
    python ../scripts/benchmark_query.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / "backend" / ".env")
except ImportError:
    pass

# ── Test case definition ───────────────────────────────────────────────────────


@dataclass
class QueryTest:
    """A single query test case.

    Scoring (per test, max 4 pts):
      source_pts: 2 if any expected_sources appear in top-5, 1 if in top-10
      content_pts: 2 if all required_keywords found, 1 if ≥ half found
    """

    query: str
    description: str
    # File name substrings — any one of these in top-5 sources scores 2pts.
    expected_sources: list[str]
    # ALL these words should appear somewhere in the response (case-insensitive).
    required_keywords: list[str]
    # At least this many keyword hits to score 1pt instead of 0.
    partial_keyword_threshold: int = 1


TESTS: list[QueryTest] = [
    QueryTest(
        query="Find me any documents related to vendor proposals or supplier evaluation",
        description="Vendor & supplier docs across projects",
        expected_sources=["Vendor_Proposal", "Vendor_Evaluation"],
        required_keywords=["vendor", "proposal"],
    ),
    QueryTest(
        query="What do we have on carbon emissions or sustainability reporting?",
        description="Polaris Sustainability carbon docs",
        expected_sources=["Carbon_Reporting", "Sustainability_Requirements",
                          "Reporting_Requirements", "Project_Overview"],
        required_keywords=["carbon", "sustainability", "Polaris"],
    ),
    QueryTest(
        query="Do we have anything about warehouse logistics or supply chain forecasting?",
        description="Horizon Logistics warehouse docs",
        expected_sources=["Warehouse_Requirements", "Route_Optimization",
                          "Operations_Report", "Project_Overview"],
        required_keywords=["warehouse", "Horizon"],
    ),
    QueryTest(
        query="Which projects are currently working on data analytics or dashboards?",
        description="Northstar Analytics project identification",
        expected_sources=["Project_Overview", "Data_Governance", "Security_Review"],
        required_keywords=["Northstar", "analytics"],
    ),
    QueryTest(
        query="What's the status of the EV charging deployment proposal?",
        description="Aurora Mobility EV charging status",
        expected_sources=["Charging_Network_Deployment", "Project_Overview",
                          "Meeting_Notes", "Security_Assessment"],
        required_keywords=["Aurora", "charging", "deployment"],
    ),
    QueryTest(
        query="What access control or security documents do we have?",
        description="Atlas Workplace access control docs",
        expected_sources=["Access_Control_Plan", "Security_Review"],
        required_keywords=["access", "control"],
    ),
    QueryTest(
        query="Are there any updated or newer versions of existing project documents?",
        description="Version/duplicate detection",
        # Access_Control_Plan_v2 lives in download-recommendations/, not in the
        # indexed test-drive corpus. Meeting_Notes files contain rolling-version
        # and last-updated metadata and are what hybrid search correctly surfaces.
        expected_sources=["Meeting_Notes"],
        required_keywords=["updated"],
        partial_keyword_threshold=1,
    ),
    QueryTest(
        query="Who are the key people or team members in the Atlas Workplace project?",
        description="Named entity / people retrieval",
        expected_sources=["Project_Overview", "Meeting_Notes"],
        required_keywords=["Atlas"],
    ),
    QueryTest(
        query="What are the budget or cost figures for the Aurora Mobility project?",
        description="Financial document retrieval",
        expected_sources=["Budget_and_Cost_Forecast"],
        required_keywords=["Aurora", "budget"],
    ),
    QueryTest(
        query="What technical architecture documents do we have?",
        description="Technical/architecture docs across projects",
        expected_sources=["Technical_Architecture", "Security_Assessment"],
        required_keywords=["architecture"],
    ),
]

# ── Pipeline helpers ───────────────────────────────────────────────────────────


async def run_query(
    query: str,
    orchestrator,
    preprocessor,
    top_k: int = 10,
) -> tuple[str, list[dict]]:
    """Run the search pipeline and return (response_text, sources)."""
    from enterprise_ai_companion.capabilities.ai.llm_client import chat_complete

    search_text = preprocessor.process(query).search_text if preprocessor else query
    results = await orchestrator.search(
        query=search_text,
        top_k=top_k,
        workspace_path=None,
        semantic_weight=0.7,
        keyword_weight=0.3,
    )

    sources: list[dict] = []
    snippets: list[str] = []
    seen_paths: set[str] = set()

    for r in results[:8]:
        parts = r.document_path.replace("\\", "/").split("/")
        label = "/".join(parts[-2:]) if len(parts) >= 2 else parts[-1]
        name = parts[-1]
        snippets.append(f"[{label}]\n{r.content[:600]}")
        if r.document_path not in seen_paths:
            seen_paths.add(r.document_path)
            sources.append({"path": r.document_path, "name": name, "score": r.rrf_score})

    context_text = "\n\n".join(snippets[:5])

    if context_text:
        system_content = (
            "You are a helpful AI assistant with access to the user's indexed knowledge base.\n"
            "The context below contains real excerpts from the user's files.\n"
            "Rules:\n"
            "- Name the specific document title and project (e.g. 'Atlas Workplace — Access Control Plan').\n"
            "- Use the exact names, people, document IDs, and terms as they appear in the sources.\n"
            "- If the source includes a document ID (e.g. 'AW-DOC-004'), mention it.\n"
            "- Answer concisely — 3–5 sentences max. No markdown headers or bullet lists.\n\n"
            f"Indexed files context:\n{context_text}"
        )
    else:
        system_content = (
            "You are a helpful AI assistant. "
            "No relevant files were found for this query. "
            "Say so briefly."
        )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": query},
    ]
    response = await chat_complete(messages, max_tokens=300, temperature=0.3)
    return response, sources


def score_test(test: QueryTest, response: str, sources: list[dict]) -> tuple[int, int, str]:
    """Return (source_pts, content_pts, notes) for a test case."""
    source_names = [s["name"] for s in sources]
    resp_lower = response.lower()

    # Source scoring
    source_pts = 0
    matched_sources: list[str] = []
    for expected in test.expected_sources:
        for src in source_names[:10]:
            if expected.lower() in src.lower():
                matched_sources.append(src)
                break
    if matched_sources:
        source_pts = 2 if any(
            expected.lower() in s["name"].lower()
            for expected in test.expected_sources
            for s in sources[:5]
        ) else 1

    # Content scoring
    hits = [kw for kw in test.required_keywords if kw.lower() in resp_lower]
    if len(hits) == len(test.required_keywords):
        content_pts = 2
    elif len(hits) >= test.partial_keyword_threshold:
        content_pts = 1
    else:
        content_pts = 0

    notes = []
    if matched_sources:
        notes.append(f"sources: {', '.join(matched_sources[:3])}")
    if hits:
        notes.append(f"kw hits: {hits}")
    else:
        notes.append(f"kw missed: {test.required_keywords}")

    return source_pts, content_pts, "; ".join(notes)


# ── Main ──────────────────────────────────────────────────────────────────────


async def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    print("Loading pipeline…")

    from enterprise_ai_companion.infrastructure.database import open_db, close_db
    from enterprise_ai_companion.infrastructure.qdrant_provider import QdrantProvider
    from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
    from enterprise_ai_companion.capabilities.retrieval.hybrid_orchestrator import HybridSearchOrchestrator

    conn = await open_db()
    await conn.execute("PRAGMA busy_timeout=30000")
    qdrant = QdrantProvider()
    qdrant.initialize()

    embedding_service = EmbeddingService()
    orchestrator = HybridSearchOrchestrator(
        conn=conn,
        qdrant_client=qdrant.get_client(),
        embedding_service=embedding_service,
    )

    preprocessor = None
    try:
        from enterprise_ai_companion.capabilities.retrieval.query_preprocessor import QueryPreprocessor
        preprocessor = QueryPreprocessor()
    except Exception:
        pass

    print(f"Running {len(TESTS)} query tests…\n")

    W = 52
    rows: list[tuple[str, str, int, int, str, str]] = []

    for test in TESTS:
        print(f"  Querying: {test.query[:60]}…")
        try:
            response, sources = await run_query(test.query, orchestrator, preprocessor)
            src_pts, con_pts, notes = score_test(test, response, sources)
        except Exception as exc:
            response = f"ERROR: {exc}"
            src_pts, con_pts, notes = 0, 0, str(exc)[:60]

        rows.append((test.query, test.description, src_pts, con_pts, notes, response))

    await close_db(conn)
    qdrant.close()

    # ── Scorecard ──────────────────────────────────────────────────────────
    total_src = sum(r[2] for r in rows)
    total_con = sum(r[3] for r in rows)
    max_pts = len(TESTS) * 4

    print()
    print("=" * 100)
    print("  EAC QUERY QUALITY BENCHMARK")
    print("  Scoring: Sources [0-2] + Content keywords [0-2] = 4 pts max per query")
    print("=" * 100)
    print(f"  {'Description':<{W}} {'Src':>4} {'Kw':>4} {'Total':>6}  Notes")
    print("-" * 100)

    for query, desc, src_pts, con_pts, notes, response in rows:
        total = src_pts + con_pts
        verdict = "PASS" if total == 4 else ("PART" if total >= 2 else "FAIL")
        bar = ("##" if src_pts == 2 else ("#." if src_pts == 1 else ".."))
        bar += ("##" if con_pts == 2 else ("#." if con_pts == 1 else ".."))
        print(f"  {desc:<{W}} {src_pts:>4} {con_pts:>4} {total:>4}/4  [{bar}] {verdict}")
        print(f"  {'':2} {notes}")
        print()

    print("-" * 100)
    grand = total_src + total_con
    pct = 100 * grand // max_pts
    print(f"  TOTAL  {grand}/{max_pts}  ({pct}%)   Sources: {total_src}/{len(TESTS)*2}   Content: {total_con}/{len(TESTS)*2}")
    print("=" * 100)

    # Full responses for inspection
    print("\n\n=== FULL RESPONSES (for manual review) ===\n")
    for query, desc, src_pts, con_pts, notes, response in rows:
        total = src_pts + con_pts
        print(f"[{total}/4] {desc}")
        print(f"  Q: {query}")
        print(f"  A: {response[:300]}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
