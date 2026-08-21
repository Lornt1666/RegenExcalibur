from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from reference import declared_environmental_indicators as v11
from reference import rxep_declared_indicator_binding as rxep
from reference import declared_reference_basis as basis
from tests import test_declared_environmental_indicators as fixtures

PROCESS_UUID = "11111111-2222-3333-4444-555555555555"
FLOW_UUID = "a7432abd-0881-4977-a817-f8aaf627fb91"
FLOW_PROPERTY_UUID = "93a60a56-a3c8-11da-a746-0800200b9a66"
UNIT_GROUP_UUID = "ad38d542-3fe9-439d-9b95-2f5f7752acaf"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal(body: dict) -> dict:
    value = copy.deepcopy(body)
    value.pop("receipt_sha256", None)
    value["receipt_sha256"] = basis.sha256_bytes(basis.canonical_json_bytes(value))
    return value


def process_bytes(
    version: str,
    *,
    amount: str = "1.0",
    reference_ids: tuple[str, ...] = ("42",),
    include_exchange: bool = True,
) -> bytes:
    base = fixtures.process_xml(version).decode("utf-8")
    refs = "".join(f"<referenceToReferenceFlow>{x}</referenceToReferenceFlow>" for x in reference_ids)
    quantitative = f'<quantitativeReference type="Reference flow(s)">{refs}</quantitativeReference>'
    base = base.replace("</processInformation>", quantitative + "</processInformation>")
    exchanges = ""
    if include_exchange:
        exchanges = f'''<exchanges><exchange dataSetInternalID="42">
          <referenceToFlowDataSet type="flow data set" refObjectId="{FLOW_UUID}" version="00.00.001" />
          <meanAmount>{amount}</meanAmount>
        </exchange></exchanges>'''
    base = base.replace("</processDataSet>", exchanges + "</processDataSet>")
    return base.encode("utf-8")


def write_source(root: Path, version: str, raw: bytes) -> tuple[Path, str]:
    if version == "1.3":
        path = root / "source.xml"
        path.write_bytes(raw)
        return path, "application/xml"
    path = root / "source.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as zf:
        fixtures.write_zip_entry(zf, "ILCD/processes/process.xml", raw)
    return path, "application/zip"


def write_closure(
    root: Path,
    *,
    flow_uuid: str = FLOW_UUID,
    flow_mean: str = "1.0",
    unit_factor: str = "1",
) -> tuple[Path, Path, Path]:
    flow = root / "flow.xml"
    flow.write_text(f'''<?xml version="1.0"?>
<f:flowDataSet xmlns:f="http://lca.jrc.it/ILCD/Flow" xmlns:common="http://lca.jrc.it/ILCD/Common" version="1.1">
  <f:flowInformation><f:dataSetInformation><common:UUID>{flow_uuid}</common:UUID><f:name><f:baseName xml:lang="en">wood panel</f:baseName></f:name></f:dataSetInformation>
    <f:quantitativeReference><f:referenceToReferenceFlowProperty>0</f:referenceToReferenceFlowProperty></f:quantitativeReference>
  </f:flowInformation>
  <f:administrativeInformation><f:publicationAndOwnership><common:dataSetVersion>00.00.001</common:dataSetVersion></f:publicationAndOwnership></f:administrativeInformation>
  <f:flowProperties><f:flowProperty dataSetInternalID="0"><f:referenceToFlowPropertyDataSet refObjectId="{FLOW_PROPERTY_UUID}" version="03.00.000"/><f:meanValue>{flow_mean}</f:meanValue></f:flowProperty></f:flowProperties>
</f:flowDataSet>''', encoding="utf-8")
    prop = root / "flow-property.xml"
    prop.write_text(f'''<?xml version="1.0"?>
<flowPropertyDataSet xmlns="http://lca.jrc.it/ILCD/FlowProperty" xmlns:common="http://lca.jrc.it/ILCD/Common" version="1.1">
  <flowPropertiesInformation><dataSetInformation><common:UUID>{FLOW_PROPERTY_UUID}</common:UUID><common:name xml:lang="en">Mass</common:name></dataSetInformation>
    <quantitativeReference><referenceToReferenceUnitGroup refObjectId="{UNIT_GROUP_UUID}" type="unit group data set"/></quantitativeReference>
  </flowPropertiesInformation>
  <administrativeInformation><publicationAndOwnership><common:dataSetVersion>03.00.000</common:dataSetVersion></publicationAndOwnership></administrativeInformation>
</flowPropertyDataSet>''', encoding="utf-8")
    unit = root / "unit-group.xml"
    unit.write_text(f'''<?xml version="1.0"?>
<unitGroupDataSet xmlns="http://lca.jrc.it/ILCD/UnitGroup" xmlns:common="http://lca.jrc.it/ILCD/Common" version="1.1">
  <unitGroupInformation><dataSetInformation><common:UUID>{UNIT_GROUP_UUID}</common:UUID></dataSetInformation>
    <quantitativeReference><referenceToReferenceUnit>0</referenceToReferenceUnit></quantitativeReference>
  </unitGroupInformation>
  <administrativeInformation><publicationAndOwnership><common:dataSetVersion>25.00.000</common:dataSetVersion></publicationAndOwnership></administrativeInformation>
  <units><unit dataSetInternalID="0"><name>kg</name><meanValue>{unit_factor}</meanValue></unit></units>
</unitGroupDataSet>''', encoding="utf-8")
    return flow, prop, unit


def rxep_parent(root: Path, version: str, raw: bytes) -> tuple[Path, Path, Path]:
    source, media = write_source(root, version, raw)
    canonical = fixtures.canonical_record(source, media, version)
    record = v11.extract_record(source, canonical)
    record_bytes = (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    v11_receipt = v11.build_receipt(record, record_bytes)
    bundle = rxep.build_bundle(record, record_bytes, v11_receipt)
    bundle_path = root / "rxep-bundle.json"
    bundle_bytes = (json.dumps(bundle, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    bundle_path.write_bytes(bundle_bytes)
    receipt = rxep.build_receipt(bundle, bundle_bytes)
    receipt_path = root / "rxep-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return source, bundle_path, receipt_path


def research_receipt(root: Path, version: str, process_raw: bytes, flow: Path, prop: Path, unit: Path) -> tuple[Path, str]:
    process_key = "v12_process" if version == "1.2" else "v13_process"
    flow_key = "v12_product_flow" if version == "1.2" else "v13_product_flow"
    report = {
        "verdict": "DECLARED_REFERENCE_BASIS_RESEARCH_VERIFIABLE",
        "research_version": "1.3.0",
        "extractor_accepted": False,
        "calculated": False,
        "environmental_values_transformed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "file_evidence": {
            process_key: {"sha256": hashlib.sha256(process_raw).hexdigest()},
            flow_key: {"sha256": sha(flow)},
            "flow_property_master": {"sha256": sha(prop)},
            "unit_group_master": {"sha256": sha(unit)},
        },
    }
    report = seal(report)
    path = root / "research.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path, report["receipt_sha256"]


def build_case(
    root: Path,
    version: str = "1.3",
    *,
    amount: str = "1.0",
    reference_ids: tuple[str, ...] = ("42",),
    include_exchange: bool = True,
    flow_uuid: str = FLOW_UUID,
    flow_mean: str = "1.0",
    unit_factor: str = "1",
):
    raw = process_bytes(version, amount=amount, reference_ids=reference_ids, include_exchange=include_exchange)
    source, bundle, rxep_receipt = rxep_parent(root, version, raw)
    flow, prop, unit = write_closure(root, flow_uuid=flow_uuid, flow_mean=flow_mean, unit_factor=unit_factor)
    research, digest = research_receipt(root, version, raw, flow, prop, unit)
    return source, bundle, rxep_receipt, flow, prop, unit, research, digest


class DeclaredReferenceBasisTests(unittest.TestCase):
    def run_extract(self, root: Path, version: str = "1.3", **kwargs):
        source, bundle, receipt, flow, prop, unit, research, digest = build_case(root, version, **kwargs)
        with patch.object(basis, "RESEARCH_RECEIPT_SHA256", digest):
            record = basis.extract(
                bundle,
                rxep_receipt_path=receipt,
                source_path=source,
                product_flow_path=flow,
                flow_property_master_path=prop,
                unit_group_master_path=unit,
                research_receipt_path=research,
            )
        return record, (source, bundle, receipt, flow, prop, unit, research, digest)

    def test_v12_and_v13_identity_basis(self):
        for version in ("1.2", "1.3"):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as td:
                record, _ = self.run_extract(Path(td), version)
                self.assertEqual(record["verdict"], basis.VERDICT)
                self.assertEqual(record["declared_reference_basis"]["quantity_decimal"], "1")
                self.assertEqual(record["declared_reference_basis"]["unit"], "kg")
                self.assertFalse(record["calculated"])
                self.assertFalse(record["environmental_values_transformed"])
                self.assertFalse(record["unit_conversion_performed"])
                self.assertFalse(record["certified"])

    def test_repeated_record_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a, material = self.run_extract(root)
            source, bundle, receipt, flow, prop, unit, research, digest = material
            with patch.object(basis, "RESEARCH_RECEIPT_SHA256", digest):
                b = basis.extract(bundle, rxep_receipt_path=receipt, source_path=source, product_flow_path=flow, flow_property_master_path=prop, unit_group_master_path=unit, research_receipt_path=research)
            self.assertEqual(basis.canonical_json_bytes(a), basis.canonical_json_bytes(b))

    def test_rxep_bundle_tamper_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, material = self.run_extract(root)
            source, bundle, receipt, flow, prop, unit, research, digest = material
            data = json.loads(bundle.read_text()); data["certified"] = True; bundle.write_text(json.dumps(data))
            with patch.object(basis, "RESEARCH_RECEIPT_SHA256", digest), self.assertRaises(Exception):
                basis.extract(bundle, rxep_receipt_path=receipt, source_path=source, product_flow_path=flow, flow_property_master_path=prop, unit_group_master_path=unit, research_receipt_path=research)

    def test_source_hash_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, material = self.run_extract(root)
            source, bundle, receipt, flow, prop, unit, research, digest = material
            source.write_bytes(source.read_bytes() + b"x")
            with patch.object(basis, "RESEARCH_RECEIPT_SHA256", digest), self.assertRaisesRegex(basis.BasisError, "source SHA"):
                basis.extract(bundle, rxep_receipt_path=receipt, source_path=source, product_flow_path=flow, flow_property_master_path=prop, unit_group_master_path=unit, research_receipt_path=research)

    def test_multiple_reference_flows_fail(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(Exception, "exactly one process reference flow"):
                self.run_extract(Path(td), reference_ids=("42", "43"))

    def test_missing_reference_exchange_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(Exception, "missing or ambiguous"):
                self.run_extract(Path(td), include_exchange=False)

    def test_product_flow_uuid_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(Exception, "product flow UUID"):
                self.run_extract(Path(td), flow_uuid="00000000-0000-0000-0000-000000000000")

    def test_non_identity_process_amount_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(basis.BasisError, "process reference amount exactly 1"):
                self.run_extract(Path(td), amount="2.0")

    def test_non_identity_flow_property_mean_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(basis.BasisError, "flow-property mean exactly 1"):
                self.run_extract(Path(td), flow_mean="2.0")

    def test_non_identity_unit_factor_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(basis.BasisError, "separate explicit conversion gate"):
                self.run_extract(Path(td), unit_factor="0.001")

    def test_reference_closure_tamper_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, material = self.run_extract(root)
            source, bundle, receipt, flow, prop, unit, research, digest = material
            flow.write_bytes(flow.read_bytes() + b"x")
            with patch.object(basis, "RESEARCH_RECEIPT_SHA256", digest), self.assertRaisesRegex(basis.BasisError, "product-flow reference-closure hash mismatch"):
                basis.extract(bundle, rxep_receipt_path=receipt, source_path=source, product_flow_path=flow, flow_property_master_path=prop, unit_group_master_path=unit, research_receipt_path=research)

    def test_research_receipt_tamper_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, material = self.run_extract(root)
            source, bundle, receipt, flow, prop, unit, research, digest = material
            data = json.loads(research.read_text()); data["certified"] = True; research.write_text(json.dumps(data))
            with patch.object(basis, "RESEARCH_RECEIPT_SHA256", digest), self.assertRaisesRegex(basis.BasisError, "receipt digest mismatch"):
                basis.extract(bundle, rxep_receipt_path=receipt, source_path=source, product_flow_path=flow, flow_property_master_path=prop, unit_group_master_path=unit, research_receipt_path=research)

    def test_receipt_is_non_calculated_and_non_certified(self):
        with tempfile.TemporaryDirectory() as td:
            record, _ = self.run_extract(Path(td))
            raw = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()
            receipt = basis.build_receipt(record, raw)
            self.assertFalse(receipt["calculated"])
            self.assertFalse(receipt["environmental_values_transformed"])
            self.assertFalse(receipt["unit_conversion_performed"])
            self.assertFalse(receipt["scientific_validation_performed"])
            self.assertFalse(receipt["professional_review_performed"])
            self.assertFalse(receipt["certified"])


if __name__ == "__main__":
    unittest.main()
