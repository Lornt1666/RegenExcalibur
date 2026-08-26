import pathlib
import tempfile
import unittest
import zipfile

from reference import digitalhub_workbook_material_spec_v33 as m


def build_xlsx(path: pathlib.Path, rows):
    shared = []
    index = {}

    def sid(value):
        if value not in index:
            index[value] = len(shared)
            shared.append(value)
        return index[value]

    row_xml = []
    for rownum, values in rows:
        cells = []
        for col, value in values.items():
            cells.append(f'<c r="{col}{rownum}" t="s"><v>{sid(value)}</v></c>')
        row_xml.append(f'<row r="{rownum}">' + ''.join(cells) + '</row>')

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Data" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="x" Target="worksheets/sheet1.xml"/>'
        '</Relationships>'
    )
    shared_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        + ''.join(f'<si><t>{v}</t></si>' for v in shared)
        + '</sst>'
    )
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData>' + ''.join(row_xml) + '</sheetData></worksheet>'
    )

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/workbook.xml", workbook_xml)
        z.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        z.writestr("xl/sharedStrings.xml", shared_xml)
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)


class V33WorkbookTests(unittest.TestCase):
    def run_case(self, rows):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "fixture.xlsx"
            build_xlsx(p, rows)
            raw = p.read_bytes()
            old_bytes, old_blob = m.EXPECTED_BYTES, m.EXPECTED_GIT_BLOB_SHA1
            try:
                m.EXPECTED_BYTES = len(raw)
                m.EXPECTED_GIT_BLOB_SHA1 = m.git_blob_sha1(raw)
                return m.build(p)
            finally:
                m.EXPECTED_BYTES, m.EXPECTED_GIT_BLOB_SHA1 = old_bytes, old_blob

    def test_candidate_bound_strength(self):
        r = self.run_case([(2, {"A": "2395272", "B": "Concrete C25/30"})])
        self.assertEqual(r["discovery_state"], m.STATE_BOUND)
        self.assertEqual(r["candidate_bound_strength_class_hits"][0]["normalized_class"], "C25/30")

    def test_strength_present_but_unbound(self):
        r = self.run_case([(2, {"A": "other", "B": "Concrete C30/37"})])
        self.assertEqual(r["discovery_state"], m.STATE_UNBOUND)
        self.assertEqual(len(r["candidate_bound_strength_class_hits"]), 0)

    def test_no_strength(self):
        r = self.run_case([(2, {"A": "2395272", "B": "Ortbeton - bewehrt"})])
        self.assertEqual(r["discovery_state"], m.STATE_ABSENT)
        self.assertEqual(r["strength_class_hits"], [])

    def test_wrong_blob_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "fixture.xlsx"
            build_xlsx(p, [(2, {"A": "2395272"})])
            old_bytes, old_blob = m.EXPECTED_BYTES, m.EXPECTED_GIT_BLOB_SHA1
            try:
                m.EXPECTED_BYTES = p.stat().st_size
                m.EXPECTED_GIT_BLOB_SHA1 = "0" * 40
                with self.assertRaises(m.DiscoveryError):
                    m.build(p)
            finally:
                m.EXPECTED_BYTES, m.EXPECTED_GIT_BLOB_SHA1 = old_bytes, old_blob


if __name__ == "__main__":
    unittest.main()
