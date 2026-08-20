# 7427HWContract

Working repository for GM `16197427` (`7427`) `$31` PCM reverse engineering, truck-runtime decoding, tuning support, hardware-contract capture, and replacement-OS development.

`docs/WORKING_STATE.md` is the single live project-state authority.

## Current truck baseline

```text
PCM:                 16197427
mask:                $31
engine:              L19 7.4L TBI
current running BIN: 2.bin
2.bin SHA-256:       2387d708c8d4cc82b78fabda579e48b7daef79f331543a54b669b70b6262877e
```

`2.bin` is the current calibration-value authority for truck behavior and byte-specific tuning analysis.

The stock BMHM/HAC source remains the algorithm/dataflow/hardware-interface authority:

```text
source/31/BMHM_HAC_ORG_7100_to_end.asm
```

Do not substitute stock calibration values for current `2.bin` values when analyzing the running truck.

## Active project posture

The active workstream is truck-first stock `$31` runtime/calibration decoding and tuning.

Current focus includes:

```text
road-log reconstruction
fuel / VE / PE / AE / BLM behavior
spark / knock behavior
VSS authority audit/removal for the manual truck
ALDL field timing and causality
capture of reusable stock behavior as durable contracts
```

Replacement-OS development is preserved at its current checkpoint and advances when intentionally selected or when runtime decoding produces reusable hardware/algorithm contracts.

Workflow authority:

```text
docs/TRUCK_FIRST_RUNTIME_DECODING.md
```

## Current authority order

```text
1. docs/WORKING_STATE.md
2. docs/TRUCK_FIRST_RUNTIME_DECODING.md
3. current docs/contracts/*.md and maps/contracts/*.csv
4. current investigation/reassessment docs, respecting explicit supersession
5. source/31/BMHM_HAC_ORG_7100_to_end.asm
6. current running 2.bin for calibration-byte truth
7. source/replacement_os/* for replacement-OS implementation
8. frozen V1 planning documents/maps
9. docs/closeout/* as historical checkpoints only
```

Git history is the version record. Do not create parallel `almost-the-same` live-state documents.

## Important current runtime contracts

```text
docs/contracts/SPARK_ALDL_KR_ORDERING_CONTRACT.md
docs/contracts/SPARK_UPSTREAM_MODIFIER_CONTRACT.md
docs/contracts/ALDL_SERIALIZATION_TIMING_CONTRACT.md
docs/contracts/FUEL_CALCULATION_TRACE_CONTRACT.md
```

Locked tuning interpretations include:

```text
ALDL Spark Advance = post-normal-KR spark
ALDL Knock Retard  = amount normal knock logic removed
```

and:

```text
ALDL row != one atomic PCM snapshot
```

The `$31` transmitter live-dereferences fields while serializing them, so fast-event causality must account for field-order timing skew.

## Current VSS conclusion

The running `2.bin` contains real fuel/mixture/idle/spark consumers of raw or filtered VSS.

There is no globally neutral forced VSS value. For the manual/cable-speedometer truck, VSS should be removed from required engine authority consumer-by-consumer while optional acquisition/telemetry may remain.

Authority:

```text
docs/investigations/BIN2_VSS_AUTHORITY_AUDIT_2026-08-20.md
docs/investigations/VSS_FUELING_TRANSPORT_REASSESSMENT_2026-08-20.md
maps/analysis/bin2_vss_consumer_audit.csv
```

The transport reassessment supersedes earlier statements that inferred exact internal VSS/BPW ordering from adjacent ALDL rows.

## Replacement-OS checkpoint

Maintainable modular source:

```text
source/replacement_os/7427_rom.asm
source/replacement_os/include/*.inc
source/replacement_os/core/*.asm
source/replacement_os/hal/*.asm
```

Current proof stages:

```text
Milestone A  bootstrap/vectors       PROVEN BUILD
Milestone B  read-only ADC/REF path  PROVEN BUILD; live hardware proof pending
Milestone C  engine-off ALDL         SOURCE READY; assembly/bench proof pending
```

No observability milestone grants production fuel, spark, IAC, pump, or auxiliary-output authority.

## Source-derived calibration/data trace

A broader raw-source trace package is indexed under:

```text
maps/source_trace/README.md
```

It contains source-derived ORG/data/XDF-seed inventory metadata. Source comments and raw declarations are preserved as evidence; unknown scaling remains unknown rather than being guessed.

## Experimental tools

```text
tools/distributor_phasing_sim.py
```

The distributor-phasing simulator is an exploratory geometry tool, not stock `$31` ignition-algorithm authority.

## Historical records

`docs/closeout/` contains prior audits/checkpoints. They remain useful provenance, but their old `next step`, `current state`, or branch-status language does not override `docs/WORKING_STATE.md`.

See:

```text
docs/closeout/README.md
```
