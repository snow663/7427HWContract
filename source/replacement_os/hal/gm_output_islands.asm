; 7427 replacement OS - preserved GM output-driver islands
; -------------------------------------------------------
; This file intentionally contains stock hardware addresses.
; It MUST remain under source/replacement_os/hal/.
;
; Architecture:
;   semantic command -> permission/valid gate -> preserved GM command behavior
;
; These routines are not called by the current engine-off safe runtime.
; Merely linking this file does not authorize any actuator.
;
; Required semantic symbols come from runtime_abi.inc.

; Stock hardware command targets
GM_EFI_SYNC_PW          EQU     $3FCE
GM_EFI_ASYNC_PW         EQU     $3FF2
GM_ASIC_IO_D            EQU     $3FFC
GM_CPU_PORT_D           EQU     $3062
GM_FUEL_PUMP_LATCH      EQU     $306F

; -------------------------------------------------------
; HAL_GM_DELAY_RTS
; -------------------------------------------------------
; Stock LF3ED is literally RTS and is repeatedly called between ASIC
; accesses. Preserve the call/return cycle delay rather than deleting it.
;
HAL_GM_DELAY_RTS:
        RTS

; -------------------------------------------------------
; HAL_GM_FUEL_SYNC_COMMIT
; -------------------------------------------------------
; Stock BMHM TBI command boundary:
;   final 16-bit pulse-width count -> $3FCE
;
; Disabled/invalid behavior preserves stock no-fuel semantic: $0000 -> $3FCE.
;
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

; -------------------------------------------------------
; HAL_GM_FUEL_ASYNC_COMMIT
; -------------------------------------------------------
; Hardware tail of stock L8548 after algorithm-side compensation/biasing:
;   final async PW -> $3FF2
;   clear $3FFC bit2, write
;   set   $3FFC bit2, write
; with stock LF3ED call delays between accesses.
;
; A zero/invalid async request does not toggle the trigger.
;
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

; -------------------------------------------------------
; HAL_GM_PUMP_COMMIT
; -------------------------------------------------------
; Stock command bytes observed in BMHM:
;   $FF -> $306F asserted
;   $00 -> $306F cleared
;
; Lifecycle decides prime/run/stall timing. This routine only commits the
; stock byte command.
;
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

; -------------------------------------------------------
; HAL_GM_IAC_STATE_INIT
; -------------------------------------------------------
; Initializes private software driver state only. It does NOT touch $3062.
; Stock boot seeds the port-D shadow to $40; preserve that software seed.
;
HAL_GM_IAC_STATE_INIT:
        CLRA
        STAA    DRV_IAC_POSITION
        STAA    DRV_IAC_STATE
        LDAA    #$40
        STAA    DRV_PORTD_SHADOW
        RTS

; -------------------------------------------------------
; HAL_GM_IAC_COMMIT
; -------------------------------------------------------
; Translation of the stock L91C2-L920D step/phase driver and F40F-F411
; shadow-to-port commit.
;
; Input:
;   CMD_IAC_TARGET = desired software IAC position/count
;
; Private state:
;   DRV_IAC_POSITION
;   DRV_IAC_STATE bit0  = stock direction state
;   DRV_IAC_STATE bit2/3 = stock A/B phase state
;   DRV_IAC_STATE bit4  = stock driver-enable state
;
; Permission loss uses the stock disable semantic: clear bit4. No physical
; polarity interpretation is required.
;
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

        ; Stock equal-position path: clear direction bit, no step.
        ANDB    #$FE
        BRA     HAL_GM_IAC_MERGE

HAL_GM_IAC_NOT_EQUAL:
        ; Preserve stock unsigned CMP/BCC decision exactly.
        BCC     HAL_GM_IAC_BRANCH_91DF

        ; Stock 91D6 path.
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

        ; Exact stock phase-ring decisions from 91E8-91FE.
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

        ; Preserve stock atomic shadow merge: keep non-IAC bits, replace $1C.
        SEI
        LDAA    DRV_PORTD_SHADOW
        ANDA    #$E3
        ANDB    #$1C
        ABA
        STAA    DRV_PORTD_SHADOW
        STAA    GM_CPU_PORT_D
        CLI
        RTS

; Spark/EST is intentionally not partially emitted here.
; Its ABI is locked in docs/contracts/PRESERVED_OUTPUT_DRIVER_ISLANDS.md,
; but the full rolling-state/dwell/latency handoff must be ported as one
; complete island rather than reduced to isolated $3Fxx writes.
