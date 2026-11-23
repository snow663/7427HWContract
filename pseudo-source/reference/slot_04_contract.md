# Slow slot 04 diagnostics and adaptive cells

The normal scheduler calls `pcm_slot_04` at stock entry `$7AC7`. It runs on
ten phases of the 160-phase cycle. Each alternating group runs five times.
The common diagnostics finish before the branch samples phase bit 4.

| When | Stock calls, in order | Result |
| --- | --- | --- |
| Every call | `$C8B1` | Monitors the three solenoid patterns (codes 81–83), battery (52, 53, 75) and barometric input (63, 64). Four other stock entries return immediately. |
| Phase bit 4 clear | `$E75F`, `$E793`, `$C96A`, `$C9C0`, `$C9F7` | Qualifies the two raw coolant faults, converts coolant, advances the filter at `$00A9` and publishes the environmental lookup results and burst gain. |
| Phase bit 4 set | `$B9EE`, `$B99F`, `$EAB1`, `$EAE4`, `$C8D6`, `$C8FD` | Services adaptive reset and restore requests, qualifies both transmission-temperature faults, converts and filters the transmission temperature at `$00B5`, and derives cold weight `$00AB` from filtered engine coolant. |
| After either group | `$7AF1..$7B02` | Clears `$006F` mask `$24`. Rebuilds bit 2 from `$0016.0` and bit 5 from `$0017.7`, preserving other bits across each write. Fuel and governor logic consume the result. |

The diagnostic freeze bit is checked at each monitor entrance. The regular
sensor calculations, adaptive service and final fault publication still run
when the monitors are frozen. Code 52 has a 16-bit timer and code 53 has an
8-bit timer. Both compare battery against their own upper thresholds. Code 83
requires both pattern bits. The two other solenoid monitors each test one
bit. The first good observation consumes its recovery opportunity even if
the retained budget prevents clearing the fault.

## Adaptive-cell handoff

Service command 4 can request both operations through `$011A`. Reset fills
three banks of 17 bytes with `$80`. Restore then loads each bank through its
own ROM pointer. For each cell, the PCM reads the old cell and checksum,
masks interrupts around the cell write and the adjusted checksum write at
`$032B`, then unmasks them before advancing the cell counter. The update
preserves the byte sum of the cells and checksum. The stock restore values
are all `$80`. The tests also supply 51 distinct values and permute the
source bank pointers so bank selection and write order can be distinguished.

## Verification

The compiled C is compared with the recorded BMHM ROM executed from `$7AC7`.
The verified 64 KiB image has SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.

| Check | Result |
| --- | --- |
| Whole-slot cases and retained passes | 2,895 comparisons. Together they reached all 602 resident instruction starts, including the 20 in the slot wrapper and the 582 in its callees. |
| Injected failures | 1,296 comparisons of the attempted transactions, RAM, named state and interrupt-mask state at the failure. |
| Total in the slot 04 ROM suite | **4,191 comparisons passed.** |
| Scheduler, service and fuel handoffs | The 160-phase kernel fixture counted five updates for each temperature filter. The host contracts exercised a service-command request through reset, restore and the boot checksum check, plus the governor inhibit after a TPS fault. |

The comparison checks active logical bus accesses and IRQ-mask operations in
order. Existing typed coolant and environmental functions are compared at
their named RAM outputs. Test cases cover threshold equality, byte/word
rollover, held state, calibrated fallback, reversed limits, and input changes
between selected accesses. Target interrupt latency and electrical behavior
remain separate validation work.

[Whole-slot replay](../tests/compare_slot_04_rom.py) · [Scheduler entry](../src/slots/slot_04.c) · [Factory diagnostic analysis](../../docs/analysis/FACTORY_DIAGNOSTICS.md)
