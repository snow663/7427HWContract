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
