#!/usr/bin/env python3
"""Audit $31 HAC labeled calibration data against the actual target BMHM BIN.

Authority rule:
- BIN bytes are numeric authority.
- HAC source is semantic/provenance authority.
- Mismatches are emitted, never silently corrected.

Expected source input is 31_HAC_calibration_extract_nowrap.html containing the
`calibration-extract-json` payload produced by the project extractor.

Example:
    python tools/audit_calibration_against_bin.py \
        --extract 31_HAC_calibration_extract_nowrap.html \
        --bin BMHM_95_C-G-K_Truck_7_4TBI_4l80.bin \
        --audit maps/closeout/calibration_bin_audit.csv \
        --overlay maps/closeout/calibration_bin_correction_overlay.csv
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

AUDIT_FIELDS = [
    "address_hex",
    "address_dec",
    "section_index",
    "label",
    "directive",
    "declared_size",
    "source_operand",
    "source_bytes",
    "bin_bytes",
    "value_status",
    "alignment_status",
    "label_width_status",
    "source_warning",
    "source_parse_error",
    "comment",
]

OVERLAY_FIELDS = [
    "address_hex",
    "label",
    "directive",
    "declared_size",
    "source_operand",
    "source_bytes",
    "bin_bytes_authority",
    "correction_action",
    "alignment_status",
    "label_width_status",
    "section_index",
    "comment",
]


def load_extract(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(
        r'<script id="calibration-extract-json" type="application/json">(.*?)</script>',
        text,
        re.S,
    )
    if not match:
        raise SystemExit("calibration-extract-json payload not found")
    return json.loads(html.unescape(match.group(1)))


def parse_source_bytes(record: dict[str, Any]) -> bytes:
    raw = (record.get("bytes_be_hex") or "").strip()
    if not raw:
        return b""
    try:
        return bytes.fromhex(raw)
    except ValueError as exc:
        raise SystemExit(
            f"invalid bytes_be_hex at {record.get('address_hex')}: {raw!r}"
        ) from exc


def hx(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def compare_record(record: dict[str, Any], rom: bytes, rom_base: int) -> dict[str, str]:
    address = int(record["address"])
    declared_size = int(record.get("declared_size") or 0)
    expected = parse_source_bytes(record)

    offset = address - rom_base
    if offset < 0 or offset + declared_size > len(rom):
        actual = b""
        value_status = "OUTSIDE_BIN"
    else:
        actual = rom[offset : offset + declared_size]
        if len(expected) != declared_size:
            value_status = "SOURCE_WIDTH_ERROR"
        elif actual == expected:
            value_status = "MATCH"
        else:
            value_status = "MISMATCH"

    directive = str(record.get("directive") or "").upper()
    if directive == "FDB":
        alignment_status = "EVEN_WORD_ADDRESS" if address % 2 == 0 else "ODD_WORD_ADDRESS_REVIEW"
    else:
        alignment_status = "BYTE_ADDRESS"

    delta = record.get("next_address_delta")
    if delta is None or delta == "":
        label_width_status = "NO_NEXT_LABEL_DELTA"
    else:
        try:
            delta_i = int(delta)
            label_width_status = "WIDTH_OK" if delta_i == declared_size else f"NEXT_LABEL_DELTA_{delta_i}_REVIEW"
        except (TypeError, ValueError):
            label_width_status = "NEXT_LABEL_DELTA_PARSE_REVIEW"

    return {
        "address_hex": str(record.get("address_hex") or f"${address:04X}"),
        "address_dec": str(address),
        "section_index": str(record.get("section_index") or ""),
        "label": str(record.get("label") or ""),
        "directive": directive,
        "declared_size": str(declared_size),
        "source_operand": str(record.get("operand") or ""),
        "source_bytes": hx(expected),
        "bin_bytes": hx(actual),
        "value_status": value_status,
        "alignment_status": alignment_status,
        "label_width_status": label_width_status,
        "source_warning": str(record.get("warning") or ""),
        "source_parse_error": str(record.get("parse_error") or ""),
        "comment": re.sub(r"\s+", " ", str(record.get("comment") or "")).strip(),
    }


def correction_action(row: dict[str, str]) -> str:
    status = row["value_status"]
    if status == "MISMATCH":
        return "USE_BIN_NUMERIC_VALUE_PRESERVE_SOURCE_SEMANTICS"
    if status == "SOURCE_WIDTH_ERROR":
        return "REVIEW_SOURCE_WIDTH_AND_ADDRESS_LABELING"
    if status == "OUTSIDE_BIN":
        return "REVIEW_ROM_BASE_OR_ADDRESS"
    if row["alignment_status"] == "ODD_WORD_ADDRESS_REVIEW":
        return "REVIEW_WORD_ALIGNMENT_KEEP_BIN_VALUE"
    if row["label_width_status"] not in {"WIDTH_OK", "NO_NEXT_LABEL_DELTA"}:
        return "REVIEW_ADDRESS_LABELING_KEEP_BIN_VALUE"
    return "NO_CORRECTION"


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract", required=True, type=Path)
    parser.add_argument("--bin", required=True, dest="bin_path", type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--overlay", required=True, type=Path)
    parser.add_argument(
        "--rom-base",
        default="0x0000",
        help="CPU address represented by BIN byte 0; default 0 for full 64 KiB image",
    )
    args = parser.parse_args()

    obj = load_extract(args.extract)
    rom = args.bin_path.read_bytes()
    rom_base = int(args.rom_base, 0)

    if rom_base == 0 and len(rom) != 0x10000:
        raise SystemExit(
            f"expected full 64 KiB BMHM image with --rom-base 0; got 0x{len(rom):X} bytes"
        )

    rows = [compare_record(record, rom, rom_base) for record in obj["records"]]
    write_csv(args.audit, AUDIT_FIELDS, rows)

    overlay: list[dict[str, str]] = []
    for row in rows:
        action = correction_action(row)
        if action == "NO_CORRECTION":
            continue
        overlay.append(
            {
                "address_hex": row["address_hex"],
                "label": row["label"],
                "directive": row["directive"],
                "declared_size": row["declared_size"],
                "source_operand": row["source_operand"],
                "source_bytes": row["source_bytes"],
                "bin_bytes_authority": row["bin_bytes"],
                "correction_action": action,
                "alignment_status": row["alignment_status"],
                "label_width_status": row["label_width_status"],
                "section_index": row["section_index"],
                "comment": row["comment"],
            }
        )
    write_csv(args.overlay, OVERLAY_FIELDS, overlay)

    counts = Counter(row["value_status"] for row in rows)
    align = Counter(row["alignment_status"] for row in rows)
    width = Counter(row["label_width_status"] for row in rows)

    print(f"BIN: {args.bin_path}")
    print(f"BIN size: 0x{len(rom):X}")
    print(f"ROM base: 0x{rom_base:04X}")
    print(f"records audited: {len(rows)}")
    for key in sorted(counts):
        print(f"{key}: {counts[key]}")
    print(f"odd FDB addresses needing review: {align.get('ODD_WORD_ADDRESS_REVIEW', 0)}")
    print(
        "label-width review rows: "
        + str(sum(v for k, v in width.items() if k not in {"WIDTH_OK", "NO_NEXT_LABEL_DELTA"}))
    )
    print(f"correction/review overlay rows: {len(overlay)}")

    hard_fail = counts.get("MISMATCH", 0) + counts.get("SOURCE_WIDTH_ERROR", 0) + counts.get("OUTSIDE_BIN", 0)
    return 1 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
