#!/usr/bin/env python3
"""Build the minimal OS boot / safe-state boundary artifacts.

This is planning only. It does not create reset-vector code, scheduler ASM,
startup implementation, or new hardware writers.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

FIELDS = [
    "boot_stage", "state_name", "trigger_source", "module", "submodule",
    "state_seeded", "input_required", "output_default", "hardware_write",
    "hardware_address", "allowed_now", "bench_gated", "forbidden_until",
    "safe_value", "dropout_value", "source_contract_dependency",
    "minimal_os_required", "confidence", "notes",
]

ROWS = [
    ["reset_entry", "RESET_ENTRY", "power-on/reset vector", "boot", "entry", "boot state = reset-entry", "reset cause / watchdog cause / power state", "all runtime control outputs inactive", "no", "none", "planning_only", "yes", "BOOT_SAFE_STATE implementation pass", "no runtime control outputs active", "re-enter RESET_ENTRY or WATCHDOG_SAFE_STATE", "MINIMAL_OS_EXECUTION_SCHEDULER.md; MINIMAL_OS_MODULE_BOUNDARY.md", "yes", "high_contract", "Entry state only; no reset ASM is created."],
    ["asic_clear", "ASIC_WINDOW_CLEAR", "RESET_ENTRY", "boot", "asic_window", "ASIC/window clear policy selected", "hardware window map / init contract", "candidate output/window safe clear", "candidate", "ASIC/window registers", "no_runtime_code_yet", "yes", "exact reset writes and boot sequence are proven", "safe/inactive output windows", "safe/inactive output windows", "EFI_OUTPUT_INIT_STATE.md; EFI_OUTPUT_INIT_ROUTINE.md; MINIMAL_OS_EXECUTION_SCHEDULER.md", "yes", "medium_static", "Documents dependency only; exact writes deferred to implementation/bench proof."],
    ["output_defaults", "OUTPUT_SAFE_DEFAULTS", "after ASIC/window clear", "boot", "safe_defaults", "safe-output defaults selected", "reset state; no valid REF/DRP yet", "fuel zero; spark no-authority intent; IAC hold/software-only", "candidate", "mixed", "no_runtime_code_yet", "yes", "BOOT_SAFE_STATE implementation pass and hardware bench proof", "all outputs safe/inactive", "all outputs safe/inactive", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "yes", "high_contract", "Top-level defaults before any runtime module is allowed to command hardware."],
    ["ram_seed", "RAM_STATE_SEED", "after output defaults", "boot", "ram_state", "minimal runtime state seeded", "known reset state; retained/NVM validity flags", "software state initialized; hardware outputs unchanged", "no", "none", "planning_only", "yes", "MINIMAL_OS_STATE_VARIABLES defines exact RAM map", "known software defaults", "known software defaults", "MINIMAL_OS_MODULE_BOUNDARY.md; MINIMAL_OS_EXECUTION_SCHEDULER.md", "yes", "medium_contract", "Seeds software state only; no hardware writer."],

    ["fuel_zero", "FUEL_SAFE_STATE", "RESET_ENTRY / dropout / no-fuel gate", "fuel", "safe_zero", "fuel enable/no-fuel state = disabled", "no-fuel gate; valid PW intent absent", "$3FCE zero/no-pulse intent", "yes_provisional_via_contract", "$3FCE", "yes_provisional", "yes", "bench confirms $3FCE output behavior and units", "$3FCE = 0 / no pulse", "$3FCE = 0 / no pulse", "EFI_PW_3FCE_CONTRACT.md; EFI_PW_UNITS.md; MINIMAL_EFI_PW_WRITER.md; FUEL_MINIMAL_MODULE_INPUTS.md", "yes", "high_static_bench_pending", "$3FCE may only be written through EFI_PW_WRITE or documented init-clear path."],
    ["fuel_nonzero_block", "FUEL_SAFE_STATE", "before fuel enable/calculation", "fuel", "nonzero_block", "nonzero fuel disabled", "valid sensors; crank/run; fuel calc; no-fuel gate clear", "nonzero fuel output blocked", "no", "$3FCE", "no", "yes", "fuel calculation, no-fuel gate, and $3FCE bench validation complete", "nonzero blocked", "zero/no-pulse", "FUEL_MINIMAL_MODULE_INPUTS.md; EFI_PW_3FCE_CONTRACT.md", "yes", "high_policy", "Nonzero fuel output is not a boot default."],
    ["dfco_gate_preserve", "FUEL_SAFE_STATE", "reset/crank/run/dropout", "fuel", "no_fuel_gate", "DFCO/no-fuel gate represented", "DFCO/no-fuel permission; crank/run status", "D=0 can be forced", "candidate", "$3FCE", "yes_provisional_via_contract", "yes", "DFCO zero-gate behavior validated", "D=0 path available", "D=0 path forced", "FUEL_MINIMAL_MODULE_INPUTS.md; MINIMAL_OS_EXECUTION_SCHEDULER.md", "yes", "medium_static", "Zero gate must survive boot and dropout design."],

    ["spark_safe", "SPARK_SAFE_STATE", "RESET_ENTRY / REF_DRP_WAIT / dropout", "spark", "safe_intent", "spark safe/no-authority intent", "no valid REF/DRP; no run qualification; bypass/EST authority unknown", "no direct ASIC timing writes", "forbidden", "$3FE8/$3FE6/$3FF6/$3FDC", "no", "yes", "spark handoff, rolling seed, and physical EST/bypass behavior bench-proven", "no-authority / bypass-intent only", "safe/bypass/dropout intent only", "SPARK_MINIMAL_MODULE_INPUTS.md; SPARK_BYPASS_EST_TRANSITION.md; SPARK_ROLLING_STATE_MODEL.md", "yes", "high_policy", "Spark output is not writer-safe; intent state only."],
    ["spark_roll_seed", "SPARK_SAFE_STATE", "RESET_ENTRY / first valid period", "spark", "rolling_seed", "rolling timing seed candidate marked unresolved", "first valid DRP/ref period; init state", "rolling state held/uncommitted", "forbidden", "$3FF6/$3FDC", "no", "yes", "$3FF6/$3FDC first-event seed behavior bench-proven", "no direct seed write", "no direct seed write", "SPARK_INIT_STATE.md; SPARK_ROLLING_STATE_MODEL.md", "yes_future", "high_static", "Seed requirement is documented but not implemented."],
    ["spark_bypass_safe", "SPARK_SAFE_STATE", "RESET_ENTRY / crank/run transition", "spark", "bypass_est_authority", "bypass/EST authority state is safe/unknown", "bypass/EST input state; run qualification", "no physical authority action", "forbidden", "EST/bypass hardware", "no", "yes", "physical EST/bypass authority code bench-proven", "remain safe/no-authority", "safe/bypass/dropout intent", "SPARK_BYPASS_EST_TRANSITION.md; source/minimal_os/spark/README.md", "yes", "high_policy", "No physical EST/bypass code in boot-safe contract."],

    ["iac_safe", "IAC_SAFE_STATE", "RESET_ENTRY / REF_DRP_WAIT / dropout", "iac_idle", "software_hold", "IAC software state seed selected", "reset-in-work; bad-shutdown; L4EB0; Enable/protection", "software seed/hold only", "forbidden", "L3062", "no", "yes", "physical direction, Enable, park, cadence, and A/B mapping bench-proven", "software hold / no motion", "hold software state or safe target only", "IAC_MINIMAL_MODULE_INPUTS.md; IAC_INIT_PARK_CONTRACT.md; IAC_ENABLE_FAULT_GATE_CONTRACT.md", "yes", "high_policy", "No physical IAC motion or latch write."],
    ["iac_seed", "IAC_SAFE_STATE", "RAM_STATE_SEED", "iac_idle", "position_seed", "L0007/L0008/L0009/L000A policy selected", "retained validity; bad shutdown; reset-in-work", "software state seeded; output unchanged", "no", "L3062", "no", "yes", "IAC park/reset behavior bench-proven", "seed only", "hold or reset policy", "IAC_INIT_PARK_CONTRACT.md; source/minimal_os/iac/README.md", "yes", "high_static", "Software state seed only; does not command phase or Enable."],
    ["iac_motion_block", "IAC_SAFE_STATE", "before bench gates resolved", "iac_idle", "motion_block", "physical motion blocked", "Enable; direction; cadence; A/B mapping; seed-valid state", "no phase output", "forbidden", "L3062", "no", "yes", "all IAC physical gates proven", "no motion", "hold/no motion", "IAC_PHASE_SEQUENCE_CONTRACT.md; IAC_ENABLE_FAULT_GATE_CONTRACT.md; IAC_IDLE_AIR_OUTPUT_CONTRACT.md", "yes", "high_policy", "Output path is mapped but not implementation-ready."],

    ["wait_for_ref", "REF_DRP_WAIT", "after reset defaults", "scheduler", "ref_wait", "RPM/period invalid", "no valid REF/DRP", "fuel/spark run outputs blocked; IAC no motion", "no", "mixed", "planning_only", "yes", "valid REF/DRP capture behavior proven", "wait with safe outputs", "dropout safe outputs", "MINIMAL_OS_EXECUTION_SCHEDULER.md; SPARK_TIMEBASE_PERIOD_CONTRACT.md", "yes", "high_contract", "No runtime control output before REF/DRP validity."],
    ["crank_qualify", "CRANK_QUALIFY", "first crank/ref indication", "scheduler", "crank_gate", "crank qualification state", "REF/DRP present; crank/run flags; battery safe", "crank-safe input permissions", "no", "none", "planning_only", "yes", "crank/run qualification thresholds proven", "crank inputs may become valid", "return to REF_DRP_WAIT or DROPOUT_SAFE_STATE", "MINIMAL_OS_EXECUTION_SCHEDULER.md; SPARK_BYPASS_EST_TRANSITION.md", "yes", "medium_contract", "Crank qualification permits inputs, not unsupported outputs."],
    ["crank_outputs", "CRANK_QUALIFY", "crank qualified", "scheduler", "crank_outputs", "crank fuel intent, startup spark intent, IAC crank target selected", "RPM/period partial; coolant; battery; crank state", "fuel intent may be computed; spark/IAC intent only", "candidate", "$3FCE only", "fuel_only_provisional", "yes", "fuel $3FCE bench validation; spark/IAC output gates proven", "fuel zero or crank PW if intentionally enabled; spark/IAC intent only", "fuel zero; spark safe; IAC hold", "FUEL_MINIMAL_MODULE_INPUTS.md; SPARK_MINIMAL_MODULE_INPUTS.md; IAC_MINIMAL_MODULE_INPUTS.md", "yes", "medium_planning", "Only fuel has a provisional output path; spark/IAC remain intent-only."],
    ["first_period", "FIRST_PERIOD_VALID", "first valid REF/DRP period", "ref_rpm_period", "period_valid", "RPM/period basis becomes usable", "valid capture; no dropout", "RPM/timebase usable by modules", "no", "none", "planning_only", "yes", "period unit/update cadence proven", "timebase valid", "timebase invalidated", "SPARK_TIMEBASE_PERIOD_CONTRACT.md; MINIMAL_OS_EXECUTION_SCHEDULER.md", "yes", "high_contract", "First period does not by itself permit spark handoff."],
    ["run_qualify", "RUN_QUALIFY", "RPM/ref-event gates satisfied", "scheduler", "run_gate", "run qualification state", "valid period stream; crank/run threshold; dropout timer clear", "normal scheduler handoff permitted", "no", "none", "planning_only", "yes", "run criteria and safe transitions proven", "normal scheduler handoff", "dropout safe state", "MINIMAL_OS_EXECUTION_SCHEDULER.md; MINIMAL_OS_MODULE_BOUNDARY.md", "yes", "medium_contract", "Run qualification permits normal event scheduling but not forbidden writers."],
    ["normal_handoff", "RUN_QUALIFY", "run qualification true", "scheduler", "normal_scheduler_handoff", "normal scheduler ownership active", "sensor snapshot; period; module gates", "module events may run per scheduler contract", "event dispatch only", "no", "none", "planning_only", "yes", "runtime scheduler implementation pass", "scheduler dispatch allowed", "dropout safe state", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "yes", "medium_contract", "Still no runtime scheduler ASM in this pass."],

    ["dropout_entry", "DROPOUT_SAFE_STATE", "missing REF/DRP or unsafe runtime state", "watchdog_safe_state", "dropout_entry", "dropout state latched", "missing REF/DRP; invalid period; stalled loop; unsafe state", "modules forced to safe policy", "safe-state intent", "candidate", "mixed", "planning_only", "yes", "dropout thresholds and exact actions proven", "safe state", "safe state", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "yes", "high_contract", "Top-level dropout transition."],
    ["dropout_fuel", "DROPOUT_SAFE_STATE", "dropout state", "fuel", "fuel_zero", "fuel output forced no-pulse", "dropout flag / no-fuel gate", "$3FCE zero/no-pulse intent", "yes_provisional_via_contract", "$3FCE", "yes_provisional", "yes", "safe zero behavior and $3FCE bench validation", "$3FCE=0", "$3FCE=0", "EFI_PW_3FCE_CONTRACT.md; MINIMAL_EFI_PW_WRITER.md", "yes", "medium_static", "Only through fuel writer contract."],
    ["dropout_spark", "DROPOUT_SAFE_STATE", "dropout state", "spark", "spark_safe", "spark safe/bypass/dropout intent", "dropout flag; bypass/run invalid", "safe intent only", "forbidden", "$3FE8/$3FE6/$3FF6/$3FDC", "no", "yes", "physical spark safe/dropout behavior proven", "safe/bypass intent", "safe/bypass intent", "SPARK_MINIMAL_MODULE_INPUTS.md; SPARK_BYPASS_EST_TRANSITION.md", "yes", "high_policy", "No spark hardware write during dropout."],
    ["dropout_iac", "DROPOUT_SAFE_STATE", "dropout state", "iac_idle", "iac_hold", "IAC hold or safe target intent", "dropout flag; seed-valid state; Enable/protection", "software hold/safe target only", "forbidden", "L3062", "no", "yes", "safe IAC hold/park behavior and writer proven", "hold/no motion", "hold/no motion", "IAC_MINIMAL_MODULE_INPUTS.md; IAC_INIT_PARK_CONTRACT.md", "yes_future", "medium_policy", "No L3062 write during dropout."],
    ["watchdog_safe", "WATCHDOG_SAFE_STATE", "foreground loop stops / watchdog fault", "watchdog_safe_state", "watchdog_fallback", "watchdog-safe fallback entered", "loop-alive proof absent", "output-safe defaults requested", "candidate safe defaults", "candidate", "mixed", "no_runtime_code_yet", "yes", "watchdog safe-state implementation pass", "safe defaults", "safe defaults", "MINIMAL_OS_EXECUTION_SCHEDULER.md; MINIMAL_OS_MODULE_BOUNDARY.md", "yes", "medium_contract", "Defines fallback requirement without implementing watchdog ASM."],

    ["bench_gated_spark", "BENCH_GATED_OUTPUTS", "any spark output request", "spark", "bench_gate", "spark handoff blocked", "spark timing candidate", "no write", "none", "forbidden", "$3FE8/$3FE6/$3FF6/$3FDC", "no", "yes", "spark handoff bench classification complete", "blocked", "blocked", "SPARK_ASIC_HANDOFF_CONTRACT.md; SPARK_LA906_OUTPUT_SEQUENCE.md", "yes", "high_policy", "Spark output stays blocked."],
    ["bench_gated_iac", "BENCH_GATED_OUTPUTS", "any IAC output request", "iac_idle", "bench_gate", "IAC handoff blocked", "phase/enable candidate", "no write", "none", "forbidden", "L3062", "no", "yes", "IAC physical mapping/Enable/park/cadence proven", "blocked", "blocked", "IAC_IDLE_AIR_OUTPUT_CONTRACT.md; IAC_PHASE_SEQUENCE_CONTRACT.md; IAC_ENABLE_FAULT_GATE_CONTRACT.md", "yes", "high_policy", "IAC output stays blocked."],
    ["forbidden_outputs", "FORBIDDEN_OUTPUTS", "all boot/scheduler states", "boot", "forbidden_matrix", "forbidden write matrix active", "hardware address list", "forbidden outputs blocked", "none", "forbidden", "$3FE8/$3FE6/$3FF6/$3FDC/L3062", "no", "yes", "future bench classification and explicit writer contract", "blocked", "blocked", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "yes", "high_policy", "Central explicit forbidden list."],
    ["unknown_boot", "UNKNOWN", "unresolved boot ownership", "unknown", "unknown", "unknown state not assigned", "unclassified source/bench data", "unknown remains unknown", "none", "no", "unknown", "no", "yes", "future source trace assigns ownership", "unknown", "unknown", "MINIMAL_OS_BOOT_SAFE_STATE.md", "unknown", "low_unclassified", "Unknown boot ownership is listed, not guessed."],
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
        "# Minimal OS Boot / Safe-State Contract",
        "",
        "## Purpose",
        "",
        "Define the reset, crank, first-reference, run-qualification, and dropout-safe-state boundary for the minimal OS.",
        "",
        "This document does not implement reset code, scheduler code, or runtime ASM.",
        "",
        "## Source Dependencies",
        "",
        "- `MINIMAL_OS_EXECUTION_SCHEDULER.md`",
        "- `MINIMAL_OS_MODULE_BOUNDARY.md`",
        "- `EFI_OUTPUT_INIT_STATE.md`",
        "- `EFI_OUTPUT_INIT_ROUTINE.md`",
        "- `MINIMAL_EFI_PW_WRITER.md`",
        "- `SPARK_INIT_STATE.md`",
        "- `SPARK_BYPASS_EST_TRANSITION.md`",
        "- `SPARK_ROLLING_STATE_MODEL.md`",
        "- `IAC_INIT_PARK_CONTRACT.md`",
        "- `IAC_ENABLE_FAULT_GATE_CONTRACT.md`",
        "- `source/minimal_os/fuel/efi_pw_writer.asm`",
        "- `source/minimal_os/iac/README.md`",
        "- `source/minimal_os/spark/README.md`",
        "",
        "## Boot State Machine",
        "",
        "```text",
        "RESET_ENTRY",
        "→ ASIC / output window safe clear",
        "→ OUTPUT_SAFE_DEFAULTS",
        "→ RAM_STATE_SEED",
        "→ REF_DRP_WAIT",
        "→ CRANK_QUALIFY",
        "→ FIRST_PERIOD_VALID",
        "→ RUN_QUALIFY",
        "→ NORMAL_SCHEDULER_HANDOFF",
        "→ DROPOUT_SAFE_STATE on signal loss or unsafe state",
        "```",
        "",
        "## Safe Output Rules",
        "",
        "Fuel:",
        "",
        "- `$3FCE` may be zeroed.",
        "- Nonzero `$3FCE` requires fuel calculation and enable/no-fuel gate.",
        "- `$3FCE` may only be written through `EFI_PW_WRITE` / `MINIMAL_EFI_PW_WRITER` or documented output-init clear path.",
        "",
        "Spark:",
        "",
        "- no direct timing ASIC writes.",
        "- no EST/bypass authority implementation yet.",
        "- rolling timing seed remains bench-gated.",
        "",
        "IAC:",
        "",
        "- no direct `L3062` writes.",
        "- no physical IAC motion implementation yet.",
        "- software seed only until physical direction, Enable, park/reset behavior, and cadence are bench-gated.",
        "",
        "## Dropout Rules",
        "",
        "On missing REF/DRP or unsafe state:",
        "",
        "```text",
        "fuel → zero/no-pulse",
        "spark → safe/bypass/dropout intent only",
        "IAC → hold current software state or defined safe target",
        "watchdog → force output-safe defaults",
        "```",
        "",
        "## Boot-State Table",
        "",
        "| Boot stage | State | Module | Submodule | Output default | Hardware write | Allowed now | Bench gate | Safe value | Dropout value |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in ROWS:
        lines.append(f"| {r[0]} | `{r[1]}` | {r[3]} | {r[4]} | {r[7]} | {r[8]} `{r[9]}` | {r[10]} | {r[11]} | {r[13]} | {r[14]} |")
    lines += [
        "",
        "## Explicit Forbidden Outputs",
        "",
        "No boot state may directly write:",
        "",
        "```text",
        "$3FE8",
        "$3FE6",
        "$3FF6",
        "$3FDC",
        "L3062",
        "```",
        "",
        "No boot state may create:",
        "",
        "```text",
        "reset vector ASM",
        "runtime scheduler ASM",
        "SPARK_WRITE",
        "IAC_WRITE",
        "physical EST/bypass authority code",
        "idle strategy ASM",
        "```",
        "",
        "Exception:",
        "",
        "```text",
        "$3FCE may be forced to zero only through the existing EFI_PW_WRITE / MINIMAL_EFI_PW_WRITER contract or a documented output-init clear path.",
        "```",
        "",
        "## Unknown Ownership Rule",
        "",
        "Unknown boot ownership must remain `UNKNOWN`; it must not be silently assigned to reset, fuel, spark, IAC, watchdog, or scheduler code until source/bench evidence assigns it.",
        "",
        "## Next Contract",
        "",
        "The next useful artifact is:",
        "",
        "```text",
        "MINIMAL_OS_STATE_VARIABLES",
        "```",
        "",
        "That pass should consolidate the minimal RAM/state map across fuel, spark, IAC, scheduler, boot, watchdog, and ALDL without writing the OS.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scheduler", default="maps/contracts/minimal_os_execution_scheduler.csv")
    p.add_argument("--out-md", required=True)
    p.add_argument("--out-csv", required=True)
    args = p.parse_args()
    scheduler = resolve(args.scheduler)
    if not scheduler.exists():
        raise SystemExit(f"missing scheduler contract CSV: {scheduler}")
    write_csv(resolve(args.out_csv))
    write_md(resolve(args.out_md))
    print(f"MINIMAL_OS_BOOT_SAFE_STATE: wrote {len(ROWS)} boot-state rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
