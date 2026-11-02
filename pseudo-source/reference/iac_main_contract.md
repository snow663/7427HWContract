# Resident main IAC, service exits and airflow conversion

Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The main adapter now calls resident C routines directly. Its former
`PCM_IAC_CONTROL` task ID is reserved and unused, including in the kernel tests.
Every public routine has its own file.

| Stock scope | C routine | Responsibility |
|---|---|---|
| 93D0..989B | `pcm_iac_control` | Optional module, service, reset, stopped/running order |
| A407..A465 | `pcm_iac_service` | Service selectors and explicit whole-controller exits |
| 92A4..92F0 | `pcm_iac_seed_cells` | Default integral high bytes and snapshots |
| 9411..9536 | `pcm_iac_start` | Stopped initialization and direct/common output tail |
| 9537..969D | `pcm_iac_context` | Gear/AC transitions and pending cell commits |
| 969E..9748 | `pcm_iac_error` | Switch inputs, holds and signed RPM-error filter |
| 99C5..9C1F | `pcm_iac_integral` | Admission, integral/cold allocation and reconciliation |
| 9C20..9C95 | `pcm_iac_proportional` | Context curves and speed hysteresis |
| 9CA6..9CFC | `pcm_iac_derivative` | Ratio filtering, retained sign and magnitude |
| 9752..983C, then983D | `pcm_iac_compose` | Ordered flow, AE, follower, DFCO and PE cap |
| 983D..989B | `pcm_iac_convert` | BARO/kicker scaling and position-table conversion |
| F4A4..F4B4, thenF4B8 | `pcm_lookup_offset` | Lower-offset floor, cap and scaled lookup |

The C scope follows actual instruction bytes. In particular9CA6's missing
listing entry and A40B's malformed branch are read from the recorded image.
The eight9C96 pointer words select the corresponding ten park/drive P views;
they are data, not executable instruction starts. Boot/retained setup925E and
92F1 are separate unported reset stages.

## Entry, reset and service

Profiling0086.6 admits an explicit `PCM_IAC_EXTENSION` dependency at1803 before
any resident write. Missing code returns UNIMPLEMENTED with that identity;
a failed callback retains the completed prefix. Tests supply selected return
and state effects without defining the unknown module's machine ABI.

After the module, clear0038.6. Service003B.4 calls the real selector:

- Ignition gate0044.4 or reset0009.0 returns normally.
- 0391.5 requests reset and exits the entire controller.
- Equal0395.0/038F.6 selections return normally.
- Only0395.0 with0395.1 clear clears0036 bits0C, writes0008=0396 and exits.
- Only0395.0 with0395.1 set writes0857=0396, sets0038.6 and continues.
- Only038F.6 uses0390.6 to set/clear0037.2 and clear/set004B.7, then exits.

The last route uses raw923C/9222 setters. It does not run the larger kicker
wrappers, alter TPS-zero, reload timers or clear the other kicker flags.
`exited` represents the local return-address discard. It is not factory RAM.
The ROM fixture checks the actual caller/local frame balance on both returns.

Reset-in-work writes target0 and returns while software position is nonzero.
At zero it clears reset, sets valid0009.2 and runs92A4 before continuing. The
four integral high bytes and snapshots are seeded with saturated AC additions;
each integral fraction is retained. The completed ignition-gate route parks;
an invalid one calls the existing software reset request. The gate reuses
`reference.latch_inhibited`, the actual0044.4 owner, rather than0051.3.

Stopped initialization retains the ROM's high-byte-only writes to086E and0859,
byte RPM wrapping, separate startup hold/divider, cold/current bounds and shared
0036.5 clear. It chooses fixed or retained integral state by the actual options.
Coolant can select a direct park target; otherwise startup flow and cold enter
the common conversion tail without the running P/D/follower composition.

## Running state and arithmetic

Gear selection uses400F.6 plus0041.5, or the separate raw00A2 flags. AC request
0052.5 is an independent input. The old context remains local across both
transition producers. Delay sums wrap as bytes; ordered AC minimum/maximum
comparisons also retain their behavior when profile limits are inverted.
Only a context change commits the selected pending integral proposal. Cold
transfers retain their separate bound-high, gear-change and pending-bit gates.

The switch helper uses the existing board input shadow004D, not another
peripheral read. Its enabled path clears the shared spark override0036.5 even
when the switch just seeded an adder/delay. Gear/AC/stall/follower holds age in
stock order. The call finding a zero stall hold clears its flag; a decrement
reaching zero does not clear it until the next call. Error direction uses
unsigned RPM/target subtraction. Forced error deadbands replace the entire
filter word; otherwise the existing signed-floor byte lag applies.

Integral control models the six-byte stack frame as local values. Qualification
expiry, fallback underspeed admission, low battery and previous kicker/airflow
retain separate gates. Stall addition precedes ordinary integration. Error
coordinates have the exact four piecewise slopes. The word increment is an
unrounded table-byte times error-byte product. Cold allocation compares the old
cold value with its bound; its new sum is not subsequently clamped to that bound.
Overspeed consumes switch and startup adders first, forcing progress when the
increment high byte is zero. The VSS-fault floor wraps its AC byte addition.
All exits publish the selected integral, cold and bound words in stock order.

The software-position reconciliation paths change0007 without a ring transition.
They retain their service/mode/error/phase gates and byte wrapping. They do not
supply a physical position observation. The step driver91A3 remains unfinished.

P uses the verified pointer selection and drive-overspeed speed hysteresis.
D retains its fractional word, sign and magnitude when the lookup target equals
the old high byte. Other routes choose fast/slow lag or a direct target word;
the magnitude follows the actual two-shift rounding.

Flow composition clamps or floors at each stock stage. AE087F observes the
pre-follower composite change, not a step-count change. Follower high-byte carry
skips DFCO refresh/application on that call. Saved DFCO correction can continue
after DFCO ends. The PE cap precedes BARO and kicker scaling. Kicker subtraction
borrow sets its request and skips the later gain; other enabled routes apply it.

Position conversion uses rounded flow/16, then a **wrapped increasing delta**.
Falling knots do not follow the ordinary signed-slope lookup. The18-byte source
view includes the zero-fraction endpoint neighbor at4EA3, which also begins the
BARO header. Direct service/park/reset targets bypass the conversion.

## State, source profiles and limits

New fields represent0041.5,0052.5,0391.5,0390.6,0396,00A2,004D and the main
working words/timers0862..088C. Existing spark.service_flags0395, runtime service,
RPM, BARO, MAT and shared IAC cells remain their existing owners. Input producers
are not inferred from their consumers. Shared calibration views, including4E90,
are verified against the same stock bytes; native structs are not an EEPROM ABI.

Offset and scaled descriptors check their backing before either knot read.
Stock production views keep11 BARO knots, two MAT knots and five AE knots.
The comparison fixture separately supplies256 ROM-checked backing bytes for
each descriptor to exercise modified scale/cap/offset combinations safely.
Configuration failures retain completed earlier state and do not invent values.

The new IAC profile views cover367 distinct addresses,359 outside the prior
background/slow-IAC views. Some bytes also overlap older spark profiles. All
views and the three extended test backings are checked against the stock image.

The host tests compare all mapped state, ordered transactions/dependencies,
mask state, missing-task identity and local stack balance. Unexpected non-stack
RAM writes are rejected. Directed sweeps include every flow word under stock and
falling tables, every startup coolant/options pair, every default/addition pair,
every ratio/old-high/sign combination, integral/cold admission and allocation,
P selection/hysteresis, wrapped gear/AC transitions, all service selectors,
reset/position pairs, retained histories, and failed dependency/I/O prefixes.
The corpus exercises all919 scoped instruction starts. Both host routes
include34 CTest entries.

A passing host comparison establishes the supplied witness domain. It does not
establish target ABI, interrupt entry, RAM/stack fit, coherent word access,
preemption behavior, HC11 deadlines or physical pintle direction/cadence.
Next port91A3 count/phase service, then remaining scheduled input producers and
reset/backend work. Optional module implementations remain explicit dependencies.
