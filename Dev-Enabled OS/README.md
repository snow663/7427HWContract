# Dev-Enabled OS — GM 16197427 / $31

Independent development workstream for the **Rev B developer-enabled firmware**, its Android Bluetooth serial console, and the supporting ALDL binary protocol, verification, and release records.

This directory intentionally lives at the repository root. It does **not** replace `source/manual_idle/`, `pseudo-source/`, the maintained Rev B release, or the factory hardware contracts.

## Layout

| Directory | Responsibility |
| --- | --- |
| [firmware/](firmware/README.md) | Rev B-derived HC11 source patches, build steps, image identities, future verified BIN/XDF releases |
| [android-app/](android-app/README.md) | Android command compiler, Bluetooth RFCOMM/SPP console, symbol manifest and application |
| [protocol/](protocol/) | Shared binary protocol specification, host encoder, deterministic framing test vectors |
| [docs/](docs/) | Firmware audit, current design, integration ledger, tests, technical decisions |
| [STATUS.md](STATUS.md) | This workstream's checkpoints and open blockers |

## Scope and behavior

- The **Android app** parses user commands, expands macros, resolves image-specific names, compiles/batches reads, controls polling, and formats results.
- The **PCM** accepts only compact binary requests via the retired **$F5** diagnostic channel, validates them, queues bounded primitive operations, and returns binary replies.
- The established Bluetooth-module UART setting is **9600 8N1**; PCM SCI rate / bridge behavior must be verified independently.
- Initial primitive set: `INFO (01)`, `READ (10)`, `GATHER (11)`, `CLOSE (7F)`.
- Deferred: coherent `SNAPSHOT (12)`, `TRACE_CTRL (20)`, `TRACE_FETCH (21)`. Temporary approved overrides are a separate, later design.
- Preserve normal engine execution and the factory `$F4` diagnostic implementation; the host will not run scanner and dev console sessions concurrently.

## Baseline and release policy

The **unmodified Rev B development candidate** is the pinned parent, SHA-256
`e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1` (`0.3.12_engine_only_manual_idle_revB.bin`).
The parent has **not** been shown to be truck-validated. No developer-enabled BIN or installable Android APK is present yet. Never rename a baseline image to imply that console firmware was implemented.

The repo-wide [working state](../docs/WORKING_STATE.md) still governs active calibration/vehicle-test checkpoints, including TS00. This workstream may develop separately, but does not claim those checks passed.

## Start here

1. [Developer console design v0.2](docs/RevB_ALDL_Developer_Console_Design_v0.2.md)
2. [Implementation ledger](docs/IMPLEMENTATION_LEDGER.md)
3. [Python protocol test/reference](protocol/revb_console_v1_protocol_reference.py)
4. [Firmware implementation plan](firmware/IMPLEMENTATION_PLAN.md)
5. [Firmware allocation/release rules](firmware/README.md)
6. [Android application workstream](android-app/README.md)
