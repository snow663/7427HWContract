# Truck-First Runtime Decoding Workflow

## Current project posture

The replacement-OS effort is intentionally not the primary active workstream.

The active target is the calibration and stock `$31` runtime behavior in the truck as it exists now:

```text
PCM: 16197427
mask: $31
engine: L19 7.4L TBI
current tuning baseline: numbered tune set, literal 2.bin when referenced as Bin 2
```

Replacement-OS progress may still occur opportunistically whenever truck-focused reverse engineering resolves reusable hardware, algorithm, state-machine, telemetry, or command-interface behavior.

## Standing capture rule

Any materially decoded stock behavior discovered during truck diagnosis/tuning is to be captured in the repository automatically as part of the same workstream.

Decoded findings include, for example:

```text
algorithm ordering
RAM-variable semantics
calibration-address/table geometry
fixed-point scales
state-machine qualification
ALDL field semantics
spark/fuel/IAC/knock logic
ASIC command handoffs
transient-fuel behavior
closed-loop learning behavior
mode substitutions and clamps
bench-confirmed hardware behavior
```

Do not promote uncertain interpretation to proven fact. Every captured item should use the strongest appropriate classification:

```text
CONFIRMED STATIC
CALIBRATION-BYTE VERIFIED
REPLAY VALIDATED
BENCH VALIDATED
INFERRED / PENDING VALIDATION
SUPERSEDED
```

## Active decoded contracts

```text
docs/contracts/SPARK_ALDL_KR_ORDERING_CONTRACT.md
docs/contracts/SPARK_UPSTREAM_MODIFIER_CONTRACT.md
docs/contracts/FUEL_CALCULATION_TRACE_CONTRACT.md
```

These contracts are intended to support road-log reconstruction: when the truck does something undesirable, the goal is to trace the observed behavior through the actual stock algorithm and identify which table, correction, state machine, learned term, transient path, or hardware command caused it.

## Repository workflow

New truck-runtime decoding work should accumulate on the ongoing working branch:

```text
docs/truck-runtime-decoding
```

Periodic audit/consolidation can fold proven findings into `main` and remove or supersede stale interpretations.

The branch is not a substitute for proof discipline; it is the durable notebook for active decoded results between consolidation passes.
