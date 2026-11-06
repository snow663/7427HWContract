# Custom XDF corrections and current-address reference updates

This trace builds definitions for the unchanged Rev A image and the unreleased
manual-idle source overlay. It does not install either definition into a BIN,
edit calibration, or make the replacement current. See the
[definition guide](../../definitions/README.md) for exact image identities,
validation and application limits.

The source is the user-provided `Advanced $31 TP5 v251.xdf`, SHA-256
`0b4c321b2d11d52db479944bb1a7cd641251ae90147598439cd7efcf6e6154b6`.
Original author attribution is retained. The builder preserves reviewed
program boundaries and uses the root address register alongside the actual
ROM, not the XDF's inherited descriptions as byte authority.

| Address or code | Exact Rev A finding | Definition/reference action |
|---|---|---|
| FE9F bit0, FF43..FF5C | If global bit1 is clear, bit0 forces OL when normalized TPS is at or below FF8B | Describe the actual TPS gate, rather than claiming an RPM-qualified idle gate; add missing ROM/bit roles |
| FE9F bit1, FEC0..FECF | Global flag substitutes neutral BLM instead of RAM0248 | Document neutral multiplicative BLM in addition to the global OL state |
| FE9F bit1, FEE0..FEF2 | The same global flag clears the signed INT-derived correction at026F | Document the additive term; do not label INT a second fuel multiplier |
| 48EB, 8A3C..8A5C | Former P/N branch is bypassed; common/Drive route subtracts48EA | Mark the original Park subtraction omitted and exclude its control |
| 48F6 bit2, 8CB3..8CBD | Clear bit branches to8CBD; set bit executes the unconditional jump at8CB7 to the same8CBD | P/N BLM-cell offset is omitted although the old option test remains; preserve the other bits in48F6 |
| 4967..496A, 80A7..80C1 | Current X starts at4967 and can increment once for entry/release hysteresis; former fault-selected offset is removed | Mark4969/496A alternate thresholds omitted; preserve the normal pair |
| 4F23 / 4F24 / 4F25 | Actual Drive-entry producers use air magnitude / hold / qualification delay | Correct the supplied XDF's displaced descriptions and airflow/time scaling |
| 4F26..4F28 / 4F2C..4F2D | Consumers belong to the retired Park-entry body in Rev A | Mark these original roles omitted; do not confuse them with surviving Park cold-state housekeeping |
| 44F0..4515 / 451B..452B / 46EC..46F8 | Separate idle/transient spark correction consumers are retired by Rev A | Remove associated data controls, including data starts one byte beyond their omitted lookup headers |
| 4152 | Retained base DFCO spark-retard amount | Correct the supplied maximum-advance label; explicitly state that zero is not a universal disable |
| 9F00..9F26 | Code in Rev A, calibration only in the replacement overlay | Development profile only; never expose these addresses as data in the current Rev A XDF |

The maintained read workbook gains six named ROM/bit rows and six current-use
corrections. Its original-role column, other cells/tabs and image snapshot
remain intact. The OEM workbook is unchanged. ROM calibration has no runtime
write role, so this trace does not add these entries to the RAM/register write
reference.

Inherited surviving engine conversions remain explicitly inherited. Tests
check every custom address and conversion, schema-level layout, data extents,
math links, source identities and byte-level edits, but do not claim a native
TunerPro UI test or a new semantic audit of all inherited engine parameters.
