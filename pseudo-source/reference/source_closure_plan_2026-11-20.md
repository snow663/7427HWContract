# Connected pseudo-source closure plan — 2026-11-20

Repository `snow663/7427HWContract`; use only `work/pseudo-source-development`. It preserves the former `work/pseudo-source-closure` history and validated PR48 mainline. Old branch names below identify historical evidence, not another active branch.

## Release/branch policy

Work **in this order**, commit each coherent implementation group to the same branch, and run focused host checks where available. Do **not** open a PR, merge, rewrite main, or claim firmware/hardware validation during development. On the next explicit pull/merge request, review the entire accumulated diff, create **one** PR, run the full ROM, simulator, code-structure and source-contract suites, and merge only if they pass. Ordinary continuation does not authorize another release cycle.

This is an execution ledger, not an assertion of completed work. At plan creation the inventory was321 routines and69 CTests. The current combined inventory is374 routines:131 algorithms,227 outlines and16 explicit boundaries;105 CTests comprise56 quick checks and49 ROM suites. The previous main revision passed all five PR #47 CI workflows. Any new source change must be reverified.

## Ordered milestones

### M1 — Complete scheduled fuel/injector controller
- Port and verify the original `7D4B..7E4E` ignition/input prefix, including state/bit lifetimes, MAP transient/gear TPS, filtered O2, governor option and period/delay calculation.
- Reuse checked `7E4F..852B` calculation and sync/async publication **without skipping** predecessor or side effects.
- Implement the conditional `852C..8547` scheduled tail, respecting `0002.1/.2` phase selection, battery, EGR, O2/BLM and remaining producers.
- Connect the real `pcm_fuel_control` fast-dispatch admission, replace its dependency only after the entire path is callable, and compare selected complete foreground histories to stock ROM.
- Current status: **source-level milestone closed** (not target firmware complete). The joined `pcm_fuel_cycle` is callable from the actual fast entry under the explicit dual guarded research opt-in; after PR48 reconciliation the default `pcm_fuel_control` executes the resident PR48 path, while this independent cycle remains an alternative. Factory $7D4B..$8547 execution is independently replayed against the full, hash-identified BMHM ROM across **3,096 complete-entry selected and retained multi-cycle cases**, all eight phase groups, ignition/on/off transitions, denied and authorized fuel, battery, TPS/O2, 4-pass retained-state sequences, and injector output publication. The scoped $8EB4..$9166 governor and $7D4B ignition differentials also pass; synthetic optional $1809 A/carry return is covered but does not supply the actual external module. The [source/ROM development run](https://github.com/snow663/7427HWContract/actions/runs/44818450983) passes all **45 fast contracts and 3 focused ROM differential suites**. The real $1809 binary/firmware, physical board/ASIC transactions, target ISR/linker/RAM layout, and full all-path/no-interrupt-exclusion equivalence remain explicit M4/M5 or release-gate work; **do not claim a target BIN or physical validation**. See [joined source contract](fuel_cycle_joined_contract.md) and [RAM owner audit](fuel_ram_owner_audit.md).

### M2 — Close the remaining slow slots
- Original scope:01/03/04/05/0A/0B/0C/0D/0F. Slots01 and0F are now resident; finish03/04/05/0A/0B/0C/0D with state sharing and failure prefixes.
- Replace each `pcm_run_task` boundary only when the slot's required producers have been supplied.
- Current status: **in progress**. Slot01 ($7AAD) has all three resident source callees ($C583 BARO, $C668 speed source, $ADAA non-electronic TCC) in stock order under guarded slow-slot admission; default behavior unchanged. Slot03 ($7ABD) has the optional $1806 gate/$0F00 publication, then still calls the full $D4EB transmission dependency before resident $C514 outputs. The **$D4EB–$D4F7 diagnostic prefix**, shared $E6BC nine-entry masks, **$E562 gear limit**, **$D5B7–$D69E gear arbitration**, and **$D8CE pointer threshold selector** now have resident C algorithms independently stock-ROM-verified. The unfinished middle $D4F7–$D5B6 with $D8F0/$D8FE/$D840/$D8A7/$D7E5 must be joined before replacing the whole $D4EB callback. Slot0F is complete through its diagnostic/fault/fuel suffix. Slots03/04/05/0A/0B/0C/0D retain explicit dependencies. The earlier [focused branch gate](https://github.com/snow663/7427HWContract/actions/runs/45004479765) passes **51 fast contracts and 9 ROM differentials**. The current combined gate has49 ROM suites, of which15 have passed together;34 remain outside that run. The complete run remains the one-PR release gate. See [M2 specific ROM ledger](transmission_d4eb_source_closure.md) and [slot contracts](slow_slot_01_03_contract.md).

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
the host source, runs56 quick contracts/provenance checks and15 selected ROM
suites, and cancels superseded branch runs. It does not run all49 ROM suites.
The remaining34 comparisons and broader repository workflows belong to the
complete end-of-batch release gate.


## Cross-branch consolidation — 2026-11-22

The separate validated PR48 main history has been reconciled into this
closure branch through a two-parent commit, without opening a PR or
merging closure back to main. PR48's default resident fuel/slot01 sources
and the separately checked closure alternatives are preserved with
explicit admission flags. The updated source has 374 indexed routines
and 105 CTest entries. Its [focused combined-source CI](https://github.com/snow663/7427HWContract/actions/runs/45072057548)
passes **56 fast contracts and 15 selected ROM differentials**.
Complete 49-ROM release verification, D4EB's unported middle segment,
the seven remaining slow-slot roots and native HC11 hardware ABI remain open.
See [source conflict and validation ledger](reconciliation_2026-11-22.md).
