"""Compatibility bridge to the canonical hyphenated research asset.

The canonical research artifact remains `conformance/reference-basis-v13/research_probe.py`
for human-facing release naming. Python imports use this namespace-safe bridge.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_CANONICAL = Path(__file__).resolve().parents[1] / "reference-basis-v13" / "research_probe.py"
_SPEC = importlib.util.spec_from_file_location("proofgrid_v13_canonical_research_probe", _CANONICAL)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"unable to load canonical v1.3 research probe: {_CANONICAL}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

# Export only the deterministic parsing helpers used by the accepted extractor.
inspect_process = _MODULE.inspect_process
inspect_flow = _MODULE.inspect_flow
inspect_flow_property = _MODULE.inspect_flow_property
inspect_unit_group = _MODULE.inspect_unit_group
