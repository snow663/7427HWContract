# Rev B read/write findings audit

Audit date: 2026-11-07. Authority: exact released Rev B, SHA-256
`e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1`.
The BIN, XDF, simulator implementation and OEM workbooks are unchanged.
TS00 truck testing/fine-tuning remains active. This audit corrects references,
records evidence gaps and queues follow-up work; it does not start another
firmware simplification.

The [role-naming follow-up](REVB_MISSING_WRITE_ROLES.md) now assigns functions
to all 92 sites left without named rows by this initial audit. The original gap
counts below remain historical; the current inventory separates three dynamic
operands from global address rows and reports no writer without a named role.

## Findings and disposition

| ID | Finding | Disposition |
|---|---|---|
| RW01 | `$004C` was incorrectly marked omitted in the read register; its write label described only cleanup. IAC shadow production/publication survives. | Corrected both Current use labels. Also clarified `$004D` as the board-input mirror. |
| RW02 | The named write evidence omitted 108 rooted write instructions, 96 with fixed operands. It was not a complete write-site inventory. | Added an inventory of all 1,120 explicit rooted write sites, new named rows and 22 fixed writer associations. Remaining unnamed sites stay visible. |
| RW03 | Abstract widening hides the full RAM refresh footprint from finite operand coverage. | Added a qualified CPU walk proving 1,280 distinct bytes read and rewritten, with identical paired values, for a valid admitted cursor walk. |
| RW04 | The fast ADC wrapper still publishes result slots after its conversion-completion timeout. | Added a timeout witness. Sample publication alone does not prove fresh conversion; fault/validity context must accompany future logging. |
| RW05 | Old DFCO speed scalars `$493B/$493C` are loaded but discarded before the decision. | Added six varied-value witnesses. Their retired speed-gating roles stay omitted; no code removal or tuning change. |
| RW06 | `$088B` is still written even though no fixed/finite operand reader was found. | Clarified the surviving write as a converted air-command snapshot. Its omitted read role remains correct. |
| RW07 | The older simulator's memory boundaries and default CONFIG do not implement the conditional F1 resource interpretation used by the newer guides. | Recorded implementation observations and a follow-up item. No simulator behavior changed. |
| RW08 | `$02F3` was labeled sampled BARO input but is constructed from MAP plus a correction or fallback. | Corrected both Current use labels and added construction, saturation and fallback witnesses. |

## What was checked

The exact-image rooted sweep contains 6,449 instructions, including 2,221
explicit operand-read sites and **1,120 explicit write sites**: 1,018 fixed
and 102 indexed. RMW instructions belong in both counts. Implicit stack
transactions, instruction fetch and vector fetch remain separate categories.

Every recorded read instruction was compared with the current bytes. Every
named writer association was checked against a rooted write instruction and,
where fixed, its byte footprint. The initial 714 named write rows contained
2,532 writer associations across 1,012 instruction PCs. **No non-rooted writer,
non-write instruction or mismatched fixed destination was found in those
existing associations.** This does not independently certify their semantic
labels or every indexed binding.

After the reference update, there are 721 named write rows and 2,554
associations: 1,259 fixed matches, 726 finite indexed matches and 569 inherited
indexed associations not resolved by the generic abstract scan. Of those 569,
505 refer to the eight RAM-refresh stores, 36 to the boot serial clear, 26 to
the service-packet copy, and one each to the BLM-cell and receive-buffer stores.
Those are qualifications, not 569 proven bad writes. The refresh witness below
supplies a separate bounded proof; it does not rewrite generic abstract
contexts as universally finite.

The [full write-site table](../../maps/maintenance/revb_rw_audit/WRITE_SITES.csv)
now exposes every rooted write operand, width, instruction bytes, finite
footprint, abstract expressions and named-row associations. The
[pre-audit gap list](../../maps/maintenance/revb_rw_audit/PREAUDIT_UNINDEXED_WRITERS.csv)
preserves the original 108 omissions. Sixteen previously unindexed PCs gained
named associations; [92 sites still lack a named row](../../maps/maintenance/revb_rw_audit/WRITERS_WITHOUT_NAMED_ROWS.csv).
Some target unnamed diagnostic/cleanup bytes, generic buffers or frames.
Absence from the named register is not evidence that a site is dead or safe to
remove. Detailed semantics for these remaining sites are follow-up work.

The existing CS/EN extraction, software-shadow and ALDL witnesses remain
consistent. The F1 interpretation was checked against NXP's
[MC68HC11F1 technical data](https://www.nxp.com/docs/en/data-sheet/MC68HC11F1.pdf),
§4.2, §4.5 and Tables 4-9 through 4-12. The field definition and summary table
still support GEN-over-PROG for GCSPR=1; the contradictory sentence in §4.5.1
does not overturn those explicit definitions. Physical GM derivative backing,
CONFIG response and aliases remain conditional/unmeasured.

## RW01: an active shared shadow was labeled removed

At `$9203`, firmware reads `$004C`, retains mask `$E3`, merges the IAC
phase/enable field selected by `$1C`, and stores the resulting byte at `$920A`.
The `$9243` RMW can also set its enable bit. At `$F40F/$F411`, the common board
publication path reads that same RAM byte and writes it to `$3062`.

The engine-only cleanup at `$5C4A` clears mask `$23` in this shared byte. It
does not remove the surviving `$1C` IAC fields. Consequently, a whole-byte
`omitted` read label was false, and a cleanup-only write label was incomplete.
Both maintained Current use fields now describe the shared IAC/output shadow
with removed transmission fields cleared. Original column-B meanings remain.

`$004D` is produced by `$F414/$F417`, reading board input `$3064` into RAM.
Its original IAC-input wording was too narrow for the shared mirror. Both
Current use fields now identify the board-input publication and surviving
engine/IAC consumers. Physical input pin identities are still qualified.

## RW02: newly named state and write coverage

The maintained read and write books now name `$0000`, `$001B`, `$001B.1`,
`$001B.2`, `$016E` and `$016F`. These are existing addresses, not allocations:

- `$0000` receives interrupt/trap cause bits, including the handlers at
  `$FC04/$FC09/$FC11/$FC1A/$FC1F/$FC24/$FC29` and the dispatcher path `$794B`.
- `$EB24–$EB49` reads `$02F3`, compares it with the upper barometric-input
  threshold, ages `$016E` and updates `$001B.2`. The input is the BARO estimate
  described in RW08, not a dedicated ADC sample.
- `$EB58–$EB7D` compares the same input with the lower threshold, ages `$016F`
  and updates `$001B.1`. These are option/admission-qualified diagnostics;
  rooted instructions do not prove the shipped calibration admits every path.
- The write book also names `$0F00`, the actual destination of `$F5D8`.
  It lies in the conditional F1 EEPROM window. Its purpose and GM backing remain
  unresolved; the store alone does not prove an EEPROM programming operation.

The original named write evidence gained fixed writer associations wherever
the instruction actually addresses a named row start. RMW bit masks are used
when adding bit-field associations. Generic writes that preserve a bit can
still write the byte; an indexed/reset/refresh association does not make an
omitted operational role active. OEM role text and both OEM books are preserved.
New original-role descriptions use current instructions and the recorded stock
opcode index; this audit does not claim a fresh full-OEM-BIN analysis.

## RW03: RAM refresh is a read/write loop, not a value producer

With `$0051.2` set and cursor word `$029B = $0000`, the admitted path at
`$746C` processes 16-byte blocks. Eight LDD/STD pairs at `$7484–$74A2` read
each word and write the identical word back. The cursor advances by 16,
switches from `$0400` to `$0800`, and stops at `$0900`.

| Qualified interval | Distinct bytes read | Distinct bytes rewritten | Role |
|---|---:|---:|---|
| `$0000–$03FF` | 1,024 | 1,024 | Working-RAM refresh, including variables and the valid stack contents in the fixture. |
| `$0800–$08FF` | 256 | 256 | External working-state refresh under the expected resource map. |

The witness observes 640 word reads and 640 paired word writes with identical
addresses and values. The cursor's own stores and service-flag updates are
separate effects. This is a qualified uninterrupted walk with a valid cursor;
arbitrary retained cursor values and interrupt/corruption histories are outside
the proof. These bytes overlap existing finite coverage and must not be added
as disjoint capacity. A refresh writer does not establish a variable's control
producer, learned value or initialization history.

## RW04: ADC publication can follow a timeout

`$F25F` clears the per-call ADC fault bit, starts a conversion through ADCTL,
then polls completion at `$F267`. After twelve failed polls, `$F26E/$F271`
set `$003A.0` and `$001A.1`. Both completion and timeout paths return through
`$F274`.

The fast caller then reads ADR1, conditionally ADR2, and ADR3 and publishes
`$00A6`, `$082E` and `$01D5`. A controlled COCO-clear witness confirms these
stores still occur after timeout. On actual hardware, the result slots' values
and freshness depend on ADC behavior; the fixture deliberately does not model
that behavior. This is established software handling, not proof that the
truck's ADC is failing or that the fault response is defective.

Future diagnostic logging should preserve ADC fault/status and conversion/mux
context alongside samples. No automatic timeout fallback or filtering change
is introduced here. The previously documented caller-dependent sensor meaning
of ADR1–ADR4 remains valid.

## RW05/RW06: a read can be discarded and a write can be diagnostic

At `$8209`, A receives `$493B`. If fuel-cut state is set, `$8210` replaces A
with `$493C`. The patched path jumps to `$8218`, where `LDAA $0246` replaces A
before the next decision. These loads' N/Z/V changes are also replaced; loads
preserve carry. Six controlled cases vary both thresholds and both fuel-cut
states and reach the same final A/CCR before `$821B`.

Thus the old speed thresholds do not provide speed gating through this slice.
Their byte reads are real, but their former tuning role is removed. Removing
the loads would change execution timing, so this audit does not delete them
or declare a whole-vehicle equivalence result.

Conversely, `$9880` still publishes the converted air-command word at `$088B`.
The following conversion continues through live IAC position computation;
the calculation cannot be deleted merely because this snapshot has no
identified fixed/finite reader. The write label now states that narrower role.
Its omitted read role stays preserved. Runtime-selected ALDL reads remain
possible and are not exhausted by the finite inventory.

## RW08: the BARO diagnostic input is a constructed estimate

The old `$02F3` label suggested a sampled barometric-pressure input. At `$C5FF`,
firmware adds a lookup-derived correction to filtered MAP `$01C6`, saturates an
overflow to the byte ceiling, and publishes `$02F3` at `$C606`. It then filters
that candidate into the word at `$02F4`. A separate fallback path loads `$4E68`
and publishes the candidate and filter state at `$C61D/$C620`.

Thus `$02F3` is an estimate/fallback input to the BARO filter and the high/low
diagnostic qualifiers, not a direct ADC publication. Both maintained Current
use labels now say so while preserving the original label in column B. Three
scoped cases verify addition, saturation and fallback publication. The supplied
lookup output is controlled in those cases; they do not establish physical
pressure scaling or the complete interpolation/qualification behavior.

## RW07: simulator resource coverage needs its own checkpoint

The current `HC11Memory` implementation allocates 512 internal RAM bytes and
64 internal register bytes. Its relocated register window ends at `$303F`.
The profile labels `$0200–$2FFF` external working RAM with high contract
confidence. The newer **conditional F1 interpretation** has 1,024 RAM bytes,
96 register bytes through `$305F`, conditional EEPROM and additional selection
boundaries. The fixture observes `$0200` and `$305C` as external in the current
model and its default CONFIG response as `$03`, while Rev B expects `$0B`.

Therefore current simulator storage/traces cannot validate those F1 resource
boundaries or chip-select routing. In particular, a successful store to `$305C`
in flat backing memory is not a simulated chip-select configuration. This is a
confirmed model/interpretation mismatch, not proof of the actual GM CPU's RAM
capacity. The read/write witnesses use explicit controlled storage and were
never hardware-equivalence tests; their instruction assertions remain useful.

Follow-up: review selectable target resources, CONFIG qualification, CS/IRV
routing and peripheral side effects together, with dedicated model checks and
hardware qualifications. Keep raw ADC channel/mux bindings explicit. That work
does not authorize a new BIN or displace TS00. The model is unchanged here.

## Reproduce and remaining limits

```sh
python tools/audit_revb_rw.py --rom /path/to/revb.bin
python tools/audit_revb_rw.py --check-recorded
python tools/trace_revb_reads.py --rom /path/to/revb.bin
python tools/trace_revb_reads.py --check-recorded
python tools/verify_revb_cs_decode.py --check-recorded
python tools/build_custom_xdf.py --check
python -m unittest discover -s tests -p 'test_revb_*.py' -v
```

Use `--record` with an exact full BIN only to intentionally update generated
audit files. Recorded mode decodes all committed write instructions, checks
fixed named associations and current reference identities, and replays thirteen
scoped cases. It does not reconstruct rooted reachability or indexed abstract
flow from incomplete excerpts. Full-image mode supplies those additional
checks. Neither mode proves interrupt histories, every bit's semantic liveness,
all runtime addresses, physical peripheral side effects or truck behavior.

The [audit evidence directory](../../maps/maintenance/revb_rw_audit/README.md)
and workbook before/after journal retain exact scope and provenance. No newly
demonstrated active engine-control defect is asserted. Remaining unnamed roles,
simulator resources and any cleanup candidates remain explicitly open.
