# DISPATCHER_REVERSE_MAP_TEST

## Scope

Static test definition for dispatcher and indirect-control-flow mapping.

The artifact must:

```text
identify indirect JMP/JSR dispatch sites
record selector/index source when statically visible
record mask/shift/add/index math when statically visible
resolve table entries where table rows are statically present
reverse-map entries to landing labels
summarize landing routine write targets when possible
classify subsystem role conservatively
retain unresolved dispatchers for review
```

## Required output files

```text
tools/build_dispatcher_reverse_map.py
docs/contracts/DISPATCHER_REVERSE_MAP.md
maps/contracts/dispatcher_reverse_map.csv
```

## Required seed coverage

```text
7A4F major-loop dispatcher
FAA5 output-control block dispatcher
```

## Non-relaxation clause

This artifact must not:

```text
remove dispatch entries
change scheduler paths
create runtime ASM
mark routines removable without write-target/network proof
relax hardware-output gates
permit SLICE-1
```
