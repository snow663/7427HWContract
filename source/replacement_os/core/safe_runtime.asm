; 7427 replacement OS - engine-off safe runtime core
; --------------------------------------------------
; HARD RULE: this module contains NO hardware addresses.
; All physical access belongs in source/replacement_os/hal/.
;
; This core is intentionally incapable of enabling production actuators.
; It provides reset state, 6.25 ms semantic scheduling, lifecycle/dropout
; handling, request storage, safe arbitration, and debug heartbeat state.
;
; Include before assembly:
;   source/replacement_os/include/runtime_abi.inc

; --------------------------------------------------
; OS_SAFE_INIT
; --------------------------------------------------
; Called after processor/HAL-safe initialization.
; Leaves every production actuator permission disabled.
;
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

        ; Algorithm requests start at zero.
        STAA    REQ_FUEL_PW_HI
        STAA    REQ_FUEL_PW_LO
        STAA    REQ_SPARK_HI
        STAA    REQ_SPARK_LO
        STAA    REQ_IAC_TARGET
        STAA    REQ_PUMP
        STAA    REQ_MIL

        ; Physical permissions MUST boot false.
        STAA    PERM_FUEL
        STAA    PERM_SPARK
        STAA    PERM_IAC
        STAA    PERM_PUMP
        STAA    PERM_AUX

        ; Arbitrated outputs MUST boot invalid/inactive.
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

; --------------------------------------------------
; OS_TICK_6P25MS
; --------------------------------------------------
; Called by the HAL-owned base timer ISR or equivalent test harness.
; This reproduces the semantic heartbeat without owning timer registers.
;
OS_TICK_6P25MS:
        INC     TICK_6P25_LO
        BNE     OS_TICK_NO_CARRY
        INC     TICK_6P25_HI
OS_TICK_NO_CARRY:

        INC     SCHED_SEGMENT
        LDAA    SCHED_SEGMENT
        ANDA    #$0F
        STAA    SCHED_SEGMENT

        ; Every tick: lifecycle safety and command arbitration.
        JSR     OS_LIFECYCLE_STEP
        JSR     OS_ARBITRATE_COMMANDS

        ; Four lightweight semantic service slots within the 16-segment cycle.
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

; --------------------------------------------------
; OS_REF_EVENT
; --------------------------------------------------
; ABI: D = new raw REF/DRP period supplied by HAL/event layer.
; Does not write ignition or injector hardware.
;
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

; --------------------------------------------------
; OS_DROPOUT_AGE_TICK
; --------------------------------------------------
; The exact production timeout is calibration/lifecycle owned later.
; This engine-off safe core only saturates the age counter. A harness or
; later lifecycle module may call OS_FORCE_DROPOUT when its threshold is met.
;
OS_DROPOUT_AGE_TICK:
        LDAA    REF_DROPOUT_AGE
        CMPA    #$FF
        BEQ     OS_DROPOUT_AGE_DONE
        INCA
        STAA    REF_DROPOUT_AGE
OS_DROPOUT_AGE_DONE:
        RTS

; --------------------------------------------------
; OS_FORCE_DROPOUT
; --------------------------------------------------
; Semantic missing-REF/fault transition. Reasserts all actuator locks.
;
OS_FORCE_DROPOUT:
        LDAA    #LIFE_DROPOUT_SAFE
        STAA    LIFE_STATE

        LDAA    SENSOR_VALID_FLAGS
        ANDA    #$BF              ; clear VALID_REF
        STAA    SENSOR_VALID_FLAGS

        CLR     REF_QUAL_COUNT
        JSR     OS_DISABLE_ALL_ACTUATORS
        JSR     OS_ZERO_ALL_COMMANDS
        RTS

; --------------------------------------------------
; OS_KEYOFF_EVENT
; --------------------------------------------------
; Semantic key-off event. Physical power-hold action remains HAL-gated.
;
OS_KEYOFF_EVENT:
        LDAA    #LIFE_KEYOFF_DELAY
        STAA    LIFE_STATE
        JSR     OS_DISABLE_ALL_ACTUATORS
        JSR     OS_ZERO_ALL_COMMANDS
        RTS

; --------------------------------------------------
; OS_SHUTDOWN_READY
; --------------------------------------------------
; Called by lifecycle logic only after the frozen delayed-shutdown condition
; is satisfied. Still does not touch physical power-control hardware.
;
OS_SHUTDOWN_READY:
        LDAA    #LIFE_SHUTDOWN_READY
        STAA    LIFE_STATE
        JSR     OS_DISABLE_ALL_ACTUATORS
        JSR     OS_ZERO_ALL_COMMANDS
        RTS

; --------------------------------------------------
; OS_SET_CAL_VALID / OS_CLEAR_CAL_VALID
; --------------------------------------------------
; Calibration integrity can become valid without authorizing actuators.
;
OS_SET_CAL_VALID:
        LDAA    #BOOL_TRUE
        STAA    CAL_VALID
        RTS

OS_CLEAR_CAL_VALID:
        CLR     CAL_VALID
        JSR     OS_DISABLE_ALL_ACTUATORS
        JSR     OS_ZERO_ALL_COMMANDS
        RTS

; --------------------------------------------------
; Semantic algorithm request setters
; --------------------------------------------------
; These are deliberately harmless while permissions are disabled.
;
OS_REQUEST_FUEL_PW:
        ; D = semantic fuel PW count request
        STAA    REQ_FUEL_PW_HI
        STAB    REQ_FUEL_PW_LO
        RTS

OS_REQUEST_SPARK:
        ; D = signed/fixed-point semantic spark request
        STAA    REQ_SPARK_HI
        STAB    REQ_SPARK_LO
        RTS

OS_REQUEST_IAC_TARGET:
        ; A = semantic desired IAC count
        STAA    REQ_IAC_TARGET
        RTS

OS_REQUEST_PUMP:
        ; A = 0/off or nonzero/on request
        STAA    REQ_PUMP
        RTS

OS_REQUEST_MIL:
        ; A = 0/off or nonzero/on request
        STAA    REQ_MIL
        RTS

; --------------------------------------------------
; OS_VALIDATE_SNAPSHOT
; --------------------------------------------------
; Engine-off safe placeholder validation layer.
; No validity bit is invented here. HAL/endpoint-specific validation modules
; own the exact plausibility tests. The core only enforces a hard rule:
; calibration invalid => no actuator permission survives.
;
OS_VALIDATE_SNAPSHOT:
        LDAA    CAL_VALID
        BNE     OS_VALIDATE_DONE
        JSR     OS_DISABLE_ALL_ACTUATORS
OS_VALIDATE_DONE:
        RTS

; --------------------------------------------------
; OS_LIFECYCLE_STEP
; --------------------------------------------------
; Safe runtime does not promote to RUN_READY by itself. Later crank/run
; qualification code must do so explicitly after REF validity and endpoint
; proof. Key-off/dropout states stay locked.
;
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

; --------------------------------------------------
; OS_ARBITRATE_COMMANDS
; --------------------------------------------------
; The only path from semantic requests to HAL command state.
; In this first safe-runtime phase, permissions are never set by this module.
;
OS_ARBITRATE_COMMANDS:
        ; Fuel
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

; --------------------------------------------------
; OS_DISABLE_ALL_ACTUATORS
; --------------------------------------------------
OS_DISABLE_ALL_ACTUATORS:
        CLR     PERM_FUEL
        CLR     PERM_SPARK
        CLR     PERM_IAC
        CLR     PERM_PUMP
        CLR     PERM_AUX
        RTS

; --------------------------------------------------
; OS_ZERO_ALL_COMMANDS
; --------------------------------------------------
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

; --------------------------------------------------
; OS_DEBUG_SNAPSHOT_TICK
; --------------------------------------------------
; HAL-owned ALDL/debug code may read these semantic fields. This routine does
; not perform serial I/O and cannot touch hardware.
;
OS_DEBUG_SNAPSHOT_TICK:
        INC     DEBUG_SEQUENCE
        LDAA    DEBUG_HEARTBEAT
        EORA    #$01
        STAA    DEBUG_HEARTBEAT
        RTS

; End safe_runtime.asm
