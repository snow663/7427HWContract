#!/usr/bin/env python3
"""Build the minimal OS execution scheduler boundary artifacts.

This is contract/planning only. It does not implement a scheduler, create runtime
ASM, or add hardware writers. It assigns event ownership and preserves bench
gates for spark and IAC hardware-facing actions.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

FIELDS = [
    "scheduler_stage", "event_class", "trigger_source", "routine_or_contract", "module",
    "submodule", "inputs_consumed", "state_updated", "output_produced", "hardware_write",
    "hardware_address", "allowed_now", "bench_gated", "forbidden_until",
    "source_contract_dependency", "calibration_dependency", "minimal_os_required",
    "confidence", "notes",
]

ROWS = [
    ["boot_clear", "RESET_INIT", "power-on/reset vector", "MINIMAL_OS_MODULE_BOUNDARY.md", "reset", "hardware_window_clear", "reset cause; calibration-independent safe defaults", "ASIC/window/output safe defaults", "known-safe inactive state", "candidate", "ASIC/window registers", "no_runtime_code_yet", "yes", "BOOT_SAFE_STATE proves exact reset writes", "EFI_OUTPUT_INIT_STATE.md; MINIMAL_OS_MODULE_BOUNDARY.md", "none", "yes", "medium_contract", "Planning row only; exact boot writes belong in MINIMAL_OS_BOOT_SAFE_STATE."],
    ["fuel_boot_seed", "RESET_INIT", "power-on/reset vector", "EFI_OUTPUT_INIT_ROUTINE.md", "fuel", "fuel_output_init", "reset state; no-fuel gate", "fuel output state seeded", "EFI output safe/inactive state", "candidate", "$3FCE companion init state", "no_runtime_code_yet", "yes", "bench confirms EFI_OUTPUT_INIT_STATE", "EFI_OUTPUT_INIT_STATE.md; MINIMAL_EFI_PW_WRITER.md", "none", "yes", "medium_static", "Fuel runtime writer is separate; reset seed is not a scheduler implementation."],
    ["spark_boot_seed", "RESET_INIT", "power-on/reset vector", "SPARK_INIT_STATE.md", "spark", "rolling_state_seed", "reset state; initial DRP status", "$3FF6/$3FDC/L01EC seed candidates", "spark timing state initialized/held safe", "no", "$3FF6/$3FDC", "no", "yes", "$3FF6/$3FDC first-event seed and handoff behavior bench-proven", "SPARK_INIT_STATE.md; SPARK_ROLLING_STATE_MODEL.md", "none", "yes", "high_static", "No direct rolling-state writer is allowed by this scheduler contract."],
    ["iac_boot_seed", "RESET_INIT", "power-on/reset vector", "IAC_INIT_PARK_CONTRACT.md", "iac_idle", "actual_position_seed", "reset-in-work; bad-shutdown; NVM-validity; L4EB0", "L0007/L0008/L0009 candidate state", "IAC actual/desired/reset policy selected", "no", "L3062", "no", "yes", "physical park/reset behavior and L3062 output behavior bench-proven", "IAC_INIT_PARK_CONTRACT.md; IAC_MINIMAL_MODULE_INPUTS.md", "CAL_4EB0 candidate", "yes", "high_static", "Seeds policy; does not step motor or write L3062."],
    ["watchdog_boot", "RESET_INIT", "power-on/reset vector", "MINIMAL_OS_MODULE_BOUNDARY.md", "watchdog_safe_state", "safe_default", "reset cause; boot progress", "watchdog-safe state initialized", "safe fallback state", "no", "none", "no_runtime_code_yet", "yes", "BOOT_SAFE_STATE defines exact watchdog behavior", "MINIMAL_OS_MODULE_BOUNDARY.md", "none", "yes", "medium_contract", "Scheduler must define watchdog service points before runtime code."],

    ["crank_entry", "CRANK_INIT", "first valid crank/ref condition", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "reset", "crank_state", "REF/DRP present; crank/run flags; battery state", "crank mode entered", "crank-safe module enable set", "no", "none", "planning_only", "yes", "crank/run qualification proven", "MINIMAL_OS_MODULE_BOUNDARY.md; SPARK_BYPASS_EST_TRANSITION.md", "none", "yes", "medium_contract", "Crank is an execution state, not a hardware writer."],
    ["fuel_crank_inputs", "CRANK_INIT", "crank mode", "FUEL_MINIMAL_MODULE_INPUTS.md", "fuel", "crank_fuel_inputs", "RPM; coolant; battery; crank state; no-fuel gate", "fuel crank input state", "crank BPW/PW intent", "no", "$3FCE", "no", "yes", "fuel calculation and $3FCE writer invocation are scheduled separately", "FUEL_MINIMAL_MODULE_INPUTS.md; EFI_PW_3FCE_CONTRACT.md", "crank_start; warmup_afterstart", "yes", "high_planning", "No actual $3FCE write occurs in this row."],
    ["spark_crank_intent", "CRANK_INIT", "crank mode", "SPARK_MINIMAL_MODULE_INPUTS.md", "spark", "startup_spark_intent", "RPM/ref period; crank state; bypass/EST authority state; coolant", "startup spark intent state", "desired startup spark intent", "no", "$3FE8/$3FE6", "no", "yes", "spark output handoff bench-proven", "SPARK_MINIMAL_MODULE_INPUTS.md; SPARK_BYPASS_EST_TRANSITION.md", "spark; crank_start", "yes", "high_planning", "Computes intent only; no ASIC handoff or EST authority code."],
    ["iac_crank_target", "CRANK_INIT", "crank mode", "IAC_MINIMAL_MODULE_INPUTS.md", "iac_idle", "crank_air_target", "coolant; crank state; park/reset state; battery/Enable state", "IAC crank target state", "desired IAC/crank-air target", "no", "L3062", "no", "yes", "IAC physical direction/Enable/park behavior bench-proven", "IAC_MINIMAL_MODULE_INPUTS.md; IAC_INIT_PARK_CONTRACT.md", "iac_idle", "yes", "high_planning", "Sets/plans target only; no L3062 writer."],

    ["ref_period_capture", "REF_DRP_EVENT", "REF/DRP interrupt/event", "MINIMAL_OS_MODULE_BOUNDARY.md", "ref_rpm_period", "period_capture", "timer capture; DRP edge", "DRP/ref period basis updated", "RPM/timebase state", "no", "none", "planning_only", "yes", "exact interrupt/capture hardware contract finalized", "SPARK_TIMEBASE_PERIOD_CONTRACT.md; MINIMAL_OS_MODULE_BOUNDARY.md", "none", "yes", "high_contract", "Owns timing basis used by fuel/spark/IAC."],
    ["run_qualification", "REF_DRP_EVENT", "REF/DRP interrupt/event", "SPARK_BYPASS_EST_TRANSITION.md", "scheduler", "run_crank_qualify", "recent DRP; RPM threshold; first valid DRP; crank/run state", "run qualification flags", "crank/run permission state", "no", "none", "planning_only", "yes", "physical bypass/EST transition and dropout behavior bench-proven", "SPARK_BYPASS_EST_TRANSITION.md; MINIMAL_OS_MODULE_BOUNDARY.md", "none", "yes", "high_static", "Qualification feeds modules; it does not control EST directly."],
    ["fuel_rpm_feed", "REF_DRP_EVENT", "period/RPM updated", "FUEL_MINIMAL_MODULE_INPUTS.md", "fuel", "rpm_input_update", "RPM / engine speed", "fuel RPM input latched", "fuel calculation ready input", "no", "none", "planning_only", "no", "none", "FUEL_MINIMAL_MODULE_INPUTS.md", "none", "yes", "high_planning", "Fuel calculation consumes RPM later; no output here."],
    ["spark_period_feed", "REF_DRP_EVENT", "period/RPM updated", "SPARK_MINIMAL_MODULE_INPUTS.md", "spark", "timebase_input_update", "DRP/ref period; RPM", "spark timebase input latched", "conversion-ready timebase", "no", "$3FE8/$3FE6", "no", "yes", "spark handoff path bench-proven", "SPARK_TIMEBASE_PERIOD_CONTRACT.md; SPARK_MINIMAL_MODULE_INPUTS.md", "none", "yes", "high_static", "Feeds conversion only; no timing register write."],
    ["iac_rpm_feed", "REF_DRP_EVENT", "period/RPM updated", "IAC_MINIMAL_MODULE_INPUTS.md", "iac_idle", "idle_rpm_input_update", "actual idle RPM; RPM error basis", "IAC RPM input latched", "idle error input", "no", "none", "planning_only", "yes", "IAC cadence and target loop timing proven", "IAC_MINIMAL_MODULE_INPUTS.md", "iac_idle", "yes", "medium_planning", "IAC loop should not run directly at every REF until cadence is defined."],
    ["dropout_timer_reset", "REF_DRP_EVENT", "valid REF/DRP", "MINIMAL_OS_MODULE_BOUNDARY.md", "watchdog_safe_state", "dropout_monitor", "valid REF/DRP edge", "dropout timer reset", "dropout-safe state deferred", "no", "none", "planning_only", "yes", "dropout thresholds and safe actions proven", "MINIMAL_OS_MODULE_BOUNDARY.md; SPARK_MINIMAL_MODULE_INPUTS.md", "none", "yes", "medium_contract", "Valid REF/DRP keeps runtime outputs permitted."],

    ["sensor_sample", "SENSOR_SAMPLE_EVENT", "timer/foreground sample cadence", "MINIMAL_OS_MODULE_BOUNDARY.md", "sensors", "adc_sample", "MAP; TPS; CTS; battery; baro; O2 optional", "sensor state updated", "module input snapshot", "no", "none", "planning_only", "yes", "sensor cadence/noise/filter policy defined", "FUEL_MINIMAL_MODULE_INPUTS.md; SPARK_MINIMAL_MODULE_INPUTS.md; IAC_MINIMAL_MODULE_INPUTS.md", "sensor_scaling", "yes", "medium_contract", "Sensor acquisition feeds modules but does not own outputs."],
    ["foreground_loop", "FOREGROUND_BACKGROUND_LOOP", "main loop/service loop", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "scheduler", "foreground_dispatch", "current mode; service flags; sensor snapshot", "service-loop state", "dispatch permits module calculations", "no", "none", "planning_only", "yes", "runtime loop timing measured/proven", "MINIMAL_OS_MODULE_BOUNDARY.md", "none", "yes", "medium_contract", "Dispatch model only; no ASM scheduler generated."],

    ["fuel_calc", "FUEL_CALC_EVENT", "foreground/timer after sensor/RPM update", "FUEL_MINIMAL_MODULE_INPUTS.md", "fuel", "fuel_compute", "RPM; MAP; TPS; CTS; battery; baro; crank/run; calibration inputs", "fuel calculation state", "EFI PW count intent D", "no", "$3FCE", "planning_only", "yes", "fuel math/units validated", "FUEL_MINIMAL_MODULE_INPUTS.md; EFI_PW_UNITS.md", "fuel; crank_start; warmup_afterstart; battery_voltage; injector_deadtime", "yes", "high_planning", "Computes D but does not write hardware in this row."],
    ["fuel_dfco_gate", "FUEL_CALC_EVENT", "fuel compute", "FUEL_MINIMAL_MODULE_INPUTS.md", "fuel", "no_fuel_gate", "DFCO/no-fuel permission; crank/run; TPS/RPM/MAP", "fuel enable/no-fuel state", "D=0 candidate when gated", "no", "$3FCE", "planning_only", "yes", "DFCO zero-gate behavior validated", "FUEL_MINIMAL_MODULE_INPUTS.md; EFI_PW_3FCE_CONTRACT.md", "fuel", "yes", "high_planning", "Zero-gate must exist before writer invocation."],
    ["fuel_correction", "FUEL_CALC_EVENT", "fuel compute", "FUEL_MINIMAL_MODULE_INPUTS.md", "fuel", "injector_model", "battery; injector flow; deadtime; low-PW transfer", "corrected PW state", "EFI PW counts in 1/65536s units", "no", "$3FCE", "planning_only", "yes", "injector low-PW/deadtime validated", "FUEL_MINIMAL_MODULE_INPUTS.md; EFI_PW_UNITS.md", "injector_deadtime; battery_voltage", "yes", "high_planning", "Correction planning only; no tune change."],
    ["fuel_output", "FUEL_OUTPUT_EVENT", "fuel PW intent ready", "MINIMAL_EFI_PW_WRITER.md", "fuel", "efi_pw_write", "D = EFI pulsewidth counts", "$3FCE output state", "EFI PW command", "yes", "$3FCE", "yes_provisional", "yes", "bench confirms $3FCE output behavior and units", "EFI_PW_3FCE_CONTRACT.md; MINIMAL_EFI_PW_WRITER.md", "none", "yes", "high_static_bench_pending", "Only allowed/provisional runtime hardware write in this scheduler boundary."],

    ["spark_calc", "SPARK_PERIOD_EVENT", "foreground/timer/period-qualified event", "SPARK_MINIMAL_MODULE_INPUTS.md", "spark", "spark_intent_compute", "RPM; MAP; TPS; CTS; baro; crank/run; bypass/EST state; base spark calibration", "desired spark intent", "desired spark degrees/timing intent", "no", "$3FE8/$3FE6", "no", "yes", "spark output handoff proven", "SPARK_MINIMAL_MODULE_INPUTS.md; SPARK_CONVERSION_EQUATION.md", "spark; spark_latency", "yes", "high_planning", "Intent only; no LA906 replacement or ASIC writes."],
    ["spark_conversion", "SPARK_PERIOD_EVENT", "spark intent ready", "SPARK_CONVERSION_EQUATION.md", "spark", "degree_to_time_inputs", "desired spark; DRP period; latency; rolling seed", "conversion input state", "timing-domain candidate", "no", "$3FE8/$3FE6/$3FF6/$3FDC", "no", "yes", "LA906 packing/sign/rolling-state behavior bench-proven", "SPARK_CONVERSION_EQUATION.md; SPARK_ROLLING_STATE_MODEL.md", "none", "yes", "high_static", "Conversion dependency listed without writer implementation."],
    ["spark_output_forbidden", "SPARK_OUTPUT_EVENT", "timing-domain candidate", "SPARK_ASIC_HANDOFF_CONTRACT.md", "spark", "asic_handoff", "timing-domain candidate; rolling state", "none", "none", "forbidden", "$3FE8/$3FE6/$3FF6/$3FDC/$3FE4", "no", "yes", "bench proves exact physical roles and safe authority", "SPARK_ASIC_HANDOFF_CONTRACT.md; SPARK_LA906_OUTPUT_SEQUENCE.md", "none", "yes_future", "high_policy", "No scheduler event may write spark hardware in current state."],

    ["iac_target", "IAC_CADENCE_EVENT", "timer/cadence after RPM/sensor update", "IAC_MINIMAL_MODULE_INPUTS.md", "iac_idle", "target_compute", "RPM; desired idle; CTS; TPS; crank/run; park/reset state", "desired IAC target state", "L0008 target candidate", "no", "L3062", "no", "yes", "IAC target policy and physical target meaning proven", "IAC_MINIMAL_MODULE_INPUTS.md; IAC_INIT_PARK_CONTRACT.md", "iac_idle", "yes", "high_planning", "Target planning only; no idle strategy ASM."],
    ["iac_compare", "IAC_CADENCE_EVENT", "IAC cadence tick", "IAC_IDLE_AIR_OUTPUT_CONTRACT.md", "iac_idle", "position_compare", "L0007 actual; L0008 desired; seed-valid state", "position error/direction candidate", "step/no-step decision", "no", "L3062", "no", "yes", "physical direction and count sign proven", "IAC_IDLE_AIR_OUTPUT_CONTRACT.md; IAC_MINIMAL_MODULE_INPUTS.md", "none", "yes", "high_static", "Software compare planning; no output latch write."],
    ["iac_phase_candidate", "IAC_CADENCE_EVENT", "IAC step permitted", "IAC_PHASE_SEQUENCE_CONTRACT.md", "iac_idle", "phase_step", "direction bit; A/B phase state; cadence permit", "L000A bits0/2/3 candidate", "next A/B phase candidate", "no", "L3062", "no", "yes", "physical A/B mapping, step equivalence, and safe cadence proven", "IAC_PHASE_SEQUENCE_CONTRACT.md", "none", "yes_future", "high_static", "Phase update is not a direct hardware writer in this scheduler boundary."],
    ["iac_output_forbidden", "IAC_OUTPUT_EVENT", "IAC phase/enable candidate", "IAC_IDLE_AIR_OUTPUT_CONTRACT.md", "iac_idle", "output_latch", "L000A bits2/3/4; L004C shadow", "none", "none", "forbidden", "L3062", "no", "yes", "bench proves physical pins, Enable, park/reset, cadence, and safe writer", "IAC_IDLE_AIR_OUTPUT_CONTRACT.md; IAC_ENABLE_FAULT_GATE_CONTRACT.md", "none", "yes_future", "high_policy", "No scheduler event may write L3062 in current state."],

    ["aldl_service", "ALDL_SERVICE_EVENT", "foreground/service loop", "MINIMAL_OS_MODULE_BOUNDARY.md", "aldl_debug", "debug_service", "runtime state snapshot; diagnostic request", "ALDL/debug state", "debug output only", "no", "none", "planning_only", "no", "none", "MINIMAL_OS_MODULE_BOUNDARY.md", "aldl_debug", "optional", "medium_contract", "ALDL exposes state; it does not own control outputs."],
    ["watchdog_service", "WATCHDOG_SERVICE_EVENT", "foreground/service loop or timed tick", "MINIMAL_OS_MODULE_BOUNDARY.md", "watchdog_safe_state", "watchdog_service", "main loop alive; event progress", "watchdog serviced", "safe-state not triggered", "no", "none", "planning_only", "yes", "watchdog policy defined in boot-safe contract", "MINIMAL_OS_MODULE_BOUNDARY.md", "none", "yes", "medium_contract", "Watchdog service points must be part of scheduler design."],
    ["dropout_safe_fuel", "DROPOUT_SAFE_STATE", "missing REF/DRP or invalid runtime state", "FUEL_MINIMAL_MODULE_INPUTS.md", "fuel", "dropout_zero_gate", "dropout flag; run qualification invalid", "fuel no-pulse state", "D=0/no-pulse intent", "candidate", "$3FCE", "yes_provisional_via_fuel_writer_only", "yes", "safe zero behavior and $3FCE bench validation", "EFI_PW_3FCE_CONTRACT.md; FUEL_MINIMAL_MODULE_INPUTS.md", "none", "yes", "medium_planning", "If executed, $3FCE must be written only through EFI_PW_WRITE."],
    ["dropout_safe_spark", "DROPOUT_SAFE_STATE", "missing REF/DRP or invalid timing state", "SPARK_MINIMAL_MODULE_INPUTS.md", "spark", "dropout_safe_intent", "dropout flag; bypass/run qualification invalid", "spark safe intent", "safe/bypass/dropout state", "no", "$3FE8/$3FE6", "no", "yes", "physical bypass/dropout behavior proven", "SPARK_MINIMAL_MODULE_INPUTS.md; SPARK_BYPASS_EST_TRANSITION.md", "none", "yes", "high_policy", "No physical EST/bypass control yet."],
    ["dropout_safe_iac", "DROPOUT_SAFE_STATE", "missing REF/DRP or reset/fault state", "IAC_MINIMAL_MODULE_INPUTS.md", "iac_idle", "dropout_hold_or_park", "dropout flag; seed-valid state; Enable/protection", "IAC hold/safe policy", "hold or safe-park intent", "no", "L3062", "no", "yes", "safe IAC park/hold behavior and writer proven", "IAC_MINIMAL_MODULE_INPUTS.md; IAC_INIT_PARK_CONTRACT.md", "none", "yes_future", "medium_planning", "No L3062 output during dropout in current boundary."],

    ["bench_hook", "BENCH_ONLY_HOOK", "bench harness / trace flag", "DYNAMIC_TRACE_PLAN.md", "bench", "instrumentation", "event counters; selected state", "trace/debug only", "bench log/ALDL exposure", "no", "none", "bench_only", "no", "none", "DYNAMIC_TRACE_PLAN.md; docs/tests/*.md", "none", "optional", "medium_contract", "Bench hooks may observe, not own control hardware."],
    ["excluded_trans", "EXCLUDED", "stock strategy baggage", "CALIBRATION_SOURCE_INDEX.md", "excluded", "transmission", "TCC/shift/trans tables", "none", "none", "forbidden", "trans/TCC hardware", "no", "yes_if_future_hardware_required", "future hardware contract proves requirement", "CALIBRATION_SOURCE_INDEX.md", "trans_excluded", "no", "high_policy", "No transmission/TCC scheduling in minimal OS now."],
    ["excluded_egr_evap", "EXCLUDED", "stock strategy baggage", "CALIBRATION_SOURCE_INDEX.md", "excluded", "emissions", "EGR/EVAP/emissions tables", "none", "none", "forbidden", "EGR/EVAP hardware", "no", "yes_if_future_hardware_required", "future hardware contract proves requirement", "CALIBRATION_SOURCE_INDEX.md", "egr_excluded; evap_excluded; emissions_excluded", "no", "high_policy", "No EGR/EVAP/emissions scheduling in minimal OS now."],
    ["unknown_event", "UNKNOWN", "unresolved timing/source ownership", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "unknown", "unknown", "unknown/unclassified timing inputs", "unknown", "unknown", "no", "unknown", "no", "yes", "future source trace assigns ownership", "MINIMAL_OS_MODULE_BOUNDARY.md", "unknown", "unknown", "low_unclassified", "Unknown event ownership remains listed rather than guessed."],
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
        "# Minimal OS Execution Scheduler",
        "",
        "## Purpose",
        "",
        "Define when minimal-OS modules execute relative to reset, crank, REF/DRP events, timer events, foreground/service loops, ALDL/debug service, and watchdog-safe state.",
        "",
        "This document does not implement a scheduler and does not create runtime ASM.",
        "",
        "## Source Boundaries",
        "",
        "Fuel:",
        "",
        "- `FUEL_MINIMAL_MODULE_INPUTS.md`",
        "- `EFI_PW_3FCE_CONTRACT.md`",
        "- `MINIMAL_EFI_PW_WRITER.md`",
        "",
        "Spark:",
        "",
        "- `SPARK_MINIMAL_MODULE_INPUTS.md`",
        "- `SPARK_MINIMAL_MODULE_BOUNDARY.md`",
        "- `SPARK_BYPASS_EST_TRANSITION.md`",
        "- `SPARK_INIT_STATE.md`",
        "",
        "IAC:",
        "",
        "- `IAC_MINIMAL_MODULE_INPUTS.md`",
        "- `IAC_IDLE_AIR_OUTPUT_CONTRACT.md`",
        "- `IAC_PHASE_SEQUENCE_CONTRACT.md`",
        "- `IAC_ENABLE_FAULT_GATE_CONTRACT.md`",
        "- `IAC_INIT_PARK_CONTRACT.md`",
        "",
        "## Scheduler Model",
        "",
        "```text",
        "RESET_INIT",
        "→ hardware/window clear",
        "→ seed retained/known state",
        "→ enable watchdog-safe defaults",
        "→ wait for crank/ref events",
        "",
        "REF_DRP_EVENT",
        "→ update period/RPM basis",
        "→ run/crank qualification",
        "→ fuel/spark timebase inputs",
        "→ dropout timer reset",
        "",
        "CRANK_INIT / CRANK_LOOP",
        "→ crank fuel inputs",
        "→ startup spark intent",
        "→ IAC crank/park target",
        "→ no unsupported output handoff",
        "",
        "RUN_LOOP",
        "→ sensor sample",
        "→ fuel calculation",
        "→ spark intent calculation",
        "→ IAC desired target calculation",
        "→ ALDL/debug service",
        "→ watchdog service",
        "",
        "TIMER / CADENCE EVENTS",
        "→ fuel output timing if required",
        "→ spark timing only after bench-gated handoff is proven",
        "→ IAC step cadence only after bench-gated output behavior is proven",
        "",
        "DROPOUT_SAFE_STATE",
        "→ fuel no-pulse / zero gate",
        "→ spark safe/bypass/dropout state",
        "→ IAC hold or safe park policy",
        "```",
        "",
        "## Hardware Ownership Rule",
        "",
        "Only the module that owns a hardware contract may write that hardware-facing value.",
        "",
        "Allowed/provisional:",
        "",
        "- fuel writer may write `$3FCE` only through `EFI_PW_WRITE`",
        "",
        "Forbidden until bench-gated:",
        "",
        "- direct `$3FE8/$3FE6/$3FF6/$3FDC` spark writes",
        "- direct `L3062` IAC writes",
        "- physical EST/bypass authority code",
        "- IAC phase/output ASM",
        "",
        "## Event Table",
        "",
        "| Stage | Event | Module | Submodule | Trigger | Output | Hardware write | Allowed now | Bench gate |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in ROWS:
        lines.append(f"| {row[0]} | `{row[1]}` | {row[4]} | {row[5]} | {row[2]} | {row[8]} | {row[9]} `{row[10]}` | {row[11]} | {row[12]} |")
    lines += [
        "",
        "## Explicit Forbidden List",
        "",
        "No scheduler event may directly write:",
        "",
        "```text",
        "$3FE8",
        "$3FE6",
        "$3FF6",
        "$3FDC",
        "L3062",
        "```",
        "",
        "No scheduler event may create:",
        "",
        "```text",
        "SPARK_WRITE",
        "IAC_WRITE",
        "physical EST/bypass authority code",
        "idle strategy ASM",
        "```",
        "",
        "Exception:",
        "",
        "```text",
        "$3FCE may only be written through the existing minimal EFI PW writer contract.",
        "```",
        "",
        "## Unknown Ownership Rule",
        "",
        "Unknown timing/event ownership must stay listed as `UNKNOWN`; it must not be guessed into fuel, spark, IAC, ALDL, or watchdog until source/bench evidence assigns it.",
        "",
        "## Next Contract",
        "",
        "The next useful artifact is:",
        "",
        "```text",
        "MINIMAL_OS_BOOT_SAFE_STATE",
        "```",
        "",
        "That pass should turn this scheduler boundary into a reset/crank/run safe-state machine without implementing the full OS.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fuel-inputs", default="maps/contracts/fuel_minimal_module_inputs.csv")
    p.add_argument("--spark-inputs", default="maps/contracts/spark_minimal_module_inputs.csv")
    p.add_argument("--iac-inputs", default="maps/contracts/iac_minimal_module_inputs.csv")
    p.add_argument("--out-md", required=True)
    p.add_argument("--out-csv", required=True)
    args = p.parse_args()
    for attr in ("fuel_inputs", "spark_inputs", "iac_inputs"):
        pth = resolve(getattr(args, attr))
        if not pth.exists():
            raise SystemExit(f"missing required input boundary CSV: {pth}")
    write_csv(resolve(args.out_csv))
    write_md(resolve(args.out_md))
    print(f"MINIMAL_OS_EXECUTION_SCHEDULER: wrote {len(ROWS)} scheduler rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
