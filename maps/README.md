# Maps

Machine-readable maps, generated access inventories, current runtime-analysis tables, frozen planning manifests, and source-derived trace indexes.

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