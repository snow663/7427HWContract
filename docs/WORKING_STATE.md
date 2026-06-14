# Working State

This repository is the working directory for the 7427 hardware-contract reverse-engineering project. Do not treat downloadable ZIPs as primary project state. Git history is the version record.

## Current focus

Extract the CPU-to-hardware contract for the GM 16197427 PCM using the `$31` BMHM/HAC disassembly, then build a clean minimal OS/control program that preserves required hardware behavior.

Current technical focus after the hardware-output gate matrix and fuel bench-execution checklist pass:

```text
hardware output gate matrix: complete as current single-source subsystem gate summary
stock driver preservation policy: complete as repo-level authority model
spark stock handoff preservation: accepted static-proof route; no custom direct writer
fuel stock-output-driver preservation: considered, proof incomplete
fuel stock-output-driver static proof index: decision = incomplete_continue_3FCE_bench_route
fuel current active route: compact $3FCE SLICE-0 bench path
fuel SLICE-0 bench harness/result capture: complete, proof status not_run
fuel SLICE-0 bench execution checklist: complete as run checklist, no proof status change
IAC stock-driver preservation: contract defined, proof not complete
IAC custom direct writer: bench-required
FUEL-004: not_run until real dropout/unsafe zero path is invoked under the active compact path
SLICE-1: blocked under current compact path until FUEL-001 through FUEL-004 pass unless complete stock fuel output-driver preservation is later accepted
```

## Hardware output gate matrix

Completed as the current project-level gate summary:

- `tools/build_hardware_output_gate_matrix.py`
- `docs/contracts/HARDWARE_OUTPUT_GATE_MATRIX.md`
- `maps/contracts/hardware_output_gate_matrix.csv`
- `docs/tests/HARDWARE_OUTPUT_GATE_MATRIX_TEST.md`

Current route stack:

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

Gate rows:

```text
fuel_compact_3FCE:
  active_bench_route
  FUEL-001 through FUEL-004 still gate SLICE-1

fuel_stock_output_driver:
  candidate_incomplete
  cannot supersede compact $3FCE bench path yet

spark_stock_handoff:
  accepted_static_route
  clean spark state may feed preserved stock handoff after static completeness proof

spark_custom_writer:
  blocked_bench_required

iac_stock_driver:
  contract_defined_not_proven
  cannot bypass IAC bench proof yet

iac_custom_writer:
  blocked_bench_required
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

## Fuel stock-output-driver preservation

Completed as static decision contract:

- `tools/build_fuel_stock_output_driver_preservation_contract.py`
- `docs/contracts/FUEL_STOCK_OUTPUT_DRIVER_PRESERVATION_CONTRACT.md`
- `maps/contracts/fuel_stock_output_driver_preservation_contract.csv`
- `docs/tests/FUEL_STOCK_OUTPUT_DRIVER_PRESERVATION_CONTRACT_TEST.md`

Completed as current static decision index:

- `tools/build_fuel_stock_output_driver_static_proof_index.py`
- `docs/contracts/FUEL_STOCK_OUTPUT_DRIVER_STATIC_PROOF_INDEX.md`
- `maps/contracts/fuel_stock_output_driver_static_proof_index.csv`
- `docs/tests/FUEL_STOCK_OUTPUT_DRIVER_STATIC_PROOF_INDEX_TEST.md`

Current proof-index decision:

```text
fuel_stock_driver_preservation:
  incomplete_continue_3FCE_bench_route

active_fuel_route:
  compact $3FCE SLICE-0 bench path

SLICE-1:
  still blocked under active compact route until FUEL-001 through FUEL-004 pass
```

Locked interpretation:

```text
Fuel preservation contract exists
≠ fuel preservation proof is complete
≠ compact $3FCE bench gate is bypassed
```

Until this proof index is upgraded to `accepted_static_route`, the compact `$3FCE` bench route remains active and FUEL-001 through FUEL-004 still gate SLICE-1.

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

No spark implementation exists yet.

## IAC stock-driver preservation

Completed as static decision contract:

- `tools/build_iac_stock_driver_preservation_contract.py`
- `docs/contracts/IAC_STOCK_DRIVER_PRESERVATION_CONTRACT.md`
- `maps/contracts/iac_stock_driver_preservation_contract.csv`
- `docs/tests/IAC_STOCK_DRIVER_PRESERVATION_CONTRACT_TEST.md`

Current IAC decision:

```text
iac_stock_driver_preservation:
  contract_defined_preservation_not_proven

custom_iac_writer:
  bench_required

active_iac_route_if_work_resumes:
  no custom direct IAC writer without bench proof
  or complete stock IAC driver preservation proof first
```

Locked interpretation:

```text
IAC preservation contract exists
≠ IAC preservation proof is complete
≠ custom A/B/Enable/park bench proof is bypassed
```

Until a later IAC static proof index reaches `accepted_static_route`, custom direct IAC output remains bench-gated.

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
- `tools/build_fuel_slice0_bench_execution_checklist.py`
- `docs/bench/FUEL_SLICE0_BENCH_EXECUTION_CHECKLIST.md`
- `maps/bench/fuel_slice0_bench_execution_checklist.csv`
- `docs/tests/FUEL_SLICE0_BENCH_EXECUTION_CHECKLIST_TEST.md`

Current fuel bench state:

```text
SLICE-0 harness: bench-only, fixed vectors only, not engine-runnable
result capture: present, default proof status not_run
bench execution checklist: present, no proof status change
FUEL-001: not_run until bench evidence entered
FUEL-002: not_run until bench evidence entered
FUEL-003: not_run; may become partial if only zero-vector path is proven
FUEL-004: not_run until real dropout/unsafe zero path is invoked
SLICE-1: blocked under current compact path until FUEL-001 through FUEL-004 pass
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

Fuel compact `$3FCE` path:

```text
run python tools/verify_fuel_slice0_bench_harness.py
run python tools/verify_fuel_slice0_bench_results.py
use docs/bench/FUEL_SLICE0_BENCH_EXECUTION_CHECKLIST.md
bench SLICE-0 fixed vectors
enter only measured evidence in maps/bench/fuel_slice0_bench_results.csv
keep FUEL-004 not_run until real dropout/unsafe path is tested
```

Fuel stock-driver preservation path, if chosen:

```text
continue static proof index work from FUEL_STOCK_OUTPUT_DRIVER_STATIC_PROOF_INDEX
prove complete stock fuel scheduler/output-driver range
prove all required BPW/fuel-mode/timer/dropout/no-fuel inputs
prove all hardware writes and side effects
prove order/delay/interrupt assumptions are preserved
prove reset/first-event/dropout state is safe
prove no alternate custom direct writer exists
then decide accepted_static_route vs rejected_3FCE_bench_route_required
```

Spark side, when resumed:

```text
static extraction/pinning of complete preserved stock handoff routine range and dependencies
not a custom writer
not direct $3FE8/$3FE6/$3FF6/$3FDC writes
```

IAC side, when resumed:

```text
complete IAC stock-driver static proof index
or bench-proof custom A/B/Enable/park writer
no direct L3062/L3060/L3FFC writer until one route passes
```

## Hard boundaries

```text
No SLICE-1 engine-runnable fuel-only skeleton under the compact $3FCE path until FUEL-001 through FUEL-004 pass.
No compact direct $3FCE writer promoted to engine-runnable without FUEL-001 through FUEL-004 proof unless complete stock fuel output-driver preservation supersedes that path.
No fuel stock-driver preservation accepted while its decision remains incomplete_continue_3FCE_bench_route.
No partial stock fuel output driver treated as complete.
No custom direct spark ASIC writer without bench proof.
No simplified raw-angle spark writer.
No IAC direct L3062/L3060/L3FFC writer without bench proof or complete stock-driver preservation.
No IAC stock-driver preservation accepted while its decision remains contract_defined_preservation_not_proven.
No partial stock IAC driver treated as complete.
No ALDL packet implementation as a side effect of policy contracts.
No runtime ASM from planning/policy/static-proof contracts.
No physical register meaning claims without trace or bench evidence, except explicitly deferred semantics for complete preserved stock drivers.
```

## Static-map note

The current repo contains regenerated `build_hw_map.py` default outputs including:

```text
maps/full/hardware_access_map_v0.3.csv
maps/current/hardware_access_map_hw_only.csv
```
