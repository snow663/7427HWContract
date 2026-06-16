# SUBSYSTEM_ISOLATION_INDEX_TEST

## Scope

Static test definition for subsystem isolation after write-target and dispatcher indexing.

The artifact must summarize:

```text
fuel_compact_3FCE
fuel_stock_output_driver
spark_stock_handoff
spark_custom_writer
iac_stock_driver
iac_custom_writer
whole_rom_write_sweep
dispatcher_reverse_map
```

## Required output files

```text
tools/build_subsystem_isolation_index.py
docs/contracts/SUBSYSTEM_ISOLATION_INDEX.md
maps/contracts/subsystem_isolation_index.csv
```

## Required fields

```text
subsystem_key
current_route
current_decision
hardware_sinks_or_state
preservation_status
bench_status
implementation_permission
blocked_conditions
must_implement
may_ignore_after_proof
must_preserve_if_stock_driver
dispatcher_dependency
next_required_proof
notes
```

## Required gate preservation

The index must keep these decisions unchanged:

```text
fuel_compact_3FCE = active_bench_route
fuel_stock_output_driver = incomplete_continue_3FCE_bench_route
spark_stock_handoff = accepted_static_route_after_contract_proof
spark_custom_writer = blocked_bench_required
iac_stock_driver = contract_defined_preservation_not_proven
iac_custom_writer = blocked_bench_required
```

## Non-relaxation clause

This artifact must not:

```text
create runtime ASM
permit deleting variables without network proof
mark fuel/IAC preservation accepted
mark bench proofs passed
relax fuel $3FCE bench gates
allow SLICE-1
allow custom spark/IAC hardware writers
```
