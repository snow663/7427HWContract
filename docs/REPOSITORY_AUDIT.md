# Repository audit and cleanup

Audited reference head: `f4238b766ef083bf7c088f6e111b1a73149c9f7a` on
`analysis/factory-structure-pass1`. The default branch remains `main`; current
analysis/C work is carried by draft PR2 until it is merged. Branch status is
not a claim that the C source builds a target image.

## Findings and corrections

The live README/state/workflow/source indexes still identified the historical
`2.bin` as current and directed new firmware work toward the assembly prototype.
They now identify the reported regular 0.3.12 tune, explicitly leave its exact
normal-image hash unasserted, and point to the modular C source. The temporary
probe's identity remains attached to its single readback observation.

The live working-state index now links the current contracts instead of
repeating several generations of narrative and stale test counts. Dated
investigations, V1 plans and assembly/minimal-slice sources have explicit
historical scope. The original source and useful proof artifacts remain intact.

Five CLI tools still defaulted to the superseded v0.2 listing export. Their
defaults now use the retained v0.3 view. The coarse unreferenced per-address
export and old `/mnt/data`-dependent packaging script have been removed with
their identities recorded in
[retired_artifacts.csv](../maps/maintenance/retired_artifacts.csv).
The three retired tracked artifacts total 1,722,937 bytes and remain recoverable
from the audited parent commit/Git history.

The listing-map generator still emitted earlier CPU-register labels and
classified 305C..305F as unknown board I/O. Its F1-style names/classification
now follow [NXP MC68HC11F1 table 4-1](https://www.nxp.com/docs/en/data-sheet/MC68HC11F1.pdf),
including DDRA/PORTG/DDRG, PORTD/DDRD, OC1M/OC1D and the chip-select registers.
Generated views were refreshed. This corrects CPU-layout metadata and does not
identify package markings or board wiring. ROM-backed access contracts remain
the stronger source than the broad listing inventory.

The hardware-test Markdown view now regenerates with its CSV instead of
retaining v0.2 counts and treating all source timer paths as active stock paths.
The repository hygiene check guards current navigation, retired CLI defaults,
Markdown links and stock-ROM identity.

The simulator profile now uses the same corrected passive CPU names/register
window, with modeled device behavior left unchanged. The standalone simulator
test command is documented from its package directory. The static-builder
verifier now invokes the scheduler and state-flow builders with their required
recorded-evidence mode instead of misclassifying them as zero-argument failures.
Temporary checkout paths are normalized in its saved report. Canonical CSV-only
checks also reproduce the repaired math-helper, boot-state and spark-slice exports.
The manual regeneration workflow refreshes both CSV/Markdown test views and
pushes to the selected branch, rather than always targeting main.

An additional 208-file CSV shape audit found 87 malformed rows across four
older contract exports. Math-helper and spark-slice indexes were regenerated
with their current builders; the calibration index was regenerated from the
supplied extract with proper CSV quoting. Seven boot-planning rows had an extra
output-description field; both descriptions are retained together and the
remaining schema is realigned in the source and output. The calibration builder
now requires its external source explicitly instead of defaulting to an absent
`/mnt/data` file. Touched generators emit LF records. CSV shape is now a hygiene
check, not an assumption.

## Preserved boundaries

- Current calibration values require the exact normal 0.3.12 image and matching
  observations. Old `2.bin` data remains a historical comparison.
- The C source retains 63 public routines,43 explicit unfinished dependency
  boundaries and its existing host verification scope. No new hardware driver
  or executable ROM modification is introduced by this cleanup.
- The stock ROM/listing, generated evidence needed by tests, legacy build
  proofs and intentional checked copy of the slot inventory are retained.
- The old local workspace contained three files older than their published
  versions, an interrupted generated file and an unpublished `factory_c`
  experiment. Copies of local edits/index state were preserved before cleanup;
  the audit used a separate checkout with a tree matching the published head.

## Verification

Local results: 190 factory tests, 16 simulator tests (including the real-ROM
checks), five C kernel check groups, 63 routine/file checks and 532 compiled-C
base-fuel cases passed. All 20 recorded factory/index checks passed. Static
artifact verification passed 17 runnable/canonical builders; 32 builders with
required parameters or external inputs were explicitly skipped, with no failures.
All 208 CSV files have consistent row widths, relative Markdown links resolve,
and retained prototype verifiers pass.

```sh
python tools/verify_repository_hygiene.py
python -m unittest discover -s tests -p 'test_factory_*.py' -v
python pseudo-source/tests/run_checks.py
python tools/verify_static_artifact_builders.py --write-report
python tools/verify_rom_bootstrap.py
python tools/verify_fuel_slice0_bench_harness.py
python tools/verify_fuel_slice0_bench_results.py
```

Run the simulator tests from `hac31_romsim/` with `python -m unittest discover -s tests -v`.

The factory workflow additionally checks recorded structural/controller/
ownership/timing evidence and regenerates its required artifacts. The C
workflow independently runs its CMake/CTest route. Passing repository checks
does not establish physical hardware behavior or whole-program equivalence.
