# Bench Proof Package Test

## Goal

Verify that the bench proof package turns the current hardware/module/debug contracts into physical and ALDL-observable proof tasks without creating runtime code or granting write authority.

This test validates planning/test definition only.

## Required Files

```text
docs/bench/BENCH_PROOF_PACKAGE.md
maps/bench/bench_proof_matrix.csv
tools/build_bench_proof_package.py
```

## Required Static Checks

| Test | Expected |
|---|---|
| planning-only | no runtime ASM, bench-hook implementation, ALDL packet code, or fuel-only runnable code created |
| every spark bench gate covered | spark handoff, conversion, timebase, rolling state, mirror/ack, and EST/bypass have proof rows |
| every IAC bench gate covered | A/B mapping, both directions, hold, Enable, park, and cadence have proof rows |
| fuel `$3FCE` proof | raw count, 3.0 ms vector, zero gate, dropout zero, and low-PW observability rows exist |
| boot/dropout/watchdog proof | reset defaults, fuel-zero-before-enable, missing REF/DRP, watchdog fallback, and debug visibility rows exist |
| ALDL/debug tied to proof | proof rows identify whether ALDL/debug is required |
| scope requirement explicit | proof rows identify whether scope/logic analyzer is required |
| bench hook requirement explicit | proof rows identify whether a bench hook is required |
| implementation gates explicit | fuel, spark, IAC, and boot gates are listed |
| no proof row grants authority | observation does not permit writes |
| unknown physical mappings | remain unresolved until bench data exists |

## Command

```bash
python tools/build_bench_proof_package.py \
  --out-md docs/bench/BENCH_PROOF_PACKAGE.md \
  --out-csv maps/bench/bench_proof_matrix.csv
```

## Required Proof Groups

The matrix must include controlled proof groups:

```text
fuel_pw_output
spark_handoff
spark_bypass_est
spark_rolling_state
iac_phase
iac_enable
iac_park
boot_safe_state
aldl_debug_visibility
dropout_safe_state
```

## Required Fuel Rows

```text
FUEL-001  prove $3FCE raw counts correspond to commanded PW
FUEL-002  prove 3.0 ms vector: $00C5 ≈ 3.006 ms
FUEL-003  prove zero/no-fuel gate forces $3FCE = 0
FUEL-004  prove nonzero $3FCE does not occur during dropout/unsafe state
FUEL-005  prove low-PW transfer test can be observed through ALDL/debug
```

Fuel implementation gate:

```text
first minimal fuel-only runnable slice may proceed only after FUEL-001 through FUEL-004 pass
```

## Required Spark Rows

```text
SPARK-001  observe $3FE8/$3FE6 candidates without granting write authority
SPARK-002  correlate desired spark / L01FD / L01EE / L004F bit0
SPARK-003  correlate L005F/L0060 period basis with REF/DRP period
SPARK-004  observe L3FDC/L3FF6 rolling state behavior across events
SPARK-005  observe $3FEC->$3FE4 mirror/ack behavior
SPARK-006  classify physical EST/bypass authority transition
```

Spark implementation gate:

```text
no spark writer until these are proven or explicitly replaced by a safer hardware strategy
```

## Required IAC Rows

```text
IAC-001  scope L3062 bit2/bit3 physical A/B mapping
IAC-002  force desired > actual and record A/B ring direction
IAC-003  force desired < actual and record reverse ring direction
IAC-004  prove desired == actual holds A/B state
IAC-005  scope L3062 bit4 physical Enable behavior
IAC-006  prove Enable is not step-pulsed
IAC-007  classify L0008 = 0 physical movement
IAC-008  classify L0008 = L4EB0 = 145 physical movement / park-down behavior
IAC-009  measure safe step cadence / rate limit
```

IAC implementation gate:

```text
no IAC writer until IAC-001 through IAC-009 are resolved
```

## Required Boot / Dropout Rows

```text
BOOT-001  reset enters output-safe defaults
BOOT-002  fuel remains zero until valid crank/fuel-enable state
BOOT-003  REF/DRP missing causes dropout-safe state
BOOT-004  watchdog-safe fallback returns outputs to safe defaults
BOOT-005  ALDL/debug exposes boot/dropout/watchdog states
```

## Write-Authority Guardrail

```text
No proof row grants write authority by itself.
Observing $3FE8/$3FE6/$3FF6/$3FDC does not permit spark writes.
Observing L3062/L004C does not permit IAC writes.
Observing $3FCE does not permit nonzero fuel unless fuel gates permit it.
```

## Pass Criteria

```text
PASS:
  no runtime ASM or bench implementation exists.
  every bench-gated spark item has a proof row.
  every bench-gated IAC item has a proof row.
  fuel $3FCE proof rows exist.
  boot/dropout/watchdog proof rows exist.
  ALDL/debug visibility is tied to proof rows.
  implementation gates are explicit.
  no proof row grants write authority by itself.
  unknown physical mappings remain unresolved until bench data exists.
```

## Fail / Rework Criteria

```text
REWORK:
  runtime ASM appears.
  bench hooks are implemented instead of specified.
  ALDL packet code appears.
  fuel-only runnable code appears.
  spark/IAC write authority is implied by observation.
  any bench-gated spark/IAC output is treated as proven without data.
  unknown physical mappings are silently classified.
```

## Next Step

After this pass, choose:

```text
first minimal fuel-only runnable slice
```

That slice must still exclude spark and IAC writers.
