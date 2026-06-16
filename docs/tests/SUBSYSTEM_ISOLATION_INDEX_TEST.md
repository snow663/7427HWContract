# SUBSYSTEM_ISOLATION_INDEX_TEST

## Scope

Static test definition for subsystem isolation after write-target and dispatcher indexing.

The artifact must:

- summarize fuel compact `$3FCE`, fuel stock driver, spark stock handoff, spark custom writer, IAC stock driver, and IAC custom writer
- include the current route, preservation status, bench status, implementation permission, blocked conditions, and next required proof
- keep fuel compact `$3FCE` on the active bench route
- keep `SLICE-1` blocked until `FUEL-001` through `FUEL-004` pass under the compact route
- keep custom spark and custom IAC writers bench-required
- treat write-target and dispatcher maps as supporting analysis, not implementation permission

## Required output files

```text
maps/contracts/subsystem_isolation_index.csv
docs/contracts/SUBSYSTEM_ISOLATION_INDEX.md
```

## Non-relaxation clause

This artifact must not create runtime ASM, permit deleting variables without network proof, mark fuel/IAC preservation accepted, mark bench proofs passed, or relax any hardware-output gate.
