# Factory masked intervals and competing interrupt costs

The ordinary resident code has no reviewed SEI-to-unmask interval longer than
709 nominal E cycles. Complete non-TOC3 handlers also have finite conditional
bounds. This narrows the source of the large entry delay required by the
[late current-output witness](FACTORY_FAST_TICK_TIMING_CONTRACT.md): a single
ordinary critical section or REF/normal SCI handler cannot supply that delay
by itself. Interrupt counts, bursts and priority still need an arrival model.

Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The ROM and simulator core are unchanged. Bounds use nominal HC11 timings,
valid frames and the documented peripheral premises; they are not board
measurements or whole-program worst-case execution times.

## All rooted SEI sites are accounted for

The [interval table](../../maps/structure/factory_masked_intervals.csv)
contains all29 rooted SEIs and the initial armed I=1 suffix at7467. Of the
29,27 belong to ordinary resident paths. F616 belongs to optional broadcast
pre-copy, andFB5E belongs to the factory output-cycle machine.

Each interval starts withSEI and ends afterCLI **and its complete following
instruction**, or afterRTI restores a valid ordinary entry frame with I=0.
A JSR immediately followingCLI is included as an instruction; its callee is
then interruptible. Direct resident calls inside the masked span execute in
the analysis with explicit return frames. An unknown call, loop or timing
form fails verification rather than receiving an estimated cost.

Selected bounds are:

| Start / role | Nominal upper E cycles | Included endpoint |
|---|---:|---|
|7483 RAM refresh block|97|74AB branch afterCLI|
|7A51 scheduler tail|85|7A81 jump or7A84RTI|
|7AB7 three-conversion wrapper|709|7ABC RTS afterCLI|
|7B70 fast ADC section|419|7B9B JSR afterCLI|
|84A9 asynchronous output wrapper|227|84AE BSET afterCLI|
|F3EE output flush|81|F41F RTS afterCLI|
|F781 serial request setup|107|F7BB branch afterCLI|
|FB5E factory output-cycle iteration|46|FB70 comparison afterCLI|
|7467 initial armed I=1 suffix|136|74AB or74B4 branch afterCLI|

The709-cycle maximum includes three fullF25F invocations throughF20D. Each
loadsB=12 atF265, then polls/decrements until ready or timeout. A complete ROM
execution with readiness held low takes709 cycles, performs36 polls and
three timeout routes, restores SP and returns with I clear. Thus this
particular upper bound has an execution witness. It does not depend on those
three conversions completing normally.

The different7B79 ADC wait has no software timeout. Its419-cycle containing
interval assumes the previously documented powered/stabilized E-clock ADC
completion deadline of129 E cycles, with20 poll attempts conservatively
allowed. Holding that ADC wait not-ready invalidates the finite bound.

F616 has a separate9781-cycle byte-loop envelope: its fixed pre-copy body
costs38 cycles per iteration, conservatively allowing256 iterations. Stock
518F..51AF contains33 zero bytes covering all32 overlapping schedule-word
reads. Ordinary stock polling therefore never selects this broadcast copy.
Its larger generic cost must not be substituted for a reachable stock
critical section; activating it in another calibration changes that scope.

Boot before the first arm, STOP/trap paths, arbitrary supplied code and
invalid stack/active-frame aliases are separate boundaries. In particular,
TAP50 at7D8C leads toSTOP and a self-loop, not an ordinary finite critical
section. WAI at74D0 is an interrupt-enabled wait; its already-stacked wake
sequence differs from an ordinary instruction-to-IRQ entry.

## Complete competing handlers have conditional costs

All14 ordinary vector words other thanTOC3 select eight distinct resident
entries. Their full closures retain I=1 untilRTI, as established by the
[admission contract](FACTORY_INTERRUPT_ADMISSION_AND_CURRENT_OUTPUT.md).
The [handler table](../../maps/structure/factory_leaf_irq_cycle_bounds.csv)
includes all eight and three SCI length contracts.

| Entry / source | Handler upper E cycles, includingRTI | With nominal12-cycle ordinary entry |
|---|---:|---:|
|74EA REF / external IRQ|1221|1233|
|7875 OC5|132|144|
|78D9 OC4|132|144|
|CE7C OC1|109|121|
|F7EA SCI, normal session copy<=11|481|493|
|F7EA SCI, validated received length<=34|964|976|
|F7EA SCI, broader byte-copy envelope<=255|5605|5617|
|FC2F fallback, five vector words|24|36|
|FC3A fallback, three vector words|24|36|
|FC44 SPI empty handler|12|24|

These are structural upper bounds: some longest branch combinations cannot
occur together. Complete selected REF executions stay below1221; the tests
do not claim to reach that maximum. The REF graph's backwards branches do
not imply an unbounded loop. The0051.7 latch has only three set-only writers
inside this closure,7725/7742/775B, and the three output helpers cannot clear
it. The verifier tracks that latch through calls. The774F mode test is also
specialized to stock400B=04 with bit20 clear; the helpers preserve its Y
cursor. Other decisions are conservatively retained, including some stock
mode-inactive paths.

SCI ID lookup traverses actual ROM lists51BF→53A8→53C9→0 or
FBD7→FBE0→FBE9→0, limiting one lookup to three candidates. Accepted length
is validated atF958..F960 against22 hex=34. The normal-session route with
0050.3 clear reaches theFA0A..FA0E clamp to0B=11; the factory route can skip
that clamp. The copy bodyFA16..FA1F costs21 cycles per byte and has no call or
mask change. The zero-length route skips it.

The34/11 rows require the protocol length and session predicates to remain
valid; arbitrary aliases into receive state are outside those contracts.
The255 row is a wider local byte-count overapproximation, not permission to
assume arbitrary descriptors or supplied code have bounded effects.

Complete exchanges execute every RX/TX interrupt and resident callee. An
eleven-byte normal service payload reaches487 cycles including entry in its
longest invocation, below493. A34-byte factory payload reaches932, below976,
copies the entire payload to038E..03AF and returns intact. Both replies have
valid checksums. These observed paths validate length-sensitive execution;
they are kept distinct from conservative maxima.

## Joining costs requires an event-arrival contract

CCA1/CCA3 loads15 and requests its write toHPRIO303C using X=3000. In the
F1-style priority table, PSEL5 is reserved and defaults toIRQ: REF retains
the highest ordinary priority, TOC3 is eighth, and SCI is fifteenth. Priority
selects among pending enabled sources at arbitration. AfterTOC3 clears I,
even a source belowTOC3 can interrupt it. Lower priority therefore does not
make SCI free of interference during the timer body.

For a recurring compare and the accepted ordinary **busy** TOC3 path, let M
bound residual resident masking/instruction work before interrupt admission,
and W cover additional synchronization, bus waits or other delay not already
counted. Let each N count admitted competing handler invocations from that
compare through the busy handler's return. Count a handler already in
progress as a complete invocation, conservatively. A sufficient component
budget, using the normal SCI contract, is:

```text
M + 12 + 1090
  + 1233*N_REF + 493*N_SCI
  + 144*(N_OC4 + N_OC5) + 121*N_OC1
  + 36*N_fallback + 24*N_SPI + W < 13104
```

M=709 covers the reviewed ordinary SEI spans, the136-cycle initial suffix
and the residual of ordinary finite CPU instructions under the stated scope.
Use976 or5617 for SCI when only the corresponding broader contract applies.
The12-cycle term allows ordinary TOC3 entry; a valid WAI wake has already
performed stacking and can be accounted separately. W must retain any delay
needed beyond these nominal components. Source flags, enables, priority and
coalescing determine which counts are actually possible.

This is a sufficient conditional exclusion test, not a measured workload or
an arrival proof. It excludes a next compare before return only if its counts
bound **all** relevant interference, and no excluded path, prior unaccounted
timer overrun or frame/alias effect invalidates the components. Exceeding
the budget does not prove a nested compare. Complete non-busy main/catch-up
execution and global active TOC3 depth remain outside this bound.

The immediate next ROM target is the enable/acknowledgment/rearm lifecycle of
REF, SCI and the other timer sources, joined with their minimum interarrival
constraints and priority. That will distinguish a feasible burst from an
arbitrary IRQ schedule. Proprietary input arrival and board wait behavior
retain their external evidence boundaries.

## Reproduce and timing authority

```sh
python tools/verify_factory_masked_timing.py --rom /path/to/BMHM.BIN
python tools/verify_factory_masked_timing.py --check-recorded
python -m unittest discover -s tests -p 'test_factory_masked_timing.py' -v
```

The [verifier](../../tools/verify_factory_masked_timing.py) checks the full
stock hash, reviewed loop/guard bytes, lookup chains and REF latch writers.
The [instruction table](../../maps/structure/factory_masked_instruction_cycles.csv)
records1253 included PCs with their bytes and independent nominal costs;
the [JSON evidence](../../maps/structure/factory_masked_timing_evidence.json)
retains premises and exclusions. The simulator's cycle counter supplies no
timing authority.

Costs follow [M68HC11ERG](https://www.nxp.com/docs/en/reference-manual/M68HC11ERG.pdf),
Table1 pp13..20, and [M68HC11RM](https://www.nxp.com/docs/en/reference-manual/M68HC11RM.pdf),
AppendixA. IRQ stacking and CLI/RTI recognition followRM sections5.5/5.7.2;
the following instruction is protected afterCLI, whereas a restored I=0 at
RTI can admit an IRQ immediately. Priority follows
[MC68HC11F1](https://www.nxp.com/docs/en/data-sheet/MC68HC11F1.pdf),
section5.3/table5-3. These are conditional CPU semantics, not identification
of the installed board or proprietary ASIC behavior.
