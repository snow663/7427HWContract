# Fuel SLICE-0 Bench Results

## Purpose

Define the structured place where actual SLICE-0 bench measurements are recorded and checked against the fuel proof gates.

This document and its CSV do not claim any proof has passed by default. Initial status is:

```text
not_run
```

until real scope, logic-analyzer, and/or ALDL/debug data is entered.

## Result File

```text
maps/bench/fuel_slice0_bench_results.csv
```

## Verifier

```bash
python tools/verify_fuel_slice0_bench_results.py
```

The verifier enforces:

```text
all FUEL-001 vectors exist
FUEL-002 includes $00C5 / 197 / 3.005981 ms
FUEL-003 exists and may be partial if only zero-vector tested
FUEL-004 cannot pass from SLICE-0 vector testing alone
pass_fail is one of not_run, pass, fail, partial
pass rows include measured_pw_ms or measured_register_or_debug_counts
FUEL-004 pass requires dropout/unsafe path evidence
SLICE-1 cannot be marked allowed unless FUEL-001 through FUEL-004 are pass
```

## Measurement Tolerance

Initial conservative tolerance:

```text
pass if measured PW is within ±0.05 ms or ±3% of expected, whichever is larger
```

For the key vector:

```text
$00C5 = 197 counts
197 / 65.536 = 3.005981 ms
acceptable initial range with ±0.05 ms:
  2.956 ms to 3.056 ms
```

## Default Result Rows

| Proof | Vector | Counts | Expected ms | Default status | Condition |
|---|---|---:|---:|---|---|
| FUEL-001 | zero | `$0000` | 0.000000 | not_run | bench-only |
| FUEL-001 | one_ms | `$0042` | 1.007080 | not_run | bench-only |
| FUEL-001 | two_ms | `$0083` | 1.998901 | not_run | bench-only |
| FUEL-001 | three_ms | `$00C5` | 3.005981 | not_run | bench-only |
| FUEL-001 | four_ms | `$0106` | 3.997803 | not_run | bench-only |
| FUEL-002 | three_ms | `$00C5` | 3.005981 | not_run | bench-only |
| FUEL-003 | zero | `$0000` | 0.000000 | not_run | bench-only zero vector |
| FUEL-004 | dropout_zero | `$0000` | 0.000000 | not_run | dropout path required |

## Bench Procedure

```text
1. Confirm engine cannot run from this harness.
2. Attach scope/logic analyzer to injector command output or equivalent bench output.
3. Invoke FUEL_SLICE0_WRITE_ZERO.
4. Confirm no pulse / zero command.
5. Invoke FUEL_SLICE0_WRITE_1MS.
6. Measure pulse width.
7. Repeat for 2 ms, 3 ms, and 4 ms vectors.
8. Confirm ALDL/debug raw counts match the commanded vector if debug path exists.
9. Record each measurement in fuel_slice0_bench_results.csv.
10. Do not mark FUEL-004 pass unless dropout/unsafe zero path is actually invoked.
```

## Gate Interpretation

If `FUEL-001` and `FUEL-002` pass and `FUEL-003` is partial:

```text
$3FCE vector path is proven enough for fixed-output proof only.
```

If `FUEL-001` through `FUEL-004` pass:

```text
SLICE-1 planning can move toward implementation.
```

If `FUEL-004` is not passed:

```text
no engine-runnable fuel-only slice yet.
```

## Important Limitation

SLICE-0 fixed-vector testing can help prove `FUEL-001`, `FUEL-002`, and partial `FUEL-003`.

SLICE-0 fixed-vector testing does not fully prove `FUEL-004` unless the dropout/unsafe zero path is separately invoked and recorded.
