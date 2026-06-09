# First Minimal Fuel-Only Runnable Slice

## Purpose

Define the first constrained runtime slice that may eventually command fuel through `$3FCE`.

This document does not implement runtime code. It defines the allowed implementation envelope and bench gates.

## Output Boundary

The only allowed hardware-facing fuel output is:

```text
D = EFI pulsewidth counts in 1/65536 second units
STD $3FCE
```

through `EFI_PW_WRITE`.

## Required Bench Gate

Before any engine-runnable fuel-only implementation:

- `FUEL-001` must prove `$3FCE` raw counts correlate to commanded PW.
- `FUEL-002` must prove `$00C5 ≈ 3.006 ms`.
- `FUEL-003` must prove zero/no-fuel gate forces `$3FCE = 0`.
- `FUEL-004` must prove dropout/unsafe state forces `$3FCE = 0`.

No engine-runnable fuel-only implementation is allowed until `FUEL-001` through `FUEL-004` have actually passed on the bench, unless the slice is marked bench-harness-only and cannot run an engine.

## Slice Levels

### SLICE-0: fuel output bench harness

```text
purpose: prove $3FCE write path only
engine runnable: no
allowed output: fixed $3FCE test vectors only
required bench proofs: none before static definition
```

### SLICE-1: fuel-only crank/run skeleton

```text
purpose: zero-safe fuel control with fixed/calculated PW
engine runnable: limited
required bench proofs: FUEL-001 through FUEL-004
```

### SLICE-2: open-loop speed-density fuel

```text
purpose: MAP/RPM/CTS/battery based fuel
engine runnable: yes, fuel-only
required: sensor acquisition, VE/input tables, deadtime/low-PW handling
```

## Forbidden Scope

This slice must not implement spark authority, IAC authority, transmission, EGR, EVAP, or emissions strategy.

Spark and IAC may be observed through debug only.

Forbidden hardware/actions:

```text
no $3FE8
no $3FE6
no $3FF6
no $3FDC
no L3062
no SPARK_WRITE
no IAC_WRITE
no EST/bypass authority code
no IAC phase/output code
```

## Slice Table

| Slice | Stage | Output | Hardware write | Allowed now | Required bench proof | Notes |
|---|---|---|---|---|---|---|
| `SLICE-0` | reset_output_safe_entry | all outputs safe; fuel zero | EFI_PW_WRITE zero only if used `$3FCE` | yes_bench_harness_only | none before static definition | Fuel output bench harness only; not engine runnable. |
| `SLICE-0` | force_fuel_zero | D=$0000 | EFI_PW_WRITE `$3FCE` | yes_bench_harness_only | none before static definition | Used to prove no-pulse / safe zero path. |
| `SLICE-0` | force_3ms_test_vector | D=$00C5 test vector | EFI_PW_WRITE `$3FCE` | yes_bench_harness_only | none before static definition; FUEL-002 for proof | $00C5 ≈ 3.006 ms vector; not engine-runnable. |
| `SLICE-0` | debug_pw_visibility | $3FCE raw and ms visible | none `none` | yes_bench_harness_only | FUEL-001; FUEL-002 | Expose $3FCE counts and EFI_PW_ms = counts/65.536. |
| `SLICE-0` | dropout_forces_zero | D=$0000 | EFI_PW_WRITE zero only `$3FCE` | yes_bench_harness_only | FUEL-004 for proof | SLICE-0 must not be engine-runnable. |
| `SLICE-0` | engine_runnable_flag | not engine runnable | none `none` | yes | none | SLICE-0 is explicitly not engine-runnable. |
| `SLICE-1` | ref_rpm_valid_gate | fuel event permitted only after valid RPM/ref | none `none` | blocked_until_fuel_proofs_pass | FUEL-001; FUEL-002; FUEL-003; FUEL-004 | Limited engine-runnable skeleton gate. |
| `SLICE-1` | crank_run_fuel_enable_gate | fuel enable state | none `none` | blocked_until_fuel_proofs_pass | FUEL-001; FUEL-002; FUEL-003; FUEL-004 | Nonzero fuel gated by crank/run and fuel enable. |
| `SLICE-1` | no_fuel_dfco_zero_gate | D=$0000 when gate active | EFI_PW_WRITE `$3FCE` | blocked_until_fuel_proofs_pass | FUEL-003; FUEL-004 | No-fuel gate is mandatory. |
| `SLICE-1` | fixed_or_simple_pw_source | D = fixed/simple PW counts | none before output stage `none` | blocked_until_fuel_proofs_pass | FUEL-001; FUEL-002; FUEL-003; FUEL-004 | May be fixed/test PW or simple table PW; not full fuel strategy. |
| `SLICE-1` | efi_pw_write_only | D -> $3FCE | EFI_PW_WRITE `$3FCE` | blocked_until_fuel_proofs_pass | FUEL-001; FUEL-002; FUEL-003; FUEL-004 | Only hardware write allowed in SLICE-1. |
| `SLICE-1` | aldl_pw_visibility | debug visibility | none `none` | blocked_until_fuel_proofs_pass | FUEL-001; FUEL-002; ALDL-001 | Debug visibility required for first runnable slice. |
| `SLICE-1` | dropout_zero | D=$0000 | EFI_PW_WRITE `$3FCE` | blocked_until_fuel_proofs_pass | FUEL-004; BOOT-003 | Runtime dropout must force zero fuel. |
| `SLICE-1` | no_spark_iac_authority | no spark/IAC control | none `none` | yes | SPARK-001..006 and IAC-001..009 remain unresolved | Spark and IAC may be observed only, not controlled. |
| `SLICE-2` | rpm_input | fuel RPM input | none `none` | future_after_slice1 | FUEL-001..004 plus RPM proof | Open-loop speed-density input. |
| `SLICE-2` | map_input | load input | none `none` | future_after_slice1 | sensor acquisition proof | MAP/load input for VE. |
| `SLICE-2` | cts_input | coolant input | none `none` | future_after_slice1 | sensor acquisition proof | Coolant input for warmup/crank. |
| `SLICE-2` | battery_voltage_input | deadtime correction input | none `none` | future_after_slice1 | battery scaling proof | Battery voltage affects deadtime/PW correction. |
| `SLICE-2` | baro_altitude_basis | air density/load basis | none `none` | future_after_slice1 | baro source proof | Needed for real speed-density behavior. |
| `SLICE-2` | ve_base_airflow_input | base fuel mass input | none `none` | future_after_slice1 | calibration source mapping and sensor proof | Calibration does not permit runnable code by itself. |
| `SLICE-2` | injector_flow_constant | fuel mass to PW conversion | none `none` | future_after_slice1 | injector output proof | Injector flow constant required for real PW math. |
| `SLICE-2` | deadtime_battery_correction | PW correction | none `none` | future_after_slice1 | deadtime behavior proof | Deadtime/battery correction required before final fuel math. |
| `SLICE-2` | low_pw_correction | PW correction | none `none` | future_after_slice1 | FUEL-005 plus low-PW bench validation | Low-PW correction needed due injector floor/nonlinearity. |
| `SLICE-2` | warmup_afterstart_crank | enrichment modifier | none `none` | future_after_slice1 | calibration source mapping | Required for engine-runnable open-loop behavior. |
| `SLICE-2` | target_afr_stoich | fuel mass target | none `none` | future_after_slice1 | calibration source mapping | Target AFR/stoich basis required for speed-density math. |
| `ALL` | forbidden_outputs | none | none `$3FE8;$3FE6;$3FF6;$3FDC;L3062` | no | spark/IAC bench gates unresolved | Fuel-only slice cannot touch spark or IAC hardware. |
| `ALL` | calibration_guard | none | none `none` | no | not a bench proof | Calibration presence alone cannot promote runnable status. |

## Current Implementation Decision

Valid branches after this contract:

```text
bench FUEL-001 through FUEL-004
implement SLICE-0 bench harness first, if explicitly bench-harness-only and not engine runnable
```

Do not implement `SLICE-1` until the fuel proof rows are actually satisfied.
