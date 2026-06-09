#!/usr/bin/env python3
"""Build the minimal OS state-variable boundary artifacts.

This is planning only. It does not allocate RAM, create a linker map, or emit
runtime ASM. It consolidates source-proven symbols, hardware shadows, logical
minimal-OS state, bench-gated state, and explicit exclusions.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

FIELDS = [
    "state_name", "source_symbol", "source_address", "bitmask", "width",
    "state_class", "module_owner", "submodule_owner", "producer_event",
    "consumer_event", "reset_value", "safe_value", "retained_across_reset",
    "hardware_shadow", "hardware_address", "calibration_dependency",
    "source_contract_dependency", "bench_dependency", "carry_forward_to_minimal_os",
    "excluded_reason", "confidence", "notes",
]

ROWS = [
    # Fuel state
    ["efi_pw_command", "L3FCE/L3FCF", "$3FCE/$3FCF", "", "16", "hardware_shadow", "fuel", "efi_pw_write", "FUEL_OUTPUT_EVENT", "fuel hardware output", "$0000", "$0000/no-pulse", "no", "yes", "$3FCE", "none", "EFI_PW_3FCE_CONTRACT.md; MINIMAL_EFI_PW_WRITER.md", "$3FCE units and bench confirmation pending", "yes", "", "high_static_bench_pending", "Runtime EFI pulsewidth command; only provisional allowed hardware write path."],
    ["sync_bpw_source", "L024E", "$024E", "", "16", "fuel_state", "fuel", "base_pw", "FUEL_CALC_EVENT", "fuel calculation / EFI PW writer", "unknown", "zero/no-fuel if invalid", "no", "no", "", "fuel calibration candidates", "FUEL_MINIMAL_MODULE_INPUTS.md", "exact role still source-gated", "bench_gated", "", "medium_static", "Sync BPW/base PW source candidate from existing fuel notes."],
    ["bpw_intermediate_final", "L0250", "$0250", "", "16", "fuel_state", "fuel", "base_pw", "FUEL_CALC_EVENT", "fuel correction / output scale", "unknown", "zero/no-fuel if invalid", "no", "no", "", "fuel calibration candidates", "FUEL_MINIMAL_MODULE_INPUTS.md", "exact intermediate/final role still source-gated", "bench_gated", "", "medium_static", "Final/intermediate BPW candidate before output conversion."],
    ["fuel_enable_no_fuel_gate", "minimal_fuel_enable", "new", "", "1", "fuel_state", "fuel", "mode_gate", "BOOT_SAFE_STATE; FUEL_CALC_EVENT; DROPOUT_SAFE_STATE", "FUEL_OUTPUT_EVENT", "disabled", "disabled/no-pulse", "no", "no", "", "none", "FUEL_MINIMAL_MODULE_INPUTS.md; MINIMAL_OS_BOOT_SAFE_STATE.md", "must preserve zero/no-fuel behavior", "yes", "", "high_planning", "New minimal-OS logical gate; nonzero fuel cannot bypass it."],
    ["dfco_zero_gate", "minimal_dfco_zero_gate", "new", "", "1", "fuel_state", "fuel", "dfco_no_fuel", "FUEL_CALC_EVENT", "FUEL_OUTPUT_EVENT", "disabled or zero-for-safe", "force D=0 when active", "no", "no", "", "DFCO calibration candidates", "FUEL_MINIMAL_MODULE_INPUTS.md", "DFCO zero-gate behavior validation pending", "yes", "", "high_planning", "Logical state required so DFCO/no-fuel can force zero output."],
    ["injector_low_pw_correction_state", "minimal_low_pw_tf_state", "new", "", "mixed", "fuel_state", "fuel", "injector_model", "FUEL_CALC_EVENT", "FUEL_OUTPUT_EVENT", "identity/pass-through", "identity or zero output if invalid", "no", "no", "", "injector correction calibration", "FUEL_MINIMAL_MODULE_INPUTS.md", "low-PW transfer validation pending", "yes", "", "medium_planning", "Tracks selected low-PW transfer correction; not a stock RAM clone."],
    ["battery_deadtime_correction_state", "minimal_deadtime_state", "new", "", "mixed", "fuel_state", "fuel", "injector_model", "SENSOR_SAMPLE_EVENT; FUEL_CALC_EVENT", "FUEL_OUTPUT_EVENT", "safe default", "safe default or zero output if invalid", "no", "no", "", "battery/deadtime calibration", "FUEL_MINIMAL_MODULE_INPUTS.md", "battery/deadtime validation pending", "yes", "", "medium_planning", "Logical correction state fed by battery voltage."],

    # Spark state
    ["spark_final_advance_accum", "L01FD", "$01FD", "", "8", "spark_state", "spark", "spark_intent", "SPARK_PERIOD_EVENT", "SPARK_PERIOD_EVENT", "unknown", "safe/no-authority intent", "no", "no", "", "spark calibration candidates", "SPARK_MINIMAL_MODULE_INPUTS.md; SPARK_CONVERSION_EQUATION.md", "final scale/sign behavior bench-gated", "bench_gated", "", "high_static", "Final spark advance accumulator candidate."],
    ["spark_signed_offset", "L01EE", "$01EE", "", "16", "spark_state", "spark", "degree_to_time_conversion", "SPARK_PERIOD_EVENT", "SPARK_PERIOD_EVENT", "unknown", "zero/safe offset", "no", "no", "", "none", "SPARK_CONVERSION_EQUATION.md", "LA906 packing/sign behavior bench-gated", "bench_gated", "", "high_static", "Signed spark offset into conversion path."],
    ["spark_sign_direction_flag", "L004F", "$004F", "bit0", "1", "spark_state", "spark", "degree_to_time_conversion", "SPARK_PERIOD_EVENT", "SPARK_PERIOD_EVENT", "unknown", "safe sign/default", "no", "no", "", "none", "SPARK_CONVERSION_EQUATION.md", "sign/direction meaning bench-gated", "bench_gated", "", "high_static", "Spark sign/direction flag candidate."],
    ["spark_latency_correction", "L0201", "$0201", "", "16", "spark_state", "spark", "latency", "SPARK_PERIOD_EVENT", "SPARK_PERIOD_EVENT", "unknown", "safe latency default", "no", "no", "", "spark latency calibration", "SPARK_MINIMAL_MODULE_INPUTS.md; SPARK_CONVERSION_EQUATION.md", "latency unit/final use bench-gated", "bench_gated", "", "high_static", "Spark latency correction candidate."],
    ["drp_ref_period_basis", "L005F/L0060", "$005F/$0060", "", "16", "sensor_state", "ref_rpm_period", "period_capture", "REF_DRP_EVENT", "fuel/spark/IAC inputs", "invalid", "invalid/dropout", "no", "no", "", "none", "SPARK_TIMEBASE_PERIOD_CONTRACT.md; MINIMAL_OS_EXECUTION_SCHEDULER.md", "period units and cadence bench/source-gated", "yes", "", "high_static", "REF/DRP period basis used by RPM/timebase-dependent modules."],
    ["spark_asic_period_source", "L3FC0/L3FC1", "$3FC0/$3FC1", "", "16", "bench_gated_state", "spark", "asic_handoff_candidate", "SPARK_PERIOD_EVENT", "SPARK_OUTPUT_EVENT", "unknown", "blocked", "no", "candidate", "$3FC0/$3FC1", "none", "SPARK_ASIC_HANDOFF_CONTRACT.md", "physical role bench-gated", "bench_gated", "", "medium_static", "ASIC timing/period source candidate; not writer-safe."],
    ["spark_asic_cmd_1", "L3FE8", "$3FE8", "", "16?", "bench_gated_state", "spark", "asic_handoff_candidate", "SPARK_OUTPUT_EVENT", "hardware", "blocked", "blocked", "no", "candidate", "$3FE8", "none", "SPARK_ASIC_HANDOFF_CONTRACT.md", "direct write forbidden until bench-proven", "bench_gated", "", "high_policy", "First ASIC timing command candidate; no direct writer."],
    ["spark_asic_cmd_2", "L3FE6", "$3FE6", "", "16?", "bench_gated_state", "spark", "asic_handoff_candidate", "SPARK_OUTPUT_EVENT", "hardware", "blocked", "blocked", "no", "candidate", "$3FE6", "none", "SPARK_ASIC_HANDOFF_CONTRACT.md", "direct write forbidden until bench-proven", "bench_gated", "", "high_policy", "Second ASIC timing command candidate; no direct writer."],
    ["spark_rolling_state", "L3FDC", "$3FDC", "", "16?", "bench_gated_state", "spark", "rolling_state", "SPARK_PERIOD_EVENT", "SPARK_OUTPUT_EVENT", "blocked", "blocked", "maybe", "candidate", "$3FDC", "none", "SPARK_ROLLING_STATE_MODEL.md", "first-event seed/rolling behavior bench-gated", "bench_gated", "", "high_static", "Rolling timing state candidate."],
    ["spark_rolling_anchor", "L3FF6", "$3FF6", "", "16?", "bench_gated_state", "spark", "rolling_state", "SPARK_PERIOD_EVENT", "SPARK_OUTPUT_EVENT", "blocked", "blocked", "maybe", "candidate", "$3FF6", "none", "SPARK_ROLLING_STATE_MODEL.md; SPARK_INIT_STATE.md", "first-event anchor behavior bench-gated", "bench_gated", "", "high_static", "Rolling timing anchor candidate."],
    ["spark_status_mirror_ack", "L3FEC -> L3FE4", "$3FEC/$3FE4", "", "mixed", "bench_gated_state", "spark", "status_ack", "SPARK_OUTPUT_EVENT", "SPARK_EST_FAULT_MONITOR", "blocked", "blocked", "unknown", "candidate", "$3FEC/$3FE4", "none", "SPARK_EST_FAULT_MONITOR_CONTRACT.md", "mirror/ack requirement bench-gated", "bench_gated", "", "medium_static", "Status/mirror/ack candidate path."],
    ["est_monitor_enable", "L004F", "$004F", "bit6", "1", "spark_state", "spark", "est_fault_monitor", "SPARK_PERIOD_EVENT", "SPARK_EST_FAULT_MONITOR", "disabled/unknown", "disabled/safe", "no", "no", "", "none", "SPARK_EST_FAULT_MONITOR_CONTRACT.md", "side effects bench-gated", "bench_gated", "", "medium_static", "EST monitor enable candidate."],
    ["engine_running_flag", "L004F", "$004F", "bit7", "1", "scheduler_state", "scheduler", "run_qualify", "REF_DRP_EVENT", "all runtime modules", "not running", "not running/dropout", "no", "no", "", "none", "SPARK_BYPASS_EST_TRANSITION.md; MINIMAL_OS_EXECUTION_SCHEDULER.md", "qualification details source-gated", "yes", "", "medium_static", "Engine-running flag candidate."],
    ["first_drp_valid", "L0044", "$0044", "bit3", "1", "scheduler_state", "ref_rpm_period", "first_period_valid", "REF_DRP_EVENT", "scheduler/spark", "invalid", "invalid", "no", "no", "", "none", "SPARK_BYPASS_EST_TRANSITION.md; MINIMAL_OS_BOOT_SAFE_STATE.md", "exact transition source/bench-gated", "yes", "", "medium_static", "First DRP valid candidate."],
    ["drp_event_counter", "L0210", "$0210", "", "8/16?", "scheduler_state", "ref_rpm_period", "run_qualify", "REF_DRP_EVENT", "scheduler/spark", "0", "0/dropout", "no", "no", "", "none", "SPARK_BYPASS_EST_TRANSITION.md", "counter semantics source-gated", "bench_gated", "", "medium_static", "Qualifying DRP/ref event counter candidate."],
    ["est_error_counter", "L022C", "$022C", "", "8/16?", "spark_state", "spark", "est_fault_monitor", "SPARK_EST_FAULT_MONITOR", "ALDL_DEBUG_EVENT", "0", "0 or fault-held", "no", "no", "", "none", "SPARK_EST_FAULT_MONITOR_CONTRACT.md", "fault side effects bench-gated", "bench_gated", "", "medium_static", "EST error counter candidate."],
    ["prior_est_ref_sample", "L0205", "$0205", "", "8/16?", "spark_state", "spark", "est_fault_monitor", "SPARK_EST_FAULT_MONITOR", "SPARK_EST_FAULT_MONITOR", "unknown", "safe/unknown", "no", "no", "", "none", "SPARK_EST_FAULT_MONITOR_CONTRACT.md", "sample semantics source-gated", "bench_gated", "", "medium_static", "Prior EST captured/ref sample candidate."],

    # IAC state
    ["iac_actual_position", "L0007", "$0007", "", "8", "iac_state", "iac_idle", "position_state", "IAC_CADENCE_EVENT; RAM_STATE_SEED", "IAC_CADENCE_EVENT; ALDL_DEBUG_EVENT", "unknown/seeded", "hold/no motion", "maybe", "no", "", "IAC idle calibration candidates", "IAC_IDLE_AIR_OUTPUT_CONTRACT.md; IAC_INIT_PARK_CONTRACT.md", "position seed validity and physical direction bench-gated", "yes", "", "high_static", "Actual/present IAC position."],
    ["iac_desired_position", "L0008", "$0008", "", "8", "iac_state", "iac_idle", "position_state", "IAC_CADENCE_EVENT; CRANK_INIT", "IAC_CADENCE_EVENT", "safe target/hold", "hold/no motion", "no", "no", "", "IAC target/park calibration", "IAC_IDLE_AIR_OUTPUT_CONTRACT.md; IAC_INIT_PARK_CONTRACT.md", "physical target meaning bench-gated", "yes", "", "high_static", "Desired/target IAC position."],
    ["iac_reset_in_work", "L0009", "$0009", "bit0", "1", "iac_state", "iac_idle", "startup_park", "RESET_INIT; IAC_CADENCE_EVENT", "IAC_CADENCE_EVENT", "unknown/reset policy", "hold/no motion", "maybe", "no", "", "none", "IAC_INIT_PARK_CONTRACT.md", "reset/home behavior bench-gated", "yes", "", "high_static", "Reset-in-work candidate."],
    ["iac_rs_requested", "L0009", "$0009", "bit2", "1", "iac_state", "iac_idle", "startup_park", "RESET_INIT; shutdown/park policy", "IAC_CADENCE_EVENT", "unknown", "hold/no motion", "maybe", "no", "", "none", "IAC_INIT_PARK_CONTRACT.md", "R/S request behavior bench-gated", "bench_gated", "", "high_static", "R/S requested candidate."],
    ["iac_direction", "L000A", "$000A", "bit0", "1", "iac_state", "iac_idle", "phase_state", "IAC_CADENCE_EVENT", "IAC_CADENCE_EVENT", "unknown/hold", "hold/no motion", "maybe", "no", "", "none", "IAC_PHASE_SEQUENCE_CONTRACT.md", "open/close direction bench-gated", "yes", "", "high_static", "IAC direction bit."],
    ["iac_phase_a", "L000A", "$000A", "bit2", "1", "iac_state", "iac_idle", "phase_state", "IAC_CADENCE_EVENT", "IAC_OUTPUT_EVENT", "hold/unknown", "hold/no motion", "maybe", "no", "", "none", "IAC_PHASE_SEQUENCE_CONTRACT.md", "physical A/B mapping bench-gated", "yes", "", "high_static", "A candidate bit in source ring."],
    ["iac_phase_b", "L000A", "$000A", "bit3", "1", "iac_state", "iac_idle", "phase_state", "IAC_CADENCE_EVENT", "IAC_OUTPUT_EVENT", "hold/unknown", "hold/no motion", "maybe", "no", "", "none", "IAC_PHASE_SEQUENCE_CONTRACT.md", "physical A/B mapping bench-gated", "yes", "", "high_static", "B candidate bit in source ring."],
    ["iac_enable_candidate", "L000A", "$000A", "bit4", "1", "iac_state", "iac_idle", "enable_gate", "IAC_CADENCE_EVENT; RESET_INIT", "IAC_OUTPUT_EVENT", "disabled/unknown", "disabled/hold", "maybe", "no", "", "CAL_4EB6 voltage threshold candidate", "IAC_ENABLE_FAULT_GATE_CONTRACT.md", "physical Enable function bench-gated", "yes", "", "high_static", "IAC Enable candidate bit."],
    ["iac_output_shadow", "L004C", "$004C", "bits2/3/4", "8", "hardware_shadow", "iac_idle", "output_shadow", "IAC_OUTPUT_EVENT", "IAC hardware latch", "safe/hold", "hold/no motion", "maybe", "yes", "L3062", "none", "IAC_IDLE_AIR_OUTPUT_CONTRACT.md; IAC_ENABLE_FAULT_GATE_CONTRACT.md", "direct L3062 writer and physical pins bench-gated", "bench_gated", "", "high_static", "Output shadow for IAC A/B/Enable bits."],
    ["iac_latch", "L3062", "$3062", "bits2/3/4 candidates", "8", "hardware_shadow", "iac_idle", "hardware_latch", "IAC_OUTPUT_EVENT", "hardware", "blocked", "blocked/no motion", "no", "candidate", "$3062", "none", "IAC_IDLE_AIR_OUTPUT_CONTRACT.md", "direct write forbidden until bench-proven", "bench_gated", "", "high_policy", "Hardware latch write candidate; not writer-safe."],
    ["iac_park_down_scalar", "L4EB0", "$4EB0", "", "8", "calibration_reference", "iac_idle", "startup_park", "RESET_INIT; IAC_CADENCE_EVENT", "IAC startup/park policy", "145 stock value", "software reference only", "no", "no", "", "CAL_4EB0", "IAC_INIT_PARK_CONTRACT.md", "physical meaning/direction bench-gated", "bench_gated", "", "high_static", "145-step park-down value calibration reference."],
    ["battery_voltage_vdc10", "L00A7", "$00A7", "", "8", "sensor_state", "sensors", "battery_voltage", "SENSOR_SAMPLE_EVENT", "fuel/IAC/spark corrections", "invalid/unknown", "safe low/invalid", "no", "no", "", "battery_voltage calibration", "IAC_ENABLE_FAULT_GATE_CONTRACT.md; FUEL_MINIMAL_MODULE_INPUTS.md", "scaling already candidate; behavior bench-gated", "yes", "", "high_static", "Battery voltage in VDC/10 candidate."],
    ["low_battery_protection", "L003E", "$003E", "bit2", "1", "watchdog_state", "watchdog_safe_state", "protection_gate", "SENSOR_SAMPLE_EVENT; BOOT_SAFE_STATE", "IAC enable / fuel safe state", "safe/protect", "protect", "no", "no", "", "none", "IAC_ENABLE_FAULT_GATE_CONTRACT.md; MINIMAL_OS_BOOT_SAFE_STATE.md", "exact flag semantics bench/source-gated", "bench_gated", "", "medium_static", "Low-battery/protection flag candidate."],

    # Scheduler / boot / watchdog / ALDL logical state
    ["rpm_valid", "minimal_rpm_valid", "new", "", "1", "scheduler_state", "ref_rpm_period", "period_valid", "REF_DRP_EVENT; DROPOUT_SAFE_STATE", "fuel/spark/IAC scheduler gates", "false", "false", "no", "no", "", "none", "MINIMAL_OS_EXECUTION_SCHEDULER.md; MINIMAL_OS_BOOT_SAFE_STATE.md", "thresholds/source timing pending", "yes", "", "high_planning", "New minimal logical state; not a stock clone."],
    ["ref_drp_valid", "minimal_ref_drp_valid", "new", "", "1", "scheduler_state", "ref_rpm_period", "period_valid", "REF_DRP_EVENT; DROPOUT_SAFE_STATE", "all runtime modules", "false", "false", "no", "no", "", "none", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "exact dropout thresholds pending", "yes", "", "high_planning", "Valid reference stream gate."],
    ["first_period_valid", "minimal_first_period_valid", "new", "", "1", "scheduler_state", "ref_rpm_period", "first_period_valid", "REF_DRP_EVENT", "spark/fuel/IAC run qualification", "false", "false", "no", "no", "", "none", "MINIMAL_OS_BOOT_SAFE_STATE.md", "exact first-period behavior pending", "yes", "", "high_planning", "First period accepted after reset/crank."],
    ["crank_run_qualification", "minimal_run_qual_state", "new", "", "mixed", "scheduler_state", "scheduler", "run_qualify", "REF_DRP_EVENT; CRANK_INIT", "fuel/spark/IAC events", "crank/not-run", "dropout/not-run", "no", "no", "", "none", "MINIMAL_OS_EXECUTION_SCHEDULER.md; MINIMAL_OS_BOOT_SAFE_STATE.md", "thresholds/source timing pending", "yes", "", "high_planning", "Minimal crank/run gate state."],
    ["dropout_state", "minimal_dropout_state", "new", "", "1", "boot_state", "watchdog_safe_state", "dropout_safe_state", "DROPOUT_SAFE_STATE", "all runtime modules", "false", "true on loss", "no", "no", "", "none", "MINIMAL_OS_BOOT_SAFE_STATE.md", "dropout thresholds pending", "yes", "", "high_planning", "Signal-loss/unsafe-state logical flag."],
    ["watchdog_alive", "minimal_watchdog_alive", "new", "", "1", "watchdog_state", "watchdog_safe_state", "watchdog_service", "WATCHDOG_SERVICE_EVENT", "BOOT_SAFE_STATE", "false until serviced", "false triggers safe", "no", "no", "", "none", "MINIMAL_OS_EXECUTION_SCHEDULER.md; MINIMAL_OS_BOOT_SAFE_STATE.md", "watchdog hardware policy pending", "yes", "", "medium_planning", "Foreground-loop alive proof."],
    ["output_safe_state", "minimal_output_safe_state", "new", "", "mixed", "boot_state", "boot", "safe_defaults", "RESET_ENTRY; DROPOUT_SAFE_STATE; WATCHDOG_SAFE_STATE", "fuel/spark/IAC outputs", "safe", "safe", "no", "no", "", "none", "MINIMAL_OS_BOOT_SAFE_STATE.md", "exact reset values pending", "yes", "", "high_planning", "Top-level safe-output request state."],
    ["bench_hook_state", "minimal_bench_hook_state", "new", "", "mixed", "aldl_debug_state", "aldl_debug", "bench_hook", "BENCH_ONLY_HOOK; ALDL_SERVICE_EVENT", "ALDL/debug output", "disabled", "disabled", "no", "no", "", "none", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "bench harness only", "likely", "", "medium_planning", "Bench/debug observation state; no control ownership."],
    ["aldl_debug_snapshot", "minimal_aldl_snapshot", "new", "", "mixed", "aldl_debug_state", "aldl_debug", "debug_service", "ALDL_SERVICE_EVENT", "bench/logging", "empty", "safe-state snapshot", "no", "no", "", "ALDL/debug index future", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "future debug map will select exposed variables", "likely", "", "medium_planning", "Logical debug snapshot, not a hardware owner."],

    # Exclusions and unknown
    ["trans_shift_tcc_state", "stock_trans_state", "stock/various", "", "mixed", "excluded_stock_state", "excluded", "transmission", "EXCLUDED", "none", "not carried", "not carried", "unknown", "no", "", "trans_excluded", "CALIBRATION_SOURCE_INDEX.md", "none", "no", "transmission/TCC strategy excluded unless hardware-required", "high_policy", "Do not carry forward stock transmission/TCC state."],
    ["egr_state", "stock_egr_state", "stock/various", "", "mixed", "excluded_stock_state", "excluded", "egr", "EXCLUDED", "none", "not carried", "not carried", "unknown", "no", "", "egr_excluded", "CALIBRATION_SOURCE_INDEX.md", "none", "no", "EGR strategy excluded unless hardware-required", "high_policy", "Do not carry forward stock EGR state."],
    ["evap_purge_state", "stock_evap_state", "stock/various", "", "mixed", "excluded_stock_state", "excluded", "evap", "EXCLUDED", "none", "not carried", "not carried", "unknown", "no", "", "evap_excluded", "CALIBRATION_SOURCE_INDEX.md", "none", "no", "EVAP/purge strategy excluded unless hardware-required", "high_policy", "Do not carry forward stock EVAP/purge state."],
    ["emissions_diag_state", "stock_emissions_diag", "stock/various", "", "mixed", "excluded_stock_state", "excluded", "emissions_diag", "EXCLUDED", "none", "not carried", "not carried", "unknown", "no", "", "emissions_excluded", "CALIBRATION_SOURCE_INDEX.md", "none", "no", "diagnostic-only emissions state excluded unless safety/hardware-required", "high_policy", "Do not carry forward emissions diagnostic-only state."],
    ["unused_gm_mode_baggage", "stock_mode_baggage", "stock/various", "", "mixed", "excluded_stock_state", "excluded", "mode_baggage", "EXCLUDED", "none", "not carried", "not carried", "unknown", "no", "", "none", "MINIMAL_OS_STATE_VARIABLES.md", "none", "no", "unused GM mode baggage excluded", "high_policy", "Stock existence alone is not enough."],
    ["unknown_state", "unknown", "unknown", "unknown", "unknown", "unknown", "unknown", "unknown", "UNKNOWN", "UNKNOWN", "unknown", "unknown", "unknown", "candidate", "unknown", "unknown", "MINIMAL_OS_STATE_VARIABLES.md", "future source trace assigns ownership", "unknown", "", "low_unclassified", "Unknown state remains listed rather than guessed."],
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
        "# Minimal OS State Variables",
        "",
        "## Purpose",
        "",
        "Define the state-variable boundary for the minimal OS.",
        "",
        "This document consolidates source-proven symbols, hardware shadows, module state, scheduler state, boot-safe state, and bench-gated state. It does not allocate RAM or implement runtime code.",
        "",
        "## Source Dependencies",
        "",
        "- `MINIMAL_OS_MODULE_BOUNDARY.md`",
        "- `MINIMAL_OS_EXECUTION_SCHEDULER.md`",
        "- `MINIMAL_OS_BOOT_SAFE_STATE.md`",
        "- `FUEL_MINIMAL_MODULE_INPUTS.md`",
        "- `SPARK_MINIMAL_MODULE_INPUTS.md`",
        "- `IAC_MINIMAL_MODULE_INPUTS.md`",
        "- fuel/spark/IAC hardware contracts",
        "",
        "## Ownership Rule",
        "",
        "Every carried-forward state variable must have one owner.",
        "",
        "Examples:",
        "",
        "| Variable | Owner | Notes |",
        "|---|---|---|",
        "| `L3FCE` | fuel output | EFI PW command |",
        "| `L0007` | IAC position state | actual/present position |",
        "| `L01EE` | spark conversion | signed spark offset |",
        "| `L005F/L0060` | REF/DRP period | spark/fuel/RPM basis |",
        "",
        "## Carry-Forward Rule",
        "",
        "A stock variable is carried forward only if it is:",
        "",
        "- required by a hardware contract,",
        "- required by a module input contract,",
        "- required by boot/safe state,",
        "- required by scheduler/event timing,",
        "- required for ALDL/debug visibility,",
        "- or bench-gated but unresolved.",
        "",
        "Everything else remains excluded or unknown.",
        "",
        "## State Class Summary",
        "",
        "| State class | Count |",
        "|---|---:|",
    ]
    counts = {}
    for r in ROWS:
        counts[r[5]] = counts.get(r[5], 0) + 1
    for k in sorted(counts):
        lines.append(f"| `{k}` | {counts[k]} |")
    lines += [
        "",
        "## Hardware Shadows",
        "",
        "Hardware shadows and hardware-facing candidate registers are identified separately from logical state. They must not be treated as ordinary RAM variables.",
        "",
        "| State | Source symbol | Hardware address | Carry-forward | Bench dependency |",
        "|---|---|---|---|---|",
    ]
    for r in ROWS:
        if r[13] in {"yes", "candidate"}:
            lines.append(f"| `{r[0]}` | `{r[1]}` | `{r[14]}` | {r[18]} | {r[17]} |")
    lines += [
        "",
        "## State Variable Table",
        "",
        "| State | Source symbol | Address | Class | Owner | Producer | Consumer | Reset | Safe | Retained | Shadow | Carry-forward | Confidence |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in ROWS:
        lines.append(f"| `{r[0]}` | `{r[1]}` | `{r[2]}` | `{r[5]}` | {r[6]}/{r[7]} | {r[8]} | {r[9]} | {r[10]} | {r[11]} | {r[12]} | {r[13]} | {r[18]} | {r[20]} |")
    lines += [
        "",
        "## Explicit Exclusions",
        "",
        "The state map must not become a full stock RAM map. These are explicitly excluded unless a future hardware contract proves them required:",
        "",
        "```text",
        "transmission shift/TCC state",
        "EGR state",
        "EVAP/purge state",
        "emissions diagnostic-only state",
        "unused GM mode baggage",
        "```",
        "",
        "## Unknown State Rule",
        "",
        "Unknown state remains `unknown`; it must not be silently assigned to a module or carried forward solely because it exists in stock code.",
        "",
        "## Next Contract",
        "",
        "The next useful artifact is:",
        "",
        "```text",
        "MINIMAL_OS_ALDL_DEBUG_MAP",
        "```",
        "",
        "That pass should decide which state variables are exposed for bench proof and live debugging before implementation.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-md", required=True)
    p.add_argument("--out-csv", required=True)
    args = p.parse_args()
    write_csv(resolve(args.out_csv))
    write_md(resolve(args.out_md))
    print(f"MINIMAL_OS_STATE_VARIABLES: wrote {len(ROWS)} state rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
