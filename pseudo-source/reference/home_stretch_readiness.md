# $31 pseudo-source home-stretch handoff — 2026-11-23

This is a consolidation of the current `work/pseudo-source-development`
**host C** implementation. It is not a release of a target HC11 binary,
a calibration revision, or authorization to drive real outputs.

## Canonical execution policy

- **Fuel default:** `pcm_fuel_control()` runs resident
  `pcm_fuel_ignition -> pcm_fuel_inputs -> pcm_fuel_calculate -> pcm_fuel_schedule`,
  as in the validated PR48 source. The independently compared
  `pcm_fuel_cycle()` is a **research alternate only** and requires
  `enable_resident_fuel_cycle` **and** `bind_fuel_ram_owners`. Do not
  schedule the two paths consecutively or treat the sparse bridge as the
  target RAM/ALDL provider.
- **Slot01 default:** `pcm_baro_input -> pcm_transmission_baro ->
  pcm_tcc_nonelectronic`. The alternate `pcm_speed_source ->
  pcm_tcc_non_electronic` requires `enable_resident_slow_slots`.
- **Slow slots:** all 16 are now resident C entries, including slots
  03/0B using the *same* D4EB gear selector, 04 diagnostics, 05 catalyst/TCC,
  0A purge, 0C register refresh, 0D AIR/MAT/diagnostic output.
- **Explicit failures:** missing admitted external calls must remain
  `PCM_UNIMPLEMENTED`/typed boundaries, not successful no-ops. This C
  policy does not replace the HC11 frame, CCR, return or trap semantics.

The current [machine-readable ledger](home_stretch_manifest.json)
records **413 indexed routines** (235 outlines, 169 algorithms,
9 explicit boundaries), all eight external-hook addresses and open
target gates. The new [source consistency gate](../tests/check_home_stretch.py)
fails if that inventory or default-path contract silently drifts.
Routine count is an *index metric*, not percent ROM equivalence.

## Remaining work — engine first

| Gate | Requirement / acceptance evidence |
| --- | --- |
| HC11 entry/interrupt ABI | Real reset setup, stack/CCR, vectors, RTI, WAI, STOP/SWI, timer-stack recovery and interrupt-safe 16-bit handoffs |
| RAM and ALDL ownership | One logical owner for shared bytes/words, read/write alias coherence, remaining sparse bridge coverage, fail-prefix preservation |
| Board/ASIC interface | Decode and chip selects, 8/16-bit bus order, register latch semantics, COP, REF/OC1/OC3, injector/EST/IAC output sequence and timing |
| Native image | Toolchain, linker script, actual code/RAM/calibration/vector placement, cycle/stack budgets, reproducible image and checksum |
| Optional calls | Explicit supported-feature decision or ABI-backed implementation for `$1800/$1803/$1806/$1809/$180C/$180F/$1812/$1815`; conditional hooks inside resident routines also count |
| Five current/transmission groups | `pcm_current_control`, `pcm_pressure_tcc`, `pcm_shift_control`, `pcm_transmission_spark`, `pcm_transmission_input_prefix`: leave transparent, lowest source priority for the manual-only controller |
| Integration release | Full *current-tree* C/ROM, factory/static, simulator/hygiene gate and joined interrupt-history checks, followed by generated-image simulation and controlled bench validation |

The other four of the nine indexed boundaries are
`pcm_reset_entry`, `pcm_spark_extension`,
`pcm_spark_output_extension` and `pcm_connection_probe`.
Nine boundaries do not mean nine remaining physical target functions.

## Practical route to the first executable image

1. Hold the default resident fuel/spark/IAC paths fixed; keep alternate
   algorithms testable but not dual-dispatched. Preserve the validated
   stock-ROM numeric and transaction fixtures.
2. Implement the physical register and logical RAM provider with explicit
   safe-output policy. Exercise live-port read/write ordering, peripheral
   side effects, alias masks, interrupt protection and fault prefixes.
3. Add minimal HC11 startup, vectors, exception/interrupt shims, stack
   budget and linker assertions. Build a ROM image with no active output
   permission until board initialization and heartbeat are verified.
4. Validate the generated image in the simulator, then observe injector,
   EST and IAC pins independently on a bench, including reset, cranking,
   no-reference and watchdog paths.
5. Choose a manual-only feature policy from a traced producer/consumer
   graph. Disable unwanted transmission/emissions code only while
   preserving shared inputs, off-writes and diagnostics. Physical truck
   testing remains a separate sign-off.

## Evidence and validation boundary

The [November 22 completeness audit](completeness_audit_2026-11-22.md)
describes the earlier 374-routine tree; the [gear-slot](transmission_d4eb_source_closure.md),
[slot04](slot_04_contract.md), [05/0A](slots_05_0a_contract.md) and
[0C/0D](slots_0c_0d_contract.md) contracts document subsequent closure.
The [fuel RAM-owner audit](fuel_ram_owner_audit.md),
[reconciliation](reconciliation_2026-11-22.md) and
[memory layout](../memory/MEMORY_LAYOUT.md) constrain target decisions.

PR48's full validation is historical evidence for `main`. Current
development branch runs focused comparisons and quick gates, but its
**complete combined-tree release regression is not yet verified**.
The source-only consolidation changes no firmware calibration, BIN, XDF
or ADX, and provides no target execution claim.

## Native HC11 vector boundary — first integration slice

`include/hc11_vector_map.def` records the **21 stock BMHM interrupt
vector identities** with factory resident PCs and the C-side handler
policy. `check_hc11_native_vectors.py` checks that data against the
stock-ROM vector evidence CSV and the **two already-existing ASM11 ROM
vector tables**. Both physical ROM tables still route non-reset
vectors to the engine-off trap; no incomplete interrupt is enabled.

`platform/hc11_vector_contract.c` provides a C-side dispatch contract
for already resident SCI, SPI, REF, OC1, TOC3, XIRQ and fallback bodies,
but only after a real native frame has been independently verified.
It refuses TOC3 without its additional stack admission contract, XIRQ
without a verified saved-CCR address, and both unresolved OC4/OC5
output-timer interrupt bodies. It reports distinct RTI, native stack
recovery, reset, halt and nonreturn boundaries; it **never executes RTI**.

This closes source/ABI-interface inventory, not native ABI execution.
No assumed compiler calling convention, completed HC11 interrupt
prologue, native C/assembly linkage, flashable BIN, or real output
authorization is claimed. The existing ASM11 bootstrap remains the
source of the actual engine-off executable reset prelude.

## Native ISR assembly envelope and C mailbox — development slice

The maintainable ASM11 ROM now **includes** `hal/native_isr_gate.asm`
and reserves eight adjacent, assembler-allocated HAL RAM bytes for the
IRQ mailbox. Its entry candidates capture the exact vector identity and
use `TSX` **before any subroutine call** to sample the hardware-saved
CCR address (SP+1). It checks a conservative $03B0..$03F7 range,
rejects a busy mailbox, and enters the existing engine-off fatal path
unless the callback returns with both a **$A5 RTI token** and zero status.
Only then does the native envelope issue `RTI` to restore the CPU's
saved frame.

The compiler-specific native C-call ABI is still an **explicit open
boundary**: `HAL_ISR_C_ENTRY_WORD` points by default to
`HAL_ISR_C_UNBOUND`, a reject-only RTS routine. Binding compiled C
requires an actual compiler-specific no-argument RTS thunk and verified
symbol/S19 linkage. The caller/callee share an eight-byte protocol rather
than assuming native C struct layout or parameter passing.

The host-tested `pcm_hc11_mailbox_dispatch` validates candidate
vector, frame evidence, admission, identity preservation, and body
status before emitting the $A5 success token. It explicitly refuses
TOC3 (which can unmask/nest and cannot share the one-entry mailbox),
XIRQ, reset/trap entries, and unimplemented OC4/OC5 output interrupts.

The source gate checks exact RAM byte offsets, critical instruction
order, non-reentrant guard, default reject thunk, **13 candidate
maskable vector entry labels**, and all 32 original safe vector words.
Every actual ROM vector except reset **still points to the original
engine-off safe trap**. This code does not create an engine-running BIN,
does not change fuel/spark logic, and does not assert native C calling
convention, interrupt nesting, stack budget or live board output proof.

### Zero-argument native C entry symbol

`platform/hc11_c_entry.c` now provides a concrete C entry symbol
`pcm_hc11_c_entry(void)`. The ASM11 `JSR 0,X` can call it without
passing an HC11-dependent C argument list, once its actual executable
address is linked into `HAL_ISR_C_ENTRY_WORD`. It forwards through
`pcm_hc11_mailbox_dispatch` using context installed through
`pcm_hc11_c_entry_bind` during an explicitly interrupt-masked native
boot, and supports `pcm_hc11_c_entry_reset` so the ROM does not
assume a C runtime has zeroed static data. Rebinding without reset,
null pointers and unmasked bind attempts are refused. The native
entry is an ordinary C function; it must **not** be declared
`interrupt` or emit `RTI`. The ASM wrapper alone owns native RTI.

Host tests prove this handoff behavior, but the real 68HC11 compiler's
symbol decoration, subroutine return convention, stack usage,
link address and RAM placement still require assembly listing/S19
verification. This commit does not rebind the ROM call word; its
default still rejects every unqualified interrupt.

## C pseudo-source HC11 execution lifecycle — testable target boundary

The new `platform/hc11_execution.c` attaches the existing **resident C**
pseudo-source to a qualified post-reset machine state. A boot witness
records that the *real* or *simulated HC11* completed INIT03,
LDS=$03FF, masked admission, C-state initialization, and safe output
permissions. These are externally established facts, **not** invented
by C. The host tests reject incomplete or false witness values.

`pcm_hc11_exec_background` executes the existing $746C background
routine and converts `PCM_BACKGROUND_WAIT_BOUNDARY` into a
**WAITING** state, explicitly requesting native WAI rather than
fabricating a successful C return. A subsequently admitted vector runs
through the existing `pcm_hc11_vector_dispatch` and returns a separate
native action: only `PCM_OK + NATIVE_RTI_REQUIRED` resumes the
dispatcher. Stack-recovery, native reset, and unimplemented output IRQs
cannot silently enter ordinary C continuation.

The existing native ASM11 gateway also checks **stack-pointer
balance after returning from the C subroutine**: TSX must equal
the saved CCR frame address before either status or RTI token is
considered. This prevents a corrupted C stack from authorizing RTI.

This is the pseudo-source execution oracle that a future simulator can
call for *state-level* differential tests. It does not magically turn
host C into HC11 instructions or eliminate the need for a real 68HC11
cross-compiler, linker/ROM layout, native C startup/ISR calling ABI,
actual WAI/RTI execution, or complete RAM-owner placement. The old
simulator and the fresh simulator remain separate from this code.
