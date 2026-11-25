# Remaining audit corrections and the factory-equivalence worklist

This package carries the remaining verified native-artifact and bus corrections,
the bounded comparator prototype, and a refreshed source inventory into a
reviewable change based on development
`2696d9d1a58d55fa913a967e18761d051e0b87b2`.
The historical audit remains at
[`8dce2cf9a492e0366213877491de7957953b361d`](https://github.com/snow663/7427HWContract/tree/8dce2cf9a492e0366213877491de7957953b361d).
PRs #50 and #51 already integrated the CPU/arithmetic corrections and the two
output-timer C bodies; this package preserves those changes.

The factory reconstruction includes transmission functionality before feature
removal. The separate custom-ROM tuning trajectory and its TS00 hardware
checkpoint are unaffected by this source-equivalence work.

## Confirmed acceptance defects and their corrections

| Defect | Reproduction at development `2696d9d` | Correction |
| --- | --- | --- |
| Bus aperture crosses a different resource class | A single `$0400..$1FFF` `EXTERNAL_GEN` window is accepted although its interior contains conditional EEPROM `$0E00..$0FFF` | `pcm_hc11_bus_bind()` requires a single contiguous resource interval, in addition to its existing endpoint, permission and ordering checks |
| Vector target bytes are absent | Removing the supplied reset or trap entry bytes still produces an accepted padded image | The composer requires bytes at both entries and explicitly reports that handler behavior is unverified |
| Native code, symbols and inspection report can be mixed | Modified C code, changed nm text, stale BSS metadata or an unbound report are accepted | The build driver binds canonical address/value code bytes, exact nm text and inspection metadata after S19 export; the linked boot composer requires the matching bundle |

The bus production change is the exact audited 14-line addition in
`pseudo-source/platform/hc11_bus.c`. The resource classifier and authorization
callbacks are unchanged. Separate `$0400..$0DFF`, `$0E00..$0FFF` and
`$1000..$1FFF` windows remain valid. This is an aperture-classification failure,
not a demonstrated write-authorization bypass or physical EEPROM validation.

Native production changes are in `pseudo-source/native/build_hc11_c.py`,
`compose_hc11_rom.py`, `compose_hc11_linked_boot.py` and
`native_artifact_binding.py`. Entry-byte presence is a necessary condition;
it does not prove a complete or safe handler. The result keeps `flash_ready`
false and reports `vector_handler_behavior_verified` as false. A binding
detects stale or mixed artifacts. It is not authentication, an independent ELF
inspection, a compiler ABI proof or evidence that a real firmware image runs.

These checks intentionally bind each individual artifact bundle exactly. They
do not require the factory BIN and a reconstructed BIN to have identical bytes,
addresses or layouts when their behavior is compared.

## Permanent failing tests and safeguards

`tests/audit/test_artifact_integrity.py` contains eight independent checks:
six native rejection cases, the compiled-C aperture case, and one valid-bundle
control. Against the exact development baseline, the seven negative cases fail
with their expected assertion evidence and the positive control passes. Against
the corrections, all eight pass. All 32 existing native tests also pass.

The ordinary `hc11_bus_contracts` test now includes the crossing-window regression
and valid split-window control. The new assertion fails against the original
bus source and passes after correction. A supplemental 190 boundary-pair check
found four inconsistent bindings before correction and none after it; that
check establishes consistency with the declared classifier, not physical decode.

The permanent runner executes the current tests in a fresh interpreter against
a temporary checkout of the exact historical commit. It verifies test identities,
literal final assertions, one passing control, zero errors/skips, pinned HEAD,
loaded module paths and the regression-file hash. A missing C compiler produces
the same count of failed methods as the real bus defect, so counts or identities
alone would be insufficient. The runner rejects that case, and CI repeats the
missing-compiler control. Its temporary worktree is removed on success or failure.

```sh
python tools/audit/reproduce_artifact_bus_baseline.py \
  --expect-mismatch --out artifact-bus-baseline-results
python -m unittest discover -s tests/audit -p test_artifact_integrity.py -v
python -m unittest discover -s pseudo-source/native/tests -v
```

The historical reproducer returns 1 for the exact old failures by default;
`--expect-mismatch` returns 0 only for those failures. Setup errors or unexpected
results return 2. A successful expectation check means the historical defects
were reproduced, not that the baseline is correct.

The completed local build and all 70 non-ROM CTests pass with assertions enabled.
The combined audit regression suite passes all 420 methods, including the
17 refreshed inventory safeguards. The
[local before/after record](audit_integration_validation.json) identifies the
tested file content and keeps historical failure, setup-control and corrected
results distinct.
The minimal bus probe also compiles with `-Wall -Wextra -Wpedantic -Werror`.
A supplemental strict build of the entire existing bus target exposed the
pre-existing discarded-const warning at `pseudo-source/platform/hc11_ram_sync.c:40`;
that unrelated file is unchanged, and that setup failure was not counted as a
defect reproduction. The ordinary target passes under its existing build flags.

## Comparator prototype: useful mechanics, bounded evidence

`tools/audit/dual_bin.py` and its 14 tests are carried forward from the audit.
They accept different code locations, RAM mappings, registers and instruction
sequences while comparing ordered normalized outputs and named retained state.
They reject extra output events, divergent retained state, shared reported
mutable state, incomplete execution and invalid schedules. The synthetic CLI
demo both matches a three-epoch stream and detects its deliberate state fault
at epoch zero.

Both sides use the same audited CPU implementation, with separate CPU/RAM state.
The example has flat synthetic memory and no real PCM peripheral model, interrupt
scheduler, native compiler evidence or reconstructed firmware BIN. The adapter's
mutable-state enumeration is an obligation, not a proof about arbitrary objects.
These tests qualify comparator mechanics only. See the
[dual-BIN contract and staged gates](../audit/DUAL_BIN_FRAMEWORK.md).

## Current inventory and development order

The regenerated inventory covers 253 known resident entry points, 415 indexed
C routines and 14,523 statically mapped instruction starts. These are different
denominators. None is a whole-firmware completion percentage or dynamic execution
coverage result.

| Classification | Current entry count |
| --- | ---: |
| Fully independently certified | 0 |
| Implemented, insufficiently verified | 190 |
| Partial implementation | 3 |
| Justified replacement | 8 |
| Unresolved or missing | 52 |

The two output-timer entries are now explicitly mapped to their C bodies and
actual-ROM suite. The remaining 52 entries include uncertain nested mappings;
they are not automatically 52 missing algorithms. The three partial entries and
nine external frontiers remain separate work packages. The historical audit's
188/54 classification stays unchanged in its retained branch.

The [current work plan](FACTORY_EQUIVALENCE_WORK_PLAN.md) includes source mapping,
the partial reset/native, interrupt-tail and module paths, current control,
transmission spark, shift, pressure/TCC, transmission inputs, external hooks,
native execution, peripheral modeling and eventual dual-BIN/bench qualification.
No transmission functionality is excluded merely because another configuration
is manual-only.

Generated inventory artifacts bind the content they actually inspect. They do
not claim that a dirty working tree was a clean commit, that static PCs executed,
or that an existing differential suite supplies an independent certificate.
CI checks regeneration and preserves this intentionally failing readiness command:

```sh
python tools/audit/build_equivalence_inventory.py --check
python tools/audit/build_equivalence_inventory.py --check --require-complete
# The second command intentionally exits 1: whole-firmware equivalence is open.
```

The new `Artifact, bus and comparator safeguards` workflow records the expected
historical failures, corrected tests, synthetic demo verdicts and an explicit
`INCOMPLETE` firmware-readiness artifact. Green regression safeguards must not
be read as a green whole-firmware certificate. The existing full integration
workflow remains a separate gate for all 70 non-ROM and 54 ROM differential
suites; only a completed run at the published revision can establish that result.
