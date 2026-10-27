# Factory spark: exact integer terms and handoff

The normal factory path now has an exact integer model from the command entering `$AB3E` through the four writes ending at `$ABC8`. The producers of `$01EA`, `$083F`, and `$01EC`, their software initialization, and their update admission are also traced against actual BMHM bytes. Five previously unresolved indexed accesses are local stack accesses. This closes this bounded arithmetic/dataflow gap; the entire upstream spark calculation and physical ASIC behavior remain separate work.

## Authority and proof scope

The complete image is 65,536 bytes, SHA-256 `6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`. Both supplied stock BMHM filenames have this identity. CPU `$4000-$FFFF` corresponds to the same full-file offsets; the first `$4000` file bytes are padding, while CPU `$0000` is RAM. These are stock BMHM facts, not the truck's separate `2.bin` calibration values.

`bmhm_spark_rom_evidence.json` records the instruction/calibration bytes and source hash. `factory_spark_rom_instructions.csv` contains 425 decoded rows. `tools/factory_spark.py` implements the equations, while `tools/factory_spark_replay.py` executes those bytes on the existing HC11 CPU implementation without using the equation model or new decoder to execute instructions.

The handoff model requires `$0086 bit6` clear. The other path calls the external `$180F` extension; its effects remain unknown. Input words read at separate PCs are independent samples. The replay supplies coherent word values but does not prove hardware word atomicity, counter motion, interrupt interleavings, or physical timing. It stops before the monitor beginning `$ABCB`, which later interacts with `$3FEC/$3FE4`.

## Producer chain

Here `u8` and `u16` mean modulo 256 and 65536; shifts are unsigned. Addresses identify stored words unless explicitly called bytes.

| State | Producer | Exact role |
|---|---|---|
| `$005F` | `$A5E8/$A5FC` | Multiply basis derived from the live period |
| `$01E8` | `$A5EA` | Unscaled period sample from `$3FC0` |
| `$01EA` | `$A50A`, `$A6A4/$A6B5` | Event decay, then adaptive candidate and unsigned period cap |
| `$01E6` | `$A6BB` | Previous period for the next adaptive update |
| `$083F` | `$A6D9` | Piecewise reference-period term |
| `$01EC` | `$A6EC/$A6FD` | Battery/reference/adaptive sum with unsigned limit |
| `$0201` byte | `$AB72` | RPM-indexed interpolation result |

At `$A5E5`, the period read is copied to `$005F` and `$01E8`. The multiplier is `m = u8(32 * byteROM4141)`. If `m=0`, `$005F` retains the raw period; otherwise `$F550` replaces it with `floor((m*period+128)/256)`. Stock `$4141=$08`, so the low product byte is zero and the raw period is retained. `$01E8` remains unscaled in both cases.

When a new reference flag is consumed, `$A4FB-$A50A` performs:

```text
v = u16(old01EA - (old01EA >> 3) - 1)
01EA = 0 if (v & 0x8000) else v
```

The later `$A687-$A6B5` adaptive update first subtracts bytes `$01C0-$01C2`. If that subtraction does not borrow and its result is at least 32, the candidate is `$FF00 | delta`. Otherwise it computes `candidate = u16(2*(previous_period-period))`; it adopts that candidate only when `u16(candidate-old01EA)` has bit15 clear. This is an N-bit test, not a general signed comparison. The result is then capped to `period >> 3` by an unsigned comparison. Intermediate stores are retained in the replay/model, including the transient `$FFxx` candidate before the cap.

At `$A6BB`, the current period becomes the previous period. The reference term is:

```text
R(p) = (p >> 1) + 79                    for p < 458
     = ((p - 458) >> 4) + 308           for 458 <= p < 1638
     = ((p - 458) >> 2) + 87            for p >= 1638
```

`$A6D9` stores `R(p)` at `$083F`. Then:

```text
candidate = u16(4*max(120-byte00A7, 0) + R(p) + current01EA)
limit = u16(read16(3FC0, A6EF) - 39)
01EC = min(candidate, limit)             # unsigned, after wrapping
```

The limit uses a fresh period read; it is a separate input from the sample at `$A5E5`. A period below 39 wraps the subtraction; the code does not clamp it to zero. `$A703` copies byte `$01C1` to `$01C2`; `$A709` then copies `$01C0` to `$01C1`, so the adaptive comparison uses the older latch. The battery input remains raw counts; conflicting HAC voltage comments do not establish its physical scale.

## Command conversion and stack word

`$AB3E/$AB41` store the incoming command in `$01EE/$01F0`. Bit15 determines `$004F bit0`. The magnitude is the command's low byte, negated as a byte when bit15 is set. It is not a general 16-bit absolute value.

When `$0051 bit6` is clear, `$AB55-$AB61` applies startup scaling:

```text
m = u8(high(01F2) + bit7(low(01F2)))
magnitude = u8(floor(magnitude*m/256) + 1)
```

The product is truncated here; the increment is unconditional. `$FF80/$FFFF` startup words can wrap `m` to zero. With bit6 set, this gain is bypassed.

`$F499` uses byte `$0062` and the table at `$454A`. The header caps the input at stock `$C0`; the index is `input >> 4`, and the fraction is `(input & 15) << 4`. It interpolates between adjacent knots by rounding the absolute difference product, adding or subtracting according to slope. Its actual read geometry includes the neighbor at `$4558`, even at a zero fraction. `$0201` receives one byte.

The rounded `$F550` product is then signed and latency-adjusted:

```text
t = floor((effective_magnitude * word005F + 128) / 256)
saved = u16((t if command_bit15 else -t) - byte0201)
```

`$AB89` pushes B, `$AB8A` pushes A, and TSX addresses the resulting word. If SP immediately before `$AB89` is S, the saved word occupies S-1/S. The accesses at `$AB9A`, `$AB9E`, `$ABA0`, and `$ABA2` all use this word. They are not writes or reads of a global variable at the last immediate X address seen earlier in the listing.

The fifth newly classified stack access is `$AAD4`. `$AACF` saves a byte equal to `A_at_AACB >> 1`; `$AAD4` subtracts it from `$01EE`, with borrow propagated into the high byte. `$AADB` releases the saved byte. Its address is `SP_at_AACF`, independent of any earlier opaque call's stack effects.

## Anchor, branch, and four writes

D is explicitly cleared after saving the timing result. It calculates a separate anchor:

```text
anchor = (u16(-read16(3FC0, AB8E)) >> 4) | 0xF000
candidate = u16(anchor + read16(3FF6, AB97))
difference = u16(candidate - saved)
chosen = saved if (difference & 0x8000) else candidate
```

At nonzero periods the anchor equals `u16(-ceil(period/16))`; at zero it is `$F000`. `$AB9C` is `BMI`, so it tests N alone. Substituting a signed minimum would fail at wrapped/overflow boundaries.

This supersedes the provisional equation that subtracted the period from the timing product and shifted the combined result. The product stays on the stack while the anchor is built independently.

| PC | Target | Written word |
|---|---|---|
| `$ABAA` | `$3FE8` | `first = u16(chosen - read16(3FF6, ABA4))` |
| `$ABBA` | `$3FE6` | `u16(first + read16(3FDC, ABB0) - word01EC_at_ABB3)` |
| `$ABC0` | `$3FDC` | `word01EC_at_ABB7` |
| `$ABC8` | `$3FF6` | `chosen`, restored from the stack |

The two `$3FF6` reads and the two `$01EC` reads remain distinct inputs. The equations therefore predict the ordered write values without assuming those samples are equal. `$F3ED` calls interleaved with the writes are actual RTS instructions; no unrecorded delay-body semantics are introduced.

For a raw command of 57, gain bypassed, RPM byte 40, multiply basis and period 983, both `$3FF6` samples `$F000`, `$3FDC` sample 66, and both `$01EC` samples 79, the model and ROM replay agree on `saved=$FF22` and writes `$3FE8=$0F22`, `$3FE6=$0F15`, `$3FDC=$004F`, `$3FF6=$FF22`. This is review vector 7, not a claim about physical spark angle or operating validity.

## Initialization and update admission

The indexed boot clears establish software zero values for `$005F` (`$716A`), `$01E6/$01E8/$01EA/$01EC/$01F2/$0201` (`$7173`), and `$083F` (`$717C`). `$715B` attempts zero writes to even ASIC words `$3FC0-$3FF8`, including `$3FDC/$3FF6`. Those are verified software writes; they do not establish future hardware readback values. The factory path also has distinct `$FAF7/$FB03` stores to `$3FDC/$3FF6`.

The ordinary scheduler calls `$A466` at `$79FC` on even phases when `$001A bit5` is clear. Its nominal admission interval is two TOC3 ticks, approximately 12.496948 ms. Busy/pending coalescing and other gates prevent treating this as a physical execution-frequency guarantee.

The reference IRQ sets `$0050 bit5` at `$7513` when `$0044 bit4` is clear. `$A4EC` consumes that flag. On its new-reference path the code clears the flag, clears byte `$0260`, decays `$01EA`, and clears the missing-reference byte `$0202`.

- While `$004F bit7` is clear, the first reference sets `$0044 bit3` and jumps to `$AC51`, bypassing period/term conversion.
- Later references require `$3FC0 < wordROM4133`. At or above the threshold, `$0210` is reset and conversion is bypassed. Below it, the byte counter increments; reaching `byteROM4142` sets `$004F bit7`, clears `$0210`, resets `$01F2`, and admits `$A5E5`. The counter arithmetic is byte arithmetic; these are not time units.
- With the running bit already set, a new reference can update the startup gain through `$A581/$F459`, subject to the documented flag branches, before reaching `$A5E5`.
- Without a new reference, the nonrunning path bypasses conversion. The running path can still reach `$A5E5`, incrementing `$0202`; it does not apply the event decay. At entry `$0202 >= $17`, the timeout clears the running-related flags, stores `$FFFF` to `$005F`, clears `$3060 bit4`, and reaches the SWI at `$A5D7`.

From `$A5E5` to `$A687`, the captured branch targets remain within the period/RPM/filter path; its calls are mapped helpers `$F459/$F479/$F436`. On normal return it reaches the term producer. This establishes the update context, without claiming the downstream handoff executes on every scheduler admission or that all physical/reference inputs are valid.

## Validation and remaining work

The 16 spark tests cover all 65,536 reference-term inputs and all 65,536 adaptive-decay inputs; 582 adaptive update cases; every RPM byte against the stock table and two alternating-slope tables; startup/sign/wrap boundaries; all represented BMI outcomes; independent readback samples; 512 randomized full handoffs; stack balance; initialization; first-reference, qualification and timeout branches; and the explicit external-hook boundary. They compare actual instruction execution with separately written formulas. They do not constitute an independent validation of every CPU opcode or a hardware replay.

```bash
python tools/verify_factory_spark.py --rom /path/to/BMHM.BIN
python tools/verify_factory_spark.py --check-recorded
python -m unittest discover -s tests -p 'test_factory_*.py' -v
```

The 71 factory tests and 14 CPU/simulator tests pass, including the actual-ROM 100,000-instruction regression. A recorded check establishes excerpt/output consistency; full-image mode additionally checks the complete hash before using its bytes.

Next, apply this same method to the factory `$024E` fuel accumulator and `$3FCE` handoff: enumerate caller-bound helper updates, reduce every normalization/mode branch, close initialization, and predict exact output words against ROM execution. Spark's remaining separate dependencies are upstream command construction, the `$180F` extension, post-handoff monitoring, physical timebases/ASIC behavior, and interrupt interleavings. Transmission, emissions, service, and diagnostics also remain in the full-factory denominator; this bounded closure supplies no whole-ROM completion percentage.
