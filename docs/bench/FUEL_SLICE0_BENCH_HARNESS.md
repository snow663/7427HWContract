# Fuel SLICE-0 Bench Harness

## Purpose

Define the non-engine-runnable fuel SLICE-0 bench harness used to prove the `EFI_PW_WRITE` / `$3FCE` pulsewidth command path with fixed vectors.

This is a bench harness only.

```text
not engine-runnable
not scheduler-owned
not reset-vector-owned
not crank/run fuel control
no runtime fuel math
no sensor reads
no VE table use
```

## Harness Contract

The harness may only load a fixed EFI pulsewidth count into `D` and call `EFI_PW_WRITE`:

```asm
LDD   #test_vector
JSR   EFI_PW_WRITE
```

`EFI_PW_WRITE` remains the only routine allowed to contain:

```asm
STD   L3FCE
```

The harness must not write `$3FCE` or `L3FCE` directly.

## Fixed Vectors

| Name | Counts | Decimal | PW ms | Runtime allowed? | Notes |
|---|---:|---:|---:|---|---|
| zero | `$0000` | 0 | 0.000000 | no | no-pulse vector |
| one_ms | `$0042` | 66 | 1.007080 | no | bench-only fixed vector |
| two_ms | `$0083` | 131 | 1.998901 | no | bench-only fixed vector |
| three_ms | `$00C5` | 197 | 3.005981 | no | bench proof vector |
| four_ms | `$0106` | 262 | 3.997803 | no | bench-only fixed vector |

Conversion:

```text
EFI_PW_ms = counts / 65.536
```

## Proof Row Mapping

### FUEL-001

Fixed vector raw counts must correlate to measured injector pulsewidth.

Expected proof:

```text
ALDL/debug $3FCE raw count = commanded vector
scope/logic analyzer pulse width = derived milliseconds
```

### FUEL-002

The `$00C5` vector must measure about `3.006 ms`.

Expected proof:

```text
$00C5 = 197 counts
197 / 65.536 = 3.005981 ms
```

### FUEL-003

The zero vector should produce no pulse / zero command.

Expected proof:

```text
$0000 command
$3FCE raw = 0
scope shows no injector pulse or zero-width command
```

This partially proves the zero path. It does not by itself prove all no-fuel/DFCO/dropout gates unless those gates are part of the bench setup.

### FUEL-004

SLICE-0 does not fully prove dropout behavior by itself.

Dropout proof requires separately invoking the dropout/unsafe state and verifying:

```text
dropout asserted
$3FCE = 0
no injector pulse
```

## Forbidden Scope

The harness must not:

```text
write $3FCE directly
write $3FE8/$3FE6/$3FF6/$3FDC
write L3062
create spark writer
create IAC writer
implement ALDL packet code
implement fuel math
read sensors
use VE tables
enable nonzero fuel during runtime
own reset vector
own scheduler dispatch
own crank/run fuel control
```

## Static Verification

Run:

```bash
python tools/verify_fuel_slice0_bench_harness.py
```

Required result:

```text
PASS: fuel SLICE-0 bench harness verification
```

## Next Step

Use this harness to collect bench data for:

```text
FUEL-001
FUEL-002
FUEL-003 partial zero-vector proof
```

Do not move to `SLICE-1` until `FUEL-001` through `FUEL-004` are actually marked passed.
