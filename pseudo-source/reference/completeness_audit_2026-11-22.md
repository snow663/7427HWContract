# Pseudo-source completeness audit — 2026-11-22

Audited source: `1ecbc4ef6c0df0858339e310688b8e8d6486e04a` on
`work/pseudo-source-development`. Validated mainline:
`ca22491e362ce039ff785f736a9457258066356f`, including merged PR48.
The development head contains that complete mainline history. This report is
a dated source audit; [WORKING_STATE.md](../../docs/WORKING_STATE.md) remains
the single live project-state index.

## Assessment

The engine-control core is well advanced: scheduled fuel, injector delivery,
spark/knock, idle control and EGR have resident C implementations and scoped
stock-ROM comparisons. The complete factory controller is still unfinished.
Its ordinary schedule continues to encounter unported current/transmission
tasks and seven slow-slot roots. A full scheduler run therefore still needs
explicit dependency bindings. A passing fixture with those bindings does not
establish a complete standalone controller.

The next work is substantial source reconstruction and integration. Native
HC11 execution is a separate unfinished phase after source closure. There is
no defensible whole-project completion percentage: public C routine counts
include interfaces, alternative implementations and wrappers of very
different sizes, and there is no complete C-to-ROM coverage denominator.

## Inventory checked against the source

| Item | Count | Meaning |
|---|---:|---|
| Indexed public routines / production C files | 374 | Exactly one indexed public definition per file |
| `implemented_outline` | 227 | C interface or ordered body; can contain conditional external dependencies |
| `implemented_algorithm` | 131 | Reconstructed calculations/helpers; not a whole-system execution claim |
| `dependency_boundary` | 16 | Explicit unimplemented body, external module or target entry |
| Calibration C files | 11 | Separate from the public executable-routine inventory |
| Registered CTests | 105 | 56 quick checks and 49 actual-ROM differential suites |

The source/provenance check accounts for every `src/*.c` file. A separate
scan of comment-stripped public `pcm_*` definitions and calls found no
unindexed public definition or call lacking a production definition.
This checks ownership and linkage, not the semantics of every possible path.

## What is already resident

| Area | Source status | Remaining qualification |
|---|---|---|
| Fuel and injector control | Default scheduled $7D4B..$8547 controller, governor, upstream calculation, feedback, sync/async publication and REF delivery are connected | Optional modules, shared RAM/provider consistency and all-schedule histories still need closure |
| Spark and knock | Admission, period/RPM, base/corrections, knock/adaptation, limits, conversion/publication and output monitor are connected | Optional $1812/$180F modules and native EST timing remain outside the resident proof |
| Idle | Main, background and slow IAC, startup/service paths and the pre-busy step service are resident | Optional $1803 and actual interrupt/step timing need target support |
| EGR | All five demand, feedback, control, flow and output bodies are resident | Conditional $1815 remains external; hardware behavior is separate |
| ALDL/system | SCI RX/TX, session/broadcast/service logic, retained initialization, foreground refresh, factory execution body and interrupt leaves have C implementations | Logical address provider, arbitrary factory-code calls, reset/stack/wake/return ABI and physical serial timing remain open |
| Slow slots | 00, 01, 02, 06, 07, 08, 09, 0E and 0F have resident wrappers and resident stock callees | Slot07 retains its signature-qualified external connection hook; seven other roots remain incomplete |

The combined branch deliberately retains independently checked alternatives
for fuel/governor, speed-source and non-electronic TCC work. Defaults execute
the PR48 bodies; explicit research flags select the alternatives. They must
not be scheduled consecutively or counted as additional distinct ROM area.
One canonical RAM/provider and controller contract should be selected before
target placement.

## All 16 declared dependency boundaries

| Group | Routines / stock anchors | Count |
|---|---|---:|
| Slow slots | `pcm_slot_03`, `04`, `05`, `0a`, `0b`, `0c`, `0d` | 7 |
| Current/transmission | `pcm_current_control` $7C13; `pcm_pressure_tcc` $B56B; `pcm_shift_control` $B32D; `pcm_transmission_spark` $C4E5; `pcm_transmission_input_prefix` $AE85 | 5 |
| Optional module entry | `pcm_spark_extension` $1812; `pcm_spark_output_extension` $180F; `pcm_connection_probe` $180C | 3 |
| Early native reset | `pcm_reset_entry` $7100..$711B, before the $711C C-side call | 1 |

The 16-item list is not the entire external-dependency list. Inspection of
all production `pcm_run_task` and `call_address` sites also finds optional
$1800 AFR, $1803 IAC, $1806 slot03, $1809 governor and $1815 EGR calls inside
otherwise implemented routines. Together with the three entries above,
these are the eight documented external hook addresses. The real module
contents and native register/CCR return contracts are not supplied by the
resident ROM. A missing admitted module must stay explicit; source closure
requires an evidenced implementation or an explicit supported-feature policy.

Factory entry still needs its stack precondition, and factory execution can
call a captured logical address. WAI/STOP/SWI, reset, halt, stack recovery and
interrupt returns deliberately stop at typed host boundaries. Converting
those returns into real CPU behavior belongs to the target port.

## Remaining stock-source work, sized by the actual call graphs

These are **11 concrete work groups**, with shared helpers between groups.
The seven unfinished slots are not seven small leaf routines. In particular,
closing $D4EB can close the principal body used by both slots03 and0B.

| Work group | Required source | Direct stock roots | Stock instruction starts in its transitive graph |
|---|---|---:|---:|
| Slots03/0B gear selection | $D4EB: finish $D4F7..$D5B6, its helpers and the whole-entry join | 1 | 558 |
| Slot04 diagnostics/fault publication | $C8B1, $B9EE, $B99F, $EAB1, $EAE4, $C8D6, $C8FD, $E75F, $E793, $C96A, $C9C0, $C9F7, alternating admissions and shared $006F publication | 12 | 582 |
| Slot05 | $D3B0, $D472 and option-qualified $C6BB | 3 | 532 |
| Slot0A | $D2B2 | 1 | 121 |
| Slot0C | $CC35 | 1 | 62 |
| Slot0D | $CCC1, $DBFB and $DC89 | 3 | 842 |
| Current calculation | $7C13 and its indexed access contract | 1 | 116 |
| Shift progress | $B32D, including $B334/$B367 and their helpers | 1 | 639 |
| Pressure/TCC progress | $B56B, including $B587/$BE5C/$BA38/$BF62/$BEBC/$C00B | 1 | 1,366 |
| Transmission spark inputs | $C4E5, including $B0E4/$D9B7/$DA6F/$DAE2/$C40A | 1 | 493 |
| Earlier transmission/input prefix | $AEA4, $B018, $B089, $C483, $B1F0, $B23C, $B2C9, $B2ED, in order | 8 | 831 |

Sizing method: verify the full recorded BMHM image hash; decode the instruction
starts in `maps/structure/factory_global_instructions.csv`; follow local
`factory_rom_decode.successors` and recursively include direct resident
JSR/BSR targets. This is a structural may-reach graph, with conditional call
return, not an execution trace or interrupt proof. Counts include already
ported generic math, diagnostic masks and gear helpers; they **are not counts
of instructions still needing translation**, and rows overlap. Indexed and
external transfers retain their separate contracts.

Across these groups there are 33 distinct direct roots and 117 resident entry
targets in their combined graphs, spanning 5,553 unique instruction starts.
For example, the $B56B wrapper itself contains only 10 starts, but its graph
contains 19 entry targets. This is why “16 boundaries left” understates the
remaining work. A reliable hours estimate or percentage would require a
reviewed coverage/effort map beyond the public-routine index.

The existing $D4EB diagnostic prefix, $E562 gear limit, $D5B7..$D69E finalizer
and $D8CE threshold selector are independently ported and checked. The next
helpers are $D8FE/$D8F0 and $D840/$D8A7/$D7E5, with their nested math and CCR
contracts. The partial prefix must not run before a callback that executes
the whole stock $D4EB body. See the [detailed D4EB ledger](transmission_d4eb_source_closure.md).

## Verification actually established

| Tree / evidence | Result | Limit |
|---|---|---|
| PR48 validated mainline | All 80 then-registered CTests passed, including 40 ROM suites; repository/factory/simulator checks passed | Historical mainline tree, not blanket validation of the combined branch |
| Audited development head `1ecbc4e` | [CI run45103233828](https://github.com/snow663/7427HWContract/actions/runs/45103233828) succeeded: compilation, 56 quick checks, 9 closure ROM suites and 6 imported PR48 ROM suites | 15 of the current 49 ROM suites; 34 remain outside this combined-tree run |
| Fresh local branch-consolidation gate | All385 production/calibration C files compiled with C11 warnings treated as errors; 56/56 quick checks, provenance and repository hygiene passed | No target compiler or physical execution |
| Test-runner inventory audit | CMake and `tests/run_checks.py` register the same49 ROM comparison scripts and56 quick checks | Test-count parity does not remove historical fixture substitutions |

Some earlier slice tests replace completed neighbors with explicitly scoped
test boundaries. New joined suites exercise larger real bodies, but neither
form is a complete all-controller, all-interrupt-history proof. Existing full
ROM simulator tests execute the stock image; they do not execute a new
compiled pseudo-source BIN. The audit does not independently re-prove every
algorithm or start the deferred full release suite.

## Work after the remaining bodies

Source closure also needs canonicalization of the independent alternatives,
consistent named RAM ownership across control/REF/ALDL/provider accesses,
supported optional-module policy, and joined scheduler histories without
unimplemented stock-task stubs. Current automatic-transmission tasks run in
the ordinary factory loop. A later manual-only selection needs an explicit
producer/consumer review of shared inputs and outputs.

Native execution then needs an HC11 toolchain, startup/vector/IRQ/RTI and
stack/wake/trap assembly, coherent byte/word peripheral drivers, actual RAM
and calibration placement, linker assertions, stack/cycle budgets and a
repeatable target image. Simulator execution of that generated image and
controlled board validation follow. Host object sizes do not establish target
memory fit; [MEMORY_LAYOUT.md](../memory/MEMORY_LAYOUT.md) records the limits.

The practical estimate is several substantial implementation batches across
the 11 groups, followed by a source-integration milestone and a separate native
port/validation phase. Larger pressure/TCC, slot0D and diagnostic groups can
require more than one update; shared helpers can reduce duplication. The
engine-control algorithms are far along, while complete stock-source and
flashable replacement-firmware completion both still require meaningful work.

Continue first with whole $D4EB integration and slots03/0B, then slot04. Keep
updates on `work/pseudo-source-development`. Reserve the full49-ROM and wider
repository/simulator release gate, one PR and merge for an explicit pull/merge
request. No BIN/calibration/register role changed during this audit.

The redundant remote `work/pseudo-source-closure` reference still points to
preserved ancestor `3152109`; authenticated deletion remains blocked. No
unique work is stranded there. All development continues on the canonical
branch, and no new PR was opened for this audit.
