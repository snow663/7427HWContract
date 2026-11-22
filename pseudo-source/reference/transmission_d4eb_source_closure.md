# M2 slot 03: stock $D4EB transmission source closure ledger

## Verified source segments — 2026-11-22

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
ignition suites. All **43 registered** ROM suites are reserved for the
single-PR release gate.

## Factory call graph and remaining middle segment

The actual $D4EB entry is not one short linear body. It comprises:

- **$D4EB–$D4F7:** E684→E6AC→E69C fault gates, followed by zeroing $0084 — now resident and stock-verified
- **$D4F7–$D5B6:** admission, upshift/downshift threshold options, position/gear-limit decisions, compare/read/lookup helpers — **not yet reconstructed as one full C body**
- **$D5B7–$D69E:** output candidate arbitration, inhibit/delay and eventual selected gear — now resident and stock-verified at its own entry with B supplied as input

The middle uses direct helpers at **$D8F0**, **$D8CE**,
**$D840**, **$D8A7** and **$D7E5**, with further subcalls
$D8FE, $D92E, $D980, $F4C1 and $F550.
Only $D8CE has been ported as a new public C module in this
increment. Existing generic fixed-point math can be reused only
after checking exact ROM register/CCR and stack semantics.
Source tables $D69F/$D6AB/$D763/$D775/$D787/$D79B must be
read with source widths and pointer priorities rather than
treated as plain calibration scalars.

**No duplicate execution:** In current guarded slot03 source
mode, the $D4EB dependency is still dispatched as a **whole**
through `PcmPlatform.call_address` at address $D4EB. The new
partial C prefix and finalizer are callable research primitives
and are **not** executed before that callback. Replacing the
whole call with a callback to $D4F7 would require the native
HC11 entry ABI and CCR/register/stack contract; do not pretend a
bare address is equivalent to a typed C invocation.

The stock equivalent is separate from any future manual-only
tuning changes to remove automatic transmission code. No physical
shift/TCC solenoid, PCM target timing, ALDL stream, native BIN
or complete transmission behavior has been validated here.

## Next source integration move

Port D8FE's hierarchical lookup and its D8F0 direct caller,
then D840/D8A7/D7E5 branch arithmetic. Join only the *whole*
D4F7–D5B6 candidate calculation with D5B7–D69E once its caller
inputs and retained flags are verified in a new full-entry
$D4EB ROM differential. After that, upgrade slot03's D4EB
dependency to the resident source body (still behind source-mode
admission); the optional $1806 module stays an explicit boundary.
