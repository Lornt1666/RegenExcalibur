# IFC Adapter

Status: **read-only structural ingestion implemented in v0.2**.

ProofGrid uses IfcOpenShell behind an explicit adapter boundary. The current adapter opens real `.ifc` STEP files and reports bounded project/building structure while preserving source metadata. It does **not** yet transform IFC quantities or materials into environmental claims.

## Current command

```bash
python reference/rx_cli.py ifc-inspect path/to/model.ifc --output ifc-summary.json
```

Current responsibilities:

- parse real IFC files with pinned IfcOpenShell;
- report IFC schema and bounded entity counts;
- preserve STEP IDs, GlobalIds, names, and IFC entity types for projects/buildings;
- fail closed on missing, unsupported, or unparseable files;
- state explicit limitations in generated summaries.

## Deliberately not implemented yet

- material quantity takeoff;
- unit normalization across IFC quantity/property sets;
- EPD/LCA factor matching;
- code-compliance inference;
- engineering or architectural conclusions;
- certification.

Those require separate conformance fixtures, unit/system-boundary rules, provenance, and evidence gates. Structural IFC ingestion is therefore **input capability**, not proof of environmental or regulatory correctness.
