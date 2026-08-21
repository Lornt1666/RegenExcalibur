import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "reference" / "rx_cli.py"
spec = importlib.util.spec_from_file_location("rx_cli", MODULE_PATH)
rx_cli = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(rx_cli)


class ProofGridTests(unittest.TestCase):
    def fixture(self, root: Path) -> Path:
        project_dir = root / "project"
        project_dir.mkdir()
        (project_dir / "project.json").write_text(
            json.dumps(
                {
                    "id": "demo",
                    "name": "Demo",
                    "jurisdiction": "Alberta, Canada",
                    "building_type": "test",
                }
            ),
            encoding="utf-8",
        )
        (project_dir / "materials.json").write_text(
            json.dumps(
                [
                    {
                        "id": "a",
                        "name": "A",
                        "quantity": 10,
                        "unit": "kg",
                        "gwp_kgco2e_per_unit": 2.5,
                        "factor_source": "test",
                    },
                    {
                        "id": "b",
                        "name": "B",
                        "quantity": 4,
                        "unit": "kg",
                        "gwp_kgco2e_per_unit": 1.25,
                        "factor_source": "test",
                    },
                ]
            ),
            encoding="utf-8",
        )
        return project_dir

    def test_calculation_is_deterministic_and_schema_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = self.fixture(Path(tmp))
            first, first_receipt = rx_cli.build_evidence(project_dir)
            second, second_receipt = rx_cli.build_evidence(project_dir)

            self.assertEqual(first["measurement"]["value"], 30.0)
            self.assertEqual(first["integrity"]["content_sha256"], second["integrity"]["content_sha256"])
            self.assertEqual(first_receipt["receipt_sha256"], second_receipt["receipt_sha256"])
            self.assertEqual(first["review"]["state"], "CALCULATED")
            self.assertFalse(first_receipt["certified"])
            self.assertEqual(first_receipt["verdict"], "VERIFIABLE")
            self.assertEqual(first_receipt["schema_validation"]["draft"], "2020-12")

    def test_artifacts_are_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = self.fixture(root)
            output_dir = root / "out"
            result = rx_cli.write_outputs(project_dir, output_dir)

            for name in ("evidence.json", "graph.jsonld", "receipt.json", "report.html"):
                self.assertTrue((output_dir / name).exists(), name)
            self.assertEqual(result["total_kgco2e"], 30.0)

    def test_project_schema_rejects_unknown_property(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = self.fixture(Path(tmp))
            project_path = project_dir / "project.json"
            project = json.loads(project_path.read_text(encoding="utf-8"))
            project["invented_field"] = "must fail closed"
            project_path.write_text(json.dumps(project), encoding="utf-8")

            with self.assertRaisesRegex(rx_cli.VerificationError, "project.json failed schema validation"):
                rx_cli.build_evidence(project_dir)

    def test_material_schema_rejects_negative_quantity(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = self.fixture(Path(tmp))
            materials_path = project_dir / "materials.json"
            materials = json.loads(materials_path.read_text(encoding="utf-8"))
            materials[0]["quantity"] = -1
            materials_path.write_text(json.dumps(materials), encoding="utf-8")

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
            model.create_entity(
                "IfcProject",
                GlobalId=ifcopenshell.guid.new(),
                Name="ProofGrid IFC Fixture",
            )
            model.create_entity(
                "IfcBuilding",
                GlobalId=ifcopenshell.guid.new(),
                Name="Fixture Building",
            )
            model.write(str(ifc_path))

            summary = rx_cli.inspect_ifc(ifc_path)
            self.assertTrue(summary["schema"].upper().startswith("IFC4"))
            self.assertEqual(summary["counts"]["projects"], 1)
            self.assertEqual(summary["counts"]["buildings"], 1)
            self.assertEqual(summary["buildings"][0]["name"], "Fixture Building")


if __name__ == "__main__":
    unittest.main()
