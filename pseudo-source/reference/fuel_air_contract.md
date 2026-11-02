# Fuel input normalization and air-charge calculation

Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
This batch adds eleven public routines, bringing the source to198:96 implemented
outlines,71 algorithms and31 explicit dependency boundaries. The existing
[input/output batch](fuel_input_output_contract.md) supplies raw acquisition and
injector finalization. These new bodies connect normalized inputs through VE and
the base equation; broad controller and scheduled roots remain explicit below.

| Stock scope | C routine | Result |
|---|---|---|
| B1AC..B1CE | `pcm_throttle_zero` | Admitted shared TPS-zero word filter and cap |
| B1CF..B1EF | `pcm_throttle_normalize` | Engine TPS01A6 and returned byte |
| 7DF1..7E08 | `pcm_fuel_throttle` | Prior engine TPS01DA and current/fallback01D9 |
| C96A..C9BF | `pcm_coolant_input` | Converted/effective coolant, shared range flag and0283 |
| DBFB..DC88 | `pcm_mat_input` | MAT ADC, diagnostic counters/faults, display and effective MAT |
| C583..C667 | `pcm_baro_input` | Sensed/estimated BARO, dependent AE/PE/load coordinates |
| 7E40..7E4E | `pcm_fuel_density` | Normalized MAP density0257 |
| E2C8..E2FA | `pcm_fuel_charge_temperature` | Coolant/MAT/air-rate temperature denominator0236 |
| 7F86..7FD7 | `pcm_fuel_ve` | Open/idle VE0231 and transition/reset flags |
| 7FD8..8031 | `pcm_fuel_base_publish` | Ordered base equation state and024E publication |
| 7F86..8031 | `pcm_fuel_air_charge` | Contiguous VE/base wrapper |

## Shared input owners and retention

TPS zero remains the existing IAC02F6/7 pair. B1AC admits only when raw00A6 is
greater than its high byte. The F436 target has the literal80 fractional byte;
it is not a byte-target filter. Preserve the resulting word, then cap at5B24
with a zero fraction when its high byte meets or exceeds the cap. Normalization
adds128 to this word with16-bit wrap before taking the high byte. Subtract that
zero from raw TPS with a zero floor, multiply by5B26, add32, then perform both
saturating shifts. The fuel wrapper saves the previous01D9 before the helper;
0098.0 substitutes5B23 for engine TPS while retaining the normal result at01A6.
The zero learner is a separately callable transmission-side producer, not a new
unconditional action in each fuel call.

Coolant uses the FC45 table when first-conversion0043.7 or range004E.0 is set,
otherwise FD45. It publishes00A8, updates004E.0 at106/120 hysteresis thresholds,
then applies any0016&60 diagnostic substitution according to runtime versus5B18.
Publish0006, clear0043.7, and derive0283 with the fixed16 offset and192 cap.
004E remains the existing board-output owner; its other bits are retained.

MAT performs literal SEI, mux4 and bounded conversion, then CLI **before** ADR4
is read. Invert and save the result at0230. Runtime at/below4E45 retains both
diagnostic counters and faults. Above it, enabled low/high tests first clear their
own fault bit and compare the old count to its delay with a strict greater-than
test. Their speed qualifications have opposite polarity. A count can wrap;
disabling a test clears its counter while retaining its existing fault latch.
The FE45 lookup always publishes display0855; either0017&50 fault selects4E48
for effective022F. Existing IAC0017.7 ownership is separate and unchanged.

BARO's optional mux5 ADC route also reads ADR4 after CLI. It saves raw02F3
before adding11 with a byte ceiling. The estimated route admits ignition-off or
a MAP above old BARO before evaluating diagnostic substitutions. Remaining
updates qualify RPM, coolant, TPS and the decel-TPS difference, then apply the
bounded4558 correction matrix. Preserve raw-target publication before filtering,
the nonzero retained-word route, default02F3/02F4 with fraction0, and the four
successive dependent coordinates.02F4 remains `spark.barometric_high`;02F5 is its
new fraction.01CE remains the existing normalized-load divisor owner.

## Density, temperature, VE and base publication

Density is the zero-extended MAP byte's fixed-divisor fractional quotient plus
2649. Charge temperature optionally blends MAT with a zero-floored coolant/MAT
difference and the4AE3 air-rate curve. Preserve the separate shift overflow and
later MAT-add overflow, without adding a rounding step. The4AF4 result forms
`(value<<7)+7480`. This air-rate input is the prior0232 high byte, already owned
by `iac.runtime_high`; the base publisher now updates that same owner and its
0233 fraction rather than introducing a duplicate word.

VE transforms load above64 with a rounded half plus32. Open selection uses
TPS48DA, VSS48D8 or RPM62>=72. Idle uses filtered RPM63 capped at144. A successful
return from open to idle clears004F.3 and can set004F.5 when integrator020F is at
or below490F. Preserve when each flag changes relative to the lookup and final
0231 store. The idle-state flag0050.7 is not substituted for these entry tests.

| Matrix read view | Default backing | Endpoint behavior |
|---|---|---|
| BARO4558, data455B |48 bytes | Includes six neighboring PE-cap bytes through458A |
| Open VE49D5, data49D8 |177 bytes | Includes idle-header byte4A88 |
| Idle VE4A88, data4A8B |100 bytes | Includes MAT-blend neighbors through4AEE |

The helper still reads neighbors at zero-weight endpoints and retains wrapped
row-stride multiplication. These extra bytes are source read views, not added
independent calibration parameters. The test fixture checks three527-byte
expanded views for modified offset/stride profiles; production uses the bounded
stock views. Both256-byte coolant tables and the complete MAT curve are checked
directly against ROM, including every read-view overlap.

The live base publisher retains separate density/temperature, cylinder volume,
VE, period, AFR and injector-flow stages. Store0238,0234,0232/33 and024E in that
order, sampling inputs at their consuming stages. Zero or overflowing fractional
division, staged quotient truncation and each saturation remain explicit. The
existing pure `pcm_fuel_base` remains available for fixed-input arithmetic tests;
this publisher makes its runtime state handoffs visible. Air charge0234 is
reloaded for AFR division; the period-normalized0232 result is a separate output.

## Verification and unfinished callers

The suite contains1,015,696 compiled-C/ROM comparisons across all336 scoped
instruction starts, including1,953 selected failure prefixes and1,024 retained
history calls. It checks930 distinct source-profile bytes (943 read-view entries,
including overlaps) and1,581 expanded fixture-view bytes against stock.
It compares compiled C with real ROM instructions for direct entries,
the contiguous VE/base body, explicit sensor/air/output/REF joins and retained
histories. It checks mapped state, typed bus order, literal masks, completed
slice frames, source-profile bytes and actual zero-weight neighbor reads.
Sweeps cover TPS fractions/gains, coolant ranges/fault substitutions, MAT option
and old-count behavior, BARO fallback/filtering, charge-blend saturation, VE
coordinates and base-equation period/divisor boundaries. Configuration-error
contracts also check completed prefixes and bounded lookup failures.

These explicit joins are not a replacement for the full scheduler's admissions.
Load calculation normally consumes an earlier density sample; charge temperature
likewise depends on an earlier air-rate result. Required broad fuel/slot prefixes
and their other work remain unimplemented rather than being skipped to call a
new slice. Slot1 BARO, slot4 coolant, slotD MAT and slotF temperature wrappers
therefore remain boundaries, as do the retained/initialization and wider
transmission TPS callers. Running-fuel admission, commanded AFR/PE/startup, AE,
O2/BLM and remaining EGR dependencies are the next milestone work.

Both host routes have44 checks:22 quick contracts/provenance checks and22 ROM
suites. Hardware ADC readiness, target interrupt/frame ABI, cycle/stack budgets,
memory layout, ASIC response and delivered fuel remain separate validation.
