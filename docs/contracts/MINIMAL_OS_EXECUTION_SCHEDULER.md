# Minimal OS Execution Scheduler

## Purpose

Define when minimal-OS modules execute relative to reset, crank, REF/DRP events, timer events, foreground/service loops, ALDL/debug service, and watchdog-safe state.

This document does not implement a scheduler and does not create runtime ASM.

## Source Boundaries

Fuel:

- `FUEL_MINIMAL_MODULE_INPUTS.md`
- `EFI_PW_3FCE_CONTRACT.md`
- `MINIMAL_EFI_PW_WRITER.md`

Spark:

- `SPARK_MINIMAL_MODULE_INPUTS.md`
- `SPARK_MINIMAL_MODULE_BOUNDARY.md`
- `SPARK_BYPASS_EST_TRANSITION.md`
- `SPARK_INIT_STATE.md`

IAC:

- `IAC_MINIMAL_MODULE_INPUTS.md`
- `IAC_IDLE_AIR_OUTPUT_CONTRACT.md`
- `IAC_PHASE_SEQUENCE_CONTRACT.md`
- `IAC_ENABLE_FAULT_GATE_CONTRACT.md`
- `IAC_INIT_PARK_CONTRACT.md`

## Scheduler Model

```text
RESET_INIT
→ hardware/window clear
→ seed retained/known state
→ enable watchdog-safe defaults
→ wait for crank/ref events

REF_DRP_EVENT
→ update period/RPM basis
→ run/crank qualification
→ fuel/spark timebase inputs
→ dropout timer reset

CRANK_INIT / CRANK_LOOP
→ crank fuel inputs
→ startup spark intent
→ IAC crank/park target
→ no unsupported output handoff

RUN_LOOP
→ sensor sample
→ fuel calculation
→ spark intent calculation
→ IAC desired target calculation
→ ALDL/debug service
→ watchdog service

TIMER / CADENCE EVENTS
→ fuel output timing if required
→ spark timing only after bench-gated handoff is proven
→ IAC step cadence only after bench-gated output behavior is proven

DROPOUT_SAFE_STATE
→ fuel no-pulse / zero gate
→ spark safe/bypass/dropout state
→ IAC hold or safe park policy
```

## Hardware Ownership Rule

Only the module that owns a hardware contract may write that hardware-facing value.

Allowed/provisional:

- fuel writer may write `$3FCE` only through `EFI_PW_WRITE`

Forbidden until bench-gated:

- direct `$3FE8/$3FE6/$3FF6/$3FDC` spark writes
- direct `L3062` IAC writes
- physical EST/bypass authority code
- IAC phase/output ASM

## Event Table

| Stage | Event | Module | Submodule | Trigger | Output | Hardware write | Allowed now | Bench gate |
|---|---|---|---|---|---|---|---|---|
| boot_clear | `RESET_INIT` | reset | hardware_window_clear | power-on/reset vector | known-safe inactive state | candidate `ASIC/window registers` | no_runtime_code_yet | yes |
| fuel_boot_seed | `RESET_INIT` | fuel | fuel_output_init | power-on/reset vector | EFI output safe/inactive state | candidate `$3FCE companion init state` | no_runtime_code_yet | yes |
| spark_boot_seed | `RESET_INIT` | spark | rolling_state_seed | power-on/reset vector | spark timing state initialized/held safe | no `$3FF6/$3FDC` | no | yes |
| iac_boot_seed | `RESET_INIT` | iac_idle | actual_position_seed | power-on/reset vector | IAC actual/desired/reset policy selected | no `L3062` | no | yes |
| watchdog_boot | `RESET_INIT` | watchdog_safe_state | safe_default | power-on/reset vector | safe fallback state | no `none` | no_runtime_code_yet | yes |
| crank_entry | `CRANK_INIT` | reset | crank_state | first valid crank/ref condition | crank-safe module enable set | no `none` | planning_only | yes |
| fuel_crank_inputs | `CRANK_INIT` | fuel | crank_fuel_inputs | crank mode | crank BPW/PW intent | no `$3FCE` | no | yes |
| spark_crank_intent | `CRANK_INIT` | spark | startup_spark_intent | crank mode | desired startup spark intent | no `$3FE8/$3FE6` | no | yes |
| iac_crank_target | `CRANK_INIT` | iac_idle | crank_air_target | crank mode | desired IAC/crank-air target | no `L3062` | no | yes |
| ref_period_capture | `REF_DRP_EVENT` | ref_rpm_period | period_capture | REF/DRP interrupt/event | RPM/timebase state | no `none` | planning_only | yes |
| run_qualification | `REF_DRP_EVENT` | scheduler | run_crank_qualify | REF/DRP interrupt/event | crank/run permission state | no `none` | planning_only | yes |
| fuel_rpm_feed | `REF_DRP_EVENT` | fuel | rpm_input_update | period/RPM updated | fuel calculation ready input | no `none` | planning_only | no |
| spark_period_feed | `REF_DRP_EVENT` | spark | timebase_input_update | period/RPM updated | conversion-ready timebase | no `$3FE8/$3FE6` | no | yes |
| iac_rpm_feed | `REF_DRP_EVENT` | iac_idle | idle_rpm_input_update | period/RPM updated | idle error input | no `none` | planning_only | yes |
| dropout_timer_reset | `REF_DRP_EVENT` | watchdog_safe_state | dropout_monitor | valid REF/DRP | dropout-safe state deferred | no `none` | planning_only | yes |
| sensor_sample | `SENSOR_SAMPLE_EVENT` | sensors | adc_sample | timer/foreground sample cadence | module input snapshot | no `none` | planning_only | yes |
| foreground_loop | `FOREGROUND_BACKGROUND_LOOP` | scheduler | foreground_dispatch | main loop/service loop | dispatch permits module calculations | no `none` | planning_only | yes |
| fuel_calc | `FUEL_CALC_EVENT` | fuel | fuel_compute | foreground/timer after sensor/RPM update | EFI PW count intent D | no `$3FCE` | planning_only | yes |
| fuel_dfco_gate | `FUEL_CALC_EVENT` | fuel | no_fuel_gate | fuel compute | D=0 candidate | no `$3FCE` | planning_only | yes |
| fuel_correction | `FUEL_CALC_EVENT` | fuel | injector_model | fuel compute | EFI PW counts in 1/65536s units | no `$3FCE` | planning_only | yes |
| fuel_output | `FUEL_OUTPUT_EVENT` | fuel | efi_pw_write | fuel PW intent ready | EFI PW command | yes `$3FCE` | yes_provisional | yes |
| spark_calc | `SPARK_PERIOD_EVENT` | spark | spark_intent_compute | foreground/timer/period-qualified event | desired spark degrees/timing intent | no `$3FE8/$3FE6` | no | yes |
| spark_conversion | `SPARK_PERIOD_EVENT` | spark | degree_to_time_inputs | spark intent ready | timing-domain candidate | no `$3FE8/$3FE6/$3FF6/$3FDC` | no | yes |
| spark_output_forbidden | `SPARK_OUTPUT_EVENT` | spark | asic_handoff | timing-domain candidate | none | forbidden `$3FE8/$3FE6/$3FF6/$3FDC/$3FE4` | no | yes |
| iac_target | `IAC_CADENCE_EVENT` | iac_idle | target_compute | timer/cadence after RPM/sensor update | L0008 target candidate | no `L3062` | no | yes |
| iac_compare | `IAC_CADENCE_EVENT` | iac_idle | position_compare | IAC cadence tick | step/no-step decision | no `L3062` | no | yes |
| iac_phase_candidate | `IAC_CADENCE_EVENT` | iac_idle | phase_step | IAC step permitted | next A/B phase candidate | no `L3062` | no | yes |
| iac_output_forbidden | `IAC_OUTPUT_EVENT` | iac_idle | output_latch | IAC phase/enable candidate | none | forbidden `L3062` | no | yes |
| aldl_service | `ALDL_SERVICE_EVENT` | aldl_debug | debug_service | foreground/service loop | debug output only | no `none` | planning_only | no |
| watchdog_service | `WATCHDOG_SERVICE_EVENT` | watchdog_safe_state | watchdog_service | foreground/service loop or timed tick | safe-state not triggered | no `none` | planning_only | yes |
| dropout_safe_fuel | `DROPOUT_SAFE_STATE` | fuel | dropout_zero_gate | missing REF/DRP or invalid runtime state | D=0/no-pulse intent | candidate `$3FCE` | yes_provisional_via_fuel_writer_only | yes |
| dropout_safe_spark | `DROPOUT_SAFE_STATE` | spark | dropout_safe_intent | missing REF/DRP or invalid timing state | safe/bypass/dropout state | no `$3FE8/$3FE6` | no | yes |
| dropout_safe_iac | `DROPOUT_SAFE_STATE` | iac_idle | dropout_hold_or_park | missing REF/DRP or reset/fault state | hold or safe-park intent | no `L3062` | no | yes |
| bench_hook | `BENCH_ONLY_HOOK` | bench | instrumentation | bench harness / trace flag | bench log/ALDL exposure | no `none` | bench_only | no |
| excluded_trans | `EXCLUDED` | excluded | transmission | stock strategy baggage | none | forbidden `trans/TCC hardware` | no | yes_if_future_hardware_required |
| excluded_egr_evap | `EXCLUDED` | excluded | emissions | stock strategy baggage | none | forbidden `EGR/EVAP hardware` | no | yes_if_future_hardware_required |
| unknown_event | `UNKNOWN` | unknown | unknown | unresolved timing/source ownership | unknown | no `unknown` | no | yes |

## Explicit Forbidden List

No scheduler event may directly write:

```text
$3FE8
$3FE6
$3FF6
$3FDC
L3062
```

No scheduler event may create:

```text
SPARK_WRITE
IAC_WRITE
physical EST/bypass authority code
idle strategy ASM
```

Exception:

```text
$3FCE may only be written through the existing minimal EFI PW writer contract.
```

## Unknown Ownership Rule

Unknown timing/event ownership must stay listed as `UNKNOWN`; it must not be guessed into fuel, spark, IAC, ALDL, or watchdog until source/bench evidence assigns it.

## Next Contract

The next useful artifact is:

```text
MINIMAL_OS_BOOT_SAFE_STATE
```

That pass should turn this scheduler boundary into a reset/crank/run safe-state machine without implementing the full OS.
