# Spark Timing Unit Conversion

## Purpose

Document how degree-domain spark/retard state is converted into the timing-domain value consumed by `LA906` at `0xAB97`.

This is an equation/units contract, not a spark writer.

## Known Sink

```text
0xAB97  ADDD L3FF6
```

At this point, `D` is no longer raw spark degrees. It is a timing-domain offset or absolute/rolling timing value input to the LA906 bridge.

## Known Upstream Chain

```text
L01FD final spark advance
→ L01EE current retard/signed offset state
→ sign/magnitude transform using L004F bit0
→ latency lookup result L0201
→ multiply against DRP/ref period basis L005F
→ subtract latency
→ combine with L3FC0 / period term
→ D at 0xAB97
```

## Candidate Units

| Symbol | Candidate unit | Evidence | Confidence |
|---|---|---|---|
| `L01FD` | spark degrees, likely GM-scaled | labels `FINAL SPK ADV` | medium-high |
| `L01EE` | signed spark/retard offset | feeds sign/magnitude conversion before `LA906` | medium |
| `L005F` | last DRP/ref period basis | `LDX #$005F` before `LF550` multiply | medium |
| `L0201` | latency correction | RPM-indexed lookup, then `SUBB L0201` | medium |
| `L3FC0` | ASIC timing/period source | `SUBD L3FC0` before sink | medium |
| `D at 0xAB97` | timing-domain offset/command input | feeds LA906 rolling timing math | high static / physical unit pending |

## Equation Candidate

Provisional form:

```text
D_AB97 = f(L01EE, L005F, L0201, L3FC0)
```

More concrete static shape:

```text
spark_mag = abs_or_startup_override(L01EE, L01F2, L004F bit0)
latency = lookup_$454A(RPM/25) → L0201
period_basis = L005F
period_anchor = L3FC0
mult = LF550(spark_mag, period_basis)
D_AB97 ≈ ((mult - latency - period_anchor) >> 4) with high-nibble/sign tagging
```

Do not treat this as final executable math yet. `LF550` return scaling, borrow behavior around `SUBB L0201`, and the meaning of `ORAA #$F0` still need helper-level trace or bench proof.

## Static Conversion Stages

| Stage | PC | Operation | Input | Output | Scale candidate | Confidence |
|---|---|---|---|---|---|---|
| degree_accumulator | `0xA81B` | store final spark after low-octane/base/modifier path | `L01FC/L020B/modifiers` | `L01FD` | unknown; likely GM scaled spark degrees | medium_high_static |
| degree_to_signed_offset | `0xAA1A-0xAA30` | transform final spark into current retard/2s-complement offset state | `L01FD` | `L01EE` | same degree-domain scale as L01FD until conversion | medium_static |
| knock_low_octane_fold_in | `0xA811,0xAABC-0xAAD8` | subtract or add retard sources before timing conversion | `L020B/L020C` | `L01FD/L01EE` | same as spark degree-domain variables | medium_high_static |
| sign_magnitude_transform | `0xAB47-0xAB50` | if negative set L004F bit0 and negate B; clear A | `L01EE` | `B with L004F bit0 sign` | 8-bit magnitude used for multiply | medium_static |
| startup_override_magnitude | `0xAB55-0xAB5B` | startup path can replace/scale the normal B magnitude | `L01F2` | `D` | startup-specific; bench required | medium_static |
| latency_lookup | `0xAB69-0xAB72` | 2D lookup indexed by engine RPM/25 stores latency correction | `L0062/table_$454A` | `L0201` | table units unknown; subtracted from B after multiply | medium_static |
| degree_period_multiply | `0xAB76-0xAB79` | multiply 8-bit spark magnitude against 16-bit period basis using LF550 | `B magnitude, L005F` | `D` | likely 8x16 fixed-point multiply; exact LF550 contract still needed | medium_static |
| latency_subtract | `0xAB84` | subtract latency lookup from low byte of multiply result | `L0201` | `D/B` | same low-byte units as LF550 output | medium_static |
| period_anchor_subtract | `0xAB8E-0xAB96` | subtract period/timebase term, shift right 4, set high nibble marker/sign bits | `L3FC0` | `D_AB97` | `(multiply_result - L3FC0) >> 4` with high-nibble tagging | medium_static |
| la906_sink | `0xAB97` | add rolling anchor L3FF6 | `D_AB97,L3FF6` | `D` | same timebase as LA906 ASIC timing writes, exact count/us pending | high_static_sink_low_physical_units |

## LF550 Helper Gate

The high-value unresolved item is the call at:

```text
0xAB76  LDX #$005F
0xAB79  JSR LF550
```

The next static sub-target is to define `LF550`:

```text
Does LF550 implement 8x16 multiply?
Does it divide or normalize by 256?
Which register carries the 8-bit spark magnitude?
Where does the 16-bit product return?
Does it preserve X as pointer to L005F or consume memory at X?
```

If this contract remains fuzzy after bench, add `docs/contracts/MATH_HELPER_LF550.md` before any spark writer work.

## Bench Sanity Math

At a given RPM:

```text
seconds_per_degree = 60 / (RPM × 360)
```

At 1000 RPM:

```text
1 crank degree = 166.667 us
5 degrees = 833.333 us
```

If spark uses the same 1/65536-second timebase as EFI PW, then:

```text
1 count = 15.258789 us
5 degrees at 1000 RPM ≈ 54.6 counts
5 degrees at 2000 RPM ≈ 27.3 counts
```

Do **not** assume this timebase. Use it as a bench clue: if a +5° step at 1000 RPM moves the LA906 timing-domain value by about 55 counts and the delta halves at 2000 RPM, the units are likely close to 1/65536 second.

## Required New-OS Boundary

Current static evidence supports this future boundary:

```text
minimal spark strategy produces desired/final spark in degree-domain
conversion layer computes LA906-ready timing-domain offset using period and latency
LA906 bridge maintains rolling ASIC state and writes $3FE8/$3FE6/$3FF6/$3FDC/$3FE4
```

Future API options:

```text
Option A: caller provides final spark degrees; conversion layer produces D_AB97.
Option B: caller provides LA906-ready timing-domain D directly.
Option C: caller maintains stock-compatible L01FD/L01EE/L0201/L01EC/L3FF6/L3FDC state.
```

## Open Questions

- Is `L01FD` scaled as whole degrees, half-degrees, or 256/90-degree style units?
- Is `L01EE` advance-positive or retard-positive before the sign split?
- Is `L004F` bit0 the sign of the timing offset in every path?
- Does `L005F` represent 90°, 180°, 360°, or 720° of crank/reference period?
- Is `L0201` EST/module latency in ticks, table-scaled counts, or a subtractive byte correction?
- Does `L3FC0` represent current DRP period, prior event capture, or ASIC timing anchor?
- Is `D_AB97` in the same timebase as EFI PW or a spark-only ASIC count domain?

## Stop Condition

Do not write `SPARK_WRITE` until this file can answer:

```text
For X degrees at Y RPM/ref period, what LA906 input value should be produced?
```
