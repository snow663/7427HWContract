# First Minimal Fuel-Only Runnable Slice Test

## Goal

Verify that the first minimal fuel-only slice boundary defines the smallest allowed fuel-only runtime envelope without implementing runtime code, bypassing bench gates, or granting spark/IAC authority.

This test validates contract/planning only.

## Required Files

```text
docs/contracts/FIRST_MINIMAL_FUEL_ONLY_SLICE.md
maps/contracts/first_minimal_fuel_only_slice.csv
tools/build_first_minimal_fuel_only_slice.py
```

## Required Static Checks

| Test | Expected |
|---|---|
| no runtime implementation | no fuel-only runtime ASM created |
| no spark writer | no spark ASM/writer created |
| no IAC writer | no IAC ASM/writer created |
| no forbidden hardware writes | no direct writes to `$3FE8/$3FE6/$3FF6/$3FDC/L3062` |
| fuel output only | `$3FCE` output only through `EFI_PW_WRITE` |
| SLICE-0 status | SLICE-0 marked not engine-runnable |
| SLICE-1 gate | SLICE-1 requires `FUEL-001` through `FUEL-004` |
| dropout zero | dropout forces `$3FCE = 0` |
| ALDL/debug | raw counts and ms visibility required |
| calibration guard | calibration cannot make the slice runnable by itself |
| excluded systems | trans/EGR/EVAP remain excluded |

## Command

```bash
python tools/build_first_minimal_fuel_only_slice.py \
  --out-md docs/contracts/FIRST_MINIMAL_FUEL_ONLY_SLICE.md \
  --out-csv maps/contracts/first_minimal_fuel_only_slice.csv
```

## Slice-Level Requirements

### SLICE-0

```text
purpose: prove $3FCE write path only
engine runnable: no
allowed output: fixed $3FCE test vectors only
required bench proofs: none before static definition
```

Required rows:

```text
reset/output-safe entry
force $3FCE = 0
force $3FCE = $00C5 test vector
expose $3FCE raw counts and ms over debug
dropout forces $3FCE = 0
not engine-runnable
```

### SLICE-1

```text
purpose: zero-safe fuel control with fixed/calculated PW
engine runnable: limited
required bench proofs: FUEL-001 through FUEL-004
```

Required rows:

```text
REF/RPM valid gate
crank/run fuel enable gate
no-fuel/DFCO zero gate
fixed PW or simple table PW source
EFI_PW_WRITE only
ALDL PW visibility
dropout zero
no spark/IAC authority
```

### SLICE-2

```text
purpose: MAP/RPM/CTS/battery based fuel
engine runnable: yes, fuel-only
required: sensor acquisition, VE/input tables, deadtime/low-PW handling
```

Required rows:

```text
RPM input
MAP input
CTS input
battery voltage input
baro/altitude basis
VE/base airflow input
injector flow constant
deadtime/battery correction
low-PW correction
warmup/afterstart/crank fuel
target AFR/stoich basis
```

## Required Bench Gate

Before any engine-runnable fuel-only implementation:

```text
FUEL-001 must prove $3FCE raw counts correlate to commanded PW.
FUEL-002 must prove $00C5 ≈ 3.006 ms.
FUEL-003 must prove zero/no-fuel gate forces $3FCE = 0.
FUEL-004 must prove dropout/unsafe state forces $3FCE = 0.
```

## Hardware Write Guardrail

Only hardware write allowed:

```text
EFI_PW_WRITE:
  D = EFI pulsewidth counts in 1/65536 second units
  STD $3FCE
```

Forbidden:

```text
$3FE8
$3FE6
$3FF6
$3FDC
L3062
SPARK_WRITE
IAC_WRITE
EST/bypass authority code
IAC phase/output code
```

## Pass Criteria

```text
PASS:
  no fuel runtime ASM exists from this pass.
  no spark ASM/writer exists.
  no IAC ASM/writer exists.
  no direct forbidden hardware writes exist.
  $3FCE output is only through EFI_PW_WRITE.
  SLICE-0 is marked not engine-runnable.
  SLICE-1 requires FUEL-001 through FUEL-004.
  dropout behavior forces zero fuel.
  ALDL/debug visibility of raw counts and ms is required.
  calibration cannot make the slice runnable by itself.
  trans/EGR/EVAP remain excluded.
```

## Fail / Rework Criteria

```text
REWORK:
  runtime ASM is created by this pass.
  SLICE-0 is described as engine-runnable.
  SLICE-1 is allowed before FUEL-001 through FUEL-004 pass.
  direct writes to spark/IAC hardware are introduced.
  nonzero fuel is allowed without fuel enable/no-fuel gates.
  calibration presence alone promotes runnable status.
  trans/EGR/EVAP strategy enters the slice.
```

## Valid Next Branches

After this contract:

```text
bench FUEL-001 through FUEL-004
```

or, if explicitly bench-harness-only:

```text
implement SLICE-0 bench harness first
```

Do not implement SLICE-1 until the fuel proof rows are actually satisfied.
