# Working State

This file is the single live project/workstream authority for `7427HWContract`.

Git history preserves prior states. Files under `docs/closeout/` are historical checkpoints unless this file explicitly promotes one back into current authority.

## Current active truck target

```text
PCM:                 16197427
mask:                $31
engine:              L19 7.4L TBI
current running BIN: 2.bin
2.bin SHA-256:       2387d708c8d4cc82b78fabda579e48b7daef79f331543a54b669b70b6262877e
```

`2.bin` is the calibration-value authority for the truck as it is running now.

When a byte/table/threshold statement is explicitly described as a `2.bin` fact, use the current running `2.bin` value rather than assuming the stock BMHM calibration value.

The numbered tune archive/BIN itself is treated as an external reference artifact identified by filename and SHA-256 unless it is explicitly committed later.

## Stock algorithm/source authority

```text
mask/object:          $31 / BMHM
stock executable ASM: source/31/BMHM_HAC_ORG_7100_to_end.asm
stock reference BIN: BMHM.BIN
stock BIN SHA-256:    6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
processor:            MC68HC11-family
relocated registers:  $3000
```

The stock BMHM/HAC executable is the algorithm, ordering, RAM-dataflow and hardware-interface authority where static proof is being derived.

Do not confuse these two authorities:

```text
stock BMHM/HAC source  -> what the $31 code does
current running 2.bin  -> which calibration values the truck is using now
```

## Active workstream

The active workstream is **truck-first stock-$31 runtime/calibration decoding and tuning**.

Goals:

```text
road-log reconstruction
fuel / VE / PE / AE / BLM diagnosis
spark / knock reconstruction
VSS authority removal for the manual/cable-speedometer truck
ALDL timing/field interpretation
capture of every reusable stock behavior as a durable contract
```

Replacement-OS work remains valid and retained, but it is not the primary active workstream. It advances when truck-focused reverse engineering establishes reusable hardware, algorithm, scheduler, telemetry, state-machine or command-interface behavior.

Workflow authority:

```text
docs/TRUCK_FIRST_RUNTIME_DECODING.md
```

## Current reusable runtime contracts

Primary current contracts include:

```text
docs/contracts/SPARK_ALDL_KR_ORDERING_CONTRACT.md
docs/contracts/SPARK_UPSTREAM_MODIFIER_CONTRACT.md
docs/contracts/ALDL_SERIALIZATION_TIMING_CONTRACT.md
docs/contracts/FUEL_CALCULATION_TRACE_CONTRACT.md
docs/contracts/PRESERVED_OUTPUT_DRIVER_ISLANDS.md
docs/contracts/ALDL_SCI_HANDSHAKE.md
```

Important locked interpretations:

```text
ALDL Spark Advance = post-normal-KR commanded spark
ALDL Knock Retard  = amount removed by normal knock logic
```

Approximate pre-normal-KR demand is therefore:

```text
logged spark + logged KR
```

subject to ALDL serialization skew and upstream modifiers.

`ALDL Spark + KR` is not automatically the raw main-table cell because coolant, PE/WOT, altitude, startup, low-octane adaptive retard and other upstream terms can already be present.

## ALDL serialization rule

`$31` 8192-baud ALDL is not an atomic RAM snapshot. Fields are live-dereferenced as their bytes are serialized.

For the current engine message, VSS is transmitted substantially earlier than BPW. Therefore:

```text
row N:   VSS looks normal, BPW changes
row N+1: VSS displays a glitch
```

**does not prove** BPW changed before the VSS event internally.

Authority:

```text
docs/contracts/ALDL_SERIALIZATION_TIMING_CONTRACT.md
docs/investigations/VSS_FUELING_TRANSPORT_REASSESSMENT_2026-08-20.md
```

The transport reassessment supersedes any earlier investigation wording that inferred exact VSS/BPW internal ordering from host-row order alone.

## Current VSS conclusion for 2.bin

The current running `2.bin` contains real engine-control consumers of raw and filtered VSS.

There is no globally neutral forced VSS value:

```text
VSS = 0   activates/qualifies low-speed/stationary behaviors
VSS = 255 can exercise high-speed/limiter-related behaviors
```

For this manual truck with no trustworthy PCM VSS input, the preferred architecture is:

```text
VSS acquisition / optional telemetry may remain
                |
                X  no required engine authority
                |
engine control uses RPM / MAP / TPS / ECT / O2 / knock / REF / baro etc.
```

Consumer-by-consumer authority audit:

```text
docs/investigations/BIN2_VSS_AUTHORITY_AUDIT_2026-08-20.md
maps/analysis/bin2_vss_consumer_audit.csv
```

The earlier BPW-drop trace remains useful for its BLM/MAP/INT evidence, but its row-order temporal inference is superseded by the ALDL transport reassessment.

## Current fuel-model decoding checkpoint

The stock running fuel path has been traced from speed-density air charge through the final TBI handoff.

Static ordering currently establishes, at minimum:

```text
MAP / charge temperature / displacement / VE
  -> cylinder air charge
  -> commanded-AFR divisor
  -> injector-flow divisor
  -> base synchronous PW
  -> EGR displacement term
  -> BLM
  -> fuel-state / DFCO / cut logic
  -> baro correction
  -> battery PW correction
  -> closed-loop INT/P correction
  -> MAP AE synchronous adder
  -> TBI sync/async arbitration
  -> short-PW shaping
  -> injector opening/deadtime offset
  -> final synchronous command
  -> $3FCE
```

TPS/MAP transient logic can also produce asynchronous fuel through `$3FF2` / `$3FFC bit2`.

Fixed-point external-unit normalization that is not yet proven remains explicitly classified as pending/replay-validation work in the contract rather than guessed.

Authority:

```text
docs/contracts/FUEL_CALCULATION_TRACE_CONTRACT.md
```

## Replacement-OS checkpoint

The replacement-OS work remains preserved and valid.

Long-term modular source authority:

```text
source/replacement_os/7427_rom.asm
source/replacement_os/include/*.inc
source/replacement_os/core/*.asm
source/replacement_os/hal/*.asm
```

Self-contained MiniIDE sources are proof-stage vehicles, not independent long-term implementations.

### Milestone A — bootstrap/vector image: PROVEN BUILD

```text
source:  source/replacement_os/7427_bootstrap_miniide.asm
ASM11:   0 warnings / 0 errors
code:    $7100-$7136
vectors: $FFC0-$FFFF
reset:   $FFFE -> $7100
BIN SHA-256:
c8980013fb2223dfec6e6536f2e9f3815a66a9c555a50ac25989fbfe15b9279e
```

### Milestone B — read-only ADC/REF acquisition image: PROVEN BUILD

```text
source:  source/replacement_os/7427_inputs_miniide.asm
ASM11:   0 warnings / 0 errors
RAM:     $0000-$0009
code:    $7100-$71D7
vectors: $FFC0-$FFFF
reset:   $FFFE -> $7100
BIN SHA-256:
28462ef9dbf3b6f0de59b68662fb26916dc87abea35ff7d67a0d572d42f92848
```

Milestone B does not yet prove meaningful live REF data from `$3FC0` because the stock ASIC/register startup sequence is intentionally absent.

### Milestone C — engine-off ALDL observability: SOURCE READY / UNPROVEN

```text
source: source/replacement_os/7427_aldl_tx_miniide.asm
SCI:    8192 baud
frame:  14-byte raw-input frame
board baseline before ALDL RMW: $3FFC/$3FFD = $B93A
ALDL driver: low byte $3FFD bit2
actuator authority: none
```

Assembly/listing/S19/BIN proof and bench execution remain pending.

## Important hardware contracts retained

```text
$3008 = relocated CPU PORTD / external ADC-mux selector
$3039 = relocated HC11 OPTION register
$3FFC/$3FFD stock BMHM/TBI startup baseline = $B93A
$3FFD bit2 = ALDL external-driver control
$3FFC bit2 = async-fuel-related control
```

Preserved command islands:

```text
fuel synchronous   LOCKED + PORTED
fuel async / AE    LOCKED + PORTED
IAC                LOCKED + PORTED
fuel pump          LOCKED + PORTED
spark / EST        ABI LOCKED; complete rolling-state port pending
MIL                deferred
unused I/O         reserved
```

No observability milestone grants production actuator authority.

## Source-trace artifacts

The project also has a source-derived `$31` HAC trace package generated from the broader raw source, including ORG blocks, labeled data declarations and high-value XDF seed candidates.

Provenance index:

```text
maps/source_trace/README.md
```

The raw source-trace archive is identified by SHA-256 in that file. Source-derived rows are evidence/index material; inherited XDF labels/scales are not treated as authority unless independently verified.

## Experimental utilities

```text
tools/distributor_phasing_sim.py
```

The distributor simulator is a geometry exploration/visualization tool. It is **not** stock `$31` ignition-algorithm authority.

## Authority order

For current work, use:

```text
1. docs/WORKING_STATE.md
2. docs/TRUCK_FIRST_RUNTIME_DECODING.md
3. current docs/contracts/*.md and maps/contracts/*.csv
4. current investigation/reassessment docs, respecting explicit supersession
5. source/31/BMHM_HAC_ORG_7100_to_end.asm for executable proof
6. current running 2.bin for current calibration-byte truth
7. source/replacement_os/* for replacement-OS implementation state
8. frozen V1 planning documents/maps for semantic design requirements
9. docs/closeout/* as historical checkpoints only
```

Frozen semantic planning remains in:

```text
docs/closeout/7427_V1_PLANNING_CONSOLIDATION_AUDIT.md
docs/planning/V1_*.md
maps/planning/*.csv
maps/telemetry/v1_adx_manifest.csv
```

## Current work order

Primary truck-first work:

```text
1. use current running 2.bin as the byte/table baseline for road-log diagnosis
2. remove/neutralize inappropriate VSS engine authority consumer-by-consumer
3. continue exact fuel/spark/knock/transient-state reconstruction from executable + logs
4. capture every proven reusable behavior as a contract/map
5. keep ALDL serialization skew in all fast-event causality analysis
```

Replacement-OS work resumes from the preserved Milestone-C checkpoint whenever that workstream is intentionally selected or when truck-runtime decoding provides a reusable implementation dependency.

## Working rule

Use stable filenames for live authority. Let Git history preserve versions. Keep proof-stage files only where they serve a distinct reproducibility purpose; do not maintain parallel `almost-the-same` authorities.