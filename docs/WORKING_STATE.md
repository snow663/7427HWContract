# Working State

This repository is the working directory for the 7427 hardware-contract and replacement-OS project. Git history is the version record.

## Current primary target

```text
PCM: 16197427
mask: $31
BCC/object: BMHM
raw target BIN: 31/BMHM.BIN from supplied 31.zip
BIN size: 65536 bytes
SHA-256: 6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
working executable source: source/31/BMHM_HAC_ORG_7100_to_end.asm
```

## Architecture

```text
CALIBRATION
    ↓
CUSTOM CONTROL LOGIC
    ↓
SEMANTIC REQUESTS / ARBITRATION
    ↓
PRESERVED GM COMMAND ISLANDS + READ-ONLY HAL
    ↓
7427 HARDWARE
```

The first-running-engine route preserves the stock software-to-hardware command behavior. Complete electrical characterization is therefore not a prerequisite for the V1 software contract.

## Frozen reverse-engineering status

```text
algorithm extraction           100%
scheduler/lifecycle            100%
diagnostics/failsafe           100%
calibration/tuning             100%
V1 software-facing HW contract 100%
```

Do not reopen these categories unless new executable/ROM evidence materially contradicts them or the retained feature scope is deliberately expanded.

## Current implementation status

```text
physical endpoint confirmation   0%   validation/future native-driver frontier
replacement-OS implementation   18%   active
complete runnable replacement    0%   next major gate
```

## Preserved command islands

Authority:

- `docs/contracts/PRESERVED_OUTPUT_DRIVER_ISLANDS.md`
- `source/replacement_os/hal/gm_output_islands.asm`

Current state:

```text
fuel synchronous   LOCKED + PORTED
fuel async / AE    LOCKED + PORTED
IAC                LOCKED + PORTED
fuel pump          LOCKED + PORTED
spark / EST        ABI LOCKED; complete rolling-state port pending
MIL                deferred
unused I/O         deferred
```

The current safe runtime does not call these output modules.

## Replacement OS components present

- `source/replacement_os/include/runtime_abi.inc`
- `source/replacement_os/core/safe_runtime.asm`
- `source/replacement_os/core/debug_frame.asm`
- `source/replacement_os/hal/HAL_API.md`
- `source/replacement_os/hal/adc_read.asm`
- `source/replacement_os/hal/ref_read.asm`
- `source/replacement_os/hal/gm_output_islands.asm`

Implemented so far:

```text
safe semantic initialization
6.25 ms scheduler / 16-segment counter
REF-event and dropout semantic handling
key-off/shutdown semantic state
calibration-validity gate
semantic command request/arbitration state
read-only ADC acquisition paths
read-only REF-period path
24-byte semantic debug frame builder
preserved fuel/IAC/pump command modules
```

## Current output policy

```text
fuel permission  = FALSE
spark permission = FALSE
IAC permission   = FALSE
pump permission  = FALSE
aux permission   = FALSE
```

That remains the required state for the next target image.

## Next major milestone

**FIRST TARGET-LINKED ENGINE-OFF OBSERVABILITY IMAGE**

Required work:

```text
reset/vector/startup integration
processor/timer initialization
SCI/ALDL debug transport
scheduler-driven ADC sampling
REF event integration
validation/substitution layer
link/ORG/memory layout
ROM build
static check that output islands are not reachable
```

Milestone success condition:

```text
7427 boots custom code
custom scheduler remains stable
sensor values are acquired
REF/DRP is visible during cranking
lifecycle/validity/RPM/request state is emitted over debug transport
all output permissions remain false
no preserved output command module is invoked
```

After that milestone, finish the complete spark/EST preserved island and begin permission-gated output integration one subsystem at a time.
