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

## Current implementation strategy

For the retained first-running-engine configuration, the HAL uses **preserved GM software output-command islands** rather than requiring a native electrical driver rewrite.

```text
custom algorithm
→ semantic request
→ arbitration/permission
→ compatibility adapter
→ preserved GM command sequence
→ existing 7427 hardware
```

Physical output polarity, transistor topology, current, and ASIC internal electrical behavior are therefore not prerequisites for the first-running-engine route.

Canonical output-island contract:

```text
docs/contracts/PRESERVED_OUTPUT_DRIVER_ISLANDS.md
maps/contracts/preserved_output_driver_islands.csv
source/replacement_os/hal/gm_output_islands.asm
```

Unused I/O is deferred expansion work.

## Required HAL responsibilities

### Initialization

```text
HAL_INIT_PROCESSOR_SAFE
HAL_INIT_TIMERS_SAFE
HAL_INIT_ADC_SAFE
HAL_INIT_SCI_DEBUG_SAFE
HAL_FORCE_BOARD_OUTPUTS_INACTIVE
```

The initial implementation may omit an unneeded peripheral rather than guessing its register sequence.

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

## Retained output APIs

Every output routine must obey the clean runtime permission and command-valid state. The HAL may not create its own hidden enable path.

### Fuel synchronous

```text
HAL_GM_FUEL_SYNC_COMMIT
```

BMHM TBI final command boundary:

```text
CMD_FUEL_PW -> stock-compatible 16-bit count -> $3FCE
```

Stock no-fuel semantic is `$0000 -> $3FCE`.

### Fuel asynchronous / AE pulse

```text
HAL_GM_FUEL_ASYNC_COMMIT
```

Preserved hardware tail:

```text
final async PW -> $3FF2
$3FFC bit2 clear/write -> set/write trigger
```

The compatibility layer preserves the stock `LF3ED` call/return delays. Fuel mathematics and low-PW/bias correction remain above this hardware tail.

### IAC

```text
HAL_GM_IAC_STATE_INIT
HAL_GM_IAC_COMMIT
```

Preserves the stock `L91C2-L920D` direction/phase behavior and `L004C -> $3062` output semantics using private clean-driver state rather than requiring stock RAM addresses.

### Fuel pump

```text
HAL_GM_PUMP_COMMIT
```

Preserves stock command bytes:

```text
$FF -> $306F asserted
$00 -> $306F cleared
```

Prime/run/stall/shutdown timing belongs to lifecycle logic above the HAL.

### Spark / EST

Spark ABI is locked, but the full port remains intentionally atomic:

```text
final signed stock-format spark
→ stock REF/latency/dwell/rolling conversion
→ $3FE8/$3FE6/$3FDC/$3FF6
→ preserve $3FEC->$3FE4 sync/ack tail where required
```

Do not emit a partial direct spark writer. Port the complete rolling-state/dwell handoff island before making `HAL_COMMIT_SPARK` executable.

## Current physical-proof policy

There are now two distinct development routes:

```text
PRESERVED GM COMMAND ISLAND:
  complete software-command behavior must be preserved
  electrical polarity/current/topology may be deferred

NATIVE NEW HARDWARE WRITER:
  physical endpoint proof remains required before engine-runnable use
```

The first-running-engine configuration uses the preserved-GM-command route for retained outputs.

Bench work still has value as validation, but it is no longer a prerequisite for understanding or recreating the electronics when the complete stock command behavior is retained.

## Known software-facing mappings

```text
ADC control/result window: relocated HC11 $3030-$3034
TPS raw:                 $3031 selected/multi result -> L00A6 semantic equivalent
MAP raw:                 $3032 normal multi result -> L082E semantic equivalent
O2 raw:                  $3033 normal multi result -> L01D5 semantic equivalent
coolant raw:             selected ADC result -> L00A5 semantic equivalent
MAT raw:                 selected ADC result -> inverted L0230 semantic equivalent
battery:                 selected ADC result -> L00A7 / L0055 semantic equivalent
REF period:              $3FC0 -> semantic REF period
knock count:             relocated pulse-accumulator/count path near $3203/$3204
fuel sync PW:            $3FCE
fuel async PW/trigger:   $3FF2 / $3FFC bit2 sequence
fuel pump:               $306F ($FF asserted / $00 cleared)
IAC:                     stock step/phase -> port-D shadow -> $3062
spark handoff:           $3FE8/$3FE6/$3FF6/$3FDC; retain $3FEC->$3FE4 opaque sync/ack
```

These addresses may appear in HAL implementation files only.

## Output permissions

```text
PERM_FUEL  + CMD_FUEL_VALID
PERM_SPARK + CMD_SPARK_VALID
PERM_IAC   + CMD_IAC_MOTION_VALID
PERM_PUMP  + CMD_PUMP_VALID
PERM_AUX   + CMD_AUX_VALID
```

The current engine-off runtime does not create the `PERMISSION_ENABLED` token by itself.

## No stale-command rule

On reset, dropout, key-off, invalid calibration, scheduler fault, or permission loss:

```text
fuel sync  -> stock zero-PW command
fuel async -> no trigger
spark      -> no executable spark commit until complete island exists
iac        -> stock driver-enable bit cleared / no commanded step
pump       -> stock off byte
aux        -> inactive unless separately retained
```

No physical electrical interpretation is needed to preserve those stock software semantics.
