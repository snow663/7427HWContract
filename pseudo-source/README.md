# Modular PCM pseudo-source

This is the source outline for our replacement 16197427 firmware. Each logical
routine has its own C file. The existing stock BMHM analysis supplies the
hardware and scheduling reference; algorithms and calibration layout can evolve
independently behind named interfaces.

The current deliverable is a host-compilable outline with checked scheduler
logic, reset/REF transactions and a verified fuel calculation. It does not emit
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
| `src/math/` | Shared rounded lookup and word-gain arithmetic |
| `src/spark/`, `src/idle/` | Spark and IAC task boundaries |
| `src/sensors/` | Input acquisition/housekeeping boundaries |
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

The tree contains 79 public routines: 35 implemented outlines, 40 dependency
boundaries and four implemented algorithms. Reset CPU/chip-select/board
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
Host tests do not establish target instruction timing, physical output behavior
or whole-program equivalence. The dedicated GitHub workflow runs the CMake route.

## Next source work

Implement the remaining reset stages and target early-reset/interrupt backend.
Next port the scheduled knock decay/sensor diagnostic and normal-spark
consumption of the new observation accumulator. Retain verified driver ordering
and fault exits. Then port the remaining injector, spark and IAC drivers
individually. Controller task boundaries can be replaced
with direct calls to implemented routines as those modules are completed.
Feature removal will update both dispatch admissions and shared-state producers.

The factory contracts remain linked from
[the scheduler](../docs/analysis/FACTORY_SCHEDULER_MAP.md),
[hardware boundaries](../docs/analysis/FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md),
[timing closure](../docs/analysis/FACTORY_INTERRUPT_AND_TIMING_CLOSURE.md), and
[fuel arithmetic](../docs/analysis/FACTORY_FUEL_INTEGER_HANDOFF.md).
