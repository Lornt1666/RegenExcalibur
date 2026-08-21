#!/usr/bin/env bash
set -euo pipefail

ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
OUT="/tmp/proofgrid-v08-final"
INDATA_V12="$ROOT/.proofgrid-upstream/indata-v12"
INDATA_MASTER="$ROOT/.proofgrid-upstream/indata-master"
mkdir -p "$OUT"

EXPECTED_INDATA_V12="b7233bd2dd5435a6b5973505ffa212cd03d23468"
EXPECTED_MASTER="32117b6a70d6c486344247a429449755a2c7eab4"
EXPECTED_LIB_SHA="55427919601b5deceee99b34fbbbaf8f00cbcf0aca1fdb1eb493c31f473e077b"
EXPECTED_PROFILE_SHA="96ee05b9cf5172a344df3ea844aa8d94060eae4e4e8188f72e46441a3d61921e"
EXPECTED_PROFILE_POM_SHA="0188dfb7ee16feb4c20c58003f419db7e5007382be7794d47cfd56d67a39047a"
EXPECTED_GENERIC_SHA="31402bb2746ddb9d2ab4ce40dd5d3e848ab701d1f4da00f2da004f15c7e1cc25"
EXPECTED_EN15804_SHA="a05ac55df8f567985da8c95e30ff6579761d336e0f23087aa73fefb4d9a2b147"
EXPECTED_BUILDER_RECEIPT="9b89fc710783e91a935914093ea4581535a9e9aa737a9deb3465ce156a659c17"
EXPECTED_PACKAGE_MANIFEST="fa5c531448117f9abf91b08d14d09ec7628cd2639b8f3f0cfef04e42008805e9"
EXPECTED_WARNING_FINGERPRINT="d5ef7c90e922282350d20ed647f3a2b30be77a205cbc23622a95021b1b410cd6"

# 1. Immutable public upstreams.
test "$(git -C "$INDATA_V12" rev-parse HEAD)" = "$EXPECTED_INDATA_V12"
test "$(git -C "$INDATA_MASTER" rev-parse HEAD)" = "$EXPECTED_MASTER"
grep -q 'Apache License' "$INDATA_V12/LICENSE"
grep -q 'Version 2.0' "$INDATA_V12/LICENSE"
grep -q 'Apache License' "$INDATA_MASTER/LICENSE"
grep -q 'Version 2.0' "$INDATA_MASTER/LICENSE"

# 2. Exact official validation library/profile graph.
cat > "$OUT/pom.xml" <<'POM'
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>proofgrid.v08</groupId>
  <artifactId>final-oekobaudat-profile-gate</artifactId>
  <version>1.0.0</version>
  <dependencies>
    <dependency>
      <groupId>com.okworx.ilcd.validation</groupId>
      <artifactId>ilcd-validation</artifactId>
      <version>2.12.2</version>
    </dependency>
    <dependency>
      <groupId>com.okworx.ilcd.validation.profiles</groupId>
      <artifactId>EPD-1.2-OEKOBAUDAT</artifactId>
      <version>3.8.0</version>
    </dependency>
  </dependencies>
</project>
POM

mvn -B -ntp -f "$OUT/pom.xml" dependency:go-offline
mvn -B -ntp -f "$OUT/pom.xml" dependency:build-classpath \
  -Dmdep.outputFile="$OUT/classpath.txt" -Dmdep.pathSeparator=:

LIB="$HOME/.m2/repository/com/okworx/ilcd/validation/ilcd-validation/2.12.2/ilcd-validation-2.12.2.jar"
PROFILE_DIR="$HOME/.m2/repository/com/okworx/ilcd/validation/profiles/EPD-1.2-OEKOBAUDAT/3.8.0"
PROFILE="$PROFILE_DIR/EPD-1.2-OEKOBAUDAT-3.8.0.jar"
PROFILE_POM="$PROFILE_DIR/EPD-1.2-OEKOBAUDAT-3.8.0.pom"

test "$(sha256sum "$LIB" | awk '{print $1}')" = "$EXPECTED_LIB_SHA"
test "$(sha256sum "$PROFILE" | awk '{print $1}')" = "$EXPECTED_PROFILE_SHA"
test "$(sha256sum "$PROFILE_POM" | awk '{print $1}')" = "$EXPECTED_PROFILE_POM_SHA"
test "$(unzip -p "$PROFILE" includes/EPD-1.2-Generic.jar | sha256sum | awk '{print $1}')" = "$EXPECTED_GENERIC_SHA"
test "$(unzip -p "$PROFILE" includes/EPD-1.2-EN15804.jar | sha256sum | awk '{print $1}')" = "$EXPECTED_EN15804_SHA"
printf '%s\n' "$PROFILE" > "$OUT/profile-path.txt"
java -version 2>&1 | tee "$OUT/java-version.txt"
mvn -version 2>&1 | tee "$OUT/maven-version.txt"

CP=$(cat "$OUT/classpath.txt")
mkdir -p "$OUT/classes"
javac -encoding UTF-8 -cp "$CP" -d "$OUT/classes" \
  "$ROOT/conformance/oekobaudat-v12/OekobaudatProfileProbe.java"

# 3. Deterministic synthetic fixture from pinned public data + exact profile catalogue.
python "$ROOT/conformance/oekobaudat-v12/build_synthetic_fixture.py" \
  --sample-root "$INDATA_V12/sample_data" \
  --master-root "$INDATA_MASTER" \
  --profile-jar "$PROFILE" \
  --output-root "$OUT/package"
cp "$OUT/package/fixture-build-receipt.json" "$OUT/fixture-build-receipt.json"

python - <<'PY'
import hashlib, json
p='/tmp/proofgrid-v08-final/fixture-build-receipt.json'
d=json.load(open(p))
assert d['receipt_sha256'] == '9b89fc710783e91a935914093ea4581535a9e9aa737a9deb3465ce156a659c17', d['receipt_sha256']
raw=json.dumps(d['output_files'],sort_keys=True,separators=(',',':')).encode()
manifest=hashlib.sha256(raw).hexdigest()
assert manifest == 'fa5c531448117f9abf91b08d14d09ec7628cd2639b8f3f0cfef04e42008805e9', manifest
assert len(d['closure']['copied_digital_files']) == 3
assert d['process_changes']['classification_name'] == 'oekobau.dat'
assert d['process_changes']['synthetic_process_uuid'] == '6b47f4cf-0bc4-4e0d-b9fd-9d5f845d1de0'
print('builder_receipt_sha256=', d['receipt_sha256'])
print('package_manifest_sha256=', manifest)
PY

# 4. Version guard before v1.2 profile evaluation.
python "$ROOT/conformance/oekobaudat-v12/assert_v12_package.py" \
  "$OUT/package" --output "$OUT/version-guard-receipt.json"

# 5. Exact official positive profile run.
CP="$CP:$OUT/classes"
java -Djava.net.useSystemProxies=false -cp "$CP" \
  proofgrid.v08.OekobaudatProfileProbe \
  "$PROFILE" "$OUT/package" "$OUT/positive-profile-result.json" final-positive

python - <<'PY'
import hashlib, json
p='/tmp/proofgrid-v08-final/positive-profile-result.json'
d=json.load(open(p))
assert d['profile_name'] == 'EPD 1.2 ÖKOBAUDAT'
assert d['profile_version'] == '3.8.0'
assert d['profile_coordinates'] == 'com.okworx.ilcd.validation.profiles:EPD-1.2-OEKOBAUDAT:3.8.0'
assert d['is_positive'] is True
assert d['error_count'] == 0
assert d['warning_count'] == 26
assert d['event_count'] == 26
assert all(e['severity'] == 'WARNING' for e in d['events'])
rows=[{k:e.get(k) for k in ('severity','type','aspect','aspect_description','message','alt_message')} for e in d['events']]
rows=sorted(rows,key=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False))
raw=(json.dumps(rows,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()
fingerprint=hashlib.sha256(raw).hexdigest()
assert fingerprint == 'd5ef7c90e922282350d20ed647f3a2b30be77a205cbc23622a95021b1b410cd6', fingerprint
json.dump(rows,open('/tmp/proofgrid-v08-final/normalized-warning-events.json','w'),indent=2,sort_keys=True,ensure_ascii=False)
print('official_positive=true')
print('warning_count=26')
print('normalized_warning_fingerprint=', fingerprint)
PY

# 6. Profile-rule negative: remove ÖKOBAUDAT classification and require official error.
cp -a "$OUT/package" "$OUT/negative-category-package"
python - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET
PROCESS='http://lca.jrc.it/ILCD/Process'
COMMON='http://lca.jrc.it/ILCD/Common'
root=Path('/tmp/proofgrid-v08-final/negative-category-package/ILCD/processes')
files=list(root.glob('*.xml'))
assert len(files) == 1, files
path=files[0]
tree=ET.parse(path); doc=tree.getroot()
info=doc.find(f'{{{PROCESS}}}processInformation/{{{PROCESS}}}dataSetInformation/{{{PROCESS}}}classificationInformation')
assert info is not None
removed=0
for child in list(info):
    if child.tag == f'{{{COMMON}}}classification' and child.attrib.get('name') == 'oekobau.dat':
        info.remove(child); removed += 1
assert removed == 1
tree.write(path,encoding='utf-8',xml_declaration=True,short_empty_elements=True)
PY

python "$ROOT/conformance/oekobaudat-v12/assert_v12_package.py" \
  "$OUT/negative-category-package" --output "$OUT/negative-category-version-guard.json"

java -Djava.net.useSystemProxies=false -cp "$CP" \
  proofgrid.v08.OekobaudatProfileProbe \
  "$PROFILE" "$OUT/negative-category-package" \
  "$OUT/negative-category-result.json" negative-missing-oekobaudat-category

python - <<'PY'
import json
d=json.load(open('/tmp/proofgrid-v08-final/negative-category-result.json'))
assert d['is_positive'] is False
assert d['error_count'] >= 1
messages=[e['message'] for e in d['events'] if e['severity']=='ERROR']
assert any('ÖKOBAUDAT categories must be present.' in m for m in messages), messages
print('profile_negative_missing_category=PASS')
PY

# 7. Wrong-version negative: fail before v1.2 profile evaluation.
cp -a "$OUT/package" "$OUT/wrong-version-package"
python - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET
EPD='http://www.indata.network/EPD/2019'
process_dir=Path('/tmp/proofgrid-v08-final/wrong-version-package/ILCD/processes')
files=list(process_dir.glob('*.xml'))
assert len(files)==1, files
path=files[0]
tree=ET.parse(path); root=tree.getroot()
assert root.attrib.get(f'{{{EPD}}}epd-version') == '1.2'
root.attrib[f'{{{EPD}}}epd-version']='1.3'
tree.write(path,encoding='utf-8',xml_declaration=True,short_empty_elements=True)
PY

if python "$ROOT/conformance/oekobaudat-v12/assert_v12_package.py" \
  "$OUT/wrong-version-package" --output "$OUT/wrong-version-should-not-exist.json"; then
  echo 'v1.3 mutation unexpectedly passed v1.2 guard' >&2
  exit 1
fi
echo 'wrong_version_rejected_before_profile=PASS'

# 8. Final bounded receipt. All event fingerprints exclude path-bearing references.
python - <<'PY'
from pathlib import Path
import collections, hashlib, json

root=Path('/tmp/proofgrid-v08-final')
build=json.load(open(root/'fixture-build-receipt.json'))
guard=json.load(open(root/'version-guard-receipt.json'))
pos=json.load(open(root/'positive-profile-result.json'))
neg=json.load(open(root/'negative-category-result.json'))

stable_fields=('severity','type','aspect','aspect_description','message','alt_message')
def normalized(events):
    rows=[{k:e.get(k) for k in stable_fields} for e in events]
    return sorted(rows,key=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False))
def fingerprint(events):
    rows=normalized(events)
    raw=(json.dumps(rows,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()
    return hashlib.sha256(raw).hexdigest()

warning_groups=collections.Counter((e['aspect'],e['message']) for e in pos['events'] if e['severity']=='WARNING')
package_manifest=hashlib.sha256(json.dumps(build['output_files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
positive_fingerprint=fingerprint(pos['events'])
negative_fingerprint=fingerprint(neg['events'])

process_file=next(x for x in build['output_files'] if x['path'].startswith('ILCD/processes/') and x['path'].endswith('.xml'))
operator_file=next(x for x in build['output_files'] if x['path']=='ILCD/contacts/d111dbec-b024-4be5-86c5-752d6eb2cf95.xml')

report={
  'gate':'ProofGrid v0.8 ÖKOBAUDAT ILCD+EPD v1.2 profile 3.8.0 compatibility',
  'verdict':'OEKOBAUDAT_ILCD_EPD_V12_PROFILE_3_8_0_COMPATIBLE',
  'certified':False,
  'format_version':'ILCD+EPD v1.2',
  'profile':{
    'coordinate':'com.okworx.ilcd.validation.profiles:EPD-1.2-OEKOBAUDAT:3.8.0',
    'version':'3.8.0',
    'publication_date':'2026-04-17',
    'jar_sha256':'96ee05b9cf5172a344df3ea844aa8d94060eae4e4e8188f72e46441a3d61921e',
    'pom_sha256':'0188dfb7ee16feb4c20c58003f419db7e5007382be7794d47cfd56d67a39047a',
    'generic_include_sha256':'31402bb2746ddb9d2ab4ce40dd5d3e848ab701d1f4da00f2da004f15c7e1cc25',
    'en15804_include_sha256':'a05ac55df8f567985da8c95e30ff6579761d336e0f23087aa73fefb4d9a2b147',
  },
  'validator':{
    'coordinate':'com.okworx.ilcd.validation:ilcd-validation:2.12.2',
    'jar_sha256':'55427919601b5deceee99b34fbbbaf8f00cbcf0aca1fdb1eb493c31f473e077b',
    'api_research_sources_sha256':'c2a275fea7f0a556914b4683e68c32e755fdbe9cbbc56a20fffd3174f4b4a409',
  },
  'public_upstreams':{
    'indata_v12_commit':'b7233bd2dd5435a6b5973505ffa212cd03d23468',
    'indata_master_commit':'32117b6a70d6c486344247a429449755a2c7eab4',
  },
  'research_evidence':{
    'profile_research_receipt_sha256':'94206109b8c27168649216a6ae2b1d12ac6b92e0e950618e9197444de88710ad',
    'library_research_receipt_sha256':'78d296dad1e00747b75bcaeaf5c6eb5611354fd960c98416142fcaedee054f17',
    'profile_source_tag_access':'SCM_TAG_NOT_ANONYMOUSLY_FETCHABLE_AT_RESEARCH_TIME',
  },
  'fixture':{
    'builder_receipt_sha256':build['receipt_sha256'],
    'package_file_manifest_sha256':package_manifest,
    'synthetic_process_uuid':build['process_changes']['synthetic_process_uuid'],
    'synthetic_process_sha256':process_file['sha256'],
    'synthetic_operator_uuid':build['operator_contact']['uuid'],
    'synthetic_operator_sha256':operator_file['sha256'],
    'synthetic_operator_semantics':build['operator_contact']['fixture_semantics'],
    'category_path':build['process_changes']['selected_oekobaudat_category_path'],
    'external_documents':build['closure']['copied_digital_files'],
  },
  'version_guard':guard,
  'official_profile_result':{
    'positive':pos['is_positive'],
    'errors':pos['error_count'],
    'warnings':pos['warning_count'],
    'events':pos['event_count'],
    'normalized_event_fingerprint_sha256':positive_fingerprint,
    'warning_groups':[{'count':n,'aspect':k[0],'message':k[1]} for k,n in sorted(warning_groups.items())],
  },
  'negative_controls':{
    'missing_oekobaudat_classification':{
      'positive':neg['is_positive'],
      'errors':neg['error_count'],
      'normalized_event_fingerprint_sha256':negative_fingerprint,
      'required_error_observed':any(e['severity']=='ERROR' and 'ÖKOBAUDAT categories must be present.' in e['message'] for e in neg['events']),
    },
    'v13_mutation':'REJECTED_BY_V12_VERSION_GUARD_BEFORE_PROFILE_EVALUATION',
  },
  'warning_policy':{
    'warnings_retained':True,
    'invented_environmental_values_added_to_silence_warnings':False,
    'summary':'The positive fixture retains 26 official profile warnings: gross density, predecessor metadata, and missing C1/C2 declarations for 12 EN15804+A2 EF3.0 indicators. No environmental values were fabricated merely to suppress warnings.',
  },
  'limitations':[
    'The fixture is synthetic and non-production; profile compatibility is not BBSR plausibility approval, programme-operator acceptance, registration, or certification.',
    'Use of a profile-allowed programme-operator UUID is solely a synthetic interoperability input and does not state affiliation, authority, approval, or provider/source-use rights.',
    'Profile compatibility does not establish scientific validity, product representativeness, professional LCA suitability, code compliance, engineering/architectural approval, procurement approval, or regulatory approval.',
    'This v1.2 profile receipt must not be interpreted as ILCD+EPD v1.3 profile compliance; v0.7 remains the separate v1.3 XSD/master-data gate.',
    'Source acquisition/use authorization remains a separate v0.6 evidence dimension.',
  ],
}
payload=json.dumps(report,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
report['receipt_sha256']=hashlib.sha256(payload).hexdigest()
(root/'proofgrid-v08-final-receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
print(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False))
PY

# 9. Retain receipts/results only; do not retain the synthetic package bytes.
echo 'FINAL_V08_GATE=PASS'
