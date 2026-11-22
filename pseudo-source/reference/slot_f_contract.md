# Complete slot F and diagnostic prefix

Stock BMHM is byte authority, SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The complete `pcm_slot_0f` now implements7B5A..7B6C. This source work changes
no BIN, calibration or physical address allocation.

| C entry | Stock scope | Observation |
|---|---|---|
| `pcm_diagnostic_brake_set` | E905..E99D | Brake-set speed episode, two retained ages and timed recovery. |
| `pcm_diagnostic_brake_clear` | E99E..EA3F | Converse brake-clear episode and recovery budget. |
| `pcm_diagnostic_tcc_slip` | EE02..EE5E | Signed slip, TCC/range/gear admission and first observation. |
| `pcm_diagnostic_top_gear_slip` | EE61..EEBB | Unsigned absolute slip in third gear. |
| `pcm_diagnostic_tcc_released_slip` | EEBC..EF2A | Signed open slip window with the TCC released. |
| `pcm_diagnostic_current_error` | EC2D..EC78 | Byte magnitude, output fault and inhibit timer. |
| `pcm_diagnostic_transmission_temperature` | ECFF..ED3E | Temperature hysteresis and a16-bit timer. |
| `pcm_diagnostic_ratio_invalid` | EF88..F02E | Four open ratio windows and ordered qualification. |
| `pcm_diagnostic_ratio_lowgear` | F02F..F0AC | Gear below2 and an inclusive ratio ceiling. |
| `pcm_diagnostic_ratio_highgear` | F0AD..F130 | Gear at least2, inclusive ratio floor and temperature. |
| `pcm_diagnostic_slot_f` | C4F5..C513 | The ten observations above, in table order. |
| `pcm_slot_0f` | 7B5A..7B6C | C514 outputs, C4F5 diagnostics and the7B60 fault/fuel/refresh suffix. |

## State and ordering

The output/current-enable body runs **before** diagnostic observations. New
faults feed the later reaction scans in this call; they do not retroactively
change the preceding output decision. The next output call sees the updated
canonical fault owners. The now-resident root no longer uses `PCM_SLOT_0F`.
Its enum remains reserved for compatibility with earlier adapters.

Each monitor samples the native003B.2 freeze owner on entry. Freeze retains
that monitor's flags and counters. It does not skip outputs, fault reactions,
slow fuel or the final0051.2 refresh request. Failure returns at the first
unsuccessful operation; the completed prefix remains visible, and refresh
cannot mark an incomplete slot successful.

The brake monitors preserve their distinct episode latches, strict age limits,
suppressed wrapped-zero age stores and retained fault-timer exits. Recovery
budgets add2 with byte wrap. A first-good-observation bit prevents repeating
the same recovery allowance during the boot. The released-TCC monitor clears
its first-observation fault without a budget test. Fault timers themselves
wrap; reaching the threshold publishes the fault and clears the timer.

Slip EB comparisons use signed16-bit ordering; ED, ratios and elapsed engine
time use unsigned ordering. The current-error magnitude preserves literal
8-bit negation, including80. The temperature timer at017A is a complete word
with wrap, asymmetric entry/recovery thresholds and an entry-only sensor-fault
inhibit. Ratio85 excludes the interiors of four intervals, including their
strict endpoint behavior and the gear test between the third and fourth.
Multi-bit BRCLR range gates require at least one admitted bit to be set.

RAM/calibration reads and RMW operations remain fresh and ordered. The provider
must bind diagnostic flags, selected gear, TCC state/context, current service,
output shadow, fuel and refresh to the same owners used by native C consumers.
The fixture binds those owners and keeps both AC accumulator bytes visible.
These are existing factory roles; no modified-image register use is introduced.

## Verification

The focused suite passes **43,299 compiled-C/actual-ROM comparisons**, covering
**all466 instruction starts** in the new diagnostic/root scope:

| Cases | Scope |
|---:|---|
| 60 | Direct and joined entries, freeze and whole-slot admission. |
| 9,100 | Qualified byte boundaries, counter wrap and retained ages. |
| 17,920 | Complete shared flag bytes and partial range masks. |
| 6,720 | Both brake episodes and live latch reads. |
| 1,350 | First observations and recovery budgets. |
| 1,840 | Signed slip, unsigned ratio and word-timer edges. |
| 1,010 | Four open ratio windows and intervening gear rejection. |
| 1,280 | Temperature hysteresis and full16-bit timer. |
| 900 | Calibration enable bits and live capture. |
| 140 | Captured operands, fresh reads, freeze changes and IRQ state. |
| 1,024 | Raw profiles with inconsistent thresholds and retained state. |
| 400 | Ordered wrapper/root/fuel/REF and repeated whole-slot calls. |
| 1,395 | Every failed provider prefix in representative admitted/recovery paths. |
| 160 | Retained slot1/whole-slotF/fuel/REF histories. |

The complete controller, C514 output body, slot1 and REF are production code in
these joins. Native field operations contribute state without fabricated
provider transactions; newly logical bodies compare RAM/calibration operands
as well as actual I/O. Private call-stack traffic is excluded. No claimed
coverage extends into uncalled diagnostic bodies outside this slot.

All356 production/calibration files compile with strict C11 warnings as errors.
The host runners register80 checks. The kernel observes10 diagnostic admissions
and20 transmission-output publications per160 phases:10 from slot7 and10 from
slotF, with zero old slotF callbacks. Historical spark-dispatch contracts retain
their original EGR task boundaries; EGR/kernel/controller suites independently
link the resident implementations.
The historical foreground-refresh suite similarly supplies its original slotF
producer boundary. Its oracle already excludes that producer's body; the new
whole-slot suite checks outputs/diagnostics/fuel before the refresh handoff.

The user has authorized the accumulated full regression and merge. Results for
that release are recorded in the [working state](../../docs/WORKING_STATE.md).
Whole-scheduler interleavings, target ABI/backend/device timing and remaining
slow-slot callers are separate work. No flashable target image is produced.
