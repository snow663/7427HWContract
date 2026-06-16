# FULL_ROM_WRITE_TARGET_SWEEP

## Purpose

Generate the actual whole-disassembly write/mutation inventory for the 7427 / `$31` source.

This artifact moves beyond the seed/high-value `WRITE_TARGET_NETWORK_INDEX` map by extracting every detected write/mutation site first, before subsystem classification.

Static analysis only: no runtime ASM, no hardware-output gate relaxation, no bench proof claim, and no `SLICE-1` authorization.

## Source and output

```text
source: source/31/BMHM_HAC_ORG_7100_to_end.asm
output: maps/generated/full_rom_write_target_sweep.csv
rows observed in local generation: 2215
```

The generated CSV was produced locally from the same source and is available as an external artifact when connector size prevents committing the full 617 KB CSV directly.

## Write classes swept

```text
STAA STAB STD STS STX STY
BSET BCLR
CLR INC DEC COM NEG
ASL/LSL LSR ROL ROR
```

Accumulator-only shifts/rotates are not treated as memory writes unless a memory operand exists.

## CSV columns

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

## Address classification

```text
internal_ram
hardware_register_region_30xx
asic_hardware_region_3fxx
absolute_memory_or_table
unknown
```

## Indexed write behavior

The builder tracks simple immediate `LDX #$nnnn` and `LDY #$nnnn` bases in a linear pass. Indexed writes are marked:

```text
resolved_indexed
unresolved_indexed
direct
```

Unresolved indexed writes remain in the CSV. They are not discarded.

## Interpretation rule

A write proves only that a target is mutated. It does not prove that target is important or removable.

Importance must be determined by later per-target dossiers using reads, downstream consumers, hardware reachability, dispatcher involvement, preserved-driver involvement, and safety-gate participation.

## Non-relaxation

This sweep does not change current route decisions:

```text
fuel_compact_3FCE: active_bench_route
fuel_stock_output_driver: incomplete_continue_3FCE_bench_route
spark_stock_handoff: accepted_static_route_after_contract_proof
spark_custom_writer: blocked_bench_required
iac_stock_driver: contract_defined_preservation_not_proven
iac_custom_writer: blocked_bench_required
```

Fuel remains on the compact `$3FCE` SLICE-0 bench path. `FUEL-001` through `FUEL-004` still block `SLICE-1` under that route.
