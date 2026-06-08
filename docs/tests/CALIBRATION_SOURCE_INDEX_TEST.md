# Calibration Source Index Test

## Goal

Verify that the calibration source index was generated from the machine-readable payload in `31_HAC_calibration_extract_nowrap.html` and that it does not promote stock strategy baggage into required minimal-OS inputs.

This test validates the index. It does not tune, modify, or select calibration values.

## Required Source

```text
/mnt/data/31_HAC_calibration_extract_nowrap.html
```

Expected source summary:

```text
section_count: 226
record_count: 11916
fcb_count: 11431
fdb_count: 485
min_data_address: $4000
max_data_address: $70FF
parse_error_count: 0
```

## Static Validation Tests

| Test | Expected |
|---|---|
| source payload exists | `<script id="calibration-extract-json" type="application/json">` found |
| section count | 226 |
| record count | 11916 |
| FCB count | 11431 |
| FDB count | 485 |
| address range | `$4000-$70FF` |
| parse errors | 0 |
| output CSV rows | 226 section rows plus header |
| required relevance | no section marked `required` by this index |
| excluded systems | transmission/EGR/EVAP/emissions remain excluded |
| unknown sections | unknowns are listed, not silently guessed |

## Command

```bash
python tools/build_calibration_source_index.py \
  --source /mnt/data/31_HAC_calibration_extract_nowrap.html \
  --out-md docs/contracts/CALIBRATION_SOURCE_INDEX.md \
  --out-csv maps/contracts/calibration_source_index.csv
```

## Required Checks

```text
1. section count matches 226
2. record count matches 11916
3. FCB count matches 11431
4. FDB count matches 485
5. address range is $4000-$70FF
6. parse errors stay zero
7. excluded subsystems remain excluded
8. unknown sections are listed, not silently guessed
9. no calibration section is marked required unless tied to a known module need
```

## Exclusion Discipline

These must remain excluded unless a later hardware contract proves otherwise:

```text
TCC / transmission / shift / 4L60 / 4L80 / gear strategy
EGR strategy
EVAP / purge / canister strategy
emissions-only strategy
```

Examples:

```text
TCC table:
  module_candidate = trans_excluded
  minimal_os_relevance = excluded

EGR spark correction:
  module_candidate = egr_excluded
  minimal_os_relevance = excluded

EVAP/purge:
  module_candidate = evap_excluded
  minimal_os_relevance = excluded
```

## Pass Criteria

```text
PASS:
  machine-readable JSON payload is parsed
  summary counts match expected values
  CSV contains one row per calibration section
  all rows use controlled module_candidate values
  all rows use controlled minimal_os_relevance values
  excluded systems are not promoted into minimal OS planning
  unknown sections remain visible for later source tracing
  no tuning values are changed
```

## Fail / Rework Criteria

```text
REWORK:
  parser scrapes visual HTML instead of machine-readable payload
  source counts drift from expected values without explanation
  CSV row count does not equal section count
  any section is marked required without source/hardware contract support
  transmission/EGR/EVAP/emissions strategy is pulled into minimal OS planning
  unknown rows are silently forced into fuel/spark/IAC categories
```

## Notes

This index is a planning map only. Hardware contracts still decide what the minimal OS must drive. Calibration data only becomes a module input after the corresponding source/hardware contract needs it.
