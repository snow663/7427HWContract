# DISPATCHER_REVERSE_MAP_TEST

## Scope

Static test definition for dispatcher and indirect-control-flow mapping.

The artifact must:

- identify indirect `JMP/JSR` dispatch sites
- record selector/index source when statically visible
- record mask/shift/add/index math when statically visible
- resolve table entries where table rows are statically present
- reverse-map entries to landing labels
- summarize landing routine write targets when possible
- classify subsystem role conservatively
- retain unresolved dispatchers for review

## Required output files

```text
maps/contracts/dispatcher_reverse_map.csv
docs/contracts/DISPATCHER_REVERSE_MAP.md
```

## Non-relaxation clause

This artifact must not permit removing dispatch entries, changing scheduler paths, creating runtime ASM, or relaxing any hardware-output gate.
