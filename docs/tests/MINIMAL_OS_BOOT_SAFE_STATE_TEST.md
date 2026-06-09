# Minimal OS Boot / Safe-State Test

## Goal

Verify that the boot-safe boundary defines reset, crank, first-reference, run-qualification, and dropout-safe behavior without implementing reset code, scheduler code, startup ASM, or new hardware writers.

This test validates planning only.

## Required Files

```text
docs/contracts/MINIMAL_OS_BOOT_SAFE_STATE.md
maps/contracts/minimal_os_boot_safe_state.csv
tools/build_minimal_os_boot_safe_state.py
```

## Required Static Checks

| Test | Expected |
|---|---|
| planning-only | no reset ASM or scheduler ASM created |
| fuel safe state | `$3FCE` zero/no-pulse represented |
| nonzero fuel gate | nonzero `$3FCE` remains gated by fuel calculation and no-fuel enable |
| spark hardware writes | direct `$3FE8/$3FE6/$3FF6/$3FDC` writes remain forbidden |
| IAC hardware writes | direct `L3062` writes remain forbidden |
| REF wait | `REF_DRP_WAIT` represented |
| crank qualify | `CRANK_QUALIFY` represented |
| first period | `FIRST_PERIOD_VALID` represented |
| run qualify | `RUN_QUALIFY` represented |
| dropout state | `DROPOUT_SAFE_STATE` represented for fuel/spark/IAC/watchdog |
| watchdog fallback | `WATCHDOG_SAFE_STATE` represented |
| bench-gated outputs | not marked allowed_now except `$3FCE` zero/provisional path |
| unknown boot ownership | listed as `UNKNOWN`, not guessed |

## Command

```bash
python tools/build_minimal_os_boot_safe_state.py \
  --scheduler maps/contracts/minimal_os_execution_scheduler.csv \
  --out-md docs/contracts/MINIMAL_OS_BOOT_SAFE_STATE.md \
  --out-csv maps/contracts/minimal_os_boot_safe_state.csv
```

## Required Boot States

The CSV must include:

```text
RESET_ENTRY
ASIC_WINDOW_CLEAR
OUTPUT_SAFE_DEFAULTS
RAM_STATE_SEED
FUEL_SAFE_STATE
SPARK_SAFE_STATE
IAC_SAFE_STATE
REF_DRP_WAIT
CRANK_QUALIFY
FIRST_PERIOD_VALID
RUN_QUALIFY
DROPOUT_SAFE_STATE
WATCHDOG_SAFE_STATE
BENCH_GATED_OUTPUTS
FORBIDDEN_OUTPUTS
UNKNOWN
```

## Hardware Write Rules

Allowed/provisional:

```text
$3FCE:
  zero/no-pulse only
  only through EFI_PW_WRITE / MINIMAL_EFI_PW_WRITER or documented init-clear path
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
reset vector ASM
runtime scheduler ASM
SPARK_WRITE
IAC_WRITE
physical EST/bypass authority code
idle strategy ASM
startup implementation
```

## Pass Criteria

```text
PASS:
  boot-safe contract is planning-only.
  fuel safe state includes $3FCE zero/no-pulse.
  nonzero fuel output remains gated.
  spark direct hardware writes remain forbidden.
  IAC direct L3062 writes remain forbidden.
  REF/DRP wait, crank qualification, first valid period, and run qualification are represented.
  dropout-safe fuel/spark/IAC behavior is represented.
  watchdog-safe fallback is represented.
  bench-gated outputs are not marked allowed_now except the explicit fuel zero/provisional path.
  unknown boot ownership is listed, not guessed.
```

## Fail / Rework Criteria

```text
REWORK:
  reset ASM or scheduler ASM appears.
  startup implementation appears.
  nonzero fuel is treated as a boot default.
  any direct spark ASIC writer appears.
  direct L3062 IAC writer appears.
  spark EST/bypass authority is treated as solved.
  IAC physical motion is treated as solved.
  unknown boot ownership is silently assigned.
```

## Next Planning Artifact

After this pass, continue with:

```text
MINIMAL_OS_STATE_VARIABLES
```

That pass should consolidate the minimal RAM/state map across fuel, spark, IAC, scheduler, boot, watchdog, and ALDL without writing the OS.
