# Independent BMHM output-timer handler specification

Independent derivation from the frozen audit checkout, 2026-11-24, followed by
focused implementation and actual-ROM comparison on a separate work branch.
This specifies factory resident behavior, not TS00 or custom firmware, and
makes no cycle-accurate or native C ABI claim.

## Evidence and scope

`maps/structure/bmhm_global_structure_rom_evidence.json` contains the recorded
factory bytes. Filling the unrecorded lower `$0000..$3FFF` region with `$FF`, as
the existing evidence contract requires, produces the expected full image
SHA-256 `6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The vector bytes at `$FFE0..$FFE3` are `78 75 78 D9`.

Every instruction's bytes in the following two spans were independently
matched to `maps/structure/factory_global_instructions.csv`; each span contains
40 instruction starts and exactly 100 contiguous bytes:

| Vector | Entry / last instruction | Span SHA-256 |
|---|---|---|
| `$FFE0` | `$7875..$78D8` | `71eb097c1c658d5fd1a905028cf33decf1198c0ad9098a060b93b03b359bdad7` |
| `$FFE2` | `$78D9..$793C` | `7820e2eee3cfee52e547cdc82284f5e5a82de178c8a7f52d5bd9b054eac5ba0e` |

The listing `source/31/BMHM_HAC_ORG_7100_to_end.asm:1494..1625` agrees on
instructions. Several comments are wrong: `$78E4/$78E7` say SET despite BCLR
opcodes; `$78E0` says TOC3 despite the OC4 mask/register mapping. Interpret the
instruction bytes, not these comments.

These are complete leaf ISR bodies: no JSR, BSR, tail call, extension call,
calibration read, SEI, CLI, or explicit stack access. The closing instructions
are real RTI. Normal interrupt entry has already set I; the body does not
reopen ordinary interrupt admission. Native entry saves nine bytes and RTI
restores the interrupted PC, Y, X, A, B, CCR and SP. An independently supplied
native C wrapper is still required to implement that ABI.

Existing stock reachability evidence (`FACTORY_INTERRUPT_AND_TIMING_CLOSURE.md`
and `factory_irq_source_lifecycle.csv`) says stock `400B=04,400C=B7` keeps
OC4/5 locally disabled: their only individual enables at `$77DF/$780F` are
inside excluded REF mode paths. Implementing these bodies closes an explicit
factory/calibration-mode gap. It does not establish that ordinary stock BMHM
reaches either vector without changed input/enable premises. No custom BIN or
workbook role follows from this work.

## Bank mapping

| Item | A / OC5 | B / OC4 |
|---|---|---|
| Entry | `$7875` | `$78D9` |
| Vector | `$FFE0` | `$FFE2` |
| PORTA test / TMSK1 / TFLG1 mask | `$08` | `$10` |
| TCTL1 bit modified | `$01` | `$04` |
| Hardware compare word | `$301E` | `$301C` |
| Previously armed compare RAM | `$0821` | `$0823` |
| Newly computed extension RAM | `$0825` | `$0827` |

Common registers: PORTA `$3000`, TCNT `$300E`, TCTL1 `$3020`, TMSK1
`$3022`, TFLG1 `$3023`. Common retained RAM: flag `$0046.0`, pulse word
`$0250`, and reservoir word `$023A`. All words are big-endian in the factory
address space. Other register/RAM bits and the opposite bank's words are
retained.

## Exact control flow

The two instruction streams are bank substitutions of this table. A branch
target is shown in A/B order. `EXT`, `ARM`, `TOC`, `MASK`, and `ACTION` refer
to the bank table above.

| A PC | B PC | Operation / meaning |
|---|---|---|
|7875|78D9|LDX #3000|
|7878|78DC|LDAA #MASK|
|787A|78DE|STAA TFLG1: first observable device transaction is acknowledgment|
|787C|78E0|BRCLR PORTA,MASK to 78C5/7929|
|7880|78E4|BCLR TMSK1,MASK: read current byte, clear only this mask bit, write|
|7883|78E7|BCLR TCTL1,ACTION: read current byte, clear only this action bit, write|
|7886|78EA|BRCLR RAM0046,01 to 78A7/790B|
|788A|78EE|LDD RAM0250|
|788D|78F1|ADDD RAM023A|
|7890|78F4|BCS 7895/78F9: unsigned addition carry saturates before doubling|
|7892|78F6|ASLD|
|7893|78F7|BCC 7898/78FC: shift carry selects saturation|
|7895|78F9|LDD #FFFF|
|7898|78FC|ADDD TOC; this addition wraps, it does not saturate|
|789A|78FE|STD EXT|
|789D|7901|CLRA|
|789E|7902|CLRB|
|789F|7903|STD RAM023A = 0|
|78A2|7906|BCLR RAM0046,01; a fresh byte RMW preserving other bits|
|78A5|7909|BRA 78B5/7919|
|78A7|790B|LDD RAM0250; reservoir is not read on this branch|
|78AA|790E|ASLD|
|78AB|790F|BCC 78B0/7914|
|78AD|7911|LDD #FFFF|
|78B0|7914|ADDD TOC, wrapping|
|78B2|7916|STD EXT|
|78B5|7919|LDD TCNT|
|78B7|791B|ADDD #0002, wrapping|
|78BA|791E|CPD EXT; D is unchanged, N is bit15 of wrapped D-EXT|
|78BE|7922|BPL 78D6/793A; choose D=TCNT+2 when N is clear|
|78C0|7924|LDD EXT; this is another RAM read when N was set|
|78C3|7927|BRA 78D6/793A|
|78C5|7929|BSET TCTL1,ACTION; current-byte RMW, other bits preserved|
|78C8|792C|LDD TCNT|
|78CA|792E|ADDD #0002, wrapping|
|78CD|7931|CPD ARM; D unchanged|
|78D1|7935|BPL 78D6/793A|
|78D3|7937|LDD ARM; another RAM read when N was set|
|78D6|793A|STD TOC; exactly one final hardware word write|
|78D8|793C|RTI|

There are seven conditional branch sites per bank: PORTA BRCLR, shared-flag
BRCLR, addition BCS, combined shift BCC, base-only shift BCC, extended BPL,
armed BPL. Each needs both edges covered. The two unconditional BRA sites
also need execution coverage. Full body coverage is exactly 80 distinct PCs.

## Executable arithmetic meaning

For stable ordinary RAM during the masked body, this mathematical equivalent
captures the three paths. It deliberately preserves the difference between
saturating pulse arithmetic and wrapping timer arithmetic:

```c
write8(TFLG1, MASK);
if (read8(PORTA) & MASK) {
    update8(TMSK1, clear=MASK, set=0);
    update8(TCTL1, clear=ACTION, set=0);
    if (RAM0046 & 1) {
        uint32_t sum = (uint32_t)RAM0250 + RAM023A;
        uint16_t width = sum >= 0x8000UL ? 0xFFFFu
                                                : (uint16_t)(sum * 2UL);
        EXT = (uint16_t)(width + read16(TOC));
        RAM023A = 0;
        RAM0046 &= (uint8_t)~1u;
    } else {
        uint16_t pulse = RAM0250;
        uint16_t width = pulse & 0x8000u ? 0xFFFFu
                                               : (uint16_t)(pulse * 2u);
        EXT = (uint16_t)(width + read16(TOC));
    }
    uint16_t near = (uint16_t)(read16(TCNT) + 2u);
    write16(TOC, ((uint16_t)(near - EXT) & 0x8000u) ? EXT : near);
} else {
    update8(TCTL1, clear=0, set=ACTION);
    uint16_t near = (uint16_t)(read16(TCNT) + 2u);
    write16(TOC, ((uint16_t)(near - ARM) & 0x8000u) ? ARM : near);
}
```

This is explanatory pseudocode, not a production API proposal. In particular,
the conditional EXT/ARM reload after CPD is explicit in the instruction table;
arbitrary host callbacks that mutate RAM between reads are not automatically
justified native hardware interleavings. Addition must widen an operand
*before* addition. `uint32_t sum = pulse + reservoir` can already wrap with
16-bit unsigned promotions. The sum's maximum is 131070, well within uint32_t.

The comparison is **N only**, not N xor V and not unsigned maximum. For
example, `near=8000/deadline=7FFF` chooses `8000`; `near=0000/deadline=FFFF` chooses
`0000`; `near=0000/deadline=8000` chooses `8000`. Equality chooses near; the exact
half-range distance (`difference=8000`) chooses the deadline.

Local branch flags are C from ADDD/ASLD and N from CPD. CPD does not replace D
with its subtraction result. The body does not depend on incoming arithmetic
flags; it preserves I/S/X/H internally and RTI restores the complete saved
CCR. The handler never publishes a changed arithmetic CCR to interrupted code.

## Ordered effects and retained state

All paths acknowledge before reading PORTA and before other accesses. There
is no read of TFLG1; using its own value as the acknowledgment would incorrectly
clear other W1C flags. There is exactly one TCNT word read per invocation.

Sampled PORTA bit set: acknowledgment, PORTA read, TMSK1 RMW, TCTL1 RMW,
shared-flag test, pulse/reservoir arithmetic, TOC word read, EXT publication,
optional reservoir clear then flag clear, TCNT read, EXT comparison/read,
final TOC word write. The computed EXT remains stored even when the final
TOC write instead selects near. Disabling the interrupt mask does not skip
the final compare programming.

Sampled PORTA bit clear: acknowledgment, PORTA read, TCTL1 RMW, TCNT read,
ARM comparison/read, final TOC write. TMSK1, EXT, pulse, reservoir and shared
flag are untouched. There is no old-TOC word read on this path.

If the shared flag is clear on the set-bit path, the reservoir is not read or
cleared. If the flag is set, it is consumed even when the reservoir is zero,
the combined sum saturates, or the final near value wins. This is one shared
reservation, not one per bank: in A-then-B and B-then-A sequences, the first
set-bit invocation consumes it and the second sees base pulse only. A clear-bit
invocation before either does not consume it. The opposite bank's compare and
extended state remains unchanged by each invocation.

The native instruction body has no device-error return. A host API's provider
failure is a test/model boundary: earlier accepted device writes and preceding
RAM updates must remain, with no later operation or RTI authorization. Important
prefixes: failed TOC read leaves EXT/reservoir/flag unchanged; failed TCNT read
occurs after EXT and shared consumption; failed final TOC write leaves those
RAM changes committed. The existing `pcm_read16`/`pcm_write16` contract is one
logical word transaction; native bus high/low effects require separate later
validation, not an invented atomic hardware guarantee.

## Existing C integration surface

Canonical owners are already in `pseudo-source/include/pcm.h`:

| Factory state | Existing C owner |
|---|---|
|0250|`reference.timer_pulse`|
|023A|`fuel.acceleration_reservoir`|
|0046.0|`fuel.async_suppressed`|
|0821 / 0823|`reference.compare_a / compare_b`|
|0825 / 0827|`reference.extended_a / extended_b`|

`async_suppressed` is the existing owner name; do not introduce a duplicate
pending flag or use `reference.extra_request` (0073.6). The producer at
`$84B6` sets this bit when the packet is retained for synchronous enrichment;
`$84B1` clears it after the asynchronous packet route. The currently selected
bank consumes that same retained reservoir.

Reuse the hardware enum, `pcm_read8`, `pcm_write8`, `pcm_read16`,
`pcm_write16`, and `pcm_update8`. The latter implements literal ordered byte
RMW. `reference_timer_arm.c` already owns producers `$77C7/$77F7`, and
`reference_crank_timer.c` already expresses the same N-only timer selection.
They are dependencies in the state lifecycle, not factory callees of these
new bodies. Do not call the complete crank handler from these IRQs.

`fuel_ram_owner_read/write16` maps pulse/reservoir/timer_delay but currently
omits `$0821..$0828`; `reference_event_test.c` has separate fixture mappings for
them. The ordinary C fields should be shared with their REF producers;
raw-address providers/ALDL need explicit owner mappings if exposed. Do not
silently read a stale backing bytearray for these fields.

`hc11_vector_contract.c` returned PCM_UNIMPLEMENTED for both vectors in the
audited baseline after verifying the supplied native-frame premises. The
focused implementation binds `pcm_toc5_irq` and `pcm_toc4_irq`, sharing the
internal mirrored body in `output_timer_internal.h`. It keeps the existing gate: no safe RTI until PCM_OK;
no native frame means PCM_STACK_BOUNDARY before any side effect. Portable C
must not manufacture SP/CCR or silently add SEI/CLI. `hc11_native_mmio.c`
explicitly leaves native entry/masking/RTI assembly unsupplied.

## Validation matrix and remaining integration work

The committed leaf differential cases execute actual factory bytes through
normal interrupt entry and RTI, with independent C and ROM memory/state. They
compare all seven relevant named-state values, peripheral state, and ordered
logical I/O; the ROM side additionally checks exact RAM-access order, unchanged
unowned RAM and unrelated flag bits, and interrupted registers/CCR/SP
restoration. Separate C contracts use whole-Pcm canaries to detect unrelated
owner changes. A fixture-supplied
PORTA and TCNT sequence is a declared input, not a real timer model.

1. Both banks, every one of the seven conditional sites with both edges, all
   40 PCs per bank. Fail if expected PCs or edges are missing; report them.
2. Three structural routes per bank: PORTA clear; PORTA set/shared flag clear;
   PORTA set/shared flag set. Use nonzero sentinel state for untouched words,
   unrelated RAM0046 bits and unrelated TMSK1/TCTL1/TFLG1 bits.
3. Base-only pulse values `0,1,7FFF,8000,FFFF`. Combined examples `0+0,1+1,7FFF+0,
   7FFF+1,8000+0,FFFF+0,FFFF+1,FFFF+FFFF`. Distinguish addition carry from
   doubling carry; a wrapped sum of zero must still saturate on addition carry.
4. TOC offset wrapping: old TOC `FFFF` plus width `2` gives EXT `0001`; old TOC `1`
   plus width `FFFF` gives EXT `0000`. Check EXT even when near is selected for the final TOC write.
5. TCNT `FFFE/FFFF` gives near values `0000/0001`. Compare equality and
   differences `0001,7FFF,8000,FFFF`. Include near/deadline pairs
   `8000/7FFF,0000/FFFF,0000/8000,FFFF/0000` to defeat signed-relational and unsigned-max substitutes.
6. Literal minimal witness, either bank: PORTA bit set, base=1, reservoir=2,
   flag `$0046.0=1`, old TOC `1000`, TCNT `1000` gives EXT `1006`, final TOC
   `1006`, reservoir `0`, flag cleared, own TMSK1 bit cleared, own TCTL1 bit cleared.
   PORTA clear with ARM `1006` selects `1006` but preserves EXT/reservoir/flag/TMSK1.
7. Ordered acknowledgment and W1C residuals: initialize TFLG1=FF and confirm
   only bits `08/10` cleared. Assert byte RMW masks preserve unrelated action bits,
   no PORTA write, no unexpected TMSK1 access on the clear-bit path, one TCNT
   read, one final TOC write, and conditional old-TOC read only on set-bit path.
8. Sequential A->B, B->A, clear-bit->set-bit, set-bit->set-bit, and repeated
   same-bank invocation using retained state. Combine pulse `1` and reservoir `2` and
   distinct compare sentinels: first consumer width `6`, later consumer width `2`.
   Preserve other-bank state until its own invocation. Do not reseed all RAM
   between steps. External PORTA phase updates must be explicitly supplied.
9. Same-Pcm C arm/crank producer->output-handler contracts pass without raw
   RAM serialization, including explicit PORTA phase changes. The existing REF
   ROM suite separately exercises its producers. A combined actual-ROM
   producer/IRQ/device-scheduler sequence and complete packet-select/shared-
   reservoir lifecycle remain integration work; leaf coverage does not prove
   them.
10. Each logical provider failure position, checking accepted event prefix,
    retained RAM and no safe native return. These are host API boundary tests,
    not evidence that factory hardware has fallible reads.
11. Actual IRQ admission/RTI with varied nonzero registers and admissible CCR
    bits; handler body leaves I set, IRQ does not nest through these bodies,
    all nine saved bytes are restored. C native-action contract tests are
    separate from any future genuine compiled HC11 ABI execution test.
12. Deterministic randomized RAM/input scenarios after literal witnesses;
    seeded sequence output and per-PC/per-edge coverage are retained for
    reproducibility. Avoid claiming branch coverage proves arithmetic domain
    completeness or physical pulse timing.

Physical uncertainties remain device behavior and integration, not missing
instructions in these two spans: actual PORTA pin/readback semantics, OC5 vs
IC4 mode, timer compare generation/latching, W1C racing with a fresh event,
high/low compare-register bus effects, and native instruction timing. A basic
logical I/O comparator can verify literal firmware transactions now, while
these remain named premises until an independent device model or hardware
evidence establishes them.

## Recorded result and reproduction

The new `pseudo-source/tests/compare_output_timer_rom.py` passes **3,068 cases**
with **6,626 actual factory interrupt entries**, **6,569 full architectural RTI
restorations**, and **57 intentionally failed provider prefixes**. It retires
all **80 instruction starts**, both outgoing edges at all **14 conditional
branch sites (28 edges)**, and all **four unconditional branch edges**. A
failed instruction is not counted as completed coverage. Budget exhaustion,
missing coverage, illegal execution, malformed C output, and any first
divergence fail the test. The standalone C driver also passes `--contracts`.

The same new driver, linked to the earlier missing-handler implementation,
fails the first literal witness: vector `$FFE0` returns status `1` / action `0` and no
events, while the factory first writes byte `$3023=08`. This is an executable
before/after reproduction, not a changed fixture expectation. The minimal
stdin is:

```text
1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 65504
```

The final `65504` is vector `$FFE0` in decimal. Changing it to `65506` selects
`$FFE2`; its first write must be `$3023=10`. The complete all-zero witness also checks the
TCTL1 update, TCNT read, final compare value `2`, and the ROM's RTI restoration.

```sh
cmake -S pseudo-source -B build-output-timer -DBUILD_TESTING=ON
cmake --build build-output-timer --target pcm_output_timer_tests
ctest --test-dir build-output-timer --output-on-failure -R '^output_timer_(contracts|rom_differential)$'
python pseudo-source/tests/compare_output_timer_rom.py \
  build-output-timer/pcm_output_timer_tests --report output-timer-result.json
python -m unittest discover -s tests/audit -p test_output_timer_arithmetic.py -v
python tools/audit/reproduce_output_timer_baseline.py \
  --expect-mismatch --out output-timer-baseline-results
```

The portable baseline runner builds public commit
`f2f493f4df5843d37baf23d27a460dbd7d890476` in a temporary detached worktree
and links the current test driver to its production library and vector bridge.
It requires both exact missing-body results and both literal factory traces;
an import, compilation or unrelated assertion failure is rejected. It returns
1 for the known historical defect, or 0 with `--expect-mismatch`; setup and
unexpected results return 2. It removes its temporary worktree and retains
commands, logs and hashes in the selected output directory. Full Git history,
CMake and a C compiler are required. The focused CI runs this before-fix proof
alongside the complete corrected-handler comparison.

Four additional source-bound arithmetic tests parse the actual pulse
declaration, conditional addition and saturation expression under both
16-bit and 32-bit `int` rules. They include negative controls showing that an
`unsigned` accumulator can pass on the host while losing the carry on HC11.
Temporary source mutations from `uint32_t` to `uint16_t` and to `unsigned`
produced 69 and 35 failing assertions respectively, with no setup errors.
These are regression-sensitivity controls, not newly discovered production
defects or native HC11 compilation. The original 14-method arithmetic suite
and its pinned historical baseline counts remain separate.

`--literal-only` executes only the two minimal witnesses and labels the result
with that narrower scope; it does not bypass the full suite's coverage gate.
`--literal-only --literal-vector FFE0` and `--literal-only --literal-vector FFE2`
select the independently failing baseline witness for each leaf.
The driver accepts numeric per-case inputs and returns one JSON object per
case with retained multi-vector steps. The comparator prints exact stdin,
first differing event/state, both results, and retired factory PCs on failure.

The recorded result is in
[`factory_output_timer_validation.json`](../../maps/structure/factory_output_timer_validation.json).
It binds the image, tested binaries, input stream, result stream and interpreter
to hashes, and records the baseline failure separately from the passing body
suite. A repeated build may have a different executable hash without changing
its behavior; rerun the tests for the rebuilt artifact.

These results establish the implemented leaf bodies under the stated fixture
premises. They do not certify the entire firmware, an independent dual-CPU
implementation, native compiled interrupt ABI, live timer/edge scheduling,
physical injector behavior, or cycle timing. The historical audit inventory
remains a snapshot of its original missing-body baseline and is not silently
rewritten by this focused change.
