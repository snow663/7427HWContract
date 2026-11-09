# Dated investigations

Each investigation describes the BIN/log snapshot named in that file. The
August `2.bin` investigations are historical and do not establish current
0.3.12 calibration values or active consumers. See [current state](../WORKING_STATE.md)
for the reported running version and exact-image limitations.

The [HC11 indexed-displacement correction](HC11_UNSIGNED_INDEXED_OFFSETS.md)
records the host CPU error exposed by retained-boot comparisons, its focused
instruction checks and the pending full regression under the corrected CPU.

[Manual-only idle replacement](MANUAL_IDLE_REPLACEMENT.md) traces the entire
Rev A idle boundary and records a new C/HC11 strategy tested as an in-memory
overlay. It is development source, not a released firmware revision.

The [VSS transport reassessment](VSS_FUELING_TRANSPORT_REASSESSMENT_2026-08-20.md)
supersedes the earlier exact event-order inference from adjacent ALDL rows.
Its serialization reasoning remains useful; snapshot-specific values remain
attached to the original image and logs.
