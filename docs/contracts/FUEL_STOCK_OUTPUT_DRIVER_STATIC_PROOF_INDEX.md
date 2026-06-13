# FUEL_STOCK_OUTPUT_DRIVER_STATIC_PROOF_INDEX

## Purpose

This proof index decides whether the stock fuel scheduler/output-driver route can supersede the compact `$3FCE` SLICE-0 bench path.

This is a static proof index only. It does not implement fuel ASM, does not create a fuel writer, and does not relax the current SLICE-1 gate.

## Current decision

```text
fuel_stock_driver_preservation:
  incomplete_continue_3FCE_bench_route

active_fuel_route:
  compact $3FCE SLICE-0 bench path

SLICE-1:
  still blocked under active compact route until FUEL-001 through FUEL-004 pass
```

## Candidate stock driver model

```text
clean fuel math
→ stock-compatible BPW / fuel state
→ preserved stock fuel scheduler/output driver
→ stock driver owns hardware-facing writes
```

This route is only accepted if the static proof shows the preserved stock driver is complete and all required inputs, side effects, ordering, timer dependencies, and dropout/no-fuel paths are preserved.

## Existing fallback route

```text
compact $3FCE writer
→ FUEL SLICE-0 bench proof required
```

The fallback remains active because this proof index does not yet accept the preserved stock fuel output-driver route.

## Proof rows

### FUEL-STOCK-PROOF-001 — candidate stock normal-TBI fuel output path

- Category: `routine_range`
- Source reference: `source/31/BMHM_HAC_ORG_7100_to_end.asm:83FB-858A`
- Evidence: Candidate path includes mode gating, async flag handling, zero command, async accumulation, sync BPW normalization, low-BPW offset/min clamp, normal TBI `$3FCE` write, CPI/PFI delay branch, async output helper, and port-D strobes.
- Requirement: Complete preserved driver range must be bounded before it can supersede compact `$3FCE` bench route.
- Status: `partial_identified`
- Decision impact: `incomplete_continue_3FCE_bench_route`
- Notes: Candidate range is useful but not yet proven complete against all callers, modes, first-event, dropout, and timer dependencies.

### FUEL-STOCK-PROOF-002 — normal fuel hardware-facing writes inside candidate range

- Category: `hardware_writes`
- Source reference: `source/31/BMHM_HAC_ORG_7100_to_end.asm:8426,8512,8571,857F,8587`
- Evidence: Candidate path writes `$3FCE` for zero and normal sync BPW, writes `$3FF2` for async PW, and strobes `$3FFC` around async delivery helper behavior.
- Requirement: All hardware-facing writes must be enumerated and owned by the preserved stock driver if accepted.
- Status: `partial_identified`
- Decision impact: `incomplete_continue_3FCE_bench_route`
- Notes: Output writes are identified for the candidate slice, but downstream timer/interrupt support and side effects remain unresolved.

### FUEL-STOCK-PROOF-003 — output cycling `$3FCE` writes

- Category: `excluded_path`
- Source reference: `source/31/BMHM_HAC_ORG_7100_to_end.asm:FAEE,FB44`
- Evidence: Output-cycling/test path writes `#197` to `$3FCE` for 3 ms pulses and later writes zero to `$3FCE` while toggling I/O state.
- Requirement: Production preserved fuel driver proof must exclude output-cycling/test behavior from engine-runnable fuel authority.
- Status: `identified_excluded`
- Decision impact: `no_acceptance_by_itself`
- Notes: This path can help bench understanding but is not a production fuel scheduler/output driver route.

### FUEL-STOCK-PROOF-004 — stock-compatible fuel state inputs

- Category: `required_inputs`
- Source reference: `source/31/BMHM_HAC_ORG_7100_to_end.asm:83FB-858A; docs/contracts/FUEL_STOCK_OUTPUT_DRIVER_PRESERVATION_CONTRACT.md`
- Evidence: Candidate path depends on sync BPW, async BPW, BPW bias, async flags, short-BPW flag, mode bytes, idle flag, MAP/RPM thresholds, current MAP, RPM/25, last REF period, min/max constants, and major-loop segment state.
- Requirement: Clean OS must prove it can seed every required stock-compatible input before entering preserved driver.
- Status: `incomplete`
- Decision impact: `incomplete_continue_3FCE_bench_route`
- Notes: Input list is not yet complete enough to mark stock driver preservation accepted.

### FUEL-STOCK-PROOF-005 — TOC4/TOC5/TIC4 timer support dependencies

- Category: `scheduler_timer_dependencies`
- Source reference: `docs/contracts/FUEL_SCHED_TIMER_CONTRACT.md`
- Evidence: Existing timer contract says `FUEL_SCHED_TIMER` is not the final EFI PW handoff; it schedules/services TOC4/TOC5 events and should be reproduced only if `$3FCE` alone is insufficient.
- Requirement: Static proof must decide whether preserved stock fuel driver requires timer service path or whether compact `$3FCE` remains sufficient.
- Status: `unresolved`
- Decision impact: `incomplete_continue_3FCE_bench_route`
- Notes: This unresolved dependency prevents fuel stock-driver preservation from superseding the compact bench route.

### FUEL-STOCK-PROOF-006 — fuel no-pulse / clear / dropout behavior

- Category: `enable_disable_dropout_paths`
- Source reference: `source/31/BMHM_HAC_ORG_7100_to_end.asm:8424-8429,8469-84BC,84F8-8515,FB39-FB47`
- Evidence: Candidate path contains commanded zero, async flag clear, async state reset, zero-BPW branch, and output-cycling zero path; true dropout/unsafe zero behavior is not yet proven as a preserved production path.
- Requirement: Accepted stock driver route must statically prove safe reset/first-event/dropout zero state or keep FUEL-004 active under compact route.
- Status: `incomplete`
- Decision impact: `incomplete_continue_3FCE_bench_route`
- Notes: Commanded zero and dropout/unsafe zero remain distinct proofs.

### FUEL-STOCK-PROOF-007 — no alternate custom fuel writer

- Category: `direct_writer_exclusion`
- Source reference: `repo policy contracts`
- Evidence: Static proof index does not create runtime ASM and does not install a custom `$3FCE` writer.
- Requirement: No direct custom fuel ASIC/`$3FCE` writer may supersede stock driver preservation without `FUEL-001` through `FUEL-004` bench proof.
- Status: `pass_for_this_artifact`
- Decision impact: `no_route_change`
- Notes: This artifact is a proof index only.

### FUEL-STOCK-DECISION — fuel stock driver preservation decision

- Category: `route_decision`
- Source reference: `this proof index`
- Evidence: Candidate stock fuel output-driver range and several writes/dependencies are identified, but complete static preservation proof is not yet present.
- Requirement: Decision must be one of `accepted_static_route`, `incomplete_continue_3FCE_bench_route`, `rejected_3FCE_bench_route_required`.
- Status: `incomplete_continue_3FCE_bench_route`
- Decision impact: `active_route_unchanged`
- Notes: Active fuel route remains compact `$3FCE` SLICE-0 bench path. `FUEL-001` through `FUEL-004` still gate SLICE-1 under active route.

## Accepted decision values

```text
fuel_stock_driver_preservation:
  accepted_static_route

fuel_stock_driver_preservation:
  incomplete_continue_3FCE_bench_route

fuel_stock_driver_preservation:
  rejected_3FCE_bench_route_required
```

## Locked interpretation

```text
Fuel preservation contract exists
≠ fuel preservation proof is complete
≠ compact $3FCE bench gate is bypassed
```

Until this proof index is upgraded to `accepted_static_route`, the compact `$3FCE` bench route remains the active route and `FUEL-001` through `FUEL-004` still gate SLICE-1.
