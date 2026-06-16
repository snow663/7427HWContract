# PER_TARGET_DOSSIER_INDEX

## Purpose

First-pass write-side dossier index grouped from `FULL_ROM_WRITE_TARGET_SWEEP`.

This groups the raw write/mutation evidence by `target_resolved` / `target_symbol` and produces review priority and keep/drop/replace candidates from write-side evidence only.

It does not extract read sites, consumer edges, or downstream proof yet. It does not create runtime ASM, prove hardware behavior, mark bench gates passed, or authorize `SLICE-1`.

## Source

- source sweep: `maps/generated/full_rom_write_target_sweep.csv`
- dossier rows: `793`

## Decision summary

- `unknown_pending_read_consumer_edges`: 715
- `unknown_review_safety_or_mode`: 36
- `keep_or_preserve_until_proven_otherwise`: 28
- `unknown_review_unresolved_indexed`: 13
- `unknown_review_dispatch_context`: 1

## Review priority summary

- `medium`: 751
- `high`: 42

## Hardware reachability status summary

- `not_established_write_side_only`: 765
- `hardware_or_preserved_driver_candidate`: 28

## Required interpretation

```text
write-side grouping is not read/consumer proof
diagnostic-only status is not proven in this pass
drop/remove decisions are not allowed from this artifact alone
hardware/safety/dispatch/preserved-driver candidates stay keep-or-review until downstream edges are proven
```

## Next layer

The next static layer should add read sites, downstream consumers, hardware reachability, dispatcher involvement, and preserved-driver dependency edges.
