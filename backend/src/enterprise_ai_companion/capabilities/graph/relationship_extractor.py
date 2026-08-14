"""Extracts relationships between known entities from text using a structured LLM call.

Operates after EntityExtractor — it receives the entity names that were found in
the same chunk and asks the LLM only about relationships between those entities.
This scoped prompt yields higher precision than open-ended relationship extraction.

No graph I/O occurs here — persistence is the caller's responsibility.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from enterprise_ai_companion.capabilities.ai.llm_client import chat_complete
from enterprise_ai_companion.capabilities.graph.graph_models import (
    ExtractedEntity,
    ExtractedRelationship,
    RelationshipType,
)

logger = logging.getLogger(__name__)

_MAX_INPUT_CHARS: int = 3_000
_MAX_OUTPUT_TOKENS: int = 2048

_REL_TYPES: str = ", ".join(r.value for r in RelationshipType)

_SYSTEM_PROMPT_TEMPLATE: str = (
    "You are a relationship extraction engine for an enterprise knowledge base.\n"
    "Given a text passage and a list of named entities found in that passage, "
    "identify relationships between those entities.\n"
    "Return ONLY valid JSON — no markdown fences, no commentary.\n\n"
    "Output schema:\n"
    "{{\n"
    '  "relationships": [\n'
    "    {{\n"
    '      "source": "<entity name from the provided list>",\n'
    '      "target": "<entity name from the provided list>",\n'
    '      "type": "<one of: {rel_types}>",\n'
    '      "confidence": <0.0-1.0, how certain you are this relationship exists>\n'
    "    }}\n"
    "  ]\n"
    "}}\n\n"
    "Rules:\n"
    "- Only use entity names from the provided list — do not invent new entities.\n"
    "- Only assert relationships that are clearly supported by the text.\n"
    "- Omit duplicate relationships (same source, target, and type).\n"
    '- Return {{"relationships": []}} if no relationships are evident.\n'
    "\nEntities in this passage:\n{{entity_list}}"
)


class RelationshipExtractor:
    """Extracts relationships between a known set of entities from text.

    Usage:
        extractor = RelationshipExtractor()
        rels = await extractor.extract(text, entities)
        # [ExtractedRelationship(source_name="Volvo", target_name="EV platform",
        #                        relationship_type=RelationshipType.OWNS, ...)]
    """

    async def extract(
        self,
        text: str,
        entities: list[ExtractedEntity],
    ) -> list[ExtractedRelationship]:
        """Return extracted relationships between the given entities.

        Args:
            text: The source passage (will be capped internally).
            entities: Entities already found in this passage by EntityExtractor.

        Returns:
            List of extracted relationships. Returns [] on failure or if
            fewer than 2 entities are provided (no relationship possible).
        """
        if len(entities) < 2 or not text.strip():
            return []

        entity_names = [e.name for e in entities]
        raw = await self._call_llm(text[:_MAX_INPUT_CHARS], entity_names)
        if raw is None:
            return []

        return self._parse(raw, entity_names)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _call_llm(
        self, text: str, entity_names: list[str]
    ) -> dict[str, Any] | None:
        entity_list = "\n".join(f"- {name}" for name in entity_names)
        system = _SYSTEM_PROMPT_TEMPLATE.format(
            rel_types=_REL_TYPES,
            entity_list=entity_list,
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ]
        try:
            response = await chat_complete(
                messages, max_tokens=_MAX_OUTPUT_TOKENS, temperature=0.0
            )
        except Exception as exc:
            logger.warning("RelationshipExtractor LLM call failed: %s", exc)
            return None

        return _parse_json(response)

    def _parse(
        self,
        raw: dict[str, Any],
        valid_names: list[str],
    ) -> list[ExtractedRelationship]:
        valid_set = {n.lower() for n in valid_names}
        results: list[ExtractedRelationship] = []
        seen: set[tuple[str, str, str]] = set()

        for item in raw.get("relationships", []):
            source = str(item.get("source", "")).strip()
            target = str(item.get("target", "")).strip()
            if not source or not target:
                continue
            # Reject hallucinated entities not in the provided list.
            if source.lower() not in valid_set or target.lower() not in valid_set:
                continue
            if source.lower() == target.lower():
                continue

            rel_type = _coerce_rel_type(item.get("type", ""))

            key = (source.lower(), target.lower(), rel_type.value)
            if key in seen:
                continue
            seen.add(key)

            try:
                confidence = float(item.get("confidence", 1.0))
                confidence = max(0.0, min(1.0, confidence))
            except (TypeError, ValueError):
                confidence = 1.0

            results.append(
                ExtractedRelationship(
                    source_name=source,
                    target_name=target,
                    relationship_type=rel_type,
                    confidence=confidence,
                )
            )

        return results


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _parse_json(raw: str) -> dict[str, Any] | None:
    try:
        return json.loads(raw)  # type: ignore[return-value]
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])  # type: ignore[return-value]
        except json.JSONDecodeError:
            pass
    logger.debug("RelationshipExtractor: could not parse JSON from: %s", raw[:200])
    return None


def _coerce_rel_type(value: Any) -> RelationshipType:
    try:
        return RelationshipType(str(value))
    except ValueError:
        return RelationshipType.RELATED_TO
