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
| Replacement-OS implementation | **18%** | **ACTIVE** |
| Complete runnable replacement | **0%** | **NEXT MAJOR GATE** |

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

## Next major gate: first target-linked engine-off observability image

This is now the highest-value milestone.

Success means:

```text
custom reset/startup executes on the 7427
custom 6.25 ms scheduler runs continuously
watchdog/reset path remains stable
read-only sensor sampling runs through the clean ABI
REF/DRP period is visible during cranking
debug/ALDL transport emits the semantic snapshot frame
lifecycle, validity, RPM and requested-control state are observable
all production-output permissions remain disabled
preserved output-command islands remain uncalled
```

Work required to reach that gate:

```text
target reset/vector/startup integration
processor/timer initialization
real SCI/ALDL debug byte transport
scheduler integration of ADC sampling
REF event integration
validated/substituted semantic sensor layer
link/ORG/memory layout and ROM build
static verification that output-command islands remain unreachable
```

The complete spark/EST island is the next major output module, but it is not required to achieve the engine-off observability gate.
