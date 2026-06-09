#!/usr/bin/env python3
"""Verify fuel SLICE-0 bench-result capture CSV.

This verifier checks structure, required rows, allowed result states, measurement
requirements, and implementation gates. It does not claim bench tests passed.
Default rows should remain not_run until real scope/logic-analyzer/ALDL data is
entered.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

REQUIRED_FIELDS = [
    "proof_id", "vector_name", "commanded_counts_hex", "commanded_counts_dec",
    "expected_pw_ms", "measured_pw_ms", "measured_pulse_present",
    "measured_register_or_debug_counts", "aldl_counts_match", "scope_channel",
    "test_condition", "pass_fail", "evidence_file", "notes",
]

ALLOWED_STATUS = {"not_run", "pass", "fail", "partial"}

REQUIRED_ROWS = [
    ("FUEL-001", "zero", "$0000", "0", "0.000000"),
    ("FUEL-001", "one_ms", "$0042", "66", "1.007080"),
    ("FUEL-001", "two_ms", "$0083", "131", "1.998901"),
    ("FUEL-001", "three_ms", "$00C5", "197", "3.005981"),
    ("FUEL-001", "four_ms", "$0106", "262", "3.997803"),
    ("FUEL-002", "three_ms", "$00C5", "197", "3.005981"),
    ("FUEL-003", "zero", "$0000", "0", "0.000000"),
    ("FUEL-004", "dropout_zero", "$0000", "0", "0.000000"),
]


def tolerance(expected_ms: float) -> float:
    return max(0.05, expected_ms * 0.03)


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != REQUIRED_FIELDS:
            raise ValueError(f"field mismatch: got {reader.fieldnames}, expected {REQUIRED_FIELDS}")
        return list(reader)


def proof_passed(rows: list[dict[str, str]], proof_id: str) -> bool:
    selected = [r for r in rows if r["proof_id"] == proof_id]
    return bool(selected) and all(r["pass_fail"] == "pass" for r in selected)


def verify(path: Path) -> list[str]:
    errors: list[str] = []
    rows = load_rows(path)
    by_key = {(r["proof_id"], r["vector_name"]): r for r in rows}

    if len(rows) != len(REQUIRED_ROWS):
        errors.append(f"expected {len(REQUIRED_ROWS)} rows, found {len(rows)}")

    for proof_id, vector, count_hex, count_dec, expected_ms in REQUIRED_ROWS:
        key = (proof_id, vector)
        if key not in by_key:
            errors.append(f"missing required row: {proof_id}/{vector}")
            continue
        row = by_key[key]
        if row["commanded_counts_hex"].upper() != count_hex:
            errors.append(f"{proof_id}/{vector}: commanded_counts_hex mismatch")
        if row["commanded_counts_dec"] != count_dec:
            errors.append(f"{proof_id}/{vector}: commanded_counts_dec mismatch")
        if row["expected_pw_ms"] != expected_ms:
            errors.append(f"{proof_id}/{vector}: expected_pw_ms mismatch")

    if len(by_key) != len(rows):
        errors.append("duplicate proof_id/vector_name rows detected")

    for row in rows:
        status = row["pass_fail"]
        if status not in ALLOWED_STATUS:
            errors.append(f"{row['proof_id']}/{row['vector_name']}: invalid pass_fail {status!r}")

        if status == "pass":
            has_pw = bool(row["measured_pw_ms"].strip())
            has_counts = bool(row["measured_register_or_debug_counts"].strip())
            if not (has_pw or has_counts):
                errors.append(f"{row['proof_id']}/{row['vector_name']}: pass requires measured_pw_ms or measured_register_or_debug_counts")

            if has_pw:
                try:
                    expected = float(row["expected_pw_ms"])
                    measured = float(row["measured_pw_ms"])
                except ValueError:
                    errors.append(f"{row['proof_id']}/{row['vector_name']}: measured/expected PW must be numeric")
                else:
                    tol = tolerance(expected)
                    if abs(measured - expected) > tol:
                        errors.append(
                            f"{row['proof_id']}/{row['vector_name']}: measured_pw_ms {measured:.6f} outside tolerance ±{tol:.6f} of {expected:.6f}"
                        )

            if row["proof_id"] == "FUEL-004":
                condition = (row["test_condition"] + " " + row["notes"] + " " + row["evidence_file"]).lower()
                if "dropout" not in condition and "unsafe" not in condition:
                    errors.append("FUEL-004 pass requires dropout/unsafe path evidence in test_condition/notes/evidence_file")

        if row["proof_id"] == "FUEL-004" and row["pass_fail"] == "pass":
            if "bench-only" in row["test_condition"].lower() and "dropout" not in row["test_condition"].lower():
                errors.append("FUEL-004 cannot pass from SLICE-0 bench-only vector testing alone")

    # FUEL-003 may remain partial when only the zero vector was run.
    f3 = by_key.get(("FUEL-003", "zero"))
    if f3 and f3["pass_fail"] == "partial":
        notes = (f3["notes"] + " " + f3["test_condition"]).lower()
        if "zero" not in notes and "vector" not in notes:
            errors.append("FUEL-003 partial should indicate zero-vector-only evidence")

    all_required_pass = all(proof_passed(rows, pid) for pid in ["FUEL-001", "FUEL-002", "FUEL-003", "FUEL-004"])
    text = "\n".join(
        " ".join(row.get(col, "") for col in REQUIRED_FIELDS).lower()
        for row in rows
    )
    if "slice-1 allowed" in text or "slice1 allowed" in text or "engine-runnable allowed" in text:
        if not all_required_pass:
            errors.append("SLICE-1/engine-runnable allowed claim present before FUEL-001..FUEL-004 are all pass")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="maps/bench/fuel_slice0_bench_results.csv")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    result_path = root / args.results
    try:
        errors = verify(result_path)
    except Exception as exc:
        print("FAIL: fuel SLICE-0 bench results verification")
        print(f" - {exc}")
        return 1

    if errors:
        print("FAIL: fuel SLICE-0 bench results verification")
        for error in errors:
            print(f" - {error}")
        return 1

    print("PASS: fuel SLICE-0 bench results verification")
    print(" - required FUEL-001 through FUEL-004 rows present")
    print(" - result states are controlled")
    print(" - pass rows require measurements")
    print(" - FUEL-004 cannot pass from SLICE-0 vector testing alone")
    print(" - SLICE-1 allowed claim is gated by FUEL-001..FUEL-004 pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
