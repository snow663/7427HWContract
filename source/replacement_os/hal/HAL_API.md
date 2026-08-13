# 7427 Replacement OS HAL API

## Rule

Only files under `source/replacement_os/hal/` may contain:

```text
HC11 peripheral addresses
relocated CPU register addresses
$3Fxx ASIC addresses
L30xx/L31xx/L32xx hardware-register symbols
board output-latch addresses
connector/pin-specific polarity logic
```

No production algorithm, lifecycle module, diagnostic module, scheduler, or command-arbitration module may contain those items.

## Required HAL responsibilities

### Initialization

```text
HAL_INIT_PROCESSOR_SAFE
HAL_INIT_TIMERS_SAFE
HAL_INIT_ADC_SAFE
HAL_INIT_SCI_DEBUG_SAFE
HAL_FORCE_BOARD_OUTPUTS_INACTIVE
```

The initial implementation may omit an unproven peripheral rather than guessing its register sequence.

### Input acquisition

```text
HAL_SAMPLE_TPS_RAW        -> RAW_TPS
HAL_SAMPLE_MAP_RAW        -> RAW_MAP
HAL_SAMPLE_COOLANT_RAW    -> RAW_COOLANT
HAL_SAMPLE_MAT_RAW        -> RAW_MAT_INV
HAL_SAMPLE_O2_RAW         -> RAW_O2
HAL_SAMPLE_BATTERY_RAW    -> RAW_BATTERY
HAL_READ_KNOCK_COUNT      -> RAW_KNOCK_COUNT_HI/LO
HAL_REF_EVENT             -> calls OS_REF_EVENT with raw period in D
```

A HAL function reports raw hardware state only. Calibration scaling, plausibility, substitution, and control logic stay above the HAL.

### Debug transport

```text
HAL_DEBUG_INIT
HAL_DEBUG_TX_BYTE
HAL_DEBUG_RX_BYTE
HAL_DEBUG_SERVICE
```

Debug transport may be enabled before actuators if it cannot write production outputs.

### Output commit

No output function may act unless the matching `CMD_*_VALID` flag is true.

Planned APIs:

```text
HAL_COMMIT_FUEL
HAL_COMMIT_SPARK
HAL_COMMIT_IAC
HAL_COMMIT_PUMP
HAL_COMMIT_AUX
HAL_COMMIT_SHUTDOWN
```

Each function must also have its own endpoint proof gate before it is included in the runnable image.

## Initial implementation rule

The first engine-off image shall contain either:

1. no physical actuator commit functions at all; or
2. stubs that immediately return without touching hardware.

It may contain read-only sensor acquisition and ALDL/debug transport after those endpoints have passed their own setup/test-confirm gates.

## Known software-facing mappings to implement later

These are source-proven software locations, not physical connector proof:

```text
ADC control/result window: relocated HC11 $3030-$3034
TPS raw:                 $3031 selected/multi result -> L00A6
MAP raw:                 $3032 normal multi result -> L082E
O2 raw:                  $3033 normal multi result -> L01D5
coolant raw:             selected ADC result -> L00A5
MAT raw:                 selected ADC result -> inverted L0230
battery:                 selected ADC result -> L00A7 / L0055 path
REF period:              $3FC0 -> semantic REF period
knock count:             relocated pulse-accumulator/count path near $3203/$3204
fuel PW handoff:          $3FCE
fuel pump output latch:   L306F
IAC shadow/latch:         L004C -> L3062
spark handoff:            $3FE8/$3FE6/$3FF6/$3FDC; $3FEC->$3FE4 candidate sync
```

These addresses may appear in HAL implementation files only.

## Output permissions

The semantic core owns permissions and arbitration. HAL owns no policy that can secretly bypass them.

```text
PERM_FUEL  + CMD_FUEL_VALID
PERM_SPARK + CMD_SPARK_VALID
PERM_IAC   + CMD_IAC_MOTION_VALID
PERM_PUMP  + CMD_PUMP_VALID
PERM_AUX   + CMD_AUX_VALID
```

If a command-valid flag is false, the HAL must select a proven inactive behavior rather than replay a stale prior command.

## No stale-command rule

On reset, dropout, key-off, invalid calibration, scheduler fault, or permission loss:

```text
fuel  -> no pulse / zero intent
spark -> no EST authority / safe intent
IAC   -> no motion command
pump  -> off
aux   -> inactive unless a separately proven safety requirement says otherwise
```

The physical encoding of each inactive state is endpoint/HAL evidence, not algorithm policy.
