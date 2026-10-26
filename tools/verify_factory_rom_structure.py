#!/usr/bin/env python3
"""Verify the reviewed lookup block against actual, hash-identified BMHM bytes.

--rom verifies the complete supplied image identity before reading ranges.
--check-recorded checks the committed byte evidence and pointer CSV only; it
does not substitute for reading a complete ROM image.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from factory_structure import ROOT, SOURCE, load_regions, text_sha256

EXPECTED_SHA256 = "6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004"
EVIDENCE = ROOT / "maps/structure/bmhm_rom_structure_evidence.json"
POINTERS = ROOT / "maps/structure/bmhm_rom_lookup_pointers.csv"
RANGES = [
    ("preceding_return", 0xC2D3, 0xC2D6),
    ("lookup_descriptors", 0xC2D6, 0xC40A),
    ("following_code", 0xC40A, 0xC40F),
    ("caller_C35E", 0xC06D, 0xC077),
    ("caller_C380", 0xC19F, 0xC1A9),
    ("caller_C3A2_and_data_lookup", 0xC088, 0xC09C),
    ("caller_C3C4", 0xC1C4, 0xC1CE),
    ("computed_first_four_bases", 0xC849, 0xC87C),
    ("caller_last_two_bases", 0xC881, 0xC88F),
    ("pointer_lookup_helper", 0xD8FE, 0xD92E),
    ("selected_calibration_data_reader", 0xF4C1, 0xF4DE),
]
# These are instruction encodings at the actual caller and helper addresses,
# not reassembled bytes from the HAC text. Their roles follow HC11 semantics.
ANCHORS = {
    0xC088: "CE C3 A2",       # load descriptor base, not jump to it
    0xC08F: "BD D8 FE",       # call pointer-selection helper
    0xC094: "CE 6E 08",       # fallback data-table base
    0xC099: "BD F4 C1",       # use selected/fallback X in data lookup
    0xD900: "A6 00",          # read first descriptor byte through X
    0xD903: "A6 01",          # read second descriptor byte
    0xD906: "58 3A",          # double B and add to X
    0xD90A: "08 08",          # skip the two-byte header
    0xD91F: "EE 00",          # READ the selected pointer word into X
    0xD92D: "39",             # return, rather than execute the table word
    0xC2D5: "39",             # preceding code ends in RTS
    0xF4C1: "3C 37 C6 10",    # save X/B, use a fixed interpolation step
    0xF4C9: "EC 00",          # read selected calibration data through X
    0xF4DD: "39",             # return from data interpolation helper
}


def pointer_rows(read) -> list[dict]:
    rows = []
    for region in load_regions():
        block = read(region.start, region.end + 1)
        mask, stride = block[:2]
        if not mask or mask & (mask - 1) or stride != 8:
            raise ValueError(f"Unexpected descriptor header at {region.start:04X}")
        row_count = mask.bit_length()
        if len(block) != 2 + row_count * stride:
            raise ValueError(f"Descriptor extent does not fit header at {region.start:04X}")
        for row in range(row_count):
            for slot in range(stride // 2):
                offset = 2 + row * stride + slot * 2
                word = block[offset:offset + 2]
                target = int.from_bytes(word, "big")
                if target and not 0x4000 <= target <= 0x70FF:
                    raise ValueError(f"Pointer outside calibration at {region.start + offset:04X}")
                rows.append({
                    "descriptor_base": f"{region.start:04X}",
                    "header_hex": block[:2].hex(" ").upper(),
                    "row": row, "slot": slot,
                    "word_address": f"{region.start + offset:04X}",
                    "bytes_hex": word.hex(" ").upper(),
                    "word_value": f"{target:04X}",
                    "target_region": "calibration_4000_70ff" if target else "null",
                })
    return rows


def validate_anchors(read) -> None:
    for address, expected in ANCHORS.items():
        expected_bytes = bytes.fromhex(expected)
        if read(address, address + len(expected_bytes)) != expected_bytes:
            raise ValueError(f"Caller/helper opcode mismatch at {address:04X}")


def inspect_rom(image: bytes) -> tuple[dict, list[dict]]:
    if len(image) != 0x10000:
        raise ValueError("Expected the complete 65,536-byte BMHM image")
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("ROM SHA-256 does not match the project's stock BMHM authority")
    read = lambda start, end: image[start:end]
    validate_anchors(read)
    rows = pointer_rows(read)
    evidence = {
        "rom_name": "BMHM.BIN",
        "rom_size_bytes": len(image),
        "rom_sha256": digest,
        "file_offset_equals_cpu_address": True,
        "listing_source_sha256_lf": text_sha256(SOURCE),
        "reviewed_descriptor_count": len(load_regions()),
        "reviewed_descriptor_bytes": 308,
        "pointer_words": len(rows),
        "nonzero_pointer_words": sum(row["target_region"] != "null" for row in rows),
        "byte_ranges": [{
            "purpose": purpose, "start": f"{start:04X}",
            "end_exclusive": f"{end:04X}",
            "bytes_hex": image[start:end].hex(" ").upper(),
        } for purpose, start, end in RANGES],
        "proof_scope": "actual_ROM_descriptor_bytes_and_caller_helper_encodings_verified;no_complete_reachability_or_dual_use_exclusion_claim",
    }
    return evidence, rows


def pointer_csv(rows: list[dict]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def check_recorded(evidence: dict, csv_content: str) -> None:
    if evidence["rom_sha256"] != EXPECTED_SHA256 or evidence["rom_size_bytes"] != 0x10000:
        raise ValueError("Unexpected recorded ROM identity")
    if evidence["listing_source_sha256_lf"] != text_sha256(SOURCE):
        raise ValueError("Listing changed since the recorded ROM check")
    memory: dict[int, int] = {}
    for block in evidence["byte_ranges"]:
        start, end = int(block["start"], 16), int(block["end_exclusive"], 16)
        data = bytes.fromhex(block["bytes_hex"])
        if len(data) != end - start:
            raise ValueError("Invalid recorded range length")
        for offset, byte in enumerate(data):
            if start + offset in memory and memory[start + offset] != byte:
                raise ValueError("Conflicting recorded byte ranges")
            memory[start + offset] = byte
    read = lambda start, end: bytes(memory[address] for address in range(start, end))
    validate_anchors(read)
    rows = pointer_rows(read)
    if pointer_csv(rows) != csv_content:
        raise ValueError("Recorded pointer CSV differs from the ROM byte evidence")
    if len(rows) != evidence["pointer_words"] or sum(row["target_region"] != "null" for row in rows) != evidence["nonzero_pointer_words"]:
        raise ValueError("Recorded pointer counts disagree")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path)
    parser.add_argument("--write-evidence", action="store_true")
    parser.add_argument("--check-recorded", action="store_true")
    args = parser.parse_args()
    if args.check_recorded:
        if args.rom or args.write_evidence:
            parser.error("--check-recorded is separate from full-ROM verification")
        check_recorded(json.loads(EVIDENCE.read_text()), POINTERS.read_text())
        print("PASS: recorded byte evidence is internally consistent (full ROM not read in this mode)")
        return 0
    if args.rom is None:
        parser.error("Supply --rom for actual ROM verification, or --check-recorded")
    evidence, rows = inspect_rom(args.rom.read_bytes())
    if args.write_evidence:
        EVIDENCE.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        POINTERS.write_text(pointer_csv(rows), encoding="utf-8")
    else:
        if json.loads(EVIDENCE.read_text()) != evidence or POINTERS.read_text() != pointer_csv(rows):
            raise ValueError("Actual-ROM verification differs from the committed evidence")
    print(f"PASS: actual BMHM ROM {EXPECTED_SHA256}; 10 descriptors, 308 bytes, {len(rows)} pointers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
