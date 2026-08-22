# RegenExcalibur Evidence Portal v0.1

Local-first static portal for governed evidence verification, redaction, comparison, and audit export.

## Features
- Drag/drop JSON ingestion
- Canonical SHA-256 verification
- Stored tamper-evident receipt validation
- Authority-boundary surfacing
- Evidence chronology
- Dotted-path redaction
- Version comparison
- Audit-packet JSON export
- Regulator-readable HTML receipt
- Browser Print / Save PDF
- No external libraries, analytics, database, or evidence upload

## Run
```bash
python3 -m http.server 8080
```
Open http://localhost:8080.

## Integrity procedure
Remove the top-level `tamper_evident_receipt`, recursively sort object keys, compact-serialize JSON, UTF-8 encode, SHA-256 hash, and compare to `tamper_evident_receipt.record_hash`.

## Boundary
The portal formats and verifies evidence. It is not legal advice, regulator approval, certification, an independent test-lab finding, a suitability decision, or autonomous production control.

Attribution: RegenExcalibur · 1JGM
