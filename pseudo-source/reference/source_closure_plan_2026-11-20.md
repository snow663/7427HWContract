# Connected pseudo-source closure plan — 2026-11-20

Repository `snow663/7427HWContract`; use only `work/pseudo-source-development`. It preserves the former `work/pseudo-source-closure` history and validated PR48 mainline. Old branch names below identify historical evidence, not another active branch.

## Release/branch policy

Work **in this order**, commit each coherent implementation group to the same branch, and run focused host checks where available. Do **not** open a PR, merge, rewrite main, or claim firmware/hardware validation during development. On the next explicit pull/merge request, review the entire accumulated diff, create **one** PR, run the full ROM, simulator, code-structure and source-contract suites, and merge only if they pass. Ordinary continuation does not authorize another release cycle.

The plan began with 321 routines and 69 CTests. As of November 23 there are
381 indexed routines (138 algorithms, 229 outlines and 14 explicit boundaries)
and 106 CTests (56 quick checks and 50 ROM suites).

## Ordered milestones

### M1 — Complete scheduled fuel/injector controller
- Port and verify the original `7D4B..7E4E` ignition/input prefix, including state/bit lifetimes, MAP transient/gear TPS, filtered O2, governor option and period/delay calculation.
- Reuse checked `7E4F..852B` calculation and sync/async publication **without skipping** predecessor or side effects.
- Implement the conditional `852C..8547` scheduled tail, respecting `0002.1/.2` phase selection, battery, EGR, O2/BLM and remaining producers.
- Connect the real `pcm_fuel_control` fast-dispatch admission, replace its dependency only after the entire path is callable, and compare selected complete foreground histories to stock ROM.
- Current status: **source-level milestone closed** (not target firmware complete). The joined `pcm_fuel_cycle` is callable from the actual fast entry under the explicit dual guarded research opt-in; after PR48 reconciliation the default `pcm_fuel_control` executes the resident PR48 path, while this independent cycle remains an alternative. Factory $7D4B..$8547 execution is independently replayed against the full, hash-identified BMHM ROM across **3,096 complete-entry selected and retained multi-cycle cases**, all eight phase groups, ignition/on/off transitions, denied and authorized fuel, battery, TPS/O2, 4-pass retained-state sequences, and injector output publication. The scoped $8EB4..$9166 governor and $7D4B ignition differentials also pass; synthetic optional $1809 A/carry return is covered but does not supply the actual external module. The [source/ROM development run](https://github.com/snow663/7427HWContract/actions/runs/44818450983) passes all **45 fast contracts and 3 focused ROM differential suites**. The real $1809 binary/firmware, physical board/ASIC transactions, target ISR/linker/RAM layout, and full all-path/no-interrupt-exclusion equivalence remain explicit M4/M5 or release-gate work; **do not claim a target BIN or physical validation**. See [joined source contract](fuel_cycle_joined_contract.md) and [RAM owner audit](fuel_ram_owner_audit.md).

### M2 — Close the remaining slow slots
- Original scope included slots 01, 03, 04, 05, 0A, 0B, 0C, 0D and 0F. Slots 01, 03, 0B and 0F now run resident C bodies. Five scheduled entries remain open: **04, 05, 0A, 0C and 0D**.
- Both 03 and 0B now call the complete `$D4EB` gear selector and `$C514` output routine on ordinary dispatch. Slot 03 first checks its optional external `$1806` module and publishes the `$0F00` marker. The November 23 replay covered all 602 reachable resident instruction starts in both entries and passed 4,216 comparisons overall. [Gear selection ROM ledger](transmission_d4eb_source_closure.md) · [Slot contracts](slow_slot_01_03_contract.md)
- Next close slot 04’s two alternating diagnostic groups and the shared `$006F` fuel-fault publication. Preserve the order of calls, state handoffs and failure exits for each slot.

### M3 — Resolve the eight-callee AE85 prefix and remaining current/transmission roots
- Port or explicitly eliminate each dependency only with a complete stock producer/consumer map.
- Preserve automatic transmission behavior in the stock-equivalent reference reconstruction; prepare separate manual-only feature selection.
- Current status: **queued after M2**.

### M4 — EGR and optional module closure
- Port four EGR producers/demand/flow/output controllers and inspect the optional `180C`, `180F`, `1812` dependencies with explicit dispatch policy. No guessed modules.
- Keep factory-reference implementation separate from later manual-only deletion.
- Current status: **EGR source closed in PR48**. All five demand/feedback/control/flow/output bodies are resident and checked on the combined tree. Optional180C/180F/1812 module execution, other admitted hooks and native interfaces remain open; do not report EGR itself as still delegated.

### M5 — Target execution and hardware contract
- Implement early `7100..711C` entry/vector and IRQ/RTI/stack-recovery ABI using compatible HC11 assembly.
- Resolve RAM address-provider ownership, interrupt ordering, memory and linker layout, peripheral/ASIC transactions and reset safety.
- Build a repeatable target BIN, verify memory fit/vector locations, then perform simulator and controlled physical output validation. Never infer physical proof from host tests alone.
- Current status: **queued after M4**.

## Source-of-truth rules

Factory source is the BMHM stock ROM, not ambiguous HAC comments. Consult literal instructions, bytes, branch targets and execution traces before porting routines. Preserve INT additive/P correction and BLM multiplicative application; do not replace them with two independent multipliers. Reuse established source bodies and named state owners rather than creating parallel RAM image state. Include ordinary, boundary, retained-history and failure-prefix witnesses for each stage.

`pseudo-source/routine_index.csv` is the authoritative public C routine inventory. Notes and old counts in `docs/WORKING_STATE.md` and `pseudo-source/README.md` can lag implementation; update them by milestones with evidence. Keep target/flash claims separate from C compilation and ROM-differential claims.

## Fast branch verification

The dedicated `.github/workflows/pseudo-source-fast-validation.yml` compiles
the host source and runs 56 quick checks and 16 selected ROM suites, including
the whole gear-slot comparison. The other 34 ROM suites run with the broader
repository workflows at the complete end-of-batch release gate.


## Cross-branch consolidation — 2026-11-22

The separate validated PR48 main history has been reconciled into this
closure branch through a two-parent commit, without opening a PR or
merging closure back to main. PR48's default resident fuel/slot01 sources
and the separately checked closure alternatives are preserved with
explicit admission flags. The updated source has 374 indexed routines
and 105 CTest entries. Its [focused combined-source CI](https://github.com/snow663/7427HWContract/actions/runs/45072057548)
passes **56 fast contracts and 15 selected ROM differentials**.
At that checkpoint, complete 49-ROM release verification, the D4EB middle
segment, seven slow-slot roots and the native HC11 hardware ABI were open.
See [source conflict and validation ledger](reconciliation_2026-11-22.md).
