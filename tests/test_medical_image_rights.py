"""Non-skipped positive and negative tests for medical image provenance."""
import importlib.util
import json
import struct
import tempfile
import unittest
import urllib.request
import zlib
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "medical_image_rights.py"
spec = importlib.util.spec_from_file_location("medical_image_rights", MODULE)
rights = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rights)


def png():
    def chunk(tag, content):
        return (struct.pack(">I", len(content)) + tag + content
                + struct.pack(">I", zlib.crc32(tag + content) & 0xffffffff))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 3, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress((b"\x00" + b"\x00" * 6) * 3))
            + chunk(b"IEND", b""))


def metadata():
    return {
        "source_url": "https://example.org/file.png",
        "rights_url": "https://example.org/file-rights",
        "license": "CC BY 4.0",
        "author": "Example creator",
        "title": "Anatomical diagram",
        "caption": "Anatomy reference",
        "alt_text": "Anatomical diagram",
        "clinical_relevance": "Identifies organ structures",
        "article_id": "CLIFF-003",
        "rights_verified": True,
    }


class FakeResponse:
    def __init__(self, data, mime="image/png", url="https://example.org/file.png"):
        self.data, self.headers, self.url = data, {"Content-Type": mime}, url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self.url

    def read(self, limit):
        return self.data[:limit]


class ImageRightsTests(unittest.TestCase):
    def test_valid_png_dimensions_hash(self):
        info = rights.verify_image(png(), "image/png")
        self.assertEqual((info["width"], info["height"]), (2, 3))
        self.assertEqual(len(info["sha256"]), 64)

    def test_end_to_end_content_addressed_asset_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = rights.acquire(
                metadata(), Path(tmp), opener=lambda req, timeout: FakeResponse(png())
            )
            self.assertEqual((Path(tmp) / result["asset_path"]).read_bytes(), png())
            manifest = json.loads(
                (Path(tmp) / (result["sha256"] + ".json")).read_text()
            )
            self.assertEqual(manifest["rights_url"], metadata()["rights_url"])
            self.assertEqual(
                manifest["rights_review_status"], "metadata_declared_manual_review_required"
            )

    def test_reject_unknown_license(self):
        meta = metadata()
        meta["license"] = "unknown"
        with self.assertRaises(rights.ImageRightsError):
            rights.verify_metadata(meta)

    def test_reject_unreviewed_rights(self):
        meta = metadata()
        meta["rights_verified"] = False
        with self.assertRaises(rights.ImageRightsError):
            rights.verify_metadata(meta)

    def test_reject_http_and_credentials(self):
        for url in ("http://example.org/img", "https://user:pass@example.org/img"):
            meta = metadata()
            meta["source_url"] = url
            with self.assertRaises(rights.ImageRightsError):
                rights.verify_metadata(meta)

    def test_reject_html_and_mime_mismatch(self):
        with self.assertRaises(rights.ImageRightsError):
            rights.verify_image(b"<html>oops</html>")
        with self.assertRaises(rights.ImageRightsError):
            rights.verify_image(png(), "text/html")

    def test_reject_oversized_and_bad_dimensions(self):
        with self.assertRaises(rights.ImageRightsError):
            rights.verify_image(b"x" * (rights.MAX_IMAGE_BYTES + 1))
        data = bytearray(png())
        data[16:20] = b"\x00\x00\x00\x00"
        with self.assertRaises(rights.ImageRightsError):
            rights.verify_image(bytes(data))

    def test_reject_redirect_to_http(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(rights.ImageRightsError):
                rights.acquire(
                    metadata(), Path(tmp),
                    opener=lambda req, timeout: FakeResponse(
                        png(), url="http://example.org/unsafe"
                    ),
                )


    def test_reject_corrupted_and_truncated_png_bytes(self):
        with self.assertRaises(rights.ImageRightsError):
            rights.verify_image(png()[:24], "image/png")
        with self.assertRaises(rights.ImageRightsError):
            rights.verify_image(png()[:-12], "image/png")
        corrupt = bytearray(png())
        corrupt[30] ^= 1  # Corrupt IHDR CRC without changing dimensions.
        with self.assertRaises(rights.ImageRightsError):
            rights.verify_image(bytes(corrupt), "image/png")

    def test_reject_private_network_hosts(self):
        for unsafe in (
            "https://127.0.0.1/image.png",
            "https://192.168.1.20/image.png",
            "https://[::1]/image.png",
            "https://localhost/image.png",
            "https://metadata.internal/secret",
            "https://example.local/image.png",
            "https://example.org:8443/image.png",
            "https://2130706433/image.png",
        ):
            with self.subTest(url=unsafe):
                meta = metadata()
                meta["source_url"] = unsafe
                with self.assertRaises(rights.ImageRightsError):
                    rights.verify_metadata(meta)

    def test_redirect_validator_rejects_local_target_before_connection(self):
        handler = rights.SafeRedirectHandler()
        req = urllib.request.Request("https://example.org/image.png")
        with self.assertRaises(rights.ImageRightsError):
            handler.redirect_request(
                req, None, 302, "Found", {}, "https://127.0.0.1/private"
            )

    def test_existing_image_manifest_is_idempotent_and_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            opener = lambda req, timeout: FakeResponse(png())
            first = rights.acquire(metadata(), folder, opener=opener)
            manifest_path = folder / (first["sha256"] + ".json")
            original = manifest_path.read_bytes()
            again = rights.acquire(metadata(), folder, opener=opener)
            self.assertEqual(again, first)
            self.assertEqual(manifest_path.read_bytes(), original)
            conflicting = metadata()
            conflicting["license"] = "CC BY-SA 4.0"
            with self.assertRaises(rights.ImageRightsError):
                rights.acquire(conflicting, folder, opener=opener)
            self.assertEqual(manifest_path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
