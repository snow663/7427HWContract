# DISPATCHER_REVERSE_MAP

## Purpose

Reverse-map indirect dispatch and table-driven control flow so subsystem ownership can be inferred from both selector variables and landing routines.

This is a static analysis artifact only. It does not implement runtime ASM, relax hardware gates, or prove hardware behavior.

## Source

- source file: `source/31/BMHM_HAC_ORG_7100_to_end.asm`
- dispatcher rows emitted: `17`
- dispatcher PCs observed: `7A4F, FAA5`
- reviewed embedded data is excluded using `maps/structure/reviewed_source_regions.csv` (source SHA-256 checked)

## Key dispatcher classes

- Major-loop dispatcher: `L0002 & 0x0F -> table -> JSR 0,X`.
- Output-control/ALDL dispatcher: `L038E -> JSR 0,X`; this is an indirect control block and must not be confused with production subsystem scheduling.
- Other indexed `JMP/JSR` rows are retained as unresolved/mixed until selector and table semantics are proven.
- `$C2D6-$C409` contains lookup descriptors/pointers. Apparent jumps inside `$C3A2` are data, not unresolved dispatchers.

## Required reverse-map fields

`dispatcher_pc`, `index_source`, `index_math`, `table_address`, `entry_value`, `resolved_target`, `target_write_targets`, `candidate_subsystem`, `confidence`, and `notes`.

## Isolation rule

A routine reached only through a dispatcher must be kept reachable if it owns hardware, safety, scheduler, rolling-state, or preserved-driver side effects. Do not delete by linear call-tree assumptions alone.
