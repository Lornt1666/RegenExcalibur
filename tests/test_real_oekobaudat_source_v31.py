import unittest
from reference import real_oekobaudat_source_v31 as m


class RealOekobaudatSourceV31Tests(unittest.TestCase):
    def test_canonical_decimal(self):
        self.assertEqual(m.canonical_decimal("181", "x"), "181")
        with self.assertRaises(m.V31Error):
            m.canonical_decimal("181.0", "x")

    def test_exact_validator_stack(self):
        self.assertEqual(m.PROFILE_COORD, "com.okworx.ilcd.validation.profiles:EPD-1.2-OEKOBAUDAT:3.8.0")
        self.assertEqual(m.VALIDATOR_COORD, "com.okworx.ilcd.validation:ilcd-validation:2.12.2")
        self.assertEqual(m.PROFILE_JAR_SHA, "96ee05b9cf5172a344df3ea844aa8d94060eae4e4e8188f72e46441a3d61921e")
        self.assertEqual(m.VALIDATOR_JAR_SHA, "55427919601b5deceee99b34fbbbaf8f00cbcf0aca1fdb1eb493c31f473e077b")

    def test_profile_errors_rejected(self):
        p={
            "profile_name":"EPD 1.2 ÖKOBAUDAT",
            "profile_version":"3.8.0",
            "profile_coordinates":m.PROFILE_COORD,
            "is_positive":False,
            "error_count":1,
            "warning_count":0,
            "event_count":1,
            "events":[],
        }
        with self.assertRaises(m.V31Error):
            m.verify_profile(p, "0"*64)

    def test_wrong_profile_coordinate_rejected(self):
        p={
            "profile_name":"EPD 1.2 ÖKOBAUDAT",
            "profile_version":"3.8.0",
            "profile_coordinates":"wrong",
            "is_positive":True,
            "error_count":0,
            "warning_count":0,
            "event_count":0,
            "events":[],
        }
        with self.assertRaises(m.V31Error):
            m.verify_profile(p, "0"*64)

    def test_fixed_source_identity(self):
        self.assertEqual(m.UUID, "8347f9a7-f4ec-4a36-a266-a0281f5fd16d")
        self.assertEqual(m.VERSION, "00.02.000")
        self.assertEqual(m.PROCESS_SHA, "18951c19002314adb6213d05783f8075553102a1bc57e22950d941a4804e445d")
        self.assertEqual(m.PACKAGE_SHA, "c858c2712243684b094d843bd688b5ee062b0d8005f2cd2cef93bd7e4902e3a3")

    def test_admission_does_not_imply_mapping_or_certification(self):
        self.assertEqual(m.VERDICT, "REAL_ENVIRONMENTAL_SOURCE_ADMISSION_VERIFIABLE")


if __name__ == "__main__":
    unittest.main()
