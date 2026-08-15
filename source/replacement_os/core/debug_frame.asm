; 7427 replacement OS - semantic debug frame builder
; --------------------------------------------------
; No hardware addresses are permitted in this module.
; It only snapshots semantic/runtime state into DEBUG_TX_BUFFER.
; HAL transport decides how/when the buffer is transmitted.

; Frame v1, fixed 24 bytes:
;   00  $A5 start
;   01  $31 target/mask tag
;   02  total length ($18)
;   03  sequence
;   04  lifecycle state
;   05  sensor validity flags
;   06  raw TPS
;   07  raw MAP
;   08  raw coolant
;   09  raw MAT inverted ADC
;   10  raw O2
;   11  raw battery
;   12  REF period hi
;   13  REF period lo
;   14  semantic RPM hi
;   15  semantic RPM lo
;   16  requested sync fuel PW hi
;   17  requested sync fuel PW lo
;   18  requested spark hi
;   19  requested spark lo
;   20  requested IAC target
;   21  permission summary bits
;   22  heartbeat
;   23  two's-complement additive checksum

OS_DEBUG_BUILD_FRAME:
        ; Do not overwrite a frame that is pending or being transported.
        ; Use nearby conditional branches plus JMP because the full frame
        ; builder is larger than the HC11 +/-127-byte relative branch range.
        LDAA    DEBUG_TX_PENDING
        BEQ     OS_DEBUG_CHECK_ACTIVE
        JMP     OS_DEBUG_BUILD_DONE
OS_DEBUG_CHECK_ACTIVE:
        LDAA    DEBUG_TX_ACTIVE
        BEQ     OS_DEBUG_BUILD_START
        JMP     OS_DEBUG_BUILD_DONE
OS_DEBUG_BUILD_START:

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

        ; Permission summary: bit0 fuel, bit1 spark, bit2 IAC,
        ; bit3 pump, bit4 auxiliary.
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

        ; Final byte makes the unsigned 8-bit sum of all 24 bytes equal zero.
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

; Append A to buffer at X and update running checksum.
OS_DEBUG_APPEND_A:
        STAA    0,X
        ADDA    DEBUG_TX_CHECKSUM
        STAA    DEBUG_TX_CHECKSUM
        INX
        RTS
