"""Tests for Q-0431 NASA and third-party copyright attribution and distribution gate."""

import unittest

from packages.medical_library.rights_gate import (
    DistributionRightsError,
    build_embedded_notice_bundle,
    validate_nasa_original_rights,
    validate_third_party_rights,
)


class MedicalLibraryRightsGateTests(unittest.TestCase):
    def test_valid_nasa_and_third_party_rights_produce_notice_bundle(self) -> None:
        nasa = validate_nasa_original_rights(
            {
                "entity_id": "CLIFF-001",
                "entity_type": "article",
                "publisher": "NASA",
                "source_url": "https://www.nasa.gov/integrated-medical-model-documentation/",
                "sha256": "a" * 64,
                "retrieved_at_utc": "2026-11-14T05:24:00+00:00",
                "license_name": "US_GOV_PUBLIC_DOMAIN",
            }
        )
        third_party = validate_third_party_rights(
            {
                "entity_id": "IMG-COMMONS-001",
                "entity_type": "media",
                "creator": "OpenStax Anatomy and Physiology",
                "publisher": "Wikimedia Commons / OpenStax",
                "source_url": "https://commons.wikimedia.org/wiki/File:2001_Heart.jpg",
                "license_name": "CC-BY-4.0",
                "credit_line": "OpenStax College, CC BY 4.0, via Wikimedia Commons",
                "sha256": "b" * 64,
            }
        )
        bundle = build_embedded_notice_bundle([nasa, third_party])
        self.assertEqual(bundle["total_items"], 2)
        self.assertEqual(bundle["nasa_originals"], 1)
        self.assertEqual(bundle["third_party_items"], 1)
        self.assertIn("does not endorse", bundle["disclaimer"])

    def test_blocks_unverified_restricted_or_unattributed_redistribution(self) -> None:
        # Non-NASA URL claiming to be NASA original
        with self.assertRaises(DistributionRightsError):
            validate_nasa_original_rights(
                {
                    "entity_id": "FAKE-NASA",
                    "entity_type": "article",
                    "publisher": "NASA",
                    "source_url": "https://example.com/fake-nasa.pdf",
                    "sha256": "a" * 64,
                    "retrieved_at_utc": "2026-11-14T05:24:00+00:00",
                }
            )

        # ALL_RIGHTS_RESERVED third-party image blocked
        with self.assertRaises(DistributionRightsError):
            validate_third_party_rights(
                {
                    "entity_id": "IMG-RESTRICTED",
                    "entity_type": "media",
                    "creator": "Journal Publisher",
                    "publisher": "Journal",
                    "source_url": "https://journal.example.org/fig1.png",
                    "license_name": "ALL_RIGHTS_RESERVED",
                    "credit_line": "Copyright Journal",
                    "sha256": "c" * 64,
                }
            )

        # CC-BY-4.0 without credit_line blocked
        with self.assertRaises(DistributionRightsError):
            validate_third_party_rights(
                {
                    "entity_id": "IMG-NO-CREDIT",
                    "entity_type": "media",
                    "creator": "Author",
                    "publisher": "OpenStax",
                    "source_url": "https://openstax.org/img.png",
                    "license_name": "CC-BY-4.0",
                    "credit_line": "",
                    "sha256": "d" * 64,
                }
            )

        # CC-BY-SA-4.0 without share_alike_notice blocked
        with self.assertRaises(DistributionRightsError):
            validate_third_party_rights(
                {
                    "entity_id": "IMG-SA-NO-NOTICE",
                    "entity_type": "media",
                    "creator": "Author",
                    "publisher": "Wikimedia Commons",
                    "source_url": "https://commons.wikimedia.org/wiki/File:Sample.png",
                    "license_name": "CC-BY-SA-4.0",
                    "credit_line": "Author, CC BY-SA 4.0",
                    "sha256": "e" * 64,
                }
            )


if __name__ == "__main__":
    unittest.main()
