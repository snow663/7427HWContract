# Spark $01EC integer-state trace

Status: **ROM-verified integer dataflow with independent CPU replay**. The producers of `$083F/$01EA`, software initialization, and update admission are now traced in [FACTORY_SPARK_INTEGER_HANDOFF.md](../analysis/FACTORY_SPARK_INTEGER_HANDOFF.md). Physical units and future hardware readback values remain unassigned.

ROM: `BMHM.BIN`, SHA-256 `6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`. Source: `source/31/BMHM_HAC_ORG_7100_to_end.asm`, SHA-256 `7d1f46cab692621f7713c0eed46396feb26dc6eebeced451dc700426f2d49e9c`.

## State and direct cross-references

`L01EC/L01ED` is a 16-bit word. The structural index finds:

| Access | PCs | Purpose in the listed instructions |
|---|---|---|
| Write | `$A6EC` | Store the summed candidate |
| Write | `$A6FD` | Replace it with the period-derived limit on the borrow path |
| Read | `$A6F5`, `$A6FA` | Compare/subtract against the limit, then recover the limit on replacement |
| Read | `$ABB3` | Subtract the current word from the second spark handoff value |
| Read | `$ABB7` | Load the current word for storage into `$3FDC` |

This establishes a dependency on the spark handoff. It does not establish that the word is physically dwell, latency, or another named time quantity. The indexed `$7173 -> $F2FD` clear initializes this word to zero. The direct-reference counts do not include that block-clear effect.

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

The current `$01EC` value therefore participates as a difference against the `$3FDC` readback. The software explicitly stores the word sampled at `$ABB7` into `$3FDC`. Its earlier `$01EC` sample at `$ABB3` is a separate model input, as is the live `$3FDC` readback. Hardware stability and word atomicity are not inferred. The software relationship can be understood without inventing the physical interpretation of either register.

## Dependencies now closed in the bounded integer model

- `$083F` is the exact three-segment function of `$01E8` stored at `$A6D9`.
- `$01EA` has the new-reference decay, load/period candidate selection, and unsigned `period >> 3` cap.
- Software block clears initialize `$01EA/$01EC/$083F`; boot also attempts zero writes to the relevant ASIC words.
- First-reference bypass, count/period qualification, no-reference running updates, and timeout explain producer admission.
- `$AB89-$ABC8` has an exact stack/rolling-state model that predicts the four ordered writes with independently supplied readback samples.

`tools/factory_spark.py` defines the integer models; `tests/test_factory_spark.py` checks them against actual ROM execution, including every 16-bit reference-term/decay input and boundary/random producer and handoff cases. `maps/structure/bmhm_spark_rom_evidence.json` pins the bytes and image identity.

Physical timebase, ASIC register behavior, interrupt interleavings, upstream spark command construction, the external `$180F` extension, and monitoring after `$ABCB` remain separate dependencies. This closure does not assign `$01EC` a physical dwell/latency interpretation.
