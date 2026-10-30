# Factory SCI and ALDL protocol from BMHM ROM bytes

This contract follows the resident receiver, transmitter and descriptor tables,
including ordinary addressed service and the separate factory-test protocol.
The [closure ledger](FACTORY_SERIAL_SERVICE_CLOSURE.md) identifies the ROM and
reproducible evidence. [Service and factory test](FACTORY_SERVICE_AND_TEST.md)
continues from accepted packets to control-state changes and factory execution.
All addresses are CPU addresses; full-image offsets match addresses at 4000..FFFF.

## Registers, initialization and interrupt arbitration

Boot7103..7108 relocates the CPU registers to3000. CC7C initializes SCCR1 at302C
to0 and BAUD302B to04. Boot714D..7154 reads SCSR/SCDR and writes SCCR2=26.
The SCI vector atFFD6 containsF7EA. The ISR's priority is literal:

| SCCR2/status tests | Action |
|---|---|
| SCCR2.5 set | If SCSR.5 set, call receiverF90B; otherwise return, without testing TX |
| SCCR2.5 clear, SCCR2.7 set | If SCSR.7 set, call transmitterF822; otherwise return |
| Neither above, SCCR2.6 set | If SCSR.6 set, write SCCR2=26, release driver and clear3B.6 |
| No eligible event | RTI atF821 |

The exact control values used are26 for receive/wakeup,24 for active receive,
88 for transmit, and40 while waiting for final transmit completion. These are
register values proven from bytes, not a measurement of the electrical bus.
Starting TX atFA28 writes the first ID byte and initializes its checksum/count,
then sets **low byte3FFD bit2** through a16-bit read/modify/write of3FFC and
enables88. F637 uses the same driver bit for optional broadcast. F807..F81E
releases it after the final completion event. High byte3FFC.2 belongs to the
different asynchronous-fuel trigger. See the [handshake](../contracts/ALDL_SCI_HANDSHAKE.md).

## Frame arithmetic and shared state

Normal wire format is `ID, 55+N, payload[0..N-1], checksum`, with byte arithmetic.
The checksum makes the sum of **all** frame bytes zero modulo256. N counts the
whole payload, including an ordinary service command byte. It excludes ID,
biased length and checksum. A reply with N=64 therefore has67 wire bytes.

| State | Role |
|---|---|
|0360|Number of already processed RX/TX bytes;0 starts an ID|
|0361|Running checksum, shared by RX and TX|
|0362/0363|Current descriptor word, shared by RX and TX|
|0364|Last successfully received descriptor's ID|
|0365|RX payload N, then TX payload length|
|0366 and3B.7|Saved low byte and pending-companion flag during TX|
|0367|Receive-idle age; every receiver entry clears it, even an erroneous byte|
|036C..038D|Shared32+2-byte receive area at the accepted maximum N=34|

There is no independent receive queue, atomic commit buffer or saved reply
snapshot. The same RAM and descriptor state are reused through the exchange.
The parser itself has no minimum-N check and no per-command exact-length check.

## Receive state machine, F90B..FA5A

1. Read302E then302F, load current0362 and clear0367. Status bits0E reject the
   byte before checksum addition. Otherwise add it to0361 modulo256.
2. At count0, find an ID by following descriptor link words. Start at51BF
   normally, orFBD7 when0050.3 is set. Match descriptor+2; a zero next link
   without a match aborts. MatchingF4/F5 immediately sets0042.0/.1, respectively,
   **before length/checksum validation**. Save the descriptor and write SCCR2=24.
3. At count1, subtract55. Borrow or result>22 hex aborts. Store N in0365.
4. At count>=2, let `j=count-2`. If j<N this is payload. Ordinary F4/F5 sessions
   use the first byte as a command: values>0A or a null command pointer abort.
   Replace0362 with that command's descriptor. For all modes, store the byte
   at `word[descriptor+7]+j` using F9AE. With no ordinary-session bits set,
   factory packets use their original descriptor and have no command-table step.
5. For ordinary command01's second payload byte, F984..F9A8 selects a page.
   The incoming selector0..2 chooses a word at `initial_descriptor-6+2*selector`;
   values>=3 become0. The selector is still stored at payload offset1.
6. At j>=N, require0361==0. Only now save descriptor ID to0364 and run the
   accepted-payload actions described in the companion contract. There is no
   independent equality test distinguishing an extra byte from a checksum once
   the count reaches N; the byte at that point is the checksum candidate.
7. Descriptor+4 bit7 suppresses a reply. Otherwise enterFA28 using that descriptor.

An abortFA4D zeros0360/0361 and0362/0363, and writes SCCR2=26. It does **not**
undo receive-buffer stores, clear the earlier F4/F5 session bits, erase service
payloads, reset every serial flag, or change0364. An interrupted/short/rejected
frame must not be modeled as an atomic no-op. A checksum-valid N=0 packet can
reach acceptance using retained036C; the root descriptor's80 length marker
normally suppresses its reply. No conventional command-length rule is invented
to hide this literal edge case.

## Descriptor format and accepted commands

Each descriptor starts with nine bytes: next-link word, ID byte, format byte,
reply-length byte, TX-base word, RX-base word. Root descriptors then have11
command pointer words at+9. Format80 selects embedded live-pointer entries;
40 selects addresses supplied in the RX/TX buffer; neither selects raw bytes
at TX-base. Descriptor+4 bit7 is the distinct no-reply test atFA24.

| Command | F4 descriptor | F5 descriptor | Ordinary reply/action |
|---|---|---|---|
|00|51E0|53C9|One-byte command echo; clear this device's session bit|
|01|51EF|53D8|Live data page; selector byte chooses0..2|
|02|5384|5567|N=65 reply: command plus64 memory-output slots, starting at received address word|
|03|538D|5570|Command plus individual received-address reads; response length derives from RX N|
|04|5396|5579|Copy at most11 bytes to the device service block; one-byte echo|
|05..09|0000|0000|Rejected by null command word|
|0A|539F|5582|Set the device's diagnostic-clear request; one-byte echo|

Both linked root entries are inspected in ID order:51BF(F4),53A8(F5), then
53C9(F5 terminal acknowledgement descriptor). The firstF5 match is53A8;
the repeated ID at53C9 does not supersede it. Unknown IDs are rejected.

For command01, engine selectors point to51EF,5276,52FD; all have reply N=64
and the same63 pointer entries. Transmission selectors point to53D8(N=66),
5463(N=57),54DC(N=67), containing65,56,66 entries. These lengths include the
echoed command; they are not counts of data-only pointer entries. The generated
`factory_serial_live_pointers.csv` distinguishes the data ordinal from payload
ordinal and records word-companion slots. The six pages contain376 entries.

## Transmit state machine, F822..F90A

At TX start0360=1 and0361=the ID already written. At count1 emit the biased
reply length. At count2, ordinary addressed mode emits038E (F4) or0399 (F5)
as its command echo. For later count n, set `b=n-2`. When b equals0365 emit
the negative checksum; when b>0365 finish the message. Finishing clears3B.7,
the count/checksum/descriptor words, reads302E/302F and writes SCCR2=40.
Driver release waits for the subsequent completion ISR; it is not done at the
checksum write itself. Counter arithmetic is byte arithmetic.

For command03, reply length is formed by decrementing RX N, arithmetic shifting
right and incrementing. For valid positive N<=34 this is `ceil(N/2)`; N=0
produces0. A complete request of command plus k address words therefore gets
command plus k output bytes. The routine reads live addresses; no validity,
ROM/RAM-region whitelist or per-address alignment check is present.

If a companion byte is pending, emit0366 and clear3B.7 before inspecting any
new pointer. Otherwise resolve the current source:

| Format | Source selection |
|---|---|
|00|`word[descriptor+5]+b`; addressed command echo was handled earlier|
|80|Embedded word at `descriptor+9+2*(b-1)` in an addressed session; use b directly for a broadcast|
|40, command02|Address word at TX-base+1, then add `b-1` for a contiguous read|
|40, command03|Address word at TX-base+1+2*(b-1)|
|40, command04|Same individual-address rule, with an additional10-byte offset|

The command04 address-read branch is present in code but the stock04
descriptors use format00 and length1, so their ordinary replies do not enter it.
This separates a generic supported branch from an actually selected stock format.

For a selected address outside1000..3FFF, F8DC reads one byte. Inside that range,
normal mode transforms the high address byte withCF (`address & CFFF`), then
F8CA reads a word: emit its high byte now and save its low byte for the next wire
slot. Factory0050.3 inhibits the address transformation, but still uses the
word/companion behavior. Thus normal encoded31F0 means a word from01F0;
encoded30FD means00FD. The following pointer-table entry is skipped while its
wire slot carries the saved low byte. A word at the final data slot can leave
its companion unused when checksum selection takes precedence.

The live pages are not atomic snapshots. Each new item is read when sent;
two bytes of a word item share one LDD, while unrelated items are acquired on
different TX events. The existing [serialization timing contract](../contracts/ALDL_SERIALIZATION_TIMING_CONTRACT.md)
provides the field-skew consequence. The parser and TX paths do not by themselves
prove physical baud rate, bus ownership under collisions, or peripheral read
side effects at arbitrary requested addresses.

## Optional polling/broadcast, F5E8..F64D

Return immediately when0042&03 is nonzero. Otherwise take an **unscaled byte
offset** `phase0002&1F` into518F and load a word; zero exits. The offset is not
multiplied by2, so a changed calibration could select overlapping words.
All33 bytes needed for these32 overlapping word reads are zero in stock BMHM.
Consequently this broadcast branch has no selected message in this image.

For a nonzero descriptor and nonzero ID, an existing3B.6 sets3B.5 and exits.
Otherwise set3B.6, save0362, send the ID, and save reply length0365. When length
is nonzero and format&C0 is zero, copy that many bytes from the descriptor's
embedded source pointers at+9 into TX-base before starting interrupt TX.
This optional format is a pre-copy, unlike live-pointer format80. Then set
count1, assert3FFD.2 and write SCCR2=88. Recalibrated activation is not inferred
from stock-zero schedule bytes. The nearby unused record at51AF is preserved
as configuration data, not mistaken for reachable broadcast activity.

## Limits and evidence navigation

The descriptor and mode rules close the resident serial software. Runtime
addresses, factory callbacks, external1800 hooks, electrical behavior and
interrupt interleavings retain their stated interfaces. The byte evidence
records actual opcodes, not reconstructed bytes from inherited comments.
The original HAC is unchanged. Local differences includeFA72: actual bytes
`81 28` mean `CMPA #$28`, not the listing's `CMPA #$40`.
