# WRITE_TARGET_NETWORK_INDEX

## Purpose

Whole-ROM static write-target network index for the 7427 / `$31` source.

This artifact changes the analysis model from subsystem names to write targets. It exists to answer:

```text
What does every mutated RAM / hardware / state target participate in?
```

It is a static analysis artifact only. It does not create runtime ASM, relax bench gates, or prove hardware behavior.

## Covered write classes

The builder sweeps mutation-style operations:

```text
STAA STAB STD STS STX STY
BSET BCLR
CLR INC DEC COM NEG
ASL/LSL LSR ROL ROR
```

Accumulator-only shifts/rotates are not treated as memory writes unless an operand target exists.

## Indexed write handling

Indexed forms are retained and resolved when possible:

```text
STD $1E,X
STAA $FA,Y
BSET $20,X,#$04
```

The builder tracks simple immediate `LDX #$nnnn` / `LDY #$nnnn` bases in a linear pass. Unresolved indexed targets stay in the map as unresolved targets instead of being discarded.

## Target dossier model

Each target dossier records:

```text
target_symbol
target_address
write_count
first_pc
first_routine_label
representative_instruction
write_widths
bitmasks
value_sources
x_y_bases_seen
call_contexts
nearby_branch_conditions_sample
candidate_role
confidence
write_sites_sample
notes
```

The map is a triage index, not a delete list.

## Role classification

Candidate roles include:

```text
hardware sink
final command
intermediate calculation
shadow copy
diagnostic mirror
state latch
rolling state
mode flag
safety gate
dispatcher selector
unknown
```

## High-value target seed list

The following targets must stay under review until their read/write network and downstream use are proven:

```text
L3FCE   fuel pulsewidth hardware sink
L3FE8   spark stock handoff candidate
L3FE6   spark stock handoff candidate
L3FDC   spark rolling/state candidate
L3FF6   spark EST fall / rolling anchor candidate
L3FEC   spark monitor/mirror source candidate
L3FE4   spark monitor/mirror destination candidate
L3062   IAC output/phase candidate
L3060   IAC output/phase candidate
L3FFC   IAC / output port candidate
L303A   COP/watchdog hardware candidate
```

## Deletion rule

Do not delete a variable because it looks unimportant.

Delete only after its read/write network proves it does not feed:

```text
hardware
safety
dispatch
scheduler state
rolling state
preserved stock driver input
preserved stock driver side effect
```
