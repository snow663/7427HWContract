# Working State

This repository is the working directory for the 7427 hardware-contract reverse-engineering project. Do not treat downloadable ZIPs as primary project state. Git history is the version record.

## Current focus

Extract the CPU-to-hardware contract for the GM 16197427 PCM using the `$31` BMHM/HAC disassembly, then build a clean minimal OS/control program that preserves required hardware behavior.

Current technical focus after the IAC stock-driver preservation contract pass:

```text
stock driver preservation policy: complete as repo-level contract
spark stock handoff preservation: complete as static seam contract
fuel stock-output-driver preservation: contract defined, proof not complete
fuel stock-output-driver static proof index: complete as current decision index
fuel stock-driver preservation decision: incomplete_continue_3FCE_bench_route
fuel SLICE-0 bench harness: complete, bench-only / not engine-runnable
fuel SLICE-0 bench result capture: complete, default status not_run
fuel current active route: compact $3FCE SLICE-0 bench path remains active fallback
IAC stock-driver preservation: contract defined, proof not complete
IAC custom direct writer: bench-required
IAC active route if resumed: no direct L3062/L3060/L3FFC writer without bench proof or complete stock-driver preservation
FUEL-004: not_run until real dropout/unsafe zero path is invoked under the active compact path
SLICE-1: blocked under current compact path until FUEL-001 through FUEL-004 pass unless complete stock fuel output-driver preservation is later accepted
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
  contract_defined_preservation_not_proven
  custom A/B/Enable/park writer remains bench-required
  stock-driver preservation may reclassify IAC only after complete stock IAC driver proof
```

Guardrails:

```text
Allowed:
  clean OS calculates desired state
  clean OS feeds stock-compatible state variables
  preserved stock driver owns hardware-facing writes
  physical per-register semantics are documented as deferred only for complete stock-driver preservation

Blocked:
  partial stock driver copy treated as complete
  unseeded state entering preserved stock driver
  custom direct ASIC writer without bench proof
  simplified raw-register writer without bench proof
  deleting rolling state, mirror/ack behavior, monitor flags, delay assumptions, port shadows, or reset/park behavior
  claiming physical register meaning without trace or bench evidence
  claiming final engine safety solely from static preservation
```

## Fuel stock-output-driver preservation

Completed as static decision contract:

- `tools/build_fuel_stock_output_driver_preservation_contract.py`
- `docs/contracts/FUEL_STOCK_OUTPUT_DRIVER_PRESERVATION_CONTRACT.md`
- `maps/contracts/fuel_stock_output_driver_preservation_contract.csv`
- `docs/tests/FUEL_STOCK_OUTPUT_DRIVER_PRESERVATION_CONTRACT_TEST.md`

Fuel authority policy:

```text
Clean OS may calculate desired fuel mass / BPW / enrichment state.
Clean OS may feed stock-compatible fuel state into a preserved stock fuel scheduler/output driver.
Preserved stock fuel scheduler/output driver owns all hardware-facing fuel writes.
Direct custom fuel ASIC / $3FCE writers remain bench-proof gated.
```

Proof-category split:

```text
preserved_stock_fuel_output_driver:
  static-proof gated
  proof not complete

compact_direct_$3FCE_writer:
  bench-proof gated
  active fallback path

fuel_physical_scheduler_semantics:
  deferred only if complete stock output driver is preserved
```

Current fuel decision:

```text
The fuel stock-output-driver preservation contract is defined, but preservation proof is not complete.
Therefore the compact $3FCE SLICE-0 bench path remains the active route.
FUEL-001 through FUEL-004 still gate SLICE-1 under that active route.
```

## Fuel stock-output-driver static proof index

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

What the proof index currently establishes:

```text
candidate stock normal-TBI fuel output path:
  partially identified around source/31/BMHM_HAC_ORG_7100_to_end.asm:83FB-858A

normal hardware-facing writes inside candidate range:
  partially identified: $3FCE, $3FF2, $3FFC

output-cycling $3FCE writes:
  identified and excluded from production fuel-driver acceptance

required stock-compatible inputs:
  incomplete

scheduler/timer/interrupt dependencies:
  unresolved

enable/disable/dropout/no-fuel paths:
  incomplete
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

## IAC stock-driver preservation

Completed as static decision contract:

- `tools/build_iac_stock_driver_preservation_contract.py`
- `docs/contracts/IAC_STOCK_DRIVER_PRESERVATION_CONTRACT.md`
- `maps/contracts/iac_stock_driver_preservation_contract.csv`
- `docs/tests/IAC_STOCK_DRIVER_PRESERVATION_CONTRACT_TEST.md`

IAC authority policy if preservation is eventually accepted:

```text
clean idle-air decision
→ stock-compatible IAC state
→ preserved stock IAC output driver
→ stock routine owns A/B/Enable/phase/park behavior
```

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

Known source anchors only; not a completed proof:

```text
L925E setup candidate:
  setup/park-related state, including L4EB0 -> L0007

L93E1-L940A reset/park candidate:
  reset-in-work, zero-position, run/start request, ignition-off, park, engine-running branches

L9B10 / L9BD6 position update candidates:
  decrement/increment L0007 present motor position

LF405 / LFB14-LFB69 port-output candidates:
  L3062 / L3060 / L3FFC interactions, port-shadow and strobe behavior
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

Current fuel bench state:

```text
SLICE-0 harness: bench-only, fixed vectors only, not engine-runnable
result capture: present, default proof status not_run
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

The current repo still contains the original static full-map baseline:

```text
maps/full/hardware_access_map_v0.2.csv
```

Do not reference `maps/full/hardware_access_map_v0.3.csv` as committed until it is actually regenerated or uploaded.
