# Information needed for an independent factory-equivalent program

An independent implementation needs the factory's calculations, state
transitions, sampled-input rules and hardware transactions, including their
event-order dependencies. This ledger separates rules already recoverable
from BMHM from genuinely external information. A compiler/build milestone is
not used as a measure of knowledge completeness.

Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The [machine-readable ledger](../../maps/structure/factory_equivalence_assumptions.csv)
contains fifteen scoped contracts and five remaining work packages. This is an
initial prioritized ledger, not an exhaustive denominator or completion score.

## What this pass establishes from the ROM

Twelve new [interrupt-contract checks](../../tests/test_factory_interrupt_contracts.py)
execute the existing HC11 CPU with the hash-checked committed mapped bytes.
The complete REF and SCI handlers execute where specified below. The
scheduler-only witnesses retain the existing runner's explicit callee stubs;
their counts establish scheduler admission, not completed controller work.
No simulator feature or firmware behavior is changed by this analysis.

### RAM refresh is protected per 16-byte block

7483 executesSEI before eight LDD/STD self-copy pairs. The mask remains set
through cursor029B's update at74A7;74AA executesCLI. Thus an ordinary
I-bit-maskable interrupt cannot modify a word between its read and self-write.
The test attempts REF entry at all19 intervening instruction boundaries,
then delivers REF afterCLI and the following branch. The next block preserves
the newly set0050.5 pending flag in the preceding block.

An entire multi-block refresh is not atomic. XIRQ, reset and external bus
activity are separate boundaries. The hardware purpose of refresh is not
needed to retain this literal software rule.

### The asynchronous output helper relies on its callers' mask

8548 itself has noSEI/CLI.8577 reads word3FFC,857F clears high-byte bit2,
and8587 sets it, retaining the original low byte in D. That low byte also
contains the SCI driver bit. The resident calls are:

| Call | Protection across8548 |
|---|---|
|84AA, main fuel path|84A9 executesSEI;84AD executesCLI after the helper returns|
|762D, REF path|The complete74EA IRQ path inherits I=1 and does not clear it before this call|

Both contexts reject an attempted SCI interrupt at every tested helper
boundary. A later SCI completion can release low-byte3FFD.2 after unmasking.

A deliberate counterexample calls8548 with I=0, violating both resident
contexts: initial3FFC=B93E, then SCI completion before857F writesB93A, but
the resumed helper writes stale low byte3E and finishesBD3E. The actual
factory callers prevent that selected schedule. This demonstrates why a
rewrite must carry the caller contract along with the helper's arithmetic;
it is not an observed factory race or an assertion about physical latch reads.

### Scheduler reentry changes at the busy store

7958 enables interrupts.7B6D performs ordinary tick service before797D tests
busy004F.2;7989 sets busy for a new main pass. A nested timer entry before
that store can therefore execute a main pass itself. Once busy is set, a
nested entry still executes tick service but only sets pending003A.5.

The bounded witness injects three complete TOC3 IRQs into one outer IRQ:

| Injection boundary | Main-pass phases | Phases sampled by the four91A3 call admissions |
|---|---|---|
|797D, before the busy test|1,2,3,4|0,0,1,2|
|798C, immediately after busy is set|1,2|0,0,0,0|
|7A44, during the busy main body|1,2|0,1,1,1|

In the last two rows, three arrivals set one coalescing pending bit and cause
one catch-up main pass. Catch-up does not repeat7B6D. Actual IRQ frames and
stack restoration are checked; IRQ return requires both the saved PC and SP,
because a nested handler can visit the same PC before returning.

These are conditional event schedules. No physical arrival rate, ADC waiting
time, full-controller worst-case execution time or probability is inferred.
A reconstruction cannot use one rule saying every timer arrival advances the
main phase, or one rule saying every nested timer arrival merely sets pending.

### Some helpers explicitly enable interrupts on return

F3EE..F41F and91A3..920D executeCLI beforeRTS, even when entered with I=1.
They do not restore a caller-saved interrupt mask.8548 preserves the tested
entry mask. The ordinary scheduler's use of these helpers must be analyzed
with those return conditions. Replacing them with a generic nested critical
section that restores the previous mask changes the instruction-level rule.

The [global mask table](../../maps/structure/factory_interrupt_mask_contracts.csv)
now summarizes all253 procedure entries on structural normal-RTS paths:
193 preserve the entry I bit,16 return I clear,26 depend on path/input, and18
have no normalRTS return. The sixteen always-clear entries include scheduler
wrappers and callers, rather than sixteen independent masking primitives.
For every possible masked return from an initially clear I bit, the analysis
finds a transitive opaque call. Ordinary resident paths without those calls
therefore have no such return in this conservative structural graph.

The analysis follows both branch arms, composes direct-call and16-slot
summaries, widens all nine opaque calls to either I state on conditional normal
return, and tracks A.bit4 throughTPA/TAP. The IAC routines92A4/92F1 preserve
their saved I bit while restoring other condition flags; treating everyTAP as
an arbitrary interrupt-mask change would lose that fact. Selected summaries
are compared with actual execution for both entry masks and three coolant
inputs. All seven rootedTAP sites and bothTPA sites are inventoried.

These are possible normal-return masks under explicit assumptions. Branch
feasibility, full CCR/register/stack behavior, arbitrary supplied-code effects,
execution time and interrupt schedules are not established by this table.

### ALDL acknowledgment is separate from service execution

A valid F4 command0A sets003B.1. Its response isF4 56 0A AC. The erase path
runs later, whenF64E reachesF74C and its edge latch permitsF333. Any next
accepted ordinary command first clears003B bits03 atF9D6.

Two complete exchanges establish the timing dependency: command0A followed by
command01 before theF64E poll produces valid replies but noF333 call. Insert
the poll between the exchanges andF333 executes once. A bad-checksum second
frame keeps the earlier request: the shared receive prefix changes, while
accepted selector038E remains0A, and the later poll still callsF333.

These are mailbox and edge-latch rules, not a queued promise to perform each
acknowledged request. The test executes the full SCI ISR/RX/TX paths with
explicit ready/status samples; it does not model collisions or Bluetooth.

Likewise, an accepted shorter command04 replaces only its supplied prefix.
The test follows an eleven-byte service payload with two bytes04 AA; the
remaining nine service bytes retain their previous values. There is no
implicit clearing of the omitted suffix.

### Trap, reset and XIRQ dispositions differ

The stock vector words and actual resident handler bodies establish:

| Vector/source | Entry |0000 cause bit|Resident destination|
|---|---|---|---|
|FFF6 SWI|FC04|08|Loop atFC07|
|FFF8 illegal opcode|FC1A|10|Loop atFC1D|
|FFFA COP reset|FC1F|20|Jump throughFC2C to7100|
|FFFC clock-monitor reset|FC24|40|Loop atFC27|
|FFFE external reset|FC29|80|Jump throughFC2C to7100|

Each BSET preserves the other cause bits present at entry. Later conditional
boot validation can clear0000..000A, as the retention contract specifies.
The loop bodies do not themselves service COP; subsequent hardware reset
timing and RAM retention are separate observations.

XIRQ'sFC09 handler sets0000.2, pulls the stacked CCR byte, ORs40 into it,
pushes it back andRTIs. Under the documented XIRQ entry conditions this
returns with X masked. It is not equivalent to an ordinary emptyRTI handler.
The test supplies hardware's entry X=1 precondition explicitly; the generic
CPU entry helper does not implement complete XIRQ arbitration.

CPU interrupt stacking, I/X masks and instruction-boundary recognition follow
[M68HC11RM](https://www.nxp.com/docs/en/reference-manual/M68HC11RM.pdf),
sections5.5..5.7. CPU instructions cannot be interrupted midway; this does
not establish that a proprietary peripheral latches both bus bytes coherently.

## Stack and shared-output follow-up

The [stack/shared-output contract](FACTORY_STACK_AND_SHARED_OUTPUT_CONTRACT.md)
adds 253 resident stack envelopes:237 without an opaque/reset boundary and16
prefixes ending at explicit boundaries. The six-byte IAC frame is restored
through a proved saved-Y relationship; A407's service escapes skip the rest of
its controller. Entry guards do not reserve all later callee stack bytes.

Nine further checks execute the complete selected TOC3 handlers and every
resident callee. A nested timer atC51F/C521/C522 can overwrite a new IAC shadow
with C514's older register value; the pending catch-up pass publishes that
stale field through the realF411 flush. The two-arrival comparison issues
10,39 sequentially versus10,31 when nested, with the same final software position.
This is an instruction-order witness, not measured truck incidence.

7B79 also demonstrates why a finite stack envelope is not an execution-time
bound: it waits with I set and no software timeout until ADC ready. The F1-style
ADC has a documented nominal completion contract, which must be a timing-proof
precondition; held-ready failure and actual board behavior remain distinct.

## Interrupt admission and current-control follow-up

The [admission/current-output contract](FACTORY_INTERRUPT_ADMISSION_AND_CURRENT_OUTPUT.md)
covers all15 ordinary interrupt vectors. The14 other thanTOC3 keep I set
throughRTI across their complete resident closures; onlyTOC3 opens ordinary
nesting. All seven rootedTAPs preserve reset's X=1, under valid frames and no
supplied-code CCR effects. XIRQ's vector is therefore not an additional live
preemption source in that resident scope; STOP pin recovery is separate.

Seven additional checks execute complete selected handlers. Timer reentry in
the current-control calculation can lose an accumulator update, changing the
two issued3068 words from0660,066A to0654,0660. Reentry after the accumulator
store can instead preserve its final value while publishing066A,0660. This
joins actual instructions and issued outputs; physical timing feasibility
and occurrence remain open, not inferred from I=0 alone.

## Conditional fast-tick deadline follow-up

The [fast-tick timing contract](FACTORY_FAST_TICK_TIMING_CONTRACT.md) derives
13104 nominal E cycles between recurring OC3 compares. Its independently
assigned instruction costs and bounded polls give a1090-cycle upper envelope
for a complete ordinary busy handler, includingRTI and excluding initial
stacking. ADC7's129-cycle completion, accepted stack and nominal bus timing
are explicit premises.

If entry lateness L plus additional delay H is less than12014 E cycles, that
busy entry returns before the next comparison. Counter-driven complete-handler
fixtures reproduce the current overwrite with sufficiently late supplied
entries and normal ADC completion. A passed rearm target instead waits for
counter wrap; it does not queue elapsed819-count intervals. Five new checks
verify this conditional timing layer. The source of required lateness, complete
main/tail costs and interrupt-arrival envelopes remain open. The following pass
supplies local masking and individual competing-handler costs.

## Masked intervals and competing interrupt cost follow-up

The [masked-interval/IRQ timing contract](FACTORY_MASKED_INTERVAL_AND_IRQ_TIMING.md)
accounts for all29 rooted SEIs. Its27 ordinary resident spans are bounded at
709 nominal E cycles, includingCLI's following instruction. Complete ROM
execution reaches that maximum with three bounded ADC timeouts. The separate
optional broadcast copy is not selected by stock's all-zero schedule; STOP,
traps, supplied code and invalid frames remain explicit boundaries.

All eight distinct non-TOC3 ordinary handlers have full resident bounds.
REF is at most1221 own cycles; SCI is at most481 in the normal eleven-byte
copy scope, or964 with the validated34-byte receive scope. Each ordinary
entry additionally costs12 nominal cycles. REF's latch transitions and
SCI's ROM lookup chains/copy counts make their apparent loops finite.
Six new checks execute selected masked spans and complete REF/SCI handlers.

These components support a conditional workload inequality against the13104
cycle compare period. They do not determine the number of admitted arrivals,
bursts or global TOC3 depth. Source enable/acknowledgment/rearm lifecycles and
interarrival constraints are the next timing target.

## What still requires information or further extraction

The ledger deliberately separates two ROM-analysis jobs from three external
evidence packages:

| ID | Remaining question | Information source / reconstruction consequence |
|---|---|---|
|EQ-10|Worst admitted interrupt nesting, stack footprint and masked/unmasked execution bounds across complete callees|ROM plus CPU timing semantics. All253 mask/stack summaries, ordinary nesting grammar,709-cycle local masking maximum and full competing-handler costs join the1090-cycle busy-handler bound. Source arrival envelopes and complete non-busy main/tail work must establish reachable L/H and TOC3 depth. Actual clock/wait behavior is separatelyEQ-13.|
|EQ-11|Complete cross-controller state transitions under service, clear, mode and retained-state changes|ROM value flow and selected event schedules. IAC/gear shadow and current-control accumulator/command ordering have complete selected-handler witnesses; other combinations and feasible timing still need a checked joined state specification.|
|EQ-12|Proprietary device read coherency, latch/trigger semantics and permissible transaction timing|Targeted bus/register/output observations. Existing access order, byte operations and deliberate delays can be retained while this contract is refined.|
|EQ-13|Actual board clock/wait behavior, reset retention and physical memory decode|CPU/board identification and targeted measurements. ROM gives programmed values and boot clears; it does not give every external power/reset effect.|
|EQ-14|Full calling convention/effects of optional supplied code and intended external tail-entry callers|Actual module/caller bytes or runtime evidence. Preserve the known probe/guards and exposed interfaces; complete optional-module compatibility remains conditional.|

EQ-10 andEQ-11 do not require a missing GM source file or new truck data.
They require extracting and joining information already encoded in the ROM.
EQ-12/13 concern the observable CPU/device contract. Reverse-engineering the
ASIC's internal implementation, assigning engineering names to every raw
count or redesigning actuator drivers is not a prerequisite if the original
transactions and representations are retained.

EQ-14 is not a missing resident fuel/spark algorithm. The eight external
entries and arbitrary factory callback/upload interfaces are outside the
supplied resident code. A particular module's internals must not be invented.

The next ROM-only work is to join the253-entry mask/stack contracts, local
masking/handler costs and conditional fast-tick deadline with source arrival bounds,
then extend the output-changing state combinations inEQ-11 beyond the IAC/gear
and current-control cases. A whole-machine
equivalence claim needs those contracts and the appropriate external evidence;
the number of classified instruction bytes supplies no substitute.

## Reproduction and connected evidence

```sh
python -m unittest discover -s tests -p 'test_factory_interrupt_contracts.py' -v
python tools/verify_factory_interrupt_masks.py --check-recorded
python tools/verify_factory_interrupt_masks.py --rom /path/to/BMHM.BIN
python tools/verify_factory_interrupt_admission.py --check-recorded
python tools/verify_factory_tick_timing.py --check-recorded
python tools/verify_factory_masked_timing.py --check-recorded
python -m unittest discover -s tests -p 'test_factory_*.py' -v
```

Related contracts: [REF/EST lifecycle](FACTORY_STARTUP_REF_EST_LIFECYCLE.md),
[flag lifetimes](FACTORY_FLAG_LIFETIMES.md),
[serial protocol](FACTORY_SERIAL_ALDL_PROTOCOL.md),
[scheduler](FACTORY_SCHEDULER_MAP.md),
[output boundaries](FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md),
and [global ownership](FACTORY_OWNERSHIP_CLOSURE.md).
