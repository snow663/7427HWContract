# Minimal OS Execution Scheduler Test

## Goal

Verify that the scheduler boundary defines event ownership and hardware-write permissions without creating a runtime scheduler, ASM code, or new hardware writers.

This test validates planning only.

## Required Files

```text
docs/contracts/MINIMAL_OS_EXECUTION_SCHEDULER.md
maps/contracts/minimal_os_execution_scheduler.csv
tools/build_minimal_os_execution_scheduler.py
```

## Required Static Checks

| Test | Expected |
|---|---|
| scheduler planning-only | no runtime scheduler ASM is created |
| fuel writer dependency | `$3FCE` appears only through `MINIMAL_EFI_PW_WRITER.md` / `EFI_PW_WRITE` |
| spark hardware writes | `$3FE8/$3FE6/$3FF6/$3FDC` writes remain forbidden |
| IAC hardware writes | direct `L3062` writes remain forbidden |
| reset event | `RESET_INIT` rows exist |
| crank event | `CRANK_INIT` rows exist |
| REF/DRP event | `REF_DRP_EVENT` rows exist |
| sensor sample event | `SENSOR_SAMPLE_EVENT` row exists |
| fuel calc/output events | `FUEL_CALC_EVENT` and `FUEL_OUTPUT_EVENT` rows exist |
| spark calc/output events | `SPARK_PERIOD_EVENT` rows exist and `SPARK_OUTPUT_EVENT` remains forbidden |
| IAC cadence/output events | `IAC_CADENCE_EVENT` rows exist and `IAC_OUTPUT_EVENT` remains forbidden |
| ALDL service | `ALDL_SERVICE_EVENT` row exists and owns no control output |
| watchdog service | `WATCHDOG_SERVICE_EVENT` row exists |
| dropout safe state | `DROPOUT_SAFE_STATE` rows exist for fuel/spark/IAC |
| bench-gated actions | not marked `allowed_now=yes` except `$3FCE` provisional path |
| excluded tasks | trans/EGR/EVAP/emissions are not scheduled |
| calibration input | calibration sections do not create scheduler events by themselves |
| unknown timing | unknown timing/event ownership listed, not guessed |

## Command

```bash
python tools/build_minimal_os_execution_scheduler.py \
  --fuel-inputs maps/contracts/fuel_minimal_module_inputs.csv \
  --spark-inputs maps/contracts/spark_minimal_module_inputs.csv \
  --iac-inputs maps/contracts/iac_minimal_module_inputs.csv \
  --out-md docs/contracts/MINIMAL_OS_EXECUTION_SCHEDULER.md \
  --out-csv maps/contracts/minimal_os_execution_scheduler.csv
```

## Hardware Write Rules

Allowed/provisional:

```text
$3FCE:
  only through existing EFI_PW_WRITE / MINIMAL_EFI_PW_WRITER contract
  bench pending
```

Forbidden:

```text
$3FE8
$3FE6
$3FF6
$3FDC
L3062
```

Forbidden generated code or module files:

```text
SPARK_WRITE
IAC_WRITE
physical EST/bypass authority code
idle strategy ASM
runtime scheduler ASM
```

## Required Event Classes

The CSV must include controlled scheduler classes:

```text
RESET_INIT
CRANK_INIT
REF_DRP_EVENT
FUEL_CALC_EVENT
FUEL_OUTPUT_EVENT
SPARK_PERIOD_EVENT
SPARK_OUTPUT_EVENT
IAC_CADENCE_EVENT
IAC_OUTPUT_EVENT
SENSOR_SAMPLE_EVENT
ALDL_SERVICE_EVENT
WATCHDOG_SERVICE_EVENT
DROPOUT_SAFE_STATE
FOREGROUND_BACKGROUND_LOOP
BENCH_ONLY_HOOK
EXCLUDED
UNKNOWN
```

## Pass Criteria

```text
PASS:
  scheduler is planning-only.
  all required event classes are represented.
  fuel $3FCE writer dependency is present and isolated.
  spark hardware writes remain forbidden.
  IAC L3062 writes remain forbidden.
  bench-gated actions are not marked allowed_now except the explicit $3FCE provisional path.
  excluded trans/EGR/EVAP/emissions tasks remain excluded.
  calibration data does not create scheduler events by itself.
  unknown timing/event ownership is listed, not guessed.
```

## Fail / Rework Criteria

```text
REWORK:
  any runtime scheduler ASM appears.
  any direct spark hardware writer appears.
  any direct L3062 IAC writer appears.
  physical EST/bypass authority is treated as solved.
  IAC phase/output ASM is created.
  excluded strategy baggage is scheduled.
  calibration sections independently generate required runtime events.
  unknown event ownership is silently assigned.
```

## Next Planning Artifact

After this pass, continue with:

```text
MINIMAL_OS_BOOT_SAFE_STATE
```

That pass should convert scheduler ownership into a safe reset/crank/run state machine while still avoiding full OS implementation.
