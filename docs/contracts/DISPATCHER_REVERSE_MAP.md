# DISPATCHER_REVERSE_MAP

## Purpose

Reverse-map indirect dispatch and table-driven control flow so subsystem ownership can be inferred from both selector variables and landing routines.

This exists because the code may not flow linearly as:

```text
routine A -> routine B -> routine C
```

It may flow as:

```text
state bits / math result / mode byte
-> index
-> dispatch table
-> computed jump/call
-> subsystem routine
```

This is a static analysis artifact only. It does not implement runtime ASM, change scheduling, or relax hardware-output gates.

## Required map fields

```text
dispatcher_pc
dispatcher_label
index_source
index_math
mask_shift_add_operations
table_address
entry_width
entry_count
entry_index
entry_value
resolved_target
target_label
target_write_targets
candidate_subsystem
confidence
notes
```

## Known dispatcher seeds

```text
7A4F:
  major-loop dispatcher
  selector = L0002 & 0x0F
  table = $7A85
  action = JSR 0,X

FAA5:
  output-control block dispatcher
  selector/control block = L038E
  action = JSR 0,X
  note = likely ALDL/output-control path, not production subsystem scheduling
```

## Forward/reverse analysis rule

Forward:

```text
which variable/index selects a dispatch entry?
```

Reverse:

```text
which entry lands in which routine, and what write targets does that routine own?
```

## Isolation rule

A routine reached only through a dispatcher must be kept reachable if it owns hardware, safety, scheduler, rolling-state, or preserved-driver side effects.

Do not delete routines by linear call-tree assumptions alone.
