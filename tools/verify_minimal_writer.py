#!/usr/bin/env python3
"""Static verifier for the minimal 7427 EFI pulsewidth writer stub.

This does not assemble the source. It enforces the hardware-contract shape:
  EFI_PW_WRITE contains exactly one hardware write: STD L3FCE.
  No companion/timer writes are allowed in the writer stub.
  Static vectors match the 1/65536 second unit hypothesis.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

COUNTS_PER_MS = 65.536
ALLOWED_TARGET = 'L3FCE'
ALLOWED_ADDRESS = '0X3FCE'
WRITE_MNEMONICS = {'STAA', 'STAB', 'STD', 'STX', 'STY'}
BIT_WRITE_MNEMONICS = {'BSET', 'BCLR'}
FORBIDDEN_TARGETS = {
    'L3FCC', '$3FCC', '0X3FCC',
    'L3FEA', '$3FEA', '0X3FEA',
    'L301C', '$301C', '0X301C',
    'L301E', '$301E', '0X301E',
    'L3020', '$3020', '0X3020',
    'L3022', '$3022', '0X3022',
    'L3023', '$3023', '0X3023',
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else repo_root() / p


def strip_comment(line: str) -> str:
    return line.split(';', 1)[0].strip()


def normalize_token(token: str) -> str:
    return token.strip().replace(',', '').upper()


def parse_source(path: Path) -> tuple[list[tuple[int, str, str]], list[tuple[int, str]]]:
    hardware_writes: list[tuple[int, str, str]] = []
    forbidden: list[tuple[int, str]] = []
    in_writer = False

    for lineno, raw in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        code = strip_comment(raw)
        if not code:
            continue
        label = code.rstrip(':').upper()
        if label == 'EFI_PW_WRITE':
            in_writer = True
            continue
        if in_writer and code.endswith(':') and label != 'EFI_PW_WRITE':
            in_writer = False
        if not in_writer:
            continue

        parts = code.split()
        if not parts:
            continue
        mnemonic = parts[0].upper()
        operands = [normalize_token(p) for p in parts[1:]]
        operand_blob = ' '.join(operands)

        if mnemonic in WRITE_MNEMONICS:
            target = operands[0] if operands else ''
            hardware_writes.append((lineno, mnemonic, target))
            if target in FORBIDDEN_TARGETS:
                forbidden.append((lineno, code))
        elif mnemonic in BIT_WRITE_MNEMONICS:
            if any(t in operand_blob for t in FORBIDDEN_TARGETS):
                forbidden.append((lineno, code))

    return hardware_writes, forbidden


def parse_count(value: str) -> int:
    value = value.strip().lower()
    if value.startswith('0x'):
        return int(value, 16)
    if value.startswith('$'):
        return int(value[1:], 16)
    return int(value, 10)


def verify_vectors(path: Path, tolerance_ms: float = 0.0005) -> list[str]:
    errors: list[str] = []
    with path.open(newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    for i, row in enumerate(rows, 2):
        counts = parse_count(row['input_counts_hex'])
        if counts != int(row['input_counts_dec']):
            errors.append(f'row {i}: hex/dec count mismatch')
        expected = float(row['expected_ms'])
        calculated = counts / COUNTS_PER_MS
        if abs(expected - calculated) > tolerance_ms:
            errors.append(f'row {i}: expected_ms {expected:.6f} != calculated {calculated:.6f}')
        if row['expected_write_address'].upper() != ALLOWED_ADDRESS:
            errors.append(f'row {i}: expected_write_address is not 0x3FCE')
        if str(row['expected_write_width']).strip() != '16':
            errors.append(f'row {i}: expected_write_width is not 16')
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', default='source/minimal_os/fuel/efi_pw_writer.asm')
    ap.add_argument('--vectors', default='tests/static/efi_pw_writer_vectors.csv')
    args = ap.parse_args()

    source = resolve_path(args.source)
    vectors = resolve_path(args.vectors)
    writes, forbidden = parse_source(source)
    vector_errors = verify_vectors(vectors)

    errors: list[str] = []
    if len(writes) != 1:
        errors.append(f'hardware_write_count expected 1, got {len(writes)}: {writes}')
    else:
        lineno, mnemonic, target = writes[0]
        if mnemonic != 'STD' or target != ALLOWED_TARGET:
            errors.append(f'only hardware write must be STD L3FCE, got line {lineno}: {mnemonic} {target}')
    if forbidden:
        errors.append(f'forbidden writes found: {forbidden}')
    errors.extend(vector_errors)

    print(f'source: {source}')
    print(f'vectors: {vectors}')
    print(f'hardware_write_count: {len(writes)}')
    print(f'hardware_writes: {writes}')
    print(f'forbidden_write_count: {len(forbidden)}')
    print(f'vector_error_count: {len(vector_errors)}')

    if errors:
        print('status: FAIL')
        for e in errors:
            print(f'ERROR: {e}')
        return 1

    print('only_hardware_write: STD L3FCE')
    print('status: PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
