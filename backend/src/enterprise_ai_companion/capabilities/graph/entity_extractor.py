"""Extracts named entities from text using a structured LLM call.

Replaces the inline extraction logic that lived inside KnowledgeGraphService.
The extractor is a pure transformation: text-in, ExtractedEntity list-out.
No graph I/O occurs here — persistence is the caller's responsibility.

Prompt design:
- Single JSON object with an "entities" array (strict schema, no prose).
- Temperature 0.0 for maximum determinism.
- Source text capped at 3 000 characters to stay within context limits.
- Confidence field allows downstream enrichment to prefer high-confidence nodes.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from enterprise_ai_companion.capabilities.ai.llm_client import chat_complete
from enterprise_ai_companion.capabilities.graph.graph_models import (
    EntityType,
    ExtractedEntity,
)

logger = logging.getLogger(__name__)

_MAX_INPUT_CHARS: int = 3_000
_MAX_OUTPUT_TOKENS: int = 512

_ENTITY_TYPES: str = ", ".join(e.value for e in EntityType)

_SYSTEM_PROMPT: str = (
    "You are a named entity extraction engine for an enterprise knowledge base.\n"
    "Given a text passage, identify all meaningful named entities.\n"
    "Return ONLY valid JSON — no markdown fences, no commentary.\n\n"
    "Output schema:\n"
    "{\n"
    '  "entities": [\n'
    '    {\n'
    '      "name": "<entity name as it appears in the text>",\n'
    '      "type": "<one of: ' + _ENTITY_TYPES + '>",\n'
    '      "confidence": <0.0-1.0, how certain you are this is a real named entity>\n'
    "    }\n"
    "  ]\n"
    "}\n\n"
    "Rules:\n"
    "- Only include proper nouns and specific named things, not generic terms.\n"
    "- Omit duplicates — include each entity only once.\n"
    "- Use the most precise type available. Default to Concept only if no other type fits.\n"
    "- Confidence below 0.5 means you are uncertain — still include it.\n"
    "- Return {\"entities\": []} if no entities are found."
)


class EntityExtractor:
    """Extracts named entities from a text chunk via a structured LLM call.

    Usage:
        extractor = EntityExtractor()
        entities = await extractor.extract("Volvo Cars announced a new EV platform...")
        # [ExtractedEntity(name="Volvo Cars", entity_type=EntityType.ORGANIZATION, ...)]
    """

    async def extract(self, text: str) -> list[ExtractedEntity]:
        """Return extracted entities from text. Returns [] on failure."""
        if not text.strip():
            return []

        raw = await self._call_llm(text[:_MAX_INPUT_CHARS])
        if raw is None:
            return []

        return self._parse(raw)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _call_llm(self, text: str) -> dict[str, Any] | None:
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ]
        try:
            response = await chat_complete(
                messages, max_tokens=_MAX_OUTPUT_TOKENS, temperature=0.0
            )
        except Exception as exc:
            logger.debug("EntityExtractor LLM call failed: %s", exc)
            return None

        return _parse_json(response)

    def _parse(self, raw: dict[str, Any]) -> list[ExtractedEntity]:
        results: list[ExtractedEntity] = []
        seen_names: set[str] = set()

        for item in raw.get("entities", []):
            name = str(item.get("name", "")).strip()
            if not name or name.lower() in seen_names:
                continue
            seen_names.add(name.lower())

            entity_type = _coerce_entity_type(item.get("type", ""))
            try:
                confidence = float(item.get("confidence", 1.0))
                confidence = max(0.0, min(1.0, confidence))
            except (TypeError, ValueError):
                confidence = 1.0

            results.append(
                ExtractedEntity(
                    name=name,
                    entity_type=entity_type,
                    confidence=confidence,
                )
            )

        return results


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _parse_json(raw: str) -> dict[str, Any] | None:
    """Attempt to parse raw LLM output as JSON, stripping markdown fences."""
    try:
        return json.loads(raw)  # type: ignore[return-value]
    except json.JSONDecodeError:
        pass
    # Strip markdown code fence if present.
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])  # type: ignore[return-value]
        except json.JSONDecodeError:
            pass
    logger.debug("EntityExtractor: could not parse JSON from: %s", raw[:200])
    return None


def _coerce_entity_type(value: Any) -> EntityType:
    try:
        return EntityType(str(value))
    except ValueError:
        return EntityType.CONCEPT
