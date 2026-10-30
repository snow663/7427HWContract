# Factory interrupt admission and current-control output ordering

This joins the existing mask/stack contracts with actual interrupt entries and
adds a second output-changing timer reentry case. The authority is stock BMHM
SHA-256 `6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The executable image and simulator are unchanged.

## Only TOC3 opens ordinary nesting within a resident handler

The [admission table](../../maps/structure/factory_interrupt_admission.csv)
covers all15 I-maskable vector words FFD6..FFF2, which select nine distinct
resident entries. For each of the14 vectors other thanFFE4, the complete
structural resident closure contains noCLI, noTAP and no opaque call. These
handlers inherit I=1 from interrupt entry and keep it through theirRTI.
Their stack summaries have balanced interrupt returns and no SP-reset cut.

The table includes vectors whose local hardware enables may be clear. It
specifies what their resident handler does **if that source is admitted**;
it does not declare all15 sources active on the truck.

| Vector / role under F1-style layout | Resident entry | I inside resident execution | Frame plus additional resident stack bytes |
|---|---|---|---|
|FFF2 external IRQ, factory REF handler|74EA|Remains1 throughRTI|19|
|FFD6 SCI|F7EA|Remains1 throughRTI|13|
|FFE8 OC1|CE7C|Remains1 throughRTI|11|
|FFE0 IC4/OC5; FFE2 OC4|7875;78D9|Remains1 throughRTI|9 each|
|Remaining fallback vectors|FC2F;FC3A;FC44|Remains1 throughRTI|9 each|
|FFE4 OC3 scheduler|793D|Explicitly enables ordinary interrupts|30, resident prefix only|

These numbers include a nine-byte hardware frame and exclude asynchronous
preemption. They are bounds on the analyzed resident stack-pointer envelope,
not measurements of simultaneous peaks or full-machine stack margins.
The TOC3 row retains its existing opaque-code/SP-reset boundaries.

With valid frames and the stated resident scope, an active chain of ordinary
interrupts therefore consists of zero or more TOC3 handlers, optionally
followed by one other handler. REF cannot contain an ordinary SCI or timer
preemption; SCI cannot contain an ordinary REF or timer preemption. Either
can preempt a TOC3 window where ordinary interrupts are eligible, then return
to that timer handler. Priority alone does not prevent a lower-priority
ordinary source from entering an already-unmasked timer handler.

This narrows the nesting grammar; it does not bound how many TOC3 entries
timing can admit. Source requests, local masks, flag clearing, peripheral
completion, priority when several requests are pending, and stack recovery
still belong in the complete timing/admission proof.

The [new checks](../../tests/test_factory_interrupt_admission.py) attempt timer
entry at every executed instruction boundary of one complete selected path
through each of the eight other distinct handlers. Every attempt is rejected.
Additional complete TOC3 executions admit REF or SCI at7A44; those leaf handlers
reject another timer at every executed boundary and restore the interrupted
timer's PC, SP, registers and CCR. No resident callee is replaced.

## Resident execution preserves reset's XIRQ mask

The [seven-site TAP table](../../maps/structure/factory_xmask_sites.csv)
accounts for every rootedTAP and bothTPA sites:

| TAP sites | A.bit6 source | Requested X |
|---|---|---|
|92B3;92D3|92A9 TPA snapshot|Entry X|
|9350;936A;9381;939B|934C TPA snapshot|Entry X|
|7D8C|7D86 LDD #5008|1|

The byte-backed verifier follows both branch arms of the three local blocks,
including every intervening accumulator-A writer. It rejects unresolved A.bit6
atTAP or a new unaccountedTAP site. Complete92A4/92F1 executions check both X
states, both I states and three coolant samples; all six snapshotTAPs execute.

Starting from a hardware reset with X=1, theseTAPs do not clear it. Ordinary
interrupt frames retain that value under the valid-frame assumption. The
FC09 XIRQ handler's sole intentional CCR editORs40 into its stacked byte.
Consequently, the reviewed resident execution never enables the XIRQ vector.
FC09's presence in the vector table does not by itself make XIRQ a live
preemption source during normal resident operation.

This is a conditional resident invariant. Optional1800-family code, a supplied
factory callback, uploads/frame corruption or an external entry with another
CCR state can change the premise. They are not assigned invented effects.

CPU semantics come from [M68HC11RM](https://www.nxp.com/docs/en/reference-manual/M68HC11RM.pdf),
sections5.5..5.7. Reset and XIRQ acknowledgement set X. TAP/RTI can clear X;
writing one leaves its current state unchanged. CLI/TAP unmasking permits the
following instruction to execute before an ordinary interrupt; RTI does not
give the resumed code that same guarantee. Selected injected boundaries are
beyond that delay.

Masked XIRQ can still restart clocks afterSTOP without vectoring toFC09.
At7D8C the factory requests CCR50, executesSTOP at7D8D, then has a self-loop
at7D8E. Masking the vector therefore does not prove the pin electrically
irrelevant to STOP recovery; wiring remains external evidence.

The generic CPU currently assigns CCR directly forTAP/RTI and does not model
STOP wakeup or complete XIRQ arbitration. The new execution checks use only
X transitions for which that assignment matches the documented instruction
rule. The STOP check ends before executingSTOP. An external-code X=0 case
must not be simulated as though7D8C could set X back to1.

## Reentry can lose a current accumulator update

The fast current-control calculation7C13 runs from7B6D **before** the scheduler
tests busy.7B9A enables interrupts;7B9B calls7C13. The call is the instruction
followingCLI, so its entry is beyond the unmasking delay. A further TOC3 entry
can itself execute7C13 before seeing the existing busy flag.

With current-enable004C.5 set,7C13 writes error014F, computes a rounded signed
increment, reads accumulator0150 and later stores the new word. Its critical
instructions on the positive selected path are:

```text
7C7A  ADDD $0150      ; read old accumulator, add increment
7C7D  CPD  #$0E00     ; clamp test
...
7C96  STD  $0150      ; publish accumulator
7C99  LDX  #$0E00
7C9C  FDIV           ; convert held D value to duty fraction
...
7CA5  STAA $014C     ; publish command byte
...
7BA3  STD  $3068     ; actual issued word: 0600 | byte014C
```

Its local calculation does not mask interrupts around these updates. An IRQ
preserves the interrupted CPU registers while allowing the nested handler to
change shared RAM. On return, the older D/A values can be stored over the new
state or command.

### Complete busy-handler witnesses

All runs begin with busy004F.2=1, current-enable004C.5=1, reference014D=20,
old error014F=0, accumulator0150=0400, rawB5=40, batteryA7=128 and SP03F4.
The complete stockB2ED selector initializes paired coefficients0153=64 and
0154=35 fromB31D/B325 at index1. Values are decimal except addresses,0400 and
the issued words. Other fixture RAM begins zero. Four ADC7 samples are zero;
ADC ready and IRQ arrivals are explicitly supplied.

Both timer entries execute the complete793D busy handler, every tick-service
callee and the actual7BA3 hardware write. There are no scheduler substitutions,
opaque hooks or entry into the main controller body. Neither arrival advances
phase0002; both leave busy set and one coalesced pending bit. No stack recovery
occurs. Both IRQ frames return to the original caller.

| Two-arrival schedule | Final0150, decimal | Final014C, decimal | Issued words at3068, hex |
|---|---|---|---|
|Sequential complete handlers|1489|106|0660 → 066A|
|Nested before7C7A accumulator read|1489|106|0654 → 066A|
|Nested at7C7D, after that read|1344|96|0654 → 0660|
|Nested at7C96, before accumulator store|1344|96|0654 → 0660|
|Nested at7C99, after accumulator store|1489|96|066A → 0660|
|Nested at7CA5, before command store|1489|96|066A → 0660|

The sequential first increment is320, giving1344. With the new error already
published, the second increment is145, giving1489. Nesting before the outer
accumulator read lets that outer calculation add to the nested result. Nesting
after its read lets the outer store replace that nested result with1344.

The last two rows establish a separate effect: the accumulator remains1489,
but the interrupted calculation still converts its older1344 register value.
It publishes96 after the nested handler has already issued106. Comparing only
the final accumulator would miss that command reversal.

This is a source-level ordering contract, not measured incidence, a proven
hardware-feasible arrival schedule, a pressure scale or measured solenoid
behavior. TOC3 is scheduled from its prior compare plus0333; programmed timer
prescaling and complete competing-handler/peripheral bounds constrain whether
these windows can actually be crossed by another timer arrival. This pass
supplies arrivals at eligible instruction boundaries and leaves that joined
time proof open. In particular, the existence of an unmasked instruction is
not itself proof that another compare can occur during it.

The [fast-tick timing follow-up](FACTORY_FAST_TICK_TIMING_CONTRACT.md) now gives
a conditional1090-E-cycle complete busy-handler bound against the13104-cycle
compare interval. It excludes the overwrite below an explicit delay budget
and reproduces it with counter-driven compares at late supplied entry times.
The preceding factory paths and competing sources that could produce those
times remain unproved; the earlier table is not a measured incidence claim.

## Consequence for an independent implementation

The reconstruction now has a narrower ordinary interrupt graph, a conditional
cold-reset X invariant, and a current-control ordering example independent of
the [IAC/gear shadow case](FACTORY_STACK_AND_SHARED_OUTPUT_CONTRACT.md).
Treating busy as a lock around all timer work, making7C13 automatically atomic,
or validating only final shared RAM would change the selected issued-command
semantics. Choosing to remove such ordering effects in a replacement program
is a design choice that must be distinguished from strict factory equivalence.

The remaining timing work must determine physically admitted TOC3 depth and
which conditional schedules survive the real event/peripheral constraints.
The remaining state work extends these checked joins to other output-changing
service, mode and retention combinations. Neither is replaced by instruction
coverage counts.

## Reproduce

```sh
python tools/verify_factory_interrupt_admission.py --rom /path/to/BMHM.BIN
python tools/verify_factory_interrupt_admission.py --check-recorded
python -m unittest discover -s tests -p 'test_factory_interrupt_admission.py' -v
```

F1-style vector source names follow [MC68HC11F1](https://www.nxp.com/docs/en/data-sheet/MC68HC11F1.pdf),
table5-4; they do not identify the installed chip package or external wiring.
Connected evidence: [scheduler](FACTORY_SCHEDULER_MAP.md),
[transmission](FACTORY_TRANSMISSION_CONTROL.md),
[stack envelopes](FACTORY_STACK_AND_SHARED_OUTPUT_CONTRACT.md), and
[information ledger](FACTORY_EQUIVALENCE_INFORMATION_GAPS.md).
