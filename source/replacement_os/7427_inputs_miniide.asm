; 7427 replacement OS - Milestone B single-file input acquisition
; ---------------------------------------------------------------
; Target: GM 16197427 / mask $31 / BMHM hardware
; Assembler: MGTEK ASM11 (68HC11)
;
; PURPOSE
;   Extend the proven Milestone A bootstrap with read-only acquisition of the
;   source-proven ADC channels and the ASIC REF/DRP period register.
;
; SAFETY
;   - no injector command writes
;   - no spark/EST command writes
;   - no IAC command writes
;   - no fuel-pump command writes
;   - no auxiliary-output command writes
;   - only CPU/ADC/mux configuration and read-only input acquisition are added
;   - all unowned interrupt vectors enter a COP-serviced safe trap
;
; NOTE
;   REF data at $3FC0 is captured read-only. Meaningful live REF behavior may
;   still depend on later source-proven ASIC initialization; this milestone
;   deliberately does not write the $3FC0-$3FFF command/register island.
;
; This file is deliberately self-contained. No INCLUDE files are required.

; ---------------------------------------------------------------------------
; Placement anchors
; ---------------------------------------------------------------------------
STACK_TOP               EQU     $03FF
RAM_RUNTIME_BASE        EQU     $0000
ROM_EXEC_BASE           EQU     $7100
ROM_VECTOR_BASE         EQU     $FFC0

; ---------------------------------------------------------------------------
; Minimal Milestone-B RAM
; ---------------------------------------------------------------------------
        ORG     RAM_RUNTIME_BASE

RAW_TPS:                RMB     1
RAW_MAP:                RMB     1
RAW_O2:                 RMB     1
RAW_COOLANT:            RMB     1
RAW_BATTERY:            RMB     1
RAW_MAT_INV:            RMB     1
RAW_REF_PERIOD_HI:      RMB     1
RAW_REF_PERIOD_LO:      RMB     1
ADC_TIMEOUT:            RMB     1
SAMPLE_SEQUENCE:        RMB     1
RAM_ALLOC_END:

; ---------------------------------------------------------------------------
; HC11 / board input addresses
; ---------------------------------------------------------------------------
HC11_RESET_REG_BASE     EQU     $1000
HC11_REG_BASE           EQU     $3000

HC11_PORTD_OFF          EQU     $08
HC11_DDRD_OFF           EQU     $09
HC11_TMSK2_OFF          EQU     $24
HC11_ADCTL_OFF          EQU     $30
HC11_ADR1_OFF           EQU     $31
HC11_ADR2_OFF           EQU     $32
HC11_ADR3_OFF           EQU     $33
HC11_ADR4_OFF           EQU     $34
HC11_BPROT_OFF          EQU     $35
HC11_OPT2_OFF           EQU     $38
HC11_OPTION_OFF         EQU     $39
HC11_COPRST_OFF         EQU     $3A
HC11_INIT_OFF           EQU     $3D

HC11_PORTD              EQU     $3008
HC11_DDRD               EQU     $3009
HC11_ADCTL              EQU     $3030
HC11_ADR1               EQU     $3031
HC11_ADR2               EQU     $3032
HC11_ADR3               EQU     $3033
HC11_ADR4               EQU     $3034

ASIC_REF_PERIOD         EQU     $3FC0

HC11_INIT_RELOCATE      EQU     $03
HC11_OPTION_BOOT        EQU     $B8
HC11_TMSK2_BOOT         EQU     $03
HC11_BPROT_BOOT         EQU     $1B
ADC_MUX_DDR             EQU     $38
ADC_MUX_MASK            EQU     $38
ADC_COMPLETE            EQU     $80

; ---------------------------------------------------------------------------
; Executable ROM
; ---------------------------------------------------------------------------
        ORG     ROM_EXEC_BASE

RESET_ENTRY:
        SEI
        LDS     #STACK_TOP
        JSR     HAL_INIT_PROCESSOR_INPUT_SAFE

        ; Clear only RAM owned by this milestone.
        LDX     #RAM_RUNTIME_BASE
RESET_CLEAR_RAM:
        CLR     0,X
        INX
        CPX     #RAM_ALLOC_END
        BNE     RESET_CLEAR_RAM

        ; Stock OPTION powers the ADC. Give it a bounded settling interval
        ; before the first conversion while continuing to service the COP.
        LDAB    #$FF
RESET_ADC_SETTLE:
        JSR     HAL_SERVICE_COP
        DECB
        BNE     RESET_ADC_SETTLE

; ---------------------------------------------------------------------------
; Engine-off input acquisition loop
; ---------------------------------------------------------------------------
INPUT_SAMPLE_LOOP:
        JSR     HAL_SERVICE_COP
        JSR     HAL_SAMPLE_PRIMARY_ADC
        JSR     HAL_SAMPLE_COOLANT_BATTERY
        JSR     HAL_SAMPLE_MAT
        JSR     HAL_CAPTURE_REF_PERIOD
        INC     SAMPLE_SEQUENCE
        BRA     INPUT_SAMPLE_LOOP

; ---------------------------------------------------------------------------
; Processor + input-mux initialization
; ---------------------------------------------------------------------------
; CPU-side startup matches the proven stock $7100 sequence. The only added
; board-facing configuration is the exact stock DDRD=$38 needed by F275's
; PORTD bits3..5 external analog-mux selector. PORTD is then cleared to selector
; zero, matching stock startup's later clear of relocated PORTD.
;
HAL_INIT_PROCESSOR_INPUT_SAFE:
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

        ; Stock LCC7C: DDRD = $38. Stock startup then clears PORTD.
        CLRA
        STAA    HC11_PORTD_OFF,X
        LDAA    #ADC_MUX_DDR
        STAA    HC11_DDRD_OFF,X
        RTS

; ---------------------------------------------------------------------------
; COP service
; ---------------------------------------------------------------------------
HAL_SERVICE_COP:
        LDX     #HC11_REG_BASE
        LDAA    #$55
        STAA    HC11_COPRST_OFF,X
        COMA
        STAA    HC11_COPRST_OFF,X
        RTS

; ---------------------------------------------------------------------------
; External analog mux selector
; ---------------------------------------------------------------------------
; A = stock selector value before <<3.
; Preserves stock F275 behavior on relocated CPU PORTD bits3..5.
;
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

; ---------------------------------------------------------------------------
; ADC conversion helper
; ---------------------------------------------------------------------------
; A = ADCTL mode byte. ASM11 cannot encode BRSET against absolute $3030 as a
; direct-page operand, so completion is tested using an explicit extended load.
;
HAL_ADC_START_WAIT:
        CLR     ADC_TIMEOUT
        STAA    HC11_ADCTL
        LDAB    #12
HAL_ADC_WAIT_LOOP:
        LDAA    HC11_ADCTL
        BITA    #ADC_COMPLETE
        BNE     HAL_ADC_WAIT_DONE
        DECB
        BNE     HAL_ADC_WAIT_LOOP
        LDAA    #$01
        STAA    ADC_TIMEOUT
HAL_ADC_WAIT_DONE:
        RTS

; ---------------------------------------------------------------------------
; Primary ADC group: stock F245/F248 mapping
; ADR1 TPS, ADR2 MAP, ADR3 O2
; ---------------------------------------------------------------------------
HAL_SAMPLE_PRIMARY_ADC:
        LDAA    #$14
        JSR     HAL_ADC_START_WAIT
        LDAA    ADC_TIMEOUT
        BNE     HAL_PRIMARY_DONE
        LDAA    HC11_ADR1
        STAA    RAW_TPS
        LDAA    HC11_ADR2
        STAA    RAW_MAP
        LDAA    HC11_ADR3
        STAA    RAW_O2
HAL_PRIMARY_DONE:
        RTS

; ---------------------------------------------------------------------------
; Auxiliary ADC group: stock F22E mapping retained for V1 inputs
; selector 1, ADCTL $11, ADR3 coolant, ADR4 battery
; ---------------------------------------------------------------------------
HAL_SAMPLE_COOLANT_BATTERY:
        LDAA    #$01
        JSR     HAL_ADC_SET_MUX_SELECT
        LDAA    #$11
        JSR     HAL_ADC_START_WAIT
        LDAA    ADC_TIMEOUT
        BNE     HAL_COOL_BATT_DONE
        LDAA    HC11_ADR3
        STAA    RAW_COOLANT
        LDAA    HC11_ADR4
        STAA    RAW_BATTERY
HAL_COOL_BATT_DONE:
        RTS

; ---------------------------------------------------------------------------
; MAT ADC group: stock DBFB behavior
; selector 4, ADCTL $01, ADR4 inverted before storage
; ---------------------------------------------------------------------------
HAL_SAMPLE_MAT:
        LDAA    #$04
        JSR     HAL_ADC_SET_MUX_SELECT
        LDAA    #$01
        JSR     HAL_ADC_START_WAIT
        LDAA    ADC_TIMEOUT
        BNE     HAL_MAT_DONE
        LDAA    HC11_ADR4
        COMA
        STAA    RAW_MAT_INV
HAL_MAT_DONE:
        RTS

; ---------------------------------------------------------------------------
; REF/DRP read-only capture
; ---------------------------------------------------------------------------
HAL_CAPTURE_REF_PERIOD:
        LDD     ASIC_REF_PERIOD
        STAA    RAW_REF_PERIOD_HI
        STAB    RAW_REF_PERIOD_LO
        RTS

; ---------------------------------------------------------------------------
; Safe trap for all currently unowned interrupts
; ---------------------------------------------------------------------------
HAL_FATAL_SAFE_LOOP:
        SEI
HAL_FATAL_SAFE_LOOP_1:
        JSR     HAL_SERVICE_COP
        BRA     HAL_FATAL_SAFE_LOOP_1

ROM_CODE_END:

; ---------------------------------------------------------------------------
; HC11 vector table
; ---------------------------------------------------------------------------
        ORG     ROM_VECTOR_BASE

; $FFC0-$FFD4 reserved vectors
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

; $FFD6-$FFFE active HC11 vectors
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFD6 SCI
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFD8 SPI
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFDA pulse accumulator input edge
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFDC pulse accumulator overflow
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
        FDB     HAL_FATAL_SAFE_LOOP     ; $FFFC clock monitor fail
        FDB     RESET_ENTRY             ; $FFFE external reset

; End 7427_inputs_miniide.asm
