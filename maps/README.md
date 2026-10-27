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

## Current hardware-access outputs

```text
maps/current/hardware_access_map_hw_only.csv
maps/current/hardware_test_matrix.csv
maps/current/HARDWARE_TEST_MATRIX.md
maps/full/hardware_access_map_v0.3.csv
maps/by_subsystem/*.csv
```

`maps/full/hardware_access_map_v0.3.csv` is the current full generated static-access map.

`maps/full/hardware_access_map_v0.2.csv` is retained only as historical generated evidence. It must not be treated as newer authority than v0.3.

The hardware-map regeneration workflow explicitly targets v0.3.

## Current truck-runtime analysis maps

```text
maps/analysis/bin2_vss_consumer_audit.csv
```

For current truck behavior, `2.bin` is the running calibration-value authority. See `docs/WORKING_STATE.md`.

## Source-trace index

```text
maps/source_trace/README.md
```

This records provenance for the broader `$31` HAC raw-source trace package and its ORG/data/XDF-seed inventories.

Source-derived rows are evidence/index material. Do not promote guessed scaling, inherited XDF naming, or unverified engineering units into contracts merely because a row exists in a trace CSV.

## Frozen planning maps

```text
maps/planning/*.csv
maps/telemetry/v1_adx_manifest.csv
```

These remain frozen semantic-design requirements for the replacement-OS workstream. They do not override built ROM placement or current truck calibration values.

## Regeneration rule

Use split/current views for normal review. Regenerate broad static maps when analyzer logic or the underlying source input changes. Git history is the version record.
