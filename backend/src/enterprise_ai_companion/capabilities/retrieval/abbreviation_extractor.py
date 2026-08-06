"""Abbreviation extractor for the indexing pipeline.

Scans plain text for parenthetical abbreviation–definition pairs and returns
them as structured matches.  Two patterns are detected:

    Pattern 1 — Abbreviation first:   "RRF (Reciprocal Rank Fusion)"
    Pattern 2 — Definition first:     "Reciprocal Rank Fusion (RRF)"

Each candidate is validated by checking that the abbreviation's letters match
the initial letters of the content words in the definition (stop-words
excluded).  This eliminates coincidental parenthetical expressions like
"some value (SV)" where the initials do not align.

Typical usage inside the indexing pipeline:

    extractor = AbbreviationExtractor(
        static_exclusions=frozenset({"ai", "api", "nlp"})  # already known
    )
    matches = extractor.extract(document_text)
    # → [AbbreviationMatch(abbreviation="rrf",
    #                       definition="Reciprocal Rank Fusion"), ...]
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Pattern 1 — Abbreviation appears first, definition in parentheses.
# Examples: "RRF (Reciprocal Rank Fusion)", "ETA (Estimated Time of Arrival)"
_ABBR_FIRST = re.compile(
    r"\b([A-Z]{2,8})\s*\(([a-zA-Z][^()]{2,79})\)",
    re.UNICODE,
)

# Pattern 2 — Definition appears first, abbreviation in parentheses.
# Requires definition words to start with a capital letter, reducing
# false positives from normal parenthetical remarks.
# Examples: "Reciprocal Rank Fusion (RRF)", "Key Performance Indicator (KPI)"
_DEF_FIRST = re.compile(
    r"\b((?:[A-Z][a-zA-Z\-]*\s+){1,7}[A-Z][a-zA-Z\-]*)\s*\(([A-Z]{2,8})\)",
    re.UNICODE,
)

# ---------------------------------------------------------------------------
# Stop-words excluded from acronym-initial matching
# ---------------------------------------------------------------------------

_ACRONYM_STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "of", "and", "for", "in", "to", "at", "by",
    "or", "with", "on", "as", "from", "its", "is", "are", "be",
})


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AbbreviationMatch:
    """A single abbreviation–definition pair extracted from a document.

    Attributes:
        abbreviation: Lowercase abbreviation token (e.g. "rrf").
        definition: Definition string preserving original casing
            (e.g. "Reciprocal Rank Fusion").
    """

    abbreviation: str
    definition: str


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------

class AbbreviationExtractor:
    """Extracts abbreviation–definition pairs from plain text.

    Instantiate once and reuse.  All methods are stateless with respect to
    document content — the only instance-level state is the optional set of
    abbreviations to exclude (i.e. those already present in the static
    expansion dictionary).

    Args:
        static_exclusions: Lowercase abbreviation tokens that should not be
            extracted because they are already handled by the static
            ``_EXPANSIONS`` dictionary in ``query_preprocessor.py``.
            Passing ``frozenset(_EXPANSIONS.keys())`` is recommended so
            dynamic entries never shadow static ones.
    """

    def __init__(
        self,
        static_exclusions: frozenset[str] | None = None,
    ) -> None:
        self._exclusions: frozenset[str] = static_exclusions or frozenset()

    def extract(self, text: str) -> list[AbbreviationMatch]:
        """Return all valid abbreviation–definition pairs found in *text*.

        Each abbreviation appears at most once in the returned list — the
        first occurrence in the text wins.  Duplicates are silently dropped.

        Args:
            text: Full plain-text content of a document.

        Returns:
            List of ``AbbreviationMatch`` objects, in order of first
            occurrence.  May be empty if no valid pairs are found.
        """
        seen: set[str] = set()
        results: list[AbbreviationMatch] = []

        for match in self._scan_abbr_first(text) + self._scan_def_first(text):
            key = match.abbreviation  # already lowercase
            if key in seen:
                continue
            seen.add(key)
            results.append(match)

        return results

    # ------------------------------------------------------------------
    # Private scanning methods
    # ------------------------------------------------------------------

    def _scan_abbr_first(self, text: str) -> list[AbbreviationMatch]:
        """Scan for Pattern 1: ABBR (Definition)."""
        matches: list[AbbreviationMatch] = []
        for m in _ABBR_FIRST.finditer(text):
            abbr_raw = m.group(1)
            definition = m.group(2).strip()
            if self._is_valid(abbr_raw, definition):
                matches.append(AbbreviationMatch(
                    abbreviation=abbr_raw.lower(),
                    definition=definition,
                ))
        return matches

    def _scan_def_first(self, text: str) -> list[AbbreviationMatch]:
        """Scan for Pattern 2: Definition (ABBR)."""
        matches: list[AbbreviationMatch] = []
        for m in _DEF_FIRST.finditer(text):
            definition = m.group(1).strip()
            abbr_raw = m.group(2)
            if self._is_valid(abbr_raw, definition):
                matches.append(AbbreviationMatch(
                    abbreviation=abbr_raw.lower(),
                    definition=definition,
                ))
        return matches

    def _is_valid(self, abbr: str, definition: str) -> bool:
        """Return True if *abbr* is an acceptable extraction candidate.

        Checks:
        1. The abbreviation is not in the static exclusion set.
        2. The abbreviation's letters match the initials of the content words
           in the definition (stop-words excluded).

        Args:
            abbr: Raw abbreviation string (e.g. "RRF"), any casing.
            definition: Definition string (e.g. "Reciprocal Rank Fusion").

        Returns:
            True if the candidate should be kept.
        """
        key = abbr.lower()
        if key in self._exclusions:
            return False
        return self._initials_match(abbr, definition)

    def _initials_match(self, abbr: str, definition: str) -> bool:
        """Return True if *abbr* initials align with *definition* content words.

        Stop-words are excluded from the definition before building the
        expected initial sequence, so "Optical Character Recognition (OCR)"
        passes (O, C, R → OCR) and "Some Other Thing (OCR)" fails
        (S, O, T ≠ O, C, R).

        Args:
            abbr: Uppercase abbreviation string (e.g. "OCR").
            definition: Definition phrase (e.g. "Optical Character Recognition").

        Returns:
            True when the expected initials equal ``abbr`` (case-insensitive).
        """
        words = re.split(r"\s+", definition.strip())
        content_words = [
            w.strip("(),.-;:")
            for w in words
            if w.strip("(),.-;:").lower() not in _ACRONYM_STOP_WORDS
            and w.strip("(),.-;:")
        ]
        initials = "".join(w[0].upper() for w in content_words if w)
        return initials == abbr.upper()
