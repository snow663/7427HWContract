# Rev B whole-image operation reader

The reader explains every statically rooted instruction in the exact released
`0.3.12_engine_only_manual_idle_revB.bin`, SHA-256
`e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1`.
It changes documentation only. TS00 truck testing and fine-tuning remain active;
the guide does not start any queued firmware simplification.

## Reproduce and read

Run from the repository root with the supplied image:

```sh
python tools/explain_revb_bin.py --rom /path/to/0.3.12_engine_only_manual_idle_revB.bin --output /path/to/reader
python -m unittest discover -s tests -p test_revb_english.py -v
```

The generator rejects any other image identity and never writes its input.
Open `FULL_GUIDE.html` for a self-contained searchable reader, or `FULL_GUIDE.md`
for the complete Markdown text. `chapters/` splits the executable text into
13 smaller files. Each instruction has its address, bytes, operation,
plain-English explanation and condition-code effects. Calls and branches name
their destinations; conditional branches also name the fall-through address.
The HTML links between instruction addresses reset active search filters.

The generated coverage manifest records 6,449 instructions (15,272 executable
bytes), 242 reading sections and 393 supplied XDF parameter views. The parameter
catalog records raw bytes, widths, axes, units and supplied conversion formulas;
aliases remain separate views rather than being counted as independent data.
The byte ledger accounts for all 65,536 bytes, including padding, vectors,
non-rooted fill and unclassified regions. The full hexadecimal text reconstructs
the input image. It is not a flashable BIN.

## Evidence and limits

The existing strict decoder and vector/dispatcher-rooted sweep provide exact
instructions and static destinations. English instruction rules cover all 112
mnemonics present. Local register/flag provenance is discarded at joins and
opaque calls. The 372 indexed data operations retain caller/runtime pointer
qualifications. No unresolved control-transfer frontier is reported by this
rooted sweep; that does not prove every runtime data address, RAM upload,
interrupt history or physical hardware action.

Maintained read/write roles, reviewed custom symbols and address-specific notes
provide context. Factory C-source comments are explicitly qualified topic hints,
not proof that the modified image implements the whole factory routine. Reading
sections can include shared tails and are not guaranteed independent functions.
Inherited XDF descriptions and display conversions are not blanket certified.
Unknown roles and unclassified bytes remain visible.

This is an automatic ISA/address-role walkthrough with reviewed context. It is
not an independently hand-proved semantic reconstruction, cycle-accurate trace,
hardware validation or emulator certification. The CPU reference is NXP's
[M68HC11 instruction guide](https://www.nxp.com/docs/en/reference-manual/M68HC11ERG.pdf).

The maintained read register corrects one established role at `$4EB6`:
minimum battery-voltage sample threshold for IAC step service. `$91A5` loads
the battery sample at `$00A7`, and `$91B3` compares `$4EB6`. The earlier coolant
wording described the wrong input. Only Current use C398 changes; historical
OEM role text, other cells/tabs, both OEM books and the write reference remain
preserved. The supplied XDF already describes a voltage threshold and stays
byte-identical, as does the BIN.

## Verification

The mnemonic fixtures test explanatory coverage without distributing a full BIN
through CI. Tests also distinguish signed/unsigned branches, all-selected-bit
tests, pointer scope, carry changes and flag-preserving stack operations.
Whole-image generation checks exact input identity, unique complete instruction
coverage, complete byte accounting and parameter/code separation. Delivery QA
also checks CSV bytes against the decoder, full-hex reconstruction, hashes,
HTML IDs/targets, JavaScript syntax and search behavior in a DOM fixture.
Native browser rendering was not exercised in this environment.

The reproducible reader source is maintained here; generated full-image outputs
are delivered separately. No new BIN, XDF, calibration or controller behavior
is introduced by this documentation work.

For hardware-address context, use the [CS/EN and resource guide](REVB_CS_EN_ADDRESS_MAP.md).
It explains nominal selects versus the conditional internal-resource partition,
IRV bus visibility, software output shadows and the ALDL address transform.

## Functional context layer

The grouped reader adds 289 authored functional explanations above the same
6,449 instructions. Every operation belongs to one group. Groups include full
routines, smaller decision/calculation stages, shared continuations and empty
retired entries; they are not all independent functions. Their instruction spans
exclude intervening data, and conditional paths are not a sequential narrative.

```sh
python tools/explain_revb_functions.py --rom /path/to/0.3.12_engine_only_manual_idle_revB.bin --output /path/to/reader
python -m unittest discover -s tests -p 'test_revb_*.py' -v
```

This emits the original reader plus `FUNCTIONAL_GUIDE.html`,
`FUNCTIONAL_GUIDE.md`, 13 smaller `context_chapters/`, a function-purpose CSV,
structured groups and a functional coverage manifest. Open the functional HTML
first: purpose paragraphs stay visible, with exact operations and input/output
relationships expandable. Search finds any instruction address within its group,
as well as topics, roles and tuning notes. Internal links reveal their target
group even after a search or chapter filter.

The authored context is in
`maps/maintenance/revb_function_context.json`. It combines retained contract
context with current-image descriptions of patched paths. The reader separately
records how many instructions in each group match stock bytes; stock caller,
calibration or hardware equivalence is not inferred from that count. In
particular, removed gear/speed qualification, EGR corrections, old idle/transient
spark and dual-bank idle behavior are not narrated as still executing.

The guide distinguishes IAC capture, fuel-idle classification, closed-throttle
VE selection and optional closed-throttle OL. It also explains P versus integral
permission, internal air versus IAC steps, pre-follower IAC-change fuel input,
signed spark floors and shared versus removed diagnostic/board owners.
Selected tuning connections give current values, equality rules, timebase
qualifications and a worked internal P-air example. They are explanations of the
released defaults, not proposed calibration changes or physical tuning results.

Calls, direct branches and normal fall-through/call-return continuations connect
the groups. Width-aware explicit fixed reads/writes provide shared-address
reader/writer links. These are static relationships: arbitrary indexed/stack
effects, implicit register inputs, callees, interrupts and external hardware
are not a complete def-use or runtime-order proof. Referenced XDF views retain
inherited-unit qualifications; table bases are not assumed whole footprints.

The compact boundary fixture records the first/last instruction of each group
and selected calibration excerpts. Tests check valid decoding, authored boundary
membership, exact custom assembly anchors, fixed-versus-indexed operand scope,
unique partitioning and wrong-image rejection without requiring a private BIN in
CI. Whole-image delivery additionally checks every operation byte and group
assignment, Markdown/HTML links, JavaScript syntax and search behavior in a DOM
fixture. Native browser rendering remains outside the exercised checks.
When intentionally changing context boundaries/text, regenerate the compact
fixture with the grouped reader's `--record-boundaries` option and review its
diff; ordinary generation leaves repository references untouched.
