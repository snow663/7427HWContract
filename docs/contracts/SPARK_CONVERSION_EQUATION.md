# Spark conversion equation

Status: **ROM-verified integer behavior with independent CPU replay** for `$AB3E-$ABCA`, with `$0086 bit6` clear. That bit selects the external `$180F` extension, whose implementation remains open. The command entering `$AB3E` is an explicit input; this does not establish the entire upstream spark calculation.

Authority: the 65,536-byte BMHM image, SHA-256 `6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`. Full derivation, state producers, admission, initialization, and test scope are in [FACTORY_SPARK_INTEGER_HANDOFF.md](../analysis/FACTORY_SPARK_INTEGER_HANDOFF.md). Executable integer model: `tools/factory_spark.py`; independent ROM replay: `tools/factory_spark_replay.py`.

## Raw conversion

All words wrap modulo 65536; bytes wrap modulo 256. `negative` is command bit15. The magnitude uses only the low byte, negated as an 8-bit byte when `negative` is set. It is not a general absolute-value operation on the whole command word.

If `$0051 bit6` is clear, startup scaling first computes `m = u8(high($01F2) + bit7(low($01F2)))`, then `magnitude = u8(floor(magnitude*m/256) + 1)`. That product is truncated; the following increment is unconditional and can wrap.

`$F499` looks up a byte from the header/table at `$454A-$4558`, using `$0062`. It clamps the input to header `$C0`, interpolates between 16-count cells, rounds the absolute knot difference, and adds or subtracts that adjustment according to slope. `$0201` receives the resulting **byte**.

```text
t = floor((effective_magnitude * word005F + 128) / 256)
saved = u16((t if negative else -t) - byte0201)
```

At `$AB89-$AB8A`, `saved` is pushed as a word. X then addresses that word at `SP_at_AB89-1`.

## Separate anchor and stack selection

D is cleared at `$AB8C-$AB8D`. The following shifts operate on the negated period, independently of `saved`:

```text
anchor = (u16(-read16(3FC0, AB8E)) >> 4) | 0xF000
candidate = u16(anchor + read16(3FF6, AB97))
difference = u16(candidate - saved)
chosen = saved if (difference & 0x8000) else candidate
```

`$AB9C` is BMI: selection tests N alone after the wrapped subtraction. It is not a signed minimum. At period zero, `anchor=$F000`; at period one, `anchor=$FFFF`, so a zero period needs its own case.

The previous provisional equation subtracted `$3FC0` from the timing product and shifted the combined result. **That equation is superseded:** the timing result is saved on the stack while the separate anchor is calculated. `D_AB97` means the anchor before the instruction at `$AB97`, rather than a packed version of the timing product.

## Ordered handoff

```text
first  = u16(chosen - read16(3FF6, ABA4))
write16(3FE8, first)                              # ABAA
second = u16(first + read16(3FDC, ABB0) - word01EC_at_ABB3)
write16(3FE6, second)                             # ABBA
write16(3FDC, word01EC_at_ABB7)                    # ABC0
write16(3FF6, chosen)                             # ABC8
```

Different read PCs are separate model inputs. Equality of repeated hardware readbacks, atomic word sampling, hardware counter motion, and physical output timing are not inferred from a flat memory fixture. The monitor code beginning `$ABCB`, including the later `$3FEC/$3FE4` interaction, is outside this bounded contract.

## Engineering scale and older vectors

The historical degree vectors below check the `256/90` angle-scale hypothesis and the multiply primitive only. They do not validate an arbitrary degrees API, startup gain, latency, the anchor, or the four writes. The complete raw-input handoff vectors are `maps/structure/factory_spark_handoff_vectors.csv`, independently checked by `tests/test_factory_spark.py`.

| Name | Assumed degrees | Period basis | A count | Multiply result |
|---|---:|---:|---:|---:|
| zero_deg | 0 | 983 | 0 | 0 |
| five_deg | 5 | 983 | 14 | 54 |
| ten_deg | 10 | 983 | 28 | 108 |
| twenty_deg | 20 | 983 | 57 | 219 |
| thirty_deg | 30 | 983 | 85 | 326 |
| forty_deg | 40 | 983 | 114 | 438 |
| five_deg_2000rpm | 5 | 491 | 14 | 27 |
| twenty_deg_2000rpm | 20 | 491 | 57 | 109 |

Historical vector arithmetic: PASS.

Exact software arithmetic is established for the stated inputs and path. Physical units, the external extension, upstream intent calculation, and ASIC output effects remain separate dependencies.
