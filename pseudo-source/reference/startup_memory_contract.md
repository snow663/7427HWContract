# Working RAM initialization and the literal clear helper

`pcm_reset_ram` now implements 7164..7189 directly. The old RESET_RAM task
identifier remains reserved and unused. It calls `pcm_ram_clear` at F2FD..F325
for 0036/count00CA, 0100/count019D and 0800/count0100, then the existing
0360..03FE serial byte-clear loop. Retained ranges outside those spans survive.
03FF is excluded by the clear loop; the actual HC11 JSR stack can still write it.

The helper aligns its unrolled path using the remaining count, not the address.
It emits byte clears until the count is divisible by eight, then four word
writes per block. The stock eight-bit block counter retains truncation: zero
count clears 2048 bytes, and the low byte of count/8 determines the word-block
loop, with zero again meaning 256 blocks. Address increments wrap at 16 bits.
This is the literal stock helper rather than a general memset contract.

Each logical write must update its canonical named owner through the platform
provider. Word writes remain one provider operation; splitting them would change
failure prefixes and device semantics. The serial loop uses its existing native
serial ownership adapter. No production 64KB RAM image is introduced. A failed
write returns immediately with earlier writes retained; no rollback, mask change
or watchdog service is inserted.

The startup-memory fixture reuses the checked serial/fuel state adapter and
compares exact ordered write widths, addresses and values, returned status and
a complete-image Adler checksum against actual BMHM instructions. The boot
digest excludes only the private HC11 JSR bytes 03FE/03FF; native C has no target
call frame. Direct helper cases retain those bytes in the checksum. Separate C
contracts check the serial-loop 03FF exclusion and selected native-state joins.
This does not establish target ABI, stack fit, memory backing or electrical I/O.

The ROM authority remains BMHM SHA256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The suite passes 1,008 comparisons across all 35 scoped instruction starts.
Validation covers count/address wrap, odd word destinations, low-byte block-count
truncation, every selected write-failure prefix, all 256 initial byte patterns
for the complete boot clear, and all scoped instruction starts. The broader
retained-memory policy and controller initialization remain explicit boundaries.

This is the second PR in the active three-PR source batch after service lifecycle
PR #30. The third implements initial acquisition and factory admission; check
and merge the three in order after the batch's required checks pass.
