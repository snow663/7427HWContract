; 7427 replacement OS semantic ABI
; --------------------------------
; This include defines only semantic RAM/API state.
; It MUST NOT contain HC11 peripheral addresses, ASIC addresses,
; connector pins, or stock RAM mailbox addresses.
;
; Hardware addresses belong only in source/replacement_os/hal/.

; Lifecycle states
LIFE_RESET              EQU     $00
LIFE_KEYON_SAFE         EQU     $01
LIFE_CRANK_READY        EQU     $02
LIFE_RUN_READY          EQU     $03
LIFE_DROPOUT_SAFE       EQU     $04
LIFE_KEYOFF_DELAY       EQU     $05
LIFE_SHUTDOWN_READY     EQU     $06

; Boolean values
BOOL_FALSE              EQU     $00
BOOL_TRUE               EQU     $01

; Permission values
PERMISSION_DISABLED     EQU     $00
PERMISSION_ENABLED      EQU     $A5     ; deliberate non-boolean unlock token

; Sensor validity bits for SENSOR_VALID_FLAGS
VALID_TPS               EQU     $01
VALID_MAP               EQU     $02
VALID_COOLANT           EQU     $04
VALID_MAT               EQU     $08
VALID_O2                EQU     $10
VALID_BATTERY           EQU     $20
VALID_REF               EQU     $40
VALID_KNOCK             EQU     $80

; Runtime semantic state.
; Placement is intentionally not fixed here; linker/ORG policy owns placement.

RUNTIME_STATE_BEGIN:

LIFE_STATE:             RMB     1
SCHED_SEGMENT:          RMB     1
TICK_6P25_LO:           RMB     1
TICK_6P25_HI:           RMB     1
SCHED_OVERRUN:          RMB     1
CAL_VALID:              RMB     1
SENSOR_VALID_FLAGS:     RMB     1
REF_QUAL_COUNT:         RMB     1
REF_DROPOUT_AGE:        RMB     1

; HAL-owned raw snapshot copied/consumed semantically by core.
RAW_TPS:                RMB     1
RAW_MAP:                RMB     1
RAW_COOLANT:            RMB     1
RAW_MAT_INV:            RMB     1
RAW_O2:                 RMB     1
RAW_BATTERY:            RMB     1
RAW_KNOCK_COUNT_HI:     RMB     1
RAW_KNOCK_COUNT_LO:     RMB     1
RAW_REF_PERIOD_HI:      RMB     1
RAW_REF_PERIOD_LO:      RMB     1

; Validated/substituted semantic snapshot.
SEM_TPS:                RMB     1
SEM_MAP:                RMB     1
SEM_COOLANT:            RMB     1
SEM_MAT:                RMB     1
SEM_O2:                 RMB     1
SEM_BATTERY:            RMB     1
SEM_RPM_HI:             RMB     1
SEM_RPM_LO:             RMB     1
SEM_KNOCK:              RMB     1

; Algorithm-side semantic requests.
REQ_FUEL_PW_HI:         RMB     1
REQ_FUEL_PW_LO:         RMB     1
REQ_FUEL_ASYNC_PW_HI:   RMB     1
REQ_FUEL_ASYNC_PW_LO:   RMB     1
REQ_FUEL_ASYNC_PENDING: RMB     1
REQ_SPARK_HI:           RMB     1
REQ_SPARK_LO:           RMB     1
REQ_IAC_TARGET:         RMB     1
REQ_PUMP:               RMB     1
REQ_MIL:                RMB     1

; Explicit physical-output permissions.
PERM_FUEL:              RMB     1
PERM_SPARK:             RMB     1
PERM_IAC:               RMB     1
PERM_PUMP:              RMB     1
PERM_AUX:               RMB     1

; Arbitrated HAL commands. HAL must ignore a command if its matching
; permission-valid flag is false.
CMD_FUEL_PW_HI:         RMB     1
CMD_FUEL_PW_LO:         RMB     1
CMD_FUEL_VALID:         RMB     1
CMD_FUEL_ASYNC_PW_HI:   RMB     1
CMD_FUEL_ASYNC_PW_LO:   RMB     1
CMD_FUEL_ASYNC_VALID:   RMB     1
CMD_SPARK_HI:           RMB     1
CMD_SPARK_LO:           RMB     1
CMD_SPARK_VALID:        RMB     1
CMD_IAC_TARGET:         RMB     1
CMD_IAC_MOTION_VALID:   RMB     1
CMD_PUMP:               RMB     1
CMD_PUMP_VALID:         RMB     1
CMD_MIL:                RMB     1
CMD_AUX_VALID:          RMB     1

; Preserved-output-driver private software state.
; These are RAM variables only; core algorithms must not depend on them.
; The HAL owns their interpretation.
DRV_IAC_POSITION:       RMB     1
DRV_IAC_STATE:          RMB     1
DRV_PORTD_SHADOW:       RMB     1

; Debug/observability state.
DEBUG_SEQUENCE:         RMB     1
DEBUG_HEARTBEAT:        RMB     1

RUNTIME_STATE_END:
