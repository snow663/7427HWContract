# 7427 Completion Status

## Current primary target

```text
PCM: 16197427
mask: $31
BCC/object: BMHM
raw target BIN: 31/BMHM.BIN from supplied 31.zip
BIN size: 65536 bytes
SHA-256: 6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
```

Percentages have explicit scope and must not be reduced because a later hardware/bench category remains incomplete.

## Fixed completion table

| Category | Current | Scope / completion definition | Status |
|---|---:|---|---|
| **algorithm extraction** | **100%** | Semantic production-control relationships for retained fuel, spark/knock, crank/warmup/afterstart, AE/PE/DFCO/closed-loop fuel, and idle/IAC. Physical hardware behavior excluded. | **FROZEN** |
| **scheduler/lifecycle** | **100%** | Reset/init, heartbeat/dispatch, REF/DRP lifecycle, crank/run/stall/dropout, key-off delayed shutdown, overrun/watchdog responsibilities. | **FROZEN** |
| **diagnostics/failsafe** | **100%** | Material validation, substitution, inhibit and safe-state behavior that changes production control. OEM DTC packing/reporting excluded unless behavior-changing. | **FROZEN** |
| **calibration/tuning** | **100%** | Source extraction/ownership plus direct 11,916-record audit against the actual 64 KiB BMHM BIN, reviewed production corrections, width/address/alignment review, BIN-numeric-authority rule. | **FROZEN** |
| **software-facing HW contract** | **92%** | CPU/ASIC/timer/register ownership and software paths substantially mapped; normalized endpoint/HAL inventory now active work. | ACTIVE |
| **physical endpoint confirmation** | **0%** | Requires measured stimulus/command-to-pin evidence. Existing bench result rows remain `not_run`. | BENCH FRONTIER |
| **replacement-OS implementation** | **5%** | Existing skeleton/minimal fuel writer/bench harness are infrastructure only; integrated engine-off safe runtime is now the next implementation target. | ACTIVE |
| **complete runnable replacement** | **0%** | Requires target boot, endpoint gates, controlled actuator enable, first start, closed-loop/learning and shutdown/dropout validation. | NOT STARTED |

## Calibration audit closeout

Authority artifact:

- `docs/closeout/7427_CALIBRATION_BIN_AUDIT_CLOSEOUT.md`
- `maps/closeout/calibration_bin_production_correction_overlay.csv`

Audit result:

```text
records audited:            11,916
exact matches:              11,700
value mismatches:              120
source-width errors:             96
outside-BIN records:              0
odd-address FDB reviews:        212
label-width review rows:        138
```

Reviewed production-impact discrepancies:

```text
$4146/$4148/$414A: HAC FF FE vs BMHM FF F5 → use BIN FF F5
$4C80/$4C81 duplicate labels in second DFCO table → correct addresses $4C90/$4C91
second $4EDB FCB 60 record → stale/phantom; executable indexes table from $4EDC
$50ED: HAC 00 vs BMHM D0 → use BIN D0
```

The remaining hard discrepancies are in optional `$31` remote-broadcast/service layout material or excluded transmission calibration and do not block standalone production engine-control reconstruction.

## Extraction phase gate

```text
algorithm             100  FROZEN
scheduler/lifecycle   100  FROZEN
diagnostics/failsafe  100  FROZEN
calibration/tuning    100  FROZEN
```

The reverse-engineering closeout gate is therefore **passed**.

No frozen extraction category should be reopened unless new executable/ROM evidence materially contradicts it or the retained feature scope is deliberately expanded.

## Current active phase

Proceed directly with:

```text
normalized endpoint SETUP contracts
→ bench TEST-CONFIRM records
→ engine-off safe runtime
→ sensor acquisition/validity
→ IAC permission-gated bring-up
→ spark/EST permission-gated bring-up
→ injector permission-gated bring-up
→ controlled first engine start
```

A complete algorithm never authorizes an actuator by itself.
