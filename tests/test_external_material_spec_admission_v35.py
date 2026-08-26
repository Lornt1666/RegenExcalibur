import copy
import hashlib
import unittest

from reference import external_material_spec_admission_v35 as v35


class ExternalMaterialSpecAdmissionV35Tests(unittest.TestCase):
    def content(self):
        return b"Authoritative DigitalHub material source evidence\n"

    def source(self, decision="AUTHORITATIVE_MATERIAL_SPEC_ACQUIRED_AND_CANDIDATE_BOUND"):
        content = self.content()
        source = {
            "schema_version": "1.0",
            "record_type": "ProofGridExternalMaterialSpecificationSource",
            "acquisition": {
                "channel": "EMAIL_REPLY",
                "source_locator": "gmail:test-message",
                "message_id": "test-message",
                "thread_id": "test-thread",
                "attachment_name": None,
                "media_type": "text/plain",
                "received_at": "2026-08-26T00:00:00Z",
                "content_sha256": hashlib.sha256(content).hexdigest(),
                "content_bytes": len(content),
            },
            "candidate": {
                "ifc_source_sha256": "19d7d02d53c2b88e86890ee236297b12bbb0f7748030cd32ff6a22762e9966bb",
                "step_id": 9730,
                "global_id": "3BmeJtEDj3AQO77Os2w7Ny",
                "object_id": "2395272",
                "material_name": "Ortbeton - bewehrt",
                "binding_method": "AUTHOR_EXPLICIT_CONFIRMATION",
                "candidate_bound": True,
            },
            "source_authority": {
                "author_name": "Project Author",
                "author_email": "author@example.invalid",
                "author_organization": "DigitalHub project authority",
                "relation_to_digitalhub": "Documented project author for test fixture",
                "authority_basis": "PROJECT_AUTHOR",
            },
            "material_semantics": {
                "strength_class_explicit": True,
                "concrete_strength_class": "C25/30",
                "strength_class_source_text_sha256": hashlib.sha256(b"C25/30").hexdigest(),
                "explicit_absence_statement": False,
            },
            "decision": decision,
            "authority_boundaries": {
                "fuzzy_matching": False,
                "strength_class_inferred": False,
                "environmental_mapping_performed": False,
                "impact_calculation_performed": False,
                "scientific_suitability_confirmed": False,
                "professional_review_performed": False,
                "regulator_acceptance_implied": False,
                "certified": False,
            },
        }
        return source

    def test_candidate_bound_source_admitted(self):
        record = v35.build_admission(self.source(), self.content())
        self.assertEqual(record["candidate_resolution_state"], "AUTHORITATIVE_MATERIAL_SPEC_ACQUIRED_AND_CANDIDATE_BOUND")
        self.assertFalse(record["mapping_authorized"])
        self.assertFalse(record["impact_calculation_permitted"])

    def test_acquired_but_unbound_admitted(self):
        source = self.source("AUTHORITATIVE_MATERIAL_SPEC_ACQUIRED_BUT_NOT_CANDIDATE_BOUND")
        source["candidate"]["candidate_bound"] = False
        source["candidate"]["binding_method"] = "UNBOUND"
        record = v35.build_admission(source, self.content())
        self.assertEqual(record["candidate_resolution_state"], "AUTHORITATIVE_MATERIAL_SPEC_ACQUIRED_BUT_NOT_CANDIDATE_BOUND")

    def test_explicit_absence_admitted(self):
        source = self.source("AUTHORITATIVE_SOURCE_CONFIRMS_STRENGTH_CLASS_NOT_SPECIFIED")
        source["material_semantics"] = {
            "strength_class_explicit": False,
            "concrete_strength_class": None,
            "strength_class_source_text_sha256": hashlib.sha256(b"not specified").hexdigest(),
            "explicit_absence_statement": True,
        }
        record = v35.build_admission(source, self.content())
        self.assertEqual(record["candidate_resolution_state"], "AUTHORITATIVE_SOURCE_CONFIRMS_STRENGTH_CLASS_NOT_SPECIFIED")

    def test_content_tamper_rejected(self):
        with self.assertRaises(v35.ExternalMaterialSpecAdmissionError):
            v35.build_admission(self.source(), self.content() + b"tamper")

    def test_candidate_drift_rejected(self):
        source = self.source()
        source["candidate"]["global_id"] = "wrong"
        with self.assertRaises(v35.ExternalMaterialSpecAdmissionError):
            v35.build_admission(source, self.content())

    def test_inferred_strength_rejected(self):
        source = self.source()
        source["authority_boundaries"]["strength_class_inferred"] = True
        with self.assertRaises(v35.ExternalMaterialSpecAdmissionError):
            v35.build_admission(source, self.content())

    def test_fuzzy_mapping_rejected(self):
        source = self.source()
        source["authority_boundaries"]["fuzzy_matching"] = True
        with self.assertRaises(v35.ExternalMaterialSpecAdmissionError):
            v35.build_admission(source, self.content())

    def test_premature_mapping_rejected(self):
        source = self.source()
        source["authority_boundaries"]["environmental_mapping_performed"] = True
        with self.assertRaises(v35.ExternalMaterialSpecAdmissionError):
            v35.build_admission(source, self.content())

    def test_premature_calculation_rejected(self):
        source = self.source()
        source["authority_boundaries"]["impact_calculation_performed"] = True
        with self.assertRaises(v35.ExternalMaterialSpecAdmissionError):
            v35.build_admission(source, self.content())

    def test_certification_promotion_rejected(self):
        source = self.source()
        source["authority_boundaries"]["certified"] = True
        with self.assertRaises(v35.ExternalMaterialSpecAdmissionError):
            v35.build_admission(source, self.content())


if __name__ == "__main__":
    unittest.main()
