#!/usr/bin/env python3
"""Build the minimal OS ALDL/debug visibility map.

This is planning only. It defines what should be visible for bench proof,
first-run validation, and troubleshooting. It does not implement ALDL packet
format, mode handlers, serial ISR changes, write authority, or runtime code.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

FIELDS = [
    "debug_name", "state_name", "source_symbol", "source_address", "bitmask",
    "width", "debug_class", "module_owner", "submodule_owner", "producer_event",
    "sample_event", "display_units", "conversion", "raw_value_required",
    "derived_value_allowed", "bench_required", "implementation_ready",
    "hardware_shadow", "hardware_address", "source_contract_dependency",
    "state_variable_dependency", "excluded_reason", "confidence", "notes",
]

ROWS = [
    # Fuel proof / first-run validation
    ["efi_pw_counts_raw", "efi_pw_command", "L3FCE/L3FCF", "$3FCE/$3FCF", "", "16", "hardware_shadow_debug", "fuel", "efi_pw_write", "FUEL_OUTPUT_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "raw 16-bit counts", "yes", "yes", "yes", "bench_gated", "yes", "$3FCE", "EFI_PW_3FCE_CONTRACT.md; MINIMAL_EFI_PW_WRITER.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "$3FCE counts must be directly visible or reconstructable."],
    ["efi_pw_ms", "efi_pw_command", "L3FCE/L3FCF", "$3FCE/$3FCF", "", "16", "fuel_debug", "fuel", "efi_pw_write", "FUEL_OUTPUT_EVENT", "ALDL_SERVICE_EVENT", "milliseconds", "EFI_PW_ms = counts / 65.536", "yes", "yes", "yes", "bench_gated", "yes", "$3FCE", "EFI_PW_UNITS.md; MINIMAL_EFI_PW_WRITER.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Derived milliseconds view for bench validation."],
    ["fuel_enable_no_fuel_gate", "fuel_enable_no_fuel_gate", "minimal_fuel_enable", "new", "", "1", "fuel_debug", "fuel", "mode_gate", "FUEL_CALC_EVENT", "ALDL_SERVICE_EVENT", "boolean", "0=disabled/no-fuel, 1=enabled", "yes", "yes", "yes", "planning_only", "no", "", "FUEL_MINIMAL_MODULE_INPUTS.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Nonzero fuel must not be possible unless gate permits it."],
    ["dfco_zero_gate", "dfco_zero_gate", "minimal_dfco_zero_gate", "new", "", "1", "fuel_debug", "fuel", "dfco_no_fuel", "FUEL_CALC_EVENT", "ALDL_SERVICE_EVENT", "boolean", "1=force D=0", "yes", "yes", "yes", "planning_only", "no", "", "FUEL_MINIMAL_MODULE_INPUTS.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Proves DFCO/no-fuel zero gate behavior."],
    ["sync_base_bpw_candidate", "sync_bpw_source", "L024E", "$024E", "", "16", "fuel_debug", "fuel", "base_pw", "FUEL_CALC_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "raw candidate", "yes", "yes", "maybe", "bench_gated", "no", "", "FUEL_MINIMAL_MODULE_INPUTS.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Source-proven candidate, exact role still source-gated."],
    ["final_bpw_candidate", "bpw_intermediate_final", "L0250", "$0250", "", "16", "fuel_debug", "fuel", "base_pw", "FUEL_CALC_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "raw candidate", "yes", "yes", "maybe", "bench_gated", "no", "", "FUEL_MINIMAL_MODULE_INPUTS.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Final/intermediate BPW candidate."],
    ["injector_deadtime_correction", "battery_deadtime_correction_state", "minimal_deadtime_state", "new", "", "mixed", "fuel_debug", "fuel", "injector_model", "FUEL_CALC_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "raw correction / future usec display", "yes", "yes", "maybe", "planning_only", "no", "", "FUEL_MINIMAL_MODULE_INPUTS.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Deadtime/battery correction visibility."],
    ["low_pw_transfer_correction", "injector_low_pw_correction_state", "minimal_low_pw_tf_state", "new", "", "mixed", "fuel_debug", "fuel", "injector_model", "FUEL_CALC_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "raw transfer input/output pair when implemented", "yes", "yes", "yes", "planning_only", "no", "", "FUEL_MINIMAL_MODULE_INPUTS.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Needed for low-PW bench validation."],
    ["battery_voltage", "battery_voltage_vdc10", "L00A7", "$00A7", "", "8", "sensor_debug", "sensors", "battery_voltage", "SENSOR_SAMPLE_EVENT", "ALDL_SERVICE_EVENT", "volts", "volts = L00A7 / 10", "yes", "yes", "yes", "planning_only", "no", "", "IAC_ENABLE_FAULT_GATE_CONTRACT.md; FUEL_MINIMAL_MODULE_INPUTS.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Known candidate scale VDC/10."],
    ["rpm", "drp_ref_period_basis", "L005F/L0060", "$005F/$0060", "", "16", "sensor_debug", "ref_rpm_period", "period_capture", "REF_DRP_EVENT", "ALDL_SERVICE_EVENT", "rpm", "derived from DRP/ref period after unit proof", "yes", "yes", "yes", "bench_gated", "no", "", "SPARK_TIMEBASE_PERIOD_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "RPM display is required for fuel/spark/IAC validation."],
    ["map_kpa", "map_sensor", "minimal_map", "new/source", "", "mixed", "sensor_debug", "sensors", "map", "SENSOR_SAMPLE_EVENT", "ALDL_SERVICE_EVENT", "kpa", "future MAP scaling", "yes", "yes", "yes", "planning_only", "no", "", "FUEL_MINIMAL_MODULE_INPUTS.md; SPARK_MINIMAL_MODULE_INPUTS.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Logical MAP exposure selected from module input contracts."],
    ["tps", "tps_sensor", "minimal_tps", "new/source", "", "mixed", "sensor_debug", "sensors", "tps", "SENSOR_SAMPLE_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "future TPS volts/percent scaling", "yes", "yes", "yes", "planning_only", "no", "", "FUEL_MINIMAL_MODULE_INPUTS.md; IAC_MINIMAL_MODULE_INPUTS.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Throttle state needed for fuel/IAC validation."],
    ["coolant_temperature", "cts_sensor", "minimal_cts", "new/source", "", "mixed", "sensor_debug", "sensors", "coolant", "SENSOR_SAMPLE_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "future CTS temperature scaling", "yes", "yes", "yes", "planning_only", "no", "", "FUEL_MINIMAL_MODULE_INPUTS.md; IAC_MINIMAL_MODULE_INPUTS.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Coolant drives warmup/crank/IAC targets."],
    ["target_afr_stoich", "target_afr_stoich_state", "minimal_target_afr", "new", "", "mixed", "fuel_debug", "fuel", "target_afr", "FUEL_CALC_EVENT", "ALDL_SERVICE_EVENT", "afr", "future AFR/stoch scale", "yes", "yes", "maybe", "planning_only", "no", "", "FUEL_MINIMAL_MODULE_INPUTS.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Visible target AFR/stoich basis for first-run validation."],

    # Spark bench probes
    ["desired_spark_degrees", "spark_desired_degrees", "minimal_spark_intent", "new", "", "mixed", "spark_debug", "spark", "spark_intent", "SPARK_PERIOD_EVENT", "ALDL_SERVICE_EVENT", "degrees", "spark_degrees = count * 90 / 256 where source count scale applies", "yes", "yes", "yes", "planning_only", "no", "", "SPARK_MINIMAL_MODULE_INPUTS.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Desired spark intent is observable even before output handoff is safe."],
    ["spark_final_accum", "spark_final_advance_accum", "L01FD", "$01FD", "", "8", "spark_debug", "spark", "spark_intent", "SPARK_PERIOD_EVENT", "ALDL_SERVICE_EVENT", "degrees", "spark_degrees = count * 90 / 256", "yes", "yes", "yes", "bench_gated", "no", "", "SPARK_CONVERSION_EQUATION.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Final spark accumulator candidate."],
    ["spark_signed_offset", "spark_signed_offset", "L01EE", "$01EE", "", "16", "spark_debug", "spark", "degree_to_time_conversion", "SPARK_PERIOD_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "signed raw offset", "yes", "yes", "yes", "bench_gated", "no", "", "SPARK_CONVERSION_EQUATION.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Signed spark offset into conversion path."],
    ["spark_sign_flag", "spark_sign_direction_flag", "L004F", "$004F", "bit0", "1", "spark_debug", "spark", "degree_to_time_conversion", "SPARK_PERIOD_EVENT", "ALDL_SERVICE_EVENT", "boolean", "raw bit0", "yes", "yes", "yes", "bench_gated", "no", "", "SPARK_CONVERSION_EQUATION.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Spark sign/direction flag candidate."],
    ["spark_latency", "spark_latency_correction", "L0201", "$0201", "", "16", "spark_debug", "spark", "latency", "SPARK_PERIOD_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "raw latency candidate", "yes", "yes", "yes", "bench_gated", "no", "", "SPARK_CONVERSION_EQUATION.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Latency correction candidate."],
    ["drp_ref_period_basis", "drp_ref_period_basis", "L005F/L0060", "$005F/$0060", "", "16", "spark_debug", "ref_rpm_period", "period_capture", "REF_DRP_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "raw period basis; RPM derived separately", "yes", "yes", "yes", "bench_gated", "no", "", "SPARK_TIMEBASE_PERIOD_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Required to prove conversion timebase."],
    ["spark_asic_period_source", "spark_asic_period_source", "L3FC0/L3FC1", "$3FC0/$3FC1", "", "16", "bench_probe", "spark", "asic_handoff_candidate", "SPARK_PERIOD_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "raw ASIC period/capture candidate", "yes", "yes", "yes", "bench_gated", "candidate", "$3FC0/$3FC1", "SPARK_ASIC_HANDOFF_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Bench-visible only, not write authority."],
    ["spark_rolling_state", "spark_rolling_state", "L3FDC", "$3FDC", "", "16?", "bench_probe", "spark", "rolling_state", "SPARK_PERIOD_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "raw rolling state candidate", "yes", "yes", "yes", "bench_gated", "candidate", "$3FDC", "SPARK_ROLLING_STATE_MODEL.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Bench-visible rolling timing state candidate."],
    ["spark_rolling_anchor", "spark_rolling_anchor", "L3FF6", "$3FF6", "", "16?", "bench_probe", "spark", "rolling_state", "SPARK_PERIOD_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "raw rolling anchor candidate", "yes", "yes", "yes", "bench_gated", "candidate", "$3FF6", "SPARK_ROLLING_STATE_MODEL.md; SPARK_INIT_STATE.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Bench-visible rolling anchor candidate."],
    ["spark_asic_cmd_1", "spark_asic_cmd_1", "L3FE8", "$3FE8", "", "16?", "bench_probe", "spark", "asic_handoff_candidate", "SPARK_OUTPUT_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "raw handoff candidate", "yes", "yes", "yes", "bench_gated", "candidate", "$3FE8", "SPARK_ASIC_HANDOFF_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high_policy", "Debug exposure does not permit writes."],
    ["spark_asic_cmd_2", "spark_asic_cmd_2", "L3FE6", "$3FE6", "", "16?", "bench_probe", "spark", "asic_handoff_candidate", "SPARK_OUTPUT_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "raw handoff candidate", "yes", "yes", "yes", "bench_gated", "candidate", "$3FE6", "SPARK_ASIC_HANDOFF_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high_policy", "Debug exposure does not permit writes."],
    ["spark_status_mirror_ack", "spark_status_mirror_ack", "L3FEC -> L3FE4", "$3FEC/$3FE4", "", "mixed", "bench_probe", "spark", "status_ack", "SPARK_OUTPUT_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "raw status/mirror/ack candidate", "yes", "yes", "yes", "bench_gated", "candidate", "$3FEC/$3FE4", "SPARK_EST_FAULT_MONITOR_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Bench-visible only."],
    ["bypass_est_authority_state", "bypass_est_authority_state", "minimal_bypass_est_state", "new/source", "", "mixed", "spark_debug", "spark", "bypass_est_authority", "REF_DRP_EVENT", "ALDL_SERVICE_EVENT", "state_enum", "enum: bypass/EST/no-authority/unknown", "yes", "yes", "yes", "planning_only", "no", "", "SPARK_BYPASS_EST_TRANSITION.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Visibility only, no physical authority code."],
    ["engine_running_flag", "engine_running_flag", "L004F", "$004F", "bit7", "1", "scheduler_debug", "scheduler", "run_qualify", "REF_DRP_EVENT", "ALDL_SERVICE_EVENT", "boolean", "raw bit7 candidate", "yes", "yes", "yes", "bench_gated", "no", "", "SPARK_BYPASS_EST_TRANSITION.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Engine-running flag candidate."],
    ["first_drp_valid", "first_drp_valid", "L0044", "$0044", "bit3", "1", "scheduler_debug", "ref_rpm_period", "first_period_valid", "REF_DRP_EVENT", "ALDL_SERVICE_EVENT", "boolean", "raw bit3 candidate", "yes", "yes", "yes", "bench_gated", "no", "", "SPARK_BYPASS_EST_TRANSITION.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "First DRP valid candidate."],
    ["est_monitor_enable", "est_monitor_enable", "L004F", "$004F", "bit6", "1", "spark_debug", "spark", "est_fault_monitor", "SPARK_PERIOD_EVENT", "ALDL_SERVICE_EVENT", "boolean", "raw bit6 candidate", "yes", "yes", "maybe", "bench_gated", "no", "", "SPARK_EST_FAULT_MONITOR_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "EST monitor enable candidate."],
    ["est_error_counter", "est_error_counter", "L022C", "$022C", "", "8/16?", "spark_debug", "spark", "est_fault_monitor", "SPARK_EST_FAULT_MONITOR", "ALDL_SERVICE_EVENT", "raw_counts", "raw counter", "yes", "yes", "maybe", "bench_gated", "no", "", "SPARK_EST_FAULT_MONITOR_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "EST error counter candidate."],
    ["prior_est_ref_sample", "prior_est_ref_sample", "L0205", "$0205", "", "8/16?", "spark_debug", "spark", "est_fault_monitor", "SPARK_EST_FAULT_MONITOR", "ALDL_SERVICE_EVENT", "raw_counts", "raw sample", "yes", "yes", "maybe", "bench_gated", "no", "", "SPARK_EST_FAULT_MONITOR_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Prior EST/ref sample candidate."],

    # IAC bench probes
    ["iac_actual_position", "iac_actual_position", "L0007", "$0007", "", "8", "iac_debug", "iac_idle", "position_state", "IAC_CADENCE_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "IAC position = raw counts until physical direction is bench-proven", "yes", "yes", "yes", "bench_gated", "no", "", "IAC_IDLE_AIR_OUTPUT_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Actual/present IAC position."],
    ["iac_desired_position", "iac_desired_position", "L0008", "$0008", "", "8", "iac_debug", "iac_idle", "position_state", "IAC_CADENCE_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "raw target counts", "yes", "yes", "yes", "bench_gated", "no", "", "IAC_IDLE_AIR_OUTPUT_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Desired/target IAC position."],
    ["iac_position_error", "iac_position_error", "L0008-L0007", "$0008-$0007", "", "signed", "iac_debug", "iac_idle", "position_compare", "IAC_CADENCE_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "desired - actual raw counts", "yes", "yes", "yes", "bench_gated", "no", "", "IAC_MINIMAL_MODULE_INPUTS.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Error direction remains physical-direction gated."],
    ["iac_reset_in_work", "iac_reset_in_work", "L0009", "$0009", "bit0", "1", "iac_debug", "iac_idle", "startup_park", "RESET_INIT; IAC_CADENCE_EVENT", "ALDL_SERVICE_EVENT", "boolean", "raw bit0", "yes", "yes", "yes", "bench_gated", "no", "", "IAC_INIT_PARK_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Reset-in-work candidate."],
    ["iac_rs_requested", "iac_rs_requested", "L0009", "$0009", "bit2", "1", "iac_debug", "iac_idle", "startup_park", "RESET_INIT; IAC_CADENCE_EVENT", "ALDL_SERVICE_EVENT", "boolean", "raw bit2", "yes", "yes", "maybe", "bench_gated", "no", "", "IAC_INIT_PARK_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "R/S requested candidate."],
    ["iac_direction", "iac_direction", "L000A", "$000A", "bit0", "1", "iac_debug", "iac_idle", "phase_state", "IAC_CADENCE_EVENT", "ALDL_SERVICE_EVENT", "boolean", "raw bit0; open/close meaning bench-gated", "yes", "yes", "yes", "bench_gated", "no", "", "IAC_PHASE_SEQUENCE_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Direction bit visibility without physical meaning claim."],
    ["iac_phase_ab", "iac_phase_a/iac_phase_b", "L000A", "$000A", "bits2/3", "2", "iac_debug", "iac_idle", "phase_state", "IAC_CADENCE_EVENT", "ALDL_SERVICE_EVENT", "bitfield", "raw bits2/3", "yes", "yes", "yes", "bench_gated", "no", "", "IAC_PHASE_SEQUENCE_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "A/B phase state; physical pins bench-gated."],
    ["iac_enable_candidate", "iac_enable_candidate", "L000A", "$000A", "bit4", "1", "iac_debug", "iac_idle", "enable_gate", "IAC_CADENCE_EVENT", "ALDL_SERVICE_EVENT", "boolean", "raw bit4", "yes", "yes", "yes", "bench_gated", "no", "", "IAC_ENABLE_FAULT_GATE_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Enable candidate; physical function bench-gated."],
    ["iac_output_shadow", "iac_output_shadow", "L004C", "$004C", "bits2/3/4", "8", "hardware_shadow_debug", "iac_idle", "output_shadow", "IAC_OUTPUT_EVENT", "ALDL_SERVICE_EVENT", "bitfield", "raw shadow bits", "yes", "yes", "yes", "bench_gated", "yes", "L3062", "IAC_IDLE_AIR_OUTPUT_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Debug exposure does not permit IAC writes."],
    ["iac_latch_shadowed_value", "iac_latch", "L3062", "$3062", "bits2/3/4 candidates", "8", "bench_probe", "iac_idle", "hardware_latch", "IAC_OUTPUT_EVENT", "ALDL_SERVICE_EVENT", "bitfield", "raw latch or shadowed write value", "yes", "yes", "yes", "bench_gated", "candidate", "$3062", "IAC_IDLE_AIR_OUTPUT_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high_policy", "Visible for bench proof only; direct L3062 writes remain forbidden."],
    ["iac_park_down_value", "iac_park_down_scalar", "L4EB0", "$4EB0", "", "8", "calibration_reference", "iac_idle", "startup_park", "RESET_INIT", "ALDL_SERVICE_EVENT", "raw_counts", "raw 145-step stock value", "yes", "yes", "maybe", "bench_gated", "no", "", "IAC_INIT_PARK_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Physical direction and meaning bench-gated."],
    ["low_battery_protection", "low_battery_protection", "L003E", "$003E", "bit2", "1", "watchdog_debug", "watchdog_safe_state", "protection_gate", "SENSOR_SAMPLE_EVENT", "ALDL_SERVICE_EVENT", "boolean", "raw bit2", "yes", "yes", "maybe", "bench_gated", "no", "", "IAC_ENABLE_FAULT_GATE_CONTRACT.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Protection flag candidate."],
    ["iac_cadence_state", "iac_cadence_state", "minimal_iac_cadence", "new", "", "mixed", "iac_debug", "iac_idle", "cadence", "IAC_CADENCE_EVENT", "ALDL_SERVICE_EVENT", "state_enum", "cadence/rate-limit state enum", "yes", "yes", "yes", "planning_only", "no", "", "IAC_MINIMAL_MODULE_INPUTS.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Required before IAC writer implementation."],

    # Scheduler / boot / watchdog
    ["boot_stage", "output_safe_state", "minimal_output_safe_state", "new", "", "mixed", "boot_debug", "boot", "safe_defaults", "RESET_ENTRY; DROPOUT_SAFE_STATE", "ALDL_SERVICE_EVENT", "state_enum", "boot/safe state enum", "yes", "yes", "yes", "planning_only", "no", "", "MINIMAL_OS_BOOT_SAFE_STATE.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Shows reset/boot/dropout phase."],
    ["ref_drp_valid", "ref_drp_valid", "minimal_ref_drp_valid", "new", "", "1", "scheduler_debug", "ref_rpm_period", "period_valid", "REF_DRP_EVENT", "ALDL_SERVICE_EVENT", "boolean", "true when REF/DRP stream valid", "yes", "yes", "yes", "planning_only", "no", "", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Core scheduler proof value."],
    ["first_period_valid", "first_period_valid", "minimal_first_period_valid", "new", "", "1", "scheduler_debug", "ref_rpm_period", "first_period_valid", "REF_DRP_EVENT", "ALDL_SERVICE_EVENT", "boolean", "true after first accepted period", "yes", "yes", "yes", "planning_only", "no", "", "MINIMAL_OS_BOOT_SAFE_STATE.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "First period proof."],
    ["rpm_valid", "rpm_valid", "minimal_rpm_valid", "new", "", "1", "scheduler_debug", "ref_rpm_period", "period_valid", "REF_DRP_EVENT", "ALDL_SERVICE_EVENT", "boolean", "true when RPM usable", "yes", "yes", "yes", "planning_only", "no", "", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Runtime modules need this gate."],
    ["crank_run_qualification", "crank_run_qualification", "minimal_run_qual_state", "new", "", "mixed", "scheduler_debug", "scheduler", "run_qualify", "REF_DRP_EVENT; CRANK_INIT", "ALDL_SERVICE_EVENT", "state_enum", "crank/run/dropout enum", "yes", "yes", "yes", "planning_only", "no", "", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Proves crank/run handoff."],
    ["scheduler_event_counter", "scheduler_event_counter", "minimal_scheduler_event_counter", "new", "", "16", "scheduler_debug", "scheduler", "foreground_dispatch", "FOREGROUND_BACKGROUND_LOOP", "ALDL_SERVICE_EVENT", "raw_counts", "incrementing event counter", "yes", "yes", "yes", "planning_only", "no", "", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Future logical counter for event ordering proof."],
    ["foreground_loop_alive_counter", "watchdog_alive", "minimal_watchdog_alive", "new", "", "mixed", "watchdog_debug", "watchdog_safe_state", "watchdog_service", "WATCHDOG_SERVICE_EVENT", "ALDL_SERVICE_EVENT", "raw_counts", "loop alive counter or boolean", "yes", "yes", "yes", "planning_only", "no", "", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Proves foreground/service loop liveness."],
    ["dropout_state", "dropout_state", "minimal_dropout_state", "new", "", "1", "watchdog_debug", "watchdog_safe_state", "dropout_safe_state", "DROPOUT_SAFE_STATE", "ALDL_SERVICE_EVENT", "boolean", "true on signal loss/unsafe", "yes", "yes", "yes", "planning_only", "no", "", "MINIMAL_OS_BOOT_SAFE_STATE.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Dropout visibility."],
    ["output_safe_state", "output_safe_state", "minimal_output_safe_state", "new", "", "mixed", "boot_debug", "boot", "safe_defaults", "RESET_ENTRY; DROPOUT_SAFE_STATE; WATCHDOG_SAFE_STATE", "ALDL_SERVICE_EVENT", "state_enum", "output-safe state enum", "yes", "yes", "yes", "planning_only", "no", "", "MINIMAL_OS_BOOT_SAFE_STATE.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "high", "Shows when outputs are forced safe."],
    ["bench_hook_state", "bench_hook_state", "minimal_bench_hook_state", "new", "", "mixed", "bench_probe", "aldl_debug", "bench_hook", "BENCH_ONLY_HOOK", "ALDL_SERVICE_EVENT", "state_enum", "bench hook enum", "yes", "yes", "maybe", "planning_only", "no", "", "MINIMAL_OS_EXECUTION_SCHEDULER.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "medium", "Bench hook visibility only, no control ownership."],

    # Exclusions and unknown
    ["trans_tcc_aldl_baggage", "trans_shift_tcc_state", "stock_trans_state", "stock/various", "", "mixed", "excluded_stock_aldl", "excluded", "transmission", "EXCLUDED", "none", "unknown", "none", "no", "no", "no", "no", "no", "", "CALIBRATION_SOURCE_INDEX.md", "MINIMAL_OS_STATE_VARIABLES.md", "trans/TCC ALDL baggage excluded", "high_policy", "Not exposed unless future hardware contract proves required."],
    ["egr_aldl_baggage", "egr_state", "stock_egr_state", "stock/various", "", "mixed", "excluded_stock_aldl", "excluded", "egr", "EXCLUDED", "none", "unknown", "none", "no", "no", "no", "no", "no", "", "CALIBRATION_SOURCE_INDEX.md", "MINIMAL_OS_STATE_VARIABLES.md", "EGR ALDL baggage excluded", "high_policy", "Not exposed by minimal debug map."],
    ["evap_aldl_baggage", "evap_purge_state", "stock_evap_state", "stock/various", "", "mixed", "excluded_stock_aldl", "excluded", "evap", "EXCLUDED", "none", "unknown", "none", "no", "no", "no", "no", "no", "", "CALIBRATION_SOURCE_INDEX.md", "MINIMAL_OS_STATE_VARIABLES.md", "EVAP ALDL baggage excluded", "high_policy", "Not exposed by minimal debug map."],
    ["emissions_diag_aldl_baggage", "emissions_diag_state", "stock_emissions_diag", "stock/various", "", "mixed", "excluded_stock_aldl", "excluded", "emissions_diag", "EXCLUDED", "none", "unknown", "none", "no", "no", "no", "no", "no", "", "CALIBRATION_SOURCE_INDEX.md", "MINIMAL_OS_STATE_VARIABLES.md", "emissions-only ALDL baggage excluded", "high_policy", "Not exposed by minimal debug map."],
    ["stock_mode_word_baggage", "unused_gm_mode_baggage", "stock_mode_baggage", "stock/various", "", "mixed", "excluded_stock_aldl", "excluded", "mode_baggage", "EXCLUDED", "none", "unknown", "none", "no", "no", "no", "no", "no", "", "MINIMAL_OS_STATE_VARIABLES.md", "MINIMAL_OS_STATE_VARIABLES.md", "unused stock mode-word baggage excluded", "high_policy", "Stock ALDL presence alone is not enough."],
    ["unknown_debug_value", "unknown_state", "unknown", "unknown", "unknown", "unknown", "unknown", "unknown", "unknown", "UNKNOWN", "ALDL_SERVICE_EVENT", "unknown", "unknown", "yes", "yes", "maybe", "planning_only", "candidate", "unknown", "MINIMAL_OS_STATE_VARIABLES.md", "MINIMAL_OS_STATE_VARIABLES.md", "", "low_unclassified", "Unknown debug values stay listed, not guessed."],
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
        "# Minimal OS ALDL Debug Map",
        "",
        "## Purpose",
        "",
        "Define the debug visibility boundary for the minimal OS.",
        "",
        "This document identifies which internal state, hardware shadows, and bench-gated candidates should be exposed for ALDL/debug observation. It does not implement ALDL packet format, mode handlers, serial code, or runtime ASM.",
        "",
        "## Source Dependencies",
        "",
        "- `MINIMAL_OS_STATE_VARIABLES.md`",
        "- `MINIMAL_OS_EXECUTION_SCHEDULER.md`",
        "- `MINIMAL_OS_BOOT_SAFE_STATE.md`",
        "- `FUEL_MINIMAL_MODULE_INPUTS.md`",
        "- `SPARK_MINIMAL_MODULE_INPUTS.md`",
        "- `IAC_MINIMAL_MODULE_INPUTS.md`",
        "- fuel/spark/IAC hardware contracts",
        "",
        "## Debug Priority",
        "",
        "Priority 1:",
        "",
        "- values required to prove hardware contracts",
        "- values required to prove bench-gated outputs",
        "- values required to diagnose boot/dropout safe state",
        "",
        "Priority 2:",
        "",
        "- values needed for first minimal fuel/spark/IAC validation",
        "",
        "Priority 3:",
        "",
        "- convenience values for later tuning/refinement",
        "",
        "Excluded:",
        "",
        "- trans/TCC ALDL baggage",
        "- EGR/EVAP/emissions-only diagnostic visibility",
        "- stock mode words not carried forward by the state-variable contract",
        "",
        "## ALDL Rule",
        "",
        "A value may be exposed for debug even if its owning runtime module is not implementation-ready.",
        "",
        "A value must not be treated as implementation-ready merely because it appears in the debug map.",
        "",
        "## Conversion Rules",
        "",
        "```text",
        "EFI_PW_ms = counts / 65.536",
        "spark_degrees = count * 90 / 256",
        "L00A7 volts = L00A7 / 10",
        "IAC position = raw counts until physical direction is bench-proven",
        "```",
        "",
        "## Guardrails",
        "",
        "```text",
        "Debug exposure of $3FE8/$3FE6/$3FF6/$3FDC does not permit spark writes.",
        "Debug exposure of L3062/L004C does not permit IAC writes.",
        "Debug exposure of $3FCE does not permit nonzero fuel unless fuel gates permit it.",
        "ALDL visibility is observational only.",
        "```",
        "",
        "## Debug Class Summary",
        "",
        "| Debug class | Count |",
        "|---|---:|",
    ]
    counts = {}
    for r in ROWS:
        counts[r[6]] = counts.get(r[6], 0) + 1
    for k in sorted(counts):
        lines.append(f"| `{k}` | {counts[k]} |")
    lines += [
        "",
        "## Debug Map Table",
        "",
        "| Debug name | State | Symbol | Units | Conversion | Bench required | Implementation ready | Shadow | Notes |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in ROWS:
        lines.append(f"| `{r[0]}` | `{r[1]}` | `{r[2]}` | `{r[11]}` | {r[12]} | {r[15]} | {r[16]} | {r[17]} | {r[23]} |")
    lines += [
        "",
        "## Explicit Exclusions",
        "",
        "```text",
        "trans/TCC ALDL baggage",
        "EGR ALDL baggage",
        "EVAP/purge ALDL baggage",
        "emissions-only diagnostic visibility",
        "unused stock mode-word baggage",
        "```",
        "",
        "## Unknown Debug Rule",
        "",
        "Unknown debug values remain visible as `unknown`; they must not be guessed into a module or carried forward solely because stock ALDL exposed something similar.",
        "",
        "## Next Decision Point",
        "",
        "After this pass, the planning stack is strong enough for either:",
        "",
        "```text",
        "bench proof package",
        "first minimal fuel-only runnable slice",
        "```",
        "",
        "The fuel-only slice is the only plausible implementation path before spark and IAC output bench gates are closed.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state-vars", default="maps/contracts/minimal_os_state_variables.csv")
    p.add_argument("--out-md", required=True)
    p.add_argument("--out-csv", required=True)
    args = p.parse_args()
    state_vars = resolve(args.state_vars)
    if not state_vars.exists():
        raise SystemExit(f"missing state variable map: {state_vars}")
    write_csv(resolve(args.out_csv))
    write_md(resolve(args.out_md))
    print(f"MINIMAL_OS_ALDL_DEBUG_MAP: wrote {len(ROWS)} debug rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
