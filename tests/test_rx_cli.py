import importlib.util
import json
import hashlib
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "reference" / "rx_cli.py"
spec = importlib.util.spec_from_file_location("rx_cli", MODULE_PATH)
rx_cli = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(rx_cli)


class ProofGridV03Tests(unittest.TestCase):
    def fixture(self, root: Path) -> Path:
        project_dir = root / "project"
        source_dir = project_dir / "sources"
        source_dir.mkdir(parents=True)
        source_text = "Synthetic ProofGrid factor source for deterministic tests.\n"
        source_path = source_dir / "factors.txt"
        source_path.write_text(source_text, encoding="utf-8")
        source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
        (project_dir / "project.json").write_text(
            json.dumps({"id": "demo", "name": "Demo", "jurisdiction": "Alberta, Canada", "building_type": "test"}),
            encoding="utf-8",
        )
        (project_dir / "materials.json").write_text(
            json.dumps([
                {"id": "a", "material_identity_id": "mat-a", "name": "A", "quantity": 10, "unit": "kg", "source_record_id": "SRC-A"},
                {"id": "b", "material_identity_id": "mat-b", "name": "B", "quantity": 4, "unit": "kg", "source_record_id": "SRC-B"},
            ]), encoding="utf-8"
        )
        registry = [
            self.source_record("SRC-A", "mat-a", 2.5, source_hash),
            self.source_record("SRC-B", "mat-b", 1.25, source_hash),
        ]
        (project_dir / "lca-sources.json").write_text(json.dumps(registry), encoding="utf-8")
        return project_dir

    def source_record(self, record_id: str, material_id: str, value: float, source_hash: str, *, unit: str = "kg", modules: list[str] | None = None, document_id: str | None = None) -> dict:
        return {
            "id": record_id,
            "material": {"id": material_id, "name": material_id},
            "declared_unit": unit,
            "reference_quantity": 1,
            "indicator": {"name": "GWP-total", "value": value, "unit": "kgCO2e"},
            "system_boundary": {"modules": modules or ["A1", "A2", "A3"]},
            "source": {
                "publisher": "ProofGrid test",
                "document_id": document_id or f"DOC-{record_id}",
                "version": "1",
                "verification": {"state": "UNVERIFIED", "evidence_reference": None},
                "reference": "sources/factors.txt",
                "source_content_sha256": source_hash,
                "redistribution_status": "SYNTHETIC_OPEN",
            },
            "synthetic": True,
            "limitations": ["test only"],
            "data_quality_flags": ["SYNTHETIC_TEST_DATA"],
        }

    def test_calculation_is_deterministic_and_registry_provenanced(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = self.fixture(Path(tmp))
            first, first_receipt = rx_cli.build_evidence(project_dir)
            second, second_receipt = rx_cli.build_evidence(project_dir)
            self.assertEqual(first["measurement"]["value"], 30.0)
            self.assertEqual(first["integrity"]["content_sha256"], second["integrity"]["content_sha256"])
            self.assertEqual(first_receipt["receipt_sha256"], second_receipt["receipt_sha256"])
            self.assertEqual(first_receipt["lca_registry"]["source_record_ids"], ["SRC-A", "SRC-B"])
            self.assertEqual(first_receipt["lca_registry"]["system_boundary"]["modules"], ["A1", "A2", "A3"])
            self.assertFalse(first_receipt["certified"])

    def test_artifacts_are_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = self.fixture(root)
            output_dir = root / "out"
            result = rx_cli.write_outputs(project_dir, output_dir)
            for name in ("evidence.json", "graph.jsonld", "receipt.json", "report.html"):
                self.assertTrue((output_dir / name).exists(), name)
            self.assertEqual(result["total_kgco2e"], 30.0)

    def test_unit_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = self.fixture(Path(tmp))
            materials = json.loads((project_dir / "materials.json").read_text())
            materials[0]["unit"] = "m3"
            (project_dir / "materials.json").write_text(json.dumps(materials))
            with self.assertRaisesRegex(rx_cli.VerificationError, "implicit unit conversion"):
                rx_cli.build_evidence(project_dir)

    def test_mixed_boundaries_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = self.fixture(Path(tmp))
            registry = json.loads((project_dir / "lca-sources.json").read_text())
            registry[1]["system_boundary"]["modules"] = ["A1", "A2", "A3", "A4"]
            (project_dir / "lca-sources.json").write_text(json.dumps(registry))
            with self.assertRaisesRegex(rx_cli.VerificationError, "incompatible lifecycle"):
                rx_cli.build_evidence(project_dir)

    def test_source_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = self.fixture(Path(tmp))
            (project_dir / "sources" / "factors.txt").write_text("tampered\n")
            with self.assertRaisesRegex(rx_cli.VerificationError, "source hash mismatch"):
                rx_cli.build_evidence(project_dir)

    def test_missing_source_record_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = self.fixture(Path(tmp))
            materials = json.loads((project_dir / "materials.json").read_text())
            materials[0]["source_record_id"] = "MISSING"
            (project_dir / "materials.json").write_text(json.dumps(materials))
            with self.assertRaisesRegex(rx_cli.VerificationError, "missing LCA source record"):
                rx_cli.build_evidence(project_dir)

    def test_duplicate_record_id_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = self.fixture(Path(tmp))
            registry = json.loads((project_dir / "lca-sources.json").read_text())
            registry.append(dict(registry[0]))
            (project_dir / "lca-sources.json").write_text(json.dumps(registry))
            with self.assertRaisesRegex(rx_cli.VerificationError, "duplicate LCA source record id"):
                rx_cli.build_evidence(project_dir)

    def test_conflicting_same_source_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = self.fixture(Path(tmp))
            registry = json.loads((project_dir / "lca-sources.json").read_text())
            conflict = json.loads(json.dumps(registry[0]))
            conflict["id"] = "SRC-A-CONFLICT"
            conflict["indicator"]["value"] = 9.9
            registry.append(conflict)
            (project_dir / "lca-sources.json").write_text(json.dumps(registry))
            with self.assertRaisesRegex(rx_cli.VerificationError, "conflicting LCA source records"):
                rx_cli.build_evidence(project_dir)

    def test_project_schema_rejects_unknown_property(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = self.fixture(Path(tmp))
            project = json.loads((project_dir / "project.json").read_text())
            project["unexpected"] = True
            (project_dir / "project.json").write_text(json.dumps(project))
            with self.assertRaisesRegex(rx_cli.VerificationError, "project.json failed schema validation"):
                rx_cli.build_evidence(project_dir)

    def test_material_schema_rejects_inline_factor(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = self.fixture(Path(tmp))
            materials = json.loads((project_dir / "materials.json").read_text())
            materials[0]["gwp_kgco2e_per_unit"] = 1
            (project_dir / "materials.json").write_text(json.dumps(materials))
            with self.assertRaisesRegex(rx_cli.VerificationError, "materials.json failed schema validation"):
                rx_cli.build_evidence(project_dir)

    @unittest.skipUnless(importlib.util.find_spec("ifcopenshell"), "IfcOpenShell not installed")
    def test_ifc_adapter_parses_real_ifc_model(self):
        import ifcopenshell
        import ifcopenshell.guid
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ifc_path = root / "fixture.ifc"
            model = ifcopenshell.file(schema="IFC4")
            model.create_entity("IfcProject", GlobalId=ifcopenshell.guid.new(), Name="ProofGrid IFC Fixture")
            model.create_entity("IfcBuilding", GlobalId=ifcopenshell.guid.new(), Name="Fixture Building")
            model.write(str(ifc_path))
            summary = rx_cli.inspect_ifc(ifc_path)
            self.assertTrue(summary["schema"].upper().startswith("IFC4"))
            self.assertEqual(summary["counts"]["projects"], 1)
            self.assertEqual(summary["counts"]["buildings"], 1)
            self.assertEqual(summary["buildings"][0]["name"], "Fixture Building")


if __name__ == "__main__":
    unittest.main()
