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
