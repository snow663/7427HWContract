# FUEL SLICE-0 Bench Execution Checklist

## Purpose

Turn the active compact `$3FCE` fuel route proof gates into an exact bench execution checklist.

This checklist does not implement fuel code, does not mark any proof passed, and does not relax `SLICE-1`.

## Active Route

```text
active_fuel_route: compact $3FCE SLICE-0 bench path
FUEL-001 through FUEL-004: required before SLICE-1 under this route
FUEL-004: requires real dropout/unsafe zero path, not a zero-vector call
```

## Local Precheck

Run from repo root before bench execution:

```bash
python tools/verify_fuel_slice0_bench_harness.py
python tools/verify_fuel_slice0_bench_results.py
```

Expected pre-bench interpretation:

```text
harness verifier PASS: static harness structure is valid
results verifier PASS: result CSV structure is valid; proof rows still not_run
no bench proof has passed until measured evidence is entered
```

## Bench Execution Order

| Step | Gate | Harness entry | Vector | Counts | Expected ms | Required observation | Pass condition |
|---|---|---|---|---:|---:|---|---|
| PRE-001 | precondition | none |  |  |  | confirm harness cannot run engine; bench output/load only | engine cannot run from harness and injector output is safely loaded/observed |
| FUEL-003-ZERO | FUEL-003 partial | FUEL_SLICE0_WRITE_ZERO | $0000 | 0 | 0.000000 | no injector pulse / zero command path | no output pulse and commanded/debug count is zero |
| FUEL-001-1MS | FUEL-001 | FUEL_SLICE0_WRITE_1MS | $0042 | 66 | 1.007080 | pulse width correlates to commanded count | measured PW within ±0.05 ms or ±3%, whichever is larger |
| FUEL-001-2MS | FUEL-001 | FUEL_SLICE0_WRITE_2MS | $0083 | 131 | 1.998901 | pulse width correlates to commanded count | measured PW within ±0.05 ms or ±3%, whichever is larger |
| FUEL-002-3MS | FUEL-002 | FUEL_SLICE0_WRITE_3MS | $00C5 | 197 | 3.005981 | $00C5 produces 2.956-3.056 ms pulse | measured PW is 2.956-3.056 ms and commanded/debug count is 197 if available |
| FUEL-001-4MS | FUEL-001 | FUEL_SLICE0_WRITE_4MS | $0106 | 262 | 3.997803 | pulse width correlates to commanded count | measured PW within ±0.05 ms or ±3%, whichever is larger |
| FUEL-004-DROPOUT | FUEL-004 | not proven by fixed-vector harness | $0000 | 0 | 0.000000 | real dropout/unsafe/no-fuel path asserts zero and injector pulse stops/remains absent | actual dropout/unsafe path is invoked and forces/stays zero with no injector pulse |
| POST-001 | postcheck | none |  |  |  | results CSV updated and verifier re-run | tools/verify_fuel_slice0_bench_results.py passes with measured evidence |

## Evidence Recording

Record only measured evidence in:

```text
maps/bench/fuel_slice0_bench_results.csv
docs/bench/FUEL_SLICE0_BENCH_RESULTS.md
```

Required evidence should include scope/logic-analyzer pulse width, pulse-present state, commanded/debug counts if available, channel/probe information, and evidence filename or note.

## Gate Interpretation

```text
FUEL-001 pass + FUEL-002 pass + FUEL-003 partial/pass:
  fixed-vector $3FCE path proven only

FUEL-004 not pass:
  no SLICE-1

FUEL-001 through FUEL-004 all pass:
  SLICE-1 planning may begin under the compact $3FCE route
```

## Zero Vector vs Dropout Proof

```text
$0000 vector:
  proves commanded zero / no-pulse path

dropout/unsafe zero:
  proves safety gate behavior
```

These are not the same proof.
