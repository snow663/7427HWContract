# Working state

This is the single live project-state index for 7427HWContract. Detailed
contracts and historical proofs are linked rather than repeated here.

## Active direction

The active replacement-firmware source is [pseudo-source/](../pseudo-source/README.md).
Each logical public routine has its own file. We retain the factory-style
reference-event work, periodic fast service, 160-phase counter, 16 slow slots
and one-bit busy/pending catch-up strategy. Algorithms, feature selection and
calibration/executable partitioning can be ours within physical constraints.

The source currently has 290 public routines: 155 implemented outlines,
26 explicit dependency boundaries and 109 implemented algorithms.
Host compilation and kernel tests do not establish a target ABI, target
memory fit or hardware execution. Unfinished tasks return UNIMPLEMENTED;
missing I/O returns NO_HARDWARE. Controller bodies, reset/interrupt assembly,
real driver backend and target BIN build remain unfinished.

Reset CPU/chip-select/board writes, output initialization and the REF
TCNT/OC1/strobe/pending prefix now have checked C implementations. The early
reset assembly precondition remains explicit. The resident REF event body and
its crank/running, enrichment, filter, asynchronous-output and timer helpers are
now C implementations. See the
[REF event contract](../pseudo-source/reference/ref_event_contract.md).
The OC1 counter observer is also implemented, including its baseline, noise/bias
curves and saturating pending-observation accumulator. See the
[OC1 contract](../pseudo-source/reference/oc1_knock_contract.md).
Slot8 now implements knock decay and the mux/ADC sensor diagnostic, and the
normal-spark observation consumer is a checked callable C slice. The broad spark
root now runs the implemented [resident controller](../pseudo-source/reference/spark_controller_contract.md). See the
[knock control contract](../pseudo-source/reference/knock_control_contract.md).
Burst, low-octane learning/scaling and spark gain/cap producers now have checked
C routines. Slot6 directly calls the learner after its explicit AC/switch input
dependency; the other broad slot/controller roots retain their unfinished work.
See the [adaptive spark contract](../pseudo-source/reference/adaptive_spark_contract.md).
Base/environmental terms now form a checked contiguous A700..A84D C body,
with a complete callable MAT/PE/knock auxiliary producer at CA6B..CB14. The
new matrix/filter helpers preserve successive rounding and wrapped stride math.
See the [spark terms contract](../pseudo-source/reference/spark_terms_contract.md).
Idle, transient and decel/recovery corrections now extend the contiguous
composite body through A9DF, with the shared startup/recovery word retained as
one state. See the [modifier contract](../pseudo-source/reference/spark_modifiers_contract.md).
Resident override, signed upper/lower limits and post-limit service edits now
extend command construction through AB43, under the explicit optional 1812
dependency. Both command RAM stores are retained, with no service re-clamp. See
the [command contract](../pseudo-source/reference/spark_command_contract.md).
The A466..A5E4 load/MAP/admission prelude now has checked C routines, with
independent fuel/spark qualification, the resident AC51 alternate path and
a pre-SWI timeout boundary. See the
[admission contract](../pseudo-source/reference/spark_admission_contract.md).
The normal A5E5..A6FF period/RPM and adaptive timing preparation is now
implemented, along with a conditional A466..AB43 builder. The shared word lag
retains the intermediate stores in both REF and normal load filtering. See the
[period/RPM contract](../pseudo-source/reference/spark_period_contract.md).
AB44..ABCA conversion and ordered publication now have C bodies, as does
AC51..ACA6 alternate RPM. A conditional publication wrapper keeps completion
separate from alternate returns and failures. See the
[output contract](../pseudo-source/reference/spark_output_contract.md).
The ABCB..AC50 bypass/fault monitor is now implemented, and both resident
controller/alternate adapters call real C bodies from dispatch. Counter
qualification and fault latches, the 3FEC→3FE4 word handoff, request/service gates
and failed-prefix retention remain explicit. See the
[controller contract](../pseudo-source/reference/spark_controller_contract.md).
Slot7 now directly calls its gear/current/TCC output builder, the recurring
signature probe, the implemented background IAC, the real MAT/PE/knock producer
and an explicit shift-lamp dependency. The former whole-slot binding
is unused. See the [slot7 contract](../pseudo-source/reference/slot7_contract.md).
Background IAC now includes desired RPM, movement/DFCO and AC decay, kicker
state, cold bounds, queued gear/AC transfers and stopped/running snapshot tails.
The new suite matches1,645,037 C/ROM calls across559 instruction starts and137
new source-profile bytes. Both host routes now have54 CTest entries. See the
[background IAC contract](../pseudo-source/reference/iac_background_contract.md).
Partial-mask witnesses also found the simulator's any-bit BRSET implementation.
Direct and both indexed forms now use all-selected-bit semantics;393,216
exhaustive branch vectors, all18 simulator tests (including real-ROM boot/run),
all190 factory tests and the previous C differential suites pass. Historical
factory replay guards retain their original zero/full-mask witness domain.
Slow IAC atA2B0 and its9CFD follower now run from the real slot9 wrapper between
named EGR-demand and VSS-filter dependencies. The port preserves filtered words,
hot-start/DFCO latches, timer expiry, snapshot caps, two-observation faults and
reset admission using the existing0044.4 owner. See the
[slow IAC contract](../pseudo-source/reference/iac_slow_contract.md).
The main93D0 IAC controller now calls separate service/reset/startup, context,
error, integral/P/D, composition and conversion routines. Nonlocal service exits,
retained fractions and software count reconciliation match the stock witnesses.
See the [main IAC contract](../pseudo-source/reference/iac_main_contract.md).
The91A3 IAC step service now runs directly before each busy check, including
busy reentry. It preserves voltage gates, direction reversal, reset phase
admission, ring state and the ordered SEI/shared-shadow/CLI sequence. Catch-up
passes do not add step admissions. See the
[step contract](../pseudo-source/reference/iac_step_contract.md).
Common board I/O and input housekeeping now call resident C bodies. The port
retains the masked word/byte transaction sequence, status/REF shared ownership,
MAP fallback/filter rounding, VSS timestamp polling, brake qualification and the
single-AA watchdog prefix. Real3062 latch writes are included in the kernel
busy/catch-up witness. See the [board/input contract](../pseudo-source/reference/board_io_contract.md).
The current priority is ALDL and system code. The fuel calculation and injector-control
milestone remains tracked below, with its remaining dependency work explicit.
MAP transient selection, raw VSS conversion and environmental precomputation
now have callable checked bodies; their broader fuel/slot4 wrappers stay explicit.
Slot6 AC inputs, slot7 shift-lamp logic and slot9 VSS filtering run resident C.
See the [scheduled input contract](../pseudo-source/reference/scheduled_inputs_contract.md).
The first fuel-milestone batch now implements resident ADC feedback and callable
TPS/MAP/O2 acquisition, slot0 battery and slot2 auxiliary acquisition, battery
state, injector offset and synchronous
finalization/publication. Shared REF/EST/MAP owners, literal masks, short-PW flags
and wrapped offset arithmetic remain explicit. The broad fuel controller and
remaining producer/caller admissions stay unfinished. See the
[fuel input/output contract](../pseudo-source/reference/fuel_input_output_contract.md).
The air/normalization batch now provides callable TPS zero/normalization,
coolant/MAT/BARO acquisition and diagnostics, density, charge temperature, VE
and contiguous VE/base-fuel publication. Shared0232/02F4/02F6 owners and lookup
neighbors remain explicit. See the
[fuel-air contract](../pseudo-source/reference/fuel_air_contract.md).
Callable crank/running authorization, crank preparation/delivery, O2 filtering,
MAP/TPS AE, startup seeding/decay and contiguous commanded AFR/PE now have checked
C bodies. See the [mixture contract](../pseudo-source/reference/fuel_mixture_contract.md).
The O2 controller, closed-loop admission, complete BLM selection/learning tail,
retained-cell helpers and callable EGR/BLM, derivative, BARO/battery and signed
INT/P/MAP corrections now have checked C bodies. See the
[feedback contract](../pseudo-source/reference/fuel_feedback_contract.md).
Cut/decel/recovery, AE reservoirs and sync/async accounting now connect the
admitted7E4F crank/running calculation through852B command publication. See the
[delivery contract](../pseudo-source/reference/fuel_delivery_contract.md).
Broader fuel/slot1/4/D/F roots remain boundaries. Fuel follow-up includes the7D4B ignition/input
prefix and852C scheduled tail, required EGR producers and their slow-slot
admissions/initialization.
Known access widths/order and timing premises remain binding until better
evidence supports a deliberate change. No actuator authority is granted by a host test.

Truck tuning and continued stock-ROM analysis remain supported workstreams.
They use the same evidence with separate calibration/image identities.

## Current tuning candidate

The single manual-idle **Rev B development BIN** is built from the exact supplied
spark/idle Rev A. It integrates the replacement Park/Drive controller,
idle-approach DFCO spark release, removal of the post-fuel spark recovery tail
and an extended cold-idle base-spark shelf. Both maintained non-OEM address
registers now describe Rev B; OEM references remain unchanged. The release
contains separate Rev A rollback and Rev B BIN/XDF pairs. The historical DEV
XDF remains a source-prototype reference, not the new release definition.
See [the image identity and release trace](investigations/MANUAL_IDLE_REVB_RELEASE.md)
and [definitions](../definitions/README.md). The supplied Rev A remains the last
running-image reference; no Rev B flash or truck validation is asserted.

## Tuning simplification trajectory

This is the ordered custom-ROM tuning track agreed on 2026-11-06. Keep its
progress here across conversations. The factory-equivalence ALDL/system and
complete-fuel milestones below retain their own scope; their implemented stock
C routines do not mean these custom-ROM simplifications are complete.

**Software baseline merged; TS00 validation remains active:** the Rev B single manual-idle controller,
idle-approach DFCO spark gate and cold-idle base-spark revision, merged in
[PR #40](https://github.com/snow663/7427HWContract/pull/40), merge commit
`c26cab393eaded71e8233e7dccc7294003e0a5d8`. All four PR checks passed.
The [release trace](investigations/MANUAL_IDLE_REVB_RELEASE.md) records the BIN
identity, matched XDF, rollback and software evidence. Truck validation remains
pending; a source merge is not evidence of a flash or physical calibration.

**Active first: TS00 — test and fine-tune the existing Rev B change.**
The user clarified that this must finish before any later behavior or structural
changes. Await matching Rev B truck logs, identify remaining behavior in this
specific controller/spark revision, and tune its parameters one controlled
change at a time. TS01 and every later step are queued behind this validation;
none is authorized to start ahead of it. An XDF-label review is documentation
and does not authorize editing the firmware or silently changing its calibration.

Record cold start, warm-up (especially the previously troublesome 47–62 C
region), settled hot idle, throttle release/DFCO return and available accessory
loads. Compare actual/requested RPM, spark, IAC, TPS, MAP, coolant, voltage and
fuel-state/trim observations using the matching image and logger definitions.
Keep each tuning revision hash-identified with a matched XDF and rollback.
Close TS00 with observed results, resolved issues, the final tested calibration
and any explicit remaining limitations before selecting TS01.

| Order | Status | Work | Completion evidence |
|---|---|---|---|
| TS00 | Active; awaiting truck evidence | Test and fine-tune the specific Rev B controller, idle spark and DFCO-spark changes already released. | Matching truck logs across cold/warm/hot and idle-return conditions; controlled tuning revisions; documented stability/transition results and final tested BIN/XDF identity. Software checks alone do not complete this step. |
| TS01 | Queued behind TS00 | Shared idle and fuel-mode decisions: centralize RPM/TPS thresholds and hysteresis, with distinct closed-throttle and captured-idle meanings. Coordinate idle approach and DFCO consumers without forcing every consumer to use one flag. | Reviewed producer/consumer map; explicit shared controls and remaining intentional differences; boundary/history tests for crank, idle, off-idle and DFCO, including equality and hysteresis; matched firmware/definition/register updates. |
| TS02 | Queued behind TS00 | Matching ALDL data and ADX: show operating states, requested RPM, baseline air, proportional correction, cold/startup/follower/A/C terms, freeze reasons, fuel enrichment and spark corrections. | Address/width/scaling map for the actual image; paired ADX and any required packet changes; decoded fixture agreement and clear signal names. Record physical capture validation separately. Reuse these channels for later steps. |
| TS03 | Queued behind TS00 | Single VE surface with useful low-RPM resolution, replacing the current idle/open-throttle table handoff and associated reset logic. | Compare both existing surfaces and transition behavior; document the chosen migration and any changed fuel predictions; test interpolation, bounds and transitions; publish matched BIN/XDF and compare relevant logs. Do not assume copying one table preserves both surfaces. |
| TS04 | Queued behind TS00 | Explicit commanded AFR/PE selection, with separately identified warm-up and after-start corrections replacing the layered target-selection/filter/ramp stack. | Trace every surviving target writer and its priority; document cranking, after-start, idle, cruise, PE and DFCO behavior; test transitions, faults and service overrides; log selected target and each correction. |
| TS05 | Queued behind TS00 | Clear injector pulse model across synchronous/asynchronous delivery: voltage offset, short-PW correction, minimum/replacement pulse handling and command limits. Correct inherited short-PW curve/bias labels that misleadingly say Async although the synchronous path also reads them. | Document units, order and actual delivery-path consumers; correct XDF descriptions; test zero/cut, short-PW boundaries, voltage correction, limits and delivery handoffs. Use measured injector evidence for physical correction changes rather than absorbing pulse-model errors into VE. |
| TS06 | Queued behind TS00 | Clear transient-fuel accounting for TPS, MAP, IAC-change and other surviving additions, reservoir accumulation, decay and sync/async delivery. | Explicit ownership, units and timebase for each contribution; bounded accumulation/decay and no double delivery; retained-history tests and separately logged terms; compare tip-in, lift-off and restart behavior. |
| TS07 | Queued behind TS00 | Readable spark-correction accounting: base, coolant, startup, MAT, PE, knock, DFCO and final limits, using the TS02 logging channels. | Reconcile base-to-command timing in fixtures/logs; label signs, units and neutral values; identify the active limit. Simplify only after proving each term's consumers and purpose; preserve knock response and required temperature/command protections. |

Work one trajectory step at a time. Move the selected row to in progress when
implementation starts; leave later rows queued. A step may require several PRs,
but publish a separate matched BIN/XDF checkpoint for each firmware release so
behavior changes can be assessed individually. Before advancing, update this
section with the finished scope, PR/merge, image identity, evidence, remaining
truck checks and the next concrete action. A blocker keeps its step and reason
visible; do not silently skip, renumber or mark it complete.

For the active step, keep this checkpoint current:

- Step/status: TS00, physical testing and fine-tuning active; awaiting matching logs.
- Branch/PR: Rev B source merged in PR #40; trajectory corrections are documentation in PR #41. No later firmware step is in progress.
- Starting image: Rev B, identified in the release trace above.
- Validation: baseline software checks passed; Rev B truck validation pending.
- Required evidence: matching Rev B truck logs and observations; no Rev B physical run is asserted yet.
- Supporting verification: [the XDF label trace](investigations/REVB_XDF_LABEL_VERIFICATION.md) replays 87 Rev B and 15 historical AE instruction fixtures, with supplied BIN/XDF bytes preserved. It does not complete truck validation.
- Next action: assess the first Rev B cold/warm-up/hot-idle and return-to-idle recordings, then fine-tune only this revision's change before considering later simplifications.

Each completed step must distinguish implementation, local checks, CI, merge,
packaging and physical validation. Keep relevant tests and matching XDF/ADX,
maintained non-OEM address/write registers and writer evidence aligned with the
actual released image. Preserve OEM references and the prior rollback pair.
Fuel work must retain the established distinction: BLM is multiplicative;
INT/P contributes a signed additive pulse-width correction. New air/mixture
calibration conclusions require current matching observations; an imposed-RPM
simulation does not establish engine-response stability.

## Current milestone: ALDL and system code

The SCI transport/system batch adds16 routines and replaces the serial poll,
SCI IRQ body and post-controller boot boundaries with resident C. It covers
normal/factory framing, descriptor/command/page selection, raw/live/requested
replies, broadcasts, driver handoff and session/service-duration timing.
A callable boot slice clears0360..03FE; the post-controller stage seeds phase,
BLM, startup counter, COP and the output shadow. See the
[SCI/system contract](../pseudo-source/reference/serial_system_contract.md).

The retained service batch now implements F64E..F780, the distinct F333/F380
diagnostic clears, retained checksum F326 and the ordered F781→F64E tail. AE85
runs that tail after a new explicit dependency for its eight earlier transmission
callees. Accepted commands now reach service admission, BLM/diagnostic edge
processing and cleanup while retaining payload suffixes and existing owners.
See the [service lifecycle contract](../pseudo-source/reference/service_lifecycle_contract.md).

Next extend factory-test admission/recurring execution and the remaining retained
boot/system stages using their ROM contracts. Keep the eight earlier AE85 callees
explicit until their bodies are implemented. Target logical-address binding,
startup/interrupt assembly, stack/cycle bounds and physical SCI behavior remain explicit interfaces.

The second source PR replaces the working-RAM reset boundary with the actual
three clear calls and serial loop. The callable F2FD helper retains count-driven
byte/word ordering, eight-bit block truncation and address wrap. See the
[startup memory contract](../pseudo-source/reference/startup_memory_contract.md).
Initial auxiliary/engine/battery acquisition and factory admission now also run
resident C. The 0050.3 partial latch, independent0001 owner, failed admission
prefix and raw factory timer-phase increment have joined ROM comparisons. See
the [startup sampling contract](../pseudo-source/reference/startup_sensors_contract.md).
The three-PR batch completed on 2026-11-08: service lifecycle
[PR #30](https://github.com/snow663/7427HWContract/pull/30), startup RAM
[PR #45](https://github.com/snow663/7427HWContract/pull/45), and initial sampling/
factory admission [PR #46](https://github.com/snow663/7427HWContract/pull/46)
were merged in that order after each PR's three required CI checks passed.
The checked heads were `14b8d6789c881157e50babe80595d4c9004c9d66`,
`1e933fd8e33656163b669907d19308549a37f643` and
`e8d65701a385b5422502af246f6aefd70a77530e`; each merged tree matched its
checked implementation tree. GitHub PRs retain the merge and workflow evidence.

Local verification passed all 29 quick contracts/provenance checks, the prior
27 complete ROM regression suites and both new startup ROM suites (1,008 memory
and 10,728 sampling/factory cases), 190 factory tests, all 18 simulator tests
including the two real-BMHM tests, repository hygiene and 18 runnable static
builders (33 parameterized builders intentionally skipped). The final source
registers 58 CTest checks. No target BIN or new truck calibration is produced.

Next are retained boot checks/recovery and recurring factory execution; target
control transfers remain explicit. That three-PR group is closed. Subsequent
work follows the single-branch accumulation and explicit release instruction
below; the previous three-PR cadence is superseded.

## Tracked milestone: complete fuel calculation and injector control

The goal is a connected, ROM-checked C fuel path from acquired inputs and retained
state through pulse construction, synchronous/asynchronous arbitration and ordered
injector-command writes. Complete the fuel-dependent acquisition and producer work
alongside it. Batch related routines per PR. Publish after local verification;
report GitHub CI as pending and check its results before a later merge. This is
a tracked milestone; ALDL and system code are the current implementation priority.

The current implementation already includes the base equation at 7FD8..802F,
the REF crank/running/decay/common routines, crank event gain, asynchronous output
at 8548..858A, and their timer helpers. MAP filtering/transient selection, RPM/load,
VSS and environmental slices also have checked bodies. These are building blocks:
`pcm_fuel_control` at 7D4B remains an explicit task boundary. The first
fuel batch replaced `pcm_adc_feedback` and slot0/2 task boundaries with resident C. The documented upstream and closed-loop/learning contracts now also have the
callable C stages listed above. Cut/decel/AE-reservoir and sync/async accounting now also have connected C bodies.
Full caller admissions, scheduled tail and required producer wiring remain work.

| Batch | Related implementation work | Joined evidence required |
|---|---|---|
| Acquisition and injector finalization (implemented slices) | Resident ADC/averaging path at 7B6D/F245; battery acquisition and 8613 ignition-state handling; E2FB..E303 injector offset; 84BC..852B final synchronous shaping/output; join the existing async helper | Real input/output transactions, timeout and failed prefixes, short-PW boundary, wrapped offset addition, final limit, zero output and retained state on async bypass |
| Air charge and fuel input producers (implemented normalization/air slices) | TPS acquisition/zero normalization, BARO, CTS/MAT, density/charge temperature, VE selection; connect existing base arithmetic and environmental/RPM/VSS producers | Producer/consumer state age, lookup neighbors, diagnostic substitutions, scaling, rounding and old-state feedback; complete fuel-required EGR demand/feedback/control/flow/output dependencies as encountered |
| Fuel modes, commanded AFR and enrichment (callable calculation/reservoir slices implemented) | Startup and crank equation; open-loop/idle AFR, PE and transitions; MAP/TPS/IAC-related AE gains, histories and reservoirs | Cold/hot crank through REF delivery, startup-to-running changes, OL idle and PE admission/exit, retained histories and phase-gated updates |
| Running corrections and closed-loop learning (callable correction/learning slices implemented) | 8032..83AE EGR/BLM, cut/decel/recovery, RPM/BARO/battery, signed INT/P and MAP AE; O2 filtering/activity/I/P at 863D..891D, AFR/BLM at 891E..8EB3, and slot-F admission producers | BLM saturated doubling versus signed additive INT/P; cut/recovery priority; learning/cell reset/persistence; O2 activity and distinct admission/learning gates |
| Delivery accounting and controller integration (accounting and7E4F..852B implemented; broad callers pending) | 83B1..84BB sync/async routing, packet/reservoir accounting and shared-state joins; replace the 7D4B fuel task binding; connect fuel-required scheduled producers and initialization | Full running calculation through 3FCE and 3FF2/3FFC command sequences, REF interleavings, timer routes, busy/catch-up admissions and failure-prefix retention without fuel task stubs |

The batches describe dependency groups, not a claim that each fits one PR. Move
supporting producers forward when a consumer needs them; preserve one public
routine per source file. Use the actual stock BMHM bytes and the existing
[upstream fuel](analysis/FACTORY_UPSTREAM_FUEL_CALCULATIONS.md),
[closed-loop/learning](analysis/FACTORY_CLOSED_LOOP_AND_LEARNING.md),
[integer handoff](analysis/FACTORY_FUEL_INTEGER_HANDOFF.md) and
[REF delivery](../pseudo-source/reference/ref_event_contract.md) contracts.
Existing factory documentation does not replace compiled-C/ROM comparisons.

Completion requires all of the following:

- Resident C fuel bodies and required input producers run without substituted fuel
  task bindings. Keep unfinished unrelated slot work explicit while connecting the
  fuel producers at their actual admissions; do not skip a required caller prefix.
- Compare the complete running calculation through command publication with the ROM,
  then join it with the crank/running REF paths. Preserve saturation, wrapping,
  fractions, mask ordering, shared owners and each failed transaction's committed prefix.
- Exercise cold/hot crank, startup, warm OL idle, CL cruise/learning, PE, transient
  sync/async fuel, short pulses, cut/decel/recovery, ignition-off and sensor faults.
  Include retained multi-call histories, scheduler phase/state age and selected REF
  interleavings, in addition to direct arithmetic boundary sweeps.
- Keep all existing quick contracts and ROM suites passing. Record new instruction,
  calibration and joined-call coverage with its limits rather than treating test
  counts as whole-firmware equivalence.

The host milestone establishes software calculation and command ordering. Target
startup/interrupt assembly, backend, ABI/memory fit, cycle/stack bounds and physical
injector/ASIC timing and delivered fuel require their own validation. Guarded
optional-module calls remain explicit dependencies when admitted. Truck calibration
changes require the exact current image and matching logs; stock BMHM comparisons
do not establish the current tune's calibration values.

## Current truck image

The last supplied running reference is **0.3.12 engine-only spark/idle Rev A**,
SHA-256 `d771e824686d086986ee0bdef37697bfc63274071a13b79fc4ba59746644923e`.
The earlier serial probe has a separate identity. Rev B is now the prepared
candidate, with no flash asserted. The maintained registers follow that
candidate; use the Rev A rollback pair when analyzing the earlier logs.

The older `2.bin`, SHA-256
`2387d708c8d4cc82b78fabda579e48b7daef79f331543a54b669b70b6262877e`,
is a historical calibration snapshot. Its byte values, logs and VSS conclusions
apply to that snapshot. Revalidate against the current normal tune before
using them for tuning changes. See [runtime workflow](TRUCK_FIRST_RUNTIME_DECODING.md).

## Factory authority

Stock BMHM SHA-256:

```text
6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
```

Actual bytes and ROM-checked instruction/table evidence outrank conflicting
raw HAC labels or source-only inventories. The original listing is preserved
under [source/31](../source/README.md). CPU 4000..FFFF is committed mapped ROM;
file 0000..3FFF padding is not runtime low memory. F1-style register identities
are conditional CPU-layout interpretations, not a claim about package markings
or every physical board connection.

## Current contracts

| Subject | Current reference |
|---|---|
| Engine air/fuel/spark calculations | [Engine closure](analysis/FACTORY_ENGINE_CALCULATION_CLOSURE.md) |
| Idle, RPM/VSS and governor | [Idle/speed closure](analysis/FACTORY_IDLE_SPEED_CONTROL_CLOSURE.md) |
| Diagnostics, transmission, emissions | [DTE closure](analysis/FACTORY_DIAGNOSTICS_TRANSMISSION_EMISSIONS_CLOSURE.md) |
| Serial, service and factory test | [Serial closure](analysis/FACTORY_SERIAL_SERVICE_CLOSURE.md) |
| Rooted structure and ownership | [Structure](analysis/FACTORY_GLOBAL_STRUCTURE_AUDIT.md), [ownership](analysis/FACTORY_OWNERSHIP_CLOSURE.md) |
| Physical interface boundaries | [Hardware](analysis/FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md), [memory/decode](analysis/FACTORY_EXTENSION_MEMORY_INTERFACE.md) |
| Joined IRQ/timing/stack premises | [Timing closure](analysis/FACTORY_INTERRUPT_AND_TIMING_CLOSURE.md) |
| Joined service/mode/optional behavior | [State transitions](analysis/FACTORY_JOINED_STATE_AND_OPTIONAL_BEHAVIOR.md) |
| Remaining information | [Ledger](analysis/FACTORY_EQUIVALENCE_INFORMATION_GAPS.md) |

These are scoped contracts. Rooted byte counts or passing selected witnesses
are not a whole-firmware completion percentage.

## Findings carried forward

- BLM is multiplicative around 128. INT/proportional correction reaches fuel
  as a separately encoded signed additive term, not another percentage.
- ALDL fields are read during serialization; a displayed row is not an atomic
  controller snapshot. Spark/KR interpretation also retains upstream modifier
  and field-age context.
- Ordinary AE85 calls F781 then F64E consecutively. Actual service comparison
  words are 51BB=FFFF and 51BD=0000. Idle expiry can rearm a held engine-clear
  edge before final cleanup. Earlier adjacent-word values are superseded.
- Only REF, OC1, OC3 and SCI are locally live in stock BMHM. Timing/stack bounds
  retain stated input, frame, device and board premises.
- The user supplied one valid all-zero CPU 1800..1817 readback from the temporary
  probe. See [record](../pseudo-source/reference/1800_readback.md). It establishes
  an absent 7E18 signature in that sample, not memory backing or writability.
  The optional module/loader is excluded from the initial new-firmware scope.

## Verification and remaining work

The current factory suite has 190 tests. The C source checks cover six kernel
contract groups, one-public-routine-per-file provenance, and 532 compiled-C
base-fuel cases against actual stock instructions. Another 128 startup and 4,112
REF cases compare ordered C/ROM transactions and pending state; 64 injected I/O
failures check prefix exits. The complete REF adds 2,502 handler cases, 143 I/O
failure comparisons, 38 direct timer-entry cases and 293 verified calibration bytes.
All 423 scoped instruction starts are exercised; two guards need direct driver
entry because the complete-handler producer limits their input. This is coverage,
not all-state equivalence. OC1 adds 261,632 numeric cases, 16 failure prefixes and
1,280 REF/OC1 sequences, covering all 34 handler instructions and 128 table bytes.
Knock control adds 283,023 comparisons across decay, normal KR, acquisition,
failure prefixes and selected producer/consumer histories. All 121 scoped
instruction starts execute; 24 new calibration bytes and the shared diagnostic
enable match stock. Adaptive spark adds 480,560 comparisons and covers all 201
scoped instruction starts plus 83 new calibration bytes. The source check suite
now has forty-four CTest entries. Base/environmental spark adds 753,561 comparisons,
all 336 scoped instruction starts and 1,035 new distinct calibration bytes.
Modifiers add 225,622 comparisons, all 234 scoped instruction starts and 38 new
calibration bytes, with 43 prior/shared bytes checked again. Command construction
adds 356,872 comparisons across all 137 scoped instruction starts and 27 checked
calibration bytes (17 new, 10 prior/shared), including explicit 1812 boundaries.
Admission adds 620,169 comparisons across
155 pre-trap instruction starts and 14 new calibration bytes; actual SWI/trap
execution remains outside the host routine. Period/RPM work adds 699,057
comparisons across 163 scoped instructions and four calibration bytes (three
new, one shared), including full-builder histories and 660 failure prefixes.
Output/alternate work adds 603,682 comparisons across 104 instruction starts
and 15 new latency bytes, including 1,174 failure prefixes. The monitor/controller
suite adds 468,978 comparisons across all 50 monitor/cleanup instruction starts,
three new calibration bytes, 2,894 failure prefixes and 512 history calls. The
full root and both real dispatcher adapters run without their former task bindings.
Slot7 adds400,081 comparisons across43 output/probe/wrapper instruction starts,
945 failure prefixes and256 history steps. Its256-byte raw gear-index view and
shared400F option match stock; that view includes neighboring code/data rather
than claiming256 separate calibration parameters.
Background IAC adds1,645,037 comparisons across559 desired/helper/background
instruction starts, with137 new source-profile bytes,333 failure prefixes and
512 retained-state calls. Slot7 and subsequent normal spark use the real body
in the new suite; the prior slot7 suite alone retains a test-only boundary.
Slow IAC adds 749,466 comparisons across348 scoped instruction starts and
86 new profile bytes, retaining explicit EGR/VSS dependencies. Main IAC adds
888,333 comparisons across 919 scoped instruction starts. Step service adds
376,456 comparisons across 48 instruction starts. Board/input service adds
803,504 comparisons across 141 instruction starts, 7,971 selected failure
prefixes, 1,024 retained history calls and 11 checked source-profile bytes.
The six-group scheduled input batch adds1,603,654 comparisons across384 scoped
instruction starts,185 checked profile bytes,678 selected failure prefixes and
1,024 retained histories. Earlier slice suites retain explicitly isolated historical
input/lamp/VSS fixtures; the current kernel and combined suite link resident bodies.
The fuel input/output batch adds370,428 comparisons across all181 scoped
instruction starts,22 new profile bytes,2,600 selected failure prefixes and1,024
retained history calls. Resident ADC feedback also runs in the kernel phase and
busy/catch-up witnesses without its former task binding.
The fuel-air suite contains1,015,696 comparisons across336 scoped instruction
starts,930 distinct checked profile bytes and1,581 expanded fixture-view bytes.
It includes1,953 selected failure prefixes,1,024 retained histories and explicit
BARO/counter-wrap admissions in addition to the complete arithmetic sweeps.
The mixture suite adds476,821 comparisons across742 reachable instruction starts,
with two defensive guards bounded by arithmetic invariants,540 distinct profile
bytes,3,087 expanded fixture bytes,553 selected failure prefixes and1,024 retained
startup/AE/AFR/PE/REF history calls.
The feedback suite adds927,344 comparisons across all750 scoped instruction
starts,312 distinct profile bytes,1,054 expanded fixture bytes,377 selected
failure prefixes and1,024 retained O2/BLM/correction/REF history calls.
The delivery suite adds665,548 comparisons across368 reachable scoped starts
with one arithmetic-bounded guard,85 distinct profile bytes,17 expanded curve
bytes,1,343 selected failure prefixes and1,024 retained calculation/delivery/REF
history calls.
The SCI/system suite adds309,610 comparisons across all385 scoped instruction
starts (target RTI excluded),431 selected failure prefixes and256 retained
histories. Its full logical-address sweep includes130,667 normal/factory
selections outside private HC11 call-stack bytes. A coherent test provider binds
canonical state; the real address-space/backend and F64E service lifecycle remain
explicit work. Final duration sampling has24 callback and1,440 boundary checks.
The retained service suite adds80,142 comparisons across all198 scoped starts,
1,434 selected failure prefixes and256 retained histories. Packet/service/spark
joins, nonzero prior-output cleanup and all solenoid enable/value pairs are
included. Expanded data tracing also restored the second TX descriptor-format
read;432 mutation cases and44,799 transport regressions pass.
CI gates on the 27 quick contracts/provenance tests before the 27 ROM suites.
Independent comparisons run two at a time, with the longest suites scheduled first.
The simulator has 18 CPU/GUI/real-ROM tests and its
CI matrix on Python3.10/3.11/3.12.

EQ-11 retains additional joined state combinations. EQ-12/13 cover physical
device/board evidence; EQ-14 covers actual optional-module/external-caller code.
We can continue the C source while preserving those explicit interfaces.

## Delivery workflow

As requested on 2026-11-08, accumulate several substantial routine groups as
separate commits on one development branch. The full suite is expensive; give
each run a larger body of completed source to validate. There is no fixed
three-PR or three-commit batch size. Retain one public routine per source file
and keep implementation, provenance, focused test cases and documentation
aligned as the branch advances.

Use compilation and focused contract/ROM comparisons where needed to catch
problems in the changed routines during development. Do not open a PR, launch
the complete regression suite or merge automatically after an ordinary update
or a request to continue. Ordinary development-branch pushes do not trigger the
current full CI workflow; a PR does.

When the user says **"pull and merge"**, prepare one PR for the accumulated
branch changes, run the full suite and required repository checks against its
final head, resolve any failures, and merge after the checks pass. That phrase
provides authorization to complete the release; another confirmation is not
required. Record the checked head, validation, merge, remaining work and next
action in this working state. Resume later development on one branch from the
resulting main rather than creating a PR for each routine group. The previous
three-PR cadence and older per-update publication guidance are superseded.

Active development branch: `work/pseudo-source-development`, starting from
`b2d851d81eb7a3843b9153309de1e2ff7dc40c02`. No new PR or full-suite run is
requested yet. Next implementation work is retained boot checks/recovery and
recurring factory execution. The previously completed group #30/#45/#46 remains
historical validation evidence.

## Historical material

Earlier assembly and minimal-slice proofs remain under [source/](../source/README.md).
Their old next-step language and unimplemented declarations are interpreted
within that prototype. Frozen V1 plans and dated `2.bin` investigations do not
override the current C design or current-tune image identity.
Git history is the version record; no parallel live-state document is created.
[Repository audit](REPOSITORY_AUDIT.md) records the cleanup and retained evidence.
