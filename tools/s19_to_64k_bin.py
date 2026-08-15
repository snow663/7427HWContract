#!/usr/bin/env python3
"""Convert Motorola S-record output to a 64 KiB ROM image.

Intended for MGTEK ASM11 output from the 7427 replacement-OS build.
Unspecified bytes are filled with 0xFF so the result matches an erased ROM.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

IMAGE_SIZE = 0x10000
FILL = 0xFF
ADDRESS_BYTES = {"S1": 2, "S2": 3, "S3": 4}


def parse_record(line: str) -> tuple[int, bytes] | None:
    line = line.strip()
    if not line:
        return None

    rectype = line[:2]
    if rectype not in ADDRESS_BYTES:
        return None

    addr_len = ADDRESS_BYTES[rectype]
    count = int(line[2:4], 16)
    raw = bytes.fromhex(line[4:])

    if (sum(bytes.fromhex(line[2:])) & 0xFF) != 0xFF:
        raise ValueError(f"bad S-record checksum: {line}")

    address = int.from_bytes(raw[:addr_len], "big")
    data_len = count - addr_len - 1
    data = raw[addr_len:addr_len + data_len]
    return address, data


def convert(src: Path, dst: Path) -> None:
    image = bytearray([FILL] * IMAGE_SIZE)

    for line in src.read_text().splitlines():
        parsed = parse_record(line)
        if parsed is None:
            continue
        address, data = parsed
        end = address + len(data)
        if address < 0 or end > IMAGE_SIZE:
            raise ValueError(f"record exceeds 64 KiB image: {line}")
        image[address:end] = data

    dst.write_bytes(image)

    reset_vector = int.from_bytes(image[0xFFFE:0x10000], "big")
    digest = hashlib.sha256(image).hexdigest()
    print(f"wrote {dst} ({len(image)} bytes)")
    print(f"reset vector @ $FFFE = ${reset_vector:04X}")
    print(f"SHA256 {digest}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_s19", type=Path)
    parser.add_argument("output_bin", type=Path)
    args = parser.parse_args()
    convert(args.input_s19, args.output_bin)


if __name__ == "__main__":
    main()
