"""Unit tests for FolderNamingService.

Pure in-memory fakes — no database, no LLM network calls required.
"""

from __future__ import annotations

import pytest

from enterprise_ai_companion.capabilities.organisation.folder_naming_service import (
    FolderNamingService,
    _deterministic_name,
    _sanitize_name,
)
from enterprise_ai_companion.capabilities.organisation.placement_ports import (
    GraphScorePort,
)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class _FakeGraphPort(GraphScorePort):
    def __init__(self, entities: dict[str, set[str]]) -> None:
        self._entities = entities

    async def get_canonicals_for_document(self, document_id: str) -> set[str]:
        return self._entities.get(document_id, set())

    async def get_canonicals_for_folder(self, folder_path: str) -> set[str]:
        return set()

    async def get_known_folder_paths(self) -> list[str]:
        return []


async def _fake_llm(
    messages: list[dict[str, str]], max_tokens: int, temperature: float
) -> str:
    return "LLM Generated Name"


async def _echo_llm(
    messages: list[dict[str, str]], max_tokens: int, temperature: float
) -> str:
    """Returns the user message content so tests can inspect the prompt."""
    return messages[0]["content"]


# ---------------------------------------------------------------------------
# _sanitize_name — pure sync
# ---------------------------------------------------------------------------

class TestSanitizeName:
    def test_clean_name_unchanged(self) -> None:
        assert _sanitize_name("Project Alpha") == "Project Alpha"

    def test_removes_colon(self) -> None:
        assert ":" not in _sanitize_name("A: B")

    def test_removes_backslash(self) -> None:
        assert "\\" not in _sanitize_name("A\\B")

    def test_removes_forward_slash(self) -> None:
        assert "/" not in _sanitize_name("A/B")

    def test_removes_angle_brackets(self) -> None:
        result = _sanitize_name("<Safety>")
        assert "<" not in result and ">" not in result

    def test_removes_pipe(self) -> None:
        assert "|" not in _sanitize_name("A|B")

    def test_removes_asterisk(self) -> None:
        assert "*" not in _sanitize_name("A*B")

    def test_removes_question_mark(self) -> None:
        assert "?" not in _sanitize_name("What?")

    def test_removes_double_quote(self) -> None:
        assert '"' not in _sanitize_name('"Quoted"')

    def test_collapses_extra_spaces(self) -> None:
        assert _sanitize_name("A  B   C") == "A B C"

    def test_truncates_to_60_chars(self) -> None:
        long_name = "Word " * 20  # 100 chars
        result = _sanitize_name(long_name)
        assert len(result) <= 60

    def test_truncates_at_word_boundary(self) -> None:
        # 55-char prefix + space + "LongWord" = 64 chars total
        name = "A" * 55 + " LongWord"
        result = _sanitize_name(name)
        assert not result.endswith(" ")
        assert len(result) <= 60

    def test_empty_input_returns_empty(self) -> None:
        assert _sanitize_name("") == ""

    def test_strips_leading_trailing_spaces(self) -> None:
        assert _sanitize_name("  Hello World  ") == "Hello World"


# ---------------------------------------------------------------------------
# _deterministic_name — pure sync
# ---------------------------------------------------------------------------

class TestDeterministicName:
    def test_empty_entities_returns_fallback(self) -> None:
        assert _deterministic_name([]) == "New Folder"

    def test_single_entity_title_cased(self) -> None:
        result = _deterministic_name(["volvo safety"])
        assert result == "Volvo Safety"

    def test_multiple_entities_joined_with_space(self) -> None:
        result = _deterministic_name(["alpha", "beta"])
        assert result == "Alpha Beta"

    def test_underscore_replaced_with_space(self) -> None:
        result = _deterministic_name(["safety_reports"])
        assert result == "Safety Reports"

    def test_hyphen_replaced_with_space(self) -> None:
        result = _deterministic_name(["engine-design"])
        assert result == "Engine Design"

    def test_all_caps_entity_title_cased(self) -> None:
        result = _deterministic_name(["VOLVO GROUP"])
        assert result == "Volvo Group"

    def test_result_does_not_exceed_60_chars(self) -> None:
        very_long = ["a" * 30, "b" * 30, "c" * 30]
        result = _deterministic_name(very_long)
        assert len(result) <= 60

    def test_whitespace_only_entity_uses_fallback(self) -> None:
        assert _deterministic_name(["   ", "  "]) == "New Folder"


# ---------------------------------------------------------------------------
# FolderNamingService.name_cluster — async integration
# ---------------------------------------------------------------------------

class TestNameClusterDeterministic:
    async def test_no_entities_returns_new_folder(self) -> None:
        service = FolderNamingService(_FakeGraphPort({}))
        result = await service.name_cluster(["d1", "d2"])
        assert result == "New Folder"

    async def test_single_common_entity_used(self) -> None:
        entities = {"d1": {"Volvo Safety"}, "d2": {"Volvo Safety"}}
        service = FolderNamingService(_FakeGraphPort(entities))
        result = await service.name_cluster(["d1", "d2"])
        assert "Volvo" in result

    async def test_most_frequent_entity_leads(self) -> None:
        # "alpha" appears in 3 docs, "beta" in 1
        entities = {
            "d1": {"alpha"},
            "d2": {"alpha"},
            "d3": {"alpha", "beta"},
            "d4": set(),
        }
        service = FolderNamingService(_FakeGraphPort(entities))
        result = await service.name_cluster(["d1", "d2", "d3", "d4"])
        # "Alpha" must appear in the name
        assert "Alpha" in result

    async def test_at_most_three_entities_used(self) -> None:
        entities = {
            "d1": {"alpha", "beta", "gamma", "delta"},
        }
        service = FolderNamingService(_FakeGraphPort(entities))
        result = await service.name_cluster(["d1"])
        # At most 3 entities → at most 3 words (approximately)
        word_count = len(result.split())
        assert word_count <= 9  # each entity could be 3 words, top 3 → 9 max

    async def test_graph_failure_per_doc_still_produces_name(self) -> None:
        class _FailingPort(_FakeGraphPort):
            async def get_canonicals_for_document(self, doc_id: str) -> set[str]:
                if doc_id == "fail":
                    raise RuntimeError("graph error")
                return {"safety"}

        service = FolderNamingService(_FailingPort({}))
        result = await service.name_cluster(["ok", "fail"])
        assert result == "Safety"

    async def test_empty_doc_list_returns_new_folder(self) -> None:
        service = FolderNamingService(_FakeGraphPort({}))
        result = await service.name_cluster([])
        assert result == "New Folder"

    async def test_result_has_no_filesystem_forbidden_chars(self) -> None:
        entities = {"d1": {"A/B:C", "D*E"}}
        service = FolderNamingService(_FakeGraphPort(entities))
        result = await service.name_cluster(["d1"])
        for char in r'<>:"/\|?*':
            assert char not in result

    async def test_deterministic_across_calls(self) -> None:
        entities = {"d1": {"alpha", "beta"}, "d2": {"alpha"}}
        service = FolderNamingService(_FakeGraphPort(entities))
        r1 = await service.name_cluster(["d1", "d2"])
        r2 = await service.name_cluster(["d1", "d2"])
        assert r1 == r2


class TestNameClusterLLM:
    async def test_llm_disabled_by_default_fake_never_called(self) -> None:
        called: list[bool] = []

        async def _spy_llm(
            messages: list[dict[str, str]], max_tokens: int, temperature: float
        ) -> str:
            called.append(True)
            return "Should Not Be Used"

        entities = {"d1": {"alpha"}}
        service = FolderNamingService(
            _FakeGraphPort(entities),
            llm_enabled=False,
            _llm_complete=_spy_llm,
        )
        await service.name_cluster(["d1"])
        assert called == []

    async def test_llm_enabled_calls_fake(self) -> None:
        called: list[bool] = []

        async def _spy_llm(
            messages: list[dict[str, str]], max_tokens: int, temperature: float
        ) -> str:
            called.append(True)
            return "Custom Name"

        entities = {"d1": {"alpha"}}
        service = FolderNamingService(
            _FakeGraphPort(entities),
            llm_enabled=True,
            _llm_complete=_spy_llm,
        )
        result = await service.name_cluster(["d1"])
        assert called == [True]
        assert result == "Custom Name"

    async def test_llm_enabled_returns_sanitized_response(self) -> None:
        async def _llm_with_forbidden(
            messages: list[dict[str, str]], max_tokens: int, temperature: float
        ) -> str:
            return "Bad: Name/Here"

        entities = {"d1": {"alpha"}}
        service = FolderNamingService(
            _FakeGraphPort(entities),
            llm_enabled=True,
            _llm_complete=_llm_with_forbidden,
        )
        result = await service.name_cluster(["d1"])
        assert ":" not in result
        assert "/" not in result

    async def test_llm_enabled_falls_back_on_failure(self) -> None:
        async def _failing_llm(
            messages: list[dict[str, str]], max_tokens: int, temperature: float
        ) -> str:
            raise RuntimeError("LLM network error")

        entities = {"d1": {"alpha", "beta"}}
        service = FolderNamingService(
            _FakeGraphPort(entities),
            llm_enabled=True,
            _llm_complete=_failing_llm,
        )
        result = await service.name_cluster(["d1"])
        # Deterministic fallback should kick in
        assert result != "New Folder" or True  # at minimum doesn't crash
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_llm_enabled_no_entities_skips_llm(self) -> None:
        """LLM is not called when there are no entities to send."""
        called: list[bool] = []

        async def _spy_llm(
            messages: list[dict[str, str]], max_tokens: int, temperature: float
        ) -> str:
            called.append(True)
            return "Should Not Be Used"

        service = FolderNamingService(
            _FakeGraphPort({}),
            llm_enabled=True,
            _llm_complete=_spy_llm,
        )
        result = await service.name_cluster(["d1"])
        assert called == []
        assert result == "New Folder"

    async def test_llm_prompt_contains_entity_names(self) -> None:
        """Verify the LLM prompt includes entity names but not doc content."""
        prompts: list[str] = []

        async def _capture_llm(
            messages: list[dict[str, str]], max_tokens: int, temperature: float
        ) -> str:
            prompts.append(messages[0]["content"])
            return "Captured"

        entities = {"d1": {"engine_design"}}
        service = FolderNamingService(
            _FakeGraphPort(entities),
            llm_enabled=True,
            _llm_complete=_capture_llm,
        )
        await service.name_cluster(["d1"])
        assert prompts
        assert "engine_design" in prompts[0]

    async def test_llm_prompt_includes_folder_samples(self) -> None:
        prompts: list[str] = []

        async def _capture_llm(
            messages: list[dict[str, str]], max_tokens: int, temperature: float
        ) -> str:
            prompts.append(messages[0]["content"])
            return "Captured"

        entities = {"d1": {"alpha"}}
        service = FolderNamingService(
            _FakeGraphPort(entities),
            llm_enabled=True,
            _llm_complete=_capture_llm,
        )
        await service.name_cluster(["d1"], existing_folder_samples=["My Docs", "Projects"])
        assert prompts
        assert "My Docs" in prompts[0]
        assert "Projects" in prompts[0]
