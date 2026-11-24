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
