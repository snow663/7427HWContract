# Factory stack envelopes and shared IAC/gear output ordering

This closes another part of the independent-reconstruction information
checklist: resident stack-pointer use, frame cleanup and nonlocal returns,
plus an output-changing interaction between the timer step service and
transmission shadow publication. Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
No calibration or executable byte is changed for these checks.

## A finite resident call envelope is different from a nesting bound

The [253-entry table](../../maps/structure/factory_stack_contracts.csv) follows
both branch arms and composes the actual call graph, including the16-slot
scheduler table.237 entries have a finite resident envelope without an opaque
or SP-reset boundary;16 have a finite resident prefix ending at such boundaries.
All nine opaque calls remain cuts. There is no assigned stack bound for their
unprovided implementations or for arbitrary factory uploads into active frames.

Depth is bytes below **SP at procedure entry**. The caller's two-byte return
frame, or the interrupt's nine-byte frame, is already outside that measurement.
Pushes, pulls, calls and local SP restoration are included. These are stack
pointer envelopes with valid return frames and no asynchronous preemption,
not complete memory-write footprints, feasible-path coverage or WCET bounds.

| Entry / context | Additional resident bytes below entry SP | Qualification |
|---|---|---|
|793D TOC3|21|Resident prefix; stack recovery, factory redirection and opaque hooks are boundaries|
|74EA REF|10|Resident handler; interrupted frame counted separately|
|F7EA SCI|4|Resident handler; interrupted frame counted separately|
|7B6D ordinary tick service|4|Complete resident calls; ADC wait still needs a completion condition|
|D840 transmission computation|15|Complete resident calls; matched by selected actual execution|
|99C5 IAC computation|14|Includes its six-byte local frame and nested helpers; matched at three SP locations|
|91A3 IAC step service|0|No additional data/call stack; may still change shared state|

For a single TOC3 resident prefix entered from foreground SP03FF, the frame
uses9 bytes and that prefix adds at most21 under this analysis:30 total, with
SP no lower than03E1. This is not the full-machine bound when another interrupt
can arrive or a supplied-code/SP-reset boundary is crossed.

The separate [segment table](../../maps/structure/factory_stack_segments.csv)
starts after known assignments:7103 atSP03FF after reset'sLDS;797A atSP03F6
after recovery'sLDS;FA5E atSP03FF after factory entry'sLDS. These assignments
discard a previous context and cannot be treated as ordinary balanced returns.

## The IAC TYS is a proved local-frame restoration

99D7..99DF pushes six bytes, then99E0'sTSY establishesY=entry_SP-5.
The complete existing register/stack analysis tracks Y through every resident
callee. Before9C1D it provesSP=entry_SP-6 andY=entry_SP+1, after the final
ABY by6.9C1D'sTYS therefore restoresSP=entry_SP, and the followingRTS returns
withSP=entry_SP+2. It is not another unconstrained stack reset.

The verifier checks the unique local entry and these symbolic states; changed
code or a new entry into that cleanup fails verification. Actual complete99C5
execution reaches the14-byte envelope and restores the caller atSP03D0,03F4
and03FF. This retains local-frame provenance separately from absolute RAM.

## Service can deliberately skip the rest of the IAC controller

A407 has pre-RTS depths0 and-2. On its escape routes it pops its own return
address, then the finalRTS consumes the93D0 controller's return address.
The sole resident call is93DE. Its escaping continuation is the controller's
caller, not93E1. The analyzer propagates that exit without walking the skipped
controller body.

Complete executions establish the separate cases:

| Service selection | Control transfer / state |
|---|---|
|0391.5 reset request|Return to controller caller; position0007=255, target0008=0|
|0395.0 set and0395.1 clear|Return to controller caller after setting target0008=0396|
|Only038F.6 selected|Return to controller caller after kicker state/output-request work|
|0395.0/.1 both set|Return locally to93E1;0857=0396 and0038.6 set|

All tested escapes restore the original caller SP. A high-level recreation
needs an explicit whole-controller escape for the first three cases; an
ordinary return from the service helper alone would continue different code.

## The entry guard is not a reservation for future calls

The scheduler checksTSX against its bounds at795C..7971. A test entering that
check withSP03AF is accepted without003A.3. Executing the following complete
tick service then lowersSP to03A9: its call frame and nested calls consume six
more bytes, writing below03B0.03B0 is also the foreground watermark scan's
start, not a hardware-enforced lower bound for every subsequent stack access.

This is a selected initial-SP witness. It does not establish that ordinary
truck timing reaches that entry state or that a collision has occurred.
Maximum admitted nesting and the hardware arrival constraints must still be
joined before claiming a full-machine stack margin.

## A timer update can be overwritten by the gear-shadow merge

Transmission publicationC514 obtains gear-pattern data fromB319+byte00D9.
C51C loads old004C into B, thenC51F masks B withFC, C521 combines the gear
pattern, andC522 stores the whole byte back to004C. This sequence has no
localSEI. Normal slot3/7/B callers can reach it with I clear.

TOC3's7B6D calls the actual91A3 IAC step service before checking busy. Its
own004C update masks interrupts and replaces bits1C while preserving the
other fields. That protection does not cover an earlier C514 read. If TOC3
enters afterC51C and beforeC522, RTI restores C514's older B register; the
whole-byte store can overwrite the intervening IAC-field change.

### Complete-handler witness

Both executions start with the same stock image, phase0002=2, position0007=2,
target0008=1, mode000A=10, shadow004C=10, raw batteryA7=128 and period3FC0=0700.
Active engine service selects the supported position override0395=1,0396=1,
holding target1 while the ordinary controller runs. Other fixture RAM begins
zero. ADC ready/status values are supplied explicitly.

The first step service changes direction without moving. The second decrements
the software position to1 and advances mode000A's IAC field to18. Each execution
services two real TOC3 entries and dispatches main phases3 and4. Every selected
resident callee executes; there are no scheduler/callee substitutions or invoked
external hooks. Partial multi-bitBRSET cases outside the existing verification
CPU's usable subset are rejected rather than counted as evidence.

| Timer-entry ordering | Bytes written byF411 to3062 | Final software position |000A &1C|004C &1C|
|---|---|---|---|---|
|Two complete sequential TOC3 entries|10,39|1|18|18|
|Second entry nested atC51F|10,31|1|18|10|

In the nested case, the busy reentry sets pending003A.5. After C514 restores
the stale field, the pending catch-up main pass reaches the actualF3EE/F411
flush without another7B6D step-service call. It therefore publishes31. This
establishes an issued-command difference, not merely a transient RAM difference.
It also shows why the same logged software position need not mean the same
issued phase sequence.

Five instruction boundaries were tested through the complete handlers:

| Nested TOC3 boundary | Final issued IAC field |
|---|---|
|C51C, before old-shadow load|18; new shadow is loaded afterward|
|C51F, after old-shadow load|10; intervening field overwritten|
|C521, before addition|10; intervening field overwritten|
|C522, before store|10; intervening field overwritten|
|C525, after store|18; step service preserves the new gear field|

These are conditional instruction-order witnesses, not measured truck
incidence, a physical motor-step claim or a proof of particular timer spacing.
The waveform/pin meaning and real event timing remain external observations.
The factory merge is thus a concrete shared-state ordering rule for the
equivalence specification, even though the nominal fields are disjoint.

## The ADC poll separates stack bounds from execution-time bounds

7B70 sets I,7B73 starts conversion, and7B79 repeatedly tests3030.7 with a
self-branch. It has no local counter, watchdog service or software timeout.
Holding ready low for200 iterations keeps PC and SP unchanged and refuses
REF entry. Releasing ready lets the complete7B6D return within its four-byte
additional stack envelope. The separately calledF25F poll has different rules;
its timeout cannot be assumed to protect this earlier loop.

Under the documented F1-style CPU layout, boot'sOPTION=B8 enables ADC power
and selects E clock. The [MC68HC11F1 data sheet](https://www.nxp.com/docs/en/data-sheet/MC68HC11F1.pdf),
section10 and figure10-3, specifies a128-E-cycle four-conversion sequence
following a one-E-cycle start delay. That supplies a nominal peripheral timing
contract if this CPU layout and operating conditions apply. It does not add a
software timeout or establish actual board clock frequency.

[M68HC11RM](https://www.nxp.com/docs/en/reference-manual/M68HC11RM.pdf),
sections5.5..5.7 and theWAI entry, also matters for nesting:WAI pre-stacks the
nine-byte frame; waking does not push a second one. CLI/TAP unmasking permits
the following instruction to execute before an interrupt is recognized.
The new witnesses avoid relying on an immediate interrupt in that protected
slot. Normal ADC completion and physical event-arrival bounds are inputs to
an eventual timing proof, not consequences of finite stack use.

## Reproduction and remaining scope

```sh
python tools/verify_factory_stack_contracts.py --rom /path/to/BMHM.BIN
python tools/verify_factory_stack_contracts.py --check-recorded
python -m unittest discover -s tests -p 'test_factory_stack_and_shared_state.py' -v
```

Nine new checks cover generated contracts, complete local-frame restoration,
transmission math depth, service exits, WAI wake, guard margin, held-ADC waiting
and the complete-handler output-order comparison. Fresh mode checks the supplied
stock image identity; recorded mode reuses committed mapped bytes.

The [information ledger](FACTORY_EQUIVALENCE_INFORMATION_GAPS.md) now has
resident stack envelopes alongside the mask contracts. EQ-10 still needs
admitted asynchronous nesting and timing bounds with peripheral conditions.
EQ-11 now includes the actual IAC/gear ordering witness; other cross-controller
combinations retain their explicit scope. Neither result depends on the user's
separate diagnostic-test BIN or a new hardware observation.
