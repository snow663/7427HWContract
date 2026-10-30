# Maps

Machine-readable maps, generated access inventories, current runtime-analysis tables, frozen planning manifests, and source-derived trace indexes.

## Factory-code structure

`maps/structure/` contains the reviewed code/data overlay, source entry-point evidence, control-flow references, and direct memory read/write indexes. Use `docs/analysis/FACTORY_CODE_STRUCTURE.md` for the interpretation and next tracing order.

The first reviewed data block is `$C2D6-$C409`. The dispatcher/write-target builders consume that overlay. Older broad hardware-access maps are coarse inventories and may still contain data-as-code rows; they do not override this reviewed classification or measure semantic completion.

`factory_scheduler_*.csv` and `bmhm_scheduler_rom_evidence.json` add actual-ROM
slot words, conditional call order, local control/state edges, direct writer
candidates, and one-level callee state inventories. See
`docs/analysis/FACTORY_SCHEDULER_MAP.md` for execution tests and scope limits.
The scheduler's listing-discrepancy map records code hidden by malformed or
misaligned HAC rows. The reviewed corrections now flow into the effective main and legacy indexes;
`factory_rom_overlay_audit.csv` records each replacement/suppression. The original
HAC remains unchanged.

`factory_nested_*.csv`, `factory_indexed_flow.csv`,
`factory_indexed_clear_calls.csv`, and `factory_masked_state_updates.csv` extend
the scheduler through nested calls. They distinguish exact/bounded addresses,
frame-relative and caller-parameter accesses, known effects, and opaque hooks.
The full-image/excerpt evidence is `bmhm_nested_state_rom_evidence.json`.
See `docs/analysis/FACTORY_NESTED_STATE_FLOW.md` for the 262-row baseline
accounting, verified helper footprints, validation, and remaining boundaries.

`factory_spark_*.csv` and `bmhm_spark_rom_evidence.json` add the exact normal
spark handoff, producer dependencies, five local-stack proofs, and raw-input
review vectors. `FACTORY_SPARK_INTEGER_HANDOFF.md` documents byte authority,
independent execution, initialization, update admission, and remaining limits.
Legacy write consumers use the nested flow for indexed addresses; they retain
bounded sets, stack frames, and unresolved cases instead of a linear last-load
estimate.

`factory_fuel_*.csv` and `bmhm_fuel_rom_evidence.json` support the completed
running-fuel documentation in `FACTORY_FUEL_INTEGER_HANDOFF.md`: exact bytes,
explicit memory references, state dependencies, and raw-state examples. The
document distinguishes calculations, retained telemetry words, sync/async
selection, and ordered device writes, with upstream boundaries stated directly.

`factory_upstream_*.csv` and `bmhm_upstream_rom_evidence.json` complete the
resident engine-calculation producer documentation: 50 reviewed blocks,
3,403 decoded instruction starts, 826 branch rows and 54 selected state
contracts. Use `FACTORY_ENGINE_CALCULATION_CLOSURE.md` for the checklist,
shared math, cadence, initialization and raw/cross-controller interfaces.
The state audit distinguishes direct ROM stores from other source-index
candidates, including `$B968` lookup-pointer data. It does not assert that the
global listing index is entirely byte-reviewed. External `$1800/$1812/$1815`
calls retain explicit boundaries. Reproduce with
`python tools/verify_factory_upstream.py --check-recorded` or a full `--rom`.

`factory_idle_governor_*.csv`, `factory_rpm_vss_consumers.csv` and
`bmhm_idle_governor_rom_evidence.json` complete the resident IAC/RPM/VSS/governor
documentation. The 45 spans contain 2,876 instruction starts and 816 branch rows;
25 local CFG roots, 100 selected states and the retained-cell layout make the
state/output boundaries reviewable. The direct VSS-reader ledger contains 39
ROM-checked sites. All39 now link to completed contracts following the DTE
extension; the initial IAC/speed pass left9 of these peripheral owners open. Seventeen covered listing
differences remain local byte authority rather than a claim that the entire
global source overlay is corrected. Use `FACTORY_IDLE_SPEED_CONTROL_CLOSURE.md`
and `python tools/verify_factory_idle_governor.py --check-recorded` (or `--rom`).

## Listing-derived hardware-access outputs

```text
maps/current/hardware_access_map_hw_only.csv
maps/current/hardware_test_matrix.csv
maps/current/HARDWARE_TEST_MATRIX.md
maps/full/hardware_access_map_v0.3.csv
```

`maps/full/hardware_access_map_v0.3.csv` is the retained full generated listing-access map. Historical `maps/by_subsystem/` splits have their own frozen scope in `maps/by_subsystem/SPLIT_INDEX.md`; they are not the current query defaults.

The superseded v0.2 full export has been retired; its identity is recorded in `maps/maintenance/retired_artifacts.csv`. Active query/build defaults use v0.3. Both are listing-derived inventories; ROM-backed `maps/structure/factory_global_hardware_accesses.csv` is the stronger hardware access authority.

The hardware-map regeneration workflow explicitly targets v0.3.

## Current truck-runtime analysis maps

```text
maps/analysis/bin2_vss_consumer_audit.csv
```

The `bin2_*` maps describe the historical `2.bin` snapshot. The user restored the regular0.3.12 tune after the readback test; current calibration-byte facts require that exact normal image. See `docs/WORKING_STATE.md`.

## Source-trace index

```text
maps/source_trace/README.md
```

This records provenance for the broader `$31` HAC raw-source trace package and its ORG/data/XDF-seed inventories.

Source-derived rows are evidence/index material. Do not promote guessed scaling, inherited XDF naming, or unverified engineering units into contracts merely because a row exists in a trace CSV.

## Frozen planning maps

```text
maps/planning/*.csv
maps/telemetry/v1_*.csv
```

These preserve the earlier V1 design. They are historical planning inputs and do not constrain the active `pseudo-source/` design unless explicitly adopted.

## Regeneration rule

Use split/current views for normal review. Regenerate broad static maps when analyzer logic or the underlying source input changes. Git history is the version record.


`factory_dte_*.csv` and `bmhm_dte_rom_evidence.json` document resident diagnostic,
transmission and emissions software. Start at
[the closure ledger](../docs/analysis/FACTORY_DIAGNOSTICS_TRANSMISSION_EMISSIONS_CLOSURE.md).
The62 spans contain7,628 instruction starts and2,027 branches;142 local CFG
roots and153 selected state roles retain their scoped evidence level. The
transmission maps distinguish20 header-based priority descriptors from35 direct
pointer arrays. `factory_diagnostic_bits.csv` derives all72 flash-code identities
and mask/bank mappings from bytes. These are not counts of disjoint understood
functions or a whole-ROM completion percentage. Twelve local listing differences
remain separate from the global partial overlay. The direct VSS-reader ledger
now links all39 previously enumerated sites to contracts.
