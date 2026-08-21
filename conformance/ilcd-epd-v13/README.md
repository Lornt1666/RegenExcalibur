# ProofGrid v0.7 — ILCD+EPD v1.3 XSD / Master-Data Conformance

This directory contains the immutable upstream-pin manifest for ProofGrid's v0.7 official-format conformance gate.

## Scope

v0.7 proves a narrow software statement:

```text
ILCD_EPD_V13_XSD_MASTERDATA_CONFORMANT
```

It means the declared XML instances validated against the pinned authoritative InData ILCD+EPD v1.3 schema graph and the selected authoritative master-data identity resolved from the pinned master-data repository.

It does **not** mean:

- v1.3 validation-profile compliance;
- provider/programme-operator verification;
- authorization to acquire/use/redistribute a real provider EPD;
- scientific validity or product representativeness;
- professional LCA review;
- certification.

## Pinned upstreams

`upstream.json` fixes the validation surface to:

- format repository `InDataWG/ILCD-EPD-Data-Format` commit `7625c7dfc0d5b6bc2020eb0cf0b0503349c914aa`;
- master-data repository `InDataWG/ILCD-EPD-Master-Data` commit `32117b6a70d6c486344247a429449755a2c7eab4`;
- authoritative XSD `schemas/EPD_DataSet.xsd`, git blob `d2b213528adfc2baa82e37c20eef109a9084d04a`;
- official v1.3 positive-control example, git blob `f6bf1a4bddc7800c5c7e69e6268d0b778c6e4969`;
- selected EN 15804+A2 master-data UUID `c0016b33-8cf7-415c-ac6e-deba0d21440d`.

A moving branch name is never sufficient acceptance evidence.

## No schema vendoring

The authoritative schema/master-data repositories are checked out directly at their immutable commits in the dedicated workflow. ProofGrid does not copy the upstream schema graph into this directory or rewrite inherited notices.

## Synthetic derivative

The ProofGrid positive fixture is generated at runtime from the pinned official InData v1.3 example. Only dataset identity/name fields are changed:

- UUID `7f94a337-6ae6-4e34-8658-17d48d7f3d36`;
- English base name `ProofGrid Synthetic ILCD+EPD v1.3 Conformance Fixture`;
- German base name `ProofGrid Synthetischer ILCD+EPD v1.3 Konformitaetstest`.

The generated XML is validated against the same pinned authoritative schema graph and retained with the machine-readable receipt as a workflow artifact.

## Dependency isolation

The v0.7 XML validator lock is separate from the frozen inherited ProofGrid/R5 lock:

```text
xmlschema==4.3.1
elementpath==5.1.2
```

The first attempted pair (`xmlschema 4.3.2` + `elementpath 5.1.2`) was rejected by hosted dependency resolution because it was not a satisfiable pair. The compatible exact pair above was adopted without relaxing the conformance gate.

## Security posture

Schema composition is sandboxed to the pinned local schema checkout and XML parsing is defused. Instance location hints are not used to widen the validation graph. A unit test confirms that an unpinned remote schema import is blocked.

Local malformed/adversarial XML resources are also independently sandboxed to their own local directories.

## Hosted negative cases

The dedicated workflow verifies rejection of:

- wrong format/master-data commit identity;
- authoritative XSD tampering;
- malformed XML;
- missing required process information;
- invalid process namespace;
- remote/unpinned schema resolution;
- false v1.3 profile-validation state.

## First green implementation receipt

The initial green implementation run recorded:

- 51 tests passed;
- authoritative XSD SHA-256 `2cf30de74b6a9607503aa99d791b196a88c709b9975546d837789bf1bdb93d0a`;
- official example SHA-256 `78476ee519b243088a226b013beb2d7b810d824a177070fcedb43011daa21a50`;
- selected master-data SHA-256 `56527da732b221c30cba7b1314c4ce6bae90b8804ba157927299c0193af2990f`;
- synthetic derivative SHA-256 `7db95464214c68d6cf3cd9e3164e62d414d34b55e16c9a8133ee925947f04f16`;
- receipt SHA-256 `094f96b2ff3659a9b8fdb320dcf6bc91ad0e64ebfc5c0d474b3ea0ab860d338e`;
- artifact ZIP digest `7596b06849a4c8e9680cae42f83e9183e0a19f78d6de1c97863d418a9cc8371e`.

The documentation-complete exact head must receive its own green receipt before issue #14 is closed.
