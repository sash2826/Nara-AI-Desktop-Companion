"""Conversation memory service — automatic summarisation of older turns.

After every N assistant turns the oldest M turns are summarised by the LLM
into a compressed string and stored in the conversations table. Subsequent
requests prepend this summary to the system message so the assistant can
reference earlier conclusions without re-reading the full history.

Design decisions:
- Summarisation is triggered by the caller (the conversations router) after
  persisting each assistant message, so it never blocks the streaming response.
- The LLM call uses a low temperature (0.0) for deterministic compression.
- If summarisation fails for any reason the summary column is left unchanged
  and the assistant continues without compressed memory — non-fatal.
- The summariser reads only the oldest SUMMARISE_TURNS messages so it does
  not grow unboundedly with conversation length.
"""

from __future__ import annotations

import logging

from enterprise_ai_companion.capabilities.ai.llm_client import chat_complete
from enterprise_ai_companion.capabilities.indexing.conversation_repository import (
    ConversationRepository,
)

logger = logging.getLogger(__name__)

# Trigger summarisation after this many assistant turns.
SUMMARISE_EVERY_N_TURNS: int = 10

# Summarise the oldest N messages (user + assistant pairs).
SUMMARISE_OLDEST_N_MESSAGES: int = 16

_SUMMARISE_SYSTEM_PROMPT = (
    "You are a precise assistant that compresses conversation history.\n"
    "Given a sequence of conversation turns, produce a concise summary (max 200 words) "
    "that preserves every factual claim, decision, and conclusion reached.\n"
    "Write in third person. Begin with 'Earlier in this conversation:'."
)


class ConversationMemoryService:
    """Manages turn counting and automatic summarisation for a conversation."""

    def __init__(self, repo: ConversationRepository) -> None:
        self._repo = repo

    async def on_assistant_turn_saved(self, conversation_id: str) -> None:
        """Called after each assistant message is persisted.

        Increments turn_count and triggers summarisation when the threshold
        is reached. Failures are logged but never propagated — the caller
        must not be blocked by summarisation errors.
        """
        try:
            new_count = await self._repo.increment_turn_count(conversation_id)
            if new_count % SUMMARISE_EVERY_N_TURNS == 0:
                await self._summarise(conversation_id)
        except Exception as exc:
            logger.warning(
                "ConversationMemoryService: turn-count update failed for %s: %s",
                conversation_id,
                exc,
            )

    async def get_summary_prefix(self, conversation_id: str) -> str | None:
        """Return the stored summary for injection into the system message, or None."""
        try:
            state = await self._repo.get_memory_state(conversation_id)
            return state.summary
        except Exception as exc:
            logger.warning(
                "ConversationMemoryService: could not read summary for %s: %s",
                conversation_id,
                exc,
            )
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _summarise(self, conversation_id: str) -> None:
        """Fetch the oldest messages and write a compressed summary."""
        messages = await self._repo.load_oldest_messages(
            conversation_id, limit=SUMMARISE_OLDEST_N_MESSAGES
        )
        if not messages:
            return

        transcript = "\n".join(
            f"{m.role.upper()}: {m.content}" for m in messages
        )

        prompt_messages = [
            {"role": "system", "content": _SUMMARISE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Summarise the following conversation turns:\n\n"
                    f"{transcript}"
                ),
            },
        ]

        try:
            summary = await chat_complete(
                prompt_messages,
                max_tokens=300,
                temperature=0.0,
            )
            await self._repo.save_summary(conversation_id, summary.strip())
            logger.info(
                "ConversationMemoryService: summary saved for %s (%d chars)",
                conversation_id,
                len(summary),
            )
        except Exception as exc:
            logger.warning(
                "ConversationMemoryService: LLM summarisation failed for %s: %s",
                conversation_id,
                exc,
            )
