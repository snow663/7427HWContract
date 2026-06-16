# PER_TARGET_DOSSIER_INDEX_TEST

## Scope

Static test definition for first-pass per-target dossiers.

This pass is write-side grouping only. It must not attempt to fully prove read sites or downstream consumers unless a separate read/consumer extraction layer exists.

## Required input

```text
maps/generated/full_rom_write_target_sweep.csv
```

## Required output files

```text
tools/build_per_target_dossier_index.py
docs/analysis/PER_TARGET_DOSSIER_INDEX.md
maps/generated/per_target_dossier_index.csv
docs/tests/PER_TARGET_DOSSIER_INDEX_TEST.md
```

## Required CSV columns

```text
target_resolved
target_symbol
address_class
write_count
write_pcs
write_classes
widths
bitmasks
indexed_write_count
unresolved_indexed_write_count
routine_labels
dispatcher_contexts
candidate_roles
highest_confidence
hardware_reachability_status
diagnostic_only_status
preserved_driver_relevance
keep_drop_replace_candidate
review_priority
notes
```

## Required behavior

```text
group by target_resolved when present
fall back to target_symbol / target_raw for unresolved targets
count write classes and widths
flag indexed and unresolved-indexed writes
preserve dispatcher context
flag high-value hardware/preserved-driver candidates
mark diagnostic_only_status as not_proven_write_side_only
avoid final drop/remove decisions
```

## Non-relaxation clause

This artifact must not:

```text
create runtime ASM
mark bench proof passed
allow SLICE-1
accept fuel stock-driver preservation
accept IAC stock-driver preservation
allow custom hardware writers
claim diagnostic-only status without read/consumer proof
claim a target can be deleted from write-side evidence alone
```
