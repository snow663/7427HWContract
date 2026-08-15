; 7427 replacement OS - single-file ASM11/MiniIDE build
; -----------------------------------------------------
; Target: GM 16197427 / mask $31 / BMHM hardware
;
; PURPOSE:
;   One self-contained source file for MGTEK MiniIDE / ASM11.
;   No INCLUDE files are required to assemble this file.
;
; SOURCE AUTHORITY:
;   This is the flattened MiniIDE convenience form of the modular source tree.
;   The modular files remain the maintainable source authority. When modules
;   change, regenerate/replace this monolithic build rather than editing two
;   independent implementations.
;
; FIRST-IMAGE SAFETY RULE:
;   No production output permission is ever enabled here.
;   No preserved output island is called from the main loop.
;   Unowned interrupts fall into a COP-serviced safe halt.
;
; ===========================================================================
; FLATTENED: include/target_layout.inc
; ===========================================================================

; RAM
RAM_RUNTIME_BASE        EQU     $0000
STACK_TOP               EQU     $03FF
RAM_AUX_BASE            EQU     $0800
RAM_AUX_END             EQU     $08FF

; ROM
ROM_CAL_REGION_BASE     EQU     $4000
ROM_EXEC_BASE           EQU     $7100
ROM_VECTOR_BASE         EQU     $FFC0
ROM_ACTIVE_VECTOR_BASE  EQU     $FFD6
ROM_RESET_VECTOR        EQU     $FFFE
ROM_END                 EQU     $FFFF

; ===========================================================================
; RAM allocation - FLATTENED: include/runtime_abi.inc + hal/hal_ram.inc
; ===========================================================================

        ORG     RAM_RUNTIME_BASE

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
PERMISSION_ENABLED      EQU     $A5

; Sensor validity bits
VALID_TPS               EQU     $01
VALID_MAP               EQU     $02
VALID_COOLANT           EQU     $04
VALID_MAT               EQU     $08
VALID_O2                EQU     $10
VALID_BATTERY           EQU     $20
VALID_REF               EQU     $40
VALID_KNOCK             EQU     $80

DEBUG_FRAME_LENGTH      EQU     24

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

SEM_TPS:                RMB     1
SEM_MAP:                RMB     1
SEM_COOLANT:            RMB     1
SEM_MAT:                RMB     1
SEM_O2:                 RMB     1
SEM_BATTERY:            RMB     1
SEM_RPM_HI:             RMB     1
SEM_RPM_LO:             RMB     1
SEM_KNOCK:              RMB     1

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

PERM_FUEL:              RMB     1
PERM_SPARK:             RMB     1
PERM_IAC:               RMB     1
PERM_PUMP:              RMB     1
PERM_AUX:               RMB     1

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

DRV_IAC_POSITION:       RMB     1
DRV_IAC_STATE:          RMB     1
DRV_PORTD_SHADOW:       RMB     1

DEBUG_SEQUENCE:         RMB     1
DEBUG_HEARTBEAT:        RMB     1
DEBUG_TX_PENDING:       RMB     1
DEBUG_TX_ACTIVE:        RMB     1
DEBUG_TX_LENGTH:        RMB     1
DEBUG_TX_INDEX:         RMB     1
DEBUG_TX_CHECKSUM:      RMB     1
DEBUG_TX_BUFFER:        RMB     DEBUG_FRAME_LENGTH
RUNTIME_STATE_END:

HAL_RAM_BEGIN:
HAL_ADC_TIMEOUT:        RMB     1
HAL_RAM_END:

RAM_ALLOC_END:

; ===========================================================================
; Executable ROM
; ===========================================================================

        ORG     ROM_EXEC_BASE

RESET_ENTRY:
        SEI
        LDS     #STACK_TOP
        JSR     HAL_INIT_PROCESSOR_SAFE

        LDX     #RAM_RUNTIME_BASE
RESET_CLEAR_RAM:
        CLR     0,X
        INX
        CPX     #RAM_ALLOC_END
        BNE     RESET_CLEAR_RAM

        JSR     OS_SAFE_INIT
        JSR     HAL_GM_IAC_STATE_INIT

FIRST_ROM_IDLE_LOOP:
        JSR     HAL_SERVICE_COP
        BRA     FIRST_ROM_IDLE_LOOP

; ===========================================================================
; FLATTENED: hal/init_safe.asm
; ===========================================================================

HC11_RESET_REG_BASE     EQU     $1000
HC11_REG_BASE           EQU     $3000
HC11_TMSK2_OFF          EQU     $24
HC11_BPROT_OFF          EQU     $35
HC11_OPT2_OFF           EQU     $38
HC11_OPTION_OFF         EQU     $39
HC11_COPRST_OFF         EQU     $3A
HC11_INIT_OFF           EQU     $3D

HC11_INIT_RELOCATE      EQU     $03
HC11_OPTION_BOOT        EQU     $B8
HC11_TMSK2_BOOT         EQU     $03
HC11_BPROT_BOOT         EQU     $1B

HAL_INIT_PROCESSOR_SAFE:
        LDX     #HC11_RESET_REG_BASE
        LDAA    #HC11_INIT_RELOCATE
        STAA    HC11_INIT_OFF,X

        LDX     #HC11_REG_BASE
        LDAA    #HC11_OPTION_BOOT
        STAA    HC11_OPTION_OFF,X
        LDAA    #HC11_TMSK2_BOOT
        STAA    HC11_TMSK2_OFF,X
        BCLR    HC11_OPT2_OFF,X,#$20
        LDAA    #HC11_BPROT_BOOT
        STAA    HC11_BPROT_OFF,X
        RTS

HAL_SERVICE_COP:
        LDX     #HC11_REG_BASE
        LDAA    #$55
        STAA    HC11_COPRST_OFF,X
        COMA
        STAA    HC11_COPRST_OFF,X
        RTS

HAL_FATAL_SAFE_LOOP:
        SEI
        JSR     OS_DISABLE_ALL_ACTUATORS
        JSR     OS_ZERO_ALL_COMMANDS
HAL_FATAL_SAFE_LOOP_1:
        JSR     HAL_SERVICE_COP
        BRA     HAL_FATAL_SAFE_LOOP_1

; ===========================================================================
; FLATTENED: core/safe_runtime.asm
; ===========================================================================

OS_SAFE_INIT:
        CLRA
        STAA    SCHED_SEGMENT
        STAA    TICK_6P25_LO
        STAA    TICK_6P25_HI
        STAA    SCHED_OVERRUN
        STAA    CAL_VALID
        STAA    SENSOR_VALID_FLAGS
        STAA    REF_QUAL_COUNT
        STAA    REF_DROPOUT_AGE
        STAA    DEBUG_SEQUENCE
        STAA    DEBUG_HEARTBEAT

        STAA    REQ_FUEL_PW_HI
        STAA    REQ_FUEL_PW_LO
        STAA    REQ_SPARK_HI
        STAA    REQ_SPARK_LO
        STAA    REQ_IAC_TARGET
        STAA    REQ_PUMP
        STAA    REQ_MIL

        STAA    PERM_FUEL
        STAA    PERM_SPARK
        STAA    PERM_IAC
        STAA    PERM_PUMP
        STAA    PERM_AUX

        STAA    CMD_FUEL_PW_HI
        STAA    CMD_FUEL_PW_LO
        STAA    CMD_FUEL_VALID
        STAA    CMD_SPARK_HI
        STAA    CMD_SPARK_LO
        STAA    CMD_SPARK_VALID
        STAA    CMD_IAC_TARGET
        STAA    CMD_IAC_MOTION_VALID
        STAA    CMD_PUMP
        STAA    CMD_PUMP_VALID
        STAA    CMD_MIL
        STAA    CMD_AUX_VALID

        LDAA    #LIFE_KEYON_SAFE
        STAA    LIFE_STATE
        RTS

OS_TICK_6P25MS:
        INC     TICK_6P25_LO
        BNE     OS_TICK_NO_CARRY
        INC     TICK_6P25_HI
OS_TICK_NO_CARRY:
        INC     SCHED_SEGMENT
        LDAA    SCHED_SEGMENT
        ANDA    #$0F
        STAA    SCHED_SEGMENT
        JSR     OS_LIFECYCLE_STEP
        JSR     OS_ARBITRATE_COMMANDS

        LDAA    SCHED_SEGMENT
        CMPA    #$00
        BEQ     OS_SLOT_00
        CMPA    #$04
        BEQ     OS_SLOT_04
        CMPA    #$08
        BEQ     OS_SLOT_08
        CMPA    #$0C
        BEQ     OS_SLOT_0C
        RTS

OS_SLOT_00:
        JSR     OS_VALIDATE_SNAPSHOT
        RTS
OS_SLOT_04:
        JSR     OS_DEBUG_SNAPSHOT_TICK
        RTS
OS_SLOT_08:
        JSR     OS_DROPOUT_AGE_TICK
        RTS
OS_SLOT_0C:
        JSR     OS_VALIDATE_SNAPSHOT
        RTS

OS_REF_EVENT:
        STAA    RAW_REF_PERIOD_HI
        STAB    RAW_REF_PERIOD_LO
        LDAA    SENSOR_VALID_FLAGS
        ORAA    #VALID_REF
        STAA    SENSOR_VALID_FLAGS
        CLR     REF_DROPOUT_AGE
        LDAA    REF_QUAL_COUNT
        CMPA    #$FF
        BEQ     OS_REF_COUNT_SAT
        INCA
        STAA    REF_QUAL_COUNT
OS_REF_COUNT_SAT:
        RTS

OS_DROPOUT_AGE_TICK:
        LDAA    REF_DROPOUT_AGE
        CMPA    #$FF
        BEQ     OS_DROPOUT_AGE_DONE
        INCA
        STAA    REF_DROPOUT_AGE
OS_DROPOUT_AGE_DONE:
        RTS

OS_FORCE_DROPOUT:
        LDAA    #LIFE_DROPOUT_SAFE
        STAA    LIFE_STATE
        LDAA    SENSOR_VALID_FLAGS
        ANDA    #$BF
        STAA    SENSOR_VALID_FLAGS
        CLR     REF_QUAL_COUNT
        JSR     OS_DISABLE_ALL_ACTUATORS
        JSR     OS_ZERO_ALL_COMMANDS
        RTS

OS_KEYOFF_EVENT:
        LDAA    #LIFE_KEYOFF_DELAY
        STAA    LIFE_STATE
        JSR     OS_DISABLE_ALL_ACTUATORS
        JSR     OS_ZERO_ALL_COMMANDS
        RTS

OS_SHUTDOWN_READY:
        LDAA    #LIFE_SHUTDOWN_READY
        STAA    LIFE_STATE
        JSR     OS_DISABLE_ALL_ACTUATORS
        JSR     OS_ZERO_ALL_COMMANDS
        RTS

OS_SET_CAL_VALID:
        LDAA    #BOOL_TRUE
        STAA    CAL_VALID
        RTS

OS_CLEAR_CAL_VALID:
        CLR     CAL_VALID
        JSR     OS_DISABLE_ALL_ACTUATORS
        JSR     OS_ZERO_ALL_COMMANDS
        RTS

OS_REQUEST_FUEL_PW:
        STAA    REQ_FUEL_PW_HI
        STAB    REQ_FUEL_PW_LO
        RTS

OS_REQUEST_SPARK:
        STAA    REQ_SPARK_HI
        STAB    REQ_SPARK_LO
        RTS

OS_REQUEST_IAC_TARGET:
        STAA    REQ_IAC_TARGET
        RTS

OS_REQUEST_PUMP:
        STAA    REQ_PUMP
        RTS

OS_REQUEST_MIL:
        STAA    REQ_MIL
        RTS

OS_VALIDATE_SNAPSHOT:
        LDAA    CAL_VALID
        BNE     OS_VALIDATE_DONE
        JSR     OS_DISABLE_ALL_ACTUATORS
OS_VALIDATE_DONE:
        RTS

OS_LIFECYCLE_STEP:
        LDAA    LIFE_STATE
        CMPA    #LIFE_DROPOUT_SAFE
        BEQ     OS_LIFE_LOCKED
        CMPA    #LIFE_KEYOFF_DELAY
        BEQ     OS_LIFE_LOCKED
        CMPA    #LIFE_SHUTDOWN_READY
        BEQ     OS_LIFE_LOCKED
        RTS
OS_LIFE_LOCKED:
        JSR     OS_DISABLE_ALL_ACTUATORS
        RTS

OS_ARBITRATE_COMMANDS:
        LDAA    PERM_FUEL
        CMPA    #PERMISSION_ENABLED
        BNE     OS_ARB_FUEL_OFF
        LDAA    REQ_FUEL_PW_HI
        STAA    CMD_FUEL_PW_HI
        LDAA    REQ_FUEL_PW_LO
        STAA    CMD_FUEL_PW_LO
        LDAA    #BOOL_TRUE
        STAA    CMD_FUEL_VALID
        BRA     OS_ARB_SPARK
OS_ARB_FUEL_OFF:
        CLR     CMD_FUEL_PW_HI
        CLR     CMD_FUEL_PW_LO
        CLR     CMD_FUEL_VALID

OS_ARB_SPARK:
        LDAA    PERM_SPARK
        CMPA    #PERMISSION_ENABLED
        BNE     OS_ARB_SPARK_OFF
        LDAA    REQ_SPARK_HI
        STAA    CMD_SPARK_HI
        LDAA    REQ_SPARK_LO
        STAA    CMD_SPARK_LO
        LDAA    #BOOL_TRUE
        STAA    CMD_SPARK_VALID
        BRA     OS_ARB_IAC
OS_ARB_SPARK_OFF:
        CLR     CMD_SPARK_HI
        CLR     CMD_SPARK_LO
        CLR     CMD_SPARK_VALID

OS_ARB_IAC:
        LDAA    PERM_IAC
        CMPA    #PERMISSION_ENABLED
        BNE     OS_ARB_IAC_OFF
        LDAA    REQ_IAC_TARGET
        STAA    CMD_IAC_TARGET
        LDAA    #BOOL_TRUE
        STAA    CMD_IAC_MOTION_VALID
        BRA     OS_ARB_PUMP
OS_ARB_IAC_OFF:
        CLR     CMD_IAC_MOTION_VALID

OS_ARB_PUMP:
        LDAA    PERM_PUMP
        CMPA    #PERMISSION_ENABLED
        BNE     OS_ARB_PUMP_OFF
        LDAA    REQ_PUMP
        STAA    CMD_PUMP
        LDAA    #BOOL_TRUE
        STAA    CMD_PUMP_VALID
        BRA     OS_ARB_AUX
OS_ARB_PUMP_OFF:
        CLR     CMD_PUMP
        CLR     CMD_PUMP_VALID

OS_ARB_AUX:
        LDAA    PERM_AUX
        CMPA    #PERMISSION_ENABLED
        BNE     OS_ARB_AUX_OFF
        LDAA    REQ_MIL
        STAA    CMD_MIL
        LDAA    #BOOL_TRUE
        STAA    CMD_AUX_VALID
        RTS
OS_ARB_AUX_OFF:
        CLR     CMD_MIL
        CLR     CMD_AUX_VALID
        RTS

OS_DISABLE_ALL_ACTUATORS:
        CLR     PERM_FUEL
        CLR     PERM_SPARK
        CLR     PERM_IAC
        CLR     PERM_PUMP
        CLR     PERM_AUX
        RTS

OS_ZERO_ALL_COMMANDS:
        CLR     CMD_FUEL_PW_HI
        CLR     CMD_FUEL_PW_LO
        CLR     CMD_FUEL_VALID
        CLR     CMD_SPARK_HI
        CLR     CMD_SPARK_LO
        CLR     CMD_SPARK_VALID
        CLR     CMD_IAC_MOTION_VALID
        CLR     CMD_PUMP
        CLR     CMD_PUMP_VALID
        CLR     CMD_MIL
        CLR     CMD_AUX_VALID
        RTS

OS_DEBUG_SNAPSHOT_TICK:
        INC     DEBUG_SEQUENCE
        LDAA    DEBUG_HEARTBEAT
        EORA    #$01
        STAA    DEBUG_HEARTBEAT
        RTS

; ===========================================================================
; FLATTENED: core/debug_frame.asm
; ===========================================================================

OS_DEBUG_BUILD_FRAME:
        LDAA    DEBUG_TX_PENDING
        BNE     OS_DEBUG_BUILD_DONE
        LDAA    DEBUG_TX_ACTIVE
        BNE     OS_DEBUG_BUILD_DONE

        CLR     DEBUG_TX_CHECKSUM
        LDX     #DEBUG_TX_BUFFER

        LDAA    #$A5
        JSR     OS_DEBUG_APPEND_A
        LDAA    #$31
        JSR     OS_DEBUG_APPEND_A
        LDAA    #DEBUG_FRAME_LENGTH
        JSR     OS_DEBUG_APPEND_A
        LDAA    DEBUG_SEQUENCE
        JSR     OS_DEBUG_APPEND_A
        LDAA    LIFE_STATE
        JSR     OS_DEBUG_APPEND_A
        LDAA    SENSOR_VALID_FLAGS
        JSR     OS_DEBUG_APPEND_A
        LDAA    RAW_TPS
        JSR     OS_DEBUG_APPEND_A
        LDAA    RAW_MAP
        JSR     OS_DEBUG_APPEND_A
        LDAA    RAW_COOLANT
        JSR     OS_DEBUG_APPEND_A
        LDAA    RAW_MAT_INV
        JSR     OS_DEBUG_APPEND_A
        LDAA    RAW_O2
        JSR     OS_DEBUG_APPEND_A
        LDAA    RAW_BATTERY
        JSR     OS_DEBUG_APPEND_A
        LDAA    RAW_REF_PERIOD_HI
        JSR     OS_DEBUG_APPEND_A
        LDAA    RAW_REF_PERIOD_LO
        JSR     OS_DEBUG_APPEND_A
        LDAA    SEM_RPM_HI
        JSR     OS_DEBUG_APPEND_A
        LDAA    SEM_RPM_LO
        JSR     OS_DEBUG_APPEND_A
        LDAA    REQ_FUEL_PW_HI
        JSR     OS_DEBUG_APPEND_A
        LDAA    REQ_FUEL_PW_LO
        JSR     OS_DEBUG_APPEND_A
        LDAA    REQ_SPARK_HI
        JSR     OS_DEBUG_APPEND_A
        LDAA    REQ_SPARK_LO
        JSR     OS_DEBUG_APPEND_A
        LDAA    REQ_IAC_TARGET
        JSR     OS_DEBUG_APPEND_A

        CLRB
        LDAA    PERM_FUEL
        CMPA    #PERMISSION_ENABLED
        BNE     OS_DEBUG_PERM_SPARK
        ORAB    #$01
OS_DEBUG_PERM_SPARK:
        LDAA    PERM_SPARK
        CMPA    #PERMISSION_ENABLED
        BNE     OS_DEBUG_PERM_IAC
        ORAB    #$02
OS_DEBUG_PERM_IAC:
        LDAA    PERM_IAC
        CMPA    #PERMISSION_ENABLED
        BNE     OS_DEBUG_PERM_PUMP
        ORAB    #$04
OS_DEBUG_PERM_PUMP:
        LDAA    PERM_PUMP
        CMPA    #PERMISSION_ENABLED
        BNE     OS_DEBUG_PERM_AUX
        ORAB    #$08
OS_DEBUG_PERM_AUX:
        LDAA    PERM_AUX
        CMPA    #PERMISSION_ENABLED
        BNE     OS_DEBUG_PERM_DONE
        ORAB    #$10
OS_DEBUG_PERM_DONE:
        TBA
        JSR     OS_DEBUG_APPEND_A
        LDAA    DEBUG_HEARTBEAT
        JSR     OS_DEBUG_APPEND_A

        LDAA    DEBUG_TX_CHECKSUM
        NEGA
        STAA    0,X
        LDAA    #DEBUG_FRAME_LENGTH
        STAA    DEBUG_TX_LENGTH
        CLR     DEBUG_TX_INDEX
        LDAA    #BOOL_TRUE
        STAA    DEBUG_TX_PENDING
        INC     DEBUG_SEQUENCE
OS_DEBUG_BUILD_DONE:
        RTS

OS_DEBUG_APPEND_A:
        STAA    0,X
        ADDA    DEBUG_TX_CHECKSUM
        STAA    DEBUG_TX_CHECKSUM
        INX
        RTS

; ===========================================================================
; FLATTENED: hal/adc_read.asm
; ===========================================================================

HC11_PORTD              EQU     $3008
HC11_ADCTL              EQU     $3030
HC11_ADR1               EQU     $3031
HC11_ADR2               EQU     $3032
HC11_ADR3               EQU     $3033
HC11_ADR4               EQU     $3034
ADC_COMPLETE            EQU     $80
ADC_MUX_MASK            EQU     $38

HAL_ADC_SET_MUX_SELECT:
        PSHB
        TAB
        LDAA    HC11_PORTD
        ANDA    #$C7
        ASLB
        ASLB
        ASLB
        ANDB    #ADC_MUX_MASK
        ABA
        STAA    HC11_PORTD
        PULB
        RTS

HAL_ADC_START_WAIT:
        CLR     HAL_ADC_TIMEOUT
        STAA    HC11_ADCTL
        LDAB    #12
HAL_ADC_WAIT_LOOP:
        BRSET   HC11_ADCTL,#ADC_COMPLETE,HAL_ADC_WAIT_DONE
        DECB
        BNE     HAL_ADC_WAIT_LOOP
        LDAA    #$01
        STAA    HAL_ADC_TIMEOUT
HAL_ADC_WAIT_DONE:
        RTS

HAL_SAMPLE_PRIMARY_ADC:
        LDAA    #$14
        JSR     HAL_ADC_START_WAIT
        LDAA    HAL_ADC_TIMEOUT
        BNE     HAL_PRIMARY_DONE
        LDAA    HC11_ADR1
        STAA    RAW_TPS
        LDAA    HC11_ADR2
        STAA    RAW_MAP
        LDAA    HC11_ADR3
        STAA    RAW_O2
HAL_PRIMARY_DONE:
        RTS

HAL_SAMPLE_COOLANT_BATTERY:
        LDAA    #$01
        JSR     HAL_ADC_SET_MUX_SELECT
        LDAA    #$11
        JSR     HAL_ADC_START_WAIT
        LDAA    HAL_ADC_TIMEOUT
        BNE     HAL_COOL_BATT_DONE
        LDAA    HC11_ADR3
        STAA    RAW_COOLANT
        LDAA    HC11_ADR4
        STAA    RAW_BATTERY
HAL_COOL_BATT_DONE:
        RTS

HAL_SAMPLE_MAT:
        LDAA    #$04
        JSR     HAL_ADC_SET_MUX_SELECT
        LDAA    #$01
        JSR     HAL_ADC_START_WAIT
        LDAA    HAL_ADC_TIMEOUT
        BNE     HAL_MAT_DONE
        LDAA    HC11_ADR4
        COMA
        STAA    RAW_MAT_INV
HAL_MAT_DONE:
        RTS

HAL_SAMPLE_BATTERY_STOCK_MODE:
        LDAA    #$02
        JSR     HAL_ADC_SET_MUX_SELECT
        LDAA    #$01
        JSR     HAL_ADC_START_WAIT
        LDAA    HAL_ADC_TIMEOUT
        BNE     HAL_BATT_DONE
        LDAA    HC11_ADR4
        STAA    RAW_BATTERY
HAL_BATT_DONE:
        RTS

; ===========================================================================
; FLATTENED: hal/ref_read.asm
; ===========================================================================

ASIC_REF_PERIOD         EQU     $3FC0

HAL_CAPTURE_REF_PERIOD:
        LDD     ASIC_REF_PERIOD
        JSR     OS_REF_EVENT
        RTS

; ===========================================================================
; FLATTENED: hal/gm_output_islands.asm
; Linked for compatibility proof; NOT called by the first ROM idle loop.
; ===========================================================================

GM_EFI_SYNC_PW          EQU     $3FCE
GM_EFI_ASYNC_PW         EQU     $3FF2
GM_ASIC_IO_D            EQU     $3FFC
GM_CPU_PORT_D           EQU     $3062
GM_FUEL_PUMP_LATCH      EQU     $306F

HAL_GM_DELAY_RTS:
        RTS

HAL_GM_FUEL_SYNC_COMMIT:
        LDAA    PERM_FUEL
        CMPA    #PERMISSION_ENABLED
        BNE     HAL_GM_FUEL_SYNC_OFF
        LDAA    CMD_FUEL_VALID
        BEQ     HAL_GM_FUEL_SYNC_OFF
        LDD     CMD_FUEL_PW_HI
        STD     GM_EFI_SYNC_PW
        RTS
HAL_GM_FUEL_SYNC_OFF:
        CLRA
        CLRB
        STD     GM_EFI_SYNC_PW
        JSR     HAL_GM_DELAY_RTS
        RTS

HAL_GM_FUEL_ASYNC_COMMIT:
        LDAA    PERM_FUEL
        CMPA    #PERMISSION_ENABLED
        BNE     HAL_GM_FUEL_ASYNC_DONE
        LDAA    CMD_FUEL_ASYNC_VALID
        BEQ     HAL_GM_FUEL_ASYNC_DONE
        LDD     CMD_FUEL_ASYNC_PW_HI
        BEQ     HAL_GM_FUEL_ASYNC_DONE
        STD     GM_EFI_ASYNC_PW
        JSR     HAL_GM_DELAY_RTS
        LDD     GM_ASIC_IO_D
        ANDA    #$FB
        JSR     HAL_GM_DELAY_RTS
        STD     GM_ASIC_IO_D
        ORAA    #$04
        JSR     HAL_GM_DELAY_RTS
        STD     GM_ASIC_IO_D
HAL_GM_FUEL_ASYNC_DONE:
        RTS

HAL_GM_PUMP_COMMIT:
        LDAA    PERM_PUMP
        CMPA    #PERMISSION_ENABLED
        BNE     HAL_GM_PUMP_OFF
        LDAA    CMD_PUMP_VALID
        BEQ     HAL_GM_PUMP_OFF
        LDAA    CMD_PUMP
        BEQ     HAL_GM_PUMP_OFF
        LDAA    #$FF
        STAA    GM_FUEL_PUMP_LATCH
        RTS
HAL_GM_PUMP_OFF:
        CLRA
        STAA    GM_FUEL_PUMP_LATCH
        RTS

HAL_GM_IAC_STATE_INIT:
        CLRA
        STAA    DRV_IAC_POSITION
        STAA    DRV_IAC_STATE
        LDAA    #$40
        STAA    DRV_PORTD_SHADOW
        RTS

HAL_GM_IAC_COMMIT:
        LDAA    PERM_IAC
        CMPA    #PERMISSION_ENABLED
        BNE     HAL_GM_IAC_DISABLE
        LDAA    CMD_IAC_MOTION_VALID
        BEQ     HAL_GM_IAC_DISABLE
        LDAB    DRV_IAC_STATE
        ORAB    #$10
        LDAA    DRV_IAC_POSITION
        CMPA    CMD_IAC_TARGET
        BNE     HAL_GM_IAC_NOT_EQUAL
        ANDB    #$FE
        BRA     HAL_GM_IAC_MERGE
HAL_GM_IAC_NOT_EQUAL:
        BCC     HAL_GM_IAC_BRANCH_91DF
        ANDB    #$FE
        BRSET   DRV_IAC_STATE,#$01,HAL_GM_IAC_MERGE
        INCA
        BRA     HAL_GM_IAC_POSITION_CHANGED
HAL_GM_IAC_BRANCH_91DF:
        ORAB    #$01
        BRCLR   DRV_IAC_STATE,#$01,HAL_GM_IAC_MERGE
        DECA
HAL_GM_IAC_POSITION_CHANGED:
        STAA    DRV_IAC_POSITION
        BRSET   DRV_IAC_STATE,#$0C,HAL_GM_IAC_PHASE_BOTH_SAME
        BRCLR   DRV_IAC_STATE,#$0C,HAL_GM_IAC_PHASE_BOTH_SAME
        BITB    #$01
        BNE     HAL_GM_IAC_TOGGLE_B
        BRA     HAL_GM_IAC_TOGGLE_A
HAL_GM_IAC_PHASE_BOTH_SAME:
        BITB    #$01
        BNE     HAL_GM_IAC_TOGGLE_A
HAL_GM_IAC_TOGGLE_B:
        EORB    #$04
        BRA     HAL_GM_IAC_MERGE
HAL_GM_IAC_TOGGLE_A:
        EORB    #$08
        BRA     HAL_GM_IAC_MERGE
HAL_GM_IAC_DISABLE:
        LDAB    DRV_IAC_STATE
        ANDB    #$EF
HAL_GM_IAC_MERGE:
        STAB    DRV_IAC_STATE
        SEI
        LDAA    DRV_PORTD_SHADOW
        ANDA    #$E3
        ANDB    #$1C
        ABA
        STAA    DRV_PORTD_SHADOW
        STAA    GM_CPU_PORT_D
        CLI
        RTS

ROM_CODE_END:

; ===========================================================================
; HC11 vectors
; ===========================================================================

        ORG     ROM_VECTOR_BASE

        FDB     HAL_FATAL_SAFE_LOOP     ; $FFC0
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFC2
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFC4
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFC6
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFC8
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFCA
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFCC
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFCE
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFD0
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFD2
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFD4
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFD6 SCI
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFD8 SPI
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFDA PA input edge
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFDC PA overflow
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFDE timer overflow
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFE0 TOC5
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFE2 TOC4
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFE4 TOC3
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFE6 TOC2
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFE8 TOC1
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFEA TIC3
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFEC TIC2
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFEE TIC1
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFF0 RTI
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFF2 IRQ
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFF4 XIRQ
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFF6 SWI
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFF8 illegal opcode
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFFA COP timeout
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFFC clock fail
        FDB     RESET_ENTRY             ; $FFFE external reset

; End 7427_rom_miniide.asm
