# Resident interrupt, trap and reset leaves

The hash-checked stock BMHM image is the byte authority:
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
This group ports the resident FC04..FC44 leaf effects and connects the factory
REF branch to its real leaf. It does not install native target vectors or
execute target reset/RTI instructions inside host C frames.

| Entry | Stock vector/body | Resident effect and endpoint |
|---|---|---|
| `pcm_swi_irq` |FFF6→FC04|Set0000.3; halt before the FC07 self-loop.|
| `pcm_illegal_trap` |FFF8→FC1A|Set0000.4; halt before the FC1D self-loop.|
| `pcm_cop_reset` |FFFA→FC1F|Set0000.5; reach the FC2C transfer to7100.|
| `pcm_clock_failure` |FFFC→FC24|Set0000.6; halt before the FC27 self-loop.|
| `pcm_external_reset` |FFFE→FC29|Set0000.7; reach the FC2C transfer to7100.|
| `pcm_xirq_irq` |FFF4→FC09|Set0000.2, then OR40 into the supplied saved-CCR byte.|
| `pcm_factory_reference_irq` |74EE→FC11|Set0000.1, then write01 toTFLG1.|
| `pcm_timer_fallback_irq` |FFE6/FFEA/FFEC/FFEE/FFF0→FC2F|TMSK1=A0, then TFLG1=5F.|
| `pcm_overflow_fallback_irq` |FFDA/FFDC/FFDE→FC3A|TMSK2=03, then TFLG2=FF.|
| `pcm_spi_irq` |FFD8→FC44|Empty body before RTI; no status/data read or acknowledgment.|

All cause writes are literal byte RMWs that preserve the sampled unrelated
bits. Canonical `PcmSystem.interrupt_flags` owns0000 bitsFE; scheduler
`timer_seen` retains bit01. No duplicate owner or packed native-struct address
is assumed. A later retained-memory validation failure can clear0000..000A,
including these causes; accepted retained validation leaves them present.

Appended `PCM_HALT_BOUNDARY` status10 represents the three resident self-loops.
Appended `PCM_RESET_BOUNDARY` status11 represents the transfer to7100. Existing
status values remain stable. These differ from the older `PCM_TRAP_BOUNDARY`,
which identifies a caller stopped before its SWI instruction. Actual external
reset/RAM retention and COP timing remain target/device observations.

The XIRQ entry shim supplies the **logical saved-CCR byte address**. Cause
publication precedes the CCR read. The old PULA/PSHA pair becomes an ordered
byte read and an OR40 byte write at that address, with the same net saved-frame
effect. A callback that changes the frame before the read is observed; one
that changes it after the read does not replace the captured value used for the
write. The helper neither reads nor changes a native host C stack pointer.
Target RTI later restores the modified CCR, including X=1.

The complete `pcm_reference_irq` now follows its prefix's factory result into
`pcm_factory_reference_irq`. Factory mode records the cause and acknowledges
IC3, then completes for RTI; it does not enter normal fuel work. The separate
prefix API retains its old boundary and seven-transaction ordinary contract.

Fallback handlers preserve literal register identity and order. TFLG1/TFLG2
are supplied W1C device fixtures in the comparisons. FC2F does not acknowledge
a TFLG2 real-time flag, and the SPI leaf does not invent a status-clearing read.
These vector aliases do not imply the sources are enabled in stock firmware.

Focused verification passes **8,267 C/ROM comparisons**, covering **all22
resident starts** in FC04..FC43. Each cause byte is exercised; saved CCR tests
cover all256 values, two supplied frame positions, provider mutation and both
incoming I states. Shared timer/cause ownership, fallback masks, W1C effects,
factory REF joins, retained-validation joins and every provider failure of
direct leaf paths are covered. Actual vector words/aliases are checked against
the stock bytes. Seven RTI/self-loop instruction starts are explicit endpoints.

The updated complete REF regression also passes **2,502 handler cases,143 I/O
failure prefixes and38 direct timer-entry cases**, with all423 prior scoped
starts exercised. Its historical fixture still traces hardware operations;
the new cause-byte provider failures are covered by the dedicated leaf fixture.
Kernel/hardware smoke contracts pass.

Data comparisons retain byte/word width and failed-prefix state, including the
supplied XIRQ frame byte. Prior callee frame bytes03F0..03FF are excluded only
in the joined retained-validation fixture modes. Interrupt entry/arbitration,
target frame placement, RTI, reset/halt control transfer, physical flags and
the full repository regression remain separate; the latter stays deferred
until the requested "pull and merge" step.
