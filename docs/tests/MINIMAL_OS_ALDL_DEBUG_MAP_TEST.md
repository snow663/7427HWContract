# Minimal OS ALDL Debug Map Test

## Goal

Verify that the ALDL/debug map defines observation visibility for bench proof, first-run validation, and live troubleshooting without implementing ALDL packet format, mode handlers, serial ISR changes, runtime code, or write authority.

This test validates planning only.

## Required Files

```text
docs/contracts/MINIMAL_OS_ALDL_DEBUG_MAP.md
maps/contracts/minimal_os_aldl_debug_map.csv
tools/build_minimal_os_aldl_debug_map.py
```

## Required Static Checks

| Test | Expected |
|---|---|
| planning-only | no ALDL ASM, packet implementation, mode handler, serial ISR, or runtime code created |
| fuel PW raw | `$3FCE/$3FCF` raw counts represented |
| fuel PW ms | `EFI_PW_ms = counts / 65.536` represented |
| fuel gates | fuel enable/no-fuel gate and DFCO zero gate represented |
| fuel first-run inputs | BPW candidates, deadtime, low-PW correction, battery, RPM, MAP, TPS, CTS, target AFR represented |
| spark bench probes | `$3FE8/$3FE6/$3FF6/$3FDC` debug-visible but bench-gated |
| spark conversion | desired spark, `L01FD`, `L01EE`, `L004F bit0`, `L0201`, `L005F/L0060` represented |
| spark status | bypass/EST, engine-running, first DRP, EST monitor, EST error, prior sample represented |
| IAC proof values | `L0007`, `L0008`, position error, `L0009`, `L000A`, `L004C`, `L3062`, `L4EB0`, `L00A7`, `L003E bit2`, cadence represented |
| scheduler/boot/watchdog | boot stage, REF valid, first period, RPM valid, crank/run, counters, watchdog, dropout, output-safe, bench hook represented |
| units/conversions | display units and conversions explicit where known |
| no write authority | debug exposure does not permit writes |
| exclusions | trans/EGR/EVAP/emissions/stock mode-word baggage excluded |
| unknowns | unknown debug values listed, not guessed |
| stock ALDL baggage | not carried solely because stock ALDL exposed it |

## Command

```bash
python tools/build_minimal_os_aldl_debug_map.py \
  --state-vars maps/contracts/minimal_os_state_variables.csv \
  --out-md docs/contracts/MINIMAL_OS_ALDL_DEBUG_MAP.md \
  --out-csv maps/contracts/minimal_os_aldl_debug_map.csv
```

## Required Conversion Checks

```text
EFI_PW_ms = counts / 65.536
spark_degrees = count * 90 / 256
L00A7 volts = L00A7 / 10
IAC position = raw counts until physical direction is bench-proven
```

## Required Write-Authority Guardrails

```text
Debug exposure of $3FE8/$3FE6/$3FF6/$3FDC does not permit spark writes.
Debug exposure of L3062/L004C does not permit IAC writes.
Debug exposure of $3FCE does not permit nonzero fuel unless fuel gates permit it.
ALDL visibility is observational only.
```

## Required Debug Classes

The CSV must use controlled debug classes only:

```text
fuel_debug
spark_debug
iac_debug
sensor_debug
scheduler_debug
boot_debug
watchdog_debug
hardware_shadow_debug
bench_probe
calibration_reference
excluded_stock_aldl
unknown
```

## Pass Criteria

```text
PASS:
  debug map is planning-only.
  no ALDL packet/mode/serial code appears.
  fuel $3FCE raw and ms views are represented.
  spark output/rolling candidates are visible but bench-gated.
  IAC actual/desired/phase/enable/shadow values are visible but bench-gated.
  scheduler/boot/dropout/watchdog values are represented.
  conversions and display units are explicit where known.
  debug exposure does not grant write authority.
  trans/EGR/EVAP/emissions/stock mode-word baggage are excluded.
  unknown debug values remain visible.
```

## Fail / Rework Criteria

```text
REWORK:
  ALDL packet format or serial ISR code appears.
  debug visibility is treated as write authority.
  spark handoff candidates are marked implementation-ready.
  IAC L3062/L004C exposure is treated as writer permission.
  $3FCE exposure bypasses fuel gates.
  excluded stock ALDL baggage is carried forward.
  unknown debug values are silently assigned.
```

## Next Decision Point

After this pass, the planning stack is strong enough for either:

```text
bench proof package
first minimal fuel-only runnable slice
```

The fuel-only slice is the only plausible implementation path before spark and IAC output bench gates are closed.
