"""Unit tests for the query preprocessing pipeline."""

from __future__ import annotations

import pytest

from enterprise_ai_companion.capabilities.retrieval.query_preprocessor import (
    QueryPreprocessor,
    QueryPreprocessorConfig,
    SearchIntent,
    _detect_intent,
    _expand,
    _has_fuzzy_candidates,
    _looks_like_typo,
    _normalise,
    _remove_stop_words,
    _tokenise,
)


# ---------------------------------------------------------------------------
# _normalise
# ---------------------------------------------------------------------------

class TestNormalise:
    def test_lowercases(self) -> None:
        assert _normalise("Hello World") == "hello world"

    def test_collapses_whitespace(self) -> None:
        assert _normalise("  foo   bar  ") == "foo bar"

    def test_strips_leading_trailing(self) -> None:
        assert _normalise("  query  ") == "query"

    def test_unicode_nfc(self) -> None:
        # NFC normalisation should round-trip correctly for basic ASCII.
        assert _normalise("café") == "café"

    def test_empty_string(self) -> None:
        assert _normalise("") == ""

    def test_preserves_hyphens(self) -> None:
        assert _normalise("state-of-the-art") == "state-of-the-art"


# ---------------------------------------------------------------------------
# _tokenise
# ---------------------------------------------------------------------------

class TestTokenise:
    def test_splits_on_space(self) -> None:
        assert _tokenise("hello world") == ["hello", "world"]

    def test_splits_on_punctuation(self) -> None:
        tokens = _tokenise("hello, world! how?")
        assert "hello" in tokens
        assert "world" in tokens
        assert "how" in tokens

    def test_preserves_hyphenated_compounds(self) -> None:
        tokens = _tokenise("state-of-the-art model")
        assert "state-of-the-art" in tokens

    def test_discards_empty_parts(self) -> None:
        tokens = _tokenise("  ")
        assert tokens == []

    def test_single_char_kept(self) -> None:
        tokens = _tokenise("a b c")
        assert tokens == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# _remove_stop_words
# ---------------------------------------------------------------------------

class TestRemoveStopWords:
    def test_removes_common_stop_words(self) -> None:
        tokens = ["the", "quick", "brown", "fox"]
        assert _remove_stop_words(tokens) == ["quick", "brown", "fox"]

    def test_empty_list(self) -> None:
        assert _remove_stop_words([]) == []

    def test_all_stop_words(self) -> None:
        assert _remove_stop_words(["the", "a", "is"]) == []

    def test_preserves_non_stop_words(self) -> None:
        result = _remove_stop_words(["machine", "learning"])
        assert result == ["machine", "learning"]

    def test_preserves_case_sensitivity(self) -> None:
        # Stop-word list is lowercase; uppercased tokens are NOT removed.
        result = _remove_stop_words(["The", "quick"])
        assert "The" in result


# ---------------------------------------------------------------------------
# _expand
# ---------------------------------------------------------------------------

class TestExpand:
    def test_expands_known_abbreviation(self) -> None:
        extras = _expand(["ai"])
        assert "artificial intelligence" in extras

    def test_no_duplicates_in_expansion(self) -> None:
        tokens = ["ai", "ml"]
        extras = _expand(tokens)
        assert len(extras) == len(set(extras))

    def test_unknown_token_adds_nothing(self) -> None:
        assert _expand(["volcano"]) == []

    def test_does_not_repeat_original_tokens(self) -> None:
        # "docs" expands to ["documents", "documentation"]; "documents" should not appear if already in tokens.
        tokens = ["docs", "documents"]
        extras = _expand(tokens)
        assert "documents" not in extras

    def test_rag_expands(self) -> None:
        extras = _expand(["rag"])
        assert "retrieval augmented generation" in extras

    def test_empty_input(self) -> None:
        assert _expand([]) == []


# ---------------------------------------------------------------------------
# _detect_intent
# ---------------------------------------------------------------------------

class TestDetectIntent:
    def test_factual_from_what(self) -> None:
        assert _detect_intent(["what", "is", "neo4j"]) == SearchIntent.FACTUAL

    def test_factual_from_how(self) -> None:
        assert _detect_intent(["how", "does", "qdrant", "work"]) == SearchIntent.FACTUAL

    def test_navigational_from_find(self) -> None:
        assert _detect_intent(["find", "onboarding", "document"]) == SearchIntent.NAVIGATIONAL

    def test_comparison_from_vs(self) -> None:
        assert _detect_intent(["neo4j", "vs", "postgresql"]) == SearchIntent.COMPARISON

    def test_comparison_from_compare(self) -> None:
        assert _detect_intent(["compare", "sqlite", "postgres"]) == SearchIntent.COMPARISON

    def test_exploratory_when_no_signals(self) -> None:
        assert _detect_intent(["machine", "learning", "embeddings"]) == SearchIntent.EXPLORATORY

    def test_comparison_takes_priority_over_factual(self) -> None:
        # "vs" is a comparison signal; "how" is a factual signal.
        result = _detect_intent(["how", "do", "sqlite", "vs", "postgres", "compare"])
        assert result == SearchIntent.COMPARISON


# ---------------------------------------------------------------------------
# _looks_like_typo / _has_fuzzy_candidates
# ---------------------------------------------------------------------------

class TestLooksLikeTypo:
    def test_triple_repeated_char(self) -> None:
        assert _looks_like_typo("helllo") is True

    def test_normal_word_is_not_typo(self) -> None:
        assert _looks_like_typo("search") is False

    def test_high_consonant_density_short_token(self) -> None:
        # "srch" — 4 chars, 4 consonants → 100% consonant density → typo
        assert _looks_like_typo("srch") is True

    def test_normal_short_word(self) -> None:
        assert _looks_like_typo("run") is False


class TestHasFuzzyCandidates:
    def test_detects_typo_token(self) -> None:
        assert _has_fuzzy_candidates(["helllo"]) is True

    def test_clean_tokens_no_fuzzy(self) -> None:
        assert _has_fuzzy_candidates(["machine", "learning"]) is False

    def test_empty_list(self) -> None:
        assert _has_fuzzy_candidates([]) is False


# ---------------------------------------------------------------------------
# QueryPreprocessor — integration
# ---------------------------------------------------------------------------

class TestQueryPreprocessor:
    def test_process_returns_processed_query(self) -> None:
        pq = QueryPreprocessor().process("What is machine learning?")
        assert pq.original == "What is machine learning?"
        assert pq.normalised == "what is machine learning?"
        assert "machine" in pq.tokens
        assert "machine" in pq.filtered_tokens

    def test_stop_words_removed_from_filtered_tokens(self) -> None:
        pq = QueryPreprocessor().process("the quick brown fox")
        assert "the" not in pq.filtered_tokens
        assert "quick" in pq.filtered_tokens

    def test_search_text_excludes_stop_words(self) -> None:
        pq = QueryPreprocessor().process("what is the meaning of ai")
        assert "the" not in pq.search_text
        assert "is" not in pq.search_text

    def test_ai_expands_in_search_text(self) -> None:
        pq = QueryPreprocessor().process("ai document search")
        assert "artificial intelligence" in pq.search_text or "artificial intelligence" in pq.expanded_terms

    def test_intent_detected(self) -> None:
        pq = QueryPreprocessor().process("find the architecture document")
        assert pq.intent == SearchIntent.NAVIGATIONAL

    def test_comparison_intent(self) -> None:
        pq = QueryPreprocessor().process("sqlite vs postgres performance")
        assert pq.intent == SearchIntent.COMPARISON

    def test_exploratory_intent_default(self) -> None:
        pq = QueryPreprocessor().process("embedding models performance")
        assert pq.intent == SearchIntent.EXPLORATORY

    def test_empty_query_normalises_gracefully(self) -> None:
        pq = QueryPreprocessor().process("")
        assert pq.original == ""
        assert pq.tokens == []
        assert pq.search_text == ""

    def test_config_disables_stop_word_removal(self) -> None:
        cfg = QueryPreprocessorConfig(remove_stop_words=False)
        pq = QueryPreprocessor(config=cfg).process("the quick brown fox")
        assert "the" in pq.filtered_tokens

    def test_config_disables_expansion(self) -> None:
        cfg = QueryPreprocessorConfig(expand_query=False)
        pq = QueryPreprocessor(config=cfg).process("rag pipeline")
        assert pq.expanded_terms == []

    def test_config_disables_intent_detection(self) -> None:
        cfg = QueryPreprocessorConfig(detect_intent=False)
        pq = QueryPreprocessor(config=cfg).process("what is the meaning of life")
        assert pq.intent == SearchIntent.EXPLORATORY

    def test_no_duplicate_terms_in_search_text(self) -> None:
        # "documents" should appear once even if "docs" expands to include it
        # and "documents" is also in the query.
        pq = QueryPreprocessor().process("docs documents")
        terms = pq.search_text.split()
        assert len(terms) == len(set(terms))

    def test_fuzzy_flag_set_for_likely_typo(self) -> None:
        # "helllo" has three consecutive 'l' chars — triggers the repeated-char rule.
        pq = QueryPreprocessor().process("helllo documents")
        assert pq.has_fuzzy_candidates is True

    def test_fuzzy_flag_not_set_for_clean_query(self) -> None:
        pq = QueryPreprocessor().process("machine learning models")
        assert pq.has_fuzzy_candidates is False
