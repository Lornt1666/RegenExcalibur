import importlib.util
from pathlib import Path
import tempfile
import unittest

IFC_AVAILABLE = importlib.util.find_spec("ifcopenshell") is not None


@unittest.skipUnless(IFC_AVAILABLE, "IfcOpenShell not installed")
class IFCExtractionV04Tests(unittest.TestCase):
    def build_model(self, path: Path, *, prefix: str | None = None, duplicate_conflict: bool = False, include_quantity: bool = True, use_layer_set: bool = False) -> None:
        import ifcopenshell
        import ifcopenshell.guid

        model = ifcopenshell.file(schema="IFC4")
        length_unit = model.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Prefix=prefix, Name="METRE")
        unit_assignment = model.create_entity("IfcUnitAssignment", Units=[length_unit])
        project = model.create_entity("IfcProject", GlobalId=ifcopenshell.guid.new(), Name="ProofGrid Project", UnitsInContext=unit_assignment)
        site = model.create_entity("IfcSite", GlobalId=ifcopenshell.guid.new(), Name="Site")
        building = model.create_entity("IfcBuilding", GlobalId=ifcopenshell.guid.new(), Name="Building")
        storey = model.create_entity("IfcBuildingStorey", GlobalId=ifcopenshell.guid.new(), Name="Level 1")
        space = model.create_entity("IfcSpace", GlobalId=ifcopenshell.guid.new(), Name="Room 101")
        model.create_entity("IfcRelAggregates", GlobalId=ifcopenshell.guid.new(), RelatingObject=project, RelatedObjects=[site])
        model.create_entity("IfcRelAggregates", GlobalId=ifcopenshell.guid.new(), RelatingObject=site, RelatedObjects=[building])
        model.create_entity("IfcRelAggregates", GlobalId=ifcopenshell.guid.new(), RelatingObject=building, RelatedObjects=[storey])
        model.create_entity("IfcRelAggregates", GlobalId=ifcopenshell.guid.new(), RelatingObject=storey, RelatedObjects=[space])

        wall = model.create_entity("IfcWall", GlobalId=ifcopenshell.guid.new(), Name="Wall A")
        model.create_entity("IfcRelContainedInSpatialStructure", GlobalId=ifcopenshell.guid.new(), RelatedElements=[wall], RelatingStructure=storey)

        if use_layer_set:
            gypsum = model.create_entity("IfcMaterial", Name="Gypsum Board")
            insulation = model.create_entity("IfcMaterial", Name="Insulation")
            layer1 = model.create_entity("IfcMaterialLayer", Material=gypsum, LayerThickness=0.0127)
            layer2 = model.create_entity("IfcMaterialLayer", Material=insulation, LayerThickness=0.089)
            relating_material = model.create_entity("IfcMaterialLayerSet", MaterialLayers=[layer1, layer2], LayerSetName="Wall Layers")
        else:
            relating_material = model.create_entity("IfcMaterial", Name="Concrete")
        model.create_entity("IfcRelAssociatesMaterial", GlobalId=ifcopenshell.guid.new(), RelatedObjects=[wall], RelatingMaterial=relating_material)

        if include_quantity:
            quantity_value = 3500.0 if prefix == "MILLI" else 3.5
            q1 = model.create_entity("IfcQuantityLength", Name="Length", LengthValue=quantity_value)
            qset1 = model.create_entity("IfcElementQuantity", GlobalId=ifcopenshell.guid.new(), Name="Qto_WallBaseQuantities", Quantities=[q1])
            model.create_entity("IfcRelDefinesByProperties", GlobalId=ifcopenshell.guid.new(), RelatedObjects=[wall], RelatingPropertyDefinition=qset1)
            if duplicate_conflict:
                q2 = model.create_entity("IfcQuantityLength", Name="Length", LengthValue=4.0)
                qset2 = model.create_entity("IfcElementQuantity", GlobalId=ifcopenshell.guid.new(), Name="Qto_Conflicting", Quantities=[q2])
                model.create_entity("IfcRelDefinesByProperties", GlobalId=ifcopenshell.guid.new(), RelatedObjects=[wall], RelatingPropertyDefinition=qset2)

        model.write(str(path))

    def extract(self, path: Path):
        from adapters.ifc.extract import extract_ifc_declared_data
        return extract_ifc_declared_data(path)

    def wall(self, result):
        return next(element for element in result["elements"] if element["ifc_type"] == "IfcWall")

    def test_explicit_quantity_material_unit_and_hierarchy(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.ifc"
            self.build_model(path)
            result = self.extract(path)
            wall = self.wall(result)
            self.assertEqual(len(result["source_sha256"]), 64)
            self.assertTrue(result["schema"].upper().startswith("IFC4"))
            self.assertEqual(result["spatial"]["buildings"][0]["parent_global_id"], result["spatial"]["sites"][0]["global_id"])
            self.assertEqual(result["spatial"]["storeys"][0]["parent_global_id"], result["spatial"]["buildings"][0]["global_id"])
            self.assertEqual(result["spatial"]["spaces"][0]["parent_global_id"], result["spatial"]["storeys"][0]["global_id"])
            self.assertEqual(wall["materials"][0]["name"], "Concrete")
            quantity = wall["quantities"][0]
            self.assertEqual(quantity["name"], "Length")
            self.assertEqual(quantity["value"], 3.5)
            self.assertEqual(quantity["value_source"], "declared_ifc_element_quantity")
            self.assertEqual(quantity["unit"]["unit_type"], "LENGTHUNIT")
            self.assertEqual(quantity["unit"]["name"], "METRE")
            self.assertIsNone(quantity["unit"]["prefix"])
            self.assertEqual(quantity["unit"]["source"], "project_unit_context")

    def test_millimetres_are_preserved_without_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "millimetres.ifc"
            self.build_model(path, prefix="MILLI")
            quantity = self.wall(self.extract(path))["quantities"][0]
            self.assertEqual(quantity["value"], 3500.0)
            self.assertEqual(quantity["unit"]["prefix"], "MILLI")
            self.assertNotEqual(quantity["value"], 3.5)

    def test_missing_declared_quantities_emit_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "no-quantity.ifc"
            self.build_model(path, include_quantity=False)
            wall = self.wall(self.extract(path))
            self.assertEqual(wall["quantities"], [])
            self.assertIn("NO_DECLARED_QUANTITIES", wall["warnings"])

    def test_conflicting_declared_quantity_is_not_resolved_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "conflict.ifc"
            self.build_model(path, duplicate_conflict=True)
            wall = self.wall(self.extract(path))
            self.assertEqual(len(wall["quantities"]), 2)
            self.assertTrue(any(warning.startswith("CONFLICTING_DECLARED_QUANTITY:Length") for warning in wall["warnings"]))

    def test_material_layer_set_names_are_preserved_without_lca_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "layers.ifc"
            self.build_model(path, use_layer_set=True)
            wall = self.wall(self.extract(path))
            names = [item["name"] for item in wall["materials"]]
            self.assertEqual(names, ["Gypsum Board", "Insulation"])
            self.assertTrue(all(item["source_type"] == "IfcMaterialLayerSet" for item in wall["materials"]))


if __name__ == "__main__":
    unittest.main()
