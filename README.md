# 7427HWContract

Working repository for the GM 16197427 `7427` PCM hardware-contract reverse-engineering project.

The repo is the project state. Downloadable ZIPs/CSVs are exports only and should not become the primary working record.

## Objective

Extract the HC11 CPU-to-hardware/ASIC contract from the stock `$31` BMHM/HAC ROM/disassembly, then use that contract to build a clean minimal engine-control OS:

- speed-density TBI fuel
- spark control
- IAC/idle air control
- AE / PE / DFCO
- crank / warmup / afterstart fuel
- injector low-pulsewidth transfer correction
- ALDL/debug visibility

Out of scope unless proven hardware-required:

- automatic transmission strategy
- TCC strategy
- EGR behavior
- EVAP/purge behavior
- inherited GM mode-word baggage

## Current repo index

Core state:

- `docs/WORKING_STATE.md` — active project state and next target/decision point
- `docs/contracts/*.md` — current subsystem and policy contracts
- `docs/bench/*.md` — bench proof packages, harness notes, and result capture docs
- `docs/tests/*.md` — bench/static test plans
- `maps/contracts/*.csv` — machine-readable contract summaries
- `maps/bench/*.csv` — bench proof/result matrices
- `tests/static/*.csv` — static vector tables
- `source/31/BMHM_HAC_ORG_7100_to_end.asm` — source listing used by contract builders
- `source/minimal_os/fuel/*.asm` — fuel-side source artifacts; only bench-safe/provisional paths where documented
- `source/minimal_os/spark/README.md` — spark source API/layout boundary, no ASM implementation
- `source/minimal_os/iac/README.md` — IAC source API/layout boundary, no ASM implementation
- `tools/*.py` — repo-relative analysis/build tools

Legacy/static-base artifacts still present:

- `maps/full/hardware_access_map_v0.2.csv` — original full static access map baseline

Do not claim a regenerated `maps/full/hardware_access_map_v0.3.csv` exists until it is committed.

## Current policy stack

### Stock driver preservation policy

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

### Spark stock handoff preservation contract

- `tools/build_spark_stock_handoff_preservation_contract.py`
- `docs/contracts/SPARK_STOCK_HANDOFF_PRESERVATION_CONTRACT.md`
- `maps/contracts/spark_stock_handoff_preservation_contract.csv`
- `docs/tests/SPARK_STOCK_HANDOFF_PRESERVATION_CONTRACT_TEST.md`

This is a static seam contract only. It does not implement spark ASM and does not create a spark writer.

Spark hardware authority model:

```text
Clean OS may calculate desired spark.
Clean OS may feed stock-compatible spark state.
Preserved stock handoff routine owns all ASIC-facing spark writes.
Direct custom ASIC spark writes remain forbidden.
```

### Fuel SLICE-0 bench path

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
FUEL-001/FUEL-002/FUEL-003: waiting on bench evidence
FUEL-004: not_run until real dropout/unsafe zero path is invoked
SLICE-1: blocked until FUEL-001 through FUEL-004 pass
```

## Current next target

Fuel side next action is bench-data capture, not code expansion:

```text
run python tools/verify_fuel_slice0_bench_harness.py
run python tools/verify_fuel_slice0_bench_results.py
bench SLICE-0 fixed vectors
record measured values in maps/bench/fuel_slice0_bench_results.csv
keep FUEL-004 not_run until real dropout/unsafe path is tested
```

Spark side, when resumed, should be static extraction/pinning of the complete preserved stock handoff routine range and dependencies, not a custom writer.

IAC side, when resumed, must either bench-prove a custom A/B/Enable/park writer or reframe as a preserved complete stock IAC hardware driver.

## Current hard boundaries

```text
No SLICE-1 engine-runnable fuel-only skeleton until FUEL-001 through FUEL-004 pass.
No custom direct spark ASIC writer without bench proof.
No simplified raw-angle spark writer.
No IAC direct L3062 writer without bench proof or complete stock-driver preservation.
No ALDL packet implementation as a side effect of policy contracts.
No runtime ASM from planning/policy contracts.
No physical register meaning claims without trace or bench evidence.
```

## Working rule

Use stable filenames for current work. Let Git history preserve versions. Avoid creating parallel `almost same` copies unless there is a real branch/release reason.
