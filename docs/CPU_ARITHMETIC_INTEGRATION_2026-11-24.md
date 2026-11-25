# HC11 reference execution and target arithmetic corrections

This change carries the verified CPU, interrupt-scheduling and target-width
arithmetic corrections from the
[frozen independent audit](https://github.com/snow663/7427HWContract/tree/8dce2cf9a492e0366213877491de7957953b361d)
into active development. Its development base is
`f2f493f4df5843d37baf23d27a460dbd7d890476`; the audit branch remains the separate,
complete historical record. The focused production and regression files are
copied from that audited revision.

## Included corrections

The legacy and newer CPU cores now preserve and update the documented CCR bits,
reject illegal prebyte combinations, enforce XIRQ's separate X mask and the
software restriction on setting X, and protect the instruction following a
CLI/TAP transition that clears I. Other verified corrections cover reset S,
WAI frame/timing accounting, aggregate legacy instruction clocks, and the newer
core's required CLR operand read. The coordinator admits eligible XIRQ requests
past a masked queue entry and stops retaining canceled timer-level requests,
while preserving the consumed REF edge until admission.

Nine C expressions now widen an operand before multiplication or shifting so
their saturating operations retain the carry on a 16-bit-int target. For
example, `mix_word(2u * pulse)` can wrap to zero for `pulse == 32768` before
the helper receives the result. `mix_word((uint32_t)2u * pulse)` preserves the
intermediate value and lets the helper saturate it to 65535. The affected
paths are CPI, crank, BLM, barometric/battery and derivative fuel scaling,
asynchronous accumulation, governor scaling, and startup MAP conversion.

Correct CLI deferral exposed a knock comparison-harness defect: its point-3
request was consumed when admission was initially rejected. The harness now
retains that request until the CPU admits it. Points 1 and 2 retain their
documented one-shot attempt semantics. The literal regression requires rejection
at `$AA89`, admission after the protected BRSET at `$AA8D`, one RTI at `$CEBA`,
restored registers, retained sample baseline `$0001`, and exact OC1 I/O events.
These are logical injection fixtures; they do not establish hardware IRQ-level
behavior or a native C mask backend's instruction boundaries.

The original counterexamples, source locations and authoritative references are
preserved in the frozen audit's
[CPU report](https://github.com/snow663/7427HWContract/blob/8dce2cf9a492e0366213877491de7957953b361d/docs/audit/HC11_ISA_AUDIT.md)
and
[target arithmetic report](https://github.com/snow663/7427HWContract/blob/8dce2cf9a492e0366213877491de7957953b361d/docs/audit/TARGET_ARITHMETIC_AUDIT.md).
The local `docs/audit/hc11_validation_results.json` retains the exact CPU/test
hashes and original before/after ISA results. The portable knock reproducer
requires that corrected CPU hash and checks the loaded implementation's path.

## Permanent verification gates

The focused workflow runs the independent ISA tests, six coordinator tests,
source-bound target arithmetic tests, existing newer-simulator tests, production
host compilation/contracts, and the fast knock IRQ witnesses. Its baseline
runner requires the exact pinned baseline HEAD, the recorded method and
assertion-failure counts in each selected suite, and zero errors or skips. An
import or build failure is not accepted as a reproduction. It does not compare
the complete failed-test identity manifest, so an unrelated failure with exactly
the same counts remains outside this check. The workflow retains full baseline
logs as an artifact.

The local focused run against source commit `1d1fae0` passed all 357 ISA
methods, 14 arithmetic methods, six coordinator methods and eight existing
newer-simulator methods. Running the same new regressions against the pinned
development base reproduced 493 ISA assertion/subtest failures, nine arithmetic
failures and four coordinator failures, with zero unittest errors. These counts
are assertions, not a count of independent defect classes. The full integration
workflow is a separate gate.

The target arithmetic tests use a bounded C integer-semantics model with
`pycparser==3.00` supplying syntax. They execute the actual parsed expressions
under 16-bit-int rules and independently calculated expectations. They are not
a native HC11 compiler, target ABI test, or whole-function equivalence proof.

Useful focused commands from the repository root:

```sh
python tests/audit/test_hc11_isa.py
python -m unittest discover -s tests/audit -p test_interrupt_scheduling.py -v
python -m unittest discover -s tests/audit -p test_target_arithmetic.py -v
python tools/audit/reproduce_baseline.py --repo /path/to/f2-checkout --out /path/to/results
python tools/audit/verify_target_arithmetic_host.py --jobs 2
python pseudo-source/tests/compare_knock_rom.py /path/to/pcm_knock_tests --irq-only
python tools/audit/reproduce_knock_irq_harness.py --host-binary /path/to/pcm_knock_tests --expect-mismatch
```

The old-knock-harness reproducer uses `git show` at the pinned base and runs only
its definitions against the corrected current CPU. It returns 1 for the exact
known mismatch, 2 for an unexpected result/setup error, or 0 when
`--expect-mismatch` confirms the exact expected failure. It needs the pinned Git
object, so the workflow fetches full history. Its success means the historical
defect was reproduced.

The full pseudo-source workflow now triggers on reference-core changes and
pushes to active development as well as pull requests. It builds with assertions
enabled and runs all existing host/source/image contracts and all 53 factory-ROM
differential suites. Focused regressions do not replace that integration gate.

## Scope boundaries

This integration excludes the audit's native-artifact binding corrections,
C bus-aperture changes, broad completeness inventory and dual-BIN prototype.
The two output-timer handlers were left for a separate implementation at this
correction checkpoint. Their subsequent C-body implementation and verification
are recorded in the [output-timer contract](analysis/FACTORY_OUTPUT_TIMER_IMPLEMENTATION.md).
No new firmware BIN or calibration is introduced here.

DAA, BRN and STOP remain unsupported by the legacy interpreter; illegal-opcode
trap entry, complete HPRIO arbitration, bus-cycle accuracy, hardware-backed ISA
qualification and whole-firmware equivalence remain open. Passing these
regressions establishes the bounded corrections and retains their safeguards.
