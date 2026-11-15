"""Focused QA regression and release-audit checks for Q-0432, Q-0433, and Q-0435."""

from __future__ import annotations

from hashlib import sha256
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image
from PySide6.QtWidgets import QApplication, QLabel

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.desktop.medical_source_audit import (  # noqa: E402
    ArticleAudit,
    MedicalSourceAuditPanel,
    SourceKind,
    audit_lines,
)
from knowledge.nasa.cliff_119_2023 import importer  # noqa: E402
from packages.medical_library.image_relevance_qa import _dhash, audit_images  # noqa: E402
from scripts.audit_cliff119_library import audit_library  # noqa: E402

CLIFF_DIR = REPO_ROOT / "knowledge" / "nasa" / "cliff_119_2023"
CLIFF_DB = CLIFF_DIR / "AETHERION_NASA_CLIFF_119.sqlite"
CLIFF_CATALOG = CLIFF_DIR / "quest_source_index.json"
CLIFF_MANIFEST = CLIFF_DIR / "manifest.json"


def _make_png_bytes(width: int = 32, height: int = 32, *, tint: int = 0) -> bytes:
    img = Image.new("RGB", (width, height))
    pixels = []
    for y in range(height):
        for x in range(width):
            val = (x * 7 + y * 5 + tint) % 256
            pixels.append((val, (val + 40) % 256, (255 - val) % 256))
    img.putdata(pixels)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class MedicalLibraryQAPanelAndImageQATests(unittest.TestCase):
    def test_image_relevance_qa_accepts_verified_real_image_and_blocks_defects(self) -> None:
        record = json.loads((CLIFF_DIR / "records" / "CLIFF-044.json").read_text(encoding="utf-8"))
        media_item = record["media"][0]
        real_bytes = (REPO_ROOT / media_item["file_path"]).read_bytes()
        real_sha = sha256(real_bytes).hexdigest()
        self.assertEqual(real_sha, media_item["sha256"])

        base_png = _make_png_bytes(tint=0)
        base_sha = sha256(base_png).hexdigest()
        near_png = _make_png_bytes(tint=1)
        near_sha = sha256(near_png).hexdigest()

        assets = [
            {
                "asset_id": "cliff044-real",
                "image_bytes": real_bytes,
                "sha256": real_sha,
                "condition_id": "CLIFF-044",
                "caption": media_item["caption"],
                "alt_text": media_item["alt_text"],
                "reviewer_id": "clinical-reviewer-01",
                "reviewed_condition_id": "CLIFF-044",
                "reviewed_sha256": real_sha,
                "review_decision": "APPROVED",
            },
            {
                "asset_id": "synth-base",
                "image_bytes": base_png,
                "sha256": base_sha,
                "condition_id": "CLIFF-044",
                "caption": "Synthetic gradient calibration grid",
                "alt_text": "Synthetic gradient image",
                "reviewer_id": "clinical-reviewer-01",
                "reviewed_condition_id": "CLIFF-044",
                "reviewed_sha256": base_sha,
                "review_decision": "APPROVED",
            },
            {
                "asset_id": "synth-near-dup",
                "image_bytes": near_png,
                "sha256": near_sha,
                "condition_id": "CLIFF-044",
                "caption": "Slightly shifted gradient",
                "alt_text": "Shifted synthetic gradient image",
                "reviewer_id": "clinical-reviewer-01",
                "reviewed_condition_id": "CLIFF-044",
                "reviewed_sha256": near_sha,
                "review_decision": "APPROVED",
            },
            {
                "asset_id": "exact-dup",
                "image_bytes": real_bytes,
                "sha256": real_sha,
                "condition_id": "CLIFF-044",
                "caption": media_item["caption"],
                "alt_text": media_item["alt_text"],
                "reviewer_id": "clinical-reviewer-01",
                "reviewed_condition_id": "CLIFF-044",
                "reviewed_sha256": real_sha,
                "review_decision": "APPROVED",
            },
            {
                "asset_id": "unreviewed-corrupt",
                "image_bytes": b"not-a-valid-image",
                "sha256": sha256(b"not-a-valid-image").hexdigest(),
                "condition_id": "CLIFF-044",
                "caption": "Corrupt figure",
                "alt_text": "Corrupt alt",
                "reviewer_id": "",
                "reviewed_condition_id": "CLIFF-040",
                "reviewed_sha256": "0" * 64,
                "review_decision": "PENDING",
            },
            {
                "asset_id": "",
                "image_bytes": b"",
                "sha256": "",
                "condition_id": "",
                "caption": "",
                "alt_text": "",
                "reviewer_id": "clinical-reviewer-01",
                "reviewed_condition_id": "CLIFF-044",
                "reviewed_sha256": "",
                "review_decision": "APPROVED",
            },
        ]

        results = audit_images(assets)
        self.assertEqual(len(results), 6)

        self.assertTrue(results[0].accepted)
        self.assertEqual(results[0].findings, ())
        self.assertIsNotNone(results[0].perceptual_hash)
        self.assertEqual(len(results[0].perceptual_hash or ""), 16)
        self.assertEqual(_dhash(real_bytes), results[0].perceptual_hash)

        self.assertTrue(results[1].accepted)
        self.assertFalse(results[2].accepted)
        self.assertIn("POSSIBLE_VISUAL_DUPLICATE_OF:synth-base", results[2].findings)

        self.assertFalse(results[3].accepted)
        self.assertIn("EXACT_DUPLICATE_OF:cliff044-real", results[3].findings)

        self.assertFalse(results[4].accepted)
        self.assertIn("CLINICAL_RELEVANCE_REVIEW_REQUIRED", results[4].findings)
        self.assertIn("IMAGE_DECODE_UNVERIFIED", results[4].findings)

        self.assertFalse(results[5].accepted)
        self.assertTrue(
            {
                "MISSING_IMAGE_BYTES",
                "SHA256_MISMATCH",
                "MISSING_ASSET_ID",
                "MISSING_CONDITION_ID",
                "MISSING_CLINICAL_CAPTION",
                "MISSING_ALT_TEXT",
                "CLINICAL_RELEVANCE_REVIEW_REQUIRED",
                "IMAGE_DECODE_UNVERIFIED",
            }
            <= set(results[5].findings)
        )

        with self.assertRaises(ValueError):
            audit_images([], near_duplicate_hamming_distance=65)

    def test_medical_source_audit_panel_fails_closed_in_offscreen_qt(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        with self.assertRaises(ValueError):
            ArticleAudit(title="Bad", source_kind=SourceKind.NASA_CLIFF, images_total=-1)
        with self.assertRaises(ValueError):
            ArticleAudit(
                title="Bad",
                source_kind=SourceKind.NASA_CLIFF,
                images_total=2,
                images_with_verified_rights=3,
            )

        panel = MedicalSourceAuditPanel(None)
        try:
            self.assertEqual(
                [lbl.text() for lbl in panel._labels],
                ["NO DATA — no verified offline article selected"],
            )
            self.assertIn("Status:", [lbl.text() for lbl in panel.findChildren(QLabel)])

            partial = ArticleAudit(
                title="Sepsis",
                source_kind=SourceKind.NASA_CLIFF,
                original_url="https://www.nasa.gov/integrated-medical-model-documentation/",
                source_version="2023",
                source_sha256="a" * 64,
                original_verified=False,
                offline_bytes_verified=False,
                full_text_verified=True,
                page_citations_verified=True,
                images_total=4,
                images_with_verified_rights=4,
                curated_images=4,
            )
            panel.set_audit(partial)
            app.processEvents()
            rows = dict(audit_lines(partial))
            self.assertIn("NOT a bedside clinical protocol", rows["Material classification"])
            self.assertIn("NOT endorsed or clinically certified by NASA", rows["NASA endorsement"])
            self.assertTrue(rows["Original provenance"].startswith("UNVERIFIED"))
            self.assertTrue(rows["Offline original"].startswith("UNVERIFIED"))
            self.assertEqual(rows["Article completeness"], "INCOMPLETE / UNVERIFIED")
            self.assertEqual(
                [(lbl.accessibleName(), lbl.text()) for lbl in panel._labels],
                list(audit_lines(partial)),
            )

            verified = ArticleAudit(
                title="Sepsis",
                source_kind=SourceKind.NASA_CLIFF,
                original_url="https://www.nasa.gov/example.pdf",
                source_version="2023",
                source_sha256="b" * 64,
                original_verified=True,
                offline_bytes_verified=True,
                full_text_verified=True,
                page_citations_verified=True,
                images_total=4,
                images_with_verified_rights=4,
                curated_images=4,
            )
            verified_rows = dict(audit_lines(verified))
            self.assertEqual(verified_rows["Original provenance"], "Verified by upstream source audit")
            self.assertEqual(verified_rows["Offline original"], "Verified by upstream offline byte audit")
            self.assertEqual(verified_rows["Article completeness"], "Full text and page citations checked upstream")
            self.assertIn("NOT endorsed or clinically certified by NASA", verified_rows["NASA endorsement"])
        finally:
            panel.close()
            panel.deleteLater()
            app.sendPostedEvents()
            app.processEvents()

    def test_release_audit_fails_closed_against_current_cliff_repository_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_db = Path(tmpdir) / "subset.sqlite"
            for name in ("CLIFF-040.json", "CLIFF-044.json"):
                rec = json.loads((CLIFF_DIR / "records" / name).read_text(encoding="utf-8"))
                importer.ingest_article_record(temp_db, rec, assets_root=REPO_ROOT)

            subset_report = audit_library(temp_db, CLIFF_CATALOG, CLIFF_MANIFEST, min_approved_images=3)
            self.assertFalse(subset_report["passed"])
            self.assertEqual(subset_report["counts"]["articles"], 2)
            subset_codes = {item["code"] for item in subset_report["issues"]}
            self.assertTrue({"ARTICLE_COUNT", "ARTICLE_MISSING", "UNRESOLVED_INDEX_SLOT", "MANIFEST_MISSING"} <= subset_codes)

        if CLIFF_DB.is_file():
            live_report = audit_library(CLIFF_DB, CLIFF_CATALOG, CLIFF_MANIFEST, min_approved_images=3)
            self.assertFalse(live_report["passed"])
            self.assertEqual(live_report["counts"]["articles"], 118)
            self.assertEqual(live_report["counts"]["verified_originals"], 0)
            self.assertGreaterEqual(live_report["counts"]["approved_images"], 300)
            self.assertGreaterEqual(live_report["counts"]["verified_images"], 300)
            missing_slots = {
                item.get("slot")
                for item in live_report["issues"]
                if item["code"] == "ARTICLE_MISSING"
            }
            self.assertEqual(missing_slots, {119})


if __name__ == "__main__":
    unittest.main()
