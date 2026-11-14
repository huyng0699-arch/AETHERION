"""AETHERION standalone offline medical library package."""

from packages.medical_library.rights_gate import (
    DistributionRightsError,
    RightsAuditResult,
    build_embedded_notice_bundle,
    validate_nasa_original_rights,
    validate_third_party_rights,
)

__all__ = [
    "DistributionRightsError",
    "RightsAuditResult",
    "build_embedded_notice_bundle",
    "validate_nasa_original_rights",
    "validate_third_party_rights",
]
