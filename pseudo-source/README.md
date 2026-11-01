# Modular PCM pseudo-source

This is the source outline for our replacement 16197427 firmware. Each logical
routine has its own C file. The existing stock BMHM analysis supplies the
hardware and scheduling reference; algorithms and calibration layout can evolve
independently behind named interfaces.

The current deliverable is a host-compilable outline with checked scheduler
logic, reset/REF/knock routines and verified integer algorithms. It does not emit
a flashable BIN.
The HC11 startup/vector assembly, target compiler/linker layout, complete
controller bodies and physical hardware backend remain to be implemented.

## Start here

| Location | Responsibility |
|---|---|
| `src/startup/` | Reset sequence and separate initialization stages |
| `src/interrupts/` | Periodic, reference, OC1 and SCI entry-body interfaces |
| `src/kernel/` | Phase advance, fast groups, slot dispatch, busy/pending catch-up and profiling |
| `src/slots/` | One file per slow slot,00..0F |
| `src/drivers/` | Explicit byte/word transactions, timer arm, watchdog and board-bit toggle |
| `src/fuel/` | Base calculation, REF crank/running/decay logic and asynchronous delivery |
| `src/math/` | Rounded 1D/2D lookup, word gain and signed-floor filter arithmetic |
| `src/spark/`, `src/idle/` | Knock/adaptive gains, learning, corrections and remaining spark/IAC boundaries |
| `src/sensors/` | Knock sensor diagnostic and remaining acquisition/housekeeping boundaries |
| `src/serial/` | Serial-service boundary |
| `src/transmission/`, `src/emissions/` | Existing scheduling dependencies retained visibly for later feature selection |
| `include/` | Public routine declarations, named state, platform and calibration interfaces |
| `calibration/` | Source defaults, separate from executable routines |
| `memory/` | Physical constraints and our future linker/partition rules |
| `reference/` | Factory provenance, slot inventory and observed readback result |
| `tests/` | Kernel contracts, provenance checks and compiled-C versus ROM arithmetic |

[routine_index.csv](routine_index.csv) lists every routine, its file, current
status and reference. Private helpers may remain with the routine they support.
No public routine shares its source file with another public routine.

## Implemented and still delegated

The tree contains 141 public routines: 65 implemented outlines, 41 dependency
boundaries and thirty-five implemented algorithms. Reset CPU/chip-select/board
writes, output initialization and the REF timer/strobe/latch prefix now have
transaction-level C implementations. Their 4,240 compiled-C/ROM comparisons and
64 injected I/O-failure checks are described in the
[reset/REF contract](reference/reset_ref_transactions.md).

The REF continuation is now implemented as separate crank, running, enrichment,
filter, async-output and timer routines. Another 2,502 complete-handler comparisons,
143 I/O-failure checks and 38 direct timer-entry cases match the actual stock code.
The [REF event contract](reference/ref_event_contract.md) records the configuration
and coverage boundaries. Early reset/interrupt assembly and real device/backend
timing remain unfinished.

The OC1 handler now acknowledges its flag, samples the knock-counter word,
advances its baseline, applies both direct-index curves and accumulates the
bounded observation. Its 261,632 numeric comparisons and 1,280 REF/OC1 sequences
match the stock code. See the [OC1 contract](reference/oc1_knock_contract.md) for
failure-prefix checks, coverage and the remaining knock-controller boundaries.

Slot8 now directly calls implemented knock decay and sensor diagnostics.
The normal-spark consumer atomically reads/clears pending observations and
implements its distinct zero, skip, fault and capped-update routes. The broad
spark task now calls the [resident controller](reference/spark_controller_contract.md) directly. See the
[knock control contract](reference/knock_control_contract.md) for exact mux/ADC
transactions, timeout behavior and the 283,023 additional C/ROM comparisons.

Burst timing, low-octane learning/scaling and spark gain/cap production are now
modular C routines. Slot6 calls the learner after an explicit AC/switch input
boundary. The other broad slot/controller roots retain their unported work.
The [adaptive spark contract](reference/adaptive_spark_contract.md) records
480,560 further ROM comparisons, stock burst-disable defaults and the exact
first-observation, timer-expiry and rounding behavior.

Base, coolant, altitude, EGR, MAT and PE terms now have separate routines.
The complete CA6B auxiliary producer and contiguous A700..A84D composite body
are callable C wrappers. Slot7 now calls the auxiliary producer directly in its
verified five-call order, between named background-IAC and shift-lamp dependencies.
See the [spark terms contract](reference/spark_terms_contract.md) for 753,561
additional comparisons, bounded matrix views and exact rounding/retention rules.

Idle, transient and decel/recovery corrections now extend that body through
A9DF. A shared startup/recovery word, unsigned idle error, wrapped transient
offsets and expiry-call behavior remain explicit. See the
[modifier contract](reference/spark_modifiers_contract.md) for 225,622 further
comparisons and the shared startup/recovery state.

Resident override, signed limits and service edits now extend the callable
construction through AB43. The order is upper limit→knock→lower limit→service;
service edits are not re-clamped. The optional 1812 call uses the same 0086.6
flag as profiling and remains an explicit missing-code dependency. See the
[command contract](reference/spark_command_contract.md) for the complete
composite/command wrappers and 356,872 further comparisons.

The earlier A466..A5E4 prelude now has separate load, MAP plausibility, fuel
qualification, reference admission and timeout routines. The normal route stops
at A5E5, AC51 now runs the resident alternate body, and the timeout stops before SWI.
See the [admission contract](reference/spark_admission_contract.md) for 620,169
comparisons, literal mask behavior and independent running qualifications.

Normal period/RPM preparation now connects admission to the command body. It
preserves separate raw/scaled periods, filter seeding and rounding, adaptive
N-bit adoption and a fresh final limit read. The combined builder reports
completion separately from alternate success. See the
[period/RPM contract](reference/spark_period_contract.md) for 699,057 further
comparisons across 163 scoped instructions.

Conversion/publication at AB44..ABCA and the actual AC51..ACA6 alternate body
are now callable C routines. The 180F hook stays explicit; publication
preserves four reads and four writes, repeated rolling/correction samples and
failure prefixes. See the [output contract](reference/spark_output_contract.md)
for 603,682 new comparisons across all 104 output/alternate instruction starts.
The [EST monitor and resident controller](reference/spark_controller_contract.md)
now join these bodies in the dispatcher. Both ordinary spark calls and special
alternate calls run the implemented code without platform task bindings. The
monitor retains wrapped counter deltas, qualification/fault latches and ordered
3FEC→3FE4 handoff; upstream inputs and physical EST semantics remain explicit.

The [slot7 wrapper](reference/slot7_contract.md) now executes the output builder,
signature-qualified connection probe and spark auxiliary body. Background IAC
and shift-lamp work use named dependencies. The probe can change profiling for
the same pass. The output builder preserves the shared shadow and literal
7Fxx command publication, including failed prefixes.

The kernel models the160-phase counter,16-slot dispatch, ordered fast groups,
pre-busy fast service, one-bit pending coalescing and catch-up. Timer recurrence
uses the old compare plus819; initial arming uses sampled TCNT plus8. SlotE's
refresh check and slotF's refresh request are explicit. Literal watchdog and
3066.7 operations retain transaction order.

`pcm_fuel_base()` implements stock7FD8..802F integer arithmetic, preserving
intermediate saturation and truncation. Its inputs retain the documented fixed
point representations. It does not yet implement fuel corrections, delivery
sequencing or a complete running engine controller.

An unfinished body delegates through `pcm_run_task()`. An absent binding returns
`PCM_UNIMPLEMENTED` and identifies the task; absent hardware returns
`PCM_NO_HARDWARE`. Test bindings record admission and explicitly return success.
They do not establish controller execution or hardware behavior.

The platform/task table is an immutable object that can eventually live in ROM.
The state object contains named fields rather than a64KB emulated address space.
References to old RAM addresses are comments explaining provenance, not final
storage assignments. See [architecture](docs/architecture.md).

## Local checks

With CMake and a host C compiler:

```sh
cmake -S pseudo-source -B pseudo-source/build -DBUILD_TESTING=ON
cmake --build pseudo-source/build
ctest --test-dir pseudo-source/build --output-on-failure
```

With Python and a host C compiler available as `cc`:

```sh
python pseudo-source/tests/run_checks.py
```

The checks compile the separate source files, test five kernel contract groups,
check provenance, compare 532 base-fuel cases, and compare 128 startup plus 4,112
REF prefix cases with actual stock instructions. Full-handler tests add 2,502
cases, 143 failure prefixes and 38 direct timer-entry cases. The hardware harness
also checks 64 injected failure positions and the startup/REF dependency boundaries.
OC1 checks add 261,632 numeric cases, 16 failure prefixes and 1,280 REF/OC1 pairs.
Knock control adds 283,023 comparisons and checks all 121 scoped instruction
starts, including selected IRQ boundaries and sensor-fault histories. There
are twenty-eight CTest entries; the Python route runs the same contract/differential checks.
Adaptive spark adds 480,560 comparisons, all 201 scoped instruction starts and
83 checked calibration bytes, while retaining the explicit CB15 input boundary.
Spark terms add 753,561 comparisons, all 336 scoped instruction starts and 1,035
new distinct calibration bytes, including the two-dimensional lookup/filter helpers.
Modifiers add 225,622 comparisons, all 234 scoped instruction starts and 81 checked
calibration bytes (38 new, 43 prior/shared).
Command construction adds 356,872 comparisons, all 137 scoped instruction starts
and 27 checked calibration bytes (17 new, 10 shared). Admission adds 620,169
comparisons across all 155 pre-trap instruction starts and 14 new calibration bytes.
Period/RPM preparation adds 699,057 comparisons, 163 scoped instructions and four
checked calibration bytes (three new, one shared), including the word-lag helper
and full-builder failure/retained-state histories. Output/alternate work adds
603,682 comparisons, 104 instruction starts and 15 new stock calibration bytes.
The monitor/controller suite adds 468,978 comparisons across all 50 monitor/cleanup
instruction starts and three new calibration bytes; all 1,197 expanded fixture
bytes match the recorded image. Slot7 adds400,081 comparisons across43 scoped
instructions, with a separately checked256-byte raw-index backing view and
shared400F option.
Host tests do not establish target instruction timing, physical output behavior
or whole-program equivalence. The dedicated GitHub workflow runs the CMake route.

## Next source work

Implement the remaining reset stages and target early-reset/interrupt backend.
Next port the9E99 background IAC path, its learning/stopped-engine tails and
ACA7 shift-lamp work. C9F7 environmental precomputation is separate slot4 work.
Keep the optional 180F/1812 implementations and machine ABIs as explicit
dependencies. Connect implemented slices without skipping unfinished producer work. Retain verified
driver ordering and fault exits. Continue the remaining injector, spark and IAC drivers
individually. Controller task boundaries can be replaced
with direct calls to implemented routines as those modules are completed.
Feature removal will update both dispatch admissions and shared-state producers.

The factory contracts remain linked from
[the scheduler](../docs/analysis/FACTORY_SCHEDULER_MAP.md),
[hardware boundaries](../docs/analysis/FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md),
[timing closure](../docs/analysis/FACTORY_INTERRUPT_AND_TIMING_CLOSURE.md), and
[fuel arithmetic](../docs/analysis/FACTORY_FUEL_INTEGER_HANDOFF.md).
