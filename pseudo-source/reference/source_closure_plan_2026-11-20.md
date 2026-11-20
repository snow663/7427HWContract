# Connected pseudo-source closure plan — 2026-11-20

Repository `snow663/7427HWContract`; cumulative branch `work/pseudo-source-closure` from main after merged PR #47 (merge `aadb9eca7891a5cadcbd8869b0c75efe94feb096`).

## Release/branch policy

Work **in this order**, commit each coherent implementation group to the same branch, and run focused host checks where available. Do **not** open a PR, merge, rewrite main, or claim firmware/hardware validation during development. Once all five milestones have implementation evidence, review the entire diff, create **one** PR, run the full ROM, simulator, code-structure and source-contract suites, and merge only if they pass.

This is an execution ledger, not an assertion of completed work. Existing routine counts are 321: 109 implemented algorithms, 189 implemented outlines, 23 explicit boundaries; CMake currently registers 69 CTest checks. The previous main revision passed all five PR #47 CI workflows. Any new source change must be reverified.

## Ordered milestones

### M1 — Complete scheduled fuel/injector controller
- Port and verify the original `7D4B..7E4E` ignition/input prefix, including state/bit lifetimes, MAP transient/gear TPS, filtered O2, governor option and period/delay calculation.
- Reuse checked `7E4F..852B` calculation and sync/async publication **without skipping** predecessor or side effects.
- Implement the conditional `852C..8547` scheduled tail, respecting `0002.1/.2` phase selection, battery, EGR, O2/BLM and remaining producers.
- Connect the real `pcm_fuel_control` fast-dispatch admission, replace its dependency only after the entire path is callable, and compare selected complete foreground histories to stock ROM.
- Current status: **in progress**. The resident `pcm_fuel_cycle` now composes stock $7D4B..$8547 ignition/input, running/crank admission, delivered pulse and phase-selected tail. The full $8EB4..$9166 governor is resident. Named RAM ownership is now available through a **tested opt-in** `PcmPlatform.bind_fuel_ram_owners` bridge, with no change to the default backing provider or fast dispatcher. The complete joined C path passed an authorized running injection test, eight phase values with an unauthorized zero packet, ignition terminal branch and selected I/O failures. [CI run 44748475806](https://github.com/snow663/7427HWContract/actions/runs/44748475806) passes **45 fast contracts and both dedicated BMHM governor/ignition ROM comparisons**. Full $7D4B..$8547 independent ROM parity, complete peripheral/shared-RAM provider, optional $1809 heads-up module and physical target entry remain open; **`PCM_FUEL_CONTROL` is not yet activated**. See [RAM owner audit](fuel_ram_owner_audit.md) and [joined C contract](fuel_cycle_joined_contract.md).

### M2 — Close the nine remaining slow slots
- Port 01/03/04/05/0A/0B/0C/0D/0F one by one from the ROM; include state sharing and failure prefixes.
- Replace each `pcm_run_task` boundary only when the slot's required producers have been supplied.
- Current status: **queued after M1**.

### M3 — Resolve the eight-callee AE85 transmission prefix and five remaining current/transmission roots
- Port or explicitly eliminate each dependency only with a complete stock producer/consumer map.
- Preserve automatic transmission behavior in the stock-equivalent reference reconstruction; prepare separate manual-only feature selection.
- Current status: **queued after M2**.

### M4 — EGR and optional module closure
- Port four EGR producers/demand/flow/output controllers and inspect the optional `180C`, `180F`, `1812` dependencies with explicit dispatch policy. No guessed modules.
- Keep factory-reference implementation separate from later manual-only deletion.
- Current status: **queued after M3**.

### M5 — Target execution and hardware contract
- Implement early `7100..711C` entry/vector and IRQ/RTI/stack-recovery ABI using compatible HC11 assembly.
- Resolve RAM address-provider ownership, interrupt ordering, memory and linker layout, peripheral/ASIC transactions and reset safety.
- Build a repeatable target BIN, verify memory fit/vector locations, then perform simulator and controlled physical output validation. Never infer physical proof from host tests alone.
- Current status: **queued after M4**.

## Source-of-truth rules

Factory source is the BMHM stock ROM, not ambiguous HAC comments. Consult literal instructions, bytes, branch targets and execution traces before porting routines. Preserve INT additive/P correction and BLM multiplicative application; do not replace them with two independent multipliers. Reuse established source bodies and named state owners rather than creating parallel RAM image state. Include ordinary, boundary, retained-history and failure-prefix witnesses for each stage.

`pseudo-source/routine_index.csv` is the authoritative public C routine inventory. Notes and old counts in `docs/WORKING_STATE.md` and `pseudo-source/README.md` can lag implementation; update them by milestones with evidence. Keep target/flash claims separate from C compilation and ROM-differential claims.

## Fast branch verification

The dedicated `.github/workflows/pseudo-source-fast-validation.yml` runs
only host C compilation, contracts and provenance on updates to this cumulative
source branch. It explicitly excludes `rom_differential` jobs and cancels
superseded branch runs. The full 34 ROM comparison suites and broader GitHub
checks remain the single-PR release gate, not a per-commit development tax.
