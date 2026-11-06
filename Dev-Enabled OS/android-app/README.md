# Android developer console

The Android app will provide the **text command language and binary packet compiler**. Only compact binary transactions cross the existing ALDL Bluetooth serial path; the PCM does not interpret user text.

## Connection

- Android Bluetooth Classic RFCOMM / SPP to an **already paired** serial module.
- Module-side TTL UART: **9600 8N1**, configured on the module.
- Existing ALDL interface/bridge remains in use; its actual PCM-side bitrate must be verified.
- Exactly one outstanding request, sequence checked, adapter echo filtered, response checksum verified.

## App-owned features

Console syntax + history + autocomplete; build-specific symbol catalog; typed reads; read grouping, host-controlled loops/conditionals/macros; watches and charts; traces and snapshots; CSV/JSON/raw export; latency/errors and firmware fingerprint; explicitly gated test operations in a later phase.

## Firmware-owned primitives

Phase 1: INFO, READ, GATHER, CLOSE. Phase 2: SNAPSHOT, TRACE_CTRL, TRACE_FETCH. There is **no text parser or script engine on the PCM**.

## Progress

Design and Python protocol fixtures are available under `../docs/` and `../protocol/`. The Android application is **not yet implemented as an installable APK**. Build the Kotlin codec/compiler and transport/UI modules here, keeping all symbol labels tied to the firmware image identity.

Suggested Gradle project when created: `android-app/app/src/main/java/`, `app/src/main/assets/manifests/`, `app/src/test/`. Do not silently use an incompatible manifest for a different BIN.
