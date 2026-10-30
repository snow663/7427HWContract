# Joined factory state transitions and optional behavior

This pass specifies thirty selected service, mode, callback and optional-code
transitions from stock BMHM. It joins the earlier field owners to actual caller
order and complete selected execution paths. Twenty-five execution tests plus
one evidence-reproduction test accompany the contracts. They narrow EQ-11;
they do not enumerate every controller/input/interrupt combination.

Authority is the supplied 65,536-byte stock image, SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
Mapped bytes4000..FFFF are committed in the ownership evidence. File padding
below4000 supplies no runtime RAM or missing module implementation.

## Separate the state dimensions

A replacement needs the following independently changing fields. A single
"service mode" enum would lose observable factory behavior.

| State | Producer or transition | Lifetime consequence |
|---|---|---|
|Addressed sessions0042.0/.1|Matching ID sets the bit before complete frame validation; accepted00 or idle expiry clears it|A session can exist without active service or an accepted command04|
|Selectors038E/0399|Accepted command replaces the selector; expiry/qualified cleanup clears it|Changing04 to01 alone does not clear an already active service flag|
|Payload suffix0391..0398 /039A..03A3|Accepted04 copies only its supplied prefix|Short packets, selector changes and ordinary cleanup retain omitted fields|
|Active services003B.4/.3|F64E qualifies engine/transmission service separately|Engine admission precedes its cooldown cleanup; transmission admission requires cooldown0|
|Clear/reset requests003B.0/.1 and0391.4/.6|Packet commit and retained payload|Acknowledgment does not guarantee consumption; engine payload clear can survive session release|
|Edge latches0045.4/.6/.7|Consumer records an admitted action; qualified low request or expiry rearms|BLM rearm requires the engine04 branch; idle expiry can rearm an already held engine clear|
|Receive age0367|Received-byte activity resets it; F781 increments it|A rejected frame can still delay idle expiry|
|Duration0368 and cooldown036A|F781, followed by F64E cleanup|Shared across both services; units are admitted calls, with stock comparisons described below|
|Published controller/output state|Controller calculations and output flushes|Clearing service ownership does not immediately recompute every published value|
|Optional presence / enable / status|Signature word1800, enable0086.6, status0801|These have separate gates and lifetimes|
|Factory action / arm / pointer|Accepted ID0364,0001.0,word038E|The arm bit is not bound to one callback address|

The generated [field map](../../maps/structure/factory_state_transition_fields.csv)
joins39 selected state bytes to the qualified resident read/write inventories.
Arbitrary upload destinations and supplied code retain their broader effects.

## Ordinary service polling has a fixed order

The rooted direct caller chain is7A14→AE85. Near the wrapper's end,
AE9D callsF781, AEA0 immediately callsF64E, andAEA3 returns. These are the only
rooted direct callers of the two helpers. Earlier references to7A14 as another
directF781 call were incorrect.

Consequently idle/duration expiry and service cleanup are consecutive calls
within the ordinary wrapper. No resident AFR calculation executes between
them. An interrupt can occur atAEA0 and change a command beforeF64E reads it.
Tests that deliberately call controller fragments at other boundaries establish
those fragments' behavior, not a new ordinary scheduler history.

### Corrected stock counter words

| Comparison PC | Actual operand | Stock word | Consequence |
|---|---|---|---|
|F7C6|51BB|FFFF|An active-service duration increment fromFFFE reachesFFFF and requests cooldown036A=1|
|F7DC|51BD|0000|On the next F781 call with both service flags inactive, a nonzero cooldown is incremented, compared unsigned against0, then cleared with0368|

The earlier service notes read adjacent words51BA=F4FF and51BC=FF00. Those
are not the operands of these comparisons. There is no stockFF00-call inactive
countdown. These counters are not milliseconds. The ordinary followingF64E
cleans the service flags before the next poll; repeatedly callingF781 while
omitting that cleanup is not an ordinary duration-expiry history.

### Expiry can repeat a held engine clear

The ordinary joined sequence is:

1. Engine04 requests BLM reset0391.4 and engine clear0391.6. F64E callsF280
   andF333 once, setting their edge latches0045.4/.7.
2. With receive age199, F781 increments to200. It clears sessions/selectors
   and0045&D0 while retaining active service003B.4 and the payload suffix.
3. The immediately followingF64E skips BLM qualification because038E is now0.
   Its later engine-clear decision still sees active003B.4 and held0391.6;
   the newly cleared0045.7 permits a secondF333 call.
4. Final engine cleanup then clears003B.4. BLM reset has still run only once.

This is a normal AE85 caller-order witness. It does not require a controller
task inserted between expiry and cleanup. The previously published AFR024B
also remains until a later AFR calculation replaces it.

Accepted session00 differs: it clears ownership but does not itself rearm
0045&D0. A newly pending retained0391.6 can nevertheless be consumed using the
old active flag before engine cleanup. A held request whose edge is already
latched need not run again on that release.

### Cooldown treats the two command blocks differently

On a duration-expiry pass, the engine04 path can still perform its BLM action
before final cooldown cleanup erases038E. Transmission checks036A before
setting003B.3. If it was inactive, its cleanup does not erase the new selector.

The joined test stages a new transmission frame, runs the ordinary wrapper
through duration expiry, and supplies only its accepting checksum IRQ atAEA0.
F64E discards the engine selector but retains inactive transmission selector04.
The next ordinary poll clears cooldown and activates that retained transmission
request without another packet. The test follows both wrapper calls rather
than inventing a permanent cooldown mode from isolated helper calls.

## Cleanup and acknowledgment do not cancel every output

CD90..CDCB consumes raw0393&38 and0394 without an active-service/selector
guard. After engine cleanup, valueA5 still yields issued3FD4=7A50 through
`7000 | (0394 << 4)`. Physical latch behavior remains the device contract.

C514's raw mask/value branch atC528/C52C uses retained039A.6/039B.6 before
the normal fault gates. After transmission release, both raw bits set can still
set004C.5 despite the selected normal inhibit. F3EE's real output flush then
publishes3062.5. C6BB is a separate normal TCC-reason path.

With special fast-group gate001A.5 set, valid command0A is acknowledged and
its request can remain pending while the ordinary wrapper is not admitted.
Complete selected main passes for all16 slots never callF64E orF333 in this
mode. CallingF333 directly proves it can clear001A.5; it does not establish
an admitted ordinary path to that call. Optional supplied code, reset and other
entry contexts retain separate scope.

An AFR fragment provides a further sampling rule: after8C5C samples the old
override enable, one accepting checksum IRQ can replace0395 and0397. The
resumed8C5E read then publishes the new value using the old enable decision.
The next AFR calculation observes the new disabled state. The packet prefix
was received before this window; only the actual accepting ISR is inserted
there. ISR-level payload copying does not make the surrounding controller a
coherent multi-field snapshot.

## Optional entry gates and results

The stock ROM has eight low-memory calls. The test module contains explicit
synthetic JMP/RTS handlers in fixture RAM; its programs demonstrate what each
resident caller consumes. They are not reconstructed GM module bytes.

| Entry | Resident admission and observable result | Later resident behavior |
|---|---|---|
|1800|0086.6 plus local AFR admission; RAM024A is the result|ReturnedA alone is discarded;024A is reloaded into024B. Local AFR service bypasses the hook|
|1803|0086.6 before IAC control; state effects are possible|93D7 immediately clears0038.6. Selected resident position service replaces the target and escapes the remaining controller|
|1806|0086.6 at background wrapperF5CF; state effects survive|ReturnedA is overwritten withF7 before store0F00; the hardware meaning of0F00 remains unnamed|
|1809|0086.6 plus governor admission; entryA/RAM0293 hold error magnitude|ReturnedC=1 selects returnedA for0299;C=0 continues resident computation|
|180C|Runtime word1800=7E18, independent of0086.6; incomingX=7E18|Recurring slot7 connection call can change the enable latch for later callers|
|180F|0086.6 at spark conversion; returnedA is a coefficient|A is saved across the lookup and passed toF550 to scale word005F; fixture40 scales0800 to0200|
|1812|0086.6 after composite command01FD is stored; RAM01FD is the command channel|ReturnedD alone is unused. Resident replacement and later service changes can supersede it|
|1815|0086.6 after desired EGR01AE is stored; RAM01AE is the result|ReturnedA alone is unused. Local service can replace desired value afterward|

Spark service edits occur after the normal signed limits. The complete selected
spark path reaches01EE=01F0=FFB3 after service subtraction; adding a final clamp
would change this tested behavior.

These consumed channels are not a complete ABI. Other register/CCR/RAM/hardware
effects, interrupt-mask changes, stack use and nonreturning behavior require
the supplied implementation. The earlier timing/stack contracts retain opaque
boundaries at these calls.

### Presence, activation, profiling and status remain independent

The signature checks only word1800=7E18, not a length/checksum or a complete
vector block. No ordinary resident writer sets0086.6; they clear or preserve
it. In the explicit test module,180C sets it. A later connection call can clear
it, and connection polling still occurs while it is clear.

If the signature subsequently disappears, the presence probe skips180C but
does not clear0086.6. The other hooks can remain eligible. A rewrite must not
silently bind the enable bit to every signature read.

Slot7 activation can affect the same pass's profiling tail, which samples the
current0086.6 at7A55. The complete selected slot7 pass records peak919 in02E1
from the supplied counter/compare samples1000/900. A separate conditional
deactivation-and-tail fragment skips an update and preserves that peak; it is
not claimed as a second complete sixteen-phase history. Enabling does not
clear earlier peak words02D3..02F2.

AtE4F1, status0801&03 blocks selected closed-loop admission only when0086.6
is set. Disabled hooks do not impose that status gate. Fixtures use status0/3;
unsupported partial multi-bit BRSET cases are rejected by the replay wrapper.

## Factory upload and callback state joins

| Event | Joined resident consequence |
|---|---|
|ID02 arms a returning callback|0001.0 remains set and the current word038E is called on successive loops|
|ID03 supplies a different pointer|An already armed callback uses the new pointer; the arm is not tied to the old address|
|ID03 checksum accepts afterFAA2 has loadedX and the old callback has entered|The current invocation retains its sampled CPU pointer acrossIRQ/RTI; the next loop calls the new RAM pointer|
|ID01 follows an armed callback|The factory loop disarms0001.0 before uploading; a subsequentID03 alone does not rearm it|
|Short ID01 payload|The upload still copies32 source bytes0390..03AF, including retained suffix bytes|
|Forward overlap0390→0391|The first source byte propagates through later source reads; the test observes33 equal bytes across source/destination union|
|Fresh factory TOC3 after five upload stores, beforeFAC4 consumesID01|FA5B resetsSP and abandons the old copy; the still-pending action restarts. The completing fixture records5+32=37 destination writes|

The upload/activation witness loads a32-byte synthetic vector program at1800
through the real ID01 path. A reset-style boot starts withCCR=D0, clears the
working enable bit and retains that code in this explicit memory fixture. The
real recurring signature probe subsequently calls its180C handler, which enables
the hooks. This establishes resident loading/activation mechanics conditional
on writable executable memory and retention; actual board decode/retention is
EQ-13 and actual GM module code isEQ-14.

No upload destination whitelist, safe callback-target list or atomic32-byte
copy is added to the specification. The [service/test contract](FACTORY_SERVICE_AND_TEST.md)
retains the full factory-mode admission and output-cycling details.

## Reproduction, coverage and remaining information

```sh
python tools/verify_factory_joined_state.py --rom /path/to/BMHM.BIN
python tools/verify_factory_joined_state.py --check-recorded
python -m unittest discover -s tests -p 'test_factory_joined_state_and_optional.py' -v
python -m unittest discover -s tests -p 'test_factory_*.py' -v
```

The verifier checks the stock hash, literal counter operands/words, rooted
direct caller order, all eight optional calls, the absence of a resident
enable setter, instruction anchors and execution-test references. Its four
outputs are the [transition table](../../maps/structure/factory_joined_state_transitions.csv),
[optional caller table](../../maps/structure/factory_optional_behavior_contracts.csv),
[field inventory](../../maps/structure/factory_state_transition_fields.csv), and
[evidence record](../../maps/structure/factory_state_transition_evidence.json).

Complete selected service wrappers, main passes, SCI exchanges and factory
loops execute actual stock instructions. Explicit controller fragments have
named boundaries. ASIC samples, ADC-ready values and interrupt injections are
fixture inputs; these tests do not prove physical output response or arrival
timing. The reset test in the earlier interrupt/timing suite now explicitly
starts with resetCCR=D0 as well.

EQ-11 remains open for additional threshold/fault/recovery/ignition/learning
combinations and timing-feasible preemption of other shared state. This pass's
thirty rows are scoped rules, not an exhaustive state-space proof. Stock's
zero broadcast schedule remains inactive; code available under another
calibration is not silently treated as an active BMHM mode. EQ-12/13 still
cover device/board behavior. EQ-14 still requires actual optional module and
external caller bytes to promise compatibility with a particular implementation.
See the [information ledger](FACTORY_EQUIVALENCE_INFORMATION_GAPS.md).
