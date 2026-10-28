# Factory global indexed-address contracts

This completes an address-provenance contract for each of the **951 unique
explicit indexed-memory instruction sites** in the vector-rooted ROM graph.
It extends the earlier scheduler-only study without replacing its historical
262-row denominator or equating an address formula with a fixed RAM address.
The [closure ledger](FACTORY_OWNERSHIP_CLOSURE.md) defines the remaining limits.

Authority is the complete stock BMHM image, SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
CPU4000..FFFF equals full-file offsets. BIN padding below4000 supplies no
runtime RAM, external code, hardware input, or saved stack contents.

## What the new inventory proves

`factory_global_alias_sites.csv` has exactly one row per rooted indexed PC,
including actual opcode bytes, access width, its qualified effective-address
expression, concrete byte overlaps where justified, and the proof's conditions.
`factory_global_alias_contexts.csv` separately preserves the finite abstract
analysis under253 procedure entries:1,071 local indexed-context rows.
The657 call-binding rows retain incoming X/Y/D for individual direct/indirect
calls. Conditional returns, generic entry registers, and opaque calls remain
explicit. Instruction counts are structural inventory, not execution coverage.

| Site representation | Sites | Interpretation |
|---|---:|---|
| Finite context union | 555 | Physical addresses derived in the represented generic procedure contexts |
| Reviewed conditional footprint | 176 | Loop, table, state-invariant or all-caller contract supplies byte overlaps |
| Local frame | 90 | Saved stack data; no invented absolute RAM variable |
| Caller parameter | 59 | Explicit incoming-register address expression; instantiate at each call |
| Address formula | 61 | Dynamic descriptor/table/curve provenance retained as an expression |
| Runtime pointer | 3 | Serial word/byte readsF8CA/F8DC, unrestricted uploadFABC |
| Stock-pruned optional broadcast | 7 | Zero stock schedule prevents the generic copy path |
| Total | 951 | Same unique-PC denominator as the global structure audit |

The finite analysis alone leaves214 unique sites unknown.249 site contracts
supplement it:225 reviewed formulas/footprints, plus24 all-caller helper
bindings. These include the214 unknowns, the seven stock-pruned broadcast
sites, a stock-pruned spark branch and caller signatures. The review does not
change the abstract analyzer's original results to make them appear resolved.

The formulas preserve unsigned indexed displacement, byte wrapping before an
index is added, word byte order, and both bytes of a word access. They are not
an assertion that every Cartesian combination of a finite set is reachable.
RAM terms mean values sampled at the identified producer/load, not a coherent
global snapshot or a fresh reread after every later instruction.
For example, D91F uses `base+2+u8(2*gear)+k*stride`: the initial ASLB wraps
as a byte, while each subsequent stride increment advances a16-bit pointer.

## Normal resident state invariants

The finite footprints assume resident initialization and the listed producers,
without arbitrary upload, callback, extension mutation or stack corruption.
The formulas remain usable when a finite-footprint assumption is not accepted.

| State | Resident producer and domain | Consequence |
|---|---|---|
| Gear00D9 | Boot74E7 seeds1; D69C publishes the candidate after E562 range capping, or the local service clampD676..D68C; normal domain0..3 | Keep decrements/ASLB as byte operations; an unsigned FF displacement is not -1 |
| BLM index0247 | 8D2B..8D9B selects retained cells0..20 | 8D7D/8E78/8E9A address02B3..02C7; D31C addresses4058..406C |
| Adaptive bank014A | B99F/B9EE initialize0, loop while below3 | Exactly three17-byte banks02F8..032A |
| Adaptive neighbor014B | BA65 initializes0, accepts j0..4 and neighbors0..16 | BB93/BBEB/BC21/BC2B update only the admitted bank neighbors |
| Temperature class0152 | Boot-cleared; B2ED's8*temperature/-1/+17 classifier | B31D/B325 scalar families, normal class0..7 |
| Refresh cursor029B | Boot-cleared;747B/74A7/74AD are the cursor's resident updates |16-byte blocks0000..03FF, then0800..08FF; skip0400..07FF |
| Serial descriptor0362 | RX linked-list/command/page selection and TX/broadcast setup | Descriptor fields remain distinct from the memory addresses their payloads supply |

These are controller invariants with identified producers. They do not prove
every possible interrupt interleaving preserves every multi-instruction
snapshot. A changed calibration can alter table geometry/admission; supplied
code can invalidate all of them. Per-site conditions make that distinction
reviewable instead of silently widening a normal table into an arbitrary owner.

### Foreground self-copy and stack watermark

With0051.2 set,7470 loads cursor029B. Cursor0400 redirects to0800;0900 ends
the pass, clears the cursor's high byte and clears0051.2. Each block masks
I-bit interrupts, reads/re-writes eight adjacent words unchanged, advances the
cursor16 and reenables interrupts. Normal cursor progression makes the low
byte zero at the terminal high-byte clear. It does not initialize every word
to zero, set a diagnostic bit, or enable profiling.

74B7 separately scans03B0..03FF until a nonzero byte or the upper bound.
It supplies the stack-watermark comparison, not another unrestricted RAM
pointer. WAI's later conditional resume is already included in the rooted
structural graph; the address analysis does not infer an actual wake schedule.

### Every caller of the remaining writing helpers

| Helper / indexed operation | Complete rooted direct caller binding | Byte ownership |
|---|---|---|
| E58C, nine-byte estimator state | AF9A:Y=00B9; AFF7:Y=00C8 | Two independent capture/filter records; Y+0,+1 word,+3,+4 word,+6 word,+8 |
| F275, ADC mux read/modify/write | All rooted callers have X=3000 | PORTD3008; no RAM flag alias |
| F25F, ADC poll | All rooted callers have X=3000 | ADCTL3030 indexed read; direct timeout flag writes remain separate |
| F479, filter word update | 7789:X=006A; A669:X=0068 |006A/006B or0068/0069, with a separate Y coefficient input |
| F2FD, clear helper | Six immediate-argument calls716A/7173/717C/7219/7222/722B | Exact remainder/block writer footprints, not one unrestricted helper X |

The generator checks all discovered caller bindings and rejects an additional
non-call incoming edge or unexpected argument. This is stronger than choosing
one known call and applying it to every use of a helper. It closes the nine
remaining formal non-frame writing sites from the first global alias pass.

For F2FD,716A/7173/717C clear0036..00FF,0100..029C,0800..08FF.
7219/7222/722B clear0000..000A,000B..0035,029D..034D only on retained
checksum rejection.7182 is a separate clear of0360..03FE, excluding03FF.
Clear helper remainder stores and its four interleaved word stores have
different PCs/byte overlaps; those differences remain in the bit-writer map.

The active adaptive-update footprint is qualified by call order as well as a
table name. B494 callsBA65 only on the completed normal upshift path, with
gear1..3. Ordinary B32D/B367 runs atphase&3=1; B56B/BA38 follows atphase&3=2.
The sole normal gear publisherD69C is insideD4EB, whose table slots3/B have
phase&3=3. There is no ordinary intervening gear publication between a new
adaptive93 event and its next pressure-pass counter consumption.93.6 prevents
repeated counting. This scheduler/state qualification matters when binding
BA50 to032C..034D rather than extrapolating a gear0 table-underflow case.

## Descriptor, curve and retained-cell families

| Family | Address rule / ownership |
|---|---|
| Transmission D8FE | First selected bit before stop test; full word at base+2+u8(2*B)+k*stride; null fails immediately; no implicit fallback to another set bit |
| D7E5/D840/D8A7 | Caller Y is an argument record; its fields select normal/cold/gain descriptors or direct word arrays; saved X/SP frames are separate |
| D8CE | Range override uses byte-wrapped2*(3*((A2&7)>>1)+B) before adding the caller table base |
| C271 | Selected TCC base curve is preserved across6E2A lookup; C00B's transition tail uses record6E3B, not a stale curve pointer |
| IAC cells | Park029D versus drive02A7; AC selects+3, cold+6; local Y frames carry incremental/integral/cold working words |
| IAC9880 conversion | Indexhi(u16((flow>>4)+((flow>>3)&1))) into4E92; the word read includes the following knot |
| Adaptive restore/reset | BC65 points02F8/0309/031A; BA32 points6A81/6A92/6AA3; each bank has17 bytes, checksum032B is distinct |
| Adaptive neighbor commit | Bank pointer plus an admitted0..16 neighbor;032B is adjusted with the changed byte under SEI/CLI |
| DTC banks | Live0016..001E, candidates0056..005E, retained000B..0013; mask/flash table pointers are ROM data |
| E6BC reaction helper | Incoming category X is E71F/E728/E731/E73A/E743/E74C, then walks the nine masks downward; Y supplies enable/alternate masks |
| F4A4/F4B6/F4BD/F4C1 | Different entry headers choose coordinate/step/data base; knot address=data+hi(coordinate*step), with adjacent knot byte |
| F4DE | u/v subtract header offsets with floor0; row=header+3+floor(v/16)+floor(u/16)*stride; second row adds stride |

The detailed [transmission](FACTORY_TRANSMISSION_CONTROL.md),
[IAC](FACTORY_IAC_CONTROLLER.md), [diagnostic](FACTORY_DIAGNOSTICS.md) and
[engine math](FACTORY_ENGINE_CALCULATION_CLOSURE.md) contracts remain the
semantic authority for those expressions. The new alias map connects them to
individual PCs; it does not replace arithmetic/state conditions with a label.

## Serial stores and supplied pointers have different alias rules

| PC | Proven source/destination | Limit |
|---|---|---|
| F9AE | RXbase+j, all21 stock descriptor RX bases036C; j<N<=34 | Writes036C..038D before full checksum acceptance; abort does not roll them back |
| F9DC | Ordinary selected command-block first byte |038E or0399 |
| FA16/FA18 | Accepted copy036C+j to selected block+j | Ordinary04:<=11; factory:<=34 into038E..03AF; no zero fill |
| FAB9 | Factory upload source0390+j | Exactly32 bytes, including retained suffix after a short packet |
| FABC | u16(word sampled atFAB0[038E]+j), j0..31 | No target whitelist; can alias any CPU address and wrapFFFF→0000 |
| F8CA/F8DC | Live descriptor pointer or supplied memory-request address | Word versus byte route and normal &CFFF alias transform stay explicit |

The owner join now finds **0392 at indexed PCs86FD andE49E**. Those are
closed-loop/I/P service consumers, already described in the fuel-learning
contract. Its earlier absence from a *direct* owner search was not absence
from the program. Refresh and factory upload-source reads also appear in
the merged owners; they do not assign a new controller meaning to a field.

Upload snapshots the destination into X atFAB0, then reads each source byte at
FAB9 as the forward copy proceeds. Overlap with0390..03AF can therefore alter
later source reads; it is not a saved32-byte snapshot or memmove operation.
The32-iteration footprint describes normal completion. A new factory timer
entry can abandon the active loop by resetting SP, and supplied destinations
can change other state/devices while the copy is in progress.

FABC is the sole remaining non-frame indexed **write site without a finite
conditional footprint** in this rooted explicit-access inventory. That is a
literal received-address interface, not a missing local pointer derivation.
It is not the only way arbitrary memory can change: FAA5 and eight extension
calls can execute supplied code with unknown effects; implicit stack writes,
reset and physical devices have their own boundaries.

## Reading the owner maps correctly

`factory_global_alias_owners.csv` joins direct and qualified indexed byte
overlaps below4000. It has1,415 address rows, including RAM and devices.
ROM curve/checksum reads remain in the alias-site map; expanding all4008..FFFF
checksum bytes into a RAM-like owner count would obscure the useful result.
The checksum helper's sole rooted caller starts4008; its alignment prefix is
unused on that call, while its8-byte loop reads throughFFFF before wrapping.

The qualified owner list is **not an unconditional closed-world write set**.
Read each footprint's condition and retain FABC/FAA5/extensions as wildcard
effects. Local frames are named relative to their save sites, not folded into
global RAM addresses. Ordinary caller parameters and runtime read addresses
remain formulas because their role is inherently parametrized. No finite
ROM address union is asserted for arbitrary requested reads or supplied code.
