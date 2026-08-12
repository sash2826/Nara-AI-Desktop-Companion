"""
Generate a well-formatted PDF describing the Enterprise AI Companion search pipeline.
Usage:  uv run --with reportlab python scripts/generate_search_pipeline_pdf.py
Output: docs/Search-Pipeline-Architecture.pdf
"""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, KeepTogether, Preformatted,
    NextPageTemplate, PageBreak,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ── Palette ──────────────────────────────────────────────────────────────────
VOLVO_BLUE   = colors.HexColor("#003399")
VOLVO_LIGHT  = colors.HexColor("#E8EDF6")
ACCENT       = colors.HexColor("#0066CC")
CODE_BG      = colors.HexColor("#F4F6FA")
CODE_BORDER  = colors.HexColor("#C8D0E0")
RULE_COLOR   = colors.HexColor("#C0C8D8")
TEXT_DARK    = colors.HexColor("#1A1A2E")
TEXT_MID     = colors.HexColor("#4A4A6A")
WHITE        = colors.white

OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "Search-Pipeline-Architecture.pdf"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)


# ── Styles ────────────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    def add(name, **kw):
        if name not in base:
            base.add(ParagraphStyle(name=name, **kw))
        return base[name]

    add("DocTitle",
        fontName="Helvetica-Bold", fontSize=28, textColor=WHITE,
        spaceAfter=6, alignment=TA_CENTER, leading=34)

    add("DocSubtitle",
        fontName="Helvetica", fontSize=13, textColor=colors.HexColor("#B0C4E8"),
        alignment=TA_CENTER, spaceAfter=4)

    add("DocMeta",
        fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#8899BB"),
        alignment=TA_CENTER, spaceAfter=0)

    add("H1",
        fontName="Helvetica-Bold", fontSize=17, textColor=VOLVO_BLUE,
        spaceBefore=20, spaceAfter=6, leading=22)

    add("H2",
        fontName="Helvetica-Bold", fontSize=13, textColor=ACCENT,
        spaceBefore=14, spaceAfter=4, leading=17)

    add("H3",
        fontName="Helvetica-Bold", fontSize=11, textColor=TEXT_DARK,
        spaceBefore=10, spaceAfter=3, leading=15)

    add("Body",
        fontName="Helvetica", fontSize=10, textColor=TEXT_DARK,
        leading=15, spaceAfter=5, alignment=TA_JUSTIFY)

    add("Bullet",
        fontName="Helvetica", fontSize=10, textColor=TEXT_DARK,
        leading=14, spaceAfter=3, leftIndent=14, bulletIndent=4,
        bulletFontName="Helvetica", bulletFontSize=10)

    add("Code",
        fontName="Courier", fontSize=9, textColor=TEXT_DARK,
        leading=13, leftIndent=6, spaceAfter=2)

    add("Caption",
        fontName="Helvetica-Oblique", fontSize=9, textColor=TEXT_MID,
        alignment=TA_CENTER, spaceAfter=6)

    add("TocEntry",
        fontName="Helvetica", fontSize=10, textColor=TEXT_DARK,
        leading=16, leftIndent=0)

    add("TocEntryH2",
        fontName="Helvetica", fontSize=9, textColor=TEXT_MID,
        leading=14, leftIndent=14)

    return base


# ── Code block helper ─────────────────────────────────────────────────────────
def code_block(text, styles):
    lines = text.strip("\n").split("\n")
    paras = [Preformatted(line, styles["Code"]) for line in lines]
    inner = Table([[p] for p in paras],
                  colWidths=[14.5 * cm],
                  style=TableStyle([
                      ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
                      ("BOX",        (0, 0), (-1, -1), 0.5, CODE_BORDER),
                      ("LEFTPADDING",  (0, 0), (-1, -1), 8),
                      ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                      ("TOPPADDING",   (0, 0), (-1, -1), 6),
                      ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
                  ]))
    return inner


# ── Page templates ────────────────────────────────────────────────────────────
def _cover_page_bg(canvas, doc):
    canvas.saveState()
    w, h = A4
    # Full-bleed header band
    canvas.setFillColor(VOLVO_BLUE)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    # Decorative lighter stripe
    canvas.setFillColor(colors.HexColor("#001F66"))
    canvas.rect(0, h * 0.38, w, h * 0.02, fill=1, stroke=0)
    canvas.restoreState()


def _content_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    # Left accent bar
    canvas.setFillColor(VOLVO_BLUE)
    canvas.rect(0, 0, 0.5 * cm, h, fill=1, stroke=0)
    # Header rule
    canvas.setStrokeColor(RULE_COLOR)
    canvas.setLineWidth(0.5)
    canvas.line(1.5 * cm, h - 1.8 * cm, w - 1.5 * cm, h - 1.8 * cm)
    # Header text
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TEXT_MID)
    canvas.drawString(1.5 * cm, h - 1.5 * cm, "Enterprise AI Companion")
    canvas.drawRightString(w - 1.5 * cm, h - 1.5 * cm, "Search Pipeline Architecture")
    # Footer rule
    canvas.line(1.5 * cm, 1.5 * cm, w - 1.5 * cm, 1.5 * cm)
    # Page number
    canvas.drawCentredString(w / 2, 1.1 * cm, str(doc.page - 1))  # -1 skips cover
    canvas.restoreState()


# ── Document builder ──────────────────────────────────────────────────────────
def build_pdf():
    styles = build_styles()

    doc = BaseDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=2.4 * cm,
        bottomMargin=2.2 * cm,
        title="Search Pipeline Architecture",
        author="Enterprise AI Companion",
        subject="Hybrid semantic + keyword search pipeline",
    )

    w, h = A4
    cover_frame = Frame(0, 0, w, h, leftPadding=2*cm, rightPadding=2*cm,
                        topPadding=h*0.46, bottomPadding=0, id="cover")
    content_frame = Frame(1.8*cm, 1.8*cm,
                          w - 3.6*cm, h - 4.2*cm,
                          id="content")

    doc.addPageTemplates([
        PageTemplate(id="Cover",   frames=[cover_frame],   onPage=_cover_page_bg),
        PageTemplate(id="Content", frames=[content_frame], onPage=_content_page),
    ])

    story = []

    # ── Cover page ─────────────────────────────────────────────────────────────
    story.append(NextPageTemplate("Cover"))

    story.append(Paragraph("Search Pipeline", styles["DocTitle"]))
    story.append(Paragraph("Architecture", styles["DocTitle"]))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Enterprise AI Companion", styles["DocSubtitle"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Hybrid Semantic + Keyword Retrieval · v1.0", styles["DocMeta"]))
    story.append(Paragraph("2026-08-05", styles["DocMeta"]))

    story.append(NextPageTemplate("Content"))
    story.append(PageBreak())

    # ── Helper shorthands ──────────────────────────────────────────────────────
    def h1(t):  return Paragraph(t, styles["H1"])
    def h2(t):  return Paragraph(t, styles["H2"])
    def h3(t):  return Paragraph(t, styles["H3"])
    def p(t):   return Paragraph(t, styles["Body"])
    def b(t):   return Paragraph(f"• {t}", styles["Bullet"])
    def sp(n=6): return Spacer(1, n)
    def rule():  return HRFlowable(width="100%", thickness=0.5,
                                   color=RULE_COLOR, spaceAfter=8, spaceBefore=4)

    # ── Overview ───────────────────────────────────────────────────────────────
    story += [h1("Pipeline Overview"), rule()]
    story.append(p(
        "The search pipeline is a seven-stage system that converts a raw user query into "
        "a ranked, quality-filtered set of document excerpts that are injected into the "
        "LLM context window. No single relevance signal is trusted alone: BM25 keyword "
        "search catches exact matches that embeddings miss; cosine similarity catches "
        "conceptual matches that BM25 misses; Reciprocal Rank Fusion (RRF) combines "
        "their rankings without knowing their absolute scores; and a character-bigram "
        "reranker re-scores results by actual query-to-chunk text overlap as a final "
        "relevance gate."
    ))
    story.append(sp())

    # Pipeline summary table
    stages = [
        ("Stage 0", "Indexing",            "File hashing, chunking, embedding, dual write to SQLite + Qdrant"),
        ("Stage 1", "Query Preprocessing", "Normalise → tokenise → stop-words → fuzzy flag → expand → intent"),
        ("Stage 2", "Hybrid Search",       "BM25 keyword (FTS5) and cosine semantic (Qdrant) run in parallel"),
        ("Stage 3", "RRF Merge",           "Reciprocal Rank Fusion combines both result lists"),
        ("Stage 4", "Heuristic Reranker",  "Character-bigram cosine re-scores top-20 candidates"),
        ("Stage 5", "Quality Filter",      "Threshold gates and character budget applied"),
        ("Stage 6", "Citation X-Ref",      "Post-LLM: sources bar shows only cited documents"),
    ]
    tdata = [["Stage", "Name", "Description"]] + stages
    col_w = [2.2*cm, 4.2*cm, 9.6*cm]
    t = Table(tdata, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), VOLVO_BLUE),
        ("TEXTCOLOR",    (0, 0), (-1, 0), WHITE),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, VOLVO_LIGHT]),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 9),
        ("FONTNAME",     (0, 1), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR",    (0, 1), (0, -1), ACCENT),
        ("ALIGN",        (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("GRID",         (0, 0), (-1, -1), 0.3, RULE_COLOR),
    ]))
    story.append(t)
    story.append(sp(8))

    # ── Full pipeline diagram (text) ───────────────────────────────────────────
    story += [h2("End-to-End Flow")]
    story.append(code_block("""User query
    │
    ├─ needsRetrieval()? (<4 words or greeting → skip)
    │
    ▼
QueryPreprocessor  →  normalise, tokenise, stop-words, expand, classify
    │
    ▼
asyncio.gather():
    ├─ FTS5 BM25 keyword search    score = 1 / (1 + |bm25|)
    └─ Qdrant cosine search        score = cosine similarity (384-dim)
    │
    ▼
RRF merge:  score = Σ weight / (60 + rank)
    │
    ▼
Heuristic reranker:  0.7 × cosine_ngram + 0.3 × (rrf / max_rrf)
    │
    ▼
Quality filter:  rrf ≥ 0.01, cosine ≥ 0.01, rerank ≥ 0.08, ≤ 5 chunks, ≤ 12k chars
    │
    ▼
LLM system message with ranked excerpts + citation allowlist
    │
    ▼
Post-stream citation cross-reference  →  Sources bar""", styles))
    story.append(sp(10))

    # ── Stage 0 ────────────────────────────────────────────────────────────────
    story += [h1("Stage 0 — Indexing (Background, One-Time)"), rule()]
    story.append(p(
        "Indexing runs once per file, in the background. <b>file_indexer.py</b> computes "
        "a SHA-256 hash of each file and skips it if the hash matches a previously stored "
        "value, making re-indexing incremental and efficient."
    ))
    story.append(sp())

    for heading, body in [
        ("Chunking — text_chunker.py",
         "A sliding window of <b>1,500 characters</b> with a <b>200-character overlap</b> "
         "is applied to each document. At every boundary the chunker searches backward "
         "within the overlap zone for a sentence break "
         "(<font name='Courier' size='9'>(?&lt;=[.!?])\\s+</font>) and moves the cut "
         "there to avoid splitting mid-sentence. Each chunk is returned as a "
         "<font name='Courier' size='9'>(text, char_start, char_end)</font> tuple."),
        ("Embedding — embedding_service.py",
         "The model <b>BAAI/bge-small-en-v1.5</b> runs via ONNX/fastembed. "
         "It produces a <b>384-dimensional float vector</b> for every chunk."),
        ("Dual Write — chunk_repository.py",
         "Each chunk and its embedding are written to two stores simultaneously:"),
    ]:
        story.append(KeepTogether([h2(heading), p(body)]))

    story += [
        b("<b>SQLite chunks table</b> — stores full text content, chunk index, and character offsets"),
        b("<b>SQLite chunks_fts FTS5 virtual table</b> — Porter stemmer tokenisation, used for keyword search"),
        b("<b>Qdrant collection document_chunks</b> — cosine distance, 384 dims, used for semantic search"),
        sp(10),
    ]

    # ── Stage 1 ────────────────────────────────────────────────────────────────
    story += [h1("Stage 1 — Query Preprocessing"), rule()]
    story.append(p(
        "<b>query_preprocessor.py</b> runs six sequential steps on the raw user query "
        "before any search is performed."
    ))
    story.append(sp())

    steps = [
        ("1 — Normalise",        "Unicode NFC normalisation, lowercase, collapse whitespace."),
        ("2 — Tokenise",         "Split on <font name='Courier' size='9'>[\\s,;:!?()[\\]{}&lt;&gt;\"']+</font>."),
        ("3 — Stop-word removal","Remove a 70-term English frozenset. Preserves semantically important "
                                  "negations: <i>no</i>, <i>not</i>, <i>up</i>."),
        ("4 — Fuzzy flag",       "Marks tokens with 3+ repeated characters or high consonant density "
                                  "for downstream handling."),
        ("5 — Query expansion",  "Maps 18 abbreviations to synonym lists. Examples:\n"
                                  "  ai → [artificial intelligence, machine learning]\n"
                                  "  rag → [retrieval augmented generation]"),
        ("6 — Intent detection", "Classifies intent as: COMPARISON > FACTUAL > NAVIGATIONAL > EXPLORATORY. "
                                  "The search_text passed downstream is the concatenation of "
                                  "filtered tokens and expanded terms."),
    ]
    for title, desc in steps:
        story.append(KeepTogether([h3(title), p(desc), sp(4)]))

    story.append(sp(6))

    # ── Stage 2 ────────────────────────────────────────────────────────────────
    story += [h1("Stage 2 — Hybrid Search"), rule()]
    story.append(p(
        "<b>hybrid_orchestrator.py</b> launches both search providers concurrently via "
        "<font name='Courier' size='9'>asyncio.gather()</font>. Each fetches "
        "<font name='Courier' size='9'>top_k × 3</font> candidates (fetch multiplier = 3) "
        "to give the RRF merge stage a wider candidate pool."
    ))
    story.append(sp())

    story += [h2("2a — Keyword Search (FTS5 / BM25)")]
    story.append(p(
        "<b>keyword_search.py</b> wraps each query token in double quotes to prevent "
        "FTS5 operator injection:"
    ))
    story.append(code_block('"token1" "token2" "token3"', styles))
    story.append(p(
        "The query runs against the FTS5 table using "
        "<font name='Courier' size='9'>bm25(chunks_fts)</font>. SQLite BM25 returns "
        "negative values (lower = better), so scores are normalised to the range (0, 1]:"
    ))
    story.append(code_block("normalised_score = 1.0 / (1.0 + |raw_bm25|)", styles))
    story.append(sp(8))

    story += [h2("2b — Semantic Search (Qdrant / Cosine)")]
    story.append(p(
        "<b>qdrant_search.py</b> generates a 384-dimensional query vector via "
        "<font name='Courier' size='9'>EmbeddingService.generate(search_text)</font> "
        "and queries Qdrant using cosine similarity. Hit payloads contain "
        "<font name='Courier' size='9'>chunk_id</font> strings which are then hydrated "
        "from SQLite to retrieve full text content."
    ))
    story.append(sp(10))

    # ── Stage 3 ────────────────────────────────────────────────────────────────
    story += [h1("Stage 3 — RRF Merge"), rule()]
    story.append(p(
        "<b>hybrid_orchestrator.py</b> merges the two result lists using Reciprocal Rank "
        "Fusion (RRF). Each chunk receives a score contribution from every list it appears in:"
    ))
    story.append(code_block(
        "rrf_score(chunk) = keyword_weight  / (60 + keyword_rank)\n"
        "                 + semantic_weight / (60 + semantic_rank)", styles))
    story.append(sp())

    story.append(p(
        "The constant <b>k = 60</b> is the standard RRF smoothing value from the literature. "
        "It prevents top-ranked results from dominating by compressing the rank differences. "
        "Ranks are 1-based (rank 1 = best match). Weights default to 1.0 each and can be "
        "tuned per-request."
    ))
    story.append(sp())

    story += [h3("Numerical Example")]
    story.append(p(
        "A chunk ranked 1st in semantic and 5th in keyword:"
    ))
    story.append(code_block(
        "1/(60+1) + 1/(60+5) = 0.0164 + 0.0154 = 0.0318\n\n"
        "vs. a chunk ranked 1st in semantic only:\n\n"
        "1/(60+1) = 0.0164", styles))
    story.append(p(
        "A chunk appearing in both lists always outscores a chunk appearing in one list "
        "alone — this is why hybrid retrieval outperforms either provider individually."
    ))
    story.append(sp(10))

    # ── Stage 4 ────────────────────────────────────────────────────────────────
    story += [h1("Stage 4 — Heuristic Reranker"), rule()]
    story.append(p(
        "Both the backend (<b>reranker.py</b>) and the frontend (<b>useConversation.ts</b>) "
        "run an identical reranker on the top-20 RRF candidates. The dual implementation "
        "ensures consistent ranking whether the result is consumed by the API or directly "
        "by the chat interface."
    ))
    story.append(sp())

    story += [h2("Character Bigram TF Vectorisation")]
    story.append(p(
        "Lowercase word-tokenise each text using "
        "<font name='Courier' size='9'>\\w+</font>. For every token, extract all "
        "overlapping character bigrams:"
    ))
    story.append(code_block(
        '"hello" → ["he", "el", "ll", "lo"]', styles))
    story.append(p(
        "Count occurrences and divide by the total bigram count to get a TF vector "
        "<font name='Courier' size='9'>{bigram: frequency}</font>."
    ))
    story.append(sp())

    story += [h2("Cosine Similarity")]
    story.append(code_block(
        "dot    = Σ a[k] * b[k]   for k in b\n"
        "norm_a = √(Σ a[v]²)\n"
        "norm_b = √(Σ b[v]²)\n"
        "cosine = dot / (norm_a × norm_b)     [0 if denominator = 0]", styles))
    story.append(sp())

    story += [h2("Final Rerank Score")]
    story.append(code_block(
        "rerank_score = 0.7 × cosine(ngramTf(query), ngramTf(chunk_content))\n"
        "             + 0.3 × (rrf_score / max_rrf_score)", styles))
    story.append(p(
        "The 0.3 position bonus means that a keyword rank-1 hit (rrf/max = 1.0) "
        "receives a free +0.3 contribution to its blended score even if character-level "
        "overlap is low. This rewards documents that scored well in the initial retrieval "
        "stage while still allowing strong cosine matches to overtake them."
    ))
    story.append(sp(10))

    # ── Stage 5 ────────────────────────────────────────────────────────────────
    story += [h1("Stage 5 — Quality Filter & Character Budget"), rule()]
    story.append(p(
        "<b>context_assembler.py</b> (backend) and <b>useConversation.ts</b> (frontend) "
        "apply the following gates in order. The frontend thresholds are stricter because "
        "the LLM call cost is higher — it is better to return nothing than to inject "
        "irrelevant context that confuses the model."
    ))
    story.append(sp())

    filter_data = [
        ["Filter",         "Backend Threshold", "Frontend Threshold"],
        ["rrf_score",      "≥ 0.004",           "≥ 0.01"],
        ["cosine_score",   "—",                 "≥ 0.01"],
        ["rerank_score",   "—",                 "≥ 0.08"],
        ["Max chunks",     "5",                 "5"],
        ["Max characters", "12,000",            "12,000"],
    ]
    ft = Table(filter_data, colWidths=[5*cm, 4*cm, 4*cm], repeatRows=1)
    ft.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), VOLVO_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, VOLVO_LIGHT]),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("FONTNAME",      (0, 1), (0, -1), "Helvetica-Bold"),
        ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
        ("ALIGN",         (0, 0), (0, -1), "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.3, RULE_COLOR),
    ]))
    story.append(ft)
    story.append(sp(10))

    # ── Stage 6 ────────────────────────────────────────────────────────────────
    story += [h1("Stage 6 — Citation Cross-Reference"), rule()]
    story.append(p(
        "After the LLM streams its response, <b>useConversation.ts</b> extracts all "
        "file path references using:"
    ))
    story.append(code_block(r"/\[([^\]]+\.[a-zA-Z0-9]+)\]/g", styles))
    story.append(p(
        "Only chunks whose <font name='Courier' size='9'>documentPath</font> appears in "
        "the cited set are shown in the Sources bar. This ensures the Sources bar "
        "displays documents the model actually used, not everything that passed the "
        "retrieval quality filter."
    ))
    story.append(sp(10))

    # ── Design Rationale ───────────────────────────────────────────────────────
    story += [h1("Design Rationale"), rule()]
    story.append(p(
        "The key insight behind this architecture is that relevance is multi-dimensional "
        "and no single signal captures it reliably:"
    ))
    story.append(sp(4))
    for point in [
        ("<b>BM25 keyword search</b> is strong on exact term matches and technical "
         "identifiers (function names, error codes, acronyms) but fails on conceptual "
         "or paraphrased queries."),
        ("<b>Dense vector search</b> handles synonymy and concept proximity well but "
         "can miss rare terms that were never seen together in training."),
        ("<b>RRF</b> avoids the score normalisation problem by working on ranks rather "
         "than raw scores. A document ranked highly by both providers is almost "
         "certainly relevant."),
        ("<b>The bigram reranker</b> adds a final character-level overlap check that "
         "is independent of both BM25 and embedding models, catching cases where "
         "the initial retrieval was coarse."),
        ("<b>Dual filter thresholds</b> (strict frontend, relaxed backend) allow the "
         "API to return more candidates for downstream consumers while protecting "
         "LLM call quality in the chat interface."),
    ]:
        story.append(b(point))
        story.append(sp(2))

    story.append(sp(10))

    # ── Module Reference ───────────────────────────────────────────────────────
    story += [h1("Module Reference"), rule()]
    mod_data = [
        ["Module",                   "Layer",    "Responsibility"],
        ["file_indexer.py",          "Infra",    "File hashing, skip-if-unchanged, orchestrates indexing"],
        ["text_chunker.py",          "Infra",    "Sliding-window chunking with sentence-boundary adjustment"],
        ["embedding_service.py",     "Infra",    "BGE-small-en-v1.5 via ONNX/fastembed → 384-dim vectors"],
        ["chunk_repository.py",      "Infra",    "Dual write to SQLite (chunks + FTS5) and Qdrant"],
        ["query_preprocessor.py",    "Domain",   "Normalise, tokenise, expand, classify intent"],
        ["hybrid_orchestrator.py",   "Domain",   "Parallel search dispatch + RRF merge"],
        ["keyword_search.py",        "Infra",    "BM25 FTS5 query, score normalisation"],
        ["qdrant_search.py",         "Infra",    "Dense vector query, chunk hydration"],
        ["reranker.py",              "Domain",   "Character-bigram cosine reranking (backend)"],
        ["context_assembler.py",     "Domain",   "Quality filter, character budget, context assembly"],
        ["useConversation.ts",       "Frontend", "Reranker mirror, quality filter, citation cross-ref"],
    ]
    cw = [4.8*cm, 2.4*cm, 8.8*cm]
    mt = Table(mod_data, colWidths=cw, repeatRows=1)
    mt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), VOLVO_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, VOLVO_LIGHT]),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8.5),
        ("FONTNAME",      (0, 1), (0, -1), "Courier"),
        ("FONTSIZE",      (0, 1), (0, -1), 8),
        ("TEXTCOLOR",     (0, 1), (0, -1), ACCENT),
        ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("GRID",          (0, 0), (-1, -1), 0.3, RULE_COLOR),
    ]))
    story.append(mt)

    doc.build(story)
    print(f"PDF written -> {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
