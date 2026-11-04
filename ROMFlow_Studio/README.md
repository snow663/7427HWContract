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
