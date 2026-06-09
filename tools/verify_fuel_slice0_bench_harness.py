#!/usr/bin/env python3
"""Static verifier for the fuel SLICE-0 bench harness.

The harness is bench-only and not engine-runnable. It may only load fixed EFI
PW vectors into D and call EFI_PW_WRITE. It must not own hardware writes,
scheduler/reset/crank/run behavior, ALDL packet format, sensors, VE tables, or
fuel math.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

EXPECTED_VECTORS = {
    "zero": ("$0000", "0", "0.000000"),
    "one_ms": ("$0042", "66", "1.007080"),
    "two_ms": ("$0083", "131", "1.998901"),
    "three_ms": ("$00C5", "197", "3.005981"),
    "four_ms": ("$0106", "262", "3.997803"),
}

EXPECTED_LABELS = {
    "FUEL_SLICE0_WRITE_ZERO": "$0000",
    "FUEL_SLICE0_WRITE_1MS": "$0042",
    "FUEL_SLICE0_WRITE_2MS": "$0083",
    "FUEL_SLICE0_WRITE_3MS": "$00C5",
    "FUEL_SLICE0_WRITE_4MS": "$0106",
}

FORBIDDEN_ADDRESS_TOKENS = [
    "$3FE8", "$3FE6", "$3FF6", "$3FDC", "L3062", "$3062",
]

FORBIDDEN_SYMBOLS = [
    "SPARK_WRITE", "IAC_WRITE", "SPARK_", "IAC_PHASE", "IAC_OUTPUT",
    "RESET_VECTOR", "SCHEDULER", "CRANK_LOOP", "RUN_LOOP",
]

FORBIDDEN_SENSOR_OR_MATH = [
    "MAP", "TPS", "CTS", "COOLANT", "VE_", "AIRFLOW", "BPW_CALC",
    "FUEL_MATH", "MUL", "FDIV", "IDIV",
]


def strip_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        lines.append(line.split(";", 1)[0])
    return "\n".join(lines)


def fail(msgs: list[str], message: str) -> None:
    msgs.append(message)


def verify_harness(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    code = strip_comments(text)
    upper_text = text.upper()
    upper_code = code.upper()

    for required in ["BENCH-ONLY", "NOT ENGINE-RUNNABLE", "NOT SCHEDULER-OWNED", "NOT RESET-VECTOR-OWNED"]:
        if required not in upper_text:
            fail(errors, f"missing explicit marker: {required}")

    if re.search(r"\bSTD\s+(?:\$3FCE|L3FCE)\b", upper_code):
        fail(errors, "harness directly stores to $3FCE/L3FCE")

    if re.search(r"\b(?:STAA|STAB|STD|STS|STX|STY)\s+(?:\$3FCE|L3FCE)\b", upper_code):
        fail(errors, "harness contains direct write to $3FCE/L3FCE")

    for token in FORBIDDEN_ADDRESS_TOKENS:
        if token in upper_code:
            fail(errors, f"forbidden hardware token in code: {token}")

    for token in FORBIDDEN_SYMBOLS:
        if token in upper_code:
            fail(errors, f"forbidden ownership/symbol token in code: {token}")

    for token in FORBIDDEN_SENSOR_OR_MATH:
        if token in upper_code:
            fail(errors, f"forbidden sensor/math token in code: {token}")

    calls = re.findall(r"\bJSR\s+([A-Z0-9_]+)", upper_code)
    if not calls:
        fail(errors, "no JSR calls found")
    for call in calls:
        if call != "EFI_PW_WRITE":
            fail(errors, f"unexpected JSR target: {call}")

    for label, vector in EXPECTED_LABELS.items():
        pattern = rf"{label}:\s*\n\s*LDD\s+#\{vector}\s*\n\s*JSR\s+EFI_PW_WRITE\s*\n\s*RTS"
        if not re.search(pattern, upper_code, flags=re.MULTILINE):
            fail(errors, f"missing or malformed vector routine: {label} -> {vector}")

    return errors


def verify_vectors(path: Path) -> list[str]:
    errors: list[str] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    by_name = {row["name"]: row for row in rows}
    if set(by_name) != set(EXPECTED_VECTORS):
        fail(errors, f"vector names mismatch: got {sorted(by_name)}, expected {sorted(EXPECTED_VECTORS)}")
        return errors
    for name, (hexv, decv, msv) in EXPECTED_VECTORS.items():
        row = by_name[name]
        if row["counts_hex"].upper() != hexv:
            fail(errors, f"{name}: counts_hex {row['counts_hex']} != {hexv}")
        if row["counts_dec"] != decv:
            fail(errors, f"{name}: counts_dec {row['counts_dec']} != {decv}")
        if row["pw_ms"] != msv:
            fail(errors, f"{name}: pw_ms {row['pw_ms']} != {msv}")
        if row["allowed_in_engine_runtime"].lower() != "no":
            fail(errors, f"{name}: allowed_in_engine_runtime must be no")
    return errors


def verify_writer(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        fail(errors, f"EFI writer not found: {path}")
        return errors
    text = path.read_text(encoding="utf-8")
    code = strip_comments(text).upper()
    if "EFI_PW_WRITE" not in code:
        fail(errors, "EFI writer file does not contain EFI_PW_WRITE")
    if not re.search(r"\bSTD\s+(?:L3FCE|\$3FCE)\b", code):
        fail(errors, "EFI writer file does not contain STD L3FCE/$3FCE")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", default="source/minimal_os/fuel/slice0_bench_harness.asm")
    parser.add_argument("--vectors", default="tests/static/fuel_slice0_bench_vectors.csv")
    parser.add_argument("--writer", default="source/minimal_os/fuel/efi_pw_writer.asm")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    harness = root / args.harness
    vectors = root / args.vectors
    writer = root / args.writer

    errors: list[str] = []
    errors += verify_harness(harness)
    errors += verify_vectors(vectors)
    errors += verify_writer(writer)

    if errors:
        print("FAIL: fuel SLICE-0 bench harness verification")
        for error in errors:
            print(f" - {error}")
        return 1

    print("PASS: fuel SLICE-0 bench harness verification")
    print(" - bench-only markers present")
    print(" - fixed vectors match CSV")
    print(" - harness calls EFI_PW_WRITE only")
    print(" - no direct $3FCE/L3FCE store in harness")
    print(" - forbidden spark/IAC hardware tokens absent from code")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
