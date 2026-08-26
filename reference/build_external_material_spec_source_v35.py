#!/usr/bin/env python3
"""Build a ProofGrid v3.5 external material-specification source record.

The builder performs no semantic inference. The operator must explicitly state
source authority, candidate binding method, and one of the three v3.5 source
outcomes. Exact returned source bytes and exact quoted source text are hashed
automatically.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reference import external_material_spec_admission_v35 as admission

IFC_SOURCE_SHA = "19d7d02d53c2b88e86890ee236297b12bbb0f7748030cd32ff6a22762e9966bb"
STEP_ID = 9730
GLOBAL_ID = "3BmeJtEDj3AQO77Os2w7Ny"
OBJECT_ID = "2395272"
MATERIAL_NAME = "Ortbeton - bewehrt"

DECISIONS = (
    "AUTHORITATIVE_MATERIAL_SPEC_ACQUIRED_AND_CANDIDATE_BOUND",
    "AUTHORITATIVE_MATERIAL_SPEC_ACQUIRED_BUT_NOT_CANDIDATE_BOUND",
    "AUTHORITATIVE_SOURCE_CONFIRMS_STRENGTH_CLASS_NOT_SPECIFIED",
)
BINDING_METHODS = (
    "EXACT_GLOBAL_ID",
    "EXACT_OBJECT_ID",
    "EXACT_DOCUMENTED_MATERIAL_GROUP",
    "AUTHOR_EXPLICIT_CONFIRMATION",
    "UNBOUND",
)
AUTHORITY_BASES = (
    "PROJECT_AUTHOR",
    "PROJECT_MAINTAINER",
    "ORIGINAL_MODEL_AUTHOR",
    "ORIGINAL_SPECIFICATION_AUTHOR",
    "OTHER_DOCUMENTED_PROJECT_AUTHORITY",
)
CHANNELS = ("EMAIL_REPLY", "AUTHOR_ATTACHMENT", "OFFICIAL_PROJECT_ARTIFACT", "AUTHOR_CONFIRMATION")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(args: argparse.Namespace) -> dict:
    source_bytes = args.content_file.read_bytes()
    quoted_bytes = args.source_text_file.read_bytes() if args.source_text_file else None

    decision = args.decision
    if decision == "AUTHORITATIVE_MATERIAL_SPEC_ACQUIRED_AND_CANDIDATE_BOUND":
        if args.binding_method == "UNBOUND":
            raise ValueError("candidate-bound decision cannot use UNBOUND")
        if not args.strength_class:
            raise ValueError("candidate-bound decision requires --strength-class")
        if quoted_bytes is None:
            raise ValueError("candidate-bound decision requires --source-text-file")
        candidate_bound = True
        strength_explicit = True
        absence = False
        strength_class = args.strength_class

    elif decision == "AUTHORITATIVE_MATERIAL_SPEC_ACQUIRED_BUT_NOT_CANDIDATE_BOUND":
        if args.binding_method != "UNBOUND":
            raise ValueError("unbound decision requires --binding-method UNBOUND")
        candidate_bound = False
        strength_explicit = bool(args.strength_class)
        absence = False
        strength_class = args.strength_class
        if strength_explicit and quoted_bytes is None:
            raise ValueError("explicit unbound strength class requires --source-text-file")

    elif decision == "AUTHORITATIVE_SOURCE_CONFIRMS_STRENGTH_CLASS_NOT_SPECIFIED":
        if args.binding_method == "UNBOUND":
            raise ValueError("absence confirmation must be bound to the exact candidate")
        if args.strength_class:
            raise ValueError("absence confirmation cannot include --strength-class")
        if quoted_bytes is None:
            raise ValueError("absence confirmation requires --source-text-file")
        candidate_bound = True
        strength_explicit = False
        absence = True
        strength_class = None

    else:
        raise ValueError(f"unsupported decision: {decision}")

    record = {
        "schema_version": "1.0",
        "record_type": "ProofGridExternalMaterialSpecificationSource",
        "acquisition": {
            "channel": args.channel,
            "source_locator": args.source_locator,
            "message_id": args.message_id,
            "thread_id": args.thread_id,
            "attachment_name": args.attachment_name,
            "media_type": args.media_type,
            "received_at": args.received_at,
            "content_sha256": sha256_bytes(source_bytes),
            "content_bytes": len(source_bytes),
        },
        "candidate": {
            "ifc_source_sha256": IFC_SOURCE_SHA,
            "step_id": STEP_ID,
            "global_id": GLOBAL_ID,
            "object_id": OBJECT_ID,
            "material_name": MATERIAL_NAME,
            "binding_method": args.binding_method,
            "candidate_bound": candidate_bound,
        },
        "source_authority": {
            "author_name": args.author_name,
            "author_email": args.author_email,
            "author_organization": args.author_organization,
            "relation_to_digitalhub": args.relation_to_digitalhub,
            "authority_basis": args.authority_basis,
        },
        "material_semantics": {
            "strength_class_explicit": strength_explicit,
            "concrete_strength_class": strength_class,
            "strength_class_source_text_sha256": sha256_bytes(quoted_bytes) if quoted_bytes is not None else None,
            "explicit_absence_statement": absence,
        },
        "decision": decision,
        "authority_boundaries": {
            "fuzzy_matching": False,
            "strength_class_inferred": False,
            "environmental_mapping_performed": False,
            "impact_calculation_performed": False,
            "scientific_suitability_confirmed": False,
            "professional_review_performed": False,
            "regulator_acceptance_implied": False,
            "certified": False,
        },
    }
    admission.validate_schema(record)
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content-file", type=Path, required=True)
    parser.add_argument("--source-text-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--channel", choices=CHANNELS, required=True)
    parser.add_argument("--source-locator", required=True)
    parser.add_argument("--message-id")
    parser.add_argument("--thread-id")
    parser.add_argument("--attachment-name")
    parser.add_argument("--media-type")
    parser.add_argument("--received-at", required=True)
    parser.add_argument("--author-name", required=True)
    parser.add_argument("--author-email")
    parser.add_argument("--author-organization", required=True)
    parser.add_argument("--relation-to-digitalhub", required=True)
    parser.add_argument("--authority-basis", choices=AUTHORITY_BASES, required=True)
    parser.add_argument("--decision", choices=DECISIONS, required=True)
    parser.add_argument("--binding-method", choices=BINDING_METHODS, required=True)
    parser.add_argument("--strength-class")
    args = parser.parse_args(argv)

    try:
        record = build(args)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    except (OSError, ValueError, admission.ExternalMaterialSpecAdmissionError) as exc:
        print(f"FAILED: {exc}")
        return 2

    print("RESULT: V35_EXTERNAL_SOURCE_RECORD_BUILT")
    print("DECISION: " + record["decision"])
    print("SOURCE_SHA256: " + record["acquisition"]["content_sha256"])
    print("CANDIDATE_BOUND: " + str(record["candidate"]["candidate_bound"]).lower())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
