# ROMFlow Studio

A local, dependency-free browser workbench for the Motorola 68HC11, aimed at GM PCM firmware families without imposing the $31/BMHM code or memory map.

## Start

Windows: double-click `Launch_ROMFlow_Studio.cmd`.  Linux/macOS: `./Launch_ROMFlow_Studio.sh` or `python -m studio.server` from this directory. Requires **Python 3.10+**; no pip packages or external services. Open the displayed `http://127.0.0.1:8765/` URL in your browser. The server binds to loopback only.

Load a raw ROM with **Open ROM…**.  The image is mapped to the top of the 64KiB address space by default if it is shorter than 64KiB; set a custom load address from the API or on opening. Start in **Generic HC11** for unknown PCMs. The GM 7427/$31 profile adds *annotation hints only*; it never controls opcode decoding.

## Portable project persistence

The program automatically caches the active ROM, labels, region definitions, table definitions and graph layout in `workspace/projects/<ROM SHA prefix>/annotations.json`. Closing the browser or server does not discard these changes. Use **Recent** to switch between cached ROMs.

For a moveable backup, click **Save project ↓** (or Ctrl+S). A `.romflow` file contains:

```
manifest.json   Format/schema, ROM name, SHA-256, image start
rom.bin         Exact source ROM bytes; no patching
metadata.json   Annotations, groups, named memory zones, user roots,
                dispatch table declarations, table definitions,
                current view, graph node positions and transforms
```

Click **Open project…** (or Ctrl+O) to reload it. Analysis is recreated from the embedded ROM, with the saved state overlaid. The archive is checksum-validated and never extracted as untrusted file paths. `--project my_file.romflow` also works from the command line.

Use **Reports ↓** (or Ctrl+E) to export machine-readable analysis JSON/CSV and per-routine reports, *not* a restorable project. **Open ROM…** (Ctrl+Shift+O) starts or switches to another image; it will not erase a different ROM's cached workspace.

## Interactive features

- Expand/collapse routine groups, vectors, dispatch edges, memory zones, code/data regions and calibration tables in the explorer.
- Click flowchart nodes/edges and disassembly rows for evidence and cross-references; drag nodes, pan and zoom. Graph positions are saved per routine and globally.
- Edit and color-code names, routines, instructions, addresses, bit-field definitions and semantic notes. Your interpretations remain separate from decoder evidence.
- Add roots and explicitly proven dispatch tables; the ROM is rescanned when rooted structure changes.
- Inspect opcode bytes and derived operations, direct and conservatively resolved indexed reads/writes, ROM reads and memory zones.
- Define byte/word/dword tables with dimensions, signedness, scale, bias, units, row/column labels and bit definitions. This is *read-only* calibration visualization; the ROM is not modified.

## Boundaries of static analysis

Decoded control flow, data/code separation and interpreter claims are labeled according to evidence. Many ROM data bytes decode as legal HC11 instructions by chance. Rooted decoding is not a proof that every apparent routine executes on real hardware. Indirect jumps, self-modifying code, bank/ASIC selection, non-constant register addressing, interrupt context and math/units need explicit hypotheses or runtime verification. The GM profile and inherited HAC descriptions do not determine classification.

## Verify

`python -m unittest discover -s tests -v`

Two deliberately synthetic ROMs are provided for development/portability tests; they do not prove equivalence to factory $31 or a different real PCM. The existing `tools/factory_rom_decode.py` in the parent repo remains a separate factory-specific tool; this `studio` package is self-contained.

## Directory

```
ROMFlow_Studio/
├── Launch_ROMFlow_Studio.cmd
├── Launch_ROMFlow_Studio.sh
├── studio/           Python opcode scanner, CFG, access analysis, web server
├── static/           HTML/CSS/JavaScript interactive graphical UI
├── profiles/         Optional hardware/calibration annotation profiles
├── tests/            Backend, project persistence and fixture tests
├── examples/         Synthetic fixture images
└── workspace/        Local autosave, excluded from Git
```

## User manual

The 10-page [ROMFlow Studio User Manual (PDF)](docs/ROMFlow_Studio_User_Manual_v0.2.pdf) covers first launch, navigation, interactive flow graphs, annotation conventions, calibration definitions, memory and SCI tracing, portable `.romflow` save/reopen, practical workflows, troubleshooting and shortcuts.

## HC11 auto-reasoning (experimental)

The **Auto Insights** tab runs a *conservative abstract interpreter* over established reachable opcodes. It tracks known A/B/D/X/Y/SP values through immediate loads, ROM reads, arithmetic, indexed addressing, ABX, transfers, stack operations, and control-flow joins. Unknown RAM, peripheral I/O, call side effects and conflicting branch values remain unknown. The instruction inspector shows register states **before and after** each opcode, including evidence for inferred indexed addresses. Findings propose routine roles, ROM data references and candidate relocatable HC11 SCI register blocks; they **never silently rewrite the ROM, assert calibration units, or promote unrooted bytes to code**. This is static interpretation, not a cycle-accurate emulator. Treat proposed hardware bases and routine meanings as reviewable hypotheses.

## PCM/mask-specific knowledge packs

Select the correct PCM and mask from the header before interpreting an image. The profile does not rewrite the original BIN or automatically import annotations from another ROM. The analyzer uses profile *executable address ranges* to reject impossible fallthroughs, false dispatchers, and low-address filler decoded as code. Runs of 24 or more bytes of FF padding are not promoted to rooted code; individual FF opcodes remain legal. Unmatched masks use the cautious family template or Generic HC11. Source-provided tables are added only by **Calibration hints**, and must be checked against raw ROM bytes.

| Profile | Evidence and scope | Known execution region |
|---|---|---|
| 16197427 / $31 (BMHM) | Hash-verified BMHM ROM, $7100 reset program, $7A85 scheduler and source-hinted tables | $7100–$FFFF |
| 16197427 / BHDC | User BHDC ROMFlow export SHA d412d163…; $7B85 *candidate*, not force-rooted; mask unverified | $7100–$FFFF (family constraint, verify) |
| 16197427 / $0E | Hardware-family only; no BMHM table locations imported | $4000–$FFFF (broad, conservative) |
| 16147060 / $D8 BAMW | User-provided HAC_BAMW.src: calibration $8000, algorithm $A000, SCI at $1000; actual BIN not supplied | $A000–$FFFF |
| 16147060 / $85 | Hardware-family only; not asserted equal to BAMW | $8000–$FFFF (broad, conservative) |

**Important:** The BAMW listing marks byte $8008 as $D8, the SCI vector $FFD6 as $EDB3, and reset vector $FFFE as $F1BA, but these are listing-derived statements until verified against the target BIN. BHDC is a 7427 image, not a 7060. SHA-based identity recommendations are exact and never guessed from filenames alone. Previously saved projects remain compatible; select the appropriate profile manually if they were saved as Generic HC11.

## Hardware/mask compatibility correction

- **16197427:** compatible masks **$0D, $0E, $31, $E6**. BHDC is a 7427 calibration ID, not a PCM hardware model.
- **16147060:** supports **$85 and $D8** on the same PCM hardware. The uploaded BAMW source describes $D8 specifically.

These profile choices share PCM hardware assumptions while retaining separate ROM/calibration evidence. 7427 $0D and $E6 begin as conservative family-level profiles, without borrowing $31 table locations.
