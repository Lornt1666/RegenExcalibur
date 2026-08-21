# ProofGrid v0.6 Synthetic Source-Import Fixture

This package exists only to prove the v0.6 authorization/provenance software gate. It contains no real EPD provider data and grants no rights to third-party environmental datasets.

## Contents

- `import-manifest.json` — declared acquisition/use/authorization/source/parser manifest.
- `terms/synthetic-authorization.txt` — synthetic test authorization terms snapshot.
- `source/synthetic-declaration.xml` — synthetic environmental declaration carrier.

## Declared authority

- status: `TEST_ONLY`
- acquisition: `TEST_FIXTURE`
- intended use: `INTERNAL_TEST`
- synthetic: `true`
- storage: `ALLOWED`
- transformation: `ALLOWED`
- commercial use: `PROHIBITED`
- redistribution: `PROHIBITED`
- authorization valid through: `2099-12-31`

This authority applies only to the synthetic fixture in this repository.

## Exact input hashes

- terms snapshot: `18437a5c104ffe5b26a83004300d0b47c240bcc96e09b1119b9992da819fc601`
- synthetic declaration carrier: `1326aa51e0d62444209e78a39cef62046c5683c85609eaf7aea675839ec1a338`

## Parser scope

The fixture declares:

- format `RX-SYNTHETIC-EPD-CARRIER / 1.0`
- parser `rx-synthetic-epd-carrier / 0.6.0`
- profile `rx-synthetic-epd-carrier-1.0`

The carrier is **not** claimed to conform to ILCD+EPD, ECO Platform, ÖKOBAUDAT, EPD International, openEPD, or another programme-operator profile.

## Expected normalized record

- ID: `RX-IMPORTED-SYNTH-CONCRETE-A1A3`
- material ID: `synthetic-import-concrete`
- declared unit: `kg`
- reference quantity: `1.0`
- indicator: `GWP-total = 0.15 kgCO2e`
- boundary: `A1/A2/A3`
- verification state: `UNVERIFIED`
- synthetic: `true`
- redistribution state: `RESTRICTED`

## Genesis #29 hosted receipt

The initial implementation passed 45 hosted tests. The import receipt recorded:

- manifest content SHA-256 `78fea8f1c85bb15fd4471a5fa29644f65ea69d88104e4c69b222e85f28712c21`
- manifest file SHA-256 `b6b6634569d5b14131041c400bb8fd560d7ddde9bdb8015b85cfdd02e04f9ab5`
- normalized record canonical SHA-256 `c155b0c66c8372688b97abb3288c9a9ed8d4906c8793f13f2aa9dce36b1a03fc`
- normalized registry file SHA-256 `b8c1fdc87d4e788eff5b7fc3c6c66f31e0f6264f9c3c767c8bf8fd269d018b0b`
- import receipt SHA-256 `fe5d8e838f0b9f8ec84eb56c49c6fde219a94b4c7556016c30f95be475cc858b`
- rights decision `AUTHORIZED_FOR_DECLARED_IMPORT_ONLY`
- raw source export `false`
- `certified = false`

The documentation-complete branch must obtain its own fresh exact-head CI receipt before issue #10 is completed.
