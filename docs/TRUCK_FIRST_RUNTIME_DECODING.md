# Truck-First Runtime Decoding Workflow

## Current project posture

The active target is the calibration and stock `$31` runtime behavior in the truck as it exists now.

```text
PCM:                 16197427
mask:                $31
engine:              L19 7.4L TBI
current running BIN: 2.bin
2.bin SHA-256:       2387d708c8d4cc82b78fabda579e48b7daef79f331543a54b669b70b6262877e
```

`2.bin` is the current running calibration, not merely a comparison/reference tune.

Use the authority split:

```text
source/31/BMHM_HAC_ORG_7100_to_end.asm
    = stock algorithm / ordering / RAM-dataflow / hardware-interface authority

current running 2.bin
    = current calibration-byte / table / threshold authority for the truck
```

The replacement-OS effort remains preserved but is not the primary active workstream. It may advance opportunistically whenever truck-focused reverse engineering resolves reusable hardware, algorithm, state-machine, telemetry, scheduler, or command-interface behavior.

## Standing capture rule

Any materially decoded stock behavior discovered during truck diagnosis/tuning is to be captured in the repository as part of the same workstream.

Decoded findings include, for example:

```text
algorithm ordering
RAM-variable semantics
calibration-address/table geometry
fixed-point scales
state-machine qualification
ALDL field semantics and serialization timing
spark/fuel/IAC/knock logic
ASIC command handoffs
transient-fuel behavior
closed-loop learning behavior
mode substitutions and clamps
bench-confirmed hardware behavior
```

Do not promote uncertain interpretation to proven fact. Use the strongest appropriate classification, for example:

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
docs/contracts/ALDL_SERIALIZATION_TIMING_CONTRACT.md
docs/contracts/FUEL_CALCULATION_TRACE_CONTRACT.md
```

These contracts support road-log reconstruction: when the truck does something undesirable, trace the observed behavior through the actual stock algorithm and identify which table, correction, state machine, learned term, transient path, telemetry timing artifact, or hardware command caused it.

## Current ALDL causality rule

`$31` 8192-baud ALDL is serialized from live RAM; a host row is not one simultaneous snapshot.

Therefore apparent row ordering alone must not be used to prove exact internal event ordering during fast changes.

In particular, the later transport reassessment supersedes the earlier claim that the displayed next-row 255-mph VSS value proved the VSS transition occurred after the BPW drop internally:

```text
docs/investigations/VSS_FUELING_TRANSPORT_REASSESSMENT_2026-08-20.md
```

The earlier BPW-drop investigation remains useful for its static/log correlation of MAP, BLM-cell, BLM and INT changes, but its row-order timing inference is historical/superseded.

## Current VSS policy for this truck

The current running `2.bin` has active VSS consumers, and there is no globally neutral fake VSS value.

Preferred engine-control architecture for the current manual/cable-speedometer truck:

```text
VSS acquisition / optional logging may remain
                  |
                  X no required engine authority
                  |
engine control uses validated engine-state inputs
```

Neutralize inappropriate VSS engine consumers individually rather than forcing the global VSS state to `0` or `255`.

Authority:

```text
docs/investigations/BIN2_VSS_AUTHORITY_AUDIT_2026-08-20.md
maps/analysis/bin2_vss_consumer_audit.csv
```

## Repository workflow

New truck-runtime decoding work should accumulate as durable contracts/investigations/maps with stable filenames.

Current live project/workstream authority is:

```text
docs/WORKING_STATE.md
```

Historical branch/audit documents do not override that file.

The repository is the durable notebook for decoded results; Git history is the version record.