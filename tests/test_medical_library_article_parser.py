"""Tests for Q-0424 structured full-text article and medical citation parser."""

import unittest

from packages.medical_library.article_parser import parse_structured_article


class ArticleParserTests(unittest.TestCase):
    def test_preserves_headings_tables_figures_citations_and_page_anchors(self) -> None:
        pages = [
            (
                1,
                """NASA CliFF Synthetic Parser Test Title
1. Introduction
This section summarizes risk-planning context.
Figure 1: Abdominal anatomy diagram for orientation
| Metric | Value |
| --- | --- |
| Incidence | 0.02 |
""",
            ),
            (
                2,
                """2. References
[1] NASA IMM Documentation https://www.nasa.gov/integrated-medical-model-documentation/ doi:10.1000/test.001
""",
            ),
        ]
        parsed = parse_structured_article(pages)
        self.assertEqual(parsed["title"], "NASA CliFF Synthetic Parser Test Title")
        self.assertFalse(parsed["llm_invented_text"])
        self.assertEqual(len(parsed["sections"]), 2)
        self.assertEqual(parsed["sections"][0]["heading"], "1. Introduction")
        self.assertEqual(parsed["sections"][0]["source_anchor"], "p.1")
        self.assertEqual(len(parsed["tables"]), 1)
        self.assertEqual(parsed["tables"][0]["rows"], [["Metric", "Value"], ["Incidence", "0.02"]])
        self.assertEqual(len(parsed["figures"]), 1)
        self.assertEqual(parsed["figures"][0]["figure_reference"], "Figure 1")
        self.assertEqual(len(parsed["references"]), 1)
        self.assertEqual(
            parsed["references"][0]["citation_url"],
            "https://www.nasa.gov/integrated-medical-model-documentation/",
        )
        self.assertEqual(parsed["references"][0]["doi"], "10.1000/test.001")

    def test_unparsed_and_uncertain_pdf_text_flagged_never_fabricated(self) -> None:
        pages = [
            (1, "1. Overview\nGarbled OCR glyph \ufffd present."),
            (2, "   \n  "),
        ]
        parsed = parse_structured_article(pages, title="OCR Uncertainty Test")
        self.assertEqual(parsed["sections"][0]["uncertainty_flags"], ["PDF_TEXT_UNCERTAIN"])
        self.assertEqual(
            parsed["unparsed_pages"],
            [{"page_number": 2, "reason": "EMPTY_OR_UNPARSED_PDF_TEXT"}],
        )
        with self.assertRaises(ValueError):
            parse_structured_article([])


if __name__ == "__main__":
    unittest.main()
