# WRITE_TARGET_NETWORK_INDEX

## Purpose

Whole-ROM static sweep of write targets. This starts from mutations instead of subsystem names so that RAM, hardware, shadows, mode flags, safety gates, rolling state, and dispatcher selectors can be separated by read/write network context.

This is a static analysis artifact only. It does not implement runtime ASM, relax bench gates, or prove hardware behavior.

## Source

- source file: `/mnt/data/source.asm`
- target dossier rows emitted: `793`

## Write op coverage

- `ASL`: 11
- `BCLR`: 34
- `BSET`: 35
- `CLR`: 31
- `COM`: 2
- `DEC`: 27
- `INC`: 19
- `LSR`: 1
- `ROL`: 13
- `ROR`: 11
- `STAA`: 359
- `STAB`: 75
- `STD`: 145
- `STX`: 25
- `STY`: 5

## Candidate role counts

- `RAM state/calculation/shadow`: 458
- `ROM/data? unexpected write target`: 197
- `mode flag/safety gate/state latch`: 72
- `hardware register/ASIC/CPU peripheral`: 42
- `unknown`: 14
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
| `L3060` | 2 | `hardware sink/state:IAC candidate` | IAC port/phase/enable/park candidate |
| `L3FFC` | 13 | `hardware sink/state:IAC candidate` | IAC port/phase/enable/park candidate |
| `L303A` | 10 | `hardware sink:watchdog/COP` | COP reset register candidate |

## Indexing limitations

- Indexed writes are resolved only when the linear pass can see a recent immediate `LDX`/`LDY` base.
- Branch context is nearby static context, not a full path-sensitive proof.
- Read counts are symbol-token observations and are intended as triage hints, not complete dataflow proof.
- A target is not safe to delete merely because its role is unknown or low confidence.

## Deletion rule

Do not delete a variable because it looks unimportant. Delete only after the read/write network proves it does not feed hardware, safety, dispatch, or a preserved stock driver.

