# Math Helper LF550

## Purpose

Classify `LF550`, the math helper used in the spark degree-to-tick conversion path.

## Static Classification

`LF550` is an unsigned 8×16 fixed-point multiply helper. It multiplies an 8-bit scalar in `A` by a 16-bit operand pointed to by `X`, rounds from the discarded low byte, and returns the upper 16-bit result in `D`.

```text
input:
  A = 8-bit multiplier/scalar
  X = address of 16-bit multiplicand, MSB at 0,X and LSB at 1,X

output:
  D = rounded upper 16 bits of the 24-bit product

equation:
  D = round((A * M16) / 256)
  D ≈ (A * M16 + 0x80) >> 8
```

The source comments explicitly identify this as `8 x 16 Multiply with 16 bit result rounded to the upper 16 bits` and document the call/return register contract.

## Known Spark Caller

```text
0xAB76  LDX #$005F
0xAB79  JSR LF550
```

This call occurs after spark magnitude/sign handling and before latency/period-anchor subtraction. `L005F` is currently classified as the DRP/ref period basis candidate.

## Questions Resolved

| Question | Static answer | Confidence |
|---|---|---|
| What register carries the spark magnitude? | `A` at helper entry | high |
| Does `X` point to a 16-bit operand? | yes, MSB at `0,X`, LSB at `1,X` | high |
| Is pointed operand read as 8-bit or 16-bit? | two 8-bit reads forming a 16-bit operand | high |
| Return register? | `D` / `A:B` | high |
| Operation? | unsigned 8×16 fixed-point multiply | high |
| Scale? | rounded upper 16 bits, equivalent to divide by 256 | high |
| Sign handling? | none inside helper; caller handles sign/magnitude | high |
| Saturation? | none in `LF550`; saturation belongs to different 16×16 helper at `F564` | high |
| Rounding? | yes, carry from low partial product is propagated with `ADCA #$00` | high |

## Helper Body

| PC | Instruction | Operation class | Effect | Notes |
|---|---|---|---|---|
| `0xF550` | `PSHA` | load_input | save multiplier A | Save Multiplier |
| `0xF551` | `LDAB 1,X` | read_pointed_operand | load multiplicand LSB into B | Get LSB of multiplicand |
| `0xF553` | `MUL` | multiply_step | A * low_byte → D | MSB Partial product |
| `0xF554` | `ADCA #$00` | rounding_or_carry_propagation | round low partial product | Round |
| `0xF556` | `PULB` | stack_scratch | restore multiplier to B |  |
| `0xF557` | `PSHA` | stack_scratch | save rounded low-byte partial | Save partial product |
| `0xF558` | `LDAA 0,X` | read_pointed_operand | load multiplicand MSB into A | Get MSB of multiplicand |
| `0xF55A` | `MUL` | multiply_step | MSB * multiplier → D | MSB Partial product |
| `0xF55B` | `PSHX` | stack_scratch | save X | Save |
| `0xF55C` | `TSX` | stack_scratch | X points into stack scratch |  |
| `0xF55D` | `ADDB 2,X` | add_accumulate | add saved partial into low byte of high product | Add in LSB Partial prod |
| `0xF55F` | `ADCA #$00` | rounding_or_carry_propagation | carry propagate / rounding | Round |
| `0xF561` | `PULX` | stack_scratch | restore X |  |
| `0xF562` | `INS` | stack_scratch | discard saved partial |  |
| `0xF563` | `RTS` | return_value | return with D=result |  |

## Helper Algebra

Let:

```text
m = A entry value, unsigned 8-bit
M = [X:X+1], unsigned 16-bit
M_hi = M >> 8
M_lo = M & $FF
```

The helper computes:

```text
partial_lo = round((m * M_lo) / 256)
partial_hi = m * M_hi
D = partial_hi + partial_lo
```

Equivalent working equation:

```text
D = round((m * M) / 256)
D ≈ (m * M + $80) >> 8
```

The exact carry behavior is implemented through HC11 `MUL` carry plus `ADCA #$00`, so an emulator test should verify edge cases around low-byte products ending in `$7F/$80`.

## Caller Inventory

Static caller count found: `35`.

| Caller PC | Caller routine | Local context note |
|---|---|---|
| `0x75B2` | `L74D3` | MUL 8X16 Subroutine |
| `0x784F` | `L77F7` | MUL 8X16 Subroutine |
| `0x7E80` | `L7E80` | MUL 8X16 Subroutine |
| `0x7FE4` | `L7F96` | 8 x 16 Mult w/16b result rounded to upper 16b |
| `0x7FF1` | `L7F96` | 8 x 16 Mult w/16b result rounded to upper 16b |
| `0x803B` | `L8008` | 8 x 16 Mult w/16b result rounded to upper 16b |
| `0x80FF` | `L80D0` | MUL 8X16 Subroutine |
| `0x82DB` | `L82CF` | MUL 8X16 Subroutine |
| `0x8336` | `L82F9` | MUL 8X16 Subroutine |
| `0x835D` | `L82F9` | MUL 8X16 Subroutine |
| `0x837A` | `L82F9` | MUL 8X16 Subroutine |
| `0x851D` | `L84F5` | 8 x 16 Mult w/16b result rounded to upper 16b |
| `0x8599` | `L858B` | 8 x 16 MULT SUBROUTINE |
| `0x85BD` | `L85B2` | 8 x 16 MULT SUBROUTINE |
| `0x85DB` | `L85B2` | MUL 8X16 Subroutine |
| `0x85ED` | `L85B2` | MUL 8X16 Subroutine |
| `0x8605` | `L85F9` | MUL 8X16 Subroutine |
| `0x8F8C` | `L8F43` | MUL 8X16 Subroutine |
| `0x984C` | `L982A` | MUL 8X16 Subroutine |
| `0x9873` | `L985B` | MUL 8X16 Subroutine |
| `0x9E17` | `L9E17` | MUL 8X16 Subroutine |
| `0x9E26` | `L9E17` | MUL 8X16 Subroutine |
| `0x9E41` | `L9E17` | MUL 8X16 Subroutine |
| `0x9E58` | `L9E17` | MUL 8X16 Subroutine |
| `0x9EB5` | `L9E83` | MUL 8X16 Subroutine |
| `0x9EC1` | `L9E83` | MUL 8X16 Subroutine |
| `0x9FF7` | `L9FD4` | MUL 8X16 Subroutine |
| `0xA00A` | `L9FD4` | MUL 8X16 Subroutine |
| `0xA01F` | `L9FD4` | MUL 8X16 Subroutine |
| `0xA032` | `L9FD4` | MUL 8X16 Subroutine |
| `0xA5F9` | `LA5E5` | MUL 8X16 Subroutine |
| `0xAB79` | `LAB69` | MUL 8X16 Subroutine |
| `0xAC6C` | `LAC5E` | MUL 8X16 Subroutine |
| `0xD93D` | `LD8FE` | MUL 8X16 Subroutine |
| `0xD98E` | `LD980` | MUL 8X16 Subroutine |

## Spark-Path Interpretation

For the spark conversion caller:

```text
A = spark magnitude / scalar after sign handling
X = #$005F
M16 = [L005F:L0060] = last DRP/ref period basis candidate
LF550_output = round((A * M16) / 256)
```

This confirms that the degree-to-time bridge is a fixed-point scale of spark magnitude by period basis. The exact physical meaning still depends on the unit of the caller's `A` magnitude and the timebase represented by `L005F`.

## Candidate Equation Locked By Helper

```text
mult = LF550(spark_mag, period_basis)
mult = round((spark_mag_u8 * period_basis_u16) / 256)
```

This should replace the unresolved `LF550(...)` placeholder in `SPARK_TIMING_UNIT_CONVERSION.md`.

## Required New-OS Impact

If the bench tests confirm the upstream units, the minimal spark conversion layer can reimplement `LF550` directly as:

```c
uint16_t lf550(uint8_t mag, uint16_t period_basis) {
    return (uint16_t)(((uint32_t)mag * (uint32_t)period_basis + 0x80u) >> 8);
}
```

No spark writer should be created yet. `L005F`, `L3FC0`, `L0201`, and LA906 rolling-state behavior still require unit/bench classification.
