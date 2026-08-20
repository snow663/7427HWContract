# $31 HAC Raw-Source Trace Provenance

This directory indexes the broader source-derived `$31` HAC trace artifacts supplied to the project.

These artifacts are source-derived evidence/index material. They are not inherited XDF authority and they do not override executable proof or current running-calibration bytes.

## Source-trace package

```text
archive: 31_HAC_full_source_trace_import_v1.zip
SHA-256: 8caf72a1707ac0ee2fb415b6aa6ae2d9bbabac356246a005a03adda19a8eeb7b
```

Package README reports it was generated from raw source named:

```text
$31_HAC.SRC
```

Reported extraction counts:

```text
source lines:                         46,433
ORG/range blocks detected:              236
Lxxxx FCB/FDB/FCC/RMB declarations:  12,778
high-value XDF seed candidates:          531
```

Archive members:

```text
org_blocks_memory_locations.csv
all_labeled_data_memory_locations.csv
high_value_xdf_seed_candidates.csv
README.md
```

Archive member sizes from the supplied package:

```text
org_blocks_memory_locations.csv          58,255 bytes
all_labeled_data_memory_locations.csv 2,940,946 bytes
high_value_xdf_seed_candidates.csv       63,616 bytes
README.md                                    822 bytes
```

## Extraction rules preserved from the package

```text
rows are source-derived
inherited XDF category names are not trusted as authority
unknown scaling remains raw/review rather than guessed
```

That rule is consistent with the repository's contract discipline: a source comment/declaration can establish provenance and candidate meaning, but engineering scaling or runtime semantics must be promoted only at the evidence level actually proven.

## Related supplied HTML views

The project also received two no-wrap HTML renderings for visual/search review:

```text
31_HAC_from_ORG_7100_to_end_NOWRAP.html
SHA-256: 40efe3c195f7170b3f5834bbcde3202bba732e19fc134a80983d5e647a07c966

31_HAC_calibration_extract_nowrap.html
SHA-256: 0d6305dfa13ec90049baac3679ba2ad5ed7a2986ebd0283ef0e344a72dc782ee
```

The HTML files are presentation/search artifacts, not preferred machine-readable authority.

## Authority relationship

Use the evidence split:

```text
source/31/BMHM_HAC_ORG_7100_to_end.asm
    -> committed executable-side stock algorithm/dataflow authority

raw-source trace package
    -> broader source-derived calibration/data inventory and candidate index

current running 2.bin
    -> current truck calibration-byte/table authority
```

A trace row that conflicts with executable proof or current `2.bin` bytes must not silently override either one.

## Repository payload status

This consolidation commits the provenance/index and authority rules. The supplied multi-megabyte CSV archive remains an external source artifact identified by its SHA-256 above; its full CSV payload has not been duplicated into Git by this connector pass.

If the payload is later committed, retain these stable target names:

```text
maps/source_trace/org_blocks_memory_locations.csv
maps/source_trace/all_labeled_data_memory_locations.csv
maps/source_trace/high_value_xdf_seed_candidates.csv
```

and verify the imported contents against the source archive rather than regenerating labels/scales from memory.