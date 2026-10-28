# Factory whole-program structure and ownership audit

This adds a complete **rooted structural inventory** of BMHM's7100..FFFF ROM
window, alongside the completed subsystem calculations and serial/service
contracts. It does not call every structurally reachable instruction semantically
closed. The inventory is decoded directly from the hash-identified ROM, without
using HAC's instruction/data declarations to decide the rooted graph.

## Roots, edges and scope of the result

Start from all21 vector wordsFFD6..FFFE, including resetFC29→7100 and every
interrupt/trap entry. Follow direct branches, jumps, direct calls and conditional
call continuations. At7A4F, add all16 actual word targets from7A85. WAI andSTOP
have explicit conditional resume edges: their following bytes cannot simply
be discarded as unreachable. These edges require an eventual wake/interrupt
return; they do not assert that the condition occurs on a particular truck.
SWI reaches the residentFC04 handler, which sets0000.3 and loopsFC07.

| ROM-derived structural result | Count |
|---|---:|
|Named reset/interrupt vector words|21|
|Rooted instruction starts|14,523|
|Bytes occupied by those instructions|34,527|
|Control-edge rows|18,003|
|Directly referenced memory bytes|1,637|
|Direct BSET/BCLR writer rows|771|
|Indexed memory instruction sites|951|
|Listing discrepancies in the rooted decode|47|
|External/runtime control frontiers|9|

The graph explores both sides of conditional branches and assumes a call can
return when following its continuation. It therefore includes impossible or
mutually exclusive operating paths. It does not enumerate every possible
factory callback target, turn return addresses into a static call table, prove
interrupt interleavings, or establish executed instruction coverage.
Popped-return-address escapes such asA407 remain described in their contracts;
the generic call-return edge is a may-edge, not proof that every call resumes.

There are **no overlapping rooted instruction decodes**, no decode failures,
and no rooted instruction bytes intersect the reviewed data regions. This
includes the308-byteC2D6..C409 descriptor block. The walker did not exclude those
tables in advance: it followed the actual control destinations and checked
for intersections afterward. Thus the prior false-dispatcher classification
now has a rooted control-flow cross-check as well as table-consumer evidence.
Arbitrary callback targets or supplied external code could deliberately choose
other byte alignments; those are the separately retained boundaries.

## Every byte has an explicit inventory category

The36,608-byte7100..FFFF window is partitioned as follows:

| Category | Bytes | Meaning |
|---|---:|---|
|Rooted instructions|34,527|Decoded from vector roots and the verified scheduler targets|
|Data or declared tail|2,007|Reviewed embedded tables, vector words, zero runs and literal tail metadata; not all metadata has a proven external consumer|
|Separate alternate-entry candidates|74|Decoded locally below; no rooted incoming edge in this graph|

This partition leaves no unlabeled byte in that window. It is **byte accounting**,
not a semantic-understanding percentage: classification of literal metadata,
an alternate entry's intended caller, or every bit's meaning can still be open.
Calibration4000..70FF remains a separate data region with tables explained in
the controller contracts. The full-image low padding is not executable RAM.

## Alternate and previously hidden entry structure

| Address/range | Actual bytes/behavior | Remaining interpretation |
|---|---|---|
|7AA5|39, RTS|No rooted caller; the first scheduler target is7AA6|
|A5D8..A5D9|20 FD, BRAA5D7|Post-SWI fallback;FC04 does not normally return here|
|F564..F5A1|Rounded saturating16x16 multiply helper|No direct rooted caller; supplied code could call it|
|FF90|7E9899, JMP9899|Direct-position IAC entry shape; external caller not established|
|FF93|7EA3FA, JMPA3FA|IAC reset entry shape; external caller not established|
|FF96|7EF326, JMPF326|Diagnostic checksum entry shape; external caller not established|

HAC declaresFF90..FF98 as word data crossing these three3-byte jump shapes.
Their alignment, destinations and adjacency to helper addresses suggest an
external/factory interface, but **the intended external ABI is an inference**.
There is no resident rooted caller that proves that intended use. They are
preserved as alternate executable candidates rather than silently promoted to
normal execution or discarded as data. `factory_global_alternate_entries.csv`
contains44 instruction starts across these74 bytes.

For F564, let incoming D=m and X=x be unsigned16-bit values. The instruction
reduction is `min(FFFF, floor((m*x+80hex)/256))`. It forms the low-byte product,
rounds from its bit7 through MUL/ADCA, accumulates the two cross products with
carry into a high overflow byte, and replaces both result bytes withFF if the
final upper byte is nonzero. The middle result word is returned in D; X is
consumed as scratch by the final pulls, Y is untouched, and SP balances on a
normal return. This locally explains an unused resident helper; it does not
assert any stock controller calls it.

Two more instruction-boundary corrections matter to structural reasoning:

* 74D0 is WAI, followed by74D1's branch back to746C. The continuation is a
  conditional return after an interrupt, not an independently disconnected loop.
* 7D8D is actual opcodeCF, STOP, after7D86 loadsD=5008 and7D8C executesTAP.
  Its conditional continuation7D8E branches to itself. HAC's `*****` row must
  not be counted as an unknown opcode or silently skipped to another routine.

The tail FE9F..FF8F and FF99..FF9F is byte-verified zero. FFA0..FFBF contains
literal words includingF2AA,F25F,F275,F3E4,0035,036C,53E1 and zeros. These
helper/data-shaped values are recorded in `factory_global_tail_words.csv`;
their intended consumers are not invented. Reserved vector wordsFFC0..FFD4
all containFC44, the residentRTI stub, already reached by a named vector.

## The nine nonresident/runtime control boundaries

| Call PC | Destination | Ownership |
|---|---|---|
|8C6A|1800|AFR extension|
|8EDF|1809|Governor extension|
|93D4|1803|IAC extension|
|A9E4|1812|Composite spark extension|
|AB66|180F|Spark handoff extension|
|D029|1815|EGR extension|
|F5D3|1806|Background extension|
|F5E4|180C|Extension connection/initialization|
|FAA5|wordRAM[038E]|Factory payload-supplied callback, no resident target whitelist|

The extension connection check reads word[1800] and compares it with7E18.
Its implementation is outside the mapped stock image; FF padding at file
offset1800 does not establish the runtime contents. ForFAA5, the
[factory-service contract](FACTORY_SERVICE_AND_TEST.md) now closes the producer,
arming, repeat and upload lifetimes. Arbitrary target memory/register effects
remain intentionally open. These nine sites exhaust the control frontiers
encountered by this rooted graph, not all possible behavior after external code
starts executing.

## Direct inventory and the completed contextual supplement

`factory_global_state_ownership.csv` enumerates every explicit **direct** read
and write in the rooted decode, including both bytes of word operations and
all direct full-byte co-writers. It joins the previously documented state names
and the earlier contextual indexed-writer evidence. The resulting1637-byte
inventory includes RAM, I/O and ROM reads; it is not a list of1637 RAM variables.
`factory_global_bit_writers.csv` separately records directBSET/BCLR masks so a
flag's producers can be compared without mistaking a neighboring word write
for a single bit instruction.

The previous indexed study had262 per-root baseline rows and917 expanded
context rows. The new951-site inventory is a different denominator: unique
indexed PCs throughout the whole rooted graph, including SCI/IRQ/boot paths
outside the earlier scheduler study. It cross-links the earlier classifications
and root contexts without treating one context's resolved address as universal.
The earlier28 unresolved baseline rows are still28 in that preserved study;
none is silently closed merely because a human contract now describes it.

The following worklist described the outstanding ownership proof at the time of
this structural inventory. It is now addressed by the
[global alias contract](FACTORY_GLOBAL_ALIAS_CONTRACT.md),
[flag lifetimes](FACTORY_FLAG_LIFETIMES.md), and
[ownership closure ledger](FACTORY_OWNERSHIP_CLOSURE.md):

1. Bind every indexed site's addresses by caller/mode. SerialF9AE is descriptor
   RX-base+j;FA18 is the bounded service/factory copy;FABC is an unrestricted
   upload destination. These must have different alias rules.
2. Integrate descriptor-selected transmission/RAM overrides, retained IAC/adaptive
   cell pointers, lookup-helper parameters and frame offsets into a global alias
   index, retaining branch/context qualifications.
3. Join indexed initialization and masked clears with direct bit and full-byte
   co-writers, then establish flag lifetimes and admission conditions, including
   the extension/profiling enable and shared hardware output shadows.
4. Grade alternate entries and physical/interrupt interfaces against their own
   evidence. Byte accounting and named controller equations do not replace this.

The supplement gives a qualified address contract to all951 indexed PCs,
adds all-rooted-caller bindings for the remaining writing helpers, and joins
indexed clears/masks/self-copy with direct byte/bit owners. Its finite footprints
remain conditional; runtime reads, arbitrary uploadFABC, opaque code and physical
or concurrency proofs retain explicit limits. The historical direct inventory
above is not silently relabeled as the new merged owner denominator.

This pass supplies the actual global instruction/direct-owner authority for that
work. Older `factory_memory_accesses.csv` and its derived dossiers still use
their explicitly labeled **partial** ROM overlay. They are retained as historical
indexes; for a conflicting instruction or direct owner, use the new rooted
ROM inventory.47 discrepancy rows include parser/comment/operand spelling
problems and earlier corrections; they are not47 newly discovered behavior bugs.

## Reproduction and completion status

Use `tools/verify_factory_global_structure.py --rom /path/to/BMHM.BIN` for a full
hash-checked image, or `--check-recorded` to reproduce the committed excerpts.
`bmhm_global_structure_rom_evidence.json` records image/listing identity,
counts and source bytes. Generated vectors, instructions, edges, regions,
frontiers, alternate entries, direct owners, indexed sites, bit writers and tail
words are under `maps/structure/factory_global_*`. The inherited HAC is unchanged.

The named resident engine, IAC/speed, DTE and serial/service/test calculations
now have documentation. Reset/vector-rooted structure and direct state owners
have a global byte-backed inventory. The ownership supplement now supplies
indexed-address provenance, writing-helper binding and gate lifetimes. General
flag/interleaving proofs, intended external-entry use, supplied code and physical
interfaces retain their explicitly stated limits.
This is a defensible completion ledger without an invented whole-ROM percentage.
