# Factory service, override lifetimes and manufacturing test

This closes accepted serial payloads through the resident control consumers,
the session timers and the separate manufacturing-test loop. It uses the ROM
authority and instruction inventories in the [closure ledger](FACTORY_SERIAL_SERVICE_CLOSURE.md).
Wire framing and descriptor selection are specified in the
[serial protocol](FACTORY_SERIAL_ALDL_PROTOCOL.md).

## Accepted normal-service packets, F9B9..FA21

Checksum-valid acceptance saves the selected descriptor's ID in0364. With0050.3
clear, use038E as the engine command block, or0399 forF5. Clear3B bits03, then
copy036C's command byte to that block's first byte. Subsequent actions are:

| Command | Accepted-packet state action |
|---|---|
|00|Clear0042.0 for engine, or0042.1 for transmission|
|01/02/03|Keep command selector, with request data left in036C..038D; do not copy the whole request to the service block|
|04|Copy `min(RX_N,11)` bytes from036C to the selected service block, including the command byte|
|0A|Set3B.1 for engine clear, or3B.0 for transmission clear|

An accepted ordinary packet can therefore clear a previous clear request before
the slower consumer acts on it. A command04 shorter than11 retains the uncopied
suffix; there is no automatic zero fill. A different command changes the selector
but retains the earlier override bytes. Service and command-block storage are
not interchangeable with an atomic validated control transaction.

## Engine override block and controller connections

Engine command04 occupies038E..0398. 038E=04 with0042.0 admits service3B.4
atF715. The normal service consumer isF64E, reached from the normal scheduler
and transmission input wrapperAE85; its effects are applied at those call
admissions. Individual controllers then consume the flags/bytes as follows:

| Field | Resident use and contract |
|---|---|
|038F enable mask /0390 value mask|Output requests including AIR bit1, fuel-related bit2 and throttle kicker bit6; corresponding controller gates still apply|
|0391.3|EST diagnostic service selection atAC45|
|0391.4|Rising request resets BLM throughF280, latched by0045.4|
|0391.5|IAC reset escape throughA407→A3FA|
|0391.6|Engine diagnostic-clear request, shared with3B.1 and latched by0045.7|
|0391.7|Can suppress the normal scheduler heartbeatF3E4|
|0392.0|Indexed service input at86FD/E49E: I/P control/reset versus closed-loop admission use opposite local selections; see the fuel-learning contract|
|0393.0,0394|Purge duty override at9153..9161|
|0393.1,0394|EGR desired/controller override atD030..D03A andD20B|
|0393 bits38,0394|Shared auxiliary output3FD4 selection, including an ungated raw-field consumer|
|0395.0/.1,0396|IAC direct-position or desired-RPM selection|
|0395.2,0397|AFR override before024B publication|
|0395.3/.4/.5,0398|Spark override enable, replace/add selection and subtraction; applied after signed spark limits|

The exact masks, priority and early returns remain in the controller contracts:
[IAC service](FACTORY_IAC_LEARNING_AND_OUTPUT.md),
[fuel/AFR](FACTORY_UPSTREAM_FUEL_CALCULATIONS.md),
[spark](FACTORY_UPSTREAM_SPARK_CALCULATIONS.md),
[diagnostics](FACTORY_DIAGNOSTICS.md), and
[emissions/output selectors](FACTORY_EMISSIONS_CONTROL.md).
0392's resident consumers use indexed addressing. The new
[global alias join](FACTORY_GLOBAL_ALIAS_CONTRACT.md) identifies86FD/E49E;
absence from the earlier direct-owner union did not establish an unused field.

Service ownership does not imply that every consumer checks3B.4. In particular,
CD98's shared3FD4 selector inspects0393 bits38 without a local active-service
test, and C6BB inspects raw transmission override bytes. Retaining payloads
after expiry can therefore matter even when the main service flag is gone.
`factory_serial_states.csv` records direct byte-overlap owners; indexed uploads,
clear loops, boot initialization and arbitrary callback effects remain distinct.

The IAC service helper can pop its own return address and jump out of a caller's
remaining controller work. That behavior is already documented atA407; service
acceptance does not turn the escaped continuation into a reachable return path.

## Transmission override block

Transmission command04 occupies0399..03A3. F677 requires0042.1, selector0399=04
and word036A=0, then sets3B.3. Mask/value bytes039A/039B bits08 and10 produce
a two-bit solenoid state. Compare againstB319's first three patterns and map
the result to one-based service gear0103=1..4. At039E.7, copy039F to010A.
03A0 bits40/80 update011A.6/.7. 03A1 writes0111 whenever this admitted block
reachesF6EF; it is not additionally gated by03A0. The [transmission contract](FACTORY_TRANSMISSION_CONTROL.md)
specifies downstream precedence for these states and raw TCC selector bits.

The branch atF68D tests whether **both**039A bits18 are clear before skipping
gear decoding. Individual value bits only contribute when their matching enable
bit is also set. Treat these as mask/value pairs, not a literal commanded gear.
039C/039D/03A2/03A3 retain payload storage without a named direct consumer in
the reviewed owner union. No undocumented command is assigned to those bytes.

## Clear edges, session loss and expiry

F64E first builds status bytes0130/0131 from diagnostic inputs. Its clear/reset
requests are edge latched, not continuously executed:

| Request | Action and edge latch |
|---|---|
|Engine service0391.4|F280 BLM reset,0045.4|
|3B.1 or active engine0391.6|F333 masked engine/common diagnostic clear,0045.7|
|3B.0|F380 masked transmission clear,0045.6|

A low request rearms the corresponding latch. F333 andF380 have different
mask/counter/candidate footprints; see [diagnostic clears](FACTORY_DIAGNOSTICS.md).
The new protocol trace identifies where their request bytes originate; it does
not replace either clear's exact state effects with a generic erase-all action.

If transmission service3B.3 is active and either0042.1 is lost or036A becomes
nonzero, clear0399,010A,0103,0111,0118 and3B.3. For active engine service3B.4,
loss of0042.0 or nonzero036A clears3B.4,038E and0044.2. The engine clear/reset
edges run **before** this final engine cleanup inF64E. The other payload bytes
are retained. Session00 changes its receive-ownership bit immediately, while
controller cleanup occurs when the laterF64E pass is admitted.

F781 supplies two different time mechanisms; their units are **calls toF781**:

* With0042&03 nonzero, increment byte0367. Increment wrap to0, or a new value
  >=C8, expires the session. Expiry zeros selectors038E/0399; clears0042 bits03,
  0045 bitsD0,3B bits43; releases3FFD.2; writes SCCR2=26; and clears0360/0361
  and0362/0363. It does not clear all service flags or payload bytes. A received
  byte resets0367 independently of whether its frame later succeeds.
* When either service flag3B.3/.4 is active, increment word0368. Once it reaches
  unsigned word[51BB], set036A=1. With both flags clear, increment a nonzero036A
  until it reaches word[51BD], then clear both036A and0368. Stock thresholds
  areF4FF andFF00. The words are not milliseconds and the cleanup is not
  synchronous with packet acceptance.

F781 disables interrupts during session-expiry mutation and reenables them
before override-duration handling. It is called at7A14 andAE9D under different
admission paths. A single nominal main-loop period cannot be assigned to every
increment without that scheduler context. Interrupt nesting, a callback changing
state, and factory-mode operation retain their separate boundaries.

## Manufacturing-test admission and recurring loop

At boot7193..71B4, require raw082F in[28,64) hex,00A6>=FC,082D>=FC and00A5<=05.
The082F window sets0050.3 before the remaining tests. Full admission sets0044.0,
clears0001, writes3FFC=B93A and jumps7459, bypassing the normal controller
initialization that follows71C3. The serial RAM clear at717F..7188 covers
0360..03FE;03FF is not included. Do not describe it as an inclusive03FF clear.
CB15's normal-mode refresh only retains0050.3 in that window when factory0044.0
is set. The initial test window and actual opcodes take precedence over voltage
conversions inherited from comments.

TOC3 entry793D advances its compare and clears its flag, sets0000.0, then tests
0044.0. Factory mode increments0002 and jumpsFA5B before normal busy/stack/main
scheduling. FA5B resets SP=03FF rather than returning from the interrupted frame.
It rechecks ADC channel1 in[28,64) and channel3>1A usingF275/F25F. Failure
executes SWI atFA82, whose handlerFC04 sets0000.3 and loopsFC07. In particular,
FA72 actual bytes `81 28` establish the lower bound40 decimal; HAC's operand40
hex would incorrectly collapse the admitted range.

After successful qualification, CLI permits serial/timer activity, andFA84
writesAA then55 to COP register303A. Processing then depends on last accepted
factory ID0364. With no pending action the code ends in the FBD4 self-loop;
the next timer interrupt abandons that loop through a freshFA5B/SP reset.
It is neither a normal scheduler slot nor a returning service subroutine.

## Factory descriptors and payload-supplied actions

When0050.3 is set, RX searchesFBD7→FBE0→FBE9→0. These are actual word links,
despite several inherited FCB declarations suggesting byte data.

| ID / descriptor | Reply | Accepted payload and next factory-loop action |
|---|---|---|
|01 /FBD7|N=0 acknowledgement|Copy RX N bytes036C→038E. At next factory loop, clear0001.0; read destination word038E; copy exactly32 bytes0390..03AF to incrementing destination; complement0364 toFE so the next loop will not repeat the upload.|
|02 /FBE0|N=0 acknowledgement|Copy RX N bytes036C→038E. At next loop set0001.0 and call the full word[038E] atFAA5. ID02 remains02, so subsequent loops repeat the call while it returns and ID is unchanged.|
|03 /FBE9|N=24 raw buffer reply|Copy RX N bytes036C→038E. Call word[038E] only if0001.0 was already set. Otherwise take the disabled-output route. Reply bytes come from036C..0383, not a dedicated result snapshot.|

There is **no ROM whitelist of legal callback destinations**, no page-byte/table
composition atFAA5, and no local target-range or alignment check. X is loaded
from both bytes038E/038F then `JSR 0,X` calls it. A supplied address could name
resident code, RAM code or an external mapping. This closes how the pointer is
produced and dispatched; it cannot close what arbitrary supplied code does.
Likewise, upload has no local destination-range check and still copies32 bytes
after a short payload, using retained source bytes. An accepted03 can replace
an earlier armed callback address. ID01/02/03 are not ordinary ALDL command
values01/02/03; their descriptor list and admission mode are different.

The upload destination is sampled once into X atFAB0. Source bytes are read
one at a time atFAB9, so a forward overlap can change later source reads.
The32-byte footprint assumes the loop completes; a fresh factory timer entry
can abandon it throughFA5B's SP reset. It is not an atomic32-byte transaction.

F3E4 toggles port3066.7 using A, preserving B's factory ID. ID02 branches to
the callback before that heartbeat call. All callback continuations are
conditional on a return; code that changes SP, disables interrupts, or does
not return is outside the resident callback body's effects. Factory-test serial
does not call the ordinaryF781/F64E expiry machinery as part of this loop.

## Factory output cycling and terminal patterns

With ID zero and3064.7 set, FAD9..FB38 enables the cycling route. It writes
3FCC=DFFF,3FEA=DFFF,3FCE=00C5,3FDC=0042 and3FF6=FFEC, preserving the intervening
RTS delay calls. The descriptions "3ms" and "1ms" in HAC are physical scale
interpretations, not additional ROM-derived timing proofs.

Clamp phase0002 to0 if above4F. On phases divisible by16, update3062 bits0C
by the literal branch/toggle sequence, preserve its other bits and set bits30.
Then choose row `FBF2+3*(phase>>4)`, with indices0..4:

| Index | OR into3060 after &6F | OR into3062 after &FC | OR into3FFD after &F7 |
|---|---|---|---|
|0|10|20|00|
|1|10|21|08|
|2|10|22|08|
|3|00|20|08|
|4|90|20|08|
|Disabled/default rowFC01|10|00|08|

Only a cycle boundary reaches this row publication; an intervening cycle pass
goes directly to the wait loop. A nonzero unhandled ID, or low3064.7, takes the
disabled/default route:3062&=E3 and3FCE=0 before publishingFC01. This does not
zero every hardware output.

Common row publication merges3060/3062, then underSEI merges the low3FFD byte
through word3FFC and reenables interrupts. With rowFC01 it writesD000 to
3FD4/3FD6/3FD8/3FDA and306A/306C/306E/3068, then waits. For a cycling row it
writes3FD4=D399,3FD6=D366,3FD8=D332,3FDA=D2FF,306A=7FB3,306C=7FA6,
306E=7F66,3068=0D73; starts an ID02 acknowledgement using descriptorFBE0;
then waits. `factory_test_output_rows.csv` preserves all six literal row triples.

## Resident closure and external boundaries

The protocol and lifetime derivation closes the previously named serial/service
software owners of fuel, spark, IAC, diagnostics, transmission and emissions.
External1800..1815 hook implementations, arbitrary callback/upload effects,
physical outputs/ADC thresholds and all interrupt interleavings are not inferred
from these bytes. The [whole-program structure audit](FACTORY_GLOBAL_STRUCTURE_AUDIT.md)
keeps those distinct from statically traceable resident control paths.
