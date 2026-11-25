# Full factory-equivalence development plan — 2026-11-24

## Objective and source of truth

Reconstruct and demonstrate the functional behavior of the factory GM BMHM `$31`
firmware, including transmission, before removing features. Different native
instruction sequences, internal algorithms and RAM/ROM placement are acceptable
when observable behavior and relevant retained state are equivalent.

The maintained development branch is `work/pseudo-source-development`. The
independent audit remains preserved at
[`8dce2cf`](https://github.com/snow663/7427HWContract/tree/8dce2cf9a492e0366213877491de7957953b361d).
PRs [#50](https://github.com/snow663/7427HWContract/pull/50) and
[#51](https://github.com/snow663/7427HWContract/pull/51) integrated the verified
CPU/arithmetic corrections and complete OC4/OC5 C bodies into development at
`2696d9d`. The [current entry census](../audit/CURRENT_FUNCTIONAL_COMPLETENESS.md)
and its generated CSVs govern the remaining worklist. The historical audit's
54-unresolved count includes the two timer bodies and must not be presented as
the current count.

The reviewed universe has 253 known resident entry points. Current categories
are 190 implemented but insufficiently verified, three partial, eight justified
RTS replacements and 52 unresolved entries. No independent whole-entry
certificate is awarded. The 52 entries include twelve explicit supplied-boundary
roots and forty unresolved nested mappings. They are neither a count of new C
files needed nor proof that every possible firmware entry has been discovered.

## Ordered work packages and acceptance evidence

The order below sets priorities. Native tooling, module-domain review and
peripheral evidence can proceed alongside resident-source reconstruction when
their dependencies are explicit. A green fixture test closes its stated
contract, not an entire subsystem.

| Order | Work package | Required completion evidence |
|---|---|---|
| 1 | Remaining audit integration | Port verified artifact-binding and bus-aperture corrections selectively; reproduce historical failures, run positive controls, preserve the audit branch, and keep the comparator labelled synthetic. Refresh source/test inventories and CI gates. |
| 2 | CPU instruction closure | Implement or explicitly bound DAA, BRN, STOP and illegal-opcode trap behavior using authoritative HC11 semantics. Retain independent flag, addressing, stack and interrupt counterexamples; triangulate with a second qualified implementation or real HC11 observations. |
| 3 | Current control | Close `$7C13`, including the retained `$014C` producer/consumer contract and all admitted calibration branches. |
| 4 | Transmission spark | Review and close the five indexed entries and their shared engine/spark state; preserve each unresolved mapping until demonstrated. |
| 5 | Shift control | Review and close eight indexed entries, including retained learning, transitions and output ordering. |
| 6 | Pressure and TCC | Review and close fourteen indexed entries, including cancellation, shared input dependencies and register effects. |
| 7 | Transmission-input processing | Close twenty-four indexed entries. Establish mappings for the eight ordered prefix callees and nested estimator/diagnostic/math entries; avoid duplicating algorithms already represented inline. |
| 8 | Three partial entries | Close `$7100` reset-to-runtime, the joined `$AE85` prefix/tail, and `$F5DC` signature-qualified module behavior. These are a separate gate from the 52 unresolved rows. |
| 9 | External execution domains | Resolve the eight fixed `$18xx` hooks and dynamic `wordRAM[$038E]` callback. Supply admitted implementations/ABIs or document and test a bounded configuration domain; unsupported behavior remains visible. |
| 10 | Native execution | Produce an actual HC11 compiler/linker/assembler artifact bundle; execute reset, state initialization, C entry/return and interrupts. Verify 16-bit ABI, stack, runtime helpers, memory layout and symbol/byte binding. |
| 11 | PCM peripheral model | Qualify timer, ASIC, ADC, serial, watchdog, board-output and RAM/EEPROM behavior from evidence. Define logical time, interrupt admission/acknowledgment and 8/16-bit access effects. Unknown accesses must be inconclusive. |
| 12 | Dual-BIN functional verification | Run the original and actual reconstructed BINs in isolated environments from one immutable stimulus stream. Compare ordered outputs and a reviewed retained-state relation, with separate coverage and first-divergence replay bundles. Record shared-CPU dependence until independently qualified. |
| 13 | Hardware timing and bench qualification | Measure physical bus/pin behavior, deadlines, stack limits and interrupt latency on HC11 hardware. Establish which modeled interleavings are physically reachable and validate the declared timing policy. |

Engine-operation, fuel, spark, idle, startup, interrupts, hardware access and ALDL
remain essential throughout. Transmission cannot be declared irrelevant merely
because a later derivative controller may be manual-only. Its shared producers,
consumers, retained state, optional branches and output effects belong to the
factory-equivalence dependency graph.

## Entry-level completion procedure

1. Freeze the factory bytes, entry/call context, calibration domain, hardware
   contract and required state owners. Check whether an unresolved address is
   already represented by a shared or inline C algorithm before adding a body.
2. Preserve an executable failing case for a confirmed implementation defect or
   absent observable effect. Distinguish a missing body from an unproven mapping
   and from an unimplemented external module.
3. Implement the bounded behavior, including flag-dependent arithmetic,
   retained-state updates, failure prefixes and ordered device effects. Use
   target-width arithmetic and explicit representation boundaries.
4. Compare actual factory instructions with the C implementation using an
   independently specified oracle contract. Cover calibration alternatives,
   state histories, interrupt windows and all declared branch outcomes. Record
   shared helpers, substituted calls and unsupported hardware assumptions.
5. Update the exact entry mapping and content-identified census. An implementation
   mapping can move a row to implemented-but-insufficiently-verified; a fully
   verified classification requires a separate independently reviewed behavioral
   certificate and closed dependencies. The current generator rejects that
   promotion because no such certificates are supplied.

For the partial entries, a leaf test alone is insufficient. `$AE85` needs a
joined prefix/tail comparison, `$F5DC` needs both absent and enabled-module
semantics, and `$7100` needs actual native reset-to-runtime execution.

## Dual-BIN and confidence boundaries

The initial objective is functional execution and output/state correlation.
Detailed cycle accuracy is a later hardware-qualified axis. Logical time still
must advance consistently enough to model timer expiry, polling, pulse width,
timeouts and wraparound. Equal PCs or instruction counts are not semantic
checkpoints for differently compiled programs.

Require private CPU, RAM, EEPROM, stack, peripheral state, interrupt queues and
output queues; preserve state across stimulus epochs. Keep raw events alongside
any reviewed normalization. A limit, unknown opcode, unbound call, unsupported
device effect or missing checkpoint produces an inconclusive result. It must
never be counted as agreement. See the [dual-BIN contract](../audit/DUAL_BIN_FRAMEWORK.md)
for the adapter and first-divergence requirements.

Static entry counts, all sixteen slot wrappers, host compilation, synthetic
artifact tests and large differential case counts are distinct evidence. None
alone establishes whole-firmware equivalence. The deliberately failing
`build_equivalence_inventory.py --check --require-complete` gate keeps that
distinction executable until the missing evidence is supplied.

## Feature removal and the separate custom-ROM trajectory

Feature removal follows a documented factory-equivalence baseline. A later
manual-only or simplified derivative needs its own producer/consumer analysis,
retained-state contract, explicit output-off/cleanup behavior, regression domain
and release qualification. It must preserve shared engine inputs, diagnostics
and hardware obligations even where a transmission consumer is removed.

This plan governs factory reconstruction and verification. It does not advance
the independent [Rev B/TS00 custom-ROM trajectory](../WORKING_STATE.md#tuning-simplification-trajectory),
authorize a new calibration/BIN, alter OEM register workbooks, or claim truck
validation from simulator results.
