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
- `docs/contracts/*.md` — current subsystem, policy, and gate contracts
- `docs/bench/*.md` — bench proof packages, harness notes, run checklists, and result capture docs
- `docs/tests/*.md` — bench/static test plans
- `maps/contracts/*.csv` — machine-readable contract/gate summaries
- `maps/bench/*.csv` — bench proof/checklist/result matrices
- `maps/full/hardware_access_map_v0.3.csv` — regenerated full static access map from `build_hw_map.py`
- `maps/current/hardware_access_map_hw_only.csv` — regenerated hardware-only access map from `build_hw_map.py`
- `tests/static/*.csv` — static vector tables
- `source/31/BMHM_HAC_ORG_7100_to_end.asm` — source listing used by contract builders
- `source/minimal_os/fuel/*.asm` — fuel-side source artifacts; only bench-safe/provisional paths where documented
- `source/minimal_os/spark/README.md` — spark source API/layout boundary, no ASM implementation
- `source/minimal_os/iac/README.md` — IAC source API/layout boundary, no ASM implementation
- `tools/*.py` — repo-relative analysis/build/verification tools

Legacy/static-base artifacts still present:

- `maps/full/hardware_access_map_v0.2.csv` — original full static access map baseline

## Current hardware-output gate matrix

- `tools/build_hardware_output_gate_matrix.py`
- `docs/contracts/HARDWARE_OUTPUT_GATE_MATRIX.md`
- `maps/contracts/hardware_output_gate_matrix.csv`
- `docs/tests/HARDWARE_OUTPUT_GATE_MATRIX_TEST.md`

Single-source subsystem gate summary:

```text
Spark:
  stock handoff preservation accepted as the working route
  custom direct spark writer remains bench-required
  physical ASIC spark semantics deferred

Fuel:
  stock output-driver preservation considered
  decision = incomplete_continue_3FCE_bench_route
  compact $3FCE SLICE-0 bench path remains active
  SLICE-1 still blocked by FUEL-001 through FUEL-004

IAC:
  stock driver preservation contract defined
  preservation proof not complete
  custom direct A/B/Enable/park writer remains bench-required
```

Gate-row decisions:

```text
fuel_compact_3FCE: active_bench_route
fuel_stock_output_driver: candidate_incomplete
spark_stock_handoff: accepted_static_route
spark_custom_writer: blocked_bench_required
iac_stock_driver: contract_defined_not_proven
iac_custom_writer: blocked_bench_required
```

Non-relaxation clauses:

```text
The matrix does not make SLICE-1 legal.
The matrix does not mark FUEL-001 through FUEL-004 passed.
The matrix does not accept fuel stock-driver preservation.
The matrix does not accept IAC stock-driver preservation.
The matrix does not permit a custom direct spark writer.
The matrix does not permit a custom direct IAC writer.
The matrix does not create runtime ASM.
```

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

### Fuel stock-output-driver preservation contract

- `tools/build_fuel_stock_output_driver_preservation_contract.py`
- `docs/contracts/FUEL_STOCK_OUTPUT_DRIVER_PRESERVATION_CONTRACT.md`
- `maps/contracts/fuel_stock_output_driver_preservation_contract.csv`
- `docs/tests/FUEL_STOCK_OUTPUT_DRIVER_PRESERVATION_CONTRACT_TEST.md`

This is a static decision-seam contract only. It does not implement fuel ASM and does not create a fuel writer.

### Fuel stock-output-driver static proof index

- `tools/build_fuel_stock_output_driver_static_proof_index.py`
- `docs/contracts/FUEL_STOCK_OUTPUT_DRIVER_STATIC_PROOF_INDEX.md`
- `maps/contracts/fuel_stock_output_driver_static_proof_index.csv`
- `docs/tests/FUEL_STOCK_OUTPUT_DRIVER_STATIC_PROOF_INDEX_TEST.md`

Current fuel decision:

```text
fuel stock-driver preservation contract: defined
fuel stock-driver preservation proof index: complete as current decision index
fuel stock-driver preservation decision: incomplete_continue_3FCE_bench_route
active fuel route: compact $3FCE SLICE-0 bench path
FUEL-001 through FUEL-004: still gate SLICE-1 under active compact route
```

Current locked distinction:

```text
Fuel preservation contract exists
≠ fuel preservation proof is complete
≠ compact $3FCE bench gate is bypassed
```

### Spark stock handoff preservation contract

- `tools/build_spark_stock_handoff_preservation_contract.py`
- `docs/contracts/SPARK_STOCK_HANDOFF_PRESERVATION_CONTRACT.md`
- `maps/contracts/spark_stock_handoff_preservation_contract.csv`
- `docs/tests/SPARK_STOCK_HANDOFF_PRESERVATION_CONTRACT_TEST.md`

This is a static seam contract only. It does not implement spark ASM and does not create a spark writer.

### IAC stock-driver preservation contract

- `tools/build_iac_stock_driver_preservation_contract.py`
- `docs/contracts/IAC_STOCK_DRIVER_PRESERVATION_CONTRACT.md`
- `maps/contracts/iac_stock_driver_preservation_contract.csv`
- `docs/tests/IAC_STOCK_DRIVER_PRESERVATION_CONTRACT_TEST.md`

This is a static decision-seam contract only. It does not implement IAC ASM and does not create a direct IAC writer.

## Fuel SLICE-0 bench path

- `source/minimal_os/fuel/slice0_bench_harness.asm`
- `tools/verify_fuel_slice0_bench_harness.py`
- `tests/static/fuel_slice0_bench_vectors.csv`
- `docs/bench/FUEL_SLICE0_BENCH_HARNESS.md`
- `docs/tests/FUEL_SLICE0_BENCH_HARNESS_TEST.md`
- `tools/verify_fuel_slice0_bench_results.py`
- `maps/bench/fuel_slice0_bench_results.csv`
- `docs/bench/FUEL_SLICE0_BENCH_RESULTS.md`
- `docs/tests/FUEL_SLICE0_BENCH_RESULTS_TEST.md`
- `tools/build_fuel_slice0_bench_execution_checklist.py`
- `docs/bench/FUEL_SLICE0_BENCH_EXECUTION_CHECKLIST.md`
- `maps/bench/fuel_slice0_bench_execution_checklist.csv`
- `docs/tests/FUEL_SLICE0_BENCH_EXECUTION_CHECKLIST_TEST.md`

Current fuel bench state:

```text
SLICE-0 harness: bench-only, fixed vectors only, not engine-runnable
result capture: present, default proof status not_run
bench execution checklist: present, no proof status change
FUEL-001/FUEL-002/FUEL-003: waiting on bench evidence
FUEL-004: not_run until real dropout/unsafe zero path is invoked
SLICE-1: blocked under active compact route until FUEL-001 through FUEL-004 pass
```

## Current next target

Fuel compact `$3FCE` path remains bench-data capture, not code expansion:

```text
run python tools/verify_fuel_slice0_bench_harness.py
run python tools/verify_fuel_slice0_bench_results.py
use docs/bench/FUEL_SLICE0_BENCH_EXECUTION_CHECKLIST.md
bench SLICE-0 fixed vectors
record measured values in maps/bench/fuel_slice0_bench_results.csv
keep FUEL-004 not_run until real dropout/unsafe path is tested
```

Fuel stock-driver preservation path, if chosen, continues from the static proof index:

```text
complete stock fuel scheduler/output-driver range
all required BPW/fuel-mode/timer/dropout/no-fuel inputs
all hardware writes and side effects
order/delay/interrupt assumptions
reset/first-event/dropout safety
no alternate custom direct writer
accepted_static_route vs rejected_3FCE_bench_route_required
```

Spark side, when resumed, should be static extraction/pinning of the complete preserved stock handoff routine range and dependencies, not a custom writer.

IAC side, when resumed, must either bench-prove a custom A/B/Enable/park writer or complete stock IAC hardware-driver preservation proof first.

## Current hard boundaries

```text
No SLICE-1 engine-runnable fuel-only skeleton under the compact $3FCE path until FUEL-001 through FUEL-004 pass.
No compact direct $3FCE writer promoted to engine-runnable without FUEL-001 through FUEL-004 proof unless complete stock fuel output-driver preservation supersedes that path.
No fuel stock-driver preservation accepted while its decision remains incomplete_continue_3FCE_bench_route.
No partial stock fuel output driver treated as complete.
No custom direct spark ASIC writer without bench proof.
No simplified raw-angle spark writer.
No IAC direct L3062/L3060/L3FFC writer without bench proof or complete stock-driver preservation.
No ALDL packet implementation as a side effect of policy contracts.
No runtime ASM from planning/policy/static-proof contracts.
No physical register meaning claims without trace or bench evidence, except explicitly deferred semantics for complete preserved stock drivers.
```

## Working rule

Use stable filenames for current work. Let Git history preserve versions. Avoid creating parallel `almost same` copies unless there is a real branch/release reason.
