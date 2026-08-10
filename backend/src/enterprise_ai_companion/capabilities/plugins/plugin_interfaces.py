"""Abstract base classes defining the extension points available to plugins.

A plugin implements one or more of these ABCs to participate in the
corresponding capability pipeline. The permission strings in the manifest
must align with the ABC(s) the plugin class implements:

  ``indexing.file_processing``  → FileProcessorPlugin
  ``indexing.text_processing``  → TextProcessorPlugin
  ``search.enrichment``         → SearchEnricherPlugin
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class FileProcessorPlugin(ABC):
    """Extract plain text from files of a custom type.

    Registered plugins are consulted before the built-in extractors so
    they can handle file extensions that the core system does not support,
    or override the default handling for a known extension.
    """

    @property
    @abstractmethod
    def supported_extensions(self) -> frozenset[str]:
        """Return lowercase dot-prefixed extensions, e.g. ``frozenset({".abc"})``."""

    @abstractmethod
    def extract_text(self, file_path: Path) -> str:
        """Extract and return plain text from *file_path*.

        Must be synchronous. Raise ``ValueError`` for unreadable files;
        the indexer will catch it and log the error.
        """


class TextProcessorPlugin(ABC):
    """Transform extracted text before it is chunked and embedded.

    Plugins in this category run in declaration order on the concatenated
    text produced by the file extractor.
    """

    @abstractmethod
    def process_text(self, text: str, file_path: str) -> str:
        """Return the (possibly modified) text.

        *file_path* is provided as context only; the plugin must not
        read the file itself.  Must be synchronous.
        """


class SearchEnricherPlugin(ABC):
    """Augment hybrid search results after the core ranking step.

    NOTE: Wiring into the search pipeline is deferred to Phase 07.
    The ABC is defined here so plugin authors can implement it against
    a stable interface.
    """

    @abstractmethod
    async def enrich_results(self, query: str, results: list) -> list:
        """Return the (possibly reordered or augmented) result list."""
