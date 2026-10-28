# Factory external-code and physical-hardware boundaries

This contract completes the resident side of the remaining interfaces: where
the ROM enters external code, what it supplies or consumes afterward, which
addresses it reads/writes, and what evidence is still needed to establish the
external response. It records no new bench result and assigns no effects to
missing code. ROM identity and scope are in the [ownership closure](FACTORY_OWNERSHIP_CLOSURE.md).

## Eight extension entries and the independent connection check

| Call PC → address | Resident admission and position | Resident continuation / unprovided effect |
|---|---|---|
|8C6A→1800 |0086.6; after normal AFR selection, bypassed by admitted AFR service override | Result024A is published to024B; supplied code may change other state/registers |
|93D4→1803 |0086.6; first operation of main IAC controller | Normal IAC/service work follows only if the hook returns; no save-all ABI is assumed |
|F5D3→1806 |0086.6 in slot3 background wrapper | F5D6 storesF7 to0F00 afterward; the hardware meaning of that address is not established by a store |
|8EDF→1809 | Governor's local option/running/fault gates, then0086.6 | Returned carry set goes directly to the0299 store with returnedA, bypassing local target math |
|F5E4→180C | Runtimeword[1800]==7E18; checked in slot7 | **No0086.6 guard**; could establish the enable/state, but body absent |
|AB66→180F |0086.6, between local spark factor formation and final conversion | Later resident math uses returned registers/state; stock no-hook equation does not constrain the extension |
|A9E4→1812 |0086.6, after composite spark modifiers and before later resident override/limits | Documented downstream override still follows a normal return |
|D029→1815 |0086.6, after desired EGR01AE store | Local EGR service override can replace01AE afterward |

The addresses are spaced three bytes apart, consistent with possible JMP stubs.
That shape does not supply their implementation or calling convention. The
connection test reads exactly two bytes7E18, not the complete target of a
three-byte JMP, a module checksum, or a register-preservation declaration.

The normal ROM never sets0086.6, but F5DC can call180C while it is clear.
Accordingly, all eight hooks remain universal register/memory effect boundaries
unless their actual implementation is supplied. BIN low-addressFF padding is
not a dump of runtime1800..1817. A returning hook, its optional code upload,
and the normal resident path must be kept as distinct operating contexts.

## Factory supplied code and addresses

FAA5 loads the full word038E/038F into X and calls0,X. Accepted factoryID02
arms0001.0 and repeats it on later factory loops;ID03 can replace the pointer
and invoke it while already armed. ID01 clears the latch and copies32 bytes
from0390 to u16(word sampled atFAB0[038E]+j), with no destination restriction. The upload
can wrapFFFF→0000 at the CPU-address level; whether a particular destination
accepts a write is a hardware property.

X retains that sampled destination while each source byte is read separately.
Forward overlap can change future source bytes, and a fresh factory timer entry
can abandon the active copy through its SP reset.32 bytes is the normal complete
loop footprint, not an atomic transaction promised across arbitrary interrupts.

The receive/copy/latch/loop lifetimes are closed in
[FACTORY_SERVICE_AND_TEST.md](FACTORY_SERVICE_AND_TEST.md). An arbitrary callback
can change SP, flags, interrupt masks, RAM, devices or control flow and need
not return. There is no resident legal-function whitelist to reconstruct.
Ordinary memory-request commands likewise permit arbitrary read addresses;
device read side effects belong to the addressed hardware.

FF90/FF93/FF96 are actual three-byte jumps9899/A3FA/F326. The rooted graph
and new scan find no direct resident entry reference. Their intended factory
or external ABI remains an inference. The tail's helper/data words and the
unusedF564 multiply helper are byte-documented, but no unseen external caller
is fabricated. Required next evidence is an actual supplied caller/module or
a recorded runtime entry with its registers/stack, not another interpretation
of the same tail bytes.

## CPU register identities versus board wiring

The ROM relocates registers with INIT=03 and programs the F1-style extra
chip-select registers at offsets5C..5F. The [NXP MC68HC11F1 data sheet](https://www.nxp.com/docs/en/data-sheet/MC68HC11F1.pdf),
register table4-1 (PDF pages43–44), initialization, chip-select and timer
sections distinguish standard register identities from proprietary board I/O.
This is a match to the F1-style register layout; it does not establish the
package marking or every pin's connection on this PCM.

Several labels in the earlier generated hardware contract need this correction:

| CPU address after relocation | Documented F1-layout register | Earlier provisional label |
|---|---|---|
|3001 | DDRA | PIOC |
|3002 | PORTG | PORTC |
|3003 | DDRG | PORTB |
|3008 | PORTD | PORTE / ADC input port |
|3009 | DDRD | CFORC candidate |
|300B | CFORC | CFORC, already consistent |
|300C | OC1M, output-compare1 mask | OC1D candidate |
|300D | OC1D, output-compare1 data | TCNT-high candidate |
|300E/300F | TCNT | TCNT, already consistent |
|303C | HPRIO | Unnamed indexed register |
|305C | CSSTRH, clock stretching | Unknown external board register |
|305D | CSCTL, chip-select control | Unknown external board register |
|305E | CSGADR, general chip-select address | Unknown external board register |
|305F | CSGSIZ, general chip-select size | Unknown external board register |

ROM CC7C..CCC0 writes305C=00,305D=AC,305E=00,305F=CB. These values support
the layout match; they are not measurements of external decoding, wait states
actually imposed by this board, or a memory-chip identity. INIT's selected
register page puts these CPU registers at3000..305F.3060 and above remain
separate board/ASIC address questions. The old partial-overlay table and
simulator profile are historical artifacts; this documentation does not change
device simulation, the running tune, or driver code.

## Software evidence and the remaining physical questions

`factory_global_hardware_accesses.csv` enumerates131 concrete hardware byte
addresses from direct and qualified indexed accesses. Word operations retain
both byte addresses. Runtime serial reads, arbitrary upload/callback targets,
and opaque hooks are additional wildcard effects, not absent hardware owners.

| Interface | Resident side established | Physical evidence still absent / decisive observation |
|---|---|---|
| Clock / timer / IRQ | Register setup, compare increments, masks, flag writes, vectors, pending/overrun software | Actual oscillator/E-clock, interrupt latency, missed/level-triggered events and externally induced resets; correlate E/REF/IRQ and compare outputs on a common capture |
| Timer flags3023/3025 | Which masks/values are written and which handlers consume them | CPU-defined write-one-clear behavior comes from the data sheet; board capture polarity and event timing still need pin/register correlation |
| REF/ASIC3FC0/3FCA and capture inputs | Every documented sample, conversion gate, first-event/timeout/reset path | Counter latch/read coherency, physical divider/event meaning and rollover timing; capture known REF pulses and synchronized reads |
| Synchronous fuel3FCE | Exact integer value, mode/cut path, startup and factory co-writers | Tick-to-pulse transfer, bank/phase gating, zero/max/clamp response and real injector driver delay; correlate command writes, REF and both bank outputs |
| Async fuel3FF2/3FFC.2 | Packet route, trigger sequence and distinct high-byte control bit | Latch/edge/queue semantics and pulse scheduling relative toREF; capture command/control/write order against output edges |
| Spark3FE8/3FE6/3FDC/3FF6 | Integer handoff, stack/rolling state and initialization | ASIC counter meaning, dwell/EST edge interpretation and physical angle; captureREF, bypass/EST and command words across first event/rollover |
| EST monitor3FEC→3FE4 | Resident sample/copy and fault conditions | Meaning of feedback bits/word and bypass response; correlate state reads withEST/bypass edges |
| IAC004C→3062 | Target, software count, phase/direction logic, shadow merge and flush order | Coil A/B polarity, enable behavior, direction, actual travel/homing/backlash; observecoil signals and measured movement for issued phases |
| PWM/current3068/306A/306C/306E and3FD4..3FDA | Normal and service/factory selector precedence, words written | Carrier/timebase, polarity, current/pressure and actuator response; measure pin waveform/current while recording actual write values |
| Shared latch3FFC/3FFD | High/low byte ownership, RMW sequence, serial low-byte bit2 versus async high-byte bit2 | Electrical inversion, latch/read side effects and independent-bit behavior; correlatebus writes and individual output pins |
| ADC3030..3034 / PORTD mux | Channel selection, poll/timeout, sample averaging and raw state destinations | Multiplexer wiring, impedance/reference, calibration to volts/pressure/temperature and acquisition settling; apply known electrical inputs and recordraw values |
| SCI302B..302F / external driver | Framing/checksum, IRQ arbitration, sessions and transmit-enable sequence | Actual baud/edge levels, driver polarity, collision behavior and read/status clearing timing; correlate TX/RX/enable with frames |
| Knock3FC8 and related inputs | Count deltas, RPM gains/decay, fault gates and retard/learning math | Knock interface transfer, physical count generation and sensor response; use a characterized input with simultaneous count/retard capture |
| Reset/STOP/watchdog | COP writes, stop/trap branches, reset-vector and stack recovery code | External power/reset monitor, watchdog timing and which reset cause retains RAM; recordpower/reset plus retained state and cause byte |

This is a requirements/evidence matrix, not a claim that those observations
have been performed. Existing bench status and driver-preservation decisions
remain in [HARDWARE_OUTPUT_GATE_MATRIX.md](../contracts/HARDWARE_OUTPUT_GATE_MATRIX.md).
No software-completion claim converts a physical test markednot_run into a pass.

## Interrupt and shared-output interpretation

ROM ordering specifies when the CPU samples/tests/stores. CPU semantics are
separately documented by the [NXP HC11 reference manual](https://www.nxp.com/docs/en/reference-manual/M68HC11RM.pdf).
SEI protects I-bit-maskable interrupt regions; it does not exclude reset or
all external activity. A16-bit CPU instruction does not prove a proprietary
peripheral latches both bus bytes coherently. A RAM shadow update does not
prove a physical output changed, and a serial page is not an atomic snapshot.

The byte graph follows both sides of branches and conditional call returns.
It has no missing resident direct-control destination, but is not a proof of
every feasible interrupt interleaving or maximum stack depth. Documentation
therefore closes the known resident transfer and explicitly grades the source
of any remaining uncertainty: supplied bytes/caller ABI, CPU/device semantics,
or an electrical/mechanical observation.
