# WRITE_TARGET_NETWORK_INDEX

## Purpose

Whole-ROM static sweep of write targets. This starts from mutations instead of subsystem names so that RAM, hardware, shadows, mode flags, safety gates, rolling state, and dispatcher selectors can be separated by read/write network context.

This is a static analysis artifact only. It does not implement runtime ASM, relax bench gates, or prove hardware behavior.

## Source

- source file: `source/31/BMHM_HAC_ORG_7100_to_end.asm`
- target dossier rows emitted: `786`

## Write op coverage

- `ASL`: 11
- `BCLR`: 37
- `BSET`: 33
- `CLR`: 31
- `COM`: 2
- `DEC`: 14
- `INC`: 13
- `ROL`: 14
- `ROR`: 9
- `STAA`: 365
- `STAB`: 76
- `STD`: 148
- `STX`: 27
- `STY`: 6

## Candidate role counts

- `RAM state/calculation/shadow`: 449
- `ROM/data? unexpected write target`: 114
- `unknown`: 109
- `mode flag/safety gate/state latch`: 70
- `hardware register/ASIC/CPU peripheral`: 24
- `local stack save`: 10
- `hardware sink/state:spark stock handoff`: 5
- `hardware sink/state:IAC candidate`: 3
- `hardware sink:watchdog/COP`: 1
- `hardware sink:fuel pulsewidth`: 1

## High-value target dossier seeds

| target | writes observed | role seed | note |
|---|---:|---|---|
| `L3FCE` | 4 | `hardware sink:fuel pulsewidth` | known EFI pulsewidth command sink |
| `L3FE8` | 1 | `hardware sink/state:spark stock handoff` | spark stock handoff / rolling-state candidate |
| `L3FE6` | 1 | `hardware sink/state:spark stock handoff` | spark stock handoff / rolling-state candidate |
| `L3FDC` | 2 | `hardware sink/state:spark stock handoff` | spark stock handoff / rolling-state candidate |
| `L3FF6` | 2 | `hardware sink/state:spark stock handoff` | spark stock handoff / rolling-state candidate |
| `L3FEC` | 0 | `not written in sweep` | no write row emitted |
| `L3FE4` | 1 | `hardware sink/state:spark stock handoff` | spark stock handoff / rolling-state candidate |
| `L3062` | 4 | `hardware sink/state:IAC candidate` | IAC port/phase/enable/park candidate |
| `L3060` | 3 | `hardware sink/state:IAC candidate` | IAC port/phase/enable/park candidate; ROM state-flow contexts only; see factory_indexed_flow.csv |
| `L3FFC` | 13 | `hardware sink/state:IAC candidate` | IAC port/phase/enable/park candidate |
| `L303A` | 10 | `hardware sink:watchdog/COP` | COP reset register candidate |

## Indexing limitations

- Reviewed embedded data is excluded using `maps/structure/reviewed_source_regions.csv`, checked against the source hash.
- Indexed writes are resolved only when the linear pass can see a recent immediate `LDX`/`LDY` base.
- Branch context is nearby static context, not a full path-sensitive proof.
- Read counts are symbol-token observations and are intended as triage hints, not complete dataflow proof.
- A target is not safe to delete merely because its role is unknown or low confidence.

## Deletion rule

Do not delete a variable because it looks unimportant. Delete only after the read/write network proves it does not feed hardware, safety, dispatch, or a preserved stock driver.

