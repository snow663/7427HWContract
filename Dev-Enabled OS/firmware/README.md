# Firmware — Dev-Enabled OS

This folder owns all developer-console firmware modifications and generated release metadata. It is a **new variant of the exact pinned Rev B image**, never a replacement for the separately maintained production/tuning branch.

## Status

**Design only. No dev-enabled firmware BIN has yet been generated, validated, or committed.**

- Parent image: `0.3.12_engine_only_manual_idle_revB.bin`
- Parent SHA-256: `e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1`
- Rev B checksum (unmodified): `4E78` at ROM $4006.
- Matching parent XDF: `definitions/7427_0.3.12_Manual_Idle_RevB.xdf`.

## Planned files

- `src/`: HC11 modules for staged $F5 receive, command validation, bounded dispatcher, and prepared-response TX.
- `patches/`: reproducible parent-to-development image patch builder and audit manifest.
- `releases/`: **generated verified dev-enabled BIN and XDF pairs**, each accompanied by SHA, checksums, tests, diff manifest and status notes.
- `build_manifest.json`: pinned input identity and status.

The first image must implement INFO as a read-only, checksum-validated command. No existing Rev B engine-control behavior may be deleted, repurposed or redirected except the explicitly audited retired $F5 receive/TX path and reviewed scheduler entry points. Never assume marked ROM or RAM candidates are free without auditing indirect accesses.

**No BIN in this folder should be considered vehicle-validated without actual on-vehicle test records.**
