# Dual-BIN functional verification framework

## What is delivered now

`tools/audit/dual_bin.py` provides an executable, adapter-based comparator,
immutable input epochs, separate-environment checks, ordered output and named
retained-state comparison, coverage snapshots, and first-divergence evidence.
`tests/audit/test_dual_bin.py` executes two **synthetic HC11 BINs** with different
code addresses, RAM locations, registers and instruction sequences. It checks
that those differences are accepted, while a retained-state error, extra output
write, unknown instruction, shared RAM or execution limit cannot pass.
Peer review added safeguards for nested mutable input, state shared during lazy
initialization, duplicate/unsorted named state, and rejected instructions inflating
executed coverage. Those new cases failed before the comparator correction and
all 14 comparator tests now pass. They qualify harness mechanics only.

The included `SyntheticBINAdapter` uses flat synthetic memory and two instances
of the legacy CPU engine. It has no 7427 peripheral model, interrupt scheduler,
calibration contract or real reconstructed C BIN. It is a comparator safeguard
and adapter example, **not a completed BMHM-versus-C firmware run**, and it does
not supply an independent second CPU implementation. `MATCHED_SCENARIOS` means
exactly that: the supplied bounded scenarios matched under their declared model.

```sh
python3 -m unittest discover -s tests/audit -p test_dual_bin.py -v
python3 tools/audit/dual_bin.py --synthetic-demo > synthetic_match.json
python3 tools/audit/dual_bin.py --synthetic-demo --state-fault > synthetic_failure.json
# The last command intentionally returns 1 and reports a retained-state divergence.
```

## Required evidence chain

Keep the layers separate so a failure in a lower layer cannot be concealed by a
passing test above it:

1. **CPU qualification:** independently derived instruction semantics, flag
   preservation, memory order, illegal-prefix rejection, interrupt stack/return,
   and addressing/wrap tests. An implementation passing against itself is not
   qualification. Preserve manual references and hardware-generated vectors.
2. **Hardware qualification:** an address/width/side-effect contract for every
   reachable register and external module. Unknown reads, ignored writes and
   guessed defaults must be visible and make affected comparisons inconclusive.
3. **Artifact qualification:** original BIN hash and acquisition provenance;
   compiler, assembler, linker and runtime versions; ABI probes; compiled BIN,
   ELF, maps, symbol/section reports and calibration identity bound together.
4. **Scenario comparison:** both qualified environments process one recorded
   stimulus stream, preserving state and comparing declared observables.
5. **Completeness accounting:** relate executed instructions, edges, functions,
   calibration predicates and interrupt windows to a versioned denominator.

Two environments with separate state prevent accidental state sharing. Using
the same CPU implementation in both still permits a common CPU defect to hide
a firmware error. Initially, a separately tested CPU may be used on both sides
for useful development evidence, but record that dependence. Cross-run the
original and reconstructed BINs on a second independently developed qualified
core, or triangulate disputed instructions with captured real-HC11 results.
Do not make the reconstructed side call the C function under test to emulate
an unimplemented native routine.

## Minimum real-PCM adapter contract

| Area | Required contract and failure behavior |
|---|---|
| Identity | Immutable BIN/calibration hashes, CPU revision/mode, hardware profile, compiler ABI and adapter revision in every result. Reject mismatched evidence bundles. |
| Private state | Separate CPU registers, stack, all RAM/EEPROM, device latches, timer state, interrupt queues, SCI queues, output queues, reset/watchdog state and random sources. No pointer or object sharing between environments. |
| Stimuli | One immutable, hashed stream of raw ADC/input values, reference edges, discrete switches, voltage/reset events and ALDL bytes, with stable event IDs, order and logical timestamps. Apply equivalent calibration semantics even when storage moves. |
| Progress | Run each side to independently declared semantic checkpoints with explicit limits. Different PCs, instruction counts and internal layouts are expected. A limit, unknown opcode, unresolved callback or unsupported device access is inconclusive. |
| Interrupts | Per-environment pending state, mask/priority/acknowledgement semantics and stack frames. Inject by logical events and reviewed architectural windows; do not assume identical instruction offsets in different BINs. |
| Outputs | Preserve device identity, operation, width, value and ordering. Capture output register writes and interpreted physical commands. Reject undeclared normalization and dropped extra events. |
| Persistent state | A reviewed relation between each side's meaningful retained state, including pending work, adaptive values and output latches. Address equality is unnecessary; future behavior must be preserved. |
| Diagnostics | Complete input prefix and hashes, first mismatching epoch/field, raw and normalized output, current registers, stack, relevant state, recent instructions, bus accesses and pending events. |
| Coverage | Per-side PC/edge/opcode and read/write coverage, plus mapped function, branch-condition, state-transition and interrupt-interleaving coverage. Never call static decoding dynamic execution. |

The `mutable_state_ids()` protocol is an explicit adapter obligation, not a
general proof that arbitrary Python objects share nothing. A real adapter must
enumerate its full mutable environment and have isolation regressions for it.
Input adapters must reject unsupported channels, duplicate events and invalid
values rather than silently coercing them to a convenient fixture.

Checkpoint capture/restore must include non-register execution control. In the
corrected CPU, `irq_inhibit_instructions` holds the CLI/TAP boundary delay outside
the architectural register dataclass; waiting/halted and pending device requests
also matter. Saving only A/B/X/Y/SP/PC/CCR loses future interrupt behavior. The
synthetic adapter reports this control state diagnostically but does not implement
a real PCM checkpoint restore protocol.

The knock comparison exposed a concrete example: its old fixture consumed a
post-CLI request even when the corrected CPU rejected admission. The new literal
regression preserves that request through the protected following instruction and
requires exactly one interrupt/return. Correct CPU flags alone cannot compensate
for a scheduler that silently loses pending work.

## Functional time before cycle-accurate time

Defer cycle accuracy without deleting time from the firmware's functional model.
Timer values, expiry order, pulse widths, timeouts, counters and wraparound can
change branch decisions. A firmware loop that polls a timer must still advance
according to a specified virtual-time policy.

Use external reference-edge/serial/timeout epochs as the primary input clock.
For the first phase, compare completion of bounded work and programmed timer or
pulse commands at semantic boundaries. Both sides receive the same external
events and logical timer samples; each keeps its own pending device obligations.
Specify how virtual time advances while polling or waiting and what happens when
an output schedules a future expiry. Record that policy in the scenario manifest.
It is a model assumption to validate later, not evidence of physical timing.

Do not inject an input after an equal instruction count or insist on equal PCs.
Do not manufacture matching output by pausing one side until it emits the expected
value. A checkpoint is an independently recognized event such as an acknowledged
reference interrupt or a completed dispatcher iteration, not a comparison result.
If a checkpoint cannot be identified without guessing, preserve the trace and
report an unresolved comparison rather than inventing synchronization.

For interrupt interleaving, enumerate architectural windows: before/after a
multi-byte shared-state update, after masking/unmasking, during async injector
queue changes, before RTI, and while an output compare is pending. Use side-specific
maps to corresponding semantic windows. Later hardware timing establishes which
windows are physically reachable and whether actual deadlines are met.

## Output normalization and state equivalence

For the first working implementation, use exact comparisons by default. A
normalizer must have a written reason and tests showing what differences it
accepts and rejects. Keep raw bus traces beside normalized events.

* **Fuel:** channel/bank, enable/off state, scheduled pulse width, repeat/async
  status, cancellation and completion. Preserve overlapping or queued pulses.
* **Spark:** advance/dwell/output-compare commands, enable/bypass state, event
  order and cancellation. Treat a different representation through a declared
  physical-unit conversion, not an arbitrary tolerance.
* **Idle:** coil/step phase, direction, commanded steps, retained position and
  homing/limit state. Repeated writes may have physical effects.
* **ALDL:** ordered transmitted bytes, receive acknowledgement, framing/checksum,
  memory/service effects, timeout transitions and buffer state.
* **Hardware/startup:** configuration sequence, watchdog/reset behavior,
  fuel-pump/fan/EGR or other populated outputs, latches and read-to-clear effects.

A byte-for-byte RAM comparison would wrongly reject relocated structures and
different valid algorithms. Define a relation `R(factory_state, C_state)` using
named quantities and obligations: controller modes, learned corrections,
integrators, diagnostics, queued injector work, timer jobs, serial transaction
state and physical output state. Include different representations where their
future effects are equivalent. Registers, return addresses and scratch need not
match across checkpoints, but their effects before the checkpoint remain
observable. Every omitted persistent owner needs a reason and dependency review.

Do not reset either side between successive epochs unless reset is an input event.
Matching one fuel pulse with a different retained async accumulator is a failure,
even if the next visible error would occur much later. The delivered synthetic
state-fault regression specifically protects this rule.

## Coverage and first divergence

Record at least: factory instruction starts executed; legal opcode/address-mode
pairs; taken and untaken CFG edges; direct/indirect dispatch targets; routines
entered/exited; retained owners read/written; hardware accesses by address and
width; calibration-controlled paths; and interrupt injection/return windows.
Keep resident code, external module hooks, unresolved indirect targets, data and
undecoded ranges separate. Coverage has an explicit denominator version and a
reason for every exclusion. A 100% score on a subset is not whole-ROM coverage.

Stop at the first observable or retained-state mismatch and save a replay bundle:
both artifact/profile hashes, complete stimulus prefix, calibration delta,
pre-epoch checkpoint states, normalized and raw output prefix, bus accesses,
last instructions and stacks, pending interrupts/queues and coverage. Name the
earliest differing field and its owner. A minimizer can remove earlier stimuli
while preserving reset and causal dependencies; it must rerun both environments
and produce the same category of failure. Keep the minimized stream as a test.

## Staged implementation and acceptance gates

1. **Repair the reference:** land isolated ISA regressions and target-width fixes;
   rerun all affected C/ROM suites. Resolve any new mismatch without copying the
   simulator result into C. Preserve unsupported instructions and hardware gaps.
2. **Produce a genuine reconstructed image:** cross-compile with the verified
   16-bit ABI, bind the real ELF/S19/map/calibration artifacts, execute startup,
   BSS and C entry/return on a qualified CPU, and measure actual code/RAM budgets.
   An SRecord fixture or host executable cannot pass this gate.
3. **Qualify real PCM adapters:** model the documented registers and measured
   external bus behavior; implement the missing output timer vectors and required
   module dependencies. Start with engine-off/reset and bounded peripheral jobs.
4. **Run differential engine scenarios:** cold/warm start, crank/run/stall,
   sensor bounds/faults, reference interrupts, fuel/async overlap, spark/idle,
   retained learning, calibration alternatives and ALDL. Demand named state
   and output correspondence throughout long sequences and deliberate interleavings.
5. **Close completeness:** classify remaining entry points, resolve the RAM callback
   frontier, justify optional/transmission exclusions by configuration and data
   dependencies, and publish uncovered paths. Increase confidence per subsystem.
6. **Measure timing on hardware:** validate instruction/peripheral timing,
   electrical behavior, deadlines and worst-case interrupt latency on actual HC11
   hardware. Functional agreement alone does not supply those measurements.

The first useful acceptance statement is deliberately bounded: a specified pair
of actual BINs, under specified calibrations, hardware contracts and stimuli,
matched defined outputs and state with listed coverage and no unresolved events.
Expand that claim only as its missing evidence is supplied.
