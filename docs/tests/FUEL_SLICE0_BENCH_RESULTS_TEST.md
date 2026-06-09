# Fuel SLICE-0 Bench Results Test

## Goal

Verify that the fuel SLICE-0 bench result capture package records bench measurements without claiming proof status before evidence exists.

This test validates result structure, status rules, measurement requirements, and implementation gates.

## Required Files

```text
tools/verify_fuel_slice0_bench_results.py
maps/bench/fuel_slice0_bench_results.csv
docs/bench/FUEL_SLICE0_BENCH_RESULTS.md
```

## Required Static Checks

| Test | Expected |
|---|---|
| required rows | all required `FUEL-001` through `FUEL-004` rows exist |
| default status | all default rows are `not_run` |
| FUEL-001 vectors | zero, 1 ms, 2 ms, 3 ms, 4 ms vectors exist |
| FUEL-002 vector | `$00C5`, 197 counts, 3.005981 ms exists |
| FUEL-003 row | zero vector row exists and may become `partial` if only zero-vector tested |
| FUEL-004 row | dropout/unsafe row exists and cannot pass from SLICE-0 vector test alone |
| controlled status | `pass_fail` is one of `not_run`, `pass`, `fail`, `partial` |
| pass measurement | any `pass` row includes `measured_pw_ms` or `measured_register_or_debug_counts` |
| FUEL-004 gate | FUEL-004 `pass` requires dropout/unsafe path evidence |
| SLICE-1 gate | no row can mark SLICE-1 allowed unless FUEL-001 through FUEL-004 are pass |

## Command

```bash
python tools/verify_fuel_slice0_bench_results.py
```

Required default output:

```text
PASS: fuel SLICE-0 bench results verification
```

Default PASS means the capture file is structurally valid, not that the bench tests have passed.

## Required Initial Rows

```csv
proof_id,vector_name,commanded_counts_hex,commanded_counts_dec,expected_pw_ms,measured_pw_ms,measured_pulse_present,measured_register_or_debug_counts,aldl_counts_match,scope_channel,test_condition,pass_fail,evidence_file,notes
FUEL-001,zero,$0000,0,0.000000,,,,,scope/ALDL,bench-only,not_run,,
FUEL-001,one_ms,$0042,66,1.007080,,,,,scope/ALDL,bench-only,not_run,,
FUEL-001,two_ms,$0083,131,1.998901,,,,,scope/ALDL,bench-only,not_run,,
FUEL-001,three_ms,$00C5,197,3.005981,,,,,scope/ALDL,bench-only,not_run,,
FUEL-001,four_ms,$0106,262,3.997803,,,,,scope/ALDL,bench-only,not_run,,
FUEL-002,three_ms,$00C5,197,3.005981,,,,,scope,bench-only,not_run,,
FUEL-003,zero,$0000,0,0.000000,,,,,scope/ALDL,bench-only zero vector,not_run,,
FUEL-004,dropout_zero,$0000,0,0.000000,,,,,scope/ALDL,dropout path required,not_run,,
```

## Tolerance Rule

```text
pass if measured PW is within ±0.05 ms or ±3% of expected, whichever is larger
```

For `$00C5`:

```text
$00C5 = 197 counts
197 / 65.536 = 3.005981 ms
acceptable initial range with ±0.05 ms:
  2.956 ms to 3.056 ms
```

## Gate Interpretation

```text
If FUEL-001/FUEL-002 pass and FUEL-003 is partial:
  $3FCE vector path is proven enough for fixed-output proof only.

If FUEL-001 through FUEL-004 pass:
  SLICE-1 planning can move toward implementation.

If FUEL-004 is not passed:
  no engine-runnable fuel-only slice yet.
```

## Pass Criteria

```text
PASS:
  result file is structurally valid.
  required rows are present.
  status values are controlled.
  default rows are not_run.
  pass rows require real measurements.
  FUEL-004 cannot pass without dropout/unsafe evidence.
  SLICE-1 allowed claim is blocked unless FUEL-001 through FUEL-004 pass.
```

## Fail / Rework Criteria

```text
REWORK:
  required proof rows are missing.
  pass_fail uses an uncontrolled value.
  a pass row lacks measured data.
  FUEL-004 is marked pass from bench-only vector testing.
  SLICE-1 is marked allowed before FUEL-001 through FUEL-004 pass.
  default rows claim pass without evidence.
```
