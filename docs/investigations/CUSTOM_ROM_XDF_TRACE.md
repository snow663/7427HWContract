# Custom XDF corrections and current-address reference updates

The original section below records definitions for the unchanged Rev A image and the then-unreleased
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


## Rev B label review — 2026-11-06

The subsequent [instruction/execution verification](REVB_XDF_LABEL_VERIFICATION.md)
supersedes tentative wording below. It confirms the consumer distinctions and
qualifies the earlier claims about normalized-flow units and maximum-retard naming.

This is a read-only review of the XDF actually supplied in the Rev A/Rev B
bundle. Its SHA-256 is
`788b8f5b79c646fa072b45de5f8e075c77f5d692468d39541406676a0145214e`;
the delivered ZIP entry and repository file agree. The reviewed BIN is the
Rev B image identified in the release trace. No XDF, BIN or calibration bytes
were changed by this review or its follow-up verification. The follow-up adds
the verified ALDL pointer/shared uses to the maintained read reference. Pending wording/unit corrections are recorded
here for a separately reviewed metadata update; inherited engine labels and
conversions are not collectively certified by structural XDF tests.

| Address | Delivered label / finding | Suggested wording or clarification |
|---|---|---|
| FE9F bit0 | Force OL Idle; FF43..FF5C tests normalized TPS against FF8B, without RPM capture | Force OL at closed throttle; describe global-flag precedence |
| 4979 / 4971 | Async Short BPW Offset vs. BPW / Async Short BPW Offset Bias; synchronous 84D6/84E1 and async 855A/8564 both reference them | Short-pulse added correction / Short-pulse subtraction; describe each path and the actual add-then-subtract operation |
| 496D / 496F | Minimum Synchronous BPW / Minimum Synchronous BPW Allowed; 84E9 compares the first, 84F2 loads the second | Sync minimum-pulse threshold / Sync replacement pulse; distinguish trigger from replacement |
| 50A8 | Lower Threshold for IAC AE, displayed as percent flow; new controller compares the positive pre-follower air-command increase at 9A5A | Minimum air-command increase for IAC AE; normalized command percent is valid, as are explicitly defined internal units; measured airflow percent is not established |
| 50A9 | Upper Threshold for IAC AE, displayed as percent flow; 9A52 compares normalized TPS from 01D9 | TPS ceiling for IAC-change AE; correct the unit to normalized TPS counts or consistently scaled TPS percent |
| 5216 | Desired AFR, Hex; the description already calls this a logging selection, and the stored word is 024A | ALDL channel source address; this is a RAM-address pointer for telemetry, not a mixture target |
| 49D8 / 4A8B | Open Throttle VE / Idle VE; 7F95 uses FF8B and 7FA4 uses the fixed RPM boundary, independent of IAC capture | Main VE / Closed-throttle VE; document exact selection and RPM range |
| 48DA | Maximum TPS for Idle VE; current VE selection instead reads FF8B | Name by its surviving consumers: 777B, 8DA8 and AAFE. Do not imply this still switches the VE tables; full semantic wording needs those shared uses reconciled. |
| FF8B | Fuel idle-retention / OL TPS threshold; also read by VE selection at 7F95 | Closed-throttle TPS limit (fuel/VE/OL); explain that IAC release has its own calibration at 9F15 |
| 4146 / 4148 | Maximum Spark Retard / Maximum Spark Retard for DFCO; signed lower bounds selected at AB0E/AB03 | Normal minimum spark angle / DFCO minimum spark angle describe the signed floors; Maximum Spark Retard is defensible existing shorthand. These are separate from base-relative subtraction and precede service edits |
| 4D92 | Six TBI/CPI/MPFI flow displays refer to the same two bytes using different conversions | Present the TBI flow view prominently; alternative displays are aliases, not six independent injector settings |
| FF60 / 9F00 | Base idle RPM - coolant index / Cold idle-air feedforward - coolant index | Idle target vs. coolant index / Cold idle air vs. coolant index; retain the native-index axis, not degrees C |
| 9F11 / 9F18 | Starting learned-air baseline / Integral qualification delay | Idle-air seed / IAC integral delay; retain runtime-only learning and main-call units in descriptions |
| 9F17 | IAC and DFCO spark release margin above idle target | Idle-exit / DFCO-spark RPM margin; keep both consumers and their opposite release comparisons explicit in the description |

The custom 9F00..9F26 data extents and conversions have dedicated source/test
coverage. Air units are internal controller coordinates; the coolant index is
not temperature in degrees C. Those distinctions should survive any shorter
names. Existing legacy descriptions can be misleading even where their data
addresses are structurally valid. Changes to names, units or display math must
be distinguished from ROM calibration changes and checked before a replacement
XDF is distributed. Rev B testing/fine-tuning remains the active trajectory.
