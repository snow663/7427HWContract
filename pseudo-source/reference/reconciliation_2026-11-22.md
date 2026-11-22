# Reconciliation of PR48 main and cumulative pseudo-source closure

Date: 2026-11-22

Git parents:
- Validated `main`: `ca22491e362ce039ff785f736a9457258066356f`
- Closure branch: `12d6b7aa069319f5fe4f514a57097eb1237df799`
- Common ancestor: `aadb9eca7891a5cadcbd8869b0c75efe94feb096`

This is a **two-parent source integration onto work/pseudo-source-closure**,
not a PR merge to `main`. It brings all upstream revisions into the
development branch ancestry, preserving independent commit provenance.

## Decisions on overlapping source

Eleven paths were changed on both sides. Others from `main` are carried
over unchanged by their existing Git object identity.

- `pcm_fuel_control`: preserve PR48's resident ignition/input/fuel/tail
  call sequence as the default source execution. The separately ROM-tested
  closure `pcm_fuel_cycle` remains selectable with both
  `enable_resident_fuel_cycle` and `bind_fuel_ram_owners` true.
- `pcm_slot_01`: PR48's resident C583→transmission BARO→nonelectronic
  TCC remains the default source path. The independently tested closure
  C583→speed_source→tcc_non_electronic path is retained under
  `enable_resident_slow_slots`, with no source-register call duplication.
- `pcm.h`: retain all named governor/fuel RAM owners, all three guarded
  platform flags and the typed `PcmGovernor` extension interface. Add the
  mainline `PCM_STOP_BOUNDARY` status and `PCM_GOVERNOR_EXTENSION` task
  without reassigning existing closure task indices. A target ABI must not
  assume C enum values equal factory ROM table entries.
- `governor_internal.h`: keep both independently implemented F4B6/F550
  and capped-curve helpers with their original prefixed names; those
  helpers are exercised by separate actual-ROM differential suites.
- `control.h` and `fuel.h`: retain both declaration families.
- `routine_index.csv`: union unique source paths, promote source-backed
  mainline routines that supersede old closure dependency boundaries,
  retain the closure's independently verified gear algorithms.
- `CMakeLists.txt` and `tests/run_checks.py`: union mainline EGR, fuel,
  slot-F and timer-stack-guard ROM contract suites with all additional
  closure fast fixtures and actual-ROM differentials. Preserve historical
  substitution-stub boundaries for older individual-source tests.
- Documentation: preserve PR48's validated release evidence and the
  closure's source inventory, with merged-tree verification tracked
  separately from either parent's result.

### Merged source inventory

Expected: **374 indexed public routines** (227 implemented outlines,
131 implemented algorithms, 16 named dependency boundaries);
**105 registered CTest entries** including **49 ROM differentials**.
Counts describe source coverage, not target execution readiness.

### Remaining target and source risks

Both branches port some of the same source addresses with different
function names. They are *alternatives*, not two routines to schedule
consecutively. In particular, D8xx transmission thresholds and governor
lookup helpers must remain separately tested until one canonical hardware
contract is chosen.

The optional $1806/$1809/$1815 modules, PCM-specific RAM/peripheral
provider, physical output authorization, interrupt/vector behavior and
native HC11 BIN/linker ABI remain unresolved. Slot03 $D4F7–$D5B6
transmission selection also remains a named source dependency.
The source merge does **not** flash any PCM or change a truck calibration.

### Verification rule

PR48's 80-CTest run and closure's 94-CTest focused history belong to
different trees. Do not claim they validated this merge. Record the
new merged commit and its own focused/complete CI here after actually
observing their results. Do not open a PR or merge to main without a
separate explicit request.
