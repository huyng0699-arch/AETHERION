"""Structured full-text article and medical citation parser (Q-0424)."""

from __future__ import annotations

import re
from typing import Any

HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.\s+(.+)$")
FIGURE_RE = re.compile(r"^(?:Figure|Fig\.?)\s+(\d+[A-Za-z]?)\s*[:.\-—]\s*(.+)$", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s\)\]>]+")
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b")
REF_LINE_RE = re.compile(r"^\[(\d+)\]\s+(.+)$")


def parse_structured_article(
    pages: list[tuple[int, str]],
    *,
    title: str | None = None,
) -> dict[str, Any]:
    """Parse page-anchored text into sections, tables, figures, references, and uncertainty flags.

    Never fabricates or hallucinates missing/unreadable PDF text.
    """
    if not pages:
        raise ValueError("pages must be non-empty")

    sections: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    figures: list[dict[str, Any]] = []
    references: list[dict[str, Any]] = []
    unparsed_pages: list[dict[str, Any]] = []

    current_heading: str | None = None
    current_lines: list[str] = []
    current_page_start: int | None = None
    current_page_end: int | None = None
    current_uncertain = False
    detected_title = title.strip() if title else ""

    def flush_section() -> None:
        nonlocal current_heading, current_lines, current_page_start, current_page_end, current_uncertain
        if current_heading is not None:
            body = "\n".join(current_lines).strip()
            sections.append(
                {
                    "ordinal": len(sections),
                    "heading": current_heading,
                    "text_content": body,
                    "page_start": current_page_start,
                    "page_end": current_page_end,
                    "source_anchor": f"p.{current_page_start}" if current_page_start == current_page_end else f"p.{current_page_start}-{current_page_end}",
                    "uncertainty_flags": ["PDF_TEXT_UNCERTAIN"] if current_uncertain else [],
                }
            )
        current_heading = None
        current_lines = []
        current_page_start = None
        current_page_end = None
        current_uncertain = False

    for page_num, raw_text in pages:
        if page_num < 1:
            raise ValueError(f"page_num must be >= 1, got {page_num}")
        text = raw_text or ""
        if not text.strip():
            unparsed_pages.append({"page_number": page_num, "reason": "EMPTY_OR_UNPARSED_PDF_TEXT"})
            continue

        page_has_replacement = "\ufffd" in text
        lines = text.splitlines()
        idx = 0
        while idx < len(lines):
            line = lines[idx].strip()
            if not line:
                idx += 1
                continue

            if not detected_title and not HEADING_RE.match(line) and not REF_LINE_RE.match(line):
                detected_title = line.lstrip("# ").strip()
                idx += 1
                continue

            # Pipe-delimited table block
            if line.startswith("|") and "|" in line[1:]:
                table_rows: list[list[str]] = []
                while idx < len(lines) and lines[idx].strip().startswith("|"):
                    row_line = lines[idx].strip()
                    cells = [c.strip() for c in row_line.strip("|").split("|")]
                    if not all(re.match(r"^:?-{2,}:?$", c) for c in cells if c):
                        table_rows.append(cells)
                    idx += 1
                if table_rows:
                    tables.append(
                        {
                            "ordinal": len(tables),
                            "title": f"Table {len(tables) + 1} (p.{page_num})",
                            "rows": table_rows,
                            "page_number": page_num,
                            "source_anchor": f"p.{page_num}",
                        }
                    )
                continue

            # Figure placement
            fig_match = FIGURE_RE.match(line)
            if fig_match:
                figures.append(
                    {
                        "ordinal": len(figures),
                        "figure_reference": f"Figure {fig_match.group(1)}",
                        "caption": fig_match.group(2).strip(),
                        "page_number": page_num,
                        "source_anchor": f"p.{page_num}",
                    }
                )
                idx += 1
                continue

            # Numbered citation / reference line
            ref_match = REF_LINE_RE.match(line)
            if ref_match:
                ref_body = ref_match.group(2).strip()
                url_match = URL_RE.search(ref_body)
                doi_match = DOI_RE.search(ref_body)
                references.append(
                    {
                        "ordinal": len(references),
                        "label": f"[{ref_match.group(1)}] {ref_body}",
                        "citation_url": url_match.group(0) if url_match else "",
                        "doi": doi_match.group(1) if doi_match else None,
                        "page_number": page_num,
                    }
                )
                idx += 1
                continue

            # Numbered heading
            head_match = HEADING_RE.match(line)
            if head_match:
                flush_section()
                current_heading = line
                current_page_start = page_num
                current_page_end = page_num
                current_uncertain = page_has_replacement
                idx += 1
                continue

            if current_heading is None:
                current_heading = f"Unheaded Section (p.{page_num})"
                current_page_start = page_num
            current_page_end = page_num
            if page_has_replacement:
                current_uncertain = True
            current_lines.append(line)
            idx += 1

    flush_section()

    return {
        "title": detected_title or "Untitled Document",
        "sections": sections,
        "tables": tables,
        "figures": figures,
        "references": references,
        "unparsed_pages": unparsed_pages,
        "llm_invented_text": False,
    }
