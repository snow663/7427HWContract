; 7427 replacement OS - read-only ADC HAL
; ----------------------------------------
; Hardware-specific code is allowed here ONLY.
; This module is based on the source-proven $31 BMHM ADC acquisition paths:
;   F245/F25F/F275 primary multi-channel read
;   F22E auxiliary multi-channel read
;   C56F battery read
;   DBFB MAT read
;
; This file performs ADC control/result access only.
; It MUST NOT write injector, spark, IAC, pump, or auxiliary output registers.
;
; Requires semantic RAM definitions from runtime_abi.inc.

; Relocated HC11 register addresses proven by stock INIT policy.
HC11_OPTION             EQU     $3008
HC11_ADCTL              EQU     $3030
HC11_ADR1               EQU     $3031
HC11_ADR2               EQU     $3032
HC11_ADR3               EQU     $3033
HC11_ADR4               EQU     $3034

ADC_COMPLETE            EQU     $80
ADC_DELAY_MASK          EQU     $38

; HAL diagnostic state only; placement handled with other HAL RAM.
HAL_ADC_TIMEOUT:        RMB     1

; --------------------------------------------------
; HAL_ADC_SET_DELAY
; --------------------------------------------------
; A = stock delay selector before <<3.
; Preserves the source-proven $3008 bits3..5 update from F275.
;
HAL_ADC_SET_DELAY:
        PSHB
        TAB
        LDAA    HC11_OPTION
        ANDA    #$C7              ; clear bits3..5
        ASLB
        ASLB
        ASLB
        ANDB    #ADC_DELAY_MASK
        ABA
        STAA    HC11_OPTION
        PULB
        RTS

; --------------------------------------------------
; HAL_ADC_START_WAIT
; --------------------------------------------------
; A = ADCTL mode byte.
; Returns with conversion complete or timeout marker set.
; No actuator state is modified on timeout.
;
HAL_ADC_START_WAIT:
        CLR     HAL_ADC_TIMEOUT
        STAA    HC11_ADCTL
        LDAB    #12               ; stock bounded wait count from F25F
HAL_ADC_WAIT_LOOP:
        BRSET   HC11_ADCTL,#ADC_COMPLETE,HAL_ADC_WAIT_DONE
        DECB
        BNE     HAL_ADC_WAIT_LOOP
        LDAA    #$01
        STAA    HAL_ADC_TIMEOUT
HAL_ADC_WAIT_DONE:
        RTS

; --------------------------------------------------
; HAL_SAMPLE_PRIMARY_ADC
; --------------------------------------------------
; Source-proven normal multi-channel mapping:
;   ADR1 -> TPS
;   ADR2 -> MAP
;   ADR3 -> O2
;
HAL_SAMPLE_PRIMARY_ADC:
        LDAA    #$14              ; stock F248 multi-channel selection
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

; --------------------------------------------------
; HAL_SAMPLE_COOLANT_BATTERY
; --------------------------------------------------
; Mirrors stock F22E group setup sufficiently for the two retained values:
;   ADR3 -> coolant raw
;   ADR4 -> battery raw
; ADR2 is intentionally ignored by the minimal engine-control runtime.
;
HAL_SAMPLE_COOLANT_BATTERY:
        LDAA    #$01
        JSR     HAL_ADC_SET_DELAY
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

; --------------------------------------------------
; HAL_SAMPLE_MAT
; --------------------------------------------------
; Stock DBFB path:
;   delay selector 4
;   ADCTL mode 1
;   read ADR4
;   invert value before semantic storage
;
HAL_SAMPLE_MAT:
        LDAA    #$04
        JSR     HAL_ADC_SET_DELAY
        LDAA    #$01
        JSR     HAL_ADC_START_WAIT
        LDAA    HAL_ADC_TIMEOUT
        BNE     HAL_MAT_DONE

        LDAA    HC11_ADR4
        COMA
        STAA    RAW_MAT_INV
HAL_MAT_DONE:
        RTS

; --------------------------------------------------
; HAL_SAMPLE_BATTERY_STOCK_MODE
; --------------------------------------------------
; Dedicated stock C56F-style battery conversion. Useful as a bench cross-check
; against the auxiliary multi-channel result.
;
HAL_SAMPLE_BATTERY_STOCK_MODE:
        LDAA    #$02
        JSR     HAL_ADC_SET_DELAY
        LDAA    #$01
        JSR     HAL_ADC_START_WAIT
        LDAA    HAL_ADC_TIMEOUT
        BNE     HAL_BATT_DONE

        LDAA    HC11_ADR4
        STAA    RAW_BATTERY
HAL_BATT_DONE:
        RTS

; End adc_read.asm
