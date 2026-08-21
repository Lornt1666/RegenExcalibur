from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from reference import declared_environmental_indicators as extractor
from reference import environmental_admission as admission
from reference import environmental_source_identity as source_identity

PROCESS_NS = extractor.PROCESS_NS
COMMON_NS = extractor.COMMON_NS
EPD_2019_NS = extractor.EPD_2019_NS
EPD_2013_NS = extractor.EPD_2013_NS
GWP = extractor.GWP_TOTAL_UUID
UNIT_GROUP = "1ebf3012-d0db-4de2-aefd-ef30cedb0be1"
PROCESS_UUID = "11111111-2222-3333-4444-555555555555"


def seal(body: dict) -> dict:
    result = copy.deepcopy(body)
    result.pop("receipt_sha256", None)
    result["receipt_sha256"] = admission.sha256_bytes(admission.canonical_json_bytes(result))
    return result


def process_xml(
    version: str,
    *,
    indicator_uuid: str = GWP,
    indicator_version: str | None = None,
    unit_group_uuid: str = UNIT_GROUP,
    modules: list[tuple[str, str | None, str]] | None = None,
    declare_scenario: bool = True,
    mean_amount: str = "999.25",
) -> bytes:
    if modules is None:
        modules = [
            ("A1-A3", None, "15.559479677163699"),
            ("A4", "Transport to Gdansk", "10.403452605105544"),
        ]
    scenario_xml = ""
    if declare_scenario:
        scenario_xml = f'''<common:other>
          <epd:scenarios>
            <epd:scenario name="Transport to Gdansk" group="Transport" default="true" />
          </epd:scenarios>
        </common:other>'''
    version_attr = f' version="{indicator_version}"' if indicator_version else ""
    amount_xml = "\n".join(
        f'<epd:amount module="{module}"{f" scenario=\"{scenario}\"" if scenario else ""}>{value}</epd:amount>'
        for module, scenario, value in modules
    )
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<processDataSet xmlns="{PROCESS_NS}" xmlns:common="{COMMON_NS}" xmlns:epd2="{EPD_2019_NS}" xmlns:epd="{EPD_2013_NS}" epd2:epd-version="{version}" version="1.1">
  <processInformation>
    <dataSetInformation>
      <common:UUID>{PROCESS_UUID}</common:UUID>
      <name><baseName xml:lang="en">ProofGrid v1.1 synthetic declared indicator fixture</baseName></name>
      {scenario_xml}
    </dataSetInformation>
  </processInformation>
  <administrativeInformation>
    <publicationAndOwnership><common:dataSetVersion>00.00.001</common:dataSetVersion></publicationAndOwnership>
  </administrativeInformation>
  <LCIAResults>
    <LCIAResult>
      <referenceToLCIAMethodDataSet refObjectId="{indicator_uuid}" type="LCIA method data set" uri="../lciamethods/{indicator_uuid}"{version_attr} />
      <meanAmount>{mean_amount}</meanAmount>
      <common:other>
        {amount_xml}
        <epd:referenceToUnitGroupDataSet refObjectId="{unit_group_uuid}" type="unit group data set" uri="../unitgroups/{unit_group_uuid}" />
      </common:other>
    </LCIAResult>
  </LCIAResults>
</processDataSet>
'''.encode("utf-8")


def write_zip_entry(zf: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name)
    info.date_time = (1980, 1, 1, 0, 0, 0)
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0o100644 << 16
    zf.writestr(info, data)


def build_source(root: Path, version: str, **kwargs) -> tuple[Path, str]:
    raw = process_xml(version, **kwargs)
    if version == "1.3":
        path = root / "source.xml"
        path.write_bytes(raw)
        return path, "application/xml"
    path = root / "source.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as zf:
        write_zip_entry(zf, "ILCD/processes/process.xml", raw)
    return path, "application/zip"


def receipt_chain(source: Path, media_type: str, version: str) -> tuple[dict, dict, dict]:
    detected = admission.detect_source(source, media_type)
    preflight = seal({
        "verdict": "ENVIRONMENTAL_DECLARATION_ADMISSION_PREFLIGHT_VERIFIABLE",
        "state": "AWAITING_CONFORMANCE",
        "certified": False,
        "normalization_permitted": False,
        "rights": {
            "decision": "AUTHORIZED_FOR_DECLARED_IMPORT_ONLY",
            "status": "TEST_ONLY",
            "transformation": "ALLOWED",
            "redistribution": "PROHIBITED",
        },
        "source": {
            "path": source.name,
            "media_type": media_type,
            "declared_format": {"name": "ILCD+EPD", "version": version},
            **detected,
        },
        "routing": admission.route_for(version),
    })
    if version == "1.2":
        conformance = seal({
            "claim_token": admission.V12_CLAIM,
            "compatibility_claim": True,
            "certified": False,
            "authority_inference_allowed": False,
            "package_manifest_sha256": detected["package_manifest_sha256"],
            "official_profile": {
                "coordinate": "com.okworx.ilcd.validation.profiles:EPD-1.2-OEKOBAUDAT:3.8.0",
                "jar_sha256": "9" * 64,
            },
            "positive_control": {"error_count": 0, "warning_count": 26, "is_positive": True},
        })
    else:
        conformance = seal({
            "verdict": admission.V13_VERDICT,
            "certified": False,
            "format_conformance": {
                "xsd_validation": True,
                "master_data_identity_validation": True,
                "profile_validation_performed": False,
                "profile_status": "AUTHORITATIVE_V1_3_PROFILE_NOT_AVAILABLE_IN_GATE",
            },
            "synthetic_fixture": {
                "sha256": detected["source_sha256"],
                "identity": {"epd_version": "1.3"},
            },
        })
    final = admission.finalize(preflight, conformance)
    return preflight, conformance, final


def canonical_record(source: Path, media_type: str, version: str) -> dict:
    pre, conf, final = receipt_chain(source, media_type, version)
    return source_identity.build_record(source, pre, conf, final)


class DeclaredEnvironmentalIndicatorTests(unittest.TestCase):
    def test_v12_extracts_declared_rows_without_mean_amount(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.2")
            canonical = canonical_record(source, media, "1.2")
            record = extractor.extract_record(source, canonical)
            self.assertEqual(record["verdict"], extractor.VERDICT)
            self.assertEqual(len(record["rows"]), 2)
            self.assertEqual(record["rows"][0]["module"], "A1-A3")
            self.assertEqual(record["rows"][0]["value_lexical"], "15.559479677163699")
            self.assertEqual(record["rows"][0]["value_decimal"], "15.559479677163699")
            self.assertEqual(record["ignored_unscoped_mean_amount"]["lexical_value"], "999.25")
            self.assertFalse(record["ignored_unscoped_mean_amount"]["extracted"])
            self.assertFalse(record["calculated"])
            self.assertFalse(record["unit_conversion_performed"])
            self.assertFalse(record["certified"])

    def test_v13_preserves_declared_scenario_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.3")
            canonical = canonical_record(source, media, "1.3")
            record = extractor.extract_record(source, canonical)
            scenario = record["rows"][1]["scenario"]
            self.assertEqual(scenario["name"], "Transport to Gdansk")
            self.assertEqual(scenario["group"], "Transport")
            self.assertTrue(scenario["default"])
            self.assertEqual(record["source"]["format_version"], "1.3")

    def test_repeated_extraction_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.2")
            canonical = canonical_record(source, media, "1.2")
            a = extractor.extract_record(source, canonical)
            b = extractor.extract_record(source, canonical)
            self.assertEqual(extractor.canonical_json_bytes(a), extractor.canonical_json_bytes(b))
            self.assertEqual(a["integrity"]["content_sha256"], b["integrity"]["content_sha256"])

    def test_canonical_source_integrity_tamper_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.3")
            canonical = canonical_record(source, media, "1.3")
            canonical["identity"]["process_dataset_uuid"] = "tampered"
            with self.assertRaisesRegex(extractor.ExtractionError, "integrity"):
                extractor.extract_record(source, canonical)

    def test_post_canonical_source_byte_tamper_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.3")
            canonical = canonical_record(source, media, "1.3")
            source.write_bytes(source.read_bytes() + b"\n")
            with self.assertRaisesRegex(extractor.ExtractionError, "source SHA-256 mismatch"):
                extractor.extract_record(source, canonical)

    def test_unknown_indicator_uuid_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.3")
            canonical = canonical_record(source, media, "1.3")
            with self.assertRaisesRegex(extractor.ExtractionError, "not admitted"):
                extractor.extract_record(source, canonical, indicator_uuid="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    def test_unit_group_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.3", unit_group_uuid="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
            canonical = canonical_record(source, media, "1.3")
            with self.assertRaisesRegex(extractor.ExtractionError, "unit-group UUID mismatch"):
                extractor.extract_record(source, canonical)

    def test_non_finite_declared_amount_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.3", modules=[("A1-A3", None, "NaN")])
            canonical = canonical_record(source, media, "1.3")
            with self.assertRaisesRegex(extractor.ExtractionError, "finite"):
                extractor.extract_record(source, canonical)

    def test_unknown_module_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.3", modules=[("Z9", None, "1.0")])
            canonical = canonical_record(source, media, "1.3")
            with self.assertRaisesRegex(extractor.ExtractionError, "lifecycle module"):
                extractor.extract_record(source, canonical)

    def test_undeclared_scenario_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(
                root,
                "1.3",
                declare_scenario=False,
                modules=[("A4", "Transport to Gdansk", "1.0")],
            )
            canonical = canonical_record(source, media, "1.3")
            with self.assertRaisesRegex(extractor.ExtractionError, "undeclared scenario"):
                extractor.extract_record(source, canonical)

    def test_duplicate_module_scenario_identity_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(
                root,
                "1.3",
                modules=[("A1-A3", None, "1.0"), ("A1-A3", None, "2.0")],
            )
            canonical = canonical_record(source, media, "1.3")
            with self.assertRaisesRegex(extractor.ExtractionError, "duplicate/conflicting"):
                extractor.extract_record(source, canonical)

    def test_missing_declared_amounts_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.3", modules=[])
            canonical = canonical_record(source, media, "1.3")
            with self.assertRaisesRegex(extractor.ExtractionError, "no declared"):
                extractor.extract_record(source, canonical)

    def test_indicator_reference_version_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.3", indicator_version="99.99.999")
            canonical = canonical_record(source, media, "1.3")
            with self.assertRaisesRegex(extractor.ExtractionError, "catalogue version"):
                extractor.extract_record(source, canonical)

    def test_frozen_map_research_binding_tamper_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.3")
            canonical = canonical_record(source, media, "1.3")
            frozen = json.loads(extractor.FROZEN_MAP_PATH.read_text())
            frozen["research_freeze"]["receipt_sha256"] = "0" * 64
            path = root / "frozen.json"
            path.write_text(json.dumps(frozen), encoding="utf-8")
            with self.assertRaisesRegex(extractor.ExtractionError, "research freeze"):
                extractor.extract_record(source, canonical, frozen_map_path=path)

    def test_canonical_certification_promotion_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, media = build_source(root, "1.3")
            canonical = canonical_record(source, media, "1.3")
            promoted = copy.deepcopy(canonical)
            promoted["certified"] = True
            shadow = copy.deepcopy(promoted)
            shadow["integrity"]["content_sha256"] = source_identity.ZERO_DIGEST
            promoted["integrity"]["content_sha256"] = source_identity.sha256_bytes(source_identity.canonical_json_bytes(shadow))
            with self.assertRaises(extractor.ExtractionError):
                extractor.extract_record(source, promoted)


if __name__ == "__main__":
    unittest.main()
