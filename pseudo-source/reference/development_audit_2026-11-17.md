# Pseudo-source development audit — 2026-11-17

Repository: `snow663/7427HWContract`. Active continuation branch:
`work/pseudo-source-development`. Base: `main`. Do not open an additional
PR or merge until the user explicitly requests pull/check/merge.

## Source inventory

At this audit checkpoint, `routine_index.csv` contained **321 indexed public C
routines**, with one public routine per `src/*.c`:

| Class | Count | Interpretation |
|---|---:|---|
| Implemented algorithm | 109 | Callable arithmetic/control algorithm with scoped verification |
| Implemented outline | 189 | Callable resident behavior; may require platform/provider/target work |
| Dependency boundary | 23 | Explicitly absent producer/controller/external behavior |

Neither 298 callable routines nor 321 indexed routines measure ROM-byte
equivalence or target readiness. Calibration and C host layouts remain distinct
from the installed 16197427 firmware image.

The 23 indexed dependency boundaries are: four EGR
(demand/flow/control/output); one broad fuel controller at7D4B; nine slow slots
(01/03/04/05/0A/0B/0C/0D/0F); two optional spark extension bodies (1812/180F);
one early reset-assembly entry; five transmission/current paths
(current, pressure/TCC, shift, transmission spark, eight-callee AE85 prefix);
and one optional 180C connection-probe path.

## Completed but unmerged groups

Merged source PRs30,45,46 established retained service, working RAM init and
factory admission. Subsequent committed branch groups contain retained boot,
controller seeding, recurring factory execution, foreground refresh and
interrupt leaves. Their focused C/ROM suites total **15,611 recorded
comparisons** and the branch had68 registered CTest entries immediately before
this audit. These results were recorded during development; they are not a new
end-to-end regression on the current branch.

The next instruction range,7959..7979, is now represented by
`pcm_timer_stack_guard` and a new host contract fixture. It captures the two
stock X bounds, a fresh004F busy test, recovery003A.3 and004F.2 writes, and
the separate target stack-reset handoff. This adds one registered CTest check
(**69 total**). The new fixture defines131072 threshold decisions plus provider
failure/mutation cases. **Do not report these as executed/passed until a
reproducible runner confirms them.** The existing periodic IRQ still delegates
stack entry/recovery to `PcmPlatform.check_stack`.

## Open boundaries blocking a target ROM

1. Early HC11 assembly and vector/RTI ABI, including TSX observation, LDS #03F6
   recovery, factory SP reset, WAI wake and busy/pending reentry.
2. Actual target linker/memory layout, RAM ownership mapping and physical
   read/write/chip-select/ASIC peripheral behavior and timing.
3. Required resident producers and caller admission to replace the broad fuel
   controller, ending at the actual scheduled injector output paths.
4. Remaining system/transmission prefix and optional-module code where admitted.
5. Whole-source/ROM differential run and previously accumulated tests, then
   target image build and controlled physical validation.

## Regression and release rule

Run the quick gate first:
`python pseudo-source/tests/run_checks.py --contracts-only`.
The comprehensive `run_checks.py` path and CMake/CTest jobs remain deferred
until the user's explicit pull/check/merge instruction. The earlier simulator
correction to unsigned indexed offsets must participate in the next complete
ROM comparison. Treat all source-level checks and host test results separately
from target BIN generation and physical injector/spark output behavior.

Unrelated open PR21 (VSS filter) and PR42 (Rev B register/read/write documents)
are not the current pseudo-source branch; both diverged from current main at
this audit and require reconciliation before a future merge.

## Later validation checkpoint

On2026-11-22 the guard host contracts and6,056 focused actual-ROM comparisons
were executed and passed; the kernel recovery join now binds busy/fault/pending
owners coherently. This supersedes the unexecuted-test caveat above for that
scope only. The branch now has70 registered CTest checks. See the current
[timer guard contract](timer_stack_guard_contract.md) and
[working state](../../docs/WORKING_STATE.md); full regression remains deferred.

The following2026-11-22 group replaces the EGR control/output boundaries with
resident C. It passes2,662 focused actual-ROM comparisons across all90 new
scoped starts, including the real position-feedback join. Current inventory
is321 routines:191 implemented outlines,21 dependency boundaries and109
implemented algorithms. EGR demand/flow remain boundaries. There are72 CTest
registrations; see the [EGR control contract](egr_control_contract.md).

The subsequent demand/flow group passes 8,950 focused actual-ROM comparisons
across all 323 new scoped starts, with real fraction-to-fuel/spark consumers.
Current inventory is 321 routines: 193 implemented outlines, 19 dependency
boundaries and 109 algorithms. All five EGR bodies are resident; optional1815
and target execution remain explicit. There are 74 CTest registrations; see the
[EGR producer contract](egr_producers_contract.md). Full regression is deferred.

The following scheduled-fuel group closes the7D4B controller boundary and adds
five public ignition/input/tail/governor entries. Current inventory is326 routines:
199 implemented outlines,18 dependency boundaries and109 algorithms. Its16,493
focused comparisons cover389 new software starts and real controller/REF joins;
the source now registers76 CTest checks. See the
[fuel controller contract](fuel_controller_contract.md). STOP, optional module,
remaining slow-slot producer and target backend work remain separate.

The following slow-producer group closes slot1 and adds eight public entries
for transmission BARO/TCC, pump/slow fuel, fault reactions and the slotF suffix.
Current inventory is334 routines:208 outlines,17 boundaries and109 algorithms.
Its22,168 focused C/ROM cases cover234 scoped starts and437 failed prefixes;
the existing16,493-case controller checks also pass. There are78 CTest entries.
See the [slow fuel contract](slow_fuel_contract.md); the C4F5 prefix, whole
slotF admission and slot4 callers remain explicit. Full regression is deferred.
