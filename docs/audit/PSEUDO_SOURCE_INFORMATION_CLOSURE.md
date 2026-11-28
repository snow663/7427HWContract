# Resident pseudo-source information closure — 2026-11-28

## Completion domain

The pseudo-source is a readable, host-executable specification of the original
BMHM $31 resident firmware, including transmission and manufacturing-test
logic, before feature removal. Native HC11 compilation, ROM capacity, target
ABI and physical bench qualification remain separate engineering obligations.
They are not measurements of how much of the resident algorithms is understood.

This work package starts from development 851949df95efc257862f92c9aafd7cd94d99f540. The existing
436-routine census records 28 unresolved entries, three partial entries and
nine external frontiers. The later 463-routine handoff has not been reconciled
to the published development source. Do not assume its counts are committed.
Retain the existing generated census as a source-implementation inventory;
this supplemental disposition is an information-scope review, not a promotion
to independent behavioral verification.

## External interface disposition

The eight $18xx entry points and the dynamic callback at FAA5 are supplied-code
interfaces, not missing resident bodies. The resident F5DC signature probe is
already represented in C. Their resident admission, result channels and
continuations are specified in
[extension memory](../analysis/FACTORY_EXTENSION_MEMORY_INTERFACE.md),
[joined optional behavior](../analysis/FACTORY_JOINED_STATE_AND_OPTIONAL_BEHAVIOR.md)
and [service/test](../analysis/FACTORY_SERVICE_AND_TEST.md). The test/programming
facility interpretation is strongly supported by the manufacturing-test loop,
upload mechanism, profiling and controller hooks; exclusive emissions-test
purpose has not been proven.

For the ordinary absent-module domain, require a nonmatching signature at
1800, a clear 0086.6 after the actual initialization sequence, no supplied code
or external writer enabling it, and no armed manufacturing callback. Do not
infer any physical memory value from the BIN's low-address padding. Matching
signature, enabled hooks, uploaded callback and arbitrary external side effects
must remain explicit external execution boundaries, never successful no-ops.
Signature and enable are independent, including signature loss while enabled.
Retain the resident manufacturing-test mode, serial/service operations and
all emissions and transmission logic. Actual original supplied module bytes
are required only for a claim covering that module's behavior.

## Remaining resident source obligations

The 28 entries in the published inventory have ROM-derived descriptions;
their translation and exact mappings are still outstanding. AE85 is a
separate joined parent obligation. 7100 requires behavioral representation of
reset, register relocation, memory writes and scheduler admission; it does not
require a native C binary. EQ-11 remains the primary ROM-only investigation:
shared-state transitions, retained histories, faults, calibration alternatives
and interrupt ordering. EQ-12/13 remain observable device and board contracts,
with unknown device behavior explicitly inconclusive.

The first candidate batch translates seven entries: B2B2, B2C9, B2ED, E5CF,
E5F1, E60B, E6F5. It uses the actual factory byte sequences and retains ordered
logical writes and failure prefixes. See
[closure candidates](../../pseudo-source/closure-candidates/README.md).
The candidate target is intentionally isolated from the canonical source index
until the exact-head differential gate is observed green and the source census
is regenerated on integration. The existing canonical bodies are not changed
or counted as completed by this commit.

## Acceptance

* Explicit mapping or bounded replacement for every resident entry and
  instruction, including reviewed alternate-entry scope and calibration
  dependencies.
* Preserve retained state, target-width arithmetic, observable bus
  transactions, interrupt and scheduler rules and failure prefixes.
* Run host C versus actual factory instructions, then connected controller
  histories using shared immutable stimuli, separate state and meaningful
  checkpoints; unresolved device effects are not matches.
* Keep original test-code internals, physical qualification and native
  deployability separate; preserve their real limitations.
* No removal of transmission, emissions or manufacturing-test logic until the
  factory reference is established.

This change is source/verification preparation only; no BIN, calibration,
hardware output permission or feature-removal patch is introduced.
