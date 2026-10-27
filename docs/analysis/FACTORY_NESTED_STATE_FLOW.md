# Factory nested calls and indexed state flow

The scheduler map now extends through nested calls to **234 ROM procedure
entries**, with register-return and memory-effect summaries. Of the previous
262 per-root indexed-access rows, **216 now have physical addresses or bounded
address sets**. This closes a substantial address/dataflow gap. It does not
assign semantics to every routine or establish a whole-firmware completion
percentage.

## ROM authority and scope

The complete 65,536-byte BMHM image is required for a fresh verification:

```text
SHA-256: 6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
Mapped ROM: CPU $4000-$FFFF equals full-file offset $4000-$FFFF
```

The analysis starts from the preceding 63 callee roots, the 16 scheduler
landings, TOC3 entry, boot, foreground, and factory entry: 83 distinct roots.
Following direct calls adds 151 more entries. The main indexed call is recovered
from the actual 16-word table; the RAM callback remains open.

The resulting graphs contain 13,786 distinct decoded instruction starts, 860
distinct indexed-memory instruction sites, and 586 call rows under procedure
contexts. Entries can share code through tail jumps, so these are not 234
disjoint function extents. Control flow is an overapproximation unless a branch
is excluded by known scalar/ROM values. Interrupt interleavings and actual
execution coverage are not proven by these counts.

## Progress against the previous 262 rows

| Result | Rows | Meaning |
|---|---:|---|
| One physical address | 162 | Every represented path reaches the same address |
| Bounded address set | 54 | A conservative finite set, not one chosen table element |
| Stack-relative | 1 | Frame offset established; no invented RAM variable address |
| Caller parameter | 4 | Address expressed using an incoming register |
| Pruned by constant flow | 8 | Not reached from the analyzed entry under the captured stock constants |
| Unresolved | 33 | Insufficient pointer/register information remains |
| Total | 262 | Same per-root denominator as the preceding scheduler pass |

The 917 rows in `factory_indexed_flow.csv` cover the expanded procedure contexts,
including the eight historical rows retained as pruned. They use a different
denominator from both the previous 262 rows and the whole-listing 1,038 indexed
accesses. No claim that the entire ROM has only 33 unresolved accesses is made.

Seven pruned rows belong to the optional broadcast-payload path under `$F5E8`:
the captured `$518F` schedule words are all zero, so `$F5F8` exits. The remaining
row is a constant-bounded branch in `$A466`. These conclusions apply to this
stock image and these entry paths; recalibration can change them.

## How addresses survive calls

The analyzer follows register values across branches and explicitly joins
different paths. It tracks finite constants and affine expressions such as
`entry_X+1`. Only captured ROM and locally saved stack bytes are folded. Loads
from working RAM and devices remain unknown even if the BIN has padding at
the same file offset.

Each callee is analyzed before its callers. Return-register expressions and
explicit memory accesses are substituted into the caller's input values.
Word operations retain both byte aliases. The math helpers `$F459`, `$F4C1`,
`$F4DE`, and `$F550` preserve X and Y on their normal return paths; this is
derived from their actual push/pull flow rather than assumed for every JSR.

For example, the call at `$803B` supplies X=`$024E` to `$F550`. Its access
templates then resolve as follows:

| Helper PC | Operation | Bound address / role |
|---|---|---|
| `$F551` | `LDAB 1,X` | RAM `$024F`, low byte |
| `$F558` | `LDAA 0,X` | RAM `$024E`, high byte |
| `$F55D` | `ADDB 2,X` after TSX | Temporary stack byte |
| `$F561` | PULX | Restore the caller's X |

The caller later subtracts its derived correction from `$024E`. The helper's
stack access is not a third global fuel state. Other calls to the same helper
bind their own addresses instead of inheriting `$024E` globally.

Possible RAM aliases invalidate saved-stack knowledge conservatively. Unknown
calls clobber all registers, including SP, and may touch arbitrary memory.
Known effects are still recorded, while an explicit opaque-call marker prevents
them being mistaken for complete read/write sets. Every call continuation is
conditional on a normal return.

Stack reasoning assumes a valid working-RAM stack. It does not establish
worst-case stack depth or prove recovery from arbitrary stack corruption.

The finite-set limit is 64; larger value sets widen to unknown. Byte arithmetic
that would lose wraparound information also widens. Thus a complicated loop
can remain open even if its behavior is finite. Three small constant-counter
loops receive separately reviewed footprints rather than treating X/Y values
from different iterations as correlated automatically.

## A concrete indexed flag producer

`$F333` initializes X=`$0009`, Y=`$F37F`, then decrements both for nine
iterations. Each iteration ANDs three RAM bytes with the ROM mask addressed
by Y. Its fifth iteration includes:

```text
X = $0005; Y = $F37B; ROM[$F37B] = $D9
$F341: LDAA $15,X       // read $001A
$F343: ANDA 0,Y         // AND $D9
$F346: STAA $15,X       // write $001A
```

This clears `$001A bits $26`, including bit5 used by the scheduler's special
fast-group branch. A direct `STAA $001A` search cannot find that producer.

The related `$F380` loop applies mask `$E7` from `$F3DF` to `$001A`. It clears
bits `$18` and preserves bit5. Its nine masks occupy `$F3DB-$F3E3`; those bytes
are data consumed through Y, immediately before the real `$F3E4` toggle helper.

`factory_masked_state_updates.csv` records all 45 mask/destination pairings.
The loops are checked through actual CPU execution with four varied RAM patterns
each, including a case where `$001A=$FF`: `$F333` produces `$D9`, while `$F380`
produces `$E7`.

A call-graph witness is `$793D -> $AE85 -> $F64E -> $F333`. This does **not**
prove the routine executes with bit5 set: the ordinary scheduler gate already
requires that bit clear before admitting `$AE85`. The local clearing operation
is verified; a claim that this path restores a running special-mode scheduler
would require additional admission/lifetime evidence.

## Indexed initialization footprints

The ROM `$F2FD` clear helper now has a call-specific contract for lengths
1..512, covering all six captured factory calls. The model checks the exact
helper bytes, tracks its X advance and D/Y return values, and retains word-byte
overlap. It rejects a call whose known range would erase its own return address.

| Call PC | Bytes cleared to zero | Count |
|---|---|---:|
| `$716A` | `$0036-$00FF` | 202 |
| `$7173` | `$0100-$029C` | 413 |
| `$717C` | `$0800-$08FF` | 256 |
| `$7219` | `$0000-$000A` | 11 |
| `$7222` | `$000B-$0035` | 43 |
| `$722B` | `$029D-$034D` | 177 |

The last three calls are conditional initialization paths. Their table entries
are footprints when admitted, not an assertion that all RAM is cleared on every
restart. This identifies indexed initialization of the busy/pending flags and
many state words missed by direct-store inventories.

The 512-byte bound is an analysis limit, not the firmware's maximum length.
Zero and wider lengths stay outside this specialization. Real CPU tests check
the six factory lengths plus boundaries 1, 7, 8, 9, and 512; adjacent sentinel
bytes and X/Y/D results must also agree.

## Exact multiply primitive and the replay correction

For entry A=`m` and unsigned word at X=`w`, actual `$F550-$F563` returns:

```text
D = floor((m*w + 128) / 256)
```

X and Y are preserved, and SP returns to its caller value. The units and
additional shifts belong to the enclosing caller, rather than this primitive.
Thirty independent multiplier/word combinations check rounding boundaries,
zero, and `$FFFF` through the actual ROM instructions.

This numeric cross-check exposed an existing CPU-model error: MUL used product
bit15 for carry. The [HC11 reference manual, MUL, page 560](https://www.nxp.com/docs/en/reference-manual/M68HC11RM.pdf#page=560)
specifies product bit7, which supports the following `ADCA #0` rounding step.
The one-bit correction has separate instruction tests that distinguish the two
bits and verify that other flags are unaffected. The abstract address analyzer
still widens MUL carry; its address results do not depend on this numeric fix.

## Remaining frontiers and source correction

Eight external targets remain opaque: `$1800`, `$1803`, `$1806`, `$1809`,
`$180C`, `$180F`, `$1812`, `$1815`. Their implementation is not supplied by
this ROM image. `$FAA5` additionally calls through a runtime RAM word. These
remain unknown memory/register effects even where the rest of a procedure
has known accesses.

The newly traversed `$A407` path also resolves the inherited malformed operand
at `$A40B`. Actual bytes `12 09 01 56` mean `BRSET $09,#$01,$A465`.
CPU execution checks both the taken `$A465` target and `$A40F` fallthrough.
`factory_nested_control_corrections.csv` records this alongside `LA4656` from
the original text. The older source-only control index remains unchanged until
its correction-overlay integration is reviewed.

The unresolved cases include descriptor-selected pointers, service buffers,
table geometry, and stack/register paths crossing optional extension hooks.
The four caller-parameter rows include ADC/port helpers that bind to `$3000`
in known call contexts, but their generic entry templates deliberately retain
the parameter. Exact engine integer models and physical register effects remain
separate work.

## Artifacts and verification

All maps are under `maps/structure/`:

| File | Purpose |
|---|---|
| `bmhm_nested_state_rom_evidence.json` | Image identity, captured bytes, roots, counts, limits |
| `factory_nested_calls.csv` | Caller/callsite/target and incoming X/Y/D expressions |
| `factory_indexed_flow.csv` | Indexed addresses, frame/parameter roles, explicit unknowns, baseline accounting |
| `factory_nested_memory_effects.csv` | Propagated read/write may-effects and call witnesses |
| `factory_nested_state_summary.csv` | Return-register expressions, known byte effects, opaque/open dependencies |
| `factory_indexed_clear_calls.csv` | Six verified conditional initialization footprints |
| `factory_masked_state_updates.csv` | Exact mask/destination pairs for the nine-iteration loops |
| `factory_nested_frontiers.csv` | External hooks and runtime callback boundaries |
| `factory_nested_control_corrections.csv` | ROM-backed `$A40B` branch correction |

Nested effects are unioned per first callsite. A retained witness names one
path; it does not assert that every unioned address is accessed on that one path.
Known byte lists never exclude the separately marked unknown effects.

```bash
python tools/build_factory_state_flow.py --rom /path/to/BMHM.BIN
python tools/build_factory_state_flow.py --check-recorded
python -m unittest discover -s tests -p 'test_factory_*.py' -v
cd hac31_romsim
python -m unittest discover -s tests -v
```

The 18 new flow tests include branch joins, stale-pointer rejection, unknown-call
clobbers, byte-to-word extension, carry-predicate invalidation, possible stack
aliases, nested helper substitution, word-byte aliases, actual mask loops, clear
contracts, checksum bounds, wrapped word aliases, and the malformed branch.
Together with the earlier suites, 51
factory tests and 14 CPU/simulator tests pass locally, including the full-ROM
100,000-instruction regression. Recorded checks verify excerpt/output
consistency; `--rom` verifies the complete image before constructing the maps.
