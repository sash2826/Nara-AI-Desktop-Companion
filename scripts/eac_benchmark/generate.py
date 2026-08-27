"""Render a :class:`~scripts.eac_benchmark.catalog.TestFile` to disk."""

from __future__ import annotations

import os

from scripts.benchmark_corpus.common import write_docx, write_pdf, write_pptx, write_xlsx

from .catalog import TestFile


def write_test_file(tf: TestFile, out_dir: str) -> str:
    """Write one test file into ``out_dir`` and return its path."""
    path = os.path.join(out_dir, tf.filename)
    if tf.fmt == "pdf":
        write_pdf(path, tf.blocks)
    elif tf.fmt == "docx":
        write_docx(path, tf.blocks)
    elif tf.fmt == "xlsx":
        write_xlsx(path, tf.sheets)
    elif tf.fmt == "pptx":
        title, subtitle, slides = tf.slides
        write_pptx(path, title, subtitle, slides)
    else:
        raise ValueError(f"Unsupported format: {tf.fmt}")
    return path
