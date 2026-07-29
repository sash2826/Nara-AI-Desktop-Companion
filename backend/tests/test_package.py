"""Smoke tests verifying the package is importable and correctly structured."""

import enterprise_ai_companion


def test_package_importable() -> None:
    assert enterprise_ai_companion.__version__ == "0.1.0"


def test_capabilities_importable() -> None:
    from enterprise_ai_companion import capabilities  # noqa: F401


def test_subpackages_importable() -> None:
    from enterprise_ai_companion.capabilities import indexing, retrieval, ai  # noqa: F401
    from enterprise_ai_companion import infrastructure, api  # noqa: F401
