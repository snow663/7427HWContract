# Source Inputs

Place source/disassembly/bin inputs here.

Current source used for static pass v0.2:

```text
31_HAC_from_ORG_7100_to_end_NOWRAP.asm
```

Local file size from the current session: about `730 KiB`.

This source should be committed through normal Git or split into address-range chunks if connector upload is impractical.

Suggested source layout:

```text
source/31/BMHM_HAC_ORG_7100_to_end.asm
source/31/metadata.md
source/31/import_notes.md
```

Required source metadata:

```text
mask: $31
bin/object: BMHM
processor: MC68HC11-family
register relocation: INIT -> $30, HC11 regs at $3000
analysis base: ORG $7100 through vector/end region
```
