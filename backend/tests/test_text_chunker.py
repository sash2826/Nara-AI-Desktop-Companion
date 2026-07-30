"""Unit tests for TextChunker."""

import pytest

from enterprise_ai_companion.capabilities.indexing.text_chunker import TextChunker


class TestChunker:
    def test_empty_text_returns_empty_list(self) -> None:
        chunker = TextChunker()
        assert chunker.chunk("") == []

    def test_whitespace_only_returns_empty_list(self) -> None:
        chunker = TextChunker()
        assert chunker.chunk("   \n\t  ") == []

    def test_short_text_produces_single_chunk(self) -> None:
        chunker = TextChunker(chunk_size=1500, overlap=200)
        text = "Hello world."
        result = chunker.chunk(text)
        assert len(result) == 1
        content, start, end = result[0]
        assert content == "Hello world."
        assert start == 0
        assert end == len(text)

    def test_long_text_produces_multiple_chunks(self) -> None:
        chunker = TextChunker(chunk_size=100, overlap=20)
        text = "A" * 250
        result = chunker.chunk(text)
        assert len(result) > 1

    def test_chunks_respect_max_size(self) -> None:
        chunker = TextChunker(chunk_size=100, overlap=20)
        text = "word " * 100  # 500 chars
        result = chunker.chunk(text)
        for content, _, _ in result:
            assert len(content) <= 100

    def test_overlap_preserved_between_chunks(self) -> None:
        chunker = TextChunker(chunk_size=50, overlap=10)
        text = "ABCDEFGHIJ" * 10  # 100 chars
        result = chunker.chunk(text)
        assert len(result) > 1
        # The end of chunk N should overlap with the start of chunk N+1
        for i in range(len(result) - 1):
            _, _, end_i = result[i]
            _, start_next, _ = result[i + 1]
            assert start_next < end_i  # overlap means next starts before this ends

    def test_chunk_indices_are_sequential(self) -> None:
        chunker = TextChunker(chunk_size=50, overlap=10)
        text = "X" * 200
        result = chunker.chunk(text)
        for i in range(len(result) - 1):
            _, _, end_i = result[i]
            _, start_next, _ = result[i + 1]
            assert start_next <= end_i  # non-overlapping or overlapping, but never a gap

    def test_invalid_overlap_raises(self) -> None:
        with pytest.raises(ValueError):
            TextChunker(chunk_size=100, overlap=100)

    def test_sentence_boundary_respected(self) -> None:
        chunker = TextChunker(chunk_size=60, overlap=10)
        # Two sentences, first one ends within the window
        text = "First sentence ends here. " + "B" * 50
        result = chunker.chunk(text)
        # First chunk should not cut in the middle of the second sentence's content
        assert len(result) >= 1
        first_content = result[0][0]
        # The period and space from the first sentence should be in chunk 0
        assert "First sentence ends here." in first_content
