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

The current requested task is factory-code reverse-engineering documentation. The upstream engine-calculation documentation is complete within `docs/analysis/FACTORY_ENGINE_CALCULATION_CLOSURE.md`; resident IAC/RPM/VSS/governor documentation is now also completed in `docs/analysis/FACTORY_IDLE_SPEED_CONTROL_CLOSURE.md`. Diagnostics, transmission and emissions are documented in `docs/analysis/FACTORY_DIAGNOSTICS_TRANSMISSION_EMISSIONS_CLOSURE.md`. Full SCI/ALDL, normal service and manufacturing test are documented in `docs/analysis/FACTORY_SERIAL_SERVICE_CLOSURE.md`. `docs/analysis/FACTORY_GLOBAL_STRUCTURE_AUDIT.md` supplies the vector-rooted ROM map. `docs/analysis/FACTORY_OWNERSHIP_CLOSURE.md` now connects all951 rooted indexed-address contracts, writing-helper caller bindings, global byte/bit co-writers and scheduler/service flag lifetimes. Actual external-code implementations/callers, full flag/concurrency proofs and physical observations retain explicit evidence boundaries. Simulator development and tuning changes are not required for these documentation closures.

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

Factory-code structure and exact stock-state tracing are also active analysis tasks. The first reviewed-data pass excludes `$C2D6-$C409` from the dispatcher/write-target inventories and adds direct read/write, control-reference, and entry-point indexes under `maps/structure/`.

Method, current structural findings, and the ordered investigation queue:

```text
docs/analysis/FACTORY_CODE_STRUCTURE.md
maps/structure/factory_re_worklist.csv
```

The first additional state trace is `docs/contracts/SPARK_L01EC_INTEGER_STATE.md`. Structural enumeration is separate from semantic understanding, binary verification, or runtime proof; these outputs establish no whole-ROM completion percentage.

The `$C2D6-$C409` descriptor bytes and principal caller/reader instructions are verified against actual `BMHM.BIN` bytes with the stock SHA-256 above. The byte evidence and144 pointer words are recorded in `docs/analysis/FACTORY_ROM_STRUCTURE_PROOF.md`. The newer global structure audit also confirms that no vector-rooted control path enters that block; arbitrary callbacks/extensions remain separate.

The main TOC3 scheduler now has a ROM-backed slot/call/guard/state map in
`docs/analysis/FACTORY_SCHEDULER_MAP.md` and `maps/structure/factory_scheduler_*.csv`.
It covers all 16 landing words, phase-bit fast groups, first-slot initialization,
stack checks, the coalescing pending-pass bit, profiling words, and the separate
RAM-word factory/service callback. Eighteen bounded CPU-execution tests cover
the full 160-phase sequence and exceptional paths with external callee effects
stubbed. Sixty-three direct callee roots have ROM-decoded intraprocedural state
inventories; their later nested extension is described below. Thirty-two listing
discrepancies are recorded, including executable entries hidden by HAC data or
misaligned decoding. These byte maps take precedence for covered instructions;
the original HAC is retained unchanged. The main indexes now apply the reviewed byte overlay described below.

Nested-call/indexed-state propagation now extends those roots to 234 ROM
procedure entries. `docs/analysis/FACTORY_NESTED_STATE_FLOW.md` and
`maps/structure/factory_nested_*.csv` record register-return expressions,
call-specific memory effects, and opaque boundaries. Of the earlier 262 indexed
rows, 162 now have one address and 54 a bounded address set; six are frame-relative,
four retain caller parameters, eight are pruned by stock constants, and 28 stay
unresolved in that historical finite-analysis baseline. The new global alias
contracts supply their qualified formulas without changing the old denominator
or equating a runtime expression with one physical address. These are scoped
address proofs, not whole-ROM semantic completion.
Indexed clear footprints and 45 ROM-mask/RAM pairings establish additional state
producers, including the `$F333` mask write to `$001A`. The raw branch at `$A40B`
is verified to target `$A465`; the effective indexes now use that target while preserving the original HAC.
The actual-ROM multiply replay also required correcting MUL carry from bit15 to
bit7 in the CPU model, with a dedicated regression.

The reviewed overlay now integrates all 32 scheduler listing discrepancies, the
`$A40B` correction, and the nine `$F3DB-$F3E3` mask bytes into the main indexes
and legacy dispatcher/write consumers. `factory_rom_overlay_audit.csv` retains
the replaced/suppressed rows. Legacy indexed-write addresses now come from the
ROM state-flow proofs; bounded sets, local frames, and unknowns stay explicit.

`docs/analysis/FACTORY_SPARK_INTEGER_HANDOFF.md` closes the bounded normal
`$AB3E-$ABC8` integer handoff and the `$01EA/$083F/$01EC` producers,
initialization, and update admission. Independent CPU replay checks the exact
four writes from raw inputs and separate live readback samples. The old equation
that shifted the combined timing product and period is superseded: the timing
product remains on the stack while a separate negated-period anchor is formed.
The current suite has 103 factory tests and 16 CPU/simulator tests, including the
actual-ROM 100,000-instruction regression. Physical units, ASIC effects,
interrupt interleavings, external extension and monitor code retain separate
boundaries. Running-fuel and resident upstream calculations are completed below.

`docs/analysis/FACTORY_FUEL_INTEGER_HANDOFF.md` now documents the raw running-fuel
calculation at `$7FD8-$852B`, all `$024E` correction/mode branches, synchronous
shaping and `$3FCE`, async packet accounting and `$3FF2/$3FFC`, the INT/P
combination, and the offset lookup. `FUEL_CALCULATION_TRACE_CONTRACT.md` links
that exact derivation and distinguishes the separately recorded `2.bin` values.
The docs preserve division truncation, the BLM double limit, additive INT,
wrapped final offset, persistent packet fractions, and the async bypass that
leaves `$0250` unchanged. ROM bytes and access/dependency/example maps are under
`maps/structure/factory_fuel_*` and `bmhm_fuel_rom_evidence.json`.
The separate crank equation and upstream producers are outside that particular
running slice, and are now documented in the companion contracts below.

`docs/analysis/FACTORY_ENGINE_CALCULATION_CLOSURE.md` closes the named upstream
calculation worklist: MAP/BARO/TPS/coolant and RPM coordinates, density and
charge temperature, both VE table geometries, AFR/PE/startup, MAP/TPS AE and
histories, crank/event gain and local delivery, EGR inputs, O2 I/P, BLM
selection/learning/reset, composite spark, idle/transient/decel modifiers,
knock IRQ/decay/low-octane learning, signed limits and local service overrides.
The three detailed producer documents are:

```text
docs/analysis/FACTORY_UPSTREAM_FUEL_CALCULATIONS.md
docs/analysis/FACTORY_CLOSED_LOOP_AND_LEARNING.md
docs/analysis/FACTORY_UPSTREAM_SPARK_CALCULATIONS.md
```

The new actual-ROM evidence covers 50 blocks, 3,403 decoded instruction starts,
826 branch rows and 54 selected state contracts in `factory_upstream_*.csv` and
`bmhm_upstream_rom_evidence.json`. `tools/verify_factory_upstream.py` checks
full-image identity and recorded regeneration consistency, not a whole-program
semantic coverage percentage or a mechanical proof of every equation.
It records the alternate RPM producer at `$AC51`, the source `$B968` false
writer as lookup-pointer data, and the `$A4F8` **word** clear of `$0260`.
The slot-F bit4 early return and the slower CTS/environment admission are
explicit, so nominal task rates are not mistaken for identical state ages.

The resident IAC and governor controller work is now completed in
`docs/analysis/FACTORY_IDLE_SPEED_CONTROL_CLOSURE.md`, with detailed contracts:

```text
docs/analysis/FACTORY_IAC_CONTROLLER.md
docs/analysis/FACTORY_IAC_LEARNING_AND_OUTPUT.md
docs/analysis/FACTORY_RPM_VSS_GOVERNOR.md
```

This closes desired RPM, integral/P/D/cold-flow control, follower/cracker/kicker,
retained-cell setup and transfers, reset/service exits, phase/enable/output
cadence, both REF RPM-history writers, raw/filtered VSS and timeout, RPM/VSS
fuel limits, governor target/anticipation/actuator I/P, and local diagnostic
and shared-output interactions. Software position0007 is explicitly a count,
not measured pintle position. Reset seeds position255 and target0; low voltage
can hold movement while retaining enable; busy reentry can advance the shadow
without immediately latching it. The earlier source-only IAC notes link to the
new authority and the incorrect reset-zero summary is corrected at its builder.

`bmhm_idle_governor_rom_evidence.json` and `factory_idle_governor_*.csv` cover
45 reviewed spans, 2,876 instruction starts, 816 branch rows, 25 local CFG roots
and 100 selected states. `factory_rpm_vss_consumers.csv` checks 39 direct VSS
readers. The initial pass linked30 calculation paths and left9 peripheral
or diagnostic owners; all39 now link to completed contracts in the DTE pass below. Seventeen covered listing differences are recorded locally,
including missing park snapshot code and shortened branch operands. The global
partial overlay and whole-ROM counts are not silently reclassified by this pass.

The resident diagnostics/transmission/emissions pass is completed in
`docs/analysis/FACTORY_DIAGNOSTICS_TRANSMISSION_EMISSIONS_CLOSURE.md`:

```
docs/analysis/FACTORY_DIAGNOSTICS.md
docs/analysis/FACTORY_TRANSMISSION_CONTROL.md
docs/analysis/FACTORY_EMISSIONS_CONTROL.md
```

It closes local DTC detection/recovery, reaction masks, boot/retained checksums,
log persistence and flash/lamp reporting, masked clears and local service expiry;
range/pattern/speed/TPS/temperature inputs, gear priorities, shift observation,
adaptive cells, pressure/current feedback, both TCC families and transmission
spark requests; and EGR feedback/control, purge adaptation, AIR, catalyst,
manifold and shared AC/output selectors. The post-handoff EST monitor ABCB is
also documented. Reserved flash slots and RTS stubs remain explicitly identified.

The actual-ROM inventory covers62 instruction spans,7,628 instruction starts,
2,027 branch rows,142 local CFG roots,153 selected states,20 priority descriptors
and35 direct pointer arrays. Twelve covered listing differences are recorded
locally. Thirteen new bounded execution tests check descriptor priority, capture
returns, force-current arithmetic, diagnostic persistence/clear/mask behavior,
TCC arithmetic and output/retention branches. This brings factory tests to103;
it is not a whole-program simulation or semantic coverage percentage.

The9 previously open VSS readers now link to named owners, completing the39-site
direct-reader crosswalk. Global indexed-reader completeness remains separate.
Notable literal results include E58C returning a timeout byte while its saved
speed remains held; a selected null descriptor stopping priority search; TCC
signed overflow replacing the full word; and log candidates being intersected
before retention rather than directly copied from every live fault.

The full serial and manufacturing-test work is now documented in
`docs/analysis/FACTORY_SERIAL_SERVICE_CLOSURE.md`, with companion protocol and
service/test contracts. This closes SCI interrupt arbitration, framing/checksum,
device/command/page descriptors, live/requested-memory reads, payload retention,
clear edges, session/duration expiry, factory admission,32-byte upload,
payload-supplied callback and output cycling. Engine reply N=64 includes the
command echo plus63 data bytes. Short payloads can retain old fields; no local
callback-target whitelist or upload destination restriction is invented.

`docs/analysis/FACTORY_GLOBAL_STRUCTURE_AUDIT.md` follows all21 named vector
words, direct control paths and16 scheduler words. It inventories14,523 rooted
instruction starts,34,527 code bytes,951 indexed sites and1,637 directly
referenced memory bytes. No conflicting rooted decodes or code/table collisions
occur. Nine control frontiers remain: eight1800-family extensions and the
arbitrary received callback. The7100..FFFF byte inventory also records2,007
data/tail bytes and74 alternate-candidate bytes, including three JMP shapes
atFF90/FF93/FF96 and the unusedF564 multiply helper. The tail's intended external
ABI is unproven. WAI/STOP continuations are conditional wake/return edges.

The new `factory_global_*` inventories take precedence for rooted instructions
and direct owners; older source/partial-overlay indexes keep their explicitly
historical scope. `FACTORY_OWNERSHIP_CLOSURE.md` now adds qualified address
contracts for all951 indexed PCs,253 procedure contexts,657 call bindings,
1,415 runtime byte-owner rows,3,846 bit-writer rows and12 named gate lifetimes.
All rooted callers of the remaining writing helpers are bound; FABC is the
sole non-frame explicit indexed write with an unrestricted received destination.
0392's indexed O2/service consumers86FD/E49E are now connected to the service
contract.0086.6 has no ordinary resident setter; the independent180C signature
hook remains an external enable/mutation possibility. F1-style CPU register
identities correct older provisional PORTD/OC1/305C..305F labels in the linked
hardware boundary contract. Intended external-entry callers, actual low-memory
code, general flag/interleaving proofs and physical observations remain open.
These counts are structural evidence, not a whole-program semantic percentage.

Primary current contracts include:

```text
docs/analysis/FACTORY_ENGINE_CALCULATION_CLOSURE.md
docs/analysis/FACTORY_IDLE_SPEED_CONTROL_CLOSURE.md
docs/analysis/FACTORY_DIAGNOSTICS_TRANSMISSION_EMISSIONS_CLOSURE.md
docs/analysis/FACTORY_SERIAL_SERVICE_CLOSURE.md
docs/analysis/FACTORY_GLOBAL_STRUCTURE_AUDIT.md
docs/analysis/FACTORY_OWNERSHIP_CLOSURE.md
docs/analysis/FACTORY_GLOBAL_ALIAS_CONTRACT.md
docs/analysis/FACTORY_FLAG_LIFETIMES.md
docs/analysis/FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md
docs/contracts/SPARK_ALDL_KR_ORDERING_CONTRACT.md
docs/contracts/SPARK_UPSTREAM_MODIFIER_CONTRACT.md
docs/contracts/ALDL_SERIALIZATION_TIMING_CONTRACT.md
docs/contracts/FUEL_CALCULATION_TRACE_CONTRACT.md
docs/contracts/SPARK_L01EC_INTEGER_STATE.md
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

The stock running fuel path and its resident upstream air/AFR/AE/O2/BLM producers are documented, together with the separate crank equation and reference-event delivery. Use the engine-calculation closure index for scope, shared math, cadence and the remaining input/controller interfaces.

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
