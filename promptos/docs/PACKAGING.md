# Packaging

PromptOS uses a standard `src/` layout and declares runtime JSON/schema resources as package data.

The CI wheel smoke test installs the built wheel into a fresh virtual environment and runs conformance from `/tmp`, outside the source tree. This detects missing package resources that source-tree tests can conceal.

No runtime third-party Python dependency is required by RC1.
