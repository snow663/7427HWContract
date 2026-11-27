# `$D8` port to the 7427

This directory tracks the 7060 BAMW-derived firmware running on the GM
16197427. It is a workstream within 7427HWContract, whose primary scope is
stock 7427 firmware reconstruction and the target hardware contract.
Stock 7427/BMHM evidence remains the authority for factory behavior.
The [7060 project](https://github.com/snow663/7060HWContract) owns the
donor-side stock BAMW reconstruction.

Keep port-specific adaptations, image identities, calibration and logging
definitions, and test results here. Cite the shared 7427 hardware contract for
established behavior. Record port-specific assumptions and pending checks with
the image they apply to. For address and RAM comparisons between the two stock
programs, see [BAMW and BMHM bus selections](../docs/investigations/BAMW_BMHM_SELECT_AND_RAM.md).

## Async-idle trial

The current candidate changes the BPW thresholds so the port can select steady
asynchronous fueling in the reported 1.0–1.4 ms warm-idle range. It uses the
existing mode selector, which also runs outside idle when the engine is running.

| CPU address | Role | Before | Candidate |
|---|---|---|---|
| `$82F3–$82F4` | BPW threshold while already in async | `00 21` | `00 76` (about 1.80 ms) |
| `$82F5–$82F6` | BPW threshold while presently in sync | `00 14` | `00 62` (about 1.50 ms) |
| `$82F7–$82FA` | MAP/RPM pairs, async state then sync state | `FF FF FE FE` | `FF FF FE FE` |
| `$82FF–$8300` | Minimum accumulated async shot threshold | `00 B8` | `00 B8` (about 2.81 ms) |
| `$8006–$8007` | Additive checksum of `$8008–$FFFF`, modulo 65536 | `35 9E` | `36 41` |

At `$AA5B–$AA8C`, the engine-running path selects async when pre-bias
BPW is at or below the state-dependent threshold, or both MAP/load and RPM
strictly exceed their respective thresholds. The high raw byte pairs above
leave the BPW threshold in control under ordinary idle and tip-in conditions.
The steady async path passes a zero synchronous command to the port helper.
The async dispatch path waits for the accumulated total to exceed the shot
threshold. See the [donor control flow](https://github.com/snow663/7060HWContract/blob/20294a365857e687933a502c886ecd9dbbb238ea/source/D8/D8_executable_nowrap.html#L1161).

Both images are 65536 bytes. The candidate changes four bytes in total
at `$8006`, `$8007`, `$82F4`, and `$82F6`.

| Image | SHA-256 |
|---|---|
| `D8-v3-idle-feedback-wideband.bin` | `53afe392fcdc6097683d94f23d65d2e23e1a0c454ad17a92ddf9d33b5fe4a2b0` |
| `D8-v3-idle-async.bin` | `8d5b57291f231bd2b145be61cbd4dacbbdb4748ad60f2558ef8ce28b0a0c8046` |

Byte diff and checksum are verified. Target results are pending. For the first
comparison, keep the baseline VE and fuel pressure. In the matching wideband
ADX, compare Calculated BPW before bias, Async fuel, Final sync command, Async
dispatch request counter, and wideband response at the same warm-idle RPM and
MAP. Check the return to sync on tip-in and note mode behavior on warm decel.
Last dispatched async command retains the previous value between shots. The
dispatch counter records software requests. Physical delivery and shot timing
require injector-side observation.
