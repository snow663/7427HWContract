# OC1 knock-counter observation

`pcm_oc1_irq()` now implements the complete resident handler at CE7C..CEBA,
reached through vector FFE8. The separate REF prefix remains the writer of the
OC1 compare. Authority is the stock BMHM ROM, SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.

## Transactions and named state

| Source item | C interface | Behavior |
|---|---|---|
| 3023 | `PCM_TFLG1` | Write `0x80` first to acknowledge the OC1 flag |
| 3FC8 | `PCM_KNOCK_COUNTER` | Take one word sample after acknowledgement |
| 0203 | `knock.sample_baseline` | Subtract the previous word with 16-bit wrap; then always save the successful sample |
| 0062 | `reference.rpm_coordinate` | Direct table index `rpm_coordinate >> 2`; the source loads it separately for each table |
| 45DB..461A | `calibration.knock.noise_floor[64]` | Reject a clipped delta at or below the selected byte |
| 461C..465B | `calibration.knock.observation_bias[64]` | Add only after a positive excess passed the floor gate |
| 020D | `knock.observation_accumulator` | Saturating unsigned-byte accumulation |

After unsigned subtraction, any nonzero high byte clips the delta to 255.
FFFF→0000 is therefore delta 1, while a backwards 0001→0000 sample produces
wrapped FFFF and clips to 255. This is not a signed-difference or reset detector.
The baseline advances even when the clipped delta fails the floor comparison.

The two saturations retain their separate source branches. If excess plus bias
carries, write 255 directly without reading the old accumulator. Otherwise add
the old accumulator and cap that addition at255. A zero or negative excess exits
before adding bias. Neither curve is interpolated, and table entries are raw
source counts rather than RPM or retard-degree engineering units.

The source has no factory-mode gate, no TOC1 write and no ordinary nesting.
Target entry/RTI and the masked-entry contract remain assembly responsibilities.
The C body preserves that contract without calling mask/unmask bindings.

Cold initialization clears the named knock-state fields. They remain separate
from the REF pending latch and periodic busy/pending state. The code uses named
state and immutable calibration; original RAM/ROM addresses do not prescribe
our final target allocation or a serialized calibration layout.

## Failure and physical scope

Absent calibration returns `PCM_BAD_CONFIGURATION` before I/O. Missing hardware
or a callback failure returns at the current prefix. An acknowledgement failure
leaves the baseline and accumulator untouched. A failed word read leaves those
fields untouched after the successful flag acknowledgement. No rollback,
hardware trap behavior or physical recovery action is synthesized by this API.

A word callback preserves access width; it does not prove coherent physical
counter readback. Passing these tests does not establish how the knock interface
generates 3FC8 counts or how a physical sensor responds.

The scheduled decay/fault routine at CEBB..CF15 and normal-spark consumption at
AA81..AADB are now implemented; see the [knock control contract](knock_control_contract.md).
The latter atomically consumes and clears020D. OC1 observation counts are not
themselves knock-retard degrees.
See the [upstream spark contract](../../docs/analysis/FACTORY_UPSTREAM_SPARK_CALCULATIONS.md)
and [physical hardware boundaries](../../docs/analysis/FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md).

## Independent checks

`tests/compare_oc1_rom.py` runs compiled C against actual stock CPU interrupt
entry, all handler instructions, and RTI. It compares baseline/accumulator state,
flag effects, the ordered byte-write/word-read transcript, preserved shared
state and the REF compare/latch relationship:

- 261,632 numeric cases include every 16-bit unsigned counter difference, every
  byte delta/floor pair, every positive excess/bias pair and every positive
  excess/accumulator pair. Table and counter-wrap boundaries are explicit inputs.
- 16 hardware-failure cases compare both transaction-prefix exits.
- 1,280 REF→OC1 pairs cover all 256 RPM coordinates and five counter samples.
  These are selected interrupt sequences, not measured physical compare timing.
- All 34 handler instruction starts execute, and all 128 compiled table bytes
  match the stock ROM.

The fixture supplies coherent counter words and CPU write-one-clear timer flags;
it does not simulate knock physics or peripheral interrupt admission. Real ROM
entry/RTI preserves the selected register/frame state. The C target ABI, actual
instruction/stack costs, hardware timing and final backend remain unverified.

Both local verification routes include OC1 contracts and differential checks.
The previous kernel, fuel, reset and full REF checks remain in place. The source
inventory is 129 routines: 55 implemented outlines, 40 dependency boundaries and
thirty-four algorithms. These counts and instruction coverage are not a whole-program
equivalence percentage or a target BIN build.
