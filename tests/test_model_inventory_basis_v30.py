from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
import uuid

IFC_AVAILABLE = importlib.util.find_spec("ifcopenshell") is not None

from reference import model_inventory_basis_v30 as m


@unittest.skipUnless(IFC_AVAILABLE, "IfcOpenShell not installed")
class ModelInventoryBasisV30Tests(unittest.TestCase):
    def guid(self, number: int) -> str:
        import ifcopenshell.guid

        return ifcopenshell.guid.compress(uuid.UUID(int=number).hex)

    def build_model(
        self,
        path: Path,
        *,
        duplicate_wall_global_id: bool = False,
        include_opening: bool = True,
        rewrite_mass_lexical: str | None = "2.5E2",
    ) -> None:
        import ifcopenshell

        model = ifcopenshell.file(schema="IFC4")
        length_unit = model.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
        mass_unit = model.create_entity("IfcSIUnit", UnitType="MASSUNIT", Prefix="KILO", Name="GRAM")
        unit_assignment = model.create_entity("IfcUnitAssignment", Units=[length_unit, mass_unit])
        project = model.create_entity(
            "IfcProject", GlobalId=self.guid(1), Name="v3.0 Test Project", UnitsInContext=unit_assignment
        )
        site = model.create_entity("IfcSite", GlobalId=self.guid(2), Name="Site")
        building = model.create_entity("IfcBuilding", GlobalId=self.guid(3), Name="Building")
        storey = model.create_entity("IfcBuildingStorey", GlobalId=self.guid(4), Name="Level 1")
        space = model.create_entity("IfcSpace", GlobalId=self.guid(5), Name="Room 101")
        model.create_entity(
            "IfcRelAggregates", GlobalId=self.guid(10), RelatingObject=project, RelatedObjects=[site]
        )
        model.create_entity(
            "IfcRelAggregates", GlobalId=self.guid(11), RelatingObject=site, RelatedObjects=[building]
        )
        model.create_entity(
            "IfcRelAggregates", GlobalId=self.guid(12), RelatingObject=building, RelatedObjects=[storey]
        )
        model.create_entity(
            "IfcRelAggregates", GlobalId=self.guid(13), RelatingObject=storey, RelatedObjects=[space]
        )

        wall_a = model.create_entity("IfcWall", GlobalId=self.guid(20), Name="Wall A")
        wall_b = model.create_entity(
            "IfcWall",
            GlobalId=self.guid(20) if duplicate_wall_global_id else self.guid(21),
            Name="Wall B",
        )
        model.create_entity(
            "IfcRelContainedInSpatialStructure",
            GlobalId=self.guid(30),
            RelatedElements=[wall_a, wall_b],
            RelatingStructure=storey,
        )
        material = model.create_entity("IfcMaterial", Name="Mass Control Material")
        model.create_entity(
            "IfcRelAssociatesMaterial",
            GlobalId=self.guid(31),
            RelatedObjects=[wall_a],
            RelatingMaterial=material,
        )
        quantity = model.create_entity("IfcQuantityWeight", Name="Mass", WeightValue=250.0)
        qset = model.create_entity(
            "IfcElementQuantity", GlobalId=self.guid(32), Name="Qto_WallBaseQuantities", Quantities=[quantity]
        )
        model.create_entity(
            "IfcRelDefinesByProperties",
            GlobalId=self.guid(33),
            RelatedObjects=[wall_a],
            RelatingPropertyDefinition=qset,
        )
        if include_opening:
            opening = model.create_entity("IfcOpeningElement", GlobalId=self.guid(22), Name="Opening A")
            model.create_entity(
                "IfcRelContainedInSpatialStructure",
                GlobalId=self.guid(34),
                RelatedElements=[opening],
                RelatingStructure=storey,
            )

        model.write(str(path))
        if rewrite_mass_lexical is not None:
            text = path.read_text(encoding="utf-8")
            pattern = re.compile(r"(IFCQUANTITYWEIGHT\('Mass',\$,[^,]*,)[^,]+", re.IGNORECASE)
            updated, count = pattern.subn(rf"\g<1>{rewrite_mass_lexical}", text, count=1)
            self.assertEqual(count, 1, "expected one IfcQuantityWeight lexical rewrite")
            path.write_text(updated, encoding="utf-8", newline="\n")

    def policy(self, tmp: Path) -> Path:
        src = m.POLICY_SCHEMA_PATH
        dst = tmp / "inventory-policy.json"
        shutil.copyfile(src, dst)
        return dst

    def test_synthetic_inventory_is_deterministic_path_independent_and_ineligible(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            first = tmp / "first.ifc"
            second = tmp / "renamed-copy.ifc"
            self.build_model(first)
            shutil.copyfile(first, second)
            policy = self.policy(tmp)
            a_admission, a_basis, a_receipt = m.build_records(
                first, policy, synthetic_input=True
            )
            b_admission, b_basis, b_receipt = m.build_records(
                second, policy, synthetic_input=True
            )
            self.assertEqual(a_admission, b_admission)
            self.assertEqual(a_basis, b_basis)
            self.assertEqual(a_receipt, b_receipt)
            self.assertEqual(a_basis["verdict"], "MODEL_INVENTORY_BASIS_TEST_ONLY")
            self.assertFalse(a_basis["acceptance_eligible"])
            self.assertTrue(a_basis["zero_silent_drops"])
            self.assertEqual(
                a_basis["inventory_summary"]["enumerated_count"],
                a_basis["inventory_summary"]["classified_count"],
            )
            self.assertIsNone(a_basis["authorization_manifest_sha256"])

    def test_exact_step_mass_lexical_is_authority(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            path = tmp / "lexical.ifc"
            self.build_model(path, rewrite_mass_lexical="2.5E2")
            _, basis, _ = m.build_records(path, self.policy(tmp), synthetic_input=True)
            wall = next(entry for entry in basis["entries"] if entry["name"] == "Wall A")
            quantity = wall["declared_quantities"][0]
            self.assertEqual(quantity["value_lexical"], "2.5E2")
            self.assertEqual(quantity["value_decimal"], "250")
            self.assertEqual(quantity["parser_numeric_value"], 250.0)
            self.assertTrue(quantity["source_token_is_authority"])
            self.assertFalse(quantity["parser_numeric_value_is_authority"])
            self.assertEqual(quantity["unit"]["unit_type"], "MASSUNIT")
            self.assertEqual(quantity["unit"]["prefix"], "KILO")

    def test_policy_classifies_every_enumerated_object_exactly_once(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            path = tmp / "classified.ifc"
            self.build_model(path)
            _, basis, _ = m.build_records(path, self.policy(tmp), synthetic_input=True)
            states = {entry["name"]: entry["classification_state"] for entry in basis["entries"]}
            self.assertEqual(states["Wall A"], "EVIDENCE_REQUIRED")
            self.assertEqual(states["Wall B"], "EVIDENCE_REQUIRED")
            self.assertEqual(states["Opening A"], "EVIDENCE_NOT_APPLICABLE")
            self.assertEqual(states["Room 101"], "EVIDENCE_NOT_APPLICABLE")
            summary = basis["inventory_summary"]
            self.assertEqual(summary["enumerated_count"], len(basis["entries"]))
            self.assertEqual(
                summary["evidence_required_count"]
                + summary["evidence_not_applicable_count"]
                + summary["out_of_declared_scope_count"],
                summary["enumerated_count"],
            )

    def test_duplicate_non_empty_global_id_fails_closed(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            path = tmp / "duplicate-global-id.ifc"
            self.build_model(path, duplicate_wall_global_id=True)
            with self.assertRaisesRegex(m.ModelInventoryError, "duplicate non-empty GlobalId"):
                m.build_records(path, self.policy(tmp), synthetic_input=True)

    def test_real_mode_requires_authorization_manifest(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            path = tmp / "needs-auth.ifc"
            self.build_model(path)
            with self.assertRaisesRegex(m.ModelInventoryError, "requires --authorization-manifest"):
                m.build_records(path, self.policy(tmp), synthetic_input=False)

    def test_wrong_source_authorization_fails_closed(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            path = tmp / "wrong-auth.ifc"
            self.build_model(path)
            auth = {
                "schema_version": "3.0",
                "record_type": "ProofGridRealIFCAuthorization",
                "authorization_type": "USER_AUTHORIZED_REAL_IFC",
                "source_sha256": "0" * 64,
                "source_kind": "REAL_IFC_MODEL_REVISION",
                "authorized_scope": "PROOFGRID_V30_MODEL_INVENTORY_BASIS",
                "proofgrid_v30_authorized": True,
                "synthetic": False,
                "authority_actor": "unit-test-negative-only",
                "limitations": ["Negative fixture: deliberately does not authorize these IFC bytes."],
            }
            auth_path = tmp / "authorization.json"
            auth_path.write_text(json.dumps(auth, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(m.ModelInventoryError, "authorization/source SHA-256 mismatch"):
                m.build_records(
                    path,
                    self.policy(tmp),
                    synthetic_input=False,
                    authorization_manifest=auth_path,
                )

    def test_policy_whole_building_promotion_fails_closed(self):
        policy = json.loads(m.POLICY_SCHEMA_PATH.read_text(encoding="utf-8"))
        policy["acceptance_boundary"]["whole_building_lca_claimed"] = True
        with self.assertRaisesRegex(m.ModelInventoryError, "whole-building promotion rejected"):
            m._validate_policy(policy)

    def test_step_scanner_rejects_duplicate_and_unterminated_records(self):
        with self.assertRaisesRegex(m.ModelInventoryError, "duplicate STEP record id"):
            m._scan_step_records(b"#1=IFCWALL('A');\n#1=IFCWALL('B');\n", 10)
        with self.assertRaisesRegex(m.ModelInventoryError, "unterminated STEP record"):
            m._scan_step_records(b"#1=IFCWALL('A')\n", 10)

    def test_decimal_lexical_normalization_supports_exponent_and_typed_measure(self):
        self.assertEqual(m._canonical_decimal_from_lexical("2.5E2"), "250")
        self.assertEqual(m._canonical_decimal_from_lexical("IFCMASSMEASURE(250.)"), "250")
        self.assertEqual(m._canonical_decimal_from_lexical("-0.000"), "0")


if __name__ == "__main__":
    unittest.main()
