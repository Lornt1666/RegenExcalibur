#!/usr/bin/env python3
"""ProofGrid v1.1.1 declared environmental indicators on hardened parent evidence.

The historical v1.1 parser/research logic is reused byte-for-byte, but this
wrapper requires the superseding v0.9.1 -> v1.0.1 trust chain before any
declared environmental amount is extracted.

For ILCD+EPD v1.2, the canonical source record must retain the exact accepted
validator/profile JAR/POM/include fingerprint. For v1.3, profile validation must
remain explicitly false. No value is calculated, aggregated, converted, inferred
from warnings, scientifically validated, professionally reviewed, or certified.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference import declared_environmental_indicators as base  # noqa: E402
from reference import environmental_admission_v091 as hardened_admission  # noqa: E402
from reference import environmental_source_identity_v101 as hardened_source_identity  # noqa: E402

ENGINE_NAME = base.ENGINE_NAME
ENGINE_VERSION = "1.1.1"
VERDICT = base.VERDICT

PROCESS_NS = base.PROCESS_NS
COMMON_NS = base.COMMON_NS
EPD_2019_NS = base.EPD_2019_NS
EPD_2013_NS = base.EPD_2013_NS
XML_NS = base.XML_NS
GWP_TOTAL_UUID = base.GWP_TOTAL_UUID
FROZEN_MAP_PATH = base.FROZEN_MAP_PATH
SCHEMA_PATH = base.SCHEMA_PATH
EXPECTED_RESEARCH_FREEZE = base.EXPECTED_RESEARCH_FREEZE
EXPECTED_EF30_SHA256 = base.EXPECTED_EF30_SHA256
CANONICALIZATION = base.CANONICALIZATION
ZERO_DIGEST = base.ZERO_DIGEST
ExtractionError = base.ExtractionError

canonical_json_bytes = base.canonical_json_bytes
sha256_bytes = base.sha256_bytes
sha256_file = base.sha256_file
load_json = base.load_json
canonical_decimal = base.canonical_decimal
validate_schema = base.validate_schema
load_frozen_map = base.load_frozen_map

_original_extract_record = base.extract_record
_original_verify_canonical_source_record = base.verify_canonical_source_record

# Rebind parser support operations to the hardened parent modules while keeping
# the historical extraction algorithm unchanged. ENGINE_VERSION is consumed by
# build_receipt(), which is the correct place for extraction-software identity;
# the declared-value record schema intentionally carries no software field.
base.admission = hardened_admission
base.source_identity = hardened_source_identity
base.ENGINE_VERSION = ENGINE_VERSION


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExtractionError(message)


def verify_hardened_canonical_source_record(record: dict[str, Any]) -> None:
    """Verify canonical structure/integrity plus the superseding parent trust state."""

    _original_verify_canonical_source_record(record)
    version = record.get("source", {}).get("format_version")
    conformance = record.get("conformance", {})

    if version == "1.2":
        require(
            conformance.get("official_stack") == hardened_admission.EXPECTED_V12_STACK,
            "v1.2 canonical source is missing or mismatches the exact v0.9.1 validator/profile stack",
        )
        require(
            conformance.get("official_stack_sha256") == hardened_admission.EXPECTED_V12_STACK_SHA256,
            "v1.2 canonical source official-stack digest mismatch",
        )
        require(
            conformance.get("official_profile") == hardened_admission.EXPECTED_LEGACY_PROFILE,
            "v1.2 canonical source legacy profile identity conflicts with the exact stack",
        )
        require(
            conformance.get("profile_validation_performed") is True,
            "v1.2 canonical source lacks required profile-validation evidence",
        )
    elif version == "1.3":
        require(
            conformance.get("profile_validation_performed") is False,
            "v1.3 canonical source may not silently inherit/relabel the v1.2 profile",
        )
    else:
        raise ExtractionError(f"unsupported hardened canonical source version: {version}")


def extract_record(
    source_path: Path,
    canonical_source: dict[str, Any],
    *,
    indicator_uuid: str = GWP_TOTAL_UUID,
    frozen_map_path: Path = FROZEN_MAP_PATH,
) -> dict[str, Any]:
    verify_hardened_canonical_source_record(canonical_source)
    return _original_extract_record(
        source_path,
        canonical_source,
        indicator_uuid=indicator_uuid,
        frozen_map_path=frozen_map_path,
    )


# Make the inherited CLI use the hardened precheck too. Its build_receipt()
# reads the rebound base.ENGINE_VERSION and records `1.1.1` in the receipt.
base.extract_record = extract_record


def main(argv: list[str] | None = None) -> int:
    return base.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
