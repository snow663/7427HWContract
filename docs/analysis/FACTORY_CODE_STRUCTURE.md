# Factory-code structure and tracing

This work extends understanding of the factory `$31`/BMHM program, including factory transmission, emissions, service, and diagnostic code. Replacement-OS implementation, GUI features, and simulator feature counts are outside this assessment.

## Evidence and completion

Keep these accomplishments separate:

| Level | Required evidence |
|---|---|
| Structure | Reviewed code/data boundaries; real entry points; branch/call targets; explicit unresolved references |
| State and dependencies | Producers, readers, byte/word aliases, bit consumers, indexed users, initialization, and reset paths |
| Semantics | Purpose of the routine/state, branch qualifications, execution context, and effects on other factory functions |
| Exact integer behavior | Signedness, rounding, saturation, overflow, carry/borrow, lookup geometry, and persistent-state transitions |
| Validation | ROM-byte correspondence and independently checked execution/replay; physical effects confirmed where necessary |

A populated CSV row is enumeration evidence. It is not proof of semantic understanding. A function copied unchanged is not automatically understood. Source comments and inherited HAC names remain hypotheses where executable use has not confirmed them.

No percentage is produced by this pass. An all-program percentage requires a reviewed denominator and a status/evidence ledger for every included region/function. The earlier conversational 85–90% estimate was qualitative, not an audited coverage metric.

## Actual-ROM verification

The reviewed descriptor block and its principal callers/reader are now checked against the actual hash-identified stock BMHM ROM. See `FACTORY_ROM_STRUCTURE_PROOF.md` and `maps/structure/bmhm_rom_structure_evidence.json` for the raw byte evidence. All 144 descriptor words are recorded in `bmhm_rom_lookup_pointers.csv`; all 72 nonzero entries point into calibration space. This verifies the reviewed data use without claiming that all code/data overlap or whole-ROM reachability has been excluded.

## First completed structural correction

`$C2D6-$C409` is 308 bytes of lookup descriptors/pointers, divided into ten blocks in `maps/structure/reviewed_source_regions.csv`. The evidence is the immediate/computed table bases and the actual reader routines, not the disassembler's apparent mnemonics.

| Bases | Caller evidence | Consumer |
|---|---|---|
| `$C2D6`, `$C2F8`, `$C31A`, `$C33C` | `$C849`, with optional `$44` and `$22` additions | `$D8FE` through `$C85F`/`$C872` |
| `$C35E` | `$C06D` | `$D8FE` at `$C074` |
| `$C380` | `$C19F` | `$D8FE` at `$C1A6` |
| `$C3A2` | `$C088` | `$D8FE` at `$C08F` |
| `$C3C4` | `$C1C4` | `$D8FE` at `$C1CB` |
| `$C3E6`, `$C3F8` | `$C881`, optional `$12` addition | `$D92E`, which calls `$D8FE` |

`$D8FE-$D92D` reads the descriptor header, selects an indexed pointer, reads that pointer, and returns with carry indicating failure/success. This is data access. The reader does not execute the apparent instructions in these tables. Extents follow the independently loaded/computed next bases and the next source routine at `$C40A`; the descriptor bytes and header-derived extents have now been verified against the actual BMHM ROM.

Consequences of excluding the reviewed data:

- Eight apparent dispatchers inside `$C3A2` disappear. Two real indexed call sites remain: `$7A4F` and `$FAA5`.
- The major-loop table still supplies 16 landing addresses. The dispatcher CSV contains 17 rows because one site expands to 16 entries and the other remains unresolved.
- The write sweep falls from 2,215 to 2,187 rows: 28 false mutation records are removed.
- Grouped write-target dossiers fall from 793 to 771. This removes 22 misleading target entries; it does not newly explain 22 factory variables.

The original HAC listing is preserved unchanged. The overlay is pinned to its SHA-256, normalizing line endings for Windows checkouts, and rejects reuse against a different listing until the evidence is reviewed.

## New source indexes

| File under `maps/structure/` | Purpose and limit |
|---|---|
| `reviewed_source_regions.csv` | Manually reviewed data ranges, source hash, evidence PCs, and reasons |
| `factory_listing_review.csv` | Declared data, reviewed embedded data, undecoded entries, and TEST-opcode review candidates |
| `factory_entry_points.csv` | 257 candidate entry addresses from direct calls, source vectors, and the traced scheduler table; function extents/reachability are not proven |
| `factory_control_edges.csv` | 4,521 explicit control references; includes unresolved operands rather than dropping them; no implicit fallthrough graph |
| `factory_memory_accesses.csv` | 6,744 explicit memory-access sites, distinguishing reads, writes, and read/modify/write |
| `factory_state_index.csv` | Byte-overlap index of direct accesses, including both bytes of word operations; includes RAM, ROM, and hardware regions |
| `factory_structure_summary.json` | Reproducible inventory counts and evidence hashes; no understanding percentage |
| `factory_re_worklist.csv` | Reviewed findings and open investigation scopes |

Of the access sites, 5,706 are direct and 1,038 retain unresolved indexing. An immediate constant, a call destination, and a branch destination are not counted as variable reads. Bit branches produce a state read and a separate control reference. Indexed access is never assigned an address from an unrelated earlier immediate X/Y load.

These indexes intentionally do not establish register-to-register value propagation, transitive consumer edges, implicit stack accesses, cross-call pointer effects, interrupt ownership, all code reachability, or semantic completion. The legacy write-target index still uses coarse linear index tracking; use the new direct-access index for precise direct R/W counts.

The source-only parser preserves an inherited defect: `$A40B` names `LA4656` as a branch destination. This is an unresolved direct operand in that index, not a third indirect dispatcher. The newer nested ROM trace verifies `$A465` as the actual target and checks both branch outcomes on the CPU; integrating that correction into the source-only index remains separate work. Two branch lines with colon-delimited comments are parsed without absorbing those comments into the target operand.

## How to extend understanding

1. **Close code/data and entry structure.** Start at vectors and confirmed table consumers. Add small evidence-backed ranges. Resolve conflicting references and malformed targets. Build basic blocks/reachability with unresolved edges visible; do not call everything after the latest label one function.
2. **Trace backward from factory outputs.** Prioritize synchronous/async fuel, spark, and idle output paths. For each input state, collect every producer, direct and indexed reader, initialization, reset, override, and interrupt update. Preserve word overlap and bit-specific consumers.
3. **Close one bounded path at a time.** Record exact inputs, outputs, flags, side effects, callers, cadence, and persistent state. Identify all direct exits and exceptional branches. A declaration of purpose alone does not close the path.
4. **Reduce the actual integer operations.** Preserve carry, borrow, wrapping, signed branch conditions, lookup fractions, clamps, and startup differences. Keep engineering units and hardware effects distinct from the integer transformation.
5. **Check predictions independently.** Compare against target ROM bytes, isolated execution, or sufficiently complete replay data. An undocumented state/input is a remaining dependency. A generator reproducing its own equation is not independent validation.
6. **Extend across the whole factory scope.** Include transmission, emissions, service, and complete diagnostic behavior before claiming whole-program understanding. Review disconnected code and data explicitly instead of dropping it because the truck does not use it.

The next engine-focused path is the spark rolling-state bridge. Its `$01EC` producer is now traced in `../contracts/SPARK_L01EC_INTEGER_STATE.md`: two direct writes and four direct reads establish a concrete path into `$3FE6/$3FDC`. Next close `$083F/$01EA`, the stack-based postprocessing at `$AB89-$ABC8`, and first-event/reset behavior. Fuel `$024E` and its indirect multiply/helper updates follow; the index alone is not enough to close them.

## ROM-backed scheduler extension

`FACTORY_SCHEDULER_MAP.md` now closes the bounded dispatch/call-selection model:
all 16 slots, fast phase-bit groups, startup's first slot F, busy reentry and
coalesced pending work, profiling arithmetic, and the RAM callback at `$FAA5`.
The 18 scheduler tests execute the actual captured instructions using the
existing CPU, with external callee effects stubbed and fixture-controlled
hardware. They are independent of the new map decoder and its guard formulas.

The companion maps add explicit local fallthrough/control edges, gate-producer
candidates checked against bytes, and intraprocedural state inventories for 63
direct callee roots. Their 262 unresolved indexed-access rows use a different
scope from the 1,038 whole-listing rows above; they are not an updated global
unresolved count. Nested calls, indexed writes, and physical scheduling latency
remain dependencies.

The new ROM comparison also records 32 listing discrepancies, including code at
`$E75F` declared as data and misaligned entries at `$B32D`, `$B99F`, and `$F3E4`.
The older source indexes above have not been rewritten from these byte overlays.
For covered instructions the ROM-backed maps are the stronger evidence. Full
integration of the corrections is a separate worklist item.

`FACTORY_NESTED_STATE_FLOW.md` now extends the scheduler across nested calls and
register-return templates to 234 entries. Its indexed-flow map resolves 216 of
the previous 262 per-root rows to addresses/sets and keeps the remaining frame,
parameter, pruned, and unresolved categories explicit. It also byte-verifies
the `$A40B -> $A465` branch and captures indexed clear/mask state producers.
The older whole-listing source counts above remain unchanged; these new results
do not silently change their denominator or establish whole-ROM semantics.

## Reproduce and verify

From the repository root:

```bash
python tools/build_factory_structure.py
python tools/build_full_rom_write_target_sweep.py
python tools/build_per_target_dossier_index.py
python tools/build_dispatcher_reverse_map.py
python tools/build_write_target_network_index.py
python tools/build_subsystem_isolation_index.py
python -m unittest discover -s tests -p test_factory_structure.py -v
python tools/build_factory_structure.py --check
```

The tests cover data/code confusion, retention of real dispatchers and injector writes, evidence-hash mismatch, word-byte overlap, bit-branch classification, malformed source labels, and unresolved indexed accesses. They validate the structural extraction, not factory physical behavior.
