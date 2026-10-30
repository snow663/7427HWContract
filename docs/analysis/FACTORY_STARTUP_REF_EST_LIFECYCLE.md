# Factory reset, REF admission and EST state lifetimes

This joins the factory startup, reference IRQ, spark calculation, EST monitors,
software ignition-off handling and board-output publication into one state
sequence. Authority is stock BMHM, SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
CPU4000..FFFF equals full-image offsets. Runtime RAM and peripheral responses
are separate inputs; low-address file padding supplies neither.

The resident instructions and stock constants establish the transitions below.
The new [bounded execution checks](../../tests/test_factory_startup_est.py)
execute the existing CPU with committed mapped-ROM evidence. They include real
REF interrupt entry/RTI and complete A4EC..ACA6 calculations for selected inputs.
They do not model the proprietary ASIC or prove every interrupt schedule.

## The states are independent

| State | Producer and lifetime |
|---|---|
|0050.5 pending REF|7513 sets when0044.4 is clear; A4F0 consumes. One bit, with no pulse count or queued timestamps.|
|0050.2 fresh calculation|A4F3 sets on consuming a pending REF; ACA3 clears on calculation/alternate exits. REF itself does not set this bit.|
|0044.3 first-reference/qualification stage|A544 sets on the first consumed REF while spark-running is clear. Acceptance AC25, missing-REF A5C9 and software ignition-on7D9A clear it.|
|004F.4 fuel-running|A581/A593 qualifies independently with counter0211 and period threshold4135.|
|004F.7 spark-running|A551..A57C qualifies with counter0210 and period threshold4133; sets0004.3 and resets startup gain01F2.|
|0044.6 first acceptable EST sample|ABF9 sets; a bad sample AC0A clears. Successful qualification does not explicitly clear it.|
|004F.6 EST qualified|AC1C sets. Normal software ignition-off and missing-REF cleanup preserve it. Unconditional boot RAM clear resets it.|
|0044.7 initial EST lock|AC13 sets after enough bad checks; diagnostic clear F357 and boot clear can reset it.|
|0004.7 later EST event|E038 sets after repeated unchanged samples in the later monitor. Software ignition-off7D57, diagnostic clear F354 and applicable boot clear reset it.|
|004B.4 output request|AC31 sets, ACA0 clears; F400..F40D publishes it to3060.4 while rebuilding the shadow. Physical pin identity is still unmeasured.|

The global bit-writer inventory supplies the direct and qualified indexed
co-writers, including boot clear and foreground self-copy. Supplied factory
callbacks/uploads and absent extension code retain their existing unrestricted
interfaces; these lifetimes describe the ordinary resident paths.

## Reset and the first admitted references

7156..7162 writes zero words through3FC0..3FF8. Boot7164..717C unconditionally
clears0036..00FF,0100..029C and0800..08FF. Thus the flags and local counters
above begin clear even if separate retained diagnostic memory validates.
741F/7422 seeds baseline0205 from a sample of3FCA before ordinary scheduling.

REF vectorFFF2 points to74EA. In ordinary mode the IRQ schedules3016, toggles
3062.6, conditionally sets0050.5, writes306F=FF and follows its fuel/event path.
The relevant IRQ prefix is admitted with0044.0 clear. Ignition-off0044.4
suppresses the0050.5 set. The IRQ does not itself declare spark or fuel running.

A4EC tests0050.5. When present, A4F0 clears it, A4F3 sets0050.2, clears word0260,
updates the adaptive term and clears missing-reference counter0202. Thereafter:

1. With spark-running clear and0044.3 clear, set0044.3 and takeAC51. This first
   consumed REF does not increment either run-qualification counter.
2. With0044.3 already set, call fuel qualifier A581 unless004F.4 is already set,
   then independently test spark qualification.
3. Fuel increments byte0211 only for period3FC0 below stock4135=`0CCC`.
   Spark increments byte0210 only for period below stock4133=`0888`.
   A failing period resets the respective counter. Both stock count thresholds
   4143/4142 equal2, but these are two separate counters and period reads.
4. Qualifying spark sets004F.7 and admits the normal conversion and command
   path. Fuel can qualify while spark is still below its own qualification.
   With period0900, for example, two subsequent consumed REF admissions can
   set fuel-running while spark-running remains clear.

The counters count consumed/admitted observations, not a guaranteed count of
individual physical REF pulses. Several IRQs can set an already-set pending bit.
Separate period samples at A581 and A551 also need not be a coherent pair on
hardware.

## Initial EST qualification accepts equal samples in stock BMHM

ABCB follows the integer spark writes. Its first gate is0044.3; the second is
fresh0050.2. With both set, read3FCA into D/X. Stock5B03=`BC` enables its bit5
test. With004F.6 still clear and0044.7 clear, form:

`delta = u16(sample3FCA - old0205)`

The acceptable window is high(delta)=0 and low(delta)<=C[4E71]. **Stock4E71=0:
the accepted delta is exactly zero.** A wrappedFFFF→0000 change has delta1
and fails this check. Equality does not prove the register remained constant
between reads or exclude a complete counter wrap. This initial stage does not
establish reference-pulse activity or a physical electrical handshake.

The first acceptable sample sets0044.6 and saves0205. A second consecutive
acceptable sample entersAC1C: set004F.6, clear022C, save0205, clear0044.3,
read3FEC and copy that word to3FE4 throughAC28..AC2E. The next ordinary tail
sets004B.4, subject to its fault/service gates.

A bad sample with old022C<=stock4E72(4) increments the byte, clears0044.6 and
saves0205. A good first sample does not clear this bad counter. If another bad
sample finds old022C>4, set0044.7 and live0019.5(code42), without saving the
current baseline. Thus with a zero initial count, the sixth bad check locks;
the good-pair requirement and bad-count history have different lifetimes.

With the mask disabled, AC1C accepts immediately. With004F.6 already set,
ABE2 branches directly toAC25, before the lock/delta checks: clear0044.3 and
copy3FEC→3FE4, but skipAC1C's counter clear and0205 save. With0044.3 clear,
the usual ABCB call goes straight toAC31 and performs no such copy.

### A connected execution example

The test fixture supplies period3FC0=0700, initial and subsequent3FCA=1234,
baseline0205=1234 and3FEC=BEEF. All executable/calibration bytes are stock.
Other fixture RAM starts zero. Each row executes a complete REF IRQ followed
by A4EC..ACA6, including its actual helper calls and normal spark path.

| Consumed REF admission |0044|004F|0210 /0211|004B.4|3FE4|Meaning|
|---|---|---|---|---|---|---|
|1|08|00|0 /0|0|0000|Establish first-reference stage; alternate RPM path|
|2|08|00|1 /1|0|0000|Both run qualifiers have one accepted observation|
|3|48|90|0 /0|0|0000|Fuel and spark running; first equal EST sample|
|4|40|D0|0 /0|1|BEEF|Second equal sample qualifies EST and copies feedback|

This is a reproducible chosen-input execution, not a universal four-pulse
startup promise. The third row's first acceptable check returns before the
board-request tail. Once004F.6 is set, a later new-reference path can start
updating startup gain01F2 when0051.6 is clear; the accepting pass itself reached
that gain gate earlier, while004F.6 was still clear.

## The later monitor reverses the activity expectation

E00D is a separate diagnostic-stage owner. It requires0044.2 clear,0050.3
clear, phase0002.4 clear and004F.6 set. It uses the same0205 baseline and022C
counter as the initial monitor, but now RPM0061>stock4E70(4) with an unchanged
3FCA sample increments022C. A changed sample or low RPM clears022C. Every
admitted sample is saved to0205. Skipped calls preserve both.

With old022C>stock4E73(4), E038 sets0004.7 and preserves that count. Starting
from zero with every gate admitted, five unchanged high-RPM observations build
count5 and the sixth sets the event. It does not itself set live code42.
ABCB's tail AC34..AC3F consumes0004.7: unless0044.2 is set, set live0019.5 and
clear004B.4. Service003B.4 plus0391.3 can also set0044.2 and clear the request.
An isolated later changed sample resets the counter but does not clear the
already set0004.7 latch.

The equal samples accepted during initial qualification are therefore
compatible with later equal samples being a fault: the later test
starts only after qualification and has additional RPM/mode gates. Register
3FCA's physical event source remains to be measured.

## Software ignition-off/on is different from restarting the CPU

8613 uses raw batteryA7: below40 sets0044.4 and clears0050.0;40..89 preserves
the state;90 or above clears0044.4, seeding0205 from3FCA if off was previously
set. Calibration400C.0 can then enable0050.0. These counts do not establish volts.

The ignition-off fuel branch7D4B clears run bits004F.7/.4 once027E>=8, together
with0004.7 and live code42. It preserves004F.6,0044.6/.7,0210/0211 and022C.
Its ignition-return branch7D90 clears0044.3 but does not reset those histories.
Consequently a software off/on sequence with the CPU still executing need not
repeat initial two-sample EST qualification; retained004F.6 can takeAC25 directly.
A reset that executes the unconditional boot clears begins a different state.

## Missing-reference path and its exact trap destination

Without0050.5, A59B increments0260 until stock4962=`00F0`; later admitted calls
write306F=0. At0260>=00A0 another branch caps crank-event count02CE, if needed.
Those operations are independent of the short missing-reference counter0202.

While spark-running is set, each no-new-reference calculation increments0202
and can still run the normal conversion. Starting at zero with no intervening
REF, the first23 such admissions finish with counts1..23. The next finds old
0202>=17 hex, clears004F bits90 and0044.3, sets005F=FFFF, clears3060.4 directly,
and executesSWI atA5D7. EST-qualified004F.6 is preserved by that cleanup.

Stock SWI vectorFFF6 containsFC04. FC04 sets0000.3 andFC07 loops indefinitely.
The instruction is **not a direct software restart at7100**. Hardware watchdog
reset/recovery remains separate from this observed software trap; no watchdog
timing is inferred. A pending REF after the A4EC test can also wait for the next
admission while the current no-REF path continues to its old-counter decision.

## Interrupt ordering and physical publication

The ordinary scheduler enables maskable interrupts at7958. There is no local
SEI spanning A4EC's pending-bit test and A4F0's clear. The bounded checks inject
the full stock REF IRQ at three instruction boundaries and verify register,
stack and condition-code restoration through the actualRTI:

| REF IRQ timing | Result in the current calculation |
|---|---|
|After a positive A4EC test, before A4F0|The already pending bit stays set during IRQ; A4F0 then clears it. The two observations coalesce into the current admission.|
|After A4F0, before A4F3|The IRQ sets pending again; the current calculation also sets fresh. Pending remains for a later admission.|
|After A4EC took its no-pending branch|The current path remains the no-pending path; pending remains for a subsequent calculation.|

This establishes selected real instruction interleavings, not arbitrary
preemption coverage or coherent peripheral read semantics. The single-bit
mailbox must not be replaced by an assumed event queue in a reconstruction.

F400 reads3060, masks with6F, then writes `(004B &90)` to3060 atF409 and adds
the saved6F-masked value back into004B atF40D. Thus004B.4 does reach3060.4;
setting the RAM shadow alone does not execute that publication. The whole
F3EE..F41F flush masks I-bit interrupts until its finalCLI. This still does not
identify which physical wire is driven or prove the ASIC readback behavior.

Reproduce the bounded checks with:

```sh
python -m unittest discover -s tests -p 'test_factory_startup_est.py' -v
```

Continue through the [spark arithmetic](FACTORY_SPARK_INTEGER_HANDOFF.md),
[upstream run admission](FACTORY_UPSTREAM_SPARK_CALCULATIONS.md),
[diagnostics](FACTORY_DIAGNOSTICS.md), [scheduler](FACTORY_SCHEDULER_MAP.md),
and [physical interface matrix](FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md).
