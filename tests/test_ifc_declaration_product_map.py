from __future__ import annotations
import copy, importlib.util, json
from pathlib import Path
import tempfile, unittest

IFC_AVAILABLE=importlib.util.find_spec('ifcopenshell') is not None
from reference import declaration_product_identity_closure as closure
from reference import ifc_declaration_product_map as mapper
from tests import test_declaration_product_identity_closure as closure_test

PRODUCT_UUID='a7432abd-0881-4977-a817-f8aaf627fb91'
PRODUCT_VERSION='00.00.001'

def write_json(path:Path,value:dict)->bytes:
    raw=(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode(); path.write_bytes(raw); return raw

def closure_parent(root:Path):
    record=closure.bind(*closure_test.case('1.3')); path=root/'closure.json'; raw=write_json(path,record)
    receipt=closure.build_receipt(record,raw); receipt_path=root/'closure-receipt.json'; write_json(receipt_path,receipt)
    return path,receipt_path,record,receipt

@unittest.skipUnless(IFC_AVAILABLE,'IfcOpenShell not installed')
class IFCDeclarationProductMappingTests(unittest.TestCase):
    def build_ifc(self,path:Path,*,mass_prefix:str|None='KILO',weight:float=1000.0)->None:
        import ifcopenshell
        model=ifcopenshell.file(schema='IFC4')
        mass=model.create_entity('IfcSIUnit',UnitType='MASSUNIT',Prefix=mass_prefix,Name='GRAM')
        units=model.create_entity('IfcUnitAssignment',Units=[mass])
        model.create_entity('IfcProject',GlobalId='0hS$wWKLjAuhSPZ5IG0yTw',Name='ProofGrid v1.5',UnitsInContext=units)
        wall=model.create_entity('IfcWall',GlobalId='1BXL7DJx51bvggyIPU2Xi5',Name='Mapped Wall')
        material=model.create_entity('IfcMaterial',Name='RX-MATERIAL-UNRELATED-TO-WOOD-PANEL')
        model.create_entity('IfcRelAssociatesMaterial',GlobalId='2BXL7DJx51bvggyIPU2Xi5',RelatedObjects=[wall],RelatingMaterial=material)
        quantity=model.create_entity('IfcQuantityWeight',Name='Mass',WeightValue=weight)
        qset=model.create_entity('IfcElementQuantity',GlobalId='3BXL7DJx51bvggyIPU2Xi5',Name='Qto_WallBaseQuantities',Quantities=[quantity])
        model.create_entity('IfcRelDefinesByProperties',GlobalId='0BXL7DJx51bvggyIPU2Xi5',RelatedObjects=[wall],RelatingPropertyDefinition=qset)
        model.write(str(path))

    def prepare(self,root:Path,**kwargs):
        from adapters.ifc.extract import extract_ifc_declared_data
        ifc=root/'fixture.ifc'; self.build_ifc(ifc,**kwargs); extraction=extract_ifc_declared_data(ifc); ep=root/'extraction.json'; write_json(ep,extraction)
        cp,crp,crec,creceipt=closure_parent(root); target=mapper.verify_closure(crec,cp.read_bytes(),creceipt)
        wall=next(e for e in extraction['elements'] if e['ifc_type']=='IfcWall'); material=wall['materials'][0]; quantity=next(q for q in wall['quantities'] if q['ifc_quantity_type']=='IfcQuantityWeight')
        mapping={'schema_version':'1.0','artifact_version':'1.5.0','mapping':{
          'id':'RX-V15-MAP-001','source_ifc':{'sha256':extraction['source_sha256'],'schema':extraction['schema']},
          'element':{'step_id':wall['step_id'],'global_id':wall['global_id'],'ifc_type':wall['ifc_type']},
          'material':{'association_step_id':material['association_step_id'],'material_step_id':material['material_step_id'],'declared_name':material['name'],'source_type':material['source_type']},
          'quantity':{'set_step_id':quantity['set_step_id'],'quantity_step_id':quantity['quantity_step_id'],'name':quantity['name'],'ifc_quantity_type':quantity['ifc_quantity_type'],'value':quantity['value'],'unit':{'unit_type':quantity['unit']['unit_type'],'name':quantity['unit']['name'],'prefix':quantity['unit']['prefix'],'source':quantity['unit']['source']}},
          'declaration':target,'review':{'state':'REVIEWED_MAPPING_DECISION','reviewer':'ProofGrid synthetic reviewer','role':'synthetic test mapping reviewer','rationale':'Exact-ID reviewed mapping; display-name similarity intentionally absent.','reference':'issue-42-synthetic-control'},
          'limitations':['synthetic mapping fixture; workflow review is not professional licensure']}}
        mp=root/'mapping.json'; write_json(mp,mapping); return ep,mp,cp,crp,mapping,extraction

    def run_map(self,p): return mapper.map_product(p[0],p[1],p[2],p[3])
    def mutate(self,p,fn):
        fn(p[4]); write_json(p[1],p[4])
        with self.assertRaises(mapper.ProductMappingError): self.run_map(p)

    def test_explicit_mapping_succeeds_despite_unrelated_names(self):
        with tempfile.TemporaryDirectory() as td:
            r=self.run_map(self.prepare(Path(td))); self.assertEqual(r['verdict'],mapper.VERDICT); self.assertEqual(r['declaration']['product_flow_uuid'],PRODUCT_UUID); self.assertEqual(r['declaration']['product_flow_version'],PRODUCT_VERSION); self.assertEqual(r['ifc']['material']['declared_name'],'RX-MATERIAL-UNRELATED-TO-WOOD-PANEL'); self.assertEqual(r['ifc']['quantity']['value'],1000.0); self.assertEqual(r['ifc']['quantity']['unit_identity'],'kg'); self.assertFalse(r['automatic_name_mapping_performed']); self.assertFalse(r['building_quantity_multiplication_performed']); self.assertFalse(r['certified'])
    def test_wrong_ifc_source_rejected(self):
        with tempfile.TemporaryDirectory() as td: self.mutate(self.prepare(Path(td)),lambda m:m['mapping']['source_ifc'].__setitem__('sha256','0'*64))
    def test_wrong_element_global_id_rejected(self):
        with tempfile.TemporaryDirectory() as td: self.mutate(self.prepare(Path(td)),lambda m:m['mapping']['element'].__setitem__('global_id','WRONG'))
    def test_wrong_material_step_id_rejected(self):
        with tempfile.TemporaryDirectory() as td: self.mutate(self.prepare(Path(td)),lambda m:m['mapping']['material'].__setitem__('material_step_id',m['mapping']['material']['material_step_id']+1))
    def test_wrong_quantity_value_rejected(self):
        with tempfile.TemporaryDirectory() as td: self.mutate(self.prepare(Path(td)),lambda m:m['mapping']['quantity'].__setitem__('value',999.0))
    def test_wrong_product_flow_version_rejected(self):
        with tempfile.TemporaryDirectory() as td: self.mutate(self.prepare(Path(td)),lambda m:m['mapping']['declaration'].__setitem__('product_flow_version','99.99.999'))
    def test_wrong_closure_digest_rejected(self):
        with tempfile.TemporaryDirectory() as td: self.mutate(self.prepare(Path(td)),lambda m:m['mapping']['declaration'].__setitem__('closure_content_sha256','a'*64))
    def test_gram_unit_rejected_no_implicit_conversion(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(mapper.ProductMappingError,'not identical to declaration'): self.run_map(self.prepare(Path(td),mass_prefix=None))
    def test_unreviewed_mapping_rejected_by_schema(self):
        with tempfile.TemporaryDirectory() as td: self.mutate(self.prepare(Path(td)),lambda m:m['mapping']['review'].__setitem__('state','DRAFT'))
    def test_tampered_closure_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=list(self.prepare(Path(td))); c=json.loads(p[2].read_text()); c['product_flow']['version']='99.99.999'; write_json(p[2],c)
            with self.assertRaisesRegex(mapper.ProductMappingError,'content SHA-256 mismatch'): self.run_map(tuple(p))

if __name__=='__main__': unittest.main()
