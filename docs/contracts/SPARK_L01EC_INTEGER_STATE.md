# Spark $01EC integer-state trace

Status: **source-derived integer dataflow**. Physical meaning/units, target-ROM correspondence, isolated execution, and first-event seed validity are not established by this trace.

Source: `source/31/BMHM_HAC_ORG_7100_to_end.asm`, SHA-256 `7d1f46cab692621f7713c0eed46396feb26dc6eebeced451dc700426f2d49e9c`.

## State and direct cross-references

`L01EC/L01ED` is a 16-bit word. The structural index finds:

| Access | PCs | Purpose in the listed instructions |
|---|---|---|
| Write | `$A6EC` | Store the summed candidate |
| Write | `$A6FD` | Replace it with the period-derived limit on the borrow path |
| Read | `$A6F5`, `$A6FA` | Compare/subtract against the limit, then recover the limit on replacement |
| Read | `$ABB3` | Subtract the current word from the second spark handoff value |
| Read | `$ABB7` | Load the current word for storage into `$3FDC` |

This establishes a dependency on the spark handoff. It does not establish that the word is physically dwell, latency, or another named time quantity. Global/indirect initialization remains outside these direct-reference counts.

## Exact producer ordering

The relevant instructions at `$A6DC-$A6FD` compute the following unsigned integer transformation:

```text
u16(x) = x modulo 65536

b = unsigned byte L00A7
voltage_add = 4 * max(120 - b, 0)

candidate = u16(voltage_add + word(L083F) + word(L01EA))
L01EC = candidate                         ; A6EC

limit = u16(word(L3FC0) - 39)
comparison = u16(limit - candidate)       ; A6F5 sets borrow

if unsigned subtraction borrowed:         ; candidate > limit
    L01EC = u16(comparison + candidate)   ; A6FA-A6FD, equal to limit
```

Consequently the final word is `min(candidate, limit)` in the unsigned integer domain **after both preceding wrap operations**. It is not safe to replace the wrapped `period - 39` with an assumed nonnegative engineering clamp. The add operations also contain no intervening saturation branch in this slice.

The source comment beside `#120` says `2.4 VDC`, while the comment beside `L00A7` says battery `VDC/10`. This trace preserves the executable threshold **120 counts**; it does not use that conflicting comment to assign physical units.

## Downstream rolling-state relationship

After the first handoff write to `$3FE8`, the listed sequence is:

```text
second_command = u16(first_command + readback_word_3FDC - current_L01EC)
write second_command to $3FE6             ; ABBA
write current_L01EC to $3FDC              ; ABC0
```

The current `$01EC` value therefore participates as a difference against the `$3FDC` readback. The software explicitly stores the current word back into `$3FDC`; whether the ASIC can change that value between calls is still unproven. The software relationship can be understood without inventing the physical interpretation of either register.

## Remaining dependencies

- Producers, meaning, units, and update contexts of `$083F/$01EA`.
- Physical timebase and validity of `$3FC0`, especially around startup and missing reference.
- Full stack-based computation that produces the first command and updates `$3FF6` at `$AB89-$ABC8`.
- Initialization and reset of `$01EC/$3FDC`, including indexed block-clear paths and first-event behavior.
- Target-ROM byte verification and independent execution/replay of this integer relationship.

This closes the direct producer/consumer relationship and its listed arithmetic. It does not close the entire spark conversion or assign an ASIC physical meaning.
