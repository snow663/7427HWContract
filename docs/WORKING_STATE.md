# Working state

This is the single live project-state index for 7427HWContract. Detailed
contracts and historical proofs are linked rather than repeated here.

## Active direction

The active replacement-firmware source is [pseudo-source/](../pseudo-source/README.md).
Each logical public routine has its own file. We retain the factory-style
reference-event work, periodic fast service, 160-phase counter, 16 slow slots
and one-bit busy/pending catch-up strategy. Algorithms, feature selection and
calibration/executable partitioning can be ours within physical constraints.

The source currently has 172 public routines: 76 implemented outlines,
40 explicit dependency boundaries and fifty-six implemented algorithms.
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
new source-profile bytes. Both host routes now have34 CTest entries. See the
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
Next is91A3 step service, alongside remaining scheduled producers and
reset/backend work.
Known access widths/order and timing premises remain binding until better
evidence supports a deliberate change. No actuator authority is granted by a host test.

Truck tuning and continued stock-ROM analysis remain supported workstreams.
They use the same evidence with separate calibration/image identities.

## Current truck image

The user reports restoring the regular **0.3.12** tune after the temporary
serial readback test. The exact normal-image basename and SHA-256 have not
been established here. The probe-image identity is recorded with its test,
not substituted for the normal image.

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

The current factory suite has 190 tests. The C source checks cover five kernel
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
now has thirty-four CTest entries. Base/environmental spark adds 753,561 comparisons,
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
86 new profile bytes, retaining explicit EGR/VSS dependencies. CI runs the34
independent CTest entries two at a time.
The simulator has 18 CPU/GUI/real-ROM tests and its
CI matrix on Python3.10/3.11/3.12.

EQ-11 retains additional joined state combinations. EQ-12/13 cover physical
device/board evidence; EQ-14 covers actual optional-module/external-caller code.
We can continue the C source while preserving those explicit interfaces.

## Delivery workflow

Complete each implementation step, run its required checks, publish its PR and
merge after CI passes. The user authorized merging each completed step; another
confirmation is not required. Work in progress stays on its implementation branch.

## Historical material

Earlier assembly and minimal-slice proofs remain under [source/](../source/README.md).
Their old next-step language and unimplemented declarations are interpreted
within that prototype. Frozen V1 plans and dated `2.bin` investigations do not
override the current C design or current-tune image identity.
Git history is the version record; no parallel live-state document is created.
[Repository audit](REPOSITORY_AUDIT.md) records the cleanup and retained evidence.
