# Fuel SLICE-0 Bench Harness Test

## Goal

Verify that the fuel SLICE-0 bench harness is bench-only, non-engine-runnable, and limited to fixed-vector calls through `EFI_PW_WRITE`.

This test validates static harness safety. It does not mark `FUEL-001` through `FUEL-004` as passed.

## Required Files

```text
source/minimal_os/fuel/slice0_bench_harness.asm
tools/verify_fuel_slice0_bench_harness.py
tests/static/fuel_slice0_bench_vectors.csv
docs/bench/FUEL_SLICE0_BENCH_HARNESS.md
```

## Required Static Checks

| Test | Expected |
|---|---|
| bench-only marker | harness explicitly says bench-only |
| not engine-runnable | harness explicitly says not engine-runnable |
| no reset ownership | harness explicitly says not reset-vector-owned |
| no scheduler ownership | harness explicitly says not scheduler-owned |
| no direct `$3FCE` write | harness does not contain `STD $3FCE` or `STD L3FCE` |
| writer ownership | only `EFI_PW_WRITE` owns `STD L3FCE` |
| call path | all vector routines use `JSR EFI_PW_WRITE` |
| fixed vectors | `$0000`, `$0042`, `$0083`, `$00C5`, `$0106` present |
| `$00C5` conversion | `$00C5 = 197 counts ≈ 3.005981 ms` represented |
| no spark/IAC references | no `$3FE8/$3FE6/$3FF6/$3FDC/L3062`, `SPARK_WRITE`, or `IAC_WRITE` in code |
| no ALDL implementation | no ALDL packet or mode handler added |
| no fuel math | no VE table, sensor read, or runtime fuel math added |

## Command

```bash
python tools/verify_fuel_slice0_bench_harness.py
```

Required output:

```text
PASS: fuel SLICE-0 bench harness verification
```

## Required Harness Routines

```asm
FUEL_SLICE0_WRITE_ZERO:
        LDD   #$0000
        JSR   EFI_PW_WRITE
        RTS

FUEL_SLICE0_WRITE_1MS:
        LDD   #$0042
        JSR   EFI_PW_WRITE
        RTS

FUEL_SLICE0_WRITE_2MS:
        LDD   #$0083
        JSR   EFI_PW_WRITE
        RTS

FUEL_SLICE0_WRITE_3MS:
        LDD   #$00C5
        JSR   EFI_PW_WRITE
        RTS

FUEL_SLICE0_WRITE_4MS:
        LDD   #$0106
        JSR   EFI_PW_WRITE
        RTS
```

## Vector CSV Requirements

```csv
name,counts_hex,counts_dec,pw_ms,allowed_in_engine_runtime,notes
zero,$0000,0,0.000000,no,no-pulse vector
one_ms,$0042,66,1.007080,no,bench-only fixed vector
two_ms,$0083,131,1.998901,no,bench-only fixed vector
three_ms,$00C5,197,3.005981,no,bench proof vector
four_ms,$0106,262,3.997803,no,bench-only fixed vector
```

## Proof Mapping Requirements

```text
FUEL-001:
  fixed vector raw counts correlate to measured PW

FUEL-002:
  $00C5 measures about 3.006 ms

FUEL-003:
  zero vector produces no pulse / zero command

FUEL-004:
  not proven by SLICE-0 alone unless dropout zero path is separately invoked
```

## Pass Criteria

```text
PASS:
  harness is bench-only and not engine-runnable.
  no reset/scheduler integration exists.
  no direct $3FCE write exists in the harness.
  all output calls go through EFI_PW_WRITE.
  fixed vectors match tests/static/fuel_slice0_bench_vectors.csv.
  $00C5 conversion is documented.
  no spark/IAC forbidden addresses are referenced in code.
  no ALDL packet or runtime fuel math is added.
```

## Fail / Rework Criteria

```text
REWORK:
  harness writes $3FCE/L3FCE directly.
  harness calls anything other than EFI_PW_WRITE.
  harness references spark/IAC forbidden hardware.
  harness is connected to reset, scheduler, crank/run, or engine runtime.
  harness reads sensors or VE tables.
  harness implements ALDL packet/mode code.
  harness is described as engine-runnable.
```

## Next Step

Run bench proof collection for:

```text
FUEL-001
FUEL-002
FUEL-003 partial zero-vector proof
```

Do not move to `SLICE-1` until `FUEL-001` through `FUEL-004` are actually marked passed.
