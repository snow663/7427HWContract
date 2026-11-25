"""Bind a trusted native inspection to the exact code, symbols and metadata.

This detects stale/mixed build artifacts. It is not a signature or a new ELF
inspection: a caller who fabricates a whole bundle can fabricate its hashes.
The build driver is responsible for validating the real ELF before binding.
"""
from __future__ import annotations

import hashlib
import json
import re

from compose_hc11_rom import ImageError, _flatten

SCHEMA = "7427-native-artifact-binding-v1"


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def artifact_binding(code_segments, nm_text, inspection):
    elf_hash = inspection.get("linked_elf_sha256", "")
    if not isinstance(elf_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", elf_hash):
        raise ImageError("Native inspection lacks a valid linked ELF SHA256")
    code = _flatten(code_segments, "native C binding", allow_vectors=False)
    payload = b"".join(a.to_bytes(2, "big") + bytes([code[a]]) for a in sorted(code))
    metadata = {k: v for k, v in inspection.items() if k != "artifact_binding"}
    return {
        "schema": SCHEMA,
        "code_sha256": _hash(payload),
        "nm_sha256": _hash(nm_text.encode("utf-8")),
        "inspection_sha256": _hash(json.dumps(metadata, sort_keys=True,
            separators=(",", ":"), ensure_ascii=True).encode("ascii")),
    }


def verify_artifact_binding(code_segments, nm_text, inspection):
    binding = inspection.get("artifact_binding")
    if not isinstance(binding, dict) or binding.get("schema") != SCHEMA:
        raise ImageError("Native code/symbols/inspection are not bound to one build")
    expected = artifact_binding(code_segments, nm_text, inspection)
    for field, value in expected.items():
        if binding.get(field) != value:
            raise ImageError("Native artifact bundle mismatch: " + field)
