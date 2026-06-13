# Working State

This repository is the working directory for the 7427 hardware-contract reverse-engineering project. Do not treat downloadable ZIPs as primary project state. Git history is the version record.

## Current focus

Extract the CPU-to-hardware contract for the GM 16197427 PCM using the `$31` BMHM/HAC disassembly, then build a clean minimal OS/control program that preserves required hardware behavior.

Current technical focus after the stock-driver preservation policy pass:

```text
stock driver preservation policy: complete as repo-level contract
spark stock handoff preservation: complete as static seam contract
fuel SLICE-0 bench harness: complete, bench-only / not engine-runnable
fuel SLICE-0 bench result capture: complete, default status not_run
fuel next work: run local verifiers and collect real bench data for FUEL-001/FUEL-002/FUEL-003 partial
FUEL-004: not_run until real dropout/unsafe zero path is invoked
SLICE-1: blocked until FUEL-001 through FUEL-004 pass
```

## Stock driver preservation policy

Completed:

- `tools/build_stock_driver_preservation_policy.py`
- `docs/contracts/STOCK_DRIVER_PRESERVATION_POLICY.md`
- `maps/contracts/stock_driver_preservation_policy.csv`
- `docs/tests/STOCK_DRIVER_PRESERVATION_POLICY_TEST.md`

Repo-level rule:

```text
Preserved stock driver:
  static completeness proof required
  input/state seeding proof required
  side effects/order/delay proof required
  no physical per-register proof required before use

Custom direct writer:
  bench proof required
```

Subsystem classification:

```text
fuel:
  bench_required_unless_stock_driver_preserved
  current compact $3FCE path remains bench-proof gated

spark:
  stock_preservation_allowed_after_static_contract
  clean spark state -> preserved stock handoff routine
  custom direct spark writer remains blocked/bench-required
  physical spark ASIC semantics deferred, not blocking

iac:
  bench_required_unless_stock_driver_preserved
  custom A/B/Enable/park writer remains bench-required
  stock-driver preservation may reclassify IAC if complete stock IAC driver is preserved
```

Guardrails:

```text
Allowed:
  clean OS calculates desired state
  clean OS feeds stock-compatible state variables
  preserved stock driver owns hardware-facing writes
  physical per-register semantics are documented as deferred

Blocked:
  partial stock driver copy treated as complete
  unseeded state entering preserved stock driver
  custom direct ASIC writer without bench proof
  simplified raw-register writer without bench proof
  deleting rolling state, mirror/ack behavior, monitor flags, or delay assumptions
  claiming physical register meaning without trace or bench evidence
  claiming final engine safety solely from static preservation
```

## Spark stock handoff preservation

Completed:

- `tools/build_spark_stock_handoff_preservation_contract.py`
- `docs/contracts/SPARK_STOCK_HANDOFF_PRESERVATION_CONTRACT.md`
- `maps/contracts/spark_stock_handoff_preservation_contract.csv`
- `docs/tests/SPARK_STOCK_HANDOFF_PRESERVATION_CONTRACT_TEST.md`

Spark authority policy:

```text
Clean OS may calculate desired spark.
Clean OS may feed stock-compatible spark state.
Preserved stock handoff routine owns all ASIC-facing spark writes.
Direct custom ASIC spark writes remain forbidden.
```

Proof-category split:

```text
custom_spark_writer:
  blocked_bench_required

stock_spark_handoff_preservation:
  allowed_after_static_contract

spark_physical_semantics:
  deferred_bench_optional
```

No spark implementation exists yet.

## Fuel SLICE-0 bench path

Completed:

- `source/minimal_os/fuel/slice0_bench_harness.asm`
- `tools/verify_fuel_slice0_bench_harness.py`
- `tests/static/fuel_slice0_bench_vectors.csv`
- `docs/bench/FUEL_SLICE0_BENCH_HARNESS.md`
- `docs/tests/FUEL_SLICE0_BENCH_HARNESS_TEST.md`
- `tools/verify_fuel_slice0_bench_results.py`
- `maps/bench/fuel_slice0_bench_results.csv`
- `docs/bench/FUEL_SLICE0_BENCH_RESULTS.md`
- `docs/tests/FUEL_SLICE0_BENCH_RESULTS_TEST.md`

Current fuel state:

```text
SLICE-0 harness: bench-only, fixed vectors only, not engine-runnable
result capture: present, default proof status not_run
FUEL-001: not_run until bench evidence entered
FUEL-002: not_run until bench evidence entered
FUEL-003: not_run; may become partial if only zero-vector path is proven
FUEL-004: not_run until real dropout/unsafe zero path is invoked
SLICE-1: blocked until FUEL-001 through FUEL-004 pass
```

Bench distinction:

```text
$0000 vector:
  proves commanded zero / no-pulse path

dropout/unsafe zero:
  proves safety gate behavior

These are not the same proof.
```

## Current next valid work

Fuel side:

```text
run python tools/verify_fuel_slice0_bench_harness.py
run python tools/verify_fuel_slice0_bench_results.py
bench SLICE-0 fixed vectors
enter only measured evidence in maps/bench/fuel_slice0_bench_results.csv
keep FUEL-004 not_run until real dropout/unsafe path is tested
```

Spark side, when resumed:

```text
static extraction/pinning of complete preserved stock handoff routine range and dependencies
not a custom writer
not direct $3FE8/$3FE6/$3FF6/$3FDC writes
```

IAC side, when resumed:

```text
bench-proof custom A/B/Enable/park writer
or reframe as preserved complete stock IAC hardware driver
```

## Hard boundaries

```text
No SLICE-1 engine-runnable fuel-only skeleton until FUEL-001 through FUEL-004 pass.
No custom direct spark ASIC writer without bench proof.
No simplified raw-angle spark writer.
No IAC direct L3062 writer without bench proof or complete stock-driver preservation.
No ALDL packet implementation as a side effect of policy contracts.
No runtime ASM from planning/policy contracts.
No physical register meaning claims without trace or bench evidence.
```

## Static-map note

The current repo still contains the original static full-map baseline:

```text
maps/full/hardware_access_map_v0.2.csv
```

Do not reference `maps/full/hardware_access_map_v0.3.csv` as committed until it is actually regenerated or uploaded.
