# FULL_ROM_WRITE_TARGET_SWEEP_TEST

## Scope

Static test definition for the full-ROM write/mutation inventory.

The artifact must generate a whole-disassembly write sweep, not a hand-curated target list.

## Required files

```text
tools/build_full_rom_write_target_sweep.py
maps/generated/full_rom_write_target_sweep.csv
docs/analysis/FULL_ROM_WRITE_TARGET_SWEEP.md
```

## Required CSV columns

```text
pc
routine_label
opcode
mnemonic
operand_text
write_class
target_raw
target_resolved
target_symbol
address_class
width
bitmask
x_base
y_base
index_resolution_status
value_source
nearby_branch_context
dispatcher_context
candidate_role
confidence
notes
```

## Required behavior

The builder must:

```text
sweep the full source file
include stores, bit mutations, clears, inc/dec, complement/negate, shifts, and rotates
record direct writes
record indexed writes
resolve indexed writes when base tracking allows
retain unresolved indexed writes
classify address region conservatively
classify candidate role conservatively
not drop rows simply because target role is unknown
```

## Non-relaxation clause

The sweep must not:

```text
create runtime ASM
mark hardware proof passed
mark bench proof passed
relax SLICE-1 gates
permit custom hardware writers
mark any target removable without downstream read/use proof
replace PER_TARGET_DOSSIER_INDEX
```

## Expected baseline

The initial local generated CSV contains `2215` write/mutation rows. A later source update may change this count, but any change must be reviewed as a static-analysis delta, not a hardware finding.
