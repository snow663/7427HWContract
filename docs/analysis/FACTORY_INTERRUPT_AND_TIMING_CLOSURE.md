# Factory interrupt and timing closure

The resident interrupt/timing model is now specified with explicit input and
device premises. Four ordinary sources are live in **stock BMHM**: REF, OC1,
OC3 and SCI. The other vector entries remain documented, but their existence
does not make them active workloads. All local loops and all253 procedure
entries have timing classifications, with a separate one-main-pass envelope.

Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
This closes the ROM-extraction timing package EQ-10 **conditionally**. It does
not assert that arbitrary input edges, failed peripherals or supplied programs
have finite response times. Their arrival/effect contracts are explicit inputs
to an equivalent implementation, rather than unnamed missing factory logic.

## Live sources, flags and priority

The [source table](../../maps/structure/factory_irq_source_lifecycle.csv)
accounts for all15 ordinary vector words. The verifier joins actual register
writers, source guards and mode constants with the earlier mask/stack proof.

| Source | Priority in F1-style layout | Request / acknowledgment | Recurrence |
|---|---:|---|---|
|REF, FFF2→74EA|1|OPTION.IRQE=1 latches a falling edge; honoring IRQ acknowledges that CPU edge latch|New input edges; no ROM minimum spacing|
|OC1, FFE8→CE7C|6|TMSK1.7 and TFLG1.7; CE7E writes80 to clear the flag|REF7503 programs sampled TCNT plus a ROM offset; unchanged compare also matches after counter wrap|
|OC3, FFE4→793D|8|TMSK1.5 and TFLG1.5;7948 writes20 to clear the flag|Old compare+819 counts; divide16 gives13104 E cycles|
|SCI, FFD6→F7EA|15|Enabled receive, transmit-empty or transmit-complete status; literal status/data acknowledgment sequences|Character clocks, buffer state and the26/24→88→40→26 control sequence|

CCA3 requestsHPRIO=15. Its PSEL5 selection defaults toIRQ in the F1-style
table; it does not promote SCI. Priority resolves pending requests, including
afterRTI. OnceTOC3 opens I=0, a lower-priority source can still interrupt its
body. OnlyTOC3 opens ordinary nesting; the other handlers remain I=1 through
their resident closures. The seven rootedTAPs retain reset X=1 in the valid
resident scope, so XIRQ vector entry is excluded there. STOP wake-pin behavior
remains distinct from vector entry.

Boot enablesOC1/OC3 withTMSK1=A0. Other resident writers preserve that pair,
clear OC4/5, or set their individual masks only at77DF/780F. Those two enable
sites cannot be reached by stock REF:400B=04 and400C=B7 force the reviewed
7562/7572/769B/7797 branches away from them. The only direct calls to their
helpers are inside those excluded REF paths. Thus **OC4/5 stay locally
disabled in this stock image**. Their complete132-cycle handler contracts and
injector pulse sequences remain relevant to other mode/calibration selections.

OC2 and IC1/2/3 masks are never enabled. TMSK2 is written only03, leaving
overflow, real-time and both pulse-accumulator interrupt enables clear.
SPCR is written00, keeping SPI disabled. This also explains why the empty SPI
RTI and the generic timer fallbacks are not ordinary interrupt storms. If
supplied code enables them, their literal behavior still matters: FC44 does
not acknowledge SPI, andFC2F does not clear an RTI flag inTFLG2.

Timer flags are single write-one-to-clear latches, not event queues. Multiple
REF edges while its CPU latch is already pending coalesce too. The reference
handler's writes of01 toTFLG1 concernIC3; they are not the acknowledgment of
the external IRQ edge latch. An unchanged comparison can recur after wrap,
even when the handler does not rewrite its compare register.

## Source rates and a complete conditional delay budget

Stock mode pruning reduces the REF upper bound from the earlier general1221
own cycles to **723 own cycles,735 including ordinary entry**. It executes244
distinct resident instruction sites in the pruned graph. The normal SCI bound
remains481 own /493 with entry. OC1 remains109 own /121 with entry.

The programmedBAUD=04 gives256 E cycles per bit and2560 per8N1 character.
This is the PCM SCI clock contract; a Bluetooth bridge's PC baud setting does
not change it. Receive and transmit enable epochs are exclusive under the
four stockSCCR2 values. A clean receiver entry consumes its status/data flag;
a transmitter entry consumes the empty-register condition or changes to the
completion state, which is then disabled when serviced.

For clean acknowledged traffic at the nominal matched rate, charge each new receive/data-space/
completion request to a character or preamble completion. Double buffering
and a request already pending at the start need at most two initial credits.
The preamble is included in character time; changing enable bits does not
provide an unlimited supply of fresh events. Therefore a half-open interval
of lengthT has the conservative SCI bound:

```text
N_SCI(T) <= 2 + ceil(T / 2560)
N_SCI(13104) <= 8
```

An independently clocked sender needs its own receive-character arrival
bound in place of the nominal2560; the deadline below explicitly requires
N_SCI<=8. This requires the clean flag/epoch contract. It does not cover arbitrary
register aliases, independently supplied ready bits or a stale OR-only state.
RIE can request on overrun, whereasF7F1 testsRDRF before callingF90B. A supplied
OR=1/RDRF=0 state therefore repeats the ISR without its status/data read.
The test demonstrates that conditional nonprogress rule; it does not claim
clean frames produce that state or simulate a status/data bus race.

REF7503 is the only residentOC1 compare writer. Its64 ROM offsets at465D..46DC
range from219 to426 counts, or3504..6816 E cycles. In a window shorter than
the16-bit timer wrap, each REF write can contribute at most one additional
OC1 comparison. Allowing a preexisting compare and an initially pending flag
gives the conservative bound `N_OC1 <= N_REF+2`. Rearming or coalescing can
make the actual number lower.

The ordinary masked-work envelope is709 E cycles. Extending the TOC3 prefix
over **both accepted and rejected stack-guard routes** gives1075 own cycles
through arrival at797D;1087 through setting busy on the non-busy route; and
1105 for the corresponding complete busy-route cost. The earlier accepted
busy1090-cycle row remains valid and is tighter in its narrower scope.

A useful sufficient stock contract is at most eight admitted REF invocations
per13104-E window, including carried work, normal clean SCI and no more than
W extra cycles beyond the nominal components:

```text
709 + 12 + 1105 + 8*735 + 8*493 + 10*121 + W < 13104
12860 + W < 13104
```

Thus **W<244 E cycles** excludes the next compare before an ordinary busy
entry returns, and prevents a normal new owner from being interrupted by the
next compare before it establishes busy. One sufficient edge-spacing premise
for the REF count is at least2184 E cycles between new edges, with two carried
invocations conservatively allowed: `2+ceil(13104/2184)=8`.

The ROM does not impose that minimum on its IRQ pin. It is an input contract,
not a measured engine-speed limit. Clock/wait identification and proprietary
input behavior remain EQ-12/13. A rewrite should retain this condition or use
the source-count formula with its actual input envelope; it should not assume
that merely having an I=0 window guarantees a timely interrupt.

## Source-driven execution checks distinguish normal load from bursts

The new harness runs actual handlers and every resident callee. It advances
the divide16 counter, implements single timer flags and priority, schedules
external REF edges, observesCLI's following instruction, and makes ADC ready
129 E cycles after its write. SCI tests advance its character clock, transmit
preamble, data-register/shift-register queue and final completion rather than
providing a ready bit for every desired byte.

A normal eleven-byte service request produces the complete four-byte reply
`F4 56 04 B2`, finishes with the driver released and restores the original
stack. Spaced REF edges at2184 E cycles run alongside that exchange and busy
timer entries; the timer services remain separate.

A different check finishes the real7AB7 conversion wrapper at the comparison
E=13104, then services23 closely spaced REF edges. Their frozen edge times are
replayed a second time with no adaptive refill. Priority delays the first793D
instruction until25518, giving **L=12414**. The next counter match selects a
nested entry at26253, interrupting before7C9D. The issued3068 words are
**066A→0660**, while0150 finishes1489. No timer IRQ is inserted at a chosen PC
and no entry-lateness value is supplied.

This establishes a source-arbitrated realization under the stated fixture
timing and ASIC samples. The23-edge burst violates the eight-REF premise;
it does not contradict the conditional exclusion above. It does not establish
that the ignition module/ASIC produces that burst on the truck. Sustained
REF refill also keepsOC3 pending beyond32768 E cycles without any watchdog
service in the executed handlers. That is starvation, not growing leaf-handler
nesting. The harness does not silently count it as successful timer service.

Register writes commit at instruction endpoints; reads sample at instruction
boundaries. The selected OC3 rearm checks stay more than three timer counts
from the equality/inhibition border. Arbitrary byte-bus phase at that border,
watchdog resets and ASIC read coherency are not invented by this harness.
Real priority selection occurs during interrupt stacking. The selected tests
reject any higher-priority source arriving during their12-cycle entry span,
so they do not depend on guessing that internal bus phase. Received bytes are
scheduled at character completions; there is no analog/noise or bit decoder.

## Tail ownership, guards and stack depth

The deadline contract excludes repeated pre-busy prefix nesting. It does
**not** imply a universal two-frame timer stack. At7A52 the scheduler clears
busy underSEI. When catch-up is pending,7A7D clears the pending latch and7A80
executesCLI, followed by the protected jump at7A81 to7989. A pending timer can
then enter **before7989 sets busy again**. The new entry becomes an owner while
the older owner waits at its completed tail with no remaining callee stack.

The ROM-only test reaches that gap through the actual tail, observes entry
at interrupted PC7989, and checks every owner-frame guard depth. From the
post-boot foreground SP03FF, each such owner contributes a nine-byte IRQ frame.
TSX must be at least03B0. Eight owner frames can pass; a ninth owner-level
entry fails and executes the actual fault/recovery sequence7971..7977,
including **LDS03F6**. It discards intervening frames and reuses the oldest
foreground interrupt frame. This is not a normal return through every owner.

Under the deadline/input, valid-frame and no-alias premises, a conservative
stack-address envelope is:

```text
8 owner frames                 8*9 = 72 bytes
current resident callee peak          21 bytes
one ordinary leaf, frame included     19 bytes
rejected ninth prefix, frame+PSHX     11 bytes
total                               123 bytes below03FF, reaching0384
```

The transient rejected prefix matters: the CPU pushes its frame before the
software guard runs, andREF can preempt that prefix afterPSHX. A selected real
execution reaches0385 beforeLDS03F6 restores the stack, within the0384
structural envelope. That example supplies a guard-depth state; it does not
claim all eight ancestors were reached in one physical engine history.

These bytes are not declared free RAM. Receive/service destinations and
working state occupy part of the same region; active-frame aliases remain
literal writes and can invalidate the valid-frame premise. Nor does this
eight-owner result apply after removing the input/deadline premise: a fresh
timer could otherwise enter before the older entry has even checked its guard.
There is no unqualified safe stack depth supplied merely by the guard constants.

## Main work, all local loops and watchdog outcomes

The [loop inventory](../../maps/structure/factory_timing_loop_contracts.csv)
classifies all46 local cyclic CFG components. Thirty-nine have conditional
finite visit bounds grounded in byte/word counters, ROM sentinels, initialization
or the ADC/latch contracts. Seven are waits, repeat loops or terminal loops.
Calls are composed separately; they do not turn a graph edge into a guessed
constant execution cost. Any new cycle or unreviewed instruction form fails
generation.

The [execution envelopes](../../maps/structure/factory_execution_cycle_envelopes.csv)
cover all253 prior procedure entries plus7989→before7A51, one complete main
pass. The conservative per-pass own-work sum is35733 E cycles under its listed
loop domains. It overestimates branches and includes dormant paths; it is not
a measured maximum. Optional calls retain named sites and coefficient bounds,
andSTOP/SWI/upload boundaries remain visible. Supplied code is not assigned
zero elapsed time or assumed to preserve unspecified state.

Rows with a wait/repeat boundary have no full-time upper number. In particular,
the whole793D handler is not assigned a finite cost by counting its catch-up
loop once. Main passes can continue while later busy entries replenish the
pending bit; a new implementation must preserve this coalescing/repeat rule.

All16 selected main-pass phases execute with actual resident callees and
without scheduler stubs. Their independently counted own work ranges from2999
to7622 E cycles in the explicit zero-sample fixtures. Separate complete learning
reset/clear paths take2867 atB99F,2372 atB9EE and644 atF333. These are execution
witnesses below conservative bounds, not all-input maxima.
Those main-pass meters use the existing immediate-ready ADC fixture; the
conservative envelopes retain the separate poll limits rather than treating
immediate readiness as a hardware guarantee.

The boot loop7208 compares an unchanged A: an initial A>=100 does not make
progress just because an interrupt later changes082F.7B79 is an indefinite
masked wait if ADC completion fails.7D8D/7D8E stops and then loops if resumed;
SWI/illegal/clock-monitor dispositions and the factory terminal loop are also
retained. Replacing these with successful returns would change behavior.

OPTION=B8 requestsCR=0, the shortest COP divider32768 E cycles. Actual enable
also depends onCONFIG.NOCOP and operating-mode controls, not the BIN's padded
low-address bytes. The prescaler phase gives timeout uncertainty; it must not
be treated as an exact freshly reset instruction counter. The service protocol
is55 thenAA. Boot and checksum code issue explicit pairs; normal dispatch also
carries its armed55 between separate task calls. Trap/REF-starvation paths do
not service it. Reset is a defined recovery outcome, not proof a workload met
its scheduling deadline; catch-up work can service COP while remaining active.

## Boot masking correction

The earlier136-cycle row from7467 was labeled as inheriting reset I=1. That
assumption is corrected: the row is now **conditional on actually entering
with I=1**. Boot's selected cold path executesCLI atC57F, thenD183, before the
first timer arm7464. SCI's local enable was already written at7154. Boot
initialization is therefore not one uninterrupted I=1 transaction.

A complete boot-prefix test observes the firstCLI, executes its following
instruction, delivers a real REF/RTI during initialization, and completes to
7467 with SP03FF and I=0. The initial OC3 arm is stillTCNT+8; the recurring
819-count schedule begins when its handler advances that comparison. The
709-cycle local-masking maximum and the recurring deadline arithmetic are
unchanged by correcting the initial-mask label.

## Independent implementation and remaining evidence

An equivalent high-level program now has an explicit interrupt contract:
source predicates and priority; latch/acknowledgment/coalescing rules; timed
compare rearming; SCI buffering/epochs; own-work/loop costs; busy/catch-up
ownership; stack rejection/recovery; and wait/trap/watchdog outcomes. Event
ordering and issued peripheral transactions must be preserved, including the
documented overwrite under the burst fixture.

EQ-10 can be closed as this scoped ROM specification. Testing the normal input
envelope against the installed clock, IRQ source, bus and ASIC remains EQ-12/13;
particular supplied programs remain EQ-14. Further joins of service, mode,
retained state and shared outputs remain EQ-11. Those are the remaining state
and external-evidence packages, rather than another unnamed interrupt pass.

## Reproduce and primary timing references

```sh
python tools/verify_factory_interrupt_timing_closure.py --rom /path/to/BMHM.BIN
python tools/verify_factory_interrupt_timing_closure.py --check-recorded
python -m unittest discover -s tests -p 'test_factory_interrupt_timing_closure.py' -v
```

The [verifier](../../tools/verify_factory_interrupt_timing_closure.py) and
[checks](../../tests/test_factory_interrupt_timing_closure.py) retain the
assumptions in [JSON](../../maps/structure/factory_interrupt_timing_closure_evidence.json).
Instruction costs follow [M68HC11ERG](https://www.nxp.com/docs/en/reference-manual/M68HC11ERG.pdf),
Table1, and [M68HC11RM](https://www.nxp.com/docs/en/reference-manual/M68HC11RM.pdf),
AppendixA; CPU admission/CLI/RTI/IRQE followRM sections5.5/5.7/5.8.
[MC68HC11F1](https://www.nxp.com/docs/en/data-sheet/MC68HC11F1.pdf),
sections5,7 and9, supplies priority, SCI, timer and COP semantics. These are
the stated F1-style CPU contract, not a new physical board identification.
