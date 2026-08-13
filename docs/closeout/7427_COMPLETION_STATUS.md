# 7427 Completion Status

## Current primary target

```text
PCM: 16197427
mask: $31
BCC/object: BMHM
target BIN: BMHM_95_C-G-K_Truck_7_4TBI_4l80.bin
```

This document is the fixed status view for the closeout workflow. Percentages have explicit scope and must not be reduced because a later hardware/bench category remains incomplete.

## Source-authority audit

The project File Library contains older documents named `7427_Full_Control_Model.docx` and `16196395_PCM_Architecture_Custom_OS_Developer_Guide.docx`.

They are **not canonical evidence for the current numeric/variant closeout**:

- `7427_Full_Control_Model.docx` explicitly identifies its model as `$0E`.
- `16196395_PCM_Architecture_Custom_OS_Developer_Guide.docx` is explicitly for the 16196395/BJKZ `$0E` target.

They remain useful as historical architecture/HAL-boundary corroboration, especially the conclusion that board-level pin/polarity questions are a bench frontier. They do not override `$31` BMHM executable/ROM evidence.

The `$31` tuning handbook is supporting calibration/tuning context only. It also states that BIN/mask/XDF verification precedes tuning, consistent with the current raw-BIN audit gate.

## Fixed completion table

| Category | Current | Scope / completion definition | Status |
|---|---:|---|---|
| **algorithm extraction** | **100%** | Semantic production-control math/state relationships for retained fuel, spark/knock, crank/warmup/afterstart, AE/PE/DFCO/closed-loop fuel, and idle/IAC including control-law composition. Physical hardware behavior excluded. | **FROZEN** |
| **scheduler/lifecycle** | **100%** | Reset/init ordering, 6.25 ms heartbeat and 16-segment production cadence, event/foreground relationship, REF/DRP lifecycle, crank/run qualification, stall/dropout, key-off delayed shutdown, overrun/watchdog responsibilities. Physical power-control pin effect excluded. | **FROZEN** |
| **diagnostics/failsafe** | **100%** | Material validation/substitution/inhibit behavior that changes fuel/spark/idle/lifecycle. OEM DTC packing/reporting/bookkeeping excluded unless it changes behavior. | **FROZEN** |
| **calibration/tuning** | **98%** | Source extraction and semantic ownership complete; production calibration manifest complete; byte/word source-vs-actual-BMHM-BIN audit and correction overlay still required. | **BLOCKED: RAW TARGET BIN NOT CURRENTLY RETRIEVABLE** |
| **software-facing HW contract** | **92%** | CPU/ASIC/timer/register ownership and software command/acquisition paths are substantially mapped for fuel, spark, IAC, REF/timing, SCI/ALDL, watchdog/init. Remaining work is converting retained endpoints into one normalized HAL/API inventory and closing a few hardware register semantic details that do not require physical claims. | ACTIVE AFTER CALIBRATION FREEZE |
| **physical endpoint confirmation** | **0%** | Requires actual connector/pin/electrical stimulus/measurement PASS records. Existing fuel bench result package is explicitly `not_run`; software proof does not count toward this percentage. | NOT STARTED / BENCH GATED |
| **replacement-OS implementation** | **5%** | Existing skeleton/minimal fuel writer/bench harness count only as infrastructure. No engine-off integrated safe runtime with scheduler + sensor snapshot + validity + ALDL + arbitration exists yet. | NOT YET PHASE-GATED |
| **complete runnable replacement** | **0%** | Requires integrated OS booting on target hardware, endpoint gates passed, controlled actuator enable, first start, closed-loop/learning validation, and safe shutdown/dropout. | NOT STARTED |

## Why software-facing HW contract is not 100%

This category is intentionally separate from physical endpoint confirmation.

Already strong/static:

```text
HC11 relocation and timer register ownership
full hardware-access/register maps
ASIC register contract inventory
REF period/count software interface
fuel timer/output scheduling contracts
spark timing conversion/handoff boundary
IAC actual/desired/phase/output-shadow path
SCI/ALDL architecture
COP/watchdog service interface
boot/init register sequencing
```

Still required for 100% software-facing contract:

```text
one normalized HAL endpoint/API table for every retained production input/output
explicit semantic ownership for sensor acquisition channels and conversions
explicit semantic ownership for retained auxiliary outputs (fuel pump, MIL, A/C/fan only if kept)
final software-side classification of any shared ASIC mirror/ack register that must be preserved
safe init/default/permission state for every retained HAL endpoint
```

None of those require claiming connector pins, physical polarity, or load current.

## Why physical endpoint confirmation is 0%

The repo contains bench plans and structured result files, but the current fuel bench result artifact explicitly initializes all proof rows as `not_run`. A physical percentage cannot be earned from disassembly, source comments, board inference, or a prepared test plan.

Physical completion begins only when records contain actual applied stimulus/command and measured response with a confirmed pin/connector.

## Current phase gate

```text
algorithm             100  FROZEN
scheduler/lifecycle   100  FROZEN
diagnostics/failsafe  100  FROZEN
calibration/tuning     98  WAITING ONLY FOR RAW-BIN AUDIT
```

Therefore the project must **not** reopen algorithm/scheduler/diagnostic disassembly and must **not** call the bench shell a replacement OS.

The next action is strictly:

```text
obtain/re-expose exact raw BMHM 64 KiB BIN
→ run tools/audit_calibration_against_bin.py
→ review correction overlay
→ set calibration/tuning = 100% and FREEZE
→ start normalized endpoint setup/test-confirm records
→ implement engine-off actuator-disabled safe runtime
```

## Freeze discipline

A frozen 100% category reopens only when:

1. new executable/ROM evidence directly contradicts a material semantic conclusion; or
2. the user explicitly expands the production feature scope.

A hardware pin uncertainty, electrical measurement, or bench failure does not lower algorithm/scheduler/diagnostic completion. It changes the software-facing-HW or physical-endpoint category instead.
