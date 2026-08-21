#!/usr/bin/env python3
"""Inspect a pinned ILCD validation profile JAR without extracting/vendorizing it.

The inspector records the profile JAR hash, text-resource entry hashes, UUID-like
identifiers, and bounded keyword contexts from the exact profile bytes. It is a
diagnostic/provenance tool only; it does not interpret a UUID as authorized
unless the surrounding profile resource itself establishes that meaning.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

UUID_RE = re.compile(r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
DEFAULT_KEYWORDS = [
    "oekobaudat",
    "program operator",
    "programme operator",
    "compliance system",
    "classification",
    "category",
    "sub-category",
    "subcategory",
]
TEXT_EXTENSIONS = {
    ".xml", ".xsl", ".xslt", ".sch", ".txt", ".properties", ".json",
    ".csv", ".md", ".mf", ".rules", ".config", ".yaml", ".yml",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def bounded_context(text: str, start: int, end: int, radius: int = 240) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    value = text[left:right].replace("\r", " ").replace("\n", " ").replace("\t", " ")
    return " ".join(value.split())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--keyword", action="append", default=[])
    args = parser.parse_args()

    jar_path = args.jar
    if not jar_path.is_file():
        raise SystemExit(f"profile JAR not found: {jar_path}")

    keywords = [item.lower() for item in (args.keyword or DEFAULT_KEYWORDS)]
    entries = []
    keyword_matches = []
    uuid_contexts: dict[str, list[dict[str, str]]] = {}

    with zipfile.ZipFile(jar_path) as archive:
        for info in sorted(archive.infolist(), key=lambda x: x.filename):
            if info.is_dir():
                continue
            raw = archive.read(info)
            suffix = Path(info.filename).suffix.lower()
            if suffix not in TEXT_EXTENSIONS and not info.filename.upper().endswith("META-INF/MANIFEST.MF"):
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    text = raw.decode("latin-1")
                except UnicodeDecodeError:
                    continue

            entry_record = {
                "path": info.filename,
                "size": len(raw),
                "sha256": sha256_bytes(raw),
            }
            entries.append(entry_record)
            lower = text.lower()

            for keyword in keywords:
                pos = 0
                while True:
                    index = lower.find(keyword, pos)
                    if index < 0:
                        break
                    keyword_matches.append({
                        "entry": info.filename,
                        "keyword": keyword,
                        "context": bounded_context(text, index, index + len(keyword)),
                    })
                    pos = index + len(keyword)

            for match in UUID_RE.finditer(text):
                uid = match.group(0).lower()
                context = bounded_context(text, match.start(), match.end())
                bucket = uuid_contexts.setdefault(uid, [])
                item = {"entry": info.filename, "context": context}
                if item not in bucket:
                    bucket.append(item)

    # Keep deterministic ordering and remove duplicate keyword contexts.
    dedup_keyword = []
    seen = set()
    for item in sorted(keyword_matches, key=lambda x: (x["keyword"], x["entry"], x["context"])):
        key = (item["keyword"], item["entry"], item["context"])
        if key not in seen:
            seen.add(key)
            dedup_keyword.append(item)

    result = {
        "profile_jar": jar_path.name,
        "profile_jar_sha256": sha256_bytes(jar_path.read_bytes()),
        "keywords": keywords,
        "text_entries": entries,
        "keyword_matches": dedup_keyword,
        "uuid_contexts": {key: value for key, value in sorted(uuid_contexts.items())},
    }
    result["inspection_sha256"] = sha256_bytes(canonical_json_bytes(result))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    print("PROFILE JAR SHA256", result["profile_jar_sha256"])
    print("TEXT ENTRIES", len(entries))
    print("KEYWORD MATCHES", len(dedup_keyword))
    print("UUIDS", len(uuid_contexts))
    print("INSPECTION SHA256", result["inspection_sha256"])
    print("\nKEYWORD CONTEXTS")
    for item in dedup_keyword:
        print(json.dumps(item, ensure_ascii=False, sort_keys=True))
    print("\nUUID CONTEXTS")
    for uid, contexts in sorted(uuid_contexts.items()):
        if any(keyword in " ".join(ctx["context"].lower() for ctx in contexts) for keyword in keywords):
            print(uid)
            for ctx in contexts:
                print(json.dumps(ctx, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
