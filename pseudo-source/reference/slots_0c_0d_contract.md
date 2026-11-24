# Slow scheduler slots 0C and 0D

Both entries execute through `pcm_dispatch_slot` on the ordinary 16-slot
schedule. Each runs ten times per 160-phase cycle. The recorded BMHM image
has SHA-256 `6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.

| Entry in execution order | Behavior at that call |
| --- | --- |
| Slot 0C, `$7B44 → $CC35` | While stopped, seed starting coolant at `$0282`, the filtered O₂ word at `$01D0` and the raw sample at `$01D5`. Check the stack sentinel at `$03B0`, set the timer mask, update board control at `$3FFC` with interrupts masked, then clear the output-shadow bit `$004C.7`. |
| Slot 0C, `$CC7C..$CCC0` | Issue the same 20 register writes used by reset. Reset alone follows these with the two port clears and the `$306E` word write. |
| Slot 0D, `$7B48 → $CCC1` | Filter raw O₂ into `$01D0`. Apply the AIR option, service and battery rules. Write AIR at `$3FDA`, purge at `$3FD6` and the shared command at `$3FD4`, followed by the option-qualified `$306C` and `$306A` words. |
| Slot 0D, `$7B4B → $DBFB` | Select and convert MAT, publish the display value at `$0855`, qualify low/high faults at `$0017.6/.4` and publish the control value at `$022F`. |
| Slot 0D, `$7B4E → $DC89` | Apply the diagnostic switch, engine state and phase gates. Run the eligible monitors, age history, update the nine-byte pending and retained fault banks, or drive diagnostic flash codes. Publish the lamp request at `$0072.7`. |

## Controller handoffs

Slot 0C samples the board word after `SEI`. It clears bit 0, applies the
`$400B.0` mask, preserves the `$F3ED` call/return delay, and commits the word
before `CLI`. The following register sequence also runs while the engine is
running. The stopped-engine initialization covers both bytes of `$01D0`.

Slot 0A produces purge duty at `$01D6`. Slot 0D writes `$B000 | (duty << 3)`
to `$3FD6`. Engine service can select a substitute duty from `$0394`. The
shared `$3FD4` override tests a separate mask at `$0393`. Two consecutive
battery observations at or above raw 171 take the output-clear path, including
while the engine is running.

The diagnostic pass can consume a MAT fault from the conversion that just
finished. It also consumes named IAC, MAP, spark and O₂ faults and the live
transmission diagnostic bytes. The monitors retain their byte or word counters
and phase gates. A qualified EGR integrator change, an O₂ fault and a stalled
EST counter each publish into the same state read by their downstream controllers.

An empty pending bank (`$0056..005E`) takes a snapshot of the enabled live
faults. Subsequent calls intersect those candidates with live and enabled bits.
A surviving candidate that exceeds its selected delay is ORed into history
(`$000B..0013`). The routine resets the age, recomputes the retained checksum
and applies a separate lamp mask. With the diagnostic switch set and the engine
stopped, the flash routine starts at code 12 and scans the nine history bytes
from the most significant bit down.

Engine and transmission service clears apply each ROM keep mask to the live
controller flags after the addressed write succeeds. An engine clear can
remove a pending IAC fault while preserving a transmission fault. A
transmission clear keeps the pending bank until the next reporting pass
intersects it with the cleared live bank.

## Verification

| Measurement | Slot 0C | Slot 0D |
| --- | ---: | ---: |
| Resident instruction starts reached from entry | 64 of 64 | 846 of 846 |
| Conditional branches exercised in both directions | 3 of 3 | 208 of 208 |

| Compared C/ROM cases | Count |
| --- | ---: |
| Register refresh and shared outputs | 252 |
| MAT conversion and diagnostic display | 228 |
| Signal and governor monitors | 306 |
| EGR monitors | 276 |
| O₂ monitors | 197 |
| Fault storage, lamp and digit selection | 608 |
| Retained histories, including paired slot admissions | 268 |
| Failures injected at successive logical transactions | 1,360 |
| **Total** | **3,495** |

The replay compares the ordered byte and word transactions, IRQ mask changes
and delay, accessible RAM and register snapshots, and 21 named controller
outputs. It uses the stock calibration and controlled threshold variants. In
one continuous 758-admission trace, the ROM and C displayed 12, 13 and 92
three times each and returned to 12. Fault-injection cases compare the
committed prefix at the point the addressed operation fails.

The host integration fixture follows slot 0A into the purge command, a MAT
fault into retained history and the active-low board lamp, and independently
produced IAC and transmission faults through pending, service clear and
reseed. It also checks a failed clear and successful retry. The kernel fixture
checks all 160 scheduler phases. Electrical outputs, interrupt arrival
timing and target execution still require hardware validation.

[Whole-slot replay](../tests/compare_slots_0c_0d_rom.py) · [Host handoffs](../tests/slots_0c_0d_test.c) · [Factory diagnostics](../../docs/analysis/FACTORY_DIAGNOSTICS.md) · [Factory emissions](../../docs/analysis/FACTORY_EMISSIONS_CONTROL.md)
