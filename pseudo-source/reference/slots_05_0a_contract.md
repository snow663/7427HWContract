# Slow scheduler slots 05 and 0A

Both slots execute through the ordinary 16-entry scheduler table. The recorded
BMHM image has SHA-256 `6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.

| Stock entry | Admission in 160 scheduler phases | State produced |
| --- | --- | --- |
| Slot 05, `$7B03 → $D3B0` | The catalyst estimator can advance once, at full phase `$05`, with the engine-running flag and `$400F.4` set. | Filtered catalyst estimate `$0078`, working bytes `$007A..007E`, hot counter `$084C` and rich AFR request `$0052.6`. |
| Slot 05, `$D472` | Every slot 05 admission (ten). | Manifold request `$0052.3`. Entry uses the coolant check and the second RPM/TPS row. A retained request uses the first row. |
| Slot 05, `$C6BB` | After manifold processing, when `$400F.6` is clear. Stock BMHM selects this path. | Rebuilds TCC inhibit reasons at `$008C/008D`, computes both limits, and handles the service command, faults and apply/release requests. |
| Slot 0A, `$7B39 → $D2B2` | Five admissions with phase bit 4 clear. The other five retain the entire purge state. | Purge duty `$01D6`, learned multiplier `$01D7`, update delay `$01D8` and the duty-present flag `$0041.7`. |

## Controller handoffs

The catalyst routine captures the air-rate high byte for both the gain and
the speed/air-rate surface. Its AFR-dependent correction feeds the filtered
estimate. At low throttle it clears the age and proceeds directly. At higher
throttle it can suspend the estimate and retain the previous rich request.
The AFR finishing routine applies that request to the commanded mixture.

Electronic TCC service values 1–100 write `652 × value` into `$0126`.
Values 101–200 request apply, and 201–255 request release. The regular MAP
gate uses `$6AEC` when `$0089.6` is set and `$6AED` when it is clear. Either
live fault bit in `$0018 & $30` can bypass that gate when both reaction-mask
bits in `$5B2D & $30` are set. The comparison exercises each combination
with MAP below, equal to and above the two limits.

A hot-start purge request takes priority over DFCO and preserves the learned
multiplier and delay. Closed-loop purge adjusts the multiplier from the
integrator, then applies the duty floor. Open-loop purge uses its own scaled
curve and preserves both learning bytes. Slot 0D owns the downstream service
override and hardware command at `$3FD6`.

## Verification

The replay starts the HC11 at each stock scheduler entry and runs the compiled
C through `pcm_dispatch_slot`. It compares the logical transactions in order,
the retained RAM and the named state read by fuel and transmission code. Cases
include stock calibration, controlled thresholds, changing inputs between
reads, and both slots on the same retained state across a 160-phase cycle.

| Coverage | Slot 05 | Slot 0A |
| --- | ---: | ---: |
| Resident instruction starts reached | 538 of 538 | 123 of 123 |
| Conditional branches exercised in both directions | 108 of 108 | 24 of 24 |

| Comparisons | Count |
| --- | ---: |
| Catalyst and manifold | 962 |
| Purge | 502 |
| Electronic TCC | 1,060 |
| Retained histories | 29 |
| Injected transaction failures, including partially updated state | 434 |
| **Total** | **2,987** |

The host scheduler fixture checks each admission across all 160 phases. A
separate host check follows the rich request into AFR limiting and a service
value of 100 through `$0126` to the existing `$306A` output transaction.
Electrical outputs and target interrupt timing still require target validation.

[Whole-slot replay](../tests/compare_slots_05_0a_rom.py) · [Host handoffs](../tests/slots_05_0a_test.c) · [Factory emissions](../../docs/analysis/FACTORY_EMISSIONS_CONTROL.md) · [Factory transmission](../../docs/analysis/FACTORY_TRANSMISSION_CONTROL.md)
