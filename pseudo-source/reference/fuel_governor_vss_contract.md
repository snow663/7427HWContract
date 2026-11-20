# BMHM governor VSS/hysteresis stage — $8EE4..$8F3A

This stage follows $8EC9..$8EDA's signed RPM target deviation and
**only** enters after the $8EDB optional $1809 module has been resolved.
The optional module can return carry set and accumulator A; the C
handoff uses `PCM_GOVERNOR_HEADSUP`, with transient fields
`PcmTransmission.governor_headsup_result` and
`governor_headsup_carry`. A successful carry writes the returned byte
to $0299 and **skips** the VSS and governor-target calculation.
An absent binding returns `PCM_UNIMPLEMENTED`, not an invented
no-module result. The $8F3B..$90D2 control tail is still delegated to
`PCM_GOVERNOR_TARGET`.

## Source-aligned behavior

At $8EE4 read the raw threshold $50DA. If zero, jump directly to
$8F38, clearing only $0075.7. Otherwise read the existing vehicle
speed word $0284/$0285. The canonical owners are
`PcmSpark.vehicle_speed_high` and `PcmIo.vehicle_speed_fraction`;
the C port does not create an independent stale copy.

Only the **high byte** is subtracted from threshold, leaving the
fractional byte in D. On the negative side, source
`NEGA; NEGB; SBCA #0` produces exact 16-bit magnitude, which is why
the C translation computes
`((threshold - high) << 8) - fraction`, not just
`abs(high - threshold) << 8`. Two `ASLD` instructions multiply by
four; carry on either saturates D to $FFFF. Only its high byte is
published to $0294.

On the above-threshold path, set $0075.6. If $0075.7 was clear,
read $50E1, publish the **minimum** of that value and current TPS
into the high byte of $0286, preserving low byte $0287, then set
$0075.7. Clear $0075 bits $13 afterward.

On the below-threshold path, clear $0075.6. If $0075.7 is set, read
$50DB and compare against the new $0294. When the delta is
greater/equal, clear $0075.7; when smaller, clear only bits $13.
If $0075.7 was already clear, clear that bit and leave the other
control flags untouched. Preserve each earlier state publication when
a later ROM byte read fails.

## Verification

The registered `fuel_governor_vss_contracts` fixture enumerates
262,144 combinations of threshold, high-speed byte, four fractional
speed bytes, four latch patterns and existing TPS. It includes
source-order ROM read assertions and failure positions at $50DA,
$50E1 and $50DB. These are test *definitions*, not a claim of a
fully executed repository suite or independent HC11 ROM comparison.

The new code remains callable and gated by the optional $1809
interface; the complete stock-equivalent fuel loop remains outside
fast-dispatch admission. Next: $8F3B..$90D2 speed-error, throttle
limit, integral lead and source $0299 publication.
