# Reset and reference-event C transactions

Authority is the stock BMHM ROM, SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The C source uses named state and its own calibration structure. Original
addresses below identify behavior and provenance, not final C RAM placement.

The REF prefix now connects to the implemented resident event body. See the
[full REF event contract](ref_event_contract.md) for its additional routines,
configuration branches and differential checks.

## Implemented boundaries

| C routine | Stock scope | Behavior |
|---|---|---|
| `pcm_reset_entry` | 7100..711C | Requires the early target-assembly precondition; remains an explicit dependency |
| `pcm_reset_cpu` | CC7C..CCC0, called at 711C; then 711F..712B | 22 ordered byte writes and one word write for CPU, chip-select and board setup |
| `pcm_reset_outputs` | 712B..7164 | Control seed/readback, bit update, SCSR/SCDR word read, SCCR2 write and 29 zero-word transactions through 3FC0..3FF8 |
| `pcm_reference_prefix` | 74EA..751B | Factory gate, TCNT sample, OC1 compare, two separate 3062.6 read/modify/writes, pending latch and 306F write |
| `pcm_reference_event` and callees | 751B..77C6 | Implemented resident acquisition/event/fuel paths; target backend remains separate |

F3ED is an actual RTS in this stock ROM. Its two reset calls add no peripheral
transaction. The control-word read at 7140 remains a real read; the bit update
uses that response rather than assuming the previous write read back unchanged.
The 302E word read includes SCSR and SCDR, and is retained at that width and point
in the sequence. A word callback is not proof of an indivisible physical bus cycle.

The source calibration carries the startup seed and 64 reference-delay words.
Stock 400B.0 clear selects B93A; setting it selects B91A. The reference table is
copied from 465D..46DC. Its index is `rpm_coordinate >> 2`, equivalent to the
stock byte offset `(RAM0062 >> 1) & FE`. Addition to sampled TCNT wraps at 16 bits.
These source fields are not a serialized calibration format or fixed memory layout.

## REF state and sampling

`reference.pending` corresponds to 0050.5. It coalesces repeated events into one
bit; an inhibited arrival preserves an already pending bit. The gate corresponds
to 0044.4 and is separate from the existing 0051.3 software-ignition-off field and
from the periodic scheduler's pending bit.

The RPM coordinate is sampled after the TCNT callback returns. The inhibit gate
is sampled after both board strobes. Each of the 3062 read/modify/writes takes a
fresh byte sample and preserves its unrelated bits. Neither the prefix nor the
stock continuation opens ordinary maskable nesting. Target entry/RTI must supply
the real frame and masked-entry contract.

Factory mode returns `PCM_FACTORY_BOUNDARY` before device transactions. A normal
prefix returns `PCM_OK` and the IRQ wrapper enters the implemented event body.
A failed I/O callback stops
at that prefix and returns its status. In particular, failure of the final 306F
write occurs after the pending latch may already have been set. No rollback or
physical safe-state action is invented by this host API.

## Early reset remains target work

The stock early prelude establishes SP, writes INIT at 103D, and configures OPTION,
TMSK2, OPT2 and BPROT. A real target must perform the required early instructions
in assembly before ordinary C entry. The `PCM_RESET_ENTRY` binding checks that
precondition; it must never reset SP from inside an active C call frame.
Missing precondition code stops the reset outline before the new C transactions.
The host binding used in tests is a fixture, not target startup assembly.

Retained RAM, sensors, controller initialization, later serial setup, final
ABI/linker placement and physical drivers remain separate
work. Zero writes are stock transactions, not a declaration that every output is
inactive. See [hardware boundaries](../../docs/analysis/FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md)
and [startup/EST lifetimes](../../docs/analysis/FACTORY_STARTUP_REF_EST_LIFECYCLE.md).

## Independent checks

`tests/compare_hardware_rom.py` runs compiled C and actual stock instructions
with explicit peripheral readbacks. It compares complete ordered read/write
transcripts, including width, and the REF pending state:

- 128 startup cases cover both documented selector settings, control readbacks
  and SCSR/SCDR inputs. The early assembly prelude's I/O is outside this C slice.
- 4,096 ordinary REF cases cover all 256 RPM coordinates, four timer samples,
  both initial pending states and both inhibit states. Separate 3062 samples
  exercise changes to unrelated bits between the two read/modify/writes.
- 16 factory REF cases verify exit before any device transaction.
- The C harness injects failure at every one of 64 transaction positions across
  the three implemented slices. It also checks missing-entry
  boundaries, distinct pending/ignition fields and the state-sampling points.

This work exposed a simulator operand-fetch bug: STX/STY/STS fetched their
write destination before storing. The CPU now forms the address without that
extra read. A regression checks 16 legal word-store forms, including STD controls,
using a destination that rejects reads. The operation definitions are in
[NXP M68HC11ERG, instruction table, page 19](https://www.nxp.com/docs/en/reference-manual/M68HC11ERG.pdf).
Instruction-cycle accounting was not changed by this fix.

Both the Python/`cc` and CMake/CTest routes include these checks. They establish
selected software transactions and fixture-state results, not physical ASIC
behavior, target instruction timing, a target interrupt ABI or a bootable BIN.
