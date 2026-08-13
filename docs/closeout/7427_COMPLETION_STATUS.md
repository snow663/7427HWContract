# 7427 Completion Status

## Primary target

```text
PCM: 16197427
mask: $31
BCC/object: BMHM
raw target BIN: 31/BMHM.BIN
BIN size: 65536 bytes
SHA-256: 6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
```

## Current status

| Category | Current | Status |
|---|---:|---|
| Algorithm extraction | **100%** | **FROZEN** |
| Scheduler/lifecycle | **100%** | **FROZEN** |
| Diagnostics/failsafe | **100%** | **FROZEN** |
| Calibration/tuning | **100%** | **FROZEN** |
| V1 software-facing hardware contract | **100%** | **FROZEN FOR FIRST ENGINE-CONTROL SCOPE** |
| Physical endpoint confirmation | **0%** | **DEFERRED VALIDATION / FUTURE NATIVE-DRIVER WORK** |
| Replacement-OS implementation | **18%** | **ACTIVE; PRE-ASSEMBLY PLANNING GATE NOW FIRST** |
| Complete runnable replacement | **0%** | **AFTER PLANNING + TARGET-LINKED BUILD** |

## V1 architecture decision

The first replacement uses preserved GM software-to-hardware command behavior instead of requiring complete electrical characterization first:

```text
custom control algorithms
→ semantic requests
→ compatibility/arbitration layer
→ preserved GM command islands
→ existing 7427 hardware
```

Authority:

- `docs/contracts/PRESERVED_OUTPUT_DRIVER_ISLANDS.md`
- `source/replacement_os/hal/gm_output_islands.asm`

Current command-island state:

```text
Fuel synchronous     LOCKED ABI + PORTED
Fuel asynchronous    LOCKED ABI + PORTED
IAC                   LOCKED ABI + PORTED
Fuel pump             LOCKED ABI + PORTED
Spark/EST             LOCKED ABI; complete rolling-state port pending
MIL                   DEFERRED
Unused I/O            DEFERRED
```

The preserved command-island module is not currently called by the engine-off runtime.

## Replacement OS currently implemented

```text
semantic runtime ABI
actuator-disabled safe initialization
6.25 ms semantic scheduler / 16-segment counter
REF event ingestion and dropout-safe state
key-off/shutdown semantic states
calibration-validity gate
semantic command arbitration
read-only TPS/MAP/O2/coolant/MAT/battery acquisition paths
read-only REF-period handoff
24-byte semantic debug frame builder with checksum
preserved fuel sync/async, IAC and pump command-island module
```

Important files:

- `source/replacement_os/include/runtime_abi.inc`
- `source/replacement_os/core/safe_runtime.asm`
- `source/replacement_os/core/debug_frame.asm`
- `source/replacement_os/hal/HAL_API.md`
- `source/replacement_os/hal/adc_read.asm`
- `source/replacement_os/hal/ref_read.asm`
- `source/replacement_os/hal/gm_output_islands.asm`

## Pre-assembly planning gate

Before additional target assembly/integration work, freeze five implementation plans:

```text
1. V1 calibration / XDF exposure matrix
2. V1 telemetry / ADX matrix
3. V1 module interface matrix
4. V1 ROM/RAM memory layout
5. V1 build/version manifest
```

Calibration/XDF rule:

```text
every tuner-facing control must have
  a semantic ID
  engineering units/range
  one documented intended effect
  explicit non-effects
  owning algorithm/module
  matching ADX observability where practical
```

The new calibration model is intentionally designed around useful tuning intent, not around exposing every stock calibration byte.

The XDF and ADX must derive from the same frozen semantic/calibration and telemetry definitions used by firmware so names, scaling, addresses, and live-data meaning cannot silently drift.

This planning gate is now the immediate project milestone. Do not continue assembling the target image until these interfaces are defined well enough that implementation becomes mechanical rather than architectural guesswork.

## Following major gate: first target-linked engine-off observability image

After the pre-assembly planning gate is frozen, build the first target-linked engine-off image.

Success means:

```text
custom reset/startup executes on the 7427
custom scheduler runs continuously
read-only sensor sampling runs through the clean ABI
REF/DRP period is visible during cranking
debug/ALDL transport emits the defined semantic telemetry
lifecycle, validity, RPM and requested-control state are observable
all production-output permissions remain disabled
preserved output-command islands remain uncalled
```

The complete spark/EST island remains the next major output module after the engine-off observability milestone.
