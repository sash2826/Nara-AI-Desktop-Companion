"""Deterministic (and optionally LLM-assisted) folder-name generation.

Given the document IDs in a semantic cluster, the service fetches their
canonical entity sets from the knowledge graph and derives a short, human-
readable folder name using document frequency as a ranking signal.

LLM path
--------
``EAC_CLUSTER_NAMING_LLM_ENABLED`` defaults to ``False``.  The LLM path MUST
remain disabled until data governance approval is confirmed.

When the LLM path is enabled it sends ONLY:
    - The top canonical entity names (strings, no document content).
    - Existing folder-name samples from the workspace (strings).

Document content is never sent to the LLM.

Security constraint (verbatim): "The LLM naming path must remain disabled until
data governance approval is confirmed. Do not send document content to the LLM
merely to generate folder names."
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Awaitable, Callable

from enterprise_ai_companion.capabilities.organisation.placement_ports import (
    GraphScorePort,
)

logger = logging.getLogger(__name__)

_MAX_NAME_LENGTH = 60
_TOP_ENTITY_COUNT = 3
_FALLBACK_NAME = "New Folder"

# Windows and POSIX filesystem forbidden characters.
_FILESYSTEM_FORBIDDEN_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Type alias for the LLM callable (same signature as llm_client.chat_complete).
_LLMCallable = Callable[[list[dict[str, str]], int, float], Awaitable[str]]


class FolderNamingService:
    """Generates proposed folder names for semantic document clusters.

    The deterministic strategy (always active) ranks canonical entity names by
    document frequency and joins the top results into a short, title-cased name.

    The LLM strategy (disabled by default) passes only entity names and folder
    samples to the LLM — never document content — and falls back to the
    deterministic result on failure.
    """

    def __init__(
        self,
        graph_score_port: GraphScorePort,
        llm_enabled: bool = False,
        _llm_complete: _LLMCallable | None = None,
    ) -> None:
        """
        Args:
            graph_score_port: Provides canonical entity sets per document.
            llm_enabled: Must be ``False`` (default) until data governance
                approval. Activating this sends top entity names to the LLM.
            _llm_complete: Callable with the same signature as
                ``llm_client.chat_complete``. Defaults to the real
                ``chat_complete`` when ``llm_enabled=True`` and this is
                ``None``. Inject a fake in tests to avoid network calls.
        """
        self._graph = graph_score_port
        self._llm_enabled = llm_enabled
        self._llm_complete = _llm_complete

    async def name_cluster(
        self,
        doc_ids: list[str],
        existing_folder_samples: list[str] | None = None,
        file_paths: dict[str, str] | None = None,
    ) -> str:
        """Return a short proposed folder name for the given document cluster.

        Args:
            doc_ids: Document IDs in the cluster.
            existing_folder_samples: Optional list of existing folder names from
                the workspace, passed to the LLM for stylistic consistency
                (ignored when ``llm_enabled=False``).
            file_paths: Optional mapping of doc_id → absolute file path, used
                for filename-keyword supplementation when entity sets are sparse.

        Returns:
            A sanitized, title-cased folder name. Falls back to
            ``"New Folder"`` when no useful entities are found.
        """
        top_entities = await self._top_entities(doc_ids, file_paths or {})

        if self._llm_enabled and top_entities:
            try:
                llm_name = await self._name_via_llm(
                    top_entities, existing_folder_samples or []
                )
                if llm_name:
                    logger.debug(
                        "[NAMING] LLM produced folder name: %r", llm_name
                    )
                    return llm_name
            except Exception as exc:
                logger.warning(
                    "[NAMING] LLM naming failed — using deterministic fallback: %s",
                    exc,
                )

        name = _deterministic_name(top_entities)
        logger.debug("[NAMING] Deterministic folder name: %r", name)
        return name

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _top_entities(
        self,
        doc_ids: list[str],
        file_paths: dict[str, str],
    ) -> list[str]:
        """Return the top ``_TOP_ENTITY_COUNT`` entities by document frequency."""
        counts: Counter[str] = Counter()
        for doc_id in doc_ids:
            try:
                fp = file_paths.get(doc_id, "")
                entities = await self._graph.get_canonicals_for_document(doc_id, fp)
                for entity in entities:
                    counts[entity] += 1
            except Exception as exc:
                logger.warning(
                    "[NAMING] Could not fetch entities for %s: %s", doc_id, exc
                )
        # Sort by count descending, then alphabetically for determinism.
        return [
            entity
            for entity, _ in sorted(
                counts.most_common(), key=lambda item: (-item[1], item[0])
            )[:_TOP_ENTITY_COUNT]
        ]

    async def _name_via_llm(
        self,
        top_entities: list[str],
        folder_samples: list[str],
    ) -> str:
        """Ask the LLM for a folder name using only entity names and folder samples.

        SECURITY: only entity name strings are sent — never document content.
        """
        entities_str = ", ".join(top_entities[:10])
        samples_clause = ""
        if folder_samples:
            quoted = ", ".join(f'"{s}"' for s in folder_samples[:5])
            samples_clause = f" Existing folder names for style reference: {quoted}."

        prompt = (
            f"Suggest a concise folder name (2–4 words, title case) for a group of "
            f"files related to these topics: {entities_str}.{samples_clause} "
            f"Reply with only the folder name — no punctuation at the end, "
            f"no explanation."
        )

        complete = self._llm_complete
        if complete is None:
            # Late import keeps llm_client out of the module-level dependency
            # graph so that tests can instantiate this service without network.
            from enterprise_ai_companion.capabilities.ai.llm_client import (
                chat_complete,
            )
            complete = chat_complete  # type: ignore[assignment]

        response = await complete(
            [{"role": "user", "content": prompt}],
            32,
            0.0,
        )
        candidate = response.strip().strip('"').strip("'")
        return _sanitize_name(candidate)


# ---------------------------------------------------------------------------
# Pure helpers — no I/O, fully testable standalone
# ---------------------------------------------------------------------------

def _deterministic_name(top_entities: list[str]) -> str:
    """Build a folder name from the top entity strings."""
    if not top_entities:
        return _FALLBACK_NAME

    parts: list[str] = []
    for entity in top_entities:
        # Normalize separators, then title-case each word.
        normalized = entity.replace("_", " ").replace("-", " ").strip()
        titled = " ".join(w.capitalize() for w in normalized.split() if w)
        if titled:
            parts.append(titled)

    if not parts:
        return _FALLBACK_NAME

    return _sanitize_name(" ".join(parts)) or _FALLBACK_NAME


def _sanitize_name(name: str) -> str:
    """Strip filesystem-forbidden characters, collapse whitespace, truncate."""
    cleaned = _FILESYSTEM_FORBIDDEN_RE.sub("", name)
    cleaned = " ".join(cleaned.split())  # collapse runs of whitespace
    if len(cleaned) > _MAX_NAME_LENGTH:
        # Truncate at a word boundary if possible.
        truncated = cleaned[:_MAX_NAME_LENGTH]
        boundary = truncated.rfind(" ")
        cleaned = truncated[:boundary] if boundary > 0 else truncated
    return cleaned.strip()
