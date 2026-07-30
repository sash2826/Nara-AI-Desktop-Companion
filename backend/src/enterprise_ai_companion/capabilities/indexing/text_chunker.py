"""Splits plain text into overlapping character-based chunks for embedding."""

from __future__ import annotations

import re


# Sentence boundary pattern: split after . ! ? followed by whitespace or end.
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


class TextChunker:
    """Splits text into overlapping chunks, preferring sentence boundaries.

    Args:
        chunk_size: Maximum characters per chunk.
        overlap: Characters of overlap between consecutive chunks.
    """

    def __init__(self, chunk_size: int = 1500, overlap: int = 200) -> None:
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[tuple[str, int, int]]:
        """Return a list of (content, char_start, char_end) tuples.

        Chunks are at most chunk_size characters. Consecutive chunks share
        overlap characters from the end of the previous chunk to preserve
        context across boundaries.
        """
        text = text.strip()
        if not text:
            return []

        results: list[tuple[str, int, int]] = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))

            if end < len(text):
                # Try to break at a sentence boundary within the window.
                window = text[start:end]
                best_break = self._last_sentence_break(window)
                if best_break > self.overlap:
                    end = start + best_break

            chunk_text = text[start:end].strip()
            if chunk_text:
                results.append((chunk_text, start, end))

            if end >= len(text):
                break

            # Advance by (chunk_size - overlap) so the next chunk re-reads the
            # last `overlap` characters of this one.
            start = end - self.overlap

        return results

    def _last_sentence_break(self, text: str) -> int:
        """Return the character position of the last sentence break in text, or 0."""
        best = 0
        for match in _SENTENCE_END.finditer(text):
            best = match.start()
        return best
