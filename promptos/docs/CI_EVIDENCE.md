# CI Evidence Expectations

The path-scoped workflow must produce successful jobs for Python 3.11 and 3.12.

Each job must:

1. install the package;
2. run all unit tests;
3. run all 120 deterministic conformance cases;
4. generate 60/30/30 corpus partitions;
5. build a wheel;
6. install that wheel into a clean virtual environment;
7. run conformance outside the source tree.

A green workflow proves those configured operations at the exact commit. It does not prove external model quality or production readiness.
