from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

IFC_AVAILABLE = importlib.util.find_spec("ifcopenshell") is not None

from reference import declaration_evidence_bundle as v14
from reference import ifc_declaration_product_map as mapper

PRODUCT_UUID = "a7432abd-0881-4977-a817-f8aaf627fb91"
PRODUCT_VERSION = "00.00.001"
PROCESS_UUID = "57a4ae65-d305-421e-b21f-a3f0c35b8abe"
SOURCE_SHA = "1" * 64
PROCESS_SHA = "2" * 64
CANONICAL_SHA = "3" * 64


def seal_record(body: dict) -> dict:
    result = copy.deepcopy(body)
    result["integrity"] = {
        "content_sha256": v14.ZERO_DIGEST,
        "canonicalization": v14.CANONICALIZATION,
        "signature": None,
    }
    result["integrity"]["content_sha256"] = v14.sha256_bytes(v14.canonical_json_bytes(result))
    return result


def seal_receipt(body: dict) -> dict:
    result = copy.deepcopy(body)
    result.pop("receipt_sha256", None)
    result["receipt_sha256"] = v14.sha256_bytes(v14.canonical_json_bytes(result))
    return result


def write_json(path: Path, value: dict) -> bytes:
    raw = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    path.write_bytes(raw)
    return raw


def declaration_parent(root: Path):
    basis = seal_record({
        "schema_version": "1.0",
        "record_type": "ProofGridDeclaredReferenceBasis",
        "verdict": "DECLARED_REFERENCE_BASIS_EXTRACTED_VERIFIABLE",
        "certified": False,
        "calculated": False,
        "environmental_values_transformed": False,
        "unit_conversion_performed": False,
        "parent": {
            "source_sha256": SOURCE_SHA,
            "process_xml_sha256": PROCESS_SHA,
            "process_dataset_uuid": PROCESS_UUID,
            "format_version": "1.2",
        },
        "declared_reference_basis": {
            "basis_status": "IDENTITY_CHAIN_VERIFIED",
            "identity_chain": True,
            "product_flow_uuid": PRODUCT_UUID,
            "quantity_decimal": "1",
            "unit": "kg",
            "statement": f"Synthetic 1 kg reference to {PRODUCT_UUID}.",
        },
        "product_flow": {
            "uuid": PRODUCT_UUID,
            "version": PRODUCT_VERSION,
            "names": [{"language": "en", "value": "wood panel"}],
            "reference_flow_property_internal_id": "0",
            "sha256": "4" * 64,
        },
        "limitations": ["synthetic basis fixture"],
    })
    basis_path = root / "basis.json"
    basis_raw = write_json(basis_path, basis)
    basis_receipt = seal_receipt({
        "verdict": "DECLARED_REFERENCE_BASIS_EXTRACTED_VERIFIABLE",
        "certified": False,
        "engine": {"name": "test", "version": "1.3.0"},
        "record_content_sha256": basis["integrity"]["content_sha256"],
        "record_file_sha256": v14.sha256_bytes(basis_raw),
        "source_sha256": SOURCE_SHA,
        "process_dataset_uuid": PROCESS_UUID,
        "format_version": "1.2",
        "calculated": False,
        "environmental_values_transformed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "limitations": ["synthetic basis fixture"],
    })
    basis_receipt_path = root / "basis-receipt.json"
    write_json(basis_receipt_path, basis_receipt)

    bundle = seal_record({
        "schema_version": "1.0",
        "record_type": "ProofGridDeclarationEvidenceBundle",
        "verdict": "DECLARATION_EVIDENCE_DIMENSIONS_BOUND_VERIFIABLE",
        "source_identity": {
            "source_sha256": SOURCE_SHA,
            "process_xml_sha256": PROCESS_SHA,
            "process_dataset_uuid": PROCESS_UUID,
            "format_version": "1.2",
            "canonical_source_content_sha256": CANONICAL_SHA,
        },
        "parent_evidence": {
            "declared_indicators": {
                "record_content_sha256": "5" * 64,
                "record_file_sha256": "6" * 64,
                "receipt_sha256": "7" * 64,
            },
            "declared_reference_basis": {
                "record_content_sha256": basis["integrity"]["content_sha256"],
                "record_file_sha256": v14.sha256_bytes(basis_raw),
                "receipt_sha256": basis_receipt["receipt_sha256"],
            },
            "amount_semantics": {
                "evidence_file_sha256": "8" * 64,
                "integration_receipt_sha256": "9" * 64,
                "accepted_parent_v13_head": "77931d81ae9857eb33b3cecaf8f9180f0c2b7e4a",
            },
        },
        "environmental_results": {
            "indicator_scope": {"canonical_unit": "kg CO2 eqv."},
            "rows": [{"module": "A1-A3", "value_decimal": "15.559479677163699"}],
            "row_count": 1,
            "value_origin": "DECLARED_IN_SOURCE",
            "aggregation_performed": False,
            "missing_modules_are_zero": False,
        },
        "declared_reference_basis": copy.deepcopy(basis["declared_reference_basis"]),
        "amount_semantics": {
            "format_version": "1.2",
            "reference_exchange_internal_id": "42",
            "mean_amount": {"lexical": "1.0", "decimal": "1"},
            "resulting_amount_present": False,
            "resulting_amount": None,
            "selection_policy": "MEAN_AMOUNT_ACCEPTED_ONLY_WHEN_RESULTING_AMOUNT_ABSENT",
        },
        "dimension_separation": {
            "environmental_result_unit": "kg CO2 eqv.",
            "product_reference_unit": "kg",
            "same_dimension": False,
            "unit_interchange_permitted": False,
        },
        "calculated": False,
        "environmental_values_transformed": False,
        "building_quantity_multiplication_performed": False,
        "aggregation_performed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "certified": False,
        "limitations": ["synthetic v1.4 fixture"],
    })
    bundle_path = root / "bundle.json"
    bundle_raw = write_json(bundle_path, bundle)
    bundle_receipt = seal_receipt({
        "verdict": v14.VERDICT,
        "certified": False,
        "engine": {"name": v14.ENGINE_NAME, "version": v14.ENGINE_VERSION},
        "record_content_sha256": bundle["integrity"]["content_sha256"],
        "record_file_sha256": v14.sha256_bytes(bundle_raw),
        "source_identity": copy.deepcopy(bundle["source_identity"]),
        "parent_evidence": copy.deepcopy(bundle["parent_evidence"]),
        "declared_reference_basis": copy.deepcopy(bundle["declared_reference_basis"]),
        "dimension_separation": copy.deepcopy(bundle["dimension_separation"]),
        "row_count": 1,
        "building_quantity_multiplication_performed": False,
        "calculated": False,
        "environmental_values_transformed": False,
        "aggregation_performed": False,
        "unit_conversion_performed": False,
        "scientific_validation_performed": False,
        "professional_review_performed": False,
        "limitations": ["synthetic v1.4 fixture"],
    })
    bundle_receipt_path = root / "bundle-receipt.json"
    write_json(bundle_receipt_path, bundle_receipt)
    return bundle_path, bundle_receipt_path, basis_path, basis_receipt_path, bundle, bundle_receipt, basis, basis_receipt


@unittest.skipUnless(IFC_AVAILABLE, "IfcOpenShell not installed")
class IFCDeclarationProductMappingTests(unittest.TestCase):
    def build_ifc(self, path: Path, *, mass_prefix: str | None = "KILO", weight: float = 1000.0) -> None:
        import ifcopenshell
        import ifcopenshell.guid

        model = ifcopenshell.file(schema="IFC4")
        mass_unit = model.create_entity("IfcSIUnit", UnitType="MASSUNIT", Prefix=mass_prefix, Name="GRAM")
        units = model.create_entity("IfcUnitAssignment", Units=[mass_unit])
        model.create_entity("IfcProject", GlobalId="0hS$wWKLjAuhSPZ5IG0yTw", Name="ProofGrid v1.5", UnitsInContext=units)
        wall = model.create_entity("IfcWall", GlobalId="1BXL7DJx51bvggyIPU2Xi5", Name="Mapped Wall")
        material = model.create_entity("IfcMaterial", Name="RX-MATERIAL-UNRELATED-TO-WOOD-PANEL")
        model.create_entity("IfcRelAssociatesMaterial", GlobalId=ifcopenshell.guid.new(), RelatedObjects=[wall], RelatingMaterial=material)
        quantity = model.create_entity("IfcQuantityWeight", Name="Mass", WeightValue=weight)
        qset = model.create_entity("IfcElementQuantity", GlobalId=ifcopenshell.guid.new(), Name="Qto_WallBaseQuantities", Quantities=[quantity])
        model.create_entity("IfcRelDefinesByProperties", GlobalId=ifcopenshell.guid.new(), RelatedObjects=[wall], RelatingPropertyDefinition=qset)
        model.write(str(path))

    def prepare(self, root: Path, **kwargs):
        from adapters.ifc.extract import extract_ifc_declared_data

        ifc_path = root / "fixture.ifc"
        self.build_ifc(ifc_path, **kwargs)
        extraction = extract_ifc_declared_data(ifc_path)
        extraction_path = root / "extraction.json"
        write_json(extraction_path, extraction)
        bundle_paths = declaration_parent(root)
        bundle_path, bundle_receipt_path, basis_path, basis_receipt_path, bundle, bundle_receipt, basis, basis_receipt = bundle_paths
        wall = next(e for e in extraction["elements"] if e["ifc_type"] == "IfcWall")
        material = wall["materials"][0]
        quantity = next(q for q in wall["quantities"] if q["ifc_quantity_type"] == "IfcQuantityWeight")
        declaration = mapper.resolve_declaration(bundle, bundle_receipt, basis, basis_receipt)
        mapping = {
            "schema_version": "1.0",
            "artifact_version": "1.5.0",
            "mapping": {
                "id": "RX-V15-MAP-001",
                "source_ifc": {"sha256": extraction["source_sha256"], "schema": extraction["schema"]},
                "element": {"step_id": wall["step_id"], "global_id": wall["global_id"], "ifc_type": wall["ifc_type"]},
                "material": {
                    "association_step_id": material["association_step_id"],
                    "material_step_id": material["material_step_id"],
                    "declared_name": material["name"],
                    "source_type": material["source_type"],
                },
                "quantity": {
                    "set_step_id": quantity["set_step_id"],
                    "quantity_step_id": quantity["quantity_step_id"],
                    "name": quantity["name"],
                    "ifc_quantity_type": quantity["ifc_quantity_type"],
                    "value": quantity["value"],
                    "unit": {
                        "unit_type": quantity["unit"]["unit_type"],
                        "name": quantity["unit"]["name"],
                        "prefix": quantity["unit"]["prefix"],
                        "source": quantity["unit"]["source"],
                    },
                },
                "declaration": declaration,
                "review": {
                    "state": "REVIEWED_MAPPING_DECISION",
                    "reviewer": "ProofGrid synthetic reviewer",
                    "role": "synthetic test mapping reviewer",
                    "rationale": "Explicitly map exact IFC IDs to the exact declaration product flow; display-name similarity is intentionally absent.",
                    "reference": "issue-42-synthetic-control",
                },
                "limitations": ["synthetic mapping fixture; not professional review"],
            },
        }
        mapping_path = root / "mapping.json"
        write_json(mapping_path, mapping)
        return extraction_path, mapping_path, bundle_path, bundle_receipt_path, basis_path, basis_receipt_path, mapping, extraction

    def run(self, prepared):
        return mapper.map_product(*prepared[:6])

    def test_explicit_mapping_succeeds_despite_dissimilar_display_names(self):
        with tempfile.TemporaryDirectory() as td:
            prepared = self.prepare(Path(td))
            record = self.run(prepared)
            self.assertEqual(record["verdict"], mapper.VERDICT)
            self.assertEqual(record["declaration"]["product_flow_uuid"], PRODUCT_UUID)
            self.assertEqual(record["declaration"]["product_flow_version"], PRODUCT_VERSION)
            self.assertEqual(record["ifc"]["material"]["declared_name"], "RX-MATERIAL-UNRELATED-TO-WOOD-PANEL")
            self.assertEqual(record["ifc"]["quantity"]["value"], 1000.0)
            self.assertEqual(record["ifc"]["quantity"]["unit_identity"], "kg")
            self.assertFalse(record["fuzzy_matching_performed"])
            self.assertFalse(record["automatic_name_mapping_performed"])
            self.assertFalse(record["environmental_calculation_performed"])
            self.assertFalse(record["building_quantity_multiplication_performed"])
            self.assertFalse(record["certified"])

    def mutate_mapping(self, prepared, mutator):
        extraction_path, mapping_path, bundle_path, bundle_receipt_path, basis_path, basis_receipt_path, mapping, _ = prepared
        mutator(mapping)
        write_json(mapping_path, mapping)
        with self.assertRaises(mapper.ProductMappingError):
            mapper.map_product(extraction_path, mapping_path, bundle_path, bundle_receipt_path, basis_path, basis_receipt_path)

    def test_wrong_ifc_source_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = self.prepare(Path(td))
            self.mutate_mapping(p, lambda m: m["mapping"]["source_ifc"].__setitem__("sha256", "0" * 64))

    def test_wrong_element_global_id_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = self.prepare(Path(td))
            self.mutate_mapping(p, lambda m: m["mapping"]["element"].__setitem__("global_id", "WRONG"))

    def test_wrong_material_step_id_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = self.prepare(Path(td))
            self.mutate_mapping(p, lambda m: m["mapping"]["material"].__setitem__("material_step_id", m["mapping"]["material"]["material_step_id"] + 1))

    def test_wrong_quantity_value_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = self.prepare(Path(td))
            self.mutate_mapping(p, lambda m: m["mapping"]["quantity"].__setitem__("value", 999.0))

    def test_wrong_product_flow_version_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = self.prepare(Path(td))
            self.mutate_mapping(p, lambda m: m["mapping"]["declaration"].__setitem__("product_flow_version", "99.99.999"))

    def test_wrong_bundle_digest_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = self.prepare(Path(td))
            self.mutate_mapping(p, lambda m: m["mapping"]["declaration"].__setitem__("bundle_content_sha256", "a" * 64))

    def test_basis_parent_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = self.prepare(Path(td))
            basis_path = p[4]
            basis = json.loads(basis_path.read_text())
            basis["product_flow"]["version"] = "99.99.999"
            write_json(basis_path, basis)
            with self.assertRaises(mapper.ProductMappingError):
                self.run(p)

    def test_non_identity_mass_unit_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = self.prepare(Path(td), mass_prefix=None)
            # The mapping schema requires the supported kg identity and therefore fails closed.
            with self.assertRaises(mapper.ProductMappingError):
                self.run(p)

    def test_name_only_artifact_rejected_by_schema(self):
        with tempfile.TemporaryDirectory() as td:
            p = self.prepare(Path(td))
            mapping_path = p[1]
            mapping = p[6]
            del mapping["mapping"]["material"]["material_step_id"]
            del mapping["mapping"]["material"]["association_step_id"]
            write_json(mapping_path, mapping)
            with self.assertRaises(mapper.ProductMappingError):
                self.run(p)

    def test_bundle_certification_promotion_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = self.prepare(Path(td))
            receipt_path = p[3]
            receipt = json.loads(receipt_path.read_text())
            receipt["certified"] = True
            receipt.pop("receipt_sha256", None)
            receipt = seal_receipt(receipt)
            write_json(receipt_path, receipt)
            with self.assertRaises(mapper.ProductMappingError):
                self.run(p)

    def test_repeat_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            p = self.prepare(Path(td))
            a = self.run(p)
            b = self.run(p)
            self.assertEqual(mapper.canonical_json_bytes(a), mapper.canonical_json_bytes(b))
            self.assertEqual(a["integrity"]["content_sha256"], b["integrity"]["content_sha256"])


if __name__ == "__main__":
    unittest.main()
