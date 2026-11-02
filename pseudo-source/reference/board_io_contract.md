# Resident board service, MAP/VSS inputs and switch housekeeping

Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
Actual bytes supply the C routines below. The old whole-common-I/O and input
housekeeping task IDs remain reserved and unused. Each public routine has its
own source file; the inventory is177 routines:81 implemented outlines,
37 dependency boundaries and59 algorithms.

| Stock scope | C routine | Responsibility |
|---|---|---|
| 7BA7..7C12 | `pcm_common_io` | Board →MAP →VSS →brake admission order |
| F3EE..F3FF, thenF400 | `pcm_board_latch` | Literal SEI, control-word RMW, delay and port tail |
| F400..F41F | `pcm_board_ports` | Ordered output writes, input mirror and literal CLI |
| 7BAA..7BF4 | `pcm_map_input` | Fault/default target, lookup, lag and rounded MAP byte |
| 7BF5..7C0E | `pcm_vss_sample` | Status latch and observed timestamp changes |
| 7D21..7D4A | `pcm_brake_filter` | Inverse brake-input qualification |
| 9167..91A2 | `pcm_input_housekeeping` | COP-AA prefix and AC/P-N input mirrors |

The original HAC labels do not override the recorded bytes. The comparison
scope also executes theF3ED delay RTS and the F49A/F4BD cap/offset lookup.
Those scopes contain141 instruction starts in total.

## Board word and byte ordering

F3EE assigns the IRQ mask true, reads word3FFC, executes the literal extended
JSR/RTS gap, then changes only low-byte bit0008 from0072.7: set with the flag
clear, clear with the flag set. The gap is11 nominal E cycles (JSR6 plusRTS5),
represented by the existing minimum-delay backend. Its callback must retain the
mask. Compiler/call overhead, actual settling and target timing remain separate.
The word held across the delay is written back; intervening callback changes to
the peripheral word are not silently merged into a fresh sample.

F400 then performs this sequence:

1. Read byte3060 and retain only6F in the local input sample.
2. Sample the existing004B.4 spark request and004B.7 IAC request; write only
   those90 bits to3060.
3. Reconstruct RAM004B from the latched output bits plus the earlier input6F.
4. Sample004C and write it to3062.
5. Read3064 and commit that returned sample to004D.
6. Sample004E and write it to3067, then assign the mask false (literal CLI).

The3060 peripheral write and RAM004B reconstruction are different values and
separate operations. The merge uses the local inputs/outputs even if a write
callback changes the RAM requests. Later004C/004E reads remain fresh. Direct
entry atF400 does not add SEI or the word operation. Both entries end with CLI,
even when entered masked; neither restores a saved mask.

All completed prefixes survive a failed backend operation. In particular, a
failed input read does not publish a new004D, while a later failure retains it.
A missing delay binding stops after the control-word read with the mask still
set. Defensive failure returns are source backend contracts, not a claim that
physical SEI/CLI or ROM accesses fail.

## State ownership and status sampling

The new `PcmIo` group owns004B bits6F,004E,0073/74 bitsBFFF, the01C3 MAP word,
0047.0,0041.4,009C.0,00FB and the080C/080D VSS count/timestamp. Existing owners
remain canonical for004B.4/7 (`spark.output_request` /`iac.kicker_request`),
0073.6 (`reference.extra_request`),004C (`transmission.output_shadow`),004D
(`iac.input_shadow`),0052.5 and0041.5 (`iac.ac_request` /`iac.park_neutral`),
01C6 (`spark.map_filtered`) and0072.7 (`runtime.service_output_mirror`).
The new context masks exclude those existing owners; there is no second copy
of the REF request flag or output request bits.

VSS service masks, reads word3FFA and stores0073/74 through those split owners,
then unmasks. The following0400 test uses the latched word, independently of
callback changes to the saved RAM state at CLI. A set bit admits a3FC4 timestamp
read. Compare against the current080D after that read; on inequality increment
080C as a byte and save the returned timestamp. Equality retains both values.

Thus080C counts observed timestamp changes. Polling, wrap, missed edges and
physical VSS scaling remain distinct. A joined witness lets3FFA change after
CLI while the saved0073.6 survives; the existing REF continuation consumes and
clears that same owner. The fixture stops before the actual RTI, with the timer
continuation disabled by its supplied400B.0 profile. Target frames and complete
REF behavior retain their existing separate contracts.

The reset outline now clears the new I/O group. This establishes the outline's
initial state, not completed factory retained/reset seeding or a target RAM ABI.

## MAP and input qualification

Raw082E is the MAP target unless006F&48 requests a substitute. Without fuel
running use4E68. With fuel running, form4*TPS*4E69; either word-shift carry
selects4E68. Otherwise add the product high byte to the F49A lookup. That helper
**caps RPM62>>1 before subtracting fixed16 with a zero floor**, then performs
the rounded lookup. Addition carry or a result greater than4E68 selects4E68.

Select gain4138 with0047.0, otherwise4137. The existing signed-floor byte lag
updates01C3. Store its rounded high byte to01C6 with byte wrapping; FF80 and
above can therefore round to00 rather than an added saturation correction.
The0047 gain-selection producer remains separate work.

Brake service compares004D.1 with inverse009C.0. Agreement clears00FB without
requiring a profile. Disagreement increments while oldFB<5D06; a call finding
oldFB>=limit clears009C.0 and sets it again only for current input bit1 clear.
The count is retained on that update. Disabled/unrelated input bits are not
invented additional qualifications. These are admitted-call counts, not a new
physical millisecond guarantee.

Input housekeeping first writes byteAA to303A. It does not call the complete
AA/55 watchdog helper. With400F.2 clear, input004D.0 becomes both0052.5 and0041.4;
with the feature set both prior flags are retained. Always clear0041.5, then set
it for `(004D&1C)==14` with400F.6 clear, or004D.4 clear with that option set.
The separate00A2 transmission-context owner remains unfinished.

## Profiles, witnesses and remaining work

The new immutable profile covers11 stock bytes. Its native bias descriptor has
five reachable knots; tests supply eight verified ROM knots for expanded cap
profiles. The extra neighboring bytes are fixture backing, not independently
declared new production calibration parameters. Bounds failure precedes the
MAP word/byte stores. A normal raw-MAP route does not read the unused bias view.
Native profile pointers are not a serialized EEPROM format.

The new suite passes803,504 compiled-C/ROM comparisons, exercising all141 scoped
instruction starts. It compares mapped RAM and peripheral state, ordered word/
byte/mask/delay events, final mask and completed local frame balance, and rejects
unexpected non-stack RAM writes. Sweeps cover control words and mirror flags,
all3060 input/shadow byte pairs, MAP word rounding and gains, fallback product
carries, RPM/cap order, all status and unchanged timestamp words, brake count/
limit pairs and every option/input byte pair. Selected callback/prefix witnesses
add7,971 failures and1,024 retained histories.

The full160-phase kernel uses real common-I/O and housekeeping bodies without
their former bindings. It checks160 issued3062 bytes and80 single-AA prefixes.
The busy witness injects three arrivals at the real board CLI after the first
latch write. Four count advances produce only two latch writes,14 then10 hex;
catch-up adds no step. Special fast-group and busy-return paths still bypass
board flush. Target peripheral response and physical motor edges are not inferred.
Both host routes now have38 CTest entries and six kernel contract groups.

Next connect MAP transient-gain selection and the raw/filtered VSS producers.
Upstream acquisition, other scheduled controllers, optional modules, target
reset/interrupt entry, ABI/RAM/linker/stack fit and actual peripheral/board/timing
validation remain separate work. This port supplies source behavior and backend
transactions; it does not emit a flashable target BIN.
