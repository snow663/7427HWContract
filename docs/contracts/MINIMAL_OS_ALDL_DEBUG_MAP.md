# Minimal OS ALDL Debug Map

## Purpose

Define the debug visibility boundary for the minimal OS.

This document identifies which internal state, hardware shadows, and bench-gated candidates should be exposed for ALDL/debug observation. It does not implement ALDL packet format, mode handlers, serial code, or runtime ASM.

## Source Dependencies

- `MINIMAL_OS_STATE_VARIABLES.md`
- `MINIMAL_OS_EXECUTION_SCHEDULER.md`
- `MINIMAL_OS_BOOT_SAFE_STATE.md`
- `FUEL_MINIMAL_MODULE_INPUTS.md`
- `SPARK_MINIMAL_MODULE_INPUTS.md`
- `IAC_MINIMAL_MODULE_INPUTS.md`
- fuel/spark/IAC hardware contracts

## Debug Priority

Priority 1:

- values required to prove hardware contracts
- values required to prove bench-gated outputs
- values required to diagnose boot/dropout safe state

Priority 2:

- values needed for first minimal fuel/spark/IAC validation

Priority 3:

- convenience values for later tuning/refinement

Excluded:

- trans/TCC ALDL baggage
- EGR/EVAP/emissions-only diagnostic visibility
- stock mode words not carried forward by the state-variable contract

## ALDL Rule

A value may be exposed for debug even if its owning runtime module is not implementation-ready.

A value must not be treated as implementation-ready merely because it appears in the debug map.

## Conversion Rules

```text
EFI_PW_ms = counts / 65.536
spark_degrees = count * 90 / 256
L00A7 volts = L00A7 / 10
IAC position = raw counts until physical direction is bench-proven
```

## Guardrails

```text
Debug exposure of $3FE8/$3FE6/$3FF6/$3FDC does not permit spark writes.
Debug exposure of L3062/L004C does not permit IAC writes.
Debug exposure of $3FCE does not permit nonzero fuel unless fuel gates permit it.
ALDL visibility is observational only.
```

## Debug Class Summary

| Debug class | Count |
|---|---:|
| `bench_probe` | 9 |
| `boot_debug` | 2 |
| `calibration_reference` | 1 |
| `excluded_stock_aldl` | 5 |
| `fuel_debug` | 8 |
| `hardware_shadow_debug` | 2 |
| `iac_debug` | 11 |
| `scheduler_debug` | 6 |
| `sensor_debug` | 5 |
| `spark_debug` | 12 |
| `unknown` | 1 |
| `watchdog_debug` | 3 |

## Debug Map Table

| Debug name | State | Symbol | Units | Conversion | Bench required | Implementation ready | Shadow | Notes |
|---|---|---|---|---|---|---|---|---|
| `efi_pw_counts_raw` | `efi_pw_command` | `L3FCE/L3FCF` | `raw_counts` | raw 16-bit counts | yes | bench_gated | yes | $3FCE counts must be directly visible or reconstructable. |
| `efi_pw_ms` | `efi_pw_command` | `L3FCE/L3FCF` | `milliseconds` | EFI_PW_ms = counts / 65.536 | yes | bench_gated | yes | Derived milliseconds view for bench validation. |
| `fuel_enable_no_fuel_gate` | `fuel_enable_no_fuel_gate` | `minimal_fuel_enable` | `boolean` | 0=disabled/no-fuel, 1=enabled | yes | planning_only | no | Nonzero fuel must not be possible unless gate permits it. |
| `dfco_zero_gate` | `dfco_zero_gate` | `minimal_dfco_zero_gate` | `boolean` | 1=force D=0 | yes | planning_only | no | Proves DFCO/no-fuel zero gate behavior. |
| `sync_base_bpw_candidate` | `sync_bpw_source` | `L024E` | `raw_counts` | raw candidate | maybe | bench_gated | no | Source-proven candidate, exact role still source-gated. |
| `final_bpw_candidate` | `bpw_intermediate_final` | `L0250` | `raw_counts` | raw candidate | maybe | bench_gated | no | Final/intermediate BPW candidate. |
| `injector_deadtime_correction` | `battery_deadtime_correction_state` | `minimal_deadtime_state` | `raw_counts` | raw correction / future usec display | maybe | planning_only | no | Deadtime/battery correction visibility. |
| `low_pw_transfer_correction` | `injector_low_pw_correction_state` | `minimal_low_pw_tf_state` | `raw_counts` | raw transfer input/output pair when implemented | yes | planning_only | no | Needed for low-PW bench validation. |
| `battery_voltage` | `battery_voltage_vdc10` | `L00A7` | `volts` | volts = L00A7 / 10 | yes | planning_only | no | Known candidate scale VDC/10. |
| `rpm` | `drp_ref_period_basis` | `L005F/L0060` | `rpm` | derived from DRP/ref period after unit proof | yes | bench_gated | no | RPM display is required for fuel/spark/IAC validation. |
| `map_kpa` | `map_sensor` | `minimal_map` | `kpa` | future MAP scaling | yes | planning_only | no | Logical MAP exposure selected from module input contracts. |
| `tps` | `tps_sensor` | `minimal_tps` | `raw_counts` | future TPS volts/percent scaling | yes | planning_only | no | Throttle state needed for fuel/IAC validation. |
| `coolant_temperature` | `cts_sensor` | `minimal_cts` | `raw_counts` | future CTS temperature scaling | yes | planning_only | no | Coolant drives warmup/crank/IAC targets. |
| `target_afr_stoich` | `target_afr_stoich_state` | `minimal_target_afr` | `afr` | future AFR/stoch scale | maybe | planning_only | no | Visible target AFR/stoich basis for first-run validation. |
| `desired_spark_degrees` | `spark_desired_degrees` | `minimal_spark_intent` | `degrees` | spark_degrees = count * 90 / 256 where source count scale applies | yes | planning_only | no | Desired spark intent is observable even before output handoff is safe. |
| `spark_final_accum` | `spark_final_advance_accum` | `L01FD` | `degrees` | spark_degrees = count * 90 / 256 | yes | bench_gated | no | Final spark accumulator candidate. |
| `spark_signed_offset` | `spark_signed_offset` | `L01EE` | `raw_counts` | signed raw offset | yes | bench_gated | no | Signed spark offset into conversion path. |
| `spark_sign_flag` | `spark_sign_direction_flag` | `L004F` | `boolean` | raw bit0 | yes | bench_gated | no | Spark sign/direction flag candidate. |
| `spark_latency` | `spark_latency_correction` | `L0201` | `raw_counts` | raw latency candidate | yes | bench_gated | no | Latency correction candidate. |
| `drp_ref_period_basis` | `drp_ref_period_basis` | `L005F/L0060` | `raw_counts` | raw period basis; RPM derived separately | yes | bench_gated | no | Required to prove conversion timebase. |
| `spark_asic_period_source` | `spark_asic_period_source` | `L3FC0/L3FC1` | `raw_counts` | raw ASIC period/capture candidate | yes | bench_gated | candidate | Bench-visible only, not write authority. |
| `spark_rolling_state` | `spark_rolling_state` | `L3FDC` | `raw_counts` | raw rolling state candidate | yes | bench_gated | candidate | Bench-visible rolling timing state candidate. |
| `spark_rolling_anchor` | `spark_rolling_anchor` | `L3FF6` | `raw_counts` | raw rolling anchor candidate | yes | bench_gated | candidate | Bench-visible rolling anchor candidate. |
| `spark_asic_cmd_1` | `spark_asic_cmd_1` | `L3FE8` | `raw_counts` | raw handoff candidate | yes | bench_gated | candidate | Debug exposure does not permit writes. |
| `spark_asic_cmd_2` | `spark_asic_cmd_2` | `L3FE6` | `raw_counts` | raw handoff candidate | yes | bench_gated | candidate | Debug exposure does not permit writes. |
| `spark_status_mirror_ack` | `spark_status_mirror_ack` | `L3FEC -> L3FE4` | `raw_counts` | raw status/mirror/ack candidate | yes | bench_gated | candidate | Bench-visible only. |
| `bypass_est_authority_state` | `bypass_est_authority_state` | `minimal_bypass_est_state` | `state_enum` | enum: bypass/EST/no-authority/unknown | yes | planning_only | no | Visibility only, no physical authority code. |
| `engine_running_flag` | `engine_running_flag` | `L004F` | `boolean` | raw bit7 candidate | yes | bench_gated | no | Engine-running flag candidate. |
| `first_drp_valid` | `first_drp_valid` | `L0044` | `boolean` | raw bit3 candidate | yes | bench_gated | no | First DRP valid candidate. |
| `est_monitor_enable` | `est_monitor_enable` | `L004F` | `boolean` | raw bit6 candidate | maybe | bench_gated | no | EST monitor enable candidate. |
| `est_error_counter` | `est_error_counter` | `L022C` | `raw_counts` | raw counter | maybe | bench_gated | no | EST error counter candidate. |
| `prior_est_ref_sample` | `prior_est_ref_sample` | `L0205` | `raw_counts` | raw sample | maybe | bench_gated | no | Prior EST/ref sample candidate. |
| `iac_actual_position` | `iac_actual_position` | `L0007` | `raw_counts` | IAC position = raw counts until physical direction is bench-proven | yes | bench_gated | no | Actual/present IAC position. |
| `iac_desired_position` | `iac_desired_position` | `L0008` | `raw_counts` | raw target counts | yes | bench_gated | no | Desired/target IAC position. |
| `iac_position_error` | `iac_position_error` | `L0008-L0007` | `raw_counts` | desired - actual raw counts | yes | bench_gated | no | Error direction remains physical-direction gated. |
| `iac_reset_in_work` | `iac_reset_in_work` | `L0009` | `boolean` | raw bit0 | yes | bench_gated | no | Reset-in-work candidate. |
| `iac_rs_requested` | `iac_rs_requested` | `L0009` | `boolean` | raw bit2 | maybe | bench_gated | no | R/S requested candidate. |
| `iac_direction` | `iac_direction` | `L000A` | `boolean` | raw bit0; open/close meaning bench-gated | yes | bench_gated | no | Direction bit visibility without physical meaning claim. |
| `iac_phase_ab` | `iac_phase_a/iac_phase_b` | `L000A` | `bitfield` | raw bits2/3 | yes | bench_gated | no | A/B phase state, physical pins bench-gated. |
| `iac_enable_candidate` | `iac_enable_candidate` | `L000A` | `boolean` | raw bit4 | yes | bench_gated | no | Enable candidate, physical function bench-gated. |
| `iac_output_shadow` | `iac_output_shadow` | `L004C` | `bitfield` | raw shadow bits | yes | bench_gated | yes | Debug exposure does not permit IAC writes. |
| `iac_latch_shadowed_value` | `iac_latch` | `L3062` | `bitfield` | raw latch or shadowed write value | yes | bench_gated | candidate | Visible for bench proof only; direct L3062 writes remain forbidden. |
| `iac_park_down_value` | `iac_park_down_scalar` | `L4EB0` | `raw_counts` | raw 145-step stock value | maybe | bench_gated | no | Physical direction and meaning bench-gated. |
| `low_battery_protection` | `low_battery_protection` | `L003E` | `boolean` | raw bit2 | maybe | bench_gated | no | Protection flag candidate. |
| `iac_cadence_state` | `iac_cadence_state` | `minimal_iac_cadence` | `state_enum` | cadence/rate-limit state enum | yes | planning_only | no | Required before IAC writer implementation. |
| `boot_stage` | `output_safe_state` | `minimal_output_safe_state` | `state_enum` | boot/safe state enum | yes | planning_only | no | Shows reset/boot/dropout phase. |
| `ref_drp_valid` | `ref_drp_valid` | `minimal_ref_drp_valid` | `boolean` | true when REF/DRP stream valid | yes | planning_only | no | Core scheduler proof value. |
| `first_period_valid` | `first_period_valid` | `minimal_first_period_valid` | `boolean` | true after first accepted period | yes | planning_only | no | First period proof. |
| `rpm_valid` | `rpm_valid` | `minimal_rpm_valid` | `boolean` | true when RPM usable | yes | planning_only | no | Runtime modules need this gate. |
| `crank_run_qualification` | `crank_run_qualification` | `minimal_run_qual_state` | `state_enum` | crank/run/dropout enum | yes | planning_only | no | Proves crank/run handoff. |
| `scheduler_event_counter` | `scheduler_event_counter` | `minimal_scheduler_event_counter` | `raw_counts` | incrementing event counter | yes | planning_only | no | Future logical counter for event ordering proof. |
| `foreground_loop_alive_counter` | `watchdog_alive` | `minimal_watchdog_alive` | `raw_counts` | loop alive counter or boolean | yes | planning_only | no | Proves foreground/service loop liveness. |
| `dropout_state` | `dropout_state` | `minimal_dropout_state` | `boolean` | true on signal loss/unsafe | yes | planning_only | no | Dropout visibility. |
| `output_safe_state` | `output_safe_state` | `minimal_output_safe_state` | `state_enum` | output-safe state enum | yes | planning_only | no | Shows when outputs are forced safe. |
| `bench_hook_state` | `bench_hook_state` | `minimal_bench_hook_state` | `state_enum` | bench hook enum | maybe | planning_only | no | Bench hook visibility only, no control ownership. |
| `trans_tcc_aldl_baggage` | `trans_shift_tcc_state` | `stock_trans_state` | `unknown` | none | no | no | no | Not exposed unless future hardware contract proves required. |
| `egr_aldl_baggage` | `egr_state` | `stock_egr_state` | `unknown` | none | no | no | no | Not exposed by minimal debug map. |
| `evap_aldl_baggage` | `evap_purge_state` | `stock_evap_state` | `unknown` | none | no | no | no | Not exposed by minimal debug map. |
| `emissions_diag_aldl_baggage` | `emissions_diag_state` | `stock_emissions_diag` | `unknown` | none | no | no | no | Not exposed by minimal debug map. |
| `stock_mode_word_baggage` | `unused_gm_mode_baggage` | `stock_mode_baggage` | `unknown` | none | no | no | no | Stock ALDL presence alone is not enough. |
| `unknown_debug_value` | `unknown_state` | `unknown` | `unknown` | unknown | maybe | planning_only | candidate | Unknown debug values stay listed, not guessed. |

## Explicit Exclusions

```text
trans/TCC ALDL baggage
EGR ALDL baggage
EVAP/purge ALDL baggage
emissions-only diagnostic visibility
unused stock mode-word baggage
```

## Unknown Debug Rule

Unknown debug values remain visible as `unknown`; they must not be guessed into a module or carried forward solely because stock ALDL exposed something similar.

## Next Decision Point

After this pass, the planning stack is strong enough for either:

```text
bench proof package
first minimal fuel-only runnable slice
```

The fuel-only slice is the only plausible implementation path before spark and IAC output bench gates are closed.
