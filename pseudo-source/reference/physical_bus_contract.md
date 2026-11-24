# Physical memory / peripheral backend, first connected slice

**Scope:** `pseudo-source/platform/hc11_bus.c` and
`hc11_native_mmio.c` bind the existing `PcmPlatform` read/write,
IRQ-mask and timing interfaces to a **capability-granted address-window
provider**. This is a host-tested target boundary, **not** a completed
or flashable 16197427 driver. No factory algorithm or calibration was changed.

## Source-grounded resource partition

The stock reset sets INIT=03 at $103D, then programs CSCTL=$AC,
CSGSIZ=$CB, CSGADR=$00 and CSSTRH=$00. Under the *F1-style* interpretation:

| Logical CPU address | Classified resource | Binding policy |
| --- | --- | --- |
| $0000..$03FF | relocated internal 1 KiB RAM | Can grant named physical RAM bytes; no claim native `Pcm` layout equals factory RAM |
| $0400..$0DFF; $1000..$1FFF | external general selection | **No implicit backing/alias**; grant only verified fitted subwindows |
| $0E00..$0FFF | **conditional** EEPROM overlay if CONFIG=$0B and matching derivative | No implicit EEPROM write or device identification |
| $2000..$2FFF | remaining program selection, backing unproven | No implicit ROM/RAM |
| $3000..$305F | internal CPU registers | Explicit grants and required write authorization |
| $3060..$37FF | external board IO1 select | Explicit grants and required write authorization |
| $3800..$3FFF | external board IO2 select, includes $3FC0..$3FFF ASIC use | Explicit grants and required write authorization |
| $4000..$FFFF | code/calibration/vector program image | Explicit reads, runtime writes rejected |

This follows [the F1 selection evidence](../../docs/analysis/FACTORY_EXTENSION_MEMORY_INTERFACE.md)
and [Rev B CS/EN audit](../../docs/investigations/REVB_CS_EN_ADDRESS_MAP.md).
It does **not** assert measured address aliases, fitted 8 KiB RAM,
CONFIG response, or which board components respond. The read/write
permissions on **every window** are configured explicitly.

## Transaction and authorization contract

- `pcm_hc11_bus_bind` uses immutable, nonoverlapping, sorted physical
  address grants. It rejects missing windows, wrong resource tags,
  prohibited ROM writes, implicit subword/word access and word transfers
  crossing a granted boundary. No generic 64 KiB mirror is allocated.
- `pcm_read16/pcm_write16` remain a **single logical provider call**.
  A native raw word transaction must use CPU high-byte/low-byte order
  and honor register-specific latching; the bus bridge does **not**
  silently substitute two byte callbacks. A real word is not assumed
  interrupt-atomic merely because the API is one call.
- All **non-internal-RAM writes** require an explicit
  `authorize_write(context,address,width,value)` callback, including
  board output-off transactions and CPU configuration writes. Absence
  or denial returns `PCM_NO_HARDWARE` without touching device registers.
  A target must define safe reset/output authorization from verified
  wiring and observed register side effects; there is **no invented
  universal zero-is-off policy**.
- The optional `bind_fuel_ram_owners` bridge remains disabled at bind
  time. Opt-in tests prove shared-byte mask preservation, split-word
  aliases, and that failed bus stores do not publish C state. A
  **complete** RAM/ALDL owner map is still outstanding. The serial
  subsystem's own canonical receive-state reads/writes continue to use
  the existing serial-specific helpers.
- `pcm_hc11_native_mmio_init` implements volatile byte transactions
  and explicit ordered high/low word operations only under the
  **target-selected** `PCM_HC11_NATIVE_MMIO` build define. Host builds
  refuse raw native memory dereferences. Actual HC11 assembly is still
  required for SEI/CLI, RTI, stack entry, timer scheduling and output
  interlocks. Bus fault detection and register-specific latches are
  not established by these primitive C operations.

## Host tests

`hc11_bus_contracts` verifies the above provider with a compact
fake containing only 1 KiB RAM, 96 CPU-register bytes, two scoped
peripheral regions and 16 ROM bytes. It proves:

- ungranted $1800 extension, $0F00 EEPROM and $2000 program window
  requests fail without physical callback;
- CPU/board writes are refused without a policy, and denied writes
  leave device state unchanged;
- a 16-bit $3FCE injector-word request reaches the raw **word**
  callback once, in big-endian order;
- cross-window words, ROM writes, malformed grant tables and
  duplicate binding are rejected;
- selected canonical fuel RAM flags/words track successful writes,
  preserve unrelated bits and retain state after failed stores;
- host-native MMIO functions return `PCM_NO_HARDWARE` rather than
  dereference PC pointers.

Host CMake/CTest and `tests/run_checks.py` both run these contracts.

## Remaining gates before physical execution

1. Enumerate each live address access from ROM-backed producer/consumer
   maps and choose only hardware-confirmed grant ranges; *do not*
   turn chip-select coverage into blanket memory allocations.
2. Complete the source RAM/ALDL named-owner bridge, including
   byte/word overlap, bit lifetime and direct C-field mutation
   transitions. Demonstrate cross-path read/write equivalence over
   multi-event fuel, spark, idle, diagnostics and ALDL histories.
3. Replace the test authorization policy with a board-specific
   fail-safe output state machine and validate actual ASIC register
   reads, event latches, write sequencing, COP and IRQ interactions.
4. Cross-compile with a real HC11 toolchain and implement the native
   entry/vector/IRQ stack ABI; validate cycle and bus ordering in
   simulator and then on a non-running output bench.

**No target BIN exists from this backend commit; hardware contract
completeness is not claimed.**

## Canonical RAM bridge expansion (same development batch)

The existing opt-in named-owner adapter now additionally binds the complete
board output/input shadow bytes $004B–$004E and source-verified VSS data:
filtered $0284/$0285 (shared spark high + I/O fraction), previous VSS
$080F/$0810, age $0811, and raw VSS $0812/$0813. These owners follow
`pcm_board_ports`, `pcm_vss_calculate` and `pcm_vss_filter` in current C
source. The $080F..$0813 region is explicitly granted **only in the host
fixture**, not declared fitted RAM on the real board. Byte/word overlap and
backing-failure tests run through both the existing fuel-owner gate and the
new HC11 provider. This remains a partial bridge pending a full access ledger.

The provider stages every physical read into a local byte/word and publishes
it to the C caller **only after the raw callback returns `PCM_OK`**. A
host fixture deliberately dirties the output buffer before reporting failure;
the original caller's value stays unchanged. This prevents partial owner
publication on read failures as well as write failures.

## Cross-path ALDL verification

The host bridge also runs `pcm_serial_memory_read8/read16/write8` against
board shadow $004B and canonical VSS $0284/$0812. Those foreign addresses
flow through the same guarded address-space provider and owner fields.
Serial-owned descriptor $0362 stays on the serial subsystem's direct C
owner, so the bus receives **no physical transaction** for that address.
This is a scoped address-source test, not proof of actual ALDL frame timing,
serial SCI hardware, or all shared 7427 RAM aliases.

## Consolidated serial RAM ownership (same canonical bridge)

Previously `pcm_serial_memory_write8` independently edited `Pcm.serial`
while general `pcm_write8/16` knew only the fuel/board aliases.
The serial-owned byte switch is now centralized in **`ser_put`** beside
the existing `ser_get` owner: both direct ALDL access and the opt-in
logical RAM provider use the same implementation, without replicating
state or maintaining a 64 KiB shadow.

Covered owners include shared service byte `$003B`, session and
edge bytes `$0042/$0045`, serial framing/session state
`$0360–$036B`, receive buffer `$036C–$038D`, engine command
`$038E`, and transmission command `$0399`. Word reads/writes
preserve the big-endian descriptor `$0362`, service age `$0368`,
and expiry `$036A`. Other paired serial bytes use the same two
owner accessors; this is logical C state, not a claim of interrupt-atomic
native word instructions.

Host contracts now verify all three views: direct `Pcm.serial`
mutation, `pcm_serial_memory_*` reads/writes, and
`pcm_read/write8/16` with `bind_fuel_ram_owners=true`.
Failure of the backing bus never updates the owner after the failure.

**Remaining limitation:** `Pcm.serial` direct mutations and direct ALDL
writes are not automatic *physical* memory publications. The named bridge
continues to require explicit activation, platform backing, and a
target-side coherence strategy. A source-side shared owner is not proof
of a fitted RAM alias.

## Mixed-owner 16-bit transactions

A logical 16-bit access can cross independently named bytes
(e.g. $0041–$0042 = shared IAC/AC flags plus serial sessions,
$003A–$003B = diagnostic/interrupt flags plus serial command status,
$004B–$004C = shared board shadow plus output shadow).
Previously only explicitly indexed `uint16_t` fields were overlaid:
these cross-owner reads could return stale backing.

`pcm_read16` now performs **exactly one** original physical-width
read, checks a whole-word owner first, and otherwise resolves the
two byte owners independently using the physical high/low values as
residual bits. `pcm_write16` publishes **exactly one** physical word
first and then updates both byte owners only on success when there is
no whole-word owner. The host tests check width, read counts, serial
logical reads, shared-bit preservation and rejected stores.

The two C-field writes are logical state updates, **not** a claim that
an HC11 word write or interrupt interleaving is atomic. Cross-byte
interrupt synchronization and true physical memory backing remain
separate target validation.

## Verified-critical-section internal RAM publication

The opt-in `pcm_ram_sync_publish()` is a narrowly scoped bridge for
**direct C-field changes that must become physical internal RAM bytes**.
It accepts an explicitly ordered, non-overlapping list of named byte or
word addresses and a target-provided `verify_exclusive` callback.
The callback must establish that all competing state writers and IRQs
are excluded across the entire function. The module itself never issues
an unsafe unconditional CLI/SEI or invents restoration of the CCR.

Before ANY bus read or write, it validates the entire list: each address
is inside **$0000..$03FF**, backed by a named owner, and the requested
mask is a subset of that owner's verified bits. The owned mask is
calculated using the existing residual contract: compare owner overlay
results for raw backing $00 versus $FF; bits independent of backing
are owned, and all other bits are deliberately preserved. Whole-word
requests require an existing `pcm_fuel_ram_owner_read16` owner and
mask $FFFF. External GEN, conditional EEPROM, ROM and all board/ASIC
addresses are rejected—even where the host fixture grants that bus
window.

With the critical guard satisfied, it calls only the **raw**
`PcmPlatform.read8/write8/read16/write16` callbacks. This is
intentional: `pcm_read8/16` already overlay named C fields and would
hide stale physical storage. It stages current physical data, merges
source-owned bits without disturbing unowned flags, skips unchanged
values and publishes with one provider transaction per changed entry.
After failure, a report records which entry failed and how many earlier
writes succeeded; retrying from the beginning is idempotent. No
duplicate RAM mirror or heap buffer is created.

Tests cover $003A shared flags, $0041–$0042 overlapping IAC/serial
ownership, $00FD counter word, unknown-bit preservation, no-op
republication, denied guard, malformed masks, forbidden external
windows, partial physical failure and retry. This is an
**explicit checkpoint mechanism**, not automatic cache coherence:
a target must decide exactly when to call it and must verify physical
RAM backing, IRQ exclusion and native cycle budgets. It does not
publish injector, EST, IAC or other peripheral outputs.

The exclusive-writer guard is now checked **before ownership-mask
preflight**, not just before physical transactions, because owner discovery
reads live C state. A targeted failure fixture revokes the guard immediately
after a successful physical read and proves that no subsequent physical
write occurs. The guard remains a target-supplied contract; no host check
establishes real HC11 CCR or ISR exclusion.

## Automatic factory fuel RAM literal-writer audit

`check_fuel_ram_literal_writers.py` reads the maintained stock-ROM
`maps/structure/factory_fuel_memory_accesses.csv` and both C byte-owner
switches. It refuses inconsistent read/write owner address sets and
verifies every listed **literal low-RAM write**, including both bytes of
16-bit stores. Unrecognized indirect/indexed accesses, runtime pointers,
interrupt-frame effects and the complete $7427 ABI remain explicitly
outside this narrowly defined gate. Thus a green result is useful
source-index coverage, not complete physical or timing equivalence.
