# Minimal OS State Variables

## Purpose

Define the state-variable boundary for the minimal OS.

This document consolidates source-proven symbols, hardware shadows, module state, scheduler state, boot-safe state, and bench-gated state. It does not allocate RAM or implement runtime code.

## Source Dependencies

- `MINIMAL_OS_MODULE_BOUNDARY.md`
- `MINIMAL_OS_EXECUTION_SCHEDULER.md`
- `MINIMAL_OS_BOOT_SAFE_STATE.md`
- `FUEL_MINIMAL_MODULE_INPUTS.md`
- `SPARK_MINIMAL_MODULE_INPUTS.md`
- `IAC_MINIMAL_MODULE_INPUTS.md`
- fuel/spark/IAC hardware contracts

## Ownership Rule

Every carried-forward state variable must have one owner.

Examples:

| Variable | Owner | Notes |
|---|---|---|
| `L3FCE` | fuel output | EFI PW command |
| `L0007` | IAC position state | actual/present position |
| `L01EE` | spark conversion | signed spark offset |
| `L005F/L0060` | REF/DRP period | spark/fuel/RPM basis |

## Carry-Forward Rule

A stock variable is carried forward only if it is:

- required by a hardware contract,
- required by a module input contract,
- required by boot/safe state,
- required by scheduler/event timing,
- required for ALDL/debug visibility,
- or bench-gated but unresolved.

Everything else remains excluded or unknown.

## State Class Summary

| State class | Count |
|---|---:|
| `aldl_debug_state` | 2 |
| `bench_gated_state` | 7 |
| `boot_state` | 2 |
| `calibration_reference` | 1 |
| `excluded_stock_state` | 5 |
| `fuel_state` | 6 |
| `hardware_shadow` | 3 |
| `iac_state` | 8 |
| `scheduler_state` | 6 |
| `sensor_state` | 2 |
| `spark_state` | 8 |
| `unknown` | 1 |
| `watchdog_state` | 2 |

## Hardware Shadows

Hardware shadows and hardware-facing candidate registers are identified separately from logical state. They must not be treated as ordinary RAM variables.

| State | Source symbol | Hardware address | Carry-forward | Bench dependency |
|---|---|---|---|---|
| `efi_pw_command` | `L3FCE/L3FCF` | `$3FCE` | yes | `$3FCE` units and bench confirmation pending |
| `spark_asic_period_source` | `L3FC0/L3FC1` | `$3FC0/$3FC1` | bench_gated | physical role bench-gated |
| `spark_asic_cmd_1` | `L3FE8` | `$3FE8` | bench_gated | direct write forbidden until bench-proven |
| `spark_asic_cmd_2` | `L3FE6` | `$3FE6` | bench_gated | direct write forbidden until bench-proven |
| `spark_rolling_state` | `L3FDC` | `$3FDC` | bench_gated | first-event seed and rolling behavior bench-gated |
| `spark_rolling_anchor` | `L3FF6` | `$3FF6` | bench_gated | first-event anchor behavior bench-gated |
| `spark_status_mirror_ack` | `L3FEC -> L3FE4` | `$3FEC/$3FE4` | bench_gated | mirror/ack requirement bench-gated |
| `iac_output_shadow` | `L004C` | `L3062` | bench_gated | direct L3062 writer and physical pins bench-gated |
| `iac_latch` | `L3062` | `$3062` | bench_gated | direct write forbidden until bench-proven |
| `unknown_state` | `unknown` | `unknown` | unknown | future source trace assigns ownership |

## State Variable Table

| State | Source symbol | Address | Class | Owner | Producer | Consumer | Reset | Safe | Retained | Shadow | Carry-forward | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `efi_pw_command` | `L3FCE/L3FCF` | `$3FCE/$3FCF` | `hardware_shadow` | fuel/efi_pw_write | FUEL_OUTPUT_EVENT | fuel hardware output | $0000 | $0000/no-pulse | no | yes | yes | high_static_bench_pending |
| `sync_bpw_source` | `L024E` | `$024E` | `fuel_state` | fuel/base_pw | FUEL_CALC_EVENT | fuel calculation / EFI PW writer | unknown | zero/no-fuel if invalid | no | no | bench_gated | medium_static |
| `bpw_intermediate_final` | `L0250` | `$0250` | `fuel_state` | fuel/base_pw | FUEL_CALC_EVENT | fuel correction / output scale | unknown | zero/no-fuel if invalid | no | no | bench_gated | medium_static |
| `fuel_enable_no_fuel_gate` | `minimal_fuel_enable` | `new` | `fuel_state` | fuel/mode_gate | BOOT_SAFE_STATE; FUEL_CALC_EVENT; DROPOUT_SAFE_STATE | FUEL_OUTPUT_EVENT | disabled | disabled/no-pulse | no | no | yes | high_planning |
| `dfco_zero_gate` | `minimal_dfco_zero_gate` | `new` | `fuel_state` | fuel/dfco_no_fuel | FUEL_CALC_EVENT | FUEL_OUTPUT_EVENT | disabled or zero-for-safe | force D=0 when active | no | no | yes | high_planning |
| `injector_low_pw_correction_state` | `minimal_low_pw_tf_state` | `new` | `fuel_state` | fuel/injector_model | FUEL_CALC_EVENT | FUEL_OUTPUT_EVENT | identity/pass-through | identity or zero output if invalid | no | no | yes | medium_planning |
| `battery_deadtime_correction_state` | `minimal_deadtime_state` | `new` | `fuel_state` | fuel/injector_model | SENSOR_SAMPLE_EVENT; FUEL_CALC_EVENT | FUEL_OUTPUT_EVENT | safe default | safe default or zero output if invalid | no | no | yes | medium_planning |
| `spark_final_advance_accum` | `L01FD` | `$01FD` | `spark_state` | spark/spark_intent | SPARK_PERIOD_EVENT | SPARK_PERIOD_EVENT | unknown | safe/no-authority intent | no | no | bench_gated | high_static |
| `spark_signed_offset` | `L01EE` | `$01EE` | `spark_state` | spark/degree_to_time_conversion | SPARK_PERIOD_EVENT | SPARK_PERIOD_EVENT | unknown | zero/safe offset | no | no | bench_gated | high_static |
| `spark_sign_direction_flag` | `L004F` | `$004F` | `spark_state` | spark/degree_to_time_conversion | SPARK_PERIOD_EVENT | SPARK_PERIOD_EVENT | unknown | safe sign/default | no | no | bench_gated | high_static |
| `spark_latency_correction` | `L0201` | `$0201` | `spark_state` | spark/latency | SPARK_PERIOD_EVENT | SPARK_PERIOD_EVENT | unknown | safe latency default | no | no | bench_gated | high_static |
| `drp_ref_period_basis` | `L005F/L0060` | `$005F/$0060` | `sensor_state` | ref_rpm_period/period_capture | REF_DRP_EVENT | fuel/spark/IAC inputs | invalid | invalid/dropout | no | no | yes | high_static |
| `spark_asic_period_source` | `L3FC0/L3FC1` | `$3FC0/$3FC1` | `bench_gated_state` | spark/asic_handoff_candidate | SPARK_PERIOD_EVENT | SPARK_OUTPUT_EVENT | unknown | blocked | no | candidate | bench_gated | medium_static |
| `spark_asic_cmd_1` | `L3FE8` | `$3FE8` | `bench_gated_state` | spark/asic_handoff_candidate | SPARK_OUTPUT_EVENT | hardware | blocked | blocked | no | candidate | bench_gated | high_policy |
| `spark_asic_cmd_2` | `L3FE6` | `$3FE6` | `bench_gated_state` | spark/asic_handoff_candidate | SPARK_OUTPUT_EVENT | hardware | blocked | blocked | no | candidate | bench_gated | high_policy |
| `spark_rolling_state` | `L3FDC` | `$3FDC` | `bench_gated_state` | spark/rolling_state | SPARK_PERIOD_EVENT | SPARK_OUTPUT_EVENT | blocked | blocked | maybe | candidate | bench_gated | high_static |
| `spark_rolling_anchor` | `L3FF6` | `$3FF6` | `bench_gated_state` | spark/rolling_state | SPARK_PERIOD_EVENT | SPARK_OUTPUT_EVENT | blocked | blocked | maybe | candidate | bench_gated | high_static |
| `spark_status_mirror_ack` | `L3FEC -> L3FE4` | `$3FEC/$3FE4` | `bench_gated_state` | spark/status_ack | SPARK_OUTPUT_EVENT | SPARK_EST_FAULT_MONITOR | blocked | blocked | unknown | candidate | bench_gated | medium_static |
| `est_monitor_enable` | `L004F` | `$004F` | `spark_state` | spark/est_fault_monitor | SPARK_PERIOD_EVENT | SPARK_EST_FAULT_MONITOR | disabled/unknown | disabled/safe | no | no | bench_gated | medium_static |
| `engine_running_flag` | `L004F` | `$004F` | `scheduler_state` | scheduler/run_qualify | REF_DRP_EVENT | all runtime modules | not running | not running/dropout | no | no | yes | medium_static |
| `first_drp_valid` | `L0044` | `$0044` | `scheduler_state` | ref_rpm_period/first_period_valid | REF_DRP_EVENT | scheduler/spark | invalid | invalid | no | no | yes | medium_static |
| `drp_event_counter` | `L0210` | `$0210` | `scheduler_state` | ref_rpm_period/run_qualify | REF_DRP_EVENT | scheduler/spark | 0 | 0/dropout | no | no | bench_gated | medium_static |
| `est_error_counter` | `L022C` | `$022C` | `spark_state` | spark/est_fault_monitor | SPARK_EST_FAULT_MONITOR | ALDL_DEBUG_EVENT | 0 | 0 or fault-held | no | no | bench_gated | medium_static |
| `prior_est_ref_sample` | `L0205` | `$0205` | `spark_state` | spark/est_fault_monitor | SPARK_EST_FAULT_MONITOR | SPARK_EST_FAULT_MONITOR | unknown | safe/unknown | no | no | bench_gated | medium_static |
| `iac_actual_position` | `L0007` | `$0007` | `iac_state` | iac_idle/position_state | IAC_CADENCE_EVENT; RAM_STATE_SEED | IAC_CADENCE_EVENT; ALDL_DEBUG_EVENT | unknown/seeded | hold/no motion | maybe | no | yes | high_static |
| `iac_desired_position` | `L0008` | `$0008` | `iac_state` | iac_idle/position_state | IAC_CADENCE_EVENT; CRANK_INIT | IAC_CADENCE_EVENT | safe target/hold | hold/no motion | no | no | yes | high_static |
| `iac_reset_in_work` | `L0009` | `$0009` | `iac_state` | iac_idle/startup_park | RESET_INIT; IAC_CADENCE_EVENT | IAC_CADENCE_EVENT | unknown/reset policy | hold/no motion | maybe | no | yes | high_static |
| `iac_rs_requested` | `L0009` | `$0009` | `iac_state` | iac_idle/startup_park | RESET_INIT; shutdown/park policy | IAC_CADENCE_EVENT | unknown | hold/no motion | maybe | no | bench_gated | high_static |
| `iac_direction` | `L000A` | `$000A` | `iac_state` | iac_idle/phase_state | IAC_CADENCE_EVENT | IAC_CADENCE_EVENT | unknown/hold | hold/no motion | maybe | no | yes | high_static |
| `iac_phase_a` | `L000A` | `$000A` | `iac_state` | iac_idle/phase_state | IAC_CADENCE_EVENT | IAC_OUTPUT_EVENT | hold/unknown | hold/no motion | maybe | no | yes | high_static |
| `iac_phase_b` | `L000A` | `$000A` | `iac_state` | iac_idle/phase_state | IAC_CADENCE_EVENT | IAC_OUTPUT_EVENT | hold/unknown | hold/no motion | maybe | no | yes | high_static |
| `iac_enable_candidate` | `L000A` | `$000A` | `iac_state` | iac_idle/enable_gate | IAC_CADENCE_EVENT; RESET_INIT | IAC_OUTPUT_EVENT | disabled/unknown | disabled/hold | maybe | no | yes | high_static |
| `iac_output_shadow` | `L004C` | `$004C` | `hardware_shadow` | iac_idle/output_shadow | IAC_OUTPUT_EVENT | IAC hardware latch | safe/hold | hold/no motion | maybe | yes | bench_gated | high_static |
| `iac_latch` | `L3062` | `$3062` | `hardware_shadow` | iac_idle/hardware_latch | IAC_OUTPUT_EVENT | hardware | blocked | blocked | no | candidate | bench_gated | high_policy |
| `iac_park_down_scalar` | `L4EB0` | `$4EB0` | `calibration_reference` | iac_idle/startup_park | RESET_INIT; IAC_CADENCE_EVENT | IAC startup/park policy | 145 stock value | software reference only | no | no | bench_gated | high_static |
| `battery_voltage_vdc10` | `L00A7` | `$00A7` | `sensor_state` | sensors/battery_voltage | SENSOR_SAMPLE_EVENT | fuel/IAC/spark corrections | invalid/unknown | safe low/invalid | no | no | yes | high_static |
| `low_battery_protection` | `L003E` | `$003E` | `watchdog_state` | watchdog_safe_state/protection_gate | SENSOR_SAMPLE_EVENT; BOOT_SAFE_STATE | IAC enable / fuel safe state | safe/protect | protect | no | no | bench_gated | medium_static |
| `rpm_valid` | `minimal_rpm_valid` | `new` | `scheduler_state` | ref_rpm_period/period_valid | REF_DRP_EVENT; DROPOUT_SAFE_STATE | fuel/spark/IAC scheduler gates | false | false | no | no | yes | high_planning |
| `ref_drp_valid` | `minimal_ref_drp_valid` | `new` | `scheduler_state` | ref_rpm_period/period_valid | REF_DRP_EVENT; DROPOUT_SAFE_STATE | all runtime modules | false | false | no | no | yes | high_planning |
| `first_period_valid` | `minimal_first_period_valid` | `new` | `scheduler_state` | ref_rpm_period/first_period_valid | REF_DRP_EVENT | spark/fuel/IAC run qualification | false | false | no | no | yes | high_planning |
| `crank_run_qualification` | `minimal_run_qual_state` | `new` | `scheduler_state` | scheduler/run_qualify | REF_DRP_EVENT; CRANK_INIT | fuel/spark/IAC events | crank/not-run | dropout/not-run | no | no | yes | high_planning |
| `dropout_state` | `minimal_dropout_state` | `new` | `boot_state` | watchdog_safe_state/dropout_safe_state | DROPOUT_SAFE_STATE | all runtime modules | false | true on loss | no | no | yes | high_planning |
| `watchdog_alive` | `minimal_watchdog_alive` | `new` | `watchdog_state` | watchdog_safe_state/watchdog_service | WATCHDOG_SERVICE_EVENT | BOOT_SAFE_STATE | false until serviced | false triggers safe | no | no | yes | medium_planning |
| `output_safe_state` | `minimal_output_safe_state` | `new` | `boot_state` | boot/safe_defaults | RESET_ENTRY; DROPOUT_SAFE_STATE; WATCHDOG_SAFE_STATE | fuel/spark/IAC outputs | safe | safe | no | no | yes | high_planning |
| `bench_hook_state` | `minimal_bench_hook_state` | `new` | `aldl_debug_state` | aldl_debug/bench_hook | BENCH_ONLY_HOOK; ALDL_SERVICE_EVENT | ALDL/debug output | disabled | disabled | no | no | likely | medium_planning |
| `aldl_debug_snapshot` | `minimal_aldl_snapshot` | `new` | `aldl_debug_state` | aldl_debug/debug_service | ALDL_SERVICE_EVENT | bench/logging | empty | safe-state snapshot | no | no | likely | medium_planning |
| `trans_shift_tcc_state` | `stock_trans_state` | `stock/various` | `excluded_stock_state` | excluded/transmission | EXCLUDED | none | not carried | not carried | unknown | no | no | high_policy |
| `egr_state` | `stock_egr_state` | `stock/various` | `excluded_stock_state` | excluded/egr | EXCLUDED | none | not carried | not carried | unknown | no | no | high_policy |
| `evap_purge_state` | `stock_evap_state` | `stock/various` | `excluded_stock_state` | excluded/evap | EXCLUDED | none | not carried | not carried | unknown | no | no | high_policy |
| `emissions_diag_state` | `stock_emissions_diag` | `stock/various` | `excluded_stock_state` | excluded/emissions_diag | EXCLUDED | none | not carried | not carried | unknown | no | no | high_policy |
| `unused_gm_mode_baggage` | `stock_mode_baggage` | `stock/various` | `excluded_stock_state` | excluded/mode_baggage | EXCLUDED | none | not carried | not carried | unknown | no | no | high_policy |
| `unknown_state` | `unknown` | `unknown` | `unknown` | unknown/unknown | UNKNOWN | UNKNOWN | unknown | unknown | unknown | candidate | unknown | low_unclassified |

## Explicit Exclusions

The state map must not become a full stock RAM map. These are explicitly excluded unless a future hardware contract proves them required:

```text
transmission shift/TCC state
EGR state
EVAP/purge state
emissions diagnostic-only state
unused GM mode baggage
```

## Unknown State Rule

Unknown state remains `unknown`; it must not be silently assigned to a module or carried forward solely because it exists in stock code.

## Next Contract

The next useful artifact is:

```text
MINIMAL_OS_ALDL_DEBUG_MAP
```

That pass should decide which state variables are exposed for bench proof and live debugging before implementation.
