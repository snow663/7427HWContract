# Independent verification audit — GM 16197427 / BMHM $31

Date: 2026-11-24. Review branch: `audit/independent-equivalence-2026-11-24`.

## Decision

**The reconstructed C is not yet a complete, independently demonstrated
functional equivalent of the original BMHM firmware. The uncorrected CPU and
host-only arithmetic evidence were insufficient to establish that claim.**

This audit supplies isolated corrections and executable regressions, a classified
factory-entry inventory, and an initial dual-image comparison framework. It also
preserves explicit failing readiness tests for missing firmware. Passing the
corrected regression suite is progress toward a trustworthy reference; it is not
a declaration of whole-firmware equivalence.

The substantial existing work should not be discounted: all 53 C/ROM comparison
suites execute real factory instructions for their selected paths. Their shared
CPU, fixture environments, selected observations and host C ABI limit the claims
that can be made from those passes. In two passing suites, applying the old CCR
rule to instruction pre-states observed during corrected execution would have
produced thousands of different CCR results. These are per-instruction
counterfactual comparisons, not complete baseline/corrected lockstep traces.
A matching selected output can conceal a bad reference state.

## Reviewed revisions and scope

| Branch | Pinned commit | Scope |
|---|---|---|
| `main` | `56a3145477291dd7c6bfee15db98414c983b1b2f` | Baseline reconstruction and 113 registered CTests |
| `work/pseudo-source-development` | `f2f493f4df5843d37baf23d27a460dbd7d890476` | Latest implementation; audit branch starts here; 122 registered CTests |

The legacy CPU, nine defective arithmetic expressions, routine index, structural
maps and 53 comparison scripts are common to both revisions. Development adds
native build/vector/bus/mailbox/execution infrastructure and changes RAM-owner,
word-access and serial integration. The newer 35-encoding CPU is development-only.
Neither protected branch was modified or merged by this audit.

The 64 KiB factory image used for independent byte checks and smoke tests has
SHA-256 `6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
It was reconstructed from the repository's committed byte evidence and matched
the repository's expected BMHM identity. This is a reproducible byte identity,
not independent acquisition from a physical PCM.

## Prioritized findings

Priority describes the verification work needed, rather than asserting that a
particular untested engine trajectory encounters every local counterexample.

| Priority | Finding | Disposition and effect on prior conclusions |
|---|---|---|
| P0 | Incorrect CPU reference semantics | Twelve confirmed CPU defect classes corrected. Earlier differential passes cannot independently qualify that CPU; corrected replay remains conditional on its tested scope. |
| P0 | Missing output-timer handlers `$7875/$78D9` | Still missing. Actual production C fails the necessary first acknowledgment witness for vectors `$FFE0/$FFE2`. Complete async/output lifecycle equivalence is false at this boundary. |
| P1 | Nine target-width C failures | Corrected with pre-operation `uint32_t` widening. Host results cannot be extrapolated to the 16-bit target ABI without target-width/native evidence. |
| P1 | Interrupt coordinator errors | Corrected XIRQ priority and canceled-timer-request behavior, with before/after regressions. Full HPRIO/device arbitration remains unqualified. |
| P1 | Knock comparison loses a deferred interrupt | Corrected a harness failure exposed by the qualified CLI rule. The original post-unmask request vanished on rejection; it now stays pending until architectural admission. No knock C calculation defect was established. |
| P1 | Native image provenance/entry checks | Corrected absent vector entries and stale/mixed code/symbol/report acceptance. Integrity is improved; actual C startup, ABI and complete image execution remain unverified. |
| P1 | Hardware window classification | Corrected acceptance of an external window spanning conditional EEPROM. This was not a bypass of the separate write-authorization callback. |
| P1 | STOP and hardware/ABI gaps | Legal STOP at `$7D8D` is intercepted by current tests, not executed; illegal-opcode vector entry and a qualified full PCM model are absent. |
| P2 | External module and callback frontiers | Eight fixed `$18xx` hooks and arbitrary `wordRAM[$038E]` require explicit domain/ABI contracts. No universal no-op replacement is justified. |
| P2/P3 | Current/transmission groups | 52 unresolved known entries in five group closures remain. Current control is P2; transmission is P3, while its engine-consumed state still needs an explicit dependency boundary. |

### CPU defects: exact evidence and executable tests

[HC11_ISA_AUDIT.md](HC11_ISA_AUDIT.md) gives every defect's baseline file/line,
opcode, smallest reproduction, expected/actual behavior and affected comparison
evidence. The [per-opcode matrix](hc11_opcode_matrix.json) and
[baseline matrix](hc11_opcode_matrix_baseline.json) enumerate all 1,024 slots
across the four opcode pages, including legality, addressing, modified/preserved
CCR bits, bytes and documented aggregate clocks.

Confirmed classes include:

* INX/DEX/INY/DEY changing N, and TSX/TSY changing N/Z.
* Indexed BSET/BCLR leaving NZV stale, and legacy TST/CLR retaining C.
* TAP/RTI incorrectly setting X through software; XIRQ mask/entry errors.
* 318 undocumented prefixed encodings being accepted as executable operations.
* 135 encodings with returned/elapsed clock discrepancies, plus WAI double-counting
  the pre-stacked interrupt entry.
* Missing S at newer-core reset; missing post-CLI/TAP IRQ inhibition on an actual
  I=1→0 transition; newer CLR omitting a peripheral-visible operand read.

The independent suite has 357 methods, 229,164 generated instruction cases and
524,288 exhaustive 8-bit arithmetic-helper evaluations. It covers every
implemented encoding in each core: 304 legacy and 35 newer, against a 307-encoding
normal-mode catalogue. It produces 493 failed assertions/subtests against the
pinned baseline and passes against the corrected source. That failure count is
not a count of independent defect classes.

The legacy CPU still lacks DAA, BRN and STOP. The newer CPU is a small subset and
cannot serve as an independent complete BMHM execution engine. Hardware illegal
trap entry, all read-sensitive/dummy bus effects, reset causes, full interrupt
arbitration and hardware validation remain open. Architectural-state tests with
flat memory do not establish production-bus equivalence.

### Coordinator failures beyond the CPU

Both defects originate in baseline
`hac31_romsim/romsim/simulator.py:129-141`, `_service_interrupt`:

1. Queue IRQ followed by XIRQ with CCR I=1/X=0. The baseline services neither;
   the eligible XIRQ remains hidden behind the masked FIFO head. With I=0, it
   instead services the lower-priority IRQ first. The correction considers XIRQ
   first and leaves rejected requests pending. It does not implement full HPRIO.
2. With I=1, TMSK1=`$80` and TFLG1=`$80`, poll once. Clear TFLG1 by writing `$80`
   or disable TMSK1, then clear I. The baseline enters OC1 anyway because it has
   cached a stale timer request. The correction polls timer levels at each
   recognition boundary and separately retains consumed reference-edge requests.

`tests/audit/test_interrupt_scheduling.py` has six executable cases: four
baseline failures plus positive controls for a live timer and a retained REF
edge. All six pass after correction. These findings affect the interactive PCM
simulator; the 53 slice comparisons use the CPU directly and do not all exercise
this coordinator.

### A real comparison failure exposed by the CPU correction

The original CTest batch did not stay green: `knock_rom_differential`
failed its original logical IRQ case 4. Baseline
`pseudo-source/tests/compare_knock_rom.py:128` marked an IRQ as consumed before
line 130 asked the CPU to admit it. The request was attempted immediately after
factory CLI at `$AA88`; the corrected CPU rejected it until the following BRSET
at `$AA89` completed. The harness then lost the request. The C fixture instead
called OC1 synchronously inside its unmask callback.

A reduced witness needs one nonzero byte, `$3FC9 = 1`. The old ROM helper retained
`$0203:$0204 = $0000` with no OC1 I/O; the host C produced `$0001`, a write of
`$80` to `$3023`, and a word read of `$3FC8`. This is an executable scheduling
mismatch, not proof that the knock-retard C calculation is wrong. OC1 does not
modify `$006E`, the following BRSET's input, so admission after that protected
instruction preserves this witness's selected C-visible result.

The correction retains only the point-3 post-unmask request until the CPU accepts
it. It never overrides the CPU's inhibit state. Points 1/2 remain explicitly
one-shot logical attempts; they are not a physical level-triggered OC1 model.
Permanent assertions require rejection at `$AA89`, admission at `$AA8D`, exactly
one RTI at `$CEBA`, complete interrupted-register restoration, retained state,
and exact output events. `--irq-only` runs all 1,536 original IRQ fixtures plus
the literal witness; `--irq-literal-witness` is the smallest corrected check.
`tools/audit/reproduce_knock_irq_harness.py` runs the original pinned harness
against the corrected CPU to preserve the failing-before evidence.

The integration record preserves the original batch failure and the separate
corrected knock rerun. The original session became inaccessible with 119 of 122
completion records; the three unrecorded commands were run separately. These
results must not be described as one pristine all-pass run.
Native C mask-backend instruction boundaries and real pending-source arbitration
remain unverified.

### C arithmetic under a genuine 16-bit-int ABI

[TARGET_ARITHMETIC_AUDIT.md](TARGET_ARITHMETIC_AUDIT.md) records nine source
locations and counterexamples, actual factory saturation-byte evidence,
preserved intentional wraps, and remaining pointer/layout/ABI concerns.

The essential failure is widening too late: `mix_word(2u * pulse)` wraps the
product to 16 bits before the `uint32_t` parameter can see it. With pulse 32768,
the baseline target expression produces 0 where the saturating factory operation
requires 65535. The correction is `mix_word((uint32_t)2u * pulse)`.

The same issue affects seven fuel scaling/divisor sites, the governor shift
temporary, and reset MAP conversion. Concrete examples are governor 8192 shifted
3 (0 instead of 65535), MAP raw 255 (14 instead of 255), and an async period 32768
creating a zero divisor instead of 65535. All nine appear on both reviewed branches.

The tests parse and evaluate the actual source expressions with explicit C
integer rules. They are source-bound width-model tests, **not a native HC11
compiler or native execution**. Fourteen tests produce nine failures/five passes
on each baseline and fourteen passes after correction. Actual host C remains
compatible in the tested contracts. The production syntax census contains 468
C/header files and 714 multiply/divide/remainder/shift expressions after integration;
an inventory row is not a proof that the expression is safe over every domain.

Do not infer target layout, function-pointer representation, stack budget,
library-helper ABI, native MMIO atomicity or ISR call/return correctness from
these width-model results. Signed narrowing in `fuel_governor_lead.c:35` remains
an implementation-defined portability concern rather than a confirmed wrong
GCC-HC11 value; it was not silently changed.

### Bus and image tooling

[ARTIFACT_AND_BUS_DEFECTS.md](ARTIFACT_AND_BUS_DEFECTS.md) supplies baseline
source locations and regressions for three confirmed acceptance defects:

* A `$0400..$1FFF` external-memory window passed endpoint classification while
  crossing `$0E00..$0FFF` conditional EEPROM. Accepted windows now stay within
  a contiguous resource interval.
* Images with missing reset/trap entry bytes were accepted and padded with `$FF`.
  Both entries must now be present; handler behavior is explicitly unverified.
* Native S19, nm and ELF-inspection metadata could come from different builds.
  The real build driver now binds code, symbols and inspection data after export,
  and the boot composer rejects a mismatched bundle. This is consistency checking,
  not authentication of fabricated evidence or native ABI proof.

The eight-case suite has seven baseline failures and eight corrected passes.
The existing 32 native tooling tests also pass with explicit synthetic bindings.

## Completeness and confidence

[FUNCTIONAL_COMPLETENESS.md](FUNCTIONAL_COMPLETENESS.md) and the CSV artifacts
under `maps/audit/` classify every entry in the currently justified resident
function universe. It has 253 entries, not 413: the latter counts split/composite
and interface routines in the C index. The structural graph has 14,523 instruction
starts, which are may-reach decoding evidence rather than dynamic execution.

| Class | Entries |
|---|---:|
| Fully implemented and independently behaviorally verified | 0 |
| Implemented but insufficiently verified | 188 |
| Partial | 3 |
| Intentionally replaced/excluded with a scoped justification | 8 |
| Unresolved or missing | 54 |

Zero certified entries does not mean zero working implementations. The audit
does not promote a source mapping or a passing bounded/shared-oracle comparison
into a full entry/dependency certificate. The missing/unresolved class also does
not mean 54 proven absent bodies: it includes unresolved nested mappings.

The three partial entries are `$7100` startup/native integration, `$AE85` with
an unsupplied prefix, and `$F5DC` with an absent optional module. The eight
replacement entries are raw RTS leaves, including nominal delay abstractions.
Fifty-two unresolved entries fall in current-control/transmission dependency
closures; the two output IRQ bodies are explicitly unbound. All 16 slow-slot
wrappers are resident. The nine external frontiers and 44 unrooted alternate
starts are recorded separately. The arbitrary RAM callback prevents claiming
that this finite inventory closes all possible reachable addresses.

| Subsystem | Confidence justified by current evidence |
|---|---|
| Fuel calculations and selected joined fuel paths | Substantial bounded evidence, conditional on arithmetic/CPU/device/state domains |
| Async injector lifecycle | Incomplete; missing output IRQ bodies prevent a closed lifecycle claim |
| Spark/knock | Useful slice/join evidence; optional and transmission inputs, native output behavior remain qualified |
| Idle/IAC | Useful resident control evidence; complete native step/IRQ histories unproved |
| Startup/reset | Partial; host sequencing is not a compiled reset-to-run execution |
| Interrupts | Partial; selected handlers and CPU frame rules tested, complete firmware/peripheral integration absent |
| Hardware access | Selected logical transactions supported; complete physical/device model unqualified |
| ALDL/SCI/service | Useful scoped byte/state evidence; native interrupt arbitration, callbacks and full transaction histories open |
| Transmission/current | Incomplete, with explicitly retained dependencies |
| Whole reconstructed firmware | Functional equivalence not established |

## What the old test passes mean

All 53 C/ROM comparisons execute captured factory bytes, and all 53 transitively
depend on the legacy CPU. Seventeen link explicit replacement boundary files.
The other 69 development CTests cover host algorithms, interfaces, source patterns,
ownership and synthetic native image tools. They do not execute reconstructed C
as HC11 machine code. Main has 60 such non-ROM contracts.

Representative actual execution traces demonstrate the observation gap. Base-fuel
comparisons passed 532 cases; applying the prior CCR rule to pre-states observed
during those corrected runs would have produced different CCRs in 881 TSX and
11 TST/CLR instances. Hardware/startup/REF comparisons passed 128+4112 cases, with
4246 such indexed-bit instances. These are local counterfactual CCR calculations,
not two complete CPU traces. This invalidates using those passes as CPU
qualification; it does not establish that their selected C output values were wrong.

Retained histories and interrupt injection exist in some suites, but are bounded.
They do not collectively establish all calibration branches, optional modules,
interrupt windows, pending async pulses, timer deassertion, output-latch side
effects or logical-state correspondence. The supplied per-suite inventory records
actual execution lineage and boundaries instead of inferring coverage from names.

## Dual-BIN framework and next acceptance gates

[DUAL_BIN_FRAMEWORK.md](DUAL_BIN_FRAMEWORK.md) specifies independent CPU/RAM/device
state; one immutable logical stimulus stream; explicit temporal progress;
normalized ordered outputs; a reviewed relation between persistent states;
per-side coverage; and first-divergence replay evidence. No requirement equates
PCs, instruction counts, physical RAM layout or internal algorithms.

`tools/audit/dual_bin.py` and fourteen tests implement comparator safeguards with two
different **synthetic** HC11 BINs. Relocated code/state and different instruction
counts match; a hidden retained-state error or extra output fails; unsupported
execution and budgets are inconclusive. No real reconstructed C BIN or complete
PCM adapter was supplied or invented. The demonstration uses separate instances
of the same engine, so its common implementation risk is explicit.

Proceed in this order:

1. Retain the instruction/arithmetic regressions and rerun all affected ROM
   suites. Investigate new differences without copying a bad oracle into C.
2. Implement the two missing output IRQs from factory evidence and qualify the
   complete injector/output lifecycle, including overlap, cancellation and rearm.
3. Cross-compile a genuine reconstructed HC11 image with a pinned ABI/toolchain;
   verify startup/BSS, native frames, state backing and actual ROM/RAM budgets.
4. Qualify the required peripheral model and explicit module/calibration domains.
   Keep unknown behavior visible. Resolve STOP/wake and illegal-trap policy.
5. Run original/reconstructed BINs under shared deterministic scenarios with
   independent environments and semantic checkpoints. Compare output and future-
   relevant state, preserving both traces at the first divergence.
6. Close per-entry, branch, retained-state and interrupt-window coverage, then
   validate detailed timing and electrical behavior on actual HC11 hardware.

## Observed integration results

The recorded results distinguish a historical failing batch from the final result
for each test. All host C build flags were inspected: 63 compiled targets, no
`NDEBUG` definition in flags or production/test source, and `-O2` with an empty
CMake build type. No assertion-disabled Release build was used for these results.

| Check | Observed result and scope |
|---|---|
| Focused audit unit tests | 412 passed after final integration. This includes ISA, target-width, artifact/bus, coordinator, comparator and inventory safeguards. |
| Original 122-test CTest batch | 119 completion records: 118 passed and the original knock harness failed. The session became inaccessible before the remaining three completion records; no outcome was inferred for them. |
| Corrected complete knock comparison | Passed separately: 283,024 comparisons and all 121 instruction starts in its declared scope. The C executable and CPU were unchanged during this rerun. |
| Three completion runs | IAC step passed 376,456 comparisons; slow fuel passed 22,168; slot F passed 43,299. These used the original CTest commands, compiled binaries and build working directory. |
| Latest result for every registered test | 122 of 122 passed across the recorded batch and follow-up runs: 53 actual-factory-instruction/host-C comparisons and 69 other contracts. This is not a single pristine all-pass batch. |
| Factory analysis/research tests | 190 passed. |
| Existing legacy simulator tests | 21 passed, including both optional hash-verified BMHM tests. |
| Existing newer simulator tests | 8 passed after the documented fixture corrections. |
| Native image-tool unit tests | 32 passed; these use synthetic code/artifacts and do not execute reconstructed HC11 C. |
| Pinned original knock harness with corrected CPU | The exact one-byte lost-request mismatch reproduces with exit 1; the fixed 1,536-case IRQ selection plus literal witness passes. |
| Output IRQ readiness probe | Still fails for both missing handlers, with exit 1. |
| Completeness readiness gate | Still fails, with exit 1. |

`integration_results.json` binds current code and the separate runs by source,
binary and log hashes. The original knock failure remains in the batch log;
it was not removed from the evidence. The original batch, corrected knock rerun
and three completion runs are kept distinct in the machine-readable record.

## Reproducing the evidence

```sh
python -m pip install pycparser==3.00
python -m unittest discover -s tests/audit -v

# Use the audit tests against an untouched pinned development checkout.
python tools/audit/reproduce_baseline.py --repo /path/to/f2f493f4-checkout --out /tmp/audit-baseline-results

# Build actual host C with assertions enabled, then run all 122 registered tests.
cmake -S pseudo-source -B /tmp/7427-audit-build -DBUILD_TESTING=ON -DCMAKE_BUILD_TYPE= -DCMAKE_C_FLAGS=-O2
cmake --build /tmp/7427-audit-build --parallel 4
ctest --test-dir /tmp/7427-audit-build --output-on-failure --parallel 4

# Minimal old-harness failure with the corrected CPU: expected exit 1.
python tools/audit/reproduce_knock_irq_harness.py --host-binary /tmp/7427-audit-build/pcm_knock_tests

# Corrected literal witness and all 1,536 original logical IRQ cases.
python pseudo-source/tests/compare_knock_rom.py /tmp/7427-audit-build/pcm_knock_tests --irq-only

# These readiness commands intentionally remain nonzero for real open gaps.
python tools/audit/reproduce_output_irq_gap.py
python tools/audit/build_equivalence_inventory.py --check --require-complete
```

The audit CI workflow separates regression safeguards from unresolved firmware
readiness. Its readiness job is deliberately red until the documented gates are
satisfied. The full C/ROM workflow also triggers on future reference-CPU/replay
changes. Green contract tests must never be relabeled as whole-firmware approval.

See `integration_results.json` for the final observed integration results and
commands. The detailed CPU/arithmetic evidence files preserve baseline failures;
the output IRQ witness remains an executable open failure. No physical hardware
execution, complete reconstructed native BIN, or native compiler validation is
claimed by this audit.
