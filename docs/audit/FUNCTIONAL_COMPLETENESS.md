# Independent functional-completeness and test-evidence audit

Audit date: 2026-11-24. Main reviewed at
`56a3145477291dd7c6bfee15db98414c983b1b2f`; development reviewed at
`f2f493f4df5843d37baf23d27a460dbd7d890476`. Development is the implementation
baseline for this report. This work does not modify either branch.

## Finding

**Complete functional equivalence is not established, and there are confirmed
missing engine output-interrupt bodies.** The reconstruction contains extensive
resident engine logic and useful comparisons against real factory instructions.
Those comparisons establish selected behavior under supplied conditions. They
do not constitute a complete reconstructed HC11 image, an independently qualified
CPU oracle, or a closed controller/device execution environment.

The concrete engine-critical gap is the output-timer pair: vector `$FFE0` selects
factory `$7875`, and `$FFE2` selects `$78D9`. Both are explicitly classified
`UNBOUND_OUTPUT_TIMER` by the development vector map. The production C dispatch
returns `PCM_UNIMPLEMENTED` before acknowledging the request. This cannot be
explained as a different internal algorithm or RAM layout: a required observable
register write is absent. See the executable reproduction below.

The five supplied current/transmission groups remain a separate source-completion
gap. They have dependencies on state consumed by other engine routines. Giving
transmission the lowest implementation priority does not, by itself, justify
removing those dependencies from an engine-equivalence claim.

### Baseline comparison

The indexed routine roster, rooted ROM maps, and all 53 C/ROM comparison scripts
are identical between these two reviewed revisions. Main registers 113 CTests
(53 ROM comparisons and 60 other contracts); development registers 122
(the same 53 comparisons and 69 other contracts). Development adds native image,
vector, bus, mailbox, execution and RAM-owner infrastructure. Within indexed
`src/`, its changes are the word read/write drivers, serial RAM write support,
and fuel RAM-owner accessors; it does not add the missing output IRQ bodies or
the five missing groups. Those integration changes can affect behavior and must
be retested; identical routine counts do not imply identical semantics.

Evidence: [routine index](../../pseudo-source/routine_index.csv),
[CMake registrations](../../pseudo-source/CMakeLists.txt),
[development vector map](../../pseudo-source/include/hc11_vector_map.def),
[vector dispatch](../../pseudo-source/platform/hc11_vector_contract.c).

## What the inventory counts

The machine-readable inventory covers **253 known resident factory entry
points**, derived from vector targets, direct JSR/BSR targets, all 16 resolved
scheduler-table targets, and rooted entries already identified by the repository's
call-binding and local-CFG reviews. The vector/call/dispatch union contributes
250 resident addresses. The reviewed roots add `$7100`, `$FA5B`, and `$ABCB`.

This is a census of the currently justified entry universe, not a declaration
that every possible indirect target has been discovered. The rooted graph itself
contains **14,523 instruction starts** and is a structural *may-reach* graph.
Conditional branch feasibility, call return, wake and interrupt admission are
separate questions. Its instruction count is not execution coverage.

Eight fixed external targets (`$1800`, `$1803`, `$1806`, `$1809`, `$180C`, `$180F`,
`$1812`, `$1815`) and the arbitrary factory callback `wordRAM[$038E]` remain
explicit frontiers. The callback prevents a finite, unconditional claim about
all reachable executable addresses without an input/domain restriction or a
supplied callback implementation. The 44 decoded instruction starts in the
repository's alternate-entry inventory are retained separately: they are
unrooted candidates, not silently counted as ordinary reachable functions.

The **413 indexed C routines** are a different population. They include split
slices, composite roots, alternative host/research routes, and new platform
contracts. They cannot be used as the factory function denominator. Their status
labels are 235 `implemented_outline`, 169 `implemented_algorithm`, and nine
`dependency_boundary`. An `implemented_outline` label frequently accompanies a
substantial resident implementation; it is not evidence that the body is missing.
Thirteen index entries have no parsed rooted factory start because they describe
new interfaces or contracts. The other references collectively name 362 distinct
rooted starts, many of them internal slices rather than independent functions.

### Classification rules and result

| Requested class | Known entries | Evidence standard applied |
|---|---:|---|
| Fully implemented and behaviorally verified | 0 | No independent whole-entry certificate was supplied; passing a shared-CPU differential alone does not qualify. |
| Implemented but insufficiently verified | 188 | Exact source-entry claim with a C body, or an explicitly reviewed inline/parameterized mapping; functional scope and dependency closure remain qualified. |
| Outline or partial implementation | 3 | `$7100` startup boundary/scaffold, `$AE85` resident tail with an unsupplied eight-callee prefix, and `$F5DC` resident signature probe with an absent enabled module. |
| Intentionally excluded or replaced | 8 | Raw `$39` RTS leaves, including explicit delay replacements. The justification is limited to a normal completed call and the chosen timing abstraction. |
| Unresolved or missing | 54 | Two explicitly unbound output IRQ bodies; 52 entries without a closed resident mapping in the five supplied groups and their dependencies. |

These are evidence categories, not a percentage complete. In particular,
"unresolved or missing" distinguishes an unresolved C mapping from a proven
absence. The four direct current/shift/pressure/transmission-spark wrappers and
the eight named transmission-prefix roots are explicitly supplied boundaries.
The remaining nested entries are retained as unresolved until an implementation
or justified inlining is demonstrated. No filename or containing source range
is promoted to a complete mapping.

The eight replacement entries are `$CF15`, `$E6E4`, `$EB17`, `$EB18`, `$EE5F`,
`$EE60`, `$F3ED`, and `$FBD6`. Each begins with the raw byte `$39` and has no
algorithmic body before returning. `$CF15` is explicitly folded into slot 00's
return; `$F3ED` and `$FBD6` have explicit nominal-delay contracts in their callers.
This is a justified abstraction for the initial functional comparison, subject
to later stack/interrupt/device timing validation. It does not authorize treating
the external `$18xx` hooks as empty returns.

Some functions are deliberately non-bijective. `$77F7` is the second bank of
`pcm_reference_timer_arm`. The raw `$9222`/`$923C` setters are inlined in
`pcm_iac_service`, rather than replaced by larger wrappers that change additional
state. `$9240` is the final output-enable update in `pcm_iac_boot`; `$9247` becomes
the input-shadow predicate in `pcm_iac_error`. `$D8F0`/`$D94B`, `$F49A`, and `$F5CF`
also have reviewed inlined or parameterized mappings. The generator preserves
these distinctions rather than declaring every unmapped address unimplemented.

### Generated deliverables

| Artifact | Purpose |
|---|---|
| [factory_function_inventory.csv](../../maps/audit/factory_function_inventory.csv) | Every known resident entry, class, source location, direct/tail dependencies, missing-group reachability, and unresolved transitive frontiers. |
| [missing_implementation_inventory.csv](../../maps/audit/missing_implementation_inventory.csv) | The 54 unresolved/missing and three partial entries, without hiding nested dependencies. |
| [C_source_claim_inventory.csv](../../maps/audit/C_source_claim_inventory.csv) | All 413 C index entries, their declared starts and source status; deliberately separate from the factory entry census. |
| [external_frontier_inventory.csv](../../maps/audit/external_frontier_inventory.csv) | All eight fixed hooks and the arbitrary callback; no implicit whitelist or no-op assumption. |
| [unrooted_alternate_inventory.csv](../../maps/audit/unrooted_alternate_inventory.csv) | All 44 alternate instruction starts, kept outside rooted coverage. |
| [equivalence_test_inventory.csv](../../maps/audit/equivalence_test_inventory.csv) | All 122 CTests plus 33 additional Python test modules, with oracle lineage and explicit source-level scope. |
| [equivalence_inventory_summary.json](../../maps/audit/equivalence_inventory_summary.json) | Counts, reviewed revisions and hashes of structural inputs. |

Columns containing `not_coverage`, `not_execution`, or `candidate` are deliberately
not proof columns. A test source referencing a C function does not establish that
the function executes in every mode, or that its entire branch/state space is
tested. A source range containing an entry does not establish a matching ABI or
behavior. Transitive missing-group reachability is not RAM ownership.

## Missing implementation inventory by priority

| Priority | Group | Unresolved entry addresses | Consequence |
|---|---|---|---|
| P0 | Output timer IRQs | `7875 78D9` | No C handler or required first acknowledgment for OC5/TIC4 and OC4; async/output scheduling cannot be declared complete. |
| P1 | Startup/native entry | `7100` (partial) | Host reset sequencing and native scaffolds do not establish a compiled reset-to-runtime execution, stack ABI or complete state initialization. |
| P1 | Optional/factory execution | Eight `$18xx` hooks; `wordRAM[038E]` | Conditional behavior remains external. An explicitly constrained absent-module configuration is a possible test domain, not a universal exclusion. |
| P2 | Current control | `7C13` | Resident calculation producing `$014C` is delegated to a platform task. |
| P3 | Transmission-input prefix and dependencies | `AEA4 B018 B089 B1F0 B23C B2B2 B2C9 B2ED C483 E58C E5CF E5F1 E60B E6F5 E7C7 E808 E847 E8C8 EB81 EBC0 ECCC EF2B F420 F5A2` | Eight prefix roots and their unresolved estimator/diagnostic/math dependencies remain supplied. The resident `$F781/$F64E` tail does not close this group. |
| P3 | Shift control and dependencies | `B32D B334 B367 B4B2 BA65 E654 F131 F1DD` | Missing progress/learning/reaction behavior can retain or publish state used elsewhere. |
| P3 | Pressure/TCC and dependencies | `B56B B587 B88D B91D BA38 BC77 BCC6 BE5C BEBC BF62 C00B C271 D969 E664` | Pressure and TCC progress is incomplete despite implemented gear-selection and output helpers. |
| P3 | Transmission spark and dependencies | `C40A C4E5 D9B7 DA6F DAE2` | Spark inputs/limit state remain dependent on a supplied group. |

All 16 scheduler-slot wrappers are now resident. Historical reports describing
seven still-unimplemented slots are stale for these reviewed revisions. Conversely,
a resident slot wrapper does not automatically implement every optional module,
fast-group dependency or asynchronous interrupt that can interact with it.

Evidence: [global entry/call graph](../../maps/structure/factory_global_control_edges.csv),
[reviewed call bindings](../../maps/structure/factory_global_call_bindings.csv),
[current-control boundary](../../pseudo-source/src/transmission/current_control.c),
[eight-callee prefix](../../pseudo-source/src/transmission/transmission_input_prefix.c),
[transmission analysis](../analysis/FACTORY_TRANSMISSION_CONTROL.md).

## Executable failure: missing output IRQ acknowledgment

Run the isolated witness from the repository root:

```sh
python tools/audit/reproduce_output_irq_gap.py
```

It compiles the actual production C files plus
[output_irq_readiness_probe.c](../../tests/audit/output_irq_readiness_probe.c).
No substitute IRQ implementation or CPU emulator supplies the expected behavior.
The assertion concerns the unavoidable first acknowledgment only. Status and
native-return action are diagnostic fields; later handler behavior is not inferred
from this minimal bus fixture.
The two factory instruction sequences begin:

| Vector / handler | Actual factory bytes | Necessary first external effect |
|---|---|---|
| `$FFE0 -> $7875` | `CE 30 00 86 08 A7 23` | Byte write `$3023 = $08` |
| `$FFE2 -> $78D9` | `CE 30 00 86 10 A7 23` | Byte write `$3023 = $10` |

Both sequences load X with `$3000`, load A with the mask, then store A at `$23,X`
before any conditional branch. The witness supplies verified-frame/masked-entry
preconditions and a flat, zero-filled host bus. On the audited base it returns
exit status **1**, with both failures:

```text
FAIL vector FFE0 -> factory 7875: expected first write 3023=08; got status=1 action=0 writes=0 first=0000:00
FAIL vector FFE2 -> factory 78D9: expected first write 3023=10; got status=1 action=0 writes=0 first=0000:00
```

`status=1` is `PCM_UNIMPLEMENTED`; `action=0` permits no native return. This
behavior is already acknowledged by the existing green vector-contract test,
which expects the boundary. That contract test is useful but cannot establish
functional equivalence for these vectors. The new witness intentionally requires
the missing effect and remains red until a real implementation is added. A later
green result proves only this necessary entry/acknowledgment contract; full
bank state, timer masks, comparator writes, pending requests and retained-state
behavior still require ROM comparisons and interleaving tests.

This witness is outside default test discovery. Its nonzero result is an explicit
open readiness failure, not a skipped or expected-failure firmware-equivalence
test. The compiler must finish successfully; a build/link failure does not count
as reproducing the gap.

## What the existing tests establish

### Actual factory instruction comparisons

All **53 C/ROM differential suites really execute captured factory instructions**
for their selected routes. They do not merely compare two reconstructed C
equations. Their common instruction oracle is nevertheless the same legacy core,
[`hac31_romsim/romsim/hc11_core.py`](../../hac31_romsim/romsim/hc11_core.py), via
`tools/factory_scheduler_replay.py` or a descendant. Many scripts inherit helpers
by executing a prefix of another comparison script; the inventory resolves
these chains and records the route to the CPU. For example, the serial suite
inherits fuel-delivery, feedback, mixture, air and output helpers.

This gives useful algorithm-versus-factory evidence **conditional on CPU,
initialization, memory fixtures and observation correctness**. It does not make
the CPU an independent oracle. A CPU defect can make both the translated
algorithm and its expected output agree with an incorrect assumption. The CPU
instruction audit and target-width C arithmetic audit must therefore be treated
as upstream validation gates, followed by fresh comparison runs. The newer
`7427_simulator/sim7427/cpu.py` is not the instruction engine for any of these
53 comparisons; its smoke tests cannot independently certify their results.

Seventeen of the 53 comparison targets link explicit historical replacement
files such as `alternate_boundary.c`, `iac_background_boundary.c`,
`shift_lamp_boundary.c`, `vss_filter_boundary.c`, the EGR boundary files, or
`slot_f_boundary.c`. The inventory lists the exact linked files per suite.
Later joined suites often use the corresponding resident bodies, which is
additional evidence, but does not retroactively broaden an isolated suite.
Docstrings are retained as scope evidence and may describe a historical
not-yet-ported dependency; current link configuration is recorded separately.

### Other evidence classes

The 69 remaining CTests validate host routines, fixture expectations, provenance,
source patterns, ownership, image composition or native interface contracts.
They are valuable gates, but **do not execute the reconstructed C as HC11
instructions**. In particular, the native image tests use synthetic S-records,
ELF/objdump/nm fixtures and compiler probes. Passing them does not prove that a
complete linked application boots, fits memory, initializes state or executes
correctly on an HC11.

Factory research suites under `tests/test_factory_*.py` execute real stock ROM
where their replay helpers are used, and compare it with a Python reduction or a
specific structural/interrupt/state contract. Some have carefully controlled
interrupt nesting and independent nominal cycle accounting. They strengthen the
factory behavioral specification; they are not whole reconstructed-C BIN tests.
The manual-idle/Rev A/Rev B suites concern a separate custom strategy and cannot
be counted as stock BMHM reconstruction coverage. Synthetic CPU tests and the
optional real-BMHM smoke test are separate categories; the latter may skip when
no matching external BIN is supplied.

### Important blind spots

- **Retained state:** many cases construct or clear RAM and registers before a
  slice. Several suites do feed state through sequences, including idle, knock,
  EGR, factory and connected fuel work. Those are bounded sequences, not proof
  for all reset causes, interrupted writes, prior calibrations or long-lived
  controller history. Test-source mentions of `retained` are recorded as signals,
  never converted to measured temporal coverage.
- **Interrupt interleaving:** the reference-event and OC1 suites use real stock
  interrupt entry/body/RTI. The C side is a host routine, not compiled C behind an
  HC11 frame. Callback injections at selected logical mask boundaries do not
  exhaust admissible instruction-level interleavings, CLI delay, request priority
  or pending flags. ROM-only interrupt research cannot supply the missing C side.
- **Async injection/output:** the async helper and REF-arm logic have evidence,
  but the missing OC4/OC5 completion handlers break a complete output lifecycle.
  Pulse calculation or an isolated write cannot establish eventual bank state,
  cancellation, overlap, rearm or completion behavior.
- **Calibration and optional modules:** branch-directed counterfactual values
  are useful, but do not establish all admissible tables, pointer aliases, module
  ABIs or retained option transitions. Optional return fixtures are explicit
  supplied effects, not recovered module code. The unrestricted factory callback
  must never be silently replaced by a fixed valid-target list.
- **Hardware/output semantics:** tests often compare transaction width, order
  and value while readbacks, ADC-ready, SCI status and timer words are supplied.
  Several fixtures log logical operand accesses while excluding private HC11
  stack traffic and native C owner operations. This is a reasonable abstraction
  only when its observation/memory mapping is explicit; it does not independently
  establish latch, write-one-to-clear, acknowledgment, torn-read or physical-pin
  behavior. Unknown device behavior must remain visible.
- **Coverage:** per-suite executed instruction sets are useful local evidence.
  There is no independently reviewed aggregate covering every factory function,
  both branch outcomes, relevant calibration partitions, persistent-state
  transitions and the corresponding reconstructed instructions. Static starts,
  source names and large random case counts cannot supply that denominator.

## Functional-equivalence confidence by subsystem

| Subsystem | Confidence supported now | Practical boundary |
|---|---|---|
| Fuel arithmetic and selected connected fuel paths | Conditional, substantial slice evidence | Shared CPU oracle; target-width arithmetic; broad running/retained/calibration histories need revalidation. |
| Async injector/output lifecycle | Low; incomplete | Missing OC4/OC5 bodies; isolated pulse and REF tests do not close completion/rearm/interleaving. |
| Spark, knock and timing calculations | Conditional, substantial slice/join evidence | Optional `$180F/$1812`, supplied EGR/transmission inputs, trap boundary, target ABI and actual output behavior. |
| Idle/IAC control | Conditional, substantial resident logic evidence | Optional `$1803`; sequential joins and output shadows do not prove native motor-step/IRQ histories. |
| Startup/reset and retained memory | Partial | Useful ordered boot/clear/controller tests; target stack/native reset/runtime and complete state backing remain open. |
| Interrupt subsystem | Partial and insufficient for whole-controller execution | Selected REF/OC1/fallback leaves exist; output IRQs absent and compiled-C entry/RTI/interleaving unverified. |
| Hardware access | Moderate for selected logical transactions; physical semantics unverified | Fixtures define readiness/status and many ASIC samples; actual bus/device effects need a stated model or hardware evidence. |
| ALDL/SCI/service/factory path | Conditional, useful scoped state/transaction evidence | Native frame/arbitration, service-prefix dependency, arbitrary callback, optional connection module and physical serial timing. |
| Slow scheduler slots | All 16 wrappers resident; selected whole-slot comparisons useful | This does not close fast/current/transmission groups or asynchronous completion. |
| Transmission/current groups | Incomplete | Five supplied groups with 52 unresolved known entries in their closures; retain lowest implementation priority after engine-critical work. |
| Whole reconstructed firmware | Not established | No closed compiled-HC11 dual-BIN execution, qualified CPU/device oracle, complete state relation or aggregate behavioral coverage. |

## Remediation and verification order

1. Finish independent CPU semantics and target-width arithmetic qualification,
   then rerun every affected factory comparison. Preserve smallest failing cases
   and their original expected behavior; never adjust expectations to match a
   defective emulator.
2. Implement `$7875/$78D9` from factory evidence. Make the red acknowledgment
   witness pass, then add full independent state/register and retained sequence
   comparisons, including overlap with REF and foreground async control.
3. Obtain a reproducible real HC11 compilation and linked runtime. Establish
   entry, native frame, state backing, initialization, illegal-opcode policy and
   complete interrupt/return behavior. Keep synthetic image-tool tests, but add
   execution of the produced image rather than promoting them to runtime proof.
4. Specify the allowed stock calibration/module domain and external interfaces.
   Unsupported optional calls must produce a visible unresolved outcome. For
   engine-first work, justify exactly which transmission outputs are supplied,
   when they change, and which engine paths consume them.
5. Build two isolated VM instances, one original BIN and one reconstructed BIN.
   Use one immutable, timestamped/event-ordered stimulus log and independent CPU,
   RAM and device state. Compare normalized semantic outputs and a versioned
   retained-state relation at event or quiescent boundaries, not equal PCs,
   instruction counts or RAM offsets. Record unknown hardware effects distinctly
   from mismatches. Timing can remain an explicit later validation axis.
6. At first divergence, save image hashes, calibration, seed/event index, both
   machine checkpoints, recent register transactions and the state-mapping rule
   that failed. Replay and minimize that case. Require reproducible coverage of
   entry/branch/interrupt/output/state transitions on both sides; do not infer it
   from the static census or from the other VM's coverage.
7. Port the remaining current/transmission groups and review nested mappings.
   Promote a row only with a specific implementation, dependency domain and
   independently reviewed behavioral evidence. Keep intentional replacements
   and unrooted alternate candidates explicit.

## Reproduction and audit safeguards

```sh
# Verify the byte-backed source structure used by the census.
python tools/verify_factory_global_structure.py --check-recorded

# Deterministic generation and drift gate.
python tools/audit/build_equivalence_inventory.py
python tools/audit/build_equivalence_inventory.py --check

# Green census-integrity tests, including deliberately damaged-evidence cases.
python -m unittest discover -s tests/audit -p test_equivalence_inventory.py -v

# Intentionally red: current firmware-equivalence readiness is incomplete.
python tools/audit/build_equivalence_inventory.py --check --require-complete

# Intentionally red: actual production C omits necessary output-IRQ effects.
python tools/audit/reproduce_output_irq_gap.py
```

The audit executed the structural byte-map verification and all 13 census tests
successfully. It compiled and ran the output IRQ witness and observed both
documented failures. It also observed the readiness gate's expected nonzero
result. These inventory tests safeguard omissions, false verified labels,
unresolved callback loss, range-based mapping inflation and hidden CPU lineage.
They are not replacements for instruction or firmware behavioral regressions.

After integrating other audit corrections, regenerate the inventory: added CPU
test modules or changed source locations are expected evidence changes. Review
the diff, then run the drift and schema gates again. No executable success in
this report declares untested functionality verified.
