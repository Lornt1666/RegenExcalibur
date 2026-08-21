# IFC Adapter

Status: **planned / not implemented in v0.1**.

The adapter will ingest Industry Foundation Classes (IFC) data into the canonical ProofGrid building graph while preserving source identifiers and provenance.

Initial responsibilities:

- map project/building/storey/space/product identifiers;
- extract declared quantities where available;
- preserve IFC entity IDs and source hashes;
- emit mapping warnings rather than silently invent missing values;
- keep units explicit;
- support conformance fixtures before production use.

The v0.1 genesis slice deliberately uses JSON fixtures so the evidence kernel can be validated independently of IFC parser complexity.
