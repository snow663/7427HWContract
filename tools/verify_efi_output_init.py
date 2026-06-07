#!/usr/bin/env python3
"""Static verifier for the provisional 7427 EFI output init routine.

This does not assemble the source. It verifies the intended contract shape:
  EFI_OUTPUT_INIT clears the ASIC window from $3FC0 through before $3FFA.
  Optional $3FCC/$3FEA preloads remain commented/bench-gated.
  No timer scheduler or runtime EFI_PW_WRITE call appears.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

FORBIDDEN_ACTIVE_TARGETS = {
    'L301C', '$301C', '0X301C',
    'L301E', '$301E', '0X301E',
    'L3020', '$3020', '0X3020',
    'L3022', '$3022', '0X3022',
    'L3023', '$3023', '0X3023',
}
OPTIONAL_PRELOAD_TARGETS = {'L3FCC', '$3FCC', '0X3FCC', 'L3FEA', '$3FEA', '0X3FEA'}
WRITE_MNEMONICS = {'STAA', 'STAB', 'STD', 'STX', 'STY'}
BIT_WRITE_MNEMONICS = {'BSET', 'BCLR'}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else repo_root() / p


def strip_comment(line: str) -> str:
    return line.split(';', 1)[0].strip()


def comment_text(line: str) -> str:
    if ';' not in line:
        return ''
    return line.split(';', 1)[1].strip()


def normalize_token(token: str) -> str:
    return token.strip().replace(',', '').upper()


def active_lines(path: Path) -> list[tuple[int, str, str]]:
    lines = []
    in_init = False
    for lineno, raw in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        code = strip_comment(raw)
        if not code:
            continue
        label = code.rstrip(':').upper()
        if label == 'EFI_OUTPUT_INIT':
            in_init = True
            lines.append((lineno, raw, code))
            continue
        if in_init and code.endswith(':') and label not in {'EFI_OUTPUT_INIT', 'EFI_INIT_CLEAR_LOOP'}:
            in_init = False
        if in_init:
            lines.append((lineno, raw, code))
    return lines


def find_comment_optional_preloads(path: Path) -> tuple[bool, bool]:
    saw_3fcc = False
    saw_3fea = False
    for raw in path.read_text(encoding='utf-8').splitlines():
        c = comment_text(raw).upper()
        if 'STD' in c and 'L3FCC' in c:
            saw_3fcc = True
        if 'STD' in c and 'L3FEA' in c:
            saw_3fea = True
    return saw_3fcc, saw_3fea


def verify_source(path: Path) -> list[str]:
    errors: list[str] = []
    lines = active_lines(path)
    code_blob = '\n'.join(code.upper() for _, _, code in lines)

    required_snippets = [
        'EFI_OUTPUT_INIT',
        'LDX   #L3FC0',
        'CLRA',
        'CLRB',
        'EFI_INIT_CLEAR_LOOP',
        'STD   0,X',
        'INX',
        'CPX   #L3FFA',
        'BNE   EFI_INIT_CLEAR_LOOP',
        'RTS',
    ]
    compact_blob = re.sub(r'\s+', ' ', code_blob)
    for snippet in required_snippets:
        compact = re.sub(r'\s+', ' ', snippet.upper()).strip()
        if compact not in compact_blob:
            errors.append(f'missing required init snippet: {snippet}')

    if 'EFI_PW_WRITE' in code_blob:
        errors.append('EFI_OUTPUT_INIT must not call EFI_PW_WRITE')

    active_writes = []
    optional_active = []
    forbidden_active = []
    for lineno, raw, code in lines:
        parts = code.split()
        if not parts:
            continue
        mnemonic = parts[0].upper()
        operands = [normalize_token(p) for p in parts[1:]]
        operand_blob = ' '.join(operands)
        if mnemonic in WRITE_MNEMONICS:
            target = operands[0] if operands else ''
            active_writes.append((lineno, mnemonic, target, code))
            if target in OPTIONAL_PRELOAD_TARGETS:
                optional_active.append((lineno, code))
            if target in FORBIDDEN_ACTIVE_TARGETS:
                forbidden_active.append((lineno, code))
        elif mnemonic in BIT_WRITE_MNEMONICS:
            if any(t in operand_blob for t in OPTIONAL_PRELOAD_TARGETS):
                optional_active.append((lineno, code))
            if any(t in operand_blob for t in FORBIDDEN_ACTIVE_TARGETS):
                forbidden_active.append((lineno, code))

    if not any(m == 'STD' and target == '0' for _, m, target, _ in active_writes):
        # normalize_token('0,X') becomes '0X', so also allow that form.
        if not any(m == 'STD' and target in {'0X', '0'} for _, m, target, _ in active_writes):
            errors.append('expected active clear write STD 0,X not found')

    if optional_active:
        errors.append(f'$3FCC/$3FEA active preload writes are not allowed yet: {optional_active}')
    if forbidden_active:
        errors.append(f'timer scheduler active writes are forbidden: {forbidden_active}')

    saw_3fcc_comment, saw_3fea_comment = find_comment_optional_preloads(path)
    if not saw_3fcc_comment or not saw_3fea_comment:
        errors.append('optional $3FCC/$3FEA preload comments not found')

    return errors


def parse_count(value: str) -> int:
    value = value.strip().lower()
    if value.startswith('0x'):
        return int(value, 16)
    if value.startswith('$'):
        return int(value[1:], 16)
    return int(value, 10)


def verify_vectors(path: Path) -> list[str]:
    errors: list[str] = []
    with path.open(newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    required = {
        'clear_start': ('1', 0x3FC0, 16, 0x0000),
        'clear_3fce': ('1', 0x3FCE, 16, 0x0000),
        'clear_last_before_3ffa': ('1', 0x3FF8, 16, 0x0000),
        'preload_3fcc_optional': ('0', 0x3FCC, 16, 0xD000),
        'preload_3fea_optional': ('0', 0x3FEA, 16, 0xDFFF),
    }
    by_name = {r['name']: r for r in rows}
    for name, (enabled, addr, width, value) in required.items():
        row = by_name.get(name)
        if not row:
            errors.append(f'missing vector row {name}')
            continue
        if row['enabled'] != enabled:
            errors.append(f'{name}: enabled expected {enabled}, got {row["enabled"]}')
        if parse_count(row['expected_address']) != addr:
            errors.append(f'{name}: address mismatch')
        if int(row['expected_width']) != width:
            errors.append(f'{name}: width mismatch')
        if parse_count(row['expected_value_hex']) != value:
            errors.append(f'{name}: value mismatch')
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', default='source/minimal_os/init/efi_output_init.asm')
    ap.add_argument('--vectors', default='tests/static/efi_output_init_vectors.csv')
    args = ap.parse_args()

    source = resolve_path(args.source)
    vectors = resolve_path(args.vectors)
    source_errors = verify_source(source)
    vector_errors = verify_vectors(vectors)
    errors = source_errors + vector_errors

    print(f'source: {source}')
    print(f'vectors: {vectors}')
    print(f'source_error_count: {len(source_errors)}')
    print(f'vector_error_count: {len(vector_errors)}')
    if errors:
        print('status: FAIL')
        for e in errors:
            print(f'ERROR: {e}')
        return 1
    print('clear_range: 0x3FC0 through before 0x3FFA')
    print('active_optional_preloads: none')
    print('forbidden_timer_writes: none')
    print('status: PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
