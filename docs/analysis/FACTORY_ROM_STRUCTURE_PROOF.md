# ROM-byte evidence for the lookup-block classification

The actual 65,536-byte `BMHM.BIN` was read, rather than reconstructing bytes from HAC mnemonics. Its SHA-256 is:

```text
6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
```

The separately supplied `BMHM_95_C-G-K_Truck_7_4TBI_4l80.bin` has the same size and hash. This matches the stock-image authority already recorded in `docs/WORKING_STATE.md`. The image is a full 64-KiB mapping, so the offsets shown here equal CPU addresses.

## Caller bytes establish use as a descriptor

The actual ROM at `$C088-$C09B` contains:

```text
C088: CE C3 A2 D6 D9 96 7F BD D8 FE 24 03 CE 6E 08 96
C098: B2 BD F4 C1
```

The decisive instructions are:

| PC | Actual bytes | HC11 operation |
|---|---|---|
| `$C088` | `CE C3 A2` | Load X with `$C3A2` |
| `$C08F` | `BD D8 FE` | Call `$D8FE` |
| `$C094` | `CE 6E 08` | Select fallback data-table base `$6E08` |
| `$C099` | `BD F4 C1` | Use X in the data-lookup helper |

At `$D900/$D903`, bytes `A6 00` / `A6 01` read the descriptor's first two bytes through X. `$D906-$D90B` contains `58 3A 86 01 08 08`: double the B index, add it to X, initialize the bit selector, and skip the two-byte header. The helper performs a **word read** at `$D91F` (`EE 00`, `LDX 0,X`) and returns at `$D92D` (`39`, `RTS`). It does not jump through the selected word.

The subsequent reader at `$F4C1-$F4DD` is also captured from ROM. It indexes X, reads a data word at `$F4C9` (`EC 00`), performs arithmetic/interpolation, and returns with `39`. This confirms that the selected `$6E08/$6E19` values feed a data reader, rather than relying on its HAC function name.

Instruction encodings can be checked in NXP's [M68HC11 programming reference](https://www.nxp.com/docs/en/reference-manual/M68HC11ERG.pdf). The byte values in this proof come from the actual BMHM image.

## The apparent jumps are pointer words

The ROM descriptor at `$C3A2` is exactly:

```text
C3A2: 08 08                         header: terminal mask, row stride
C3A4: 00 00 00 00 6E 08 6E 19      row 0: four big-endian words
C3AC: 00 00 00 00 6E 08 6E 19      row 1
C3B4: 00 00 00 00 6E 08 6E 19      row 2
C3BC: 00 00 00 00 6E 08 6E 19      row 3
```

The words at `$C3A8/$C3AA` are `$6E08/$6E19`, both in calibration space. The same pair repeats in the other rows. `$6E08` is also the caller's explicit fallback data-table address. Reading those same bytes as instructions happens to produce `JMP $08,X` / `JMP $19,X` because indexed JMP has opcode `$6E`.

That explains all eight apparent jump sites using the actual caller, actual helper, and actual descriptor bytes. No HAC role label is needed for that conclusion.

## The apparent writes have the same cause

At `$C2DA`, actual bytes `6C 3D` are a descriptor word pointing to `$6C3D`. Decoding them as an instruction produces `INC $3D,X`.

An example that crosses pointer-word boundaries is:

```text
C2F4: 6B D7       pointer $6BD7
C2F6: 6B E8       pointer $6BE8
```

Starting instruction decoding at `$C2F5` instead produces `D7 6B`, a valid direct-page `STAB $6B`. The HAC mnemonic at that address is therefore not an operand mismatch. It is an accidental instruction decoding across two data words. The earlier conversational claim of `F7 6B E8` at `$C2F5` was incorrect and is superseded by these actual bytes.

## Whole reviewed block

The eight 34-byte descriptors have header `08 08`, and the two 18-byte descriptors have header `02 08`. Their extents match the loaded/computed bases and the reader's terminal-mask/stride behavior. Together they contain 144 pointer words: 72 null and 72 nonzero. Every nonzero word lies in `$4000-$70FF` calibration space.

`maps/structure/bmhm_rom_lookup_pointers.csv` records all 144 entries directly from these bytes. `bmhm_rom_structure_evidence.json` preserves the identity and selected byte ranges, including the actual callers and helper. The source listing is unchanged.

## Proof limits

This verifies the data-descriptor use and byte layout in the identified BMHM ROM. It does not prove whole-ROM reachability, exclude every conceivable overlapping code/data use, verify the rest of the HAC listing, or identify physical hardware behavior. A complete claim that these addresses can never execute would require the full execution/reachability analysis; that is still open.

The 28 removed write records are mutation mnemonics in this reviewed data block, not 28 individually observed runtime writes. Structural regression tests prevent those data bytes reappearing as presumed executable mutations; they are not independent proof of execution behavior.

## Reproduce

```bash
python tools/verify_factory_rom_structure.py --rom /path/to/BMHM.BIN
```

The verifier rejects any other size or SHA-256 before accepting the evidence. To check only consistency of the recorded excerpts and pointer CSV, without claiming a fresh complete-ROM check:

```bash
python tools/verify_factory_rom_structure.py --check-recorded
```
