import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

IFC_AVAILABLE = importlib.util.find_spec("ifcopenshell") is not None
ROOT = Path(__file__).resolve().parents[1]
SOURCE_REGISTRY = ROOT / "evidence" / "examples" / "alberta-house" / "lca-sources.json"
SOURCE_CONTENT = ROOT / "evidence" / "examples" / "alberta-house" / "sources" / "fictional-demo-factors.txt"


@unittest.skipUnless(IFC_AVAILABLE, "IfcOpenShell not installed")
class IFCEnvironmentalMappingV05Tests(unittest.TestCase):
    def build_ifc(
        self,
        path: Path,
        *,
        material_name: str | None = "Concrete",
        weight: float = 1000.0,
        mass_prefix: str | None = "KILO",
        mass_name: str = "GRAM",
    ) -> None:
        import ifcopenshell
        import ifcopenshell.guid

        model = ifcopenshell.file(schema="IFC4")
        mass_unit = model.create_entity("IfcSIUnit", UnitType="MASSUNIT", Prefix=mass_prefix, Name=mass_name)
        units = model.create_entity("IfcUnitAssignment", Units=[mass_unit])
        model.create_entity(
            "IfcProject",
            GlobalId="0hS$wWKLjAuhSPZ5IG0yTw",
            Name="ProofGrid v0.5 Mapping Project",
            UnitsInContext=units,
        )
        wall = model.create_entity(
            "IfcWall",
            GlobalId="1BXL7DJx51bvggyIPU2Xi5",
            Name="Mapped Wall",
        )
        material = model.create_entity("IfcMaterial", Name=material_name)
        model.create_entity(
            "IfcRelAssociatesMaterial",
            GlobalId=ifcopenshell.guid.new(),
            RelatedObjects=[wall],
            RelatingMaterial=material,
        )
        quantity = model.create_entity("IfcQuantityWeight", Name="Mass", WeightValue=weight)
        qset = model.create_entity(
            "IfcElementQuantity",
            GlobalId=ifcopenshell.guid.new(),
            Name="Qto_WallBaseQuantities",
            Quantities=[quantity],
        )
        model.create_entity(
            "IfcRelDefinesByProperties",
            GlobalId=ifcopenshell.guid.new(),
            RelatedObjects=[wall],
            RelatingPropertyDefinition=qset,
        )
        model.write(str(path))

    def extract(self, ifc_path: Path, extraction_path: Path) -> dict:
        from adapters.ifc.extract import extract_ifc_declared_data

        extraction = extract_ifc_declared_data(ifc_path)
        extraction_path.write_bytes((json.dumps(extraction, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        return extraction

    def mapping_from_extraction(self, extraction: dict) -> dict:
        wall = next(item for item in extraction["elements"] if item["ifc_type"] == "IfcWall")
        material = wall["materials"][0]
        quantity = next(item for item in wall["quantities"] if item["ifc_quantity_type"] == "IfcQuantityWeight")
        unit = quantity["unit"]
        return {
            "schema_version": "1.0",
            "artifact_version": "0.5.0",
            "mappings": [
                {
                    "id": "RX-MAP-TEST-WALL-CONCRETE-MASS",
                    "source_ifc": {
                        "sha256": extraction["source_sha256"],
                        "schema": extraction["schema"],
                    },
                    "element": {
                        "global_id": wall["global_id"],
                        "step_id": wall["step_id"],
                        "ifc_type": wall["ifc_type"],
                    },
                    "material": {
                        "association_step_id": material["association_step_id"],
                        "material_step_id": material["material_step_id"],
                        "declared_name": material["name"] or "Concrete",
                        "source_type": material["source_type"],
                    },
                    "quantity": {
                        "set_step_id": quantity["set_step_id"],
                        "quantity_step_id": quantity["quantity_step_id"],
                        "name": quantity["name"],
                        "ifc_quantity_type": quantity["ifc_quantity_type"],
                        "value": quantity["value"],
                        "unit": {
                            "unit_type": unit["unit_type"],
                            "name": unit["name"],
                            "prefix": unit["prefix"],
                            "source": unit["source"],
                        },
                    },
                    "target": {
                        "material_identity_id": "concrete",
                        "source_record_id": "RX-FICT-CONCRETE-A1A3",
                    },
                    "review": {
                        "state": "REVIEWED",
                        "author": "ProofGrid synthetic conformance fixture",
                        "rationale": "Explicit synthetic mapping selected for v0.5 conformance; target is not inferred from the IFC material name.",
                        "reference": "issue-8-known-answer",
                    },
                }
            ],
        }

    def write_json(self, path: Path, value: object) -> None:
        path.write_bytes((json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))

    def copy_registry(self, root: Path) -> Path:
        registry_path = root / "lca-sources.json"
        source_dir = root / "sources"
        source_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE_REGISTRY, registry_path)
        shutil.copyfile(SOURCE_CONTENT, source_dir / "fictional-demo-factors.txt")
        return registry_path

    def prepare(self, root: Path, **ifc_kwargs):
        ifc_path = root / "mapping.ifc"
        extraction_path = root / "extraction.json"
        mapping_path = root / "mapping.json"
        self.build_ifc(ifc_path, **ifc_kwargs)
        extraction = self.extract(ifc_path, extraction_path)
        mapping = self.mapping_from_extraction(extraction)
        self.write_json(mapping_path, mapping)
        return extraction_path, mapping_path, mapping, self.copy_registry(root)

    def run_map(self, extraction_path: Path, mapping_path: Path, registry_path: Path):
        from reference.ifc_lca_map import map_explicit_ifc_environmental

        return map_explicit_ifc_environmental(extraction_path, mapping_path, registry_path)

    def assert_mapping_error(self, extraction_path: Path, mapping_path: Path, registry_path: Path):
        from reference.ifc_lca_map import MappingError

        with self.assertRaises(MappingError):
            self.run_map(extraction_path, mapping_path, registry_path)

    def test_explicit_reviewed_mapping_known_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extraction_path, mapping_path, _, registry_path = self.prepare(root)
            receipt = self.run_map(extraction_path, mapping_path, registry_path)
            self.assertEqual(receipt["verdict"], "EXPLICIT_IFC_ENVIRONMENTAL_MAPPING_VERIFIABLE")
            self.assertFalse(receipt["certified"])
            self.assertEqual(receipt["total_kgco2e"], 120.0)
            self.assertEqual(receipt["indicator"], "GWP-total")
            self.assertEqual(receipt["system_boundary"]["modules"], ["A1", "A2", "A3"])
            result = receipt["results"][0]
            self.assertEqual(result["quantity"]["value"], 1000.0)
            self.assertEqual(result["quantity"]["unit_identity"], "kg")
            self.assertFalse(result["quantity"]["numerical_conversion_applied"])
            self.assertEqual(result["target"]["source_record_id"], "RX-FICT-CONCRETE-A1A3")
            self.assertEqual(len(result["target"]["source_record_sha256"]), 64)
            self.assertEqual(len(receipt["mapping_artifact"]["file_sha256"]), 64)
            self.assertEqual(len(receipt["ifc_extraction"]["file_sha256"]), 64)

    def test_source_ifc_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extraction_path, mapping_path, mapping, registry_path = self.prepare(root)
            mapping["mappings"][0]["source_ifc"]["sha256"] = "0" * 64
            self.write_json(mapping_path, mapping)
            self.assert_mapping_error(extraction_path, mapping_path, registry_path)

    def test_element_identity_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extraction_path, mapping_path, mapping, registry_path = self.prepare(root)
            mapping["mappings"][0]["element"]["step_id"] += 1
            self.write_json(mapping_path, mapping)
            self.assert_mapping_error(extraction_path, mapping_path, registry_path)

    def test_material_identity_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extraction_path, mapping_path, mapping, registry_path = self.prepare(root)
            mapping["mappings"][0]["material"]["declared_name"] = "Concrete (guessed)"
            self.write_json(mapping_path, mapping)
            self.assert_mapping_error(extraction_path, mapping_path, registry_path)

    def test_quantity_value_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extraction_path, mapping_path, mapping, registry_path = self.prepare(root)
            mapping["mappings"][0]["quantity"]["value"] = 999.0
            self.write_json(mapping_path, mapping)
            self.assert_mapping_error(extraction_path, mapping_path, registry_path)

    def test_mapping_unit_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extraction_path, mapping_path, mapping, registry_path = self.prepare(root)
            mapping["mappings"][0]["quantity"]["unit"]["prefix"] = None
            self.write_json(mapping_path, mapping)
            self.assert_mapping_error(extraction_path, mapping_path, registry_path)

    def test_unsupported_ifc_unit_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extraction_path, mapping_path, _, registry_path = self.prepare(root, mass_prefix=None)
            self.assert_mapping_error(extraction_path, mapping_path, registry_path)

    def test_environmental_declared_unit_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extraction_path, mapping_path, _, registry_path = self.prepare(root)
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            next(item for item in registry if item["id"] == "RX-FICT-CONCRETE-A1A3")["declared_unit"] = "m3"
            self.write_json(registry_path, registry)
            self.assert_mapping_error(extraction_path, mapping_path, registry_path)

    def test_missing_material_name_cannot_be_inferred(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extraction_path, mapping_path, _, registry_path = self.prepare(root, material_name="")
            self.assert_mapping_error(extraction_path, mapping_path, registry_path)

    def test_duplicate_mapping_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extraction_path, mapping_path, mapping, registry_path = self.prepare(root)
            duplicate = copy.deepcopy(mapping["mappings"][0])
            duplicate["id"] = "RX-MAP-DUPLICATE"
            mapping["mappings"].append(duplicate)
            self.write_json(mapping_path, mapping)
            self.assert_mapping_error(extraction_path, mapping_path, registry_path)

    def test_conflicting_mapping_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extraction_path, mapping_path, mapping, registry_path = self.prepare(root)
            conflict = copy.deepcopy(mapping["mappings"][0])
            conflict["id"] = "RX-MAP-CONFLICT"
            conflict["target"] = {
                "material_identity_id": "reinforcing-steel",
                "source_record_id": "RX-FICT-STEEL-A1A3",
            }
            mapping["mappings"].append(conflict)
            self.write_json(mapping_path, mapping)
            self.assert_mapping_error(extraction_path, mapping_path, registry_path)

    def test_draft_mapping_is_not_authorized(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extraction_path, mapping_path, mapping, registry_path = self.prepare(root)
            mapping["mappings"][0]["review"]["state"] = "DRAFT"
            self.write_json(mapping_path, mapping)
            self.assert_mapping_error(extraction_path, mapping_path, registry_path)

    def test_unproven_source_record_hash_fails_registry_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extraction_path, mapping_path, _, registry_path = self.prepare(root)
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            concrete = next(item for item in registry if item["id"] == "RX-FICT-CONCRETE-A1A3")
            concrete["source"]["source_content_sha256"] = "f" * 64
            self.write_json(registry_path, registry)
            self.assert_mapping_error(extraction_path, mapping_path, registry_path)


if __name__ == "__main__":
    unittest.main()
