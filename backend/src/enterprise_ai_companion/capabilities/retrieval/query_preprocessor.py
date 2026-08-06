"""Query preprocessing pipeline for the search subsystem.

Each stage is independently replaceable and can be toggled via QueryPreprocessorConfig.
The pipeline produces a ProcessedQuery that carries both the clean text for
keyword/semantic search and structured metadata for downstream ranking.

Pipeline stages (in order):
    1. Normalise   — lowercase, unicode normalisation, collapse whitespace
    2. Tokenise    — split on whitespace and punctuation boundaries
    3. Stop-word removal — filter common English stop-words from token list
    4. Typo tolerance  — detect short/misspelled tokens and mark them for fuzzy matching
    5. Query expansion — add common synonyms and abbreviation expansions
    6. Intent detection — classify the query into a SearchIntent

The final text used by search providers is reassembled from the filtered tokens
(stop-words removed). The original, unaltered query is preserved for cases where
the raw form is better (e.g., exact phrase matching in FTS5).
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

class SearchIntent(str, Enum):
    """Broad classification of the user's search intent."""

    FACTUAL = "factual"          # Specific fact lookup: "who founded Volvo"
    NAVIGATIONAL = "navigational"  # Finding a specific document/file
    EXPLORATORY = "exploratory"  # Open-ended discovery
    COMPARISON = "comparison"    # Comparing two or more things


@dataclass(frozen=True)
class ProcessedQuery:
    """Result of running a raw query through the preprocessing pipeline.

    Attributes:
        original: The unmodified input string.
        normalised: Lowercased, unicode-normalised, whitespace-collapsed text.
        tokens: All tokens after normalisation (stop-words still present).
        filtered_tokens: Tokens with stop-words removed — use for search.
        expanded_terms: Additional terms added by query expansion.
        intent: Detected search intent.
        has_fuzzy_candidates: True if any token looks like a possible typo.
        search_text: Reassembled string from filtered_tokens + expanded_terms.
            This is the recommended string to pass to keyword and semantic search.
    """

    original: str
    normalised: str
    tokens: list[str]
    filtered_tokens: list[str]
    expanded_terms: list[str]
    intent: SearchIntent
    has_fuzzy_candidates: bool
    search_text: str


@dataclass
class QueryPreprocessorConfig:
    """Feature flags for the preprocessing pipeline."""

    remove_stop_words: bool = True
    expand_query: bool = True
    detect_intent: bool = True
    flag_fuzzy_candidates: bool = True


# ---------------------------------------------------------------------------
# Stop-word list
# ---------------------------------------------------------------------------

# Compact English stop-word set tuned for enterprise knowledge search.
# Preserves domain-meaningful short words (e.g. "no", "not", "up") that carry
# semantic weight in technical queries.
_STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can",
    "this", "that", "these", "those", "it", "its", "i", "my", "me",
    "we", "our", "you", "your", "he", "his", "she", "her", "they", "their",
    "what", "which", "who", "whom", "when", "where", "how",
    "about", "into", "through", "during", "before", "after",
    "above", "below", "between", "each", "so", "than", "too", "very",
    "just", "also", "then", "any", "all", "both", "few", "more", "most",
    "other", "some", "such", "own", "same",
})

# ---------------------------------------------------------------------------
# Query expansion dictionary
# ---------------------------------------------------------------------------

# Maps common abbreviations and synonyms to their expanded forms.
# Only expands when the token is an exact (lowercased) match.
_EXPANSIONS: dict[str, list[str]] = {
    "ai":    ["artificial intelligence", "machine learning"],
    "ml":    ["machine learning"],
    "nlp":   ["natural language processing"],
    "api":   ["application programming interface"],
    "db":    ["database"],
    "doc":   ["document"],
    "docs":  ["documents", "documentation"],
    "config": ["configuration"],
    "auth":  ["authentication", "authorisation"],
    "ui":    ["user interface"],
    "ux":    ["user experience"],
    "vs":    ["versus", "compared to"],
    "k8s":  ["kubernetes"],
    "ci":   ["continuous integration"],
    "cd":   ["continuous delivery", "continuous deployment"],
    "rag":  ["retrieval augmented generation"],
    "llm":  ["large language model"],
    "ocr":  ["optical character recognition"],
}

# ---------------------------------------------------------------------------
# Intent signals
# ---------------------------------------------------------------------------

_FACTUAL_SIGNALS: frozenset[str] = frozenset({
    "who", "what", "when", "where", "why", "how", "which", "define",
    "explain", "describe", "tell", "mean", "means",
})

_NAVIGATIONAL_SIGNALS: frozenset[str] = frozenset({
    "find", "open", "show", "go", "navigate", "search", "locate", "get",
    "file", "document", "folder", "path",
})

_COMPARISON_SIGNALS: frozenset[str] = frozenset({
    "vs", "versus", "compare", "difference", "differences", "between",
    "better", "worse", "pros", "cons", "or",
})


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class QueryPreprocessor:
    """Transforms a raw user query into a structured ProcessedQuery.

    Designed to be instantiated once and reused. All stages are stateless.

    Usage:
        preprocessor = QueryPreprocessor()
        pq = preprocessor.process("AI models for document retrieval")
        # pq.search_text  →  "models document retrieval artificial intelligence machine learning"
        # pq.intent       →  SearchIntent.EXPLORATORY
    """

    def __init__(self, config: QueryPreprocessorConfig | None = None) -> None:
        self._cfg = config or QueryPreprocessorConfig()
        self._dynamic_expansions: dict[str, list[str]] = {}

    def merge_expansions(self, dynamic: dict[str, list[str]]) -> None:
        """Replace the dynamic expansion set with entries from discovered abbreviations.

        Static ``_EXPANSIONS`` always takes precedence — any key in *dynamic*
        that already exists in ``_EXPANSIONS`` is silently ignored so
        document-derived entries can never shadow the curated baseline.

        This method is called after each indexing job completes and at
        application startup (to prime from abbreviations persisted in
        previous sessions).

        Args:
            dynamic: Mapping of ``{lowercase_abbreviation: [definition, ...]}``
                as returned by ``AbbreviationRepository.load_all()``.
        """
        self._dynamic_expansions = {
            k: v for k, v in dynamic.items() if k not in _EXPANSIONS
        }
        logger.debug(
            "Dynamic abbreviation expansions reloaded: %d entries",
            len(self._dynamic_expansions),
        )

    def process(self, raw_query: str) -> ProcessedQuery:
        """Run the full preprocessing pipeline on raw_query.

        Args:
            raw_query: Unmodified string from the user.

        Returns:
            ProcessedQuery with all derived fields populated.
        """
        normalised = _normalise(raw_query)
        tokens = _tokenise(normalised)

        filtered = _remove_stop_words(tokens) if self._cfg.remove_stop_words else tokens
        expanded = (
            _expand(filtered, self._dynamic_expansions)
            if self._cfg.expand_query
            else []
        )
        intent = _detect_intent(tokens) if self._cfg.detect_intent else SearchIntent.EXPLORATORY
        fuzzy = _has_fuzzy_candidates(filtered) if self._cfg.flag_fuzzy_candidates else False

        # Reassemble search text: filtered tokens + unique expanded terms.
        search_parts = filtered + [t for t in expanded if t not in filtered]
        search_text = " ".join(search_parts) if search_parts else normalised

        return ProcessedQuery(
            original=raw_query,
            normalised=normalised,
            tokens=tokens,
            filtered_tokens=filtered,
            expanded_terms=expanded,
            intent=intent,
            has_fuzzy_candidates=fuzzy,
            search_text=search_text,
        )


# ---------------------------------------------------------------------------
# Pipeline stage implementations
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    """Lowercase, unicode-normalise (NFC), and collapse internal whitespace."""
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _tokenise(text: str) -> list[str]:
    """Split on whitespace and punctuation, keeping hyphenated compounds whole.

    Tokens shorter than 1 character are discarded.
    """
    # Split on whitespace or punctuation except hyphens within words.
    parts = re.split(r"[\s,;:!?()[\]{}<>\"']+", text)
    tokens: list[str] = []
    for part in parts:
        part = part.strip("-").strip()
        if len(part) >= 1:
            tokens.append(part)
    return tokens


def _remove_stop_words(tokens: list[str]) -> list[str]:
    """Remove tokens that are in the stop-word list."""
    return [t for t in tokens if t not in _STOP_WORDS]


def _expand(
    tokens: list[str],
    dynamic: dict[str, list[str]] | None = None,
) -> list[str]:
    """Return additional terms for tokens that match the expansion dictionaries.

    Consults the static ``_EXPANSIONS`` first, then the dynamic entries
    (document-derived abbreviations).  Static entries always win — a token
    handled by ``_EXPANSIONS`` is not looked up in *dynamic*.

    Only the *new* terms are returned — the original tokens remain in
    ``filtered_tokens``.

    Args:
        tokens: Filtered token list from the current query.
        dynamic: Optional dynamic expansion mapping merged from
            ``AbbreviationRepository.load_all()``.  Pass ``None`` (or omit)
            when no dynamic expansions are available.

    Returns:
        List of additional expansion strings (may be multi-word phrases).
    """
    additions: list[str] = []
    seen: set[str] = set(tokens)
    for token in tokens:
        static_expansions = _EXPANSIONS.get(token, [])
        for expansion in static_expansions:
            if expansion not in seen:
                additions.append(expansion)
                seen.add(expansion)
        # Only consult dynamic expansions for tokens not covered by static dict.
        if not static_expansions and dynamic:
            for expansion in dynamic.get(token, []):
                if expansion not in seen:
                    additions.append(expansion)
                    seen.add(expansion)
    return additions


def _detect_intent(tokens: list[str]) -> SearchIntent:
    """Classify the query intent from the token set using signal words."""
    token_set = set(tokens)

    if token_set & _COMPARISON_SIGNALS:
        return SearchIntent.COMPARISON

    if token_set & _FACTUAL_SIGNALS:
        return SearchIntent.FACTUAL

    if token_set & _NAVIGATIONAL_SIGNALS:
        return SearchIntent.NAVIGATIONAL

    return SearchIntent.EXPLORATORY


def _has_fuzzy_candidates(tokens: list[str]) -> bool:
    """Return True if any token looks like it might be a typo.

    Heuristics:
    - Token length 2–5 with unusual consonant clusters often indicates a typo.
    - Token contains repeated characters (e.g. "helllo").
    - Token looks like it has a transposition (not detectable without a dictionary,
      so we conservatively flag very short unknown-looking tokens).

    This flag allows downstream providers to enable fuzzy matching when True.
    """
    for token in tokens:
        if _looks_like_typo(token):
            return True
    return False


def _looks_like_typo(token: str) -> bool:
    """Return True when the token exhibits common typo patterns.

    Checks:
    1. Repeated consecutive identical characters (e.g. "seach" → no, "seaach" → yes).
    2. Token is 3–6 chars but consists almost entirely of consonants (likely typo or abbreviation).
    """
    # Repeated characters (3+ identical in a row)
    if re.search(r"(.)\1{2,}", token):
        return True

    # High consonant density in short tokens (≤6 chars, >70% consonants)
    if 3 <= len(token) <= 6:
        consonants = sum(1 for c in token if c.isalpha() and c not in "aeiou")
        if len(token) > 0 and consonants / len(token) > 0.7:
            return True

    return False
