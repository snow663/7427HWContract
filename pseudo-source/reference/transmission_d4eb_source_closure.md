# Slots 03 and 0B gear selection

## November 23 source and verification

Normal scheduler dispatch runs both resident slot bodies. The entries are:

| Slot | Factory entry | Calls in execution order |
| --- | --- | --- |
| 03 | `$7ABD` | `$F5CF` checks `$0086.6`, calls external `$1806` when set, then writes `$F7` to `$0F00`. `$D4EB` selects the gear and `$C514` publishes the output. |
| 0B | `$7B3D` | `$D4EB` selects the gear and `$C514` publishes the output. |

The `$D4EB` body combines the diagnostic gates, the upshift/downshift decision
at `$D4F7..$D5B6`, and final arbitration at `$D5B7..$D69E`. The priority
in each direction is the nonzero fault threshold, the range table, kickdown
when enabled, then the normal curve. The source bits are recorded at `$0084`
before comparison. An upshift can qualify at equal road speed and RPM. A
downshift requires road speed strictly below its threshold. An inhibited
downshift samples the live gear again at `$D65A`. The selected gear and
inhibit flags reach the named state consumed by `$C514`.

| Stock code | C file in `src/transmission/` | Reconstructed behavior |
| --- | --- | --- |
| `$D4EB` and `$D8F0` | `transmission_gear_select.c` | Both threshold searches, source bits, RPM/speed admission, gear limits and finalizer handoff |
| `$D7E5` | `transmission_normal_threshold.c` | Throttle curve, separate first-knot read and cold-corrected floor |
| `$D840` | `transmission_kickdown_threshold.c` | Kickdown scalar with independently selected floor and cold offsets |
| `$D8A7` | `transmission_kickdown_rpm.c` | Upshift RPM word, including the different pointer values retained on two descriptor miss paths |
| `$D8FE` | `transmission_descriptor.c` | Selector and stop-bit priority, byte-wrapped initial gear displacement and 16-bit cursor |
| `$D92E / $D94B` | `transmission_temperature_gain.c` | Centered gain, rounded scaling and saturated doubling |
| `$D980` | `transmission_cold_offset.c` | Signed magnitude correction with rounded gain and unsigned saturation |

`gear_slots_rom_differential` takes its factory code from the recorded BMHM
image (SHA-256 `6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`).
It compares the compiled C against the HC11 interpreter from each scheduled
entry, including retained 03 → 0B → 03 sequences. Some cases vary stock RAM
inputs and calibration/table data to expose boundary behavior.

| Verification | Observed result |
| --- | --- |
| Whole-slot and retained cases | 2,004 comparisons. Together they executed all 602 resident instruction starts reachable from the pair, including all 558 reachable from `$D4EB`. Coverage is checked before running the helper cases. |
| Direct helper edges | 1,298 comparisons over pointer wrap, returned cursor, signed offsets, rounded gain and saturation |
| Injected provider failures | 914 comparisons of the attempted read, write or external call and the state at the stop |
| Scheduler cadence | Exactly one output write on each 03, 07, 0B and 0F phase across the 160-phase host fixture |
| Total in the joined ROM suite | **4,216 comparisons passed** |

The fixtures compare gear-selector bus transactions in order, named gear,
inhibit, output-shadow and TCC state, and the electronic TCC command at
`$306A`. The optional module is represented by an absent, returning or failing
provider. Its firmware, physical solenoids, target timing and interrupt
interleavings still need separate evidence. Instruction-start coverage
measures which instructions were reached across the tested cases.

## Earlier helper verification — 2026-11-22

The source of truth is the SHA256-identified full BMHM ROM contained in
`maps/structure/bmhm_ownership_rom_evidence.json`. The following new
public C routines are each in their own file and indexed by
`pseudo-source/routine_index.csv`. Each has a new independent HC11
interpreter differential and corresponding host contracts.

| Stock entry | C routine | Verification scope |
| --- | --- | --- |
| $E6BC–$E6E3 | `pcm_transmission_mask_scan` | Nine descending diagnostic status/enable/alternate/table intersections, source read order, first-match short circuit |
| $E684–$E69B | `pcm_transmission_fault_gate_684` | $001D.7 priority, $0087.1 admission and $E74C table update of $0098.7 |
| $E6AC–$E6BB | `pcm_transmission_fault_gate_6ac` | $E743 mask scan to $0099.1 |
| $E69C–$E6AB | `pcm_transmission_fault_gate_69c` | $E73A mask scan to $0099.0 |
| $D4EB–$D4F7 **prefix only** | `pcm_transmission_d4eb_prefix` | Exact E684→E6AC→E69C call order; zero $0084 after successful diagnostics |
| $E562–$E57B | `pcm_transmission_gear_limit` | $00A2 low-three-bit range mapping, zero→6 fallback, four-byte stride, indexed ROM bound and unsigned min; all possible range/candidate input bytes |
| $D5B7–$D69E | `pcm_transmission_gear_finalize` | Gear arbitration, $0098/$0099 priority, $0083 direction and delay gates, $0085 TCC request, $E562 limit, $0103 override, $00D9 publication |
| $D8CE–$D8EF | `pcm_transmission_threshold_select` | Carry-qualified $D763/$D775 pointer tables, $0098.2 inhibit, $00A2 range, wrapped 8-bit pointer offset and pointed byte |

Focused ROM comparisons:
`transmission_d4eb_prefix_rom_differential`,
`transmission_gear_limit_rom_differential`,
`transmission_gear_finalize_rom_differential`, and
`transmission_threshold_select_rom_differential`.
These use actual HC11 instruction replay rather than matching two
independently authored C oracles. Their host counterparts assert read
order, parameter guards, retained data and failure-prefix behavior.

Verified development [GitHub Actions run 45004479765](https://github.com/snow663/7427HWContract/actions/runs/45004479765)
passes **51 of 51 fast contracts** and **9 of 9 focused ROM differential
suites**, including the prior joined fuel controller, governor and
ignition suites. That checkpoint had **43 registered** ROM suites.
