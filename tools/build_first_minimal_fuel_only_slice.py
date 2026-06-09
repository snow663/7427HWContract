#!/usr/bin/env python3
"""Build the first minimal fuel-only runnable slice boundary.

This is contract/planning only. It defines SLICE-0/1/2 allowed scope,
bench gates, and forbidden hardware authority. It does not implement runtime ASM
or fuel-only runnable code.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

FIELDS = [
    "slice_level", "stage", "module", "submodule", "input_required",
    "state_required", "calibration_required", "output_produced", "hardware_write",
    "hardware_address", "allowed_now", "required_bench_proof", "dropout_behavior",
    "aldl_debug_required", "implementation_file_allowed", "forbidden_dependency",
    "confidence", "notes",
]

ROWS = [
    ["SLICE-0", "reset_output_safe_entry", "boot", "safe_entry", "reset state", "output_safe_state", "none", "all outputs safe; fuel zero", "EFI_PW_WRITE zero only if used", "$3FCE", "yes_bench_harness_only", "none before static definition", "$3FCE=0", "yes", "contract_only; future bench harness may be separate", "spark writer; IAC writer; EST authority; L3062", "high_planning", "Fuel output bench harness only; not engine runnable."],
    ["SLICE-0", "force_fuel_zero", "fuel", "efi_pw_write", "fixed zero vector", "fuel_enable_no_fuel_gate", "none", "D=$0000", "EFI_PW_WRITE", "$3FCE", "yes_bench_harness_only", "none before static definition", "$3FCE=0", "yes", "contract_only; future bench harness may be separate", "nonzero fuel without gate", "high_planning", "Used to prove no-pulse / safe zero path."],
    ["SLICE-0", "force_3ms_test_vector", "fuel", "efi_pw_write", "fixed $00C5 vector", "bench_harness_state", "none", "D=$00C5 test vector", "EFI_PW_WRITE", "$3FCE", "yes_bench_harness_only", "none before static definition; FUEL-002 for proof", "$3FCE=0", "yes", "contract_only; future bench harness may be separate", "engine runnable use before FUEL-001..004", "high_planning", "$00C5 ≈ 3.006 ms vector; not engine-runnable."],
    ["SLICE-0", "debug_pw_visibility", "aldl_debug", "fuel_pw_debug", "$3FCE raw counts", "efi_pw_command", "none", "$3FCE raw and ms visible", "none", "none", "yes_bench_harness_only", "FUEL-001; FUEL-002", "debug shows zero after dropout", "yes", "contract_only", "ALDL write authority", "high_planning", "Expose $3FCE counts and EFI_PW_ms = counts/65.536."],
    ["SLICE-0", "dropout_forces_zero", "fuel", "dropout_gate", "dropout state", "minimal_dropout_state; efi_pw_command", "none", "D=$0000", "EFI_PW_WRITE zero only", "$3FCE", "yes_bench_harness_only", "FUEL-004 for proof", "$3FCE=0", "yes", "contract_only; future bench harness may be separate", "continued nonzero fuel on dropout", "high_planning", "SLICE-0 must not be engine-runnable."],
    ["SLICE-0", "engine_runnable_flag", "boot", "slice_level", "none", "slice_level_state", "none", "not engine runnable", "none", "none", "yes", "none", "not applicable", "yes", "contract_only", "engine run mode", "high_policy", "SLICE-0 is explicitly not engine-runnable."],

    ["SLICE-1", "ref_rpm_valid_gate", "ref_rpm_period", "period_valid", "REF/DRP period", "ref_drp_valid; rpm_valid; first_period_valid", "none", "fuel event permitted only after valid RPM/ref", "none", "none", "blocked_until_fuel_proofs_pass", "FUEL-001; FUEL-002; FUEL-003; FUEL-004", "$3FCE=0 when invalid", "yes", "no until FUEL-001..004 pass", "spark/IAC authority", "high_planning", "Limited engine-runnable skeleton gate."],
    ["SLICE-1", "crank_run_fuel_enable_gate", "fuel", "mode_gate", "crank/run qualification", "crank_run_qualification; fuel_enable_no_fuel_gate", "none", "fuel enable state", "none", "none", "blocked_until_fuel_proofs_pass", "FUEL-001; FUEL-002; FUEL-003; FUEL-004", "$3FCE=0 when not enabled", "yes", "no until FUEL-001..004 pass", "nonzero fuel before enable", "high_planning", "Nonzero fuel gated by crank/run and fuel enable."],
    ["SLICE-1", "no_fuel_dfco_zero_gate", "fuel", "dfco_no_fuel", "DFCO/no-fuel gate", "dfco_zero_gate; fuel_enable_no_fuel_gate", "none", "D=$0000 when gate active", "EFI_PW_WRITE", "$3FCE", "blocked_until_fuel_proofs_pass", "FUEL-003; FUEL-004", "$3FCE=0", "yes", "no until FUEL-001..004 pass", "bypass zero gate", "high_planning", "No-fuel gate is mandatory."],
    ["SLICE-1", "fixed_or_simple_pw_source", "fuel", "pw_source", "fixed PW or simple table value", "sync_bpw_source or minimal_fixed_pw", "optional fixed test calibration only", "D = fixed/simple PW counts", "none before output stage", "none", "blocked_until_fuel_proofs_pass", "FUEL-001; FUEL-002; FUEL-003; FUEL-004", "source ignored; D=0", "yes", "no until FUEL-001..004 pass", "full VE strategy; tuning changes", "medium_planning", "May be fixed/test PW or simple table PW; not full fuel strategy."],
    ["SLICE-1", "efi_pw_write_only", "fuel", "efi_pw_write", "D pulsewidth counts", "efi_pw_command", "none", "D -> $3FCE", "EFI_PW_WRITE", "$3FCE", "blocked_until_fuel_proofs_pass", "FUEL-001; FUEL-002; FUEL-003; FUEL-004", "$3FCE=0", "yes", "no until FUEL-001..004 pass", "$3FE8;$3FE6;$3FF6;$3FDC;L3062", "high_policy", "Only hardware write allowed in SLICE-1."],
    ["SLICE-1", "aldl_pw_visibility", "aldl_debug", "fuel_debug", "$3FCE raw and ms", "efi_pw_command", "none", "debug visibility", "none", "none", "blocked_until_fuel_proofs_pass", "FUEL-001; FUEL-002; ALDL-001", "dropout visible", "yes", "no until FUEL-001..004 pass", "ALDL packet implementation unless separately scoped", "high_planning", "Debug visibility required for first runnable slice."],
    ["SLICE-1", "dropout_zero", "fuel", "dropout_safe_state", "dropout state / missing REF", "minimal_dropout_state; ref_drp_valid", "none", "D=$0000", "EFI_PW_WRITE", "$3FCE", "blocked_until_fuel_proofs_pass", "FUEL-004; BOOT-003", "$3FCE=0", "yes", "no until FUEL-001..004 pass", "continued nonzero fuel on dropout", "high_planning", "Runtime dropout must force zero fuel."],
    ["SLICE-1", "no_spark_iac_authority", "spark_iac", "forbidden_authority", "none", "none", "none", "no spark/IAC control", "none", "none", "yes", "SPARK-001..006 and IAC-001..009 remain unresolved", "spark/IAC stay safe/observed only", "yes", "contract_only", "$3FE8;$3FE6;$3FF6;$3FDC;L3062;SPARK_WRITE;IAC_WRITE", "high_policy", "Spark and IAC may be observed only, not controlled."],

    ["SLICE-2", "rpm_input", "fuel", "speed_density_input", "RPM", "rpm_valid; drp_ref_period_basis", "none", "fuel RPM input", "none", "none", "future_after_slice1", "FUEL-001..004 plus RPM proof", "$3FCE=0 when invalid", "yes", "future_contract_only", "spark/IAC authority", "medium_planning", "Open-loop speed-density input."],
    ["SLICE-2", "map_input", "fuel", "speed_density_input", "MAP", "map_sensor", "MAP scaling calibration", "load input", "none", "none", "future_after_slice1", "sensor acquisition proof", "$3FCE=0 if invalid", "yes", "future_contract_only", "unproven sensor scaling", "medium_planning", "MAP/load input for VE."],
    ["SLICE-2", "cts_input", "fuel", "warmup_input", "CTS", "cts_sensor", "CTS scaling / warmup tables", "coolant input", "none", "none", "future_after_slice1", "sensor acquisition proof", "$3FCE=0 or safe default if invalid", "yes", "future_contract_only", "unproven sensor scaling", "medium_planning", "Coolant input for warmup/crank."],
    ["SLICE-2", "battery_voltage_input", "fuel", "deadtime_input", "battery voltage", "L00A7", "deadtime/battery correction", "deadtime correction input", "none", "none", "future_after_slice1", "battery scaling proof", "safe correction or zero", "yes", "future_contract_only", "unproven deadtime", "medium_planning", "Battery voltage affects deadtime/PW correction."],
    ["SLICE-2", "baro_altitude_basis", "fuel", "airflow_input", "baro / altitude", "baro_basis", "baro correction", "air density/load basis", "none", "none", "future_after_slice1", "baro source proof", "safe default", "yes", "future_contract_only", "unproven baro source", "medium_planning", "Needed for real speed-density behavior."],
    ["SLICE-2", "ve_base_airflow_input", "fuel", "base_airflow", "VE/base airflow", "ve_table_input", "VE/base airflow calibration", "base fuel mass input", "none", "none", "future_after_slice1", "calibration source mapping and sensor proof", "safe default or zero", "yes", "future_contract_only", "calibration cannot make runnable by itself", "medium_planning", "Calibration does not permit runnable code by itself."],
    ["SLICE-2", "injector_flow_constant", "fuel", "injector_model", "injector flow", "ifrcal", "injector flow constant", "fuel mass to PW conversion", "none", "none", "future_after_slice1", "injector output proof", "safe default or zero", "yes", "future_contract_only", "tuning changes", "medium_planning", "Injector flow constant required for real PW math."],
    ["SLICE-2", "deadtime_battery_correction", "fuel", "injector_model", "deadtime correction", "minimal_deadtime_state; L00A7", "deadtime table", "PW correction", "none", "none", "future_after_slice1", "deadtime behavior proof", "safe correction or zero", "yes", "future_contract_only", "unverified deadtime behavior", "medium_planning", "Deadtime/battery correction required before final fuel math."],
    ["SLICE-2", "low_pw_correction", "fuel", "injector_model", "low-PW transfer", "minimal_low_pw_tf_state", "low-PW transfer table", "PW correction", "none", "none", "future_after_slice1", "FUEL-005 plus low-PW bench validation", "safe correction or zero", "yes", "future_contract_only", "unverified low-PW correction", "medium_planning", "Low-PW correction needed due injector floor/nonlinearity."],
    ["SLICE-2", "warmup_afterstart_crank", "fuel", "enrichment", "warmup/afterstart/crank fuel", "warmup_state; crank_state", "warmup/afterstart/crank tables", "enrichment modifier", "none", "none", "future_after_slice1", "calibration source mapping", "safe default or zero", "yes", "future_contract_only", "strategy baggage promotion", "medium_planning", "Required for engine-runnable open-loop behavior."],
    ["SLICE-2", "target_afr_stoich", "fuel", "target_afr", "target AFR / stoich basis", "target_afr_stoich_state", "target AFR/stoich calibration", "fuel mass target", "none", "none", "future_after_slice1", "calibration source mapping", "safe default or zero", "yes", "future_contract_only", "tuning changes", "medium_planning", "Target AFR/stoich basis required for speed-density math."],

    ["ALL", "forbidden_outputs", "spark_iac", "forbidden_hardware", "none", "none", "none", "none", "none", "$3FE8;$3FE6;$3FF6;$3FDC;L3062", "no", "spark/IAC bench gates unresolved", "outputs safe/observed only", "yes", "never in fuel-only slice", "SPARK_WRITE;IAC_WRITE;EST/bypass authority;IAC phase/output", "high_policy", "Fuel-only slice cannot touch spark or IAC hardware."],
    ["ALL", "calibration_guard", "calibration", "guardrail", "calibration tables", "none", "calibration source index", "none", "none", "none", "no", "not a bench proof", "no effect", "yes", "contract_only", "calibration cannot make slice runnable", "high_policy", "Calibration presence alone cannot promote runnable status."],
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root() / p


def write_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        writer.writerows(ROWS)


def write_md(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First Minimal Fuel-Only Runnable Slice",
        "",
        "## Purpose",
        "",
        "Define the first constrained runtime slice that may eventually command fuel through `$3FCE`.",
        "",
        "This document does not implement runtime code. It defines the allowed implementation envelope and bench gates.",
        "",
        "## Output Boundary",
        "",
        "The only allowed hardware-facing fuel output is:",
        "",
        "```text",
        "D = EFI pulsewidth counts in 1/65536 second units",
        "STD $3FCE",
        "```",
        "",
        "through `EFI_PW_WRITE`.",
        "",
        "## Required Bench Gate",
        "",
        "Before any engine-runnable fuel-only implementation:",
        "",
        "- `FUEL-001` must prove `$3FCE` raw counts correlate to commanded PW.",
        "- `FUEL-002` must prove `$00C5 ≈ 3.006 ms`.",
        "- `FUEL-003` must prove zero/no-fuel gate forces `$3FCE = 0`.",
        "- `FUEL-004` must prove dropout/unsafe state forces `$3FCE = 0`.",
        "",
        "No engine-runnable fuel-only implementation is allowed until `FUEL-001` through `FUEL-004` have actually passed on the bench, unless the slice is marked bench-harness-only and cannot run an engine.",
        "",
        "## Slice Levels",
        "",
        "### SLICE-0: fuel output bench harness",
        "",
        "```text",
        "purpose: prove $3FCE write path only",
        "engine runnable: no",
        "allowed output: fixed $3FCE test vectors only",
        "required bench proofs: none before static definition",
        "```",
        "",
        "### SLICE-1: fuel-only crank/run skeleton",
        "",
        "```text",
        "purpose: zero-safe fuel control with fixed/calculated PW",
        "engine runnable: limited",
        "required bench proofs: FUEL-001 through FUEL-004",
        "```",
        "",
        "### SLICE-2: open-loop speed-density fuel",
        "",
        "```text",
        "purpose: MAP/RPM/CTS/battery based fuel",
        "engine runnable: yes, fuel-only",
        "required: sensor acquisition, VE/input tables, deadtime/low-PW handling",
        "```",
        "",
        "## Forbidden Scope",
        "",
        "This slice must not implement spark authority, IAC authority, transmission, EGR, EVAP, or emissions strategy.",
        "",
        "Spark and IAC may be observed through debug only.",
        "",
        "Forbidden hardware/actions:",
        "",
        "```text",
        "no $3FE8",
        "no $3FE6",
        "no $3FF6",
        "no $3FDC",
        "no L3062",
        "no SPARK_WRITE",
        "no IAC_WRITE",
        "no EST/bypass authority code",
        "no IAC phase/output code",
        "```",
        "",
        "## Slice Table",
        "",
        "| Slice | Stage | Output | Hardware write | Allowed now | Required bench proof | Notes |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in ROWS:
        lines.append(f"| `{r[0]}` | {r[1]} | {r[7]} | {r[8]} `{r[9]}` | {r[10]} | {r[11]} | {r[17]} |")
    lines += [
        "",
        "## Current Implementation Decision",
        "",
        "Valid branches after this contract:",
        "",
        "```text",
        "bench FUEL-001 through FUEL-004",
        "implement SLICE-0 bench harness first, if explicitly bench-harness-only and not engine runnable",
        "```",
        "",
        "Do not implement `SLICE-1` until the fuel proof rows are actually satisfied.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-md", required=True)
    p.add_argument("--out-csv", required=True)
    args = p.parse_args()
    write_csv(resolve(args.out_csv))
    write_md(resolve(args.out_md))
    print(f"FIRST_MINIMAL_FUEL_ONLY_SLICE: wrote {len(ROWS)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
