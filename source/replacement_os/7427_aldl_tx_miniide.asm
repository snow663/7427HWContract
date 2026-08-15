; 7427 replacement OS - Milestone C single-file ALDL observability
; ----------------------------------------------------------------
; Target: GM 16197427 / mask $31 / BMHM hardware
; Assembler: MGTEK ASM11 (68HC11)
;
; PURPOSE
;   Extend the proven Milestone-B input image with a small periodic raw-input
;   telemetry frame transmitted through the stock-proven 8192-baud SCI/ALDL
;   hardware path.
;
; SAFETY
;   - no injector command writes
;   - no spark/EST command writes
;   - no IAC command writes
;   - no fuel-pump command writes
;   - no auxiliary-output command writes
;   - ALDL driver control modifies only LOW BYTE $3FFD bit2 through the same
;     16-bit read/modify/write form used by stock BMHM
;   - all non-SCI interrupt vectors enter a COP-serviced safe trap
;
; IMPORTANT
;   This is an engine-off bench bring-up image. The $3FFC/$3FFD register pair
;   contains other board controls. ALDL uses B/low-byte bit2 ($3FFD); async fuel
;   uses A/high-byte bit2 ($3FFC). They are distinct controls.
;
; Frame v0, 14 bytes:
;   00  $A5 start
;   01  $31 target/mask tag
;   02  total length ($0E)
;   03  sample sequence
;   04  sample status: bit0 primary ADC timeout, bit1 aux timeout, bit2 MAT timeout
;   05  raw TPS
;   06  raw MAP
;   07  raw O2
;   08  raw coolant
;   09  raw battery
;   10  raw MAT inverted ADC
;   11  REF period high
;   12  REF period low
;   13  two's-complement additive checksum
;
; No INCLUDE files are required.

; ---------------------------------------------------------------------------
; Placement anchors
; ---------------------------------------------------------------------------
STACK_TOP               EQU     $03FF
RAM_RUNTIME_BASE        EQU     $0000
ROM_EXEC_BASE           EQU     $7100
ROM_VECTOR_BASE         EQU     $FFC0

DEBUG_FRAME_LENGTH      EQU     14
TX_LOOP_DIVIDER         EQU     $1000

; ---------------------------------------------------------------------------
; Minimal Milestone-C RAM
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
SAMPLE_STATUS:          RMB     1
TX_ACTIVE:              RMB     1
TX_INDEX:               RMB     1
TX_COUNTDOWN_HI:        RMB     1
TX_COUNTDOWN_LO:        RMB     1
TX_CHECKSUM:            RMB     1
TX_BUFFER:              RMB     DEBUG_FRAME_LENGTH
RAM_ALLOC_END:

; ---------------------------------------------------------------------------
; HC11 / board addresses
; ---------------------------------------------------------------------------
HC11_RESET_REG_BASE     EQU     $1000
HC11_REG_BASE           EQU     $3000

HC11_PORTD_OFF          EQU     $08
HC11_DDRD_OFF           EQU     $09
HC11_TMSK2_OFF          EQU     $24
HC11_BAUD_OFF           EQU     $2B
HC11_SCCR1_OFF          EQU     $2C
HC11_SCCR2_OFF          EQU     $2D
HC11_SCSR_OFF           EQU     $2E
HC11_SCDR_OFF           EQU     $2F
HC11_ADCTL_OFF          EQU     $30
HC11_BPROT_OFF          EQU     $35
HC11_OPT2_OFF           EQU     $38
HC11_OPTION_OFF         EQU     $39
HC11_COPRST_OFF         EQU     $3A
HC11_INIT_OFF           EQU     $3D

HC11_PORTD              EQU     $3008
HC11_DDRD               EQU     $3009
HC11_BAUD               EQU     $302B
HC11_SCCR1              EQU     $302C
HC11_SCCR2              EQU     $302D
HC11_SCSR               EQU     $302E
HC11_SCDR               EQU     $302F
HC11_ADCTL              EQU     $3030
HC11_ADR1               EQU     $3031
HC11_ADR2               EQU     $3032
HC11_ADR3               EQU     $3033
HC11_ADR4               EQU     $3034

ASIC_REF_PERIOD         EQU     $3FC0
GM_ASIC_IO_D            EQU     $3FFC

HC11_INIT_RELOCATE      EQU     $03
HC11_OPTION_BOOT        EQU     $B8
HC11_TMSK2_BOOT         EQU     $03
HC11_BPROT_BOOT         EQU     $1B
ADC_MUX_DDR             EQU     $38
ADC_MUX_MASK            EQU     $38
ADC_COMPLETE            EQU     $80

SCI_BAUD_8192           EQU     $04
SCI_TX_TIE_TE           EQU     $88
SCI_TCIE                EQU     $40
SCI_RX_ONLY             EQU     $04
ALDL_DRIVER_BIT         EQU     $04

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

        JSR     HAL_INIT_SCI_IDLE

        LDD     #TX_LOOP_DIVIDER
        STD     TX_COUNTDOWN_HI

        ; Bounded ADC settling interval while continuing to service COP.
        LDAB    #$FF
RESET_ADC_SETTLE:
        JSR     HAL_SERVICE_COP
        DECB
        BNE     RESET_ADC_SETTLE

        ; Only SCI interrupts are intentionally enabled by this image.
        CLI

; ---------------------------------------------------------------------------
; Engine-off acquisition + periodic telemetry loop
; ---------------------------------------------------------------------------
INPUT_SAMPLE_LOOP:
        JSR     HAL_SERVICE_COP
        CLR     SAMPLE_STATUS

        JSR     HAL_SAMPLE_PRIMARY_ADC
        JSR     HAL_SAMPLE_COOLANT_BATTERY
        JSR     HAL_SAMPLE_MAT
        JSR     HAL_CAPTURE_REF_PERIOD
        INC     SAMPLE_SEQUENCE

        LDD     TX_COUNTDOWN_HI
        SUBD    #$0001
        STD     TX_COUNTDOWN_HI
        BNE     INPUT_SAMPLE_LOOP

        LDD     #TX_LOOP_DIVIDER
        STD     TX_COUNTDOWN_HI

        LDAA    TX_ACTIVE
        BNE     INPUT_SAMPLE_LOOP

        JSR     HAL_DEBUG_BUILD_FRAME
        JSR     HAL_ALDL_START_TX
        BRA     INPUT_SAMPLE_LOOP

; ---------------------------------------------------------------------------
; Processor + input-mux initialization
; ---------------------------------------------------------------------------
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

        ; Stock LCC7C input-mux configuration: DDRD=$38, PORTD initially 0.
        CLRA
        STAA    HC11_PORTD_OFF,X
        LDAA    #ADC_MUX_DDR
        STAA    HC11_DDRD_OFF,X
        RTS

; ---------------------------------------------------------------------------
; SCI / ALDL idle setup
; ---------------------------------------------------------------------------
; Stock LCC7C programs BAUD=$04. For this transmit-only bring-up SCCR1 is 0
; and the receiver is left enabled without RX interrupts between frames.
;
HAL_INIT_SCI_IDLE:
        LDAA    #SCI_BAUD_8192
        STAA    HC11_BAUD
        CLRA
        STAA    HC11_SCCR1
        LDAA    #SCI_RX_ONLY
        STAA    HC11_SCCR2

        ; Release the external ALDL driver: stock form modifies B/low byte bit2.
        LDD     GM_ASIC_IO_D
        JSR     HAL_GM_DELAY_RTS
        ANDB    #$FB
        STD     GM_ASIC_IO_D
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

HAL_GM_DELAY_RTS:
        RTS

; ---------------------------------------------------------------------------
; External analog mux selector
; ---------------------------------------------------------------------------
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

HAL_SAMPLE_PRIMARY_ADC:
        LDAA    #$14
        JSR     HAL_ADC_START_WAIT
        LDAA    ADC_TIMEOUT
        BEQ     HAL_PRIMARY_READ
        LDAA    SAMPLE_STATUS
        ORAA    #$01
        STAA    SAMPLE_STATUS
        RTS
HAL_PRIMARY_READ:
        LDAA    HC11_ADR1
        STAA    RAW_TPS
        LDAA    HC11_ADR2
        STAA    RAW_MAP
        LDAA    HC11_ADR3
        STAA    RAW_O2
        RTS

HAL_SAMPLE_COOLANT_BATTERY:
        LDAA    #$01
        JSR     HAL_ADC_SET_MUX_SELECT
        LDAA    #$11
        JSR     HAL_ADC_START_WAIT
        LDAA    ADC_TIMEOUT
        BEQ     HAL_AUX_READ
        LDAA    SAMPLE_STATUS
        ORAA    #$02
        STAA    SAMPLE_STATUS
        RTS
HAL_AUX_READ:
        LDAA    HC11_ADR3
        STAA    RAW_COOLANT
        LDAA    HC11_ADR4
        STAA    RAW_BATTERY
        RTS

HAL_SAMPLE_MAT:
        LDAA    #$04
        JSR     HAL_ADC_SET_MUX_SELECT
        LDAA    #$01
        JSR     HAL_ADC_START_WAIT
        LDAA    ADC_TIMEOUT
        BEQ     HAL_MAT_READ
        LDAA    SAMPLE_STATUS
        ORAA    #$04
        STAA    SAMPLE_STATUS
        RTS
HAL_MAT_READ:
        LDAA    HC11_ADR4
        COMA
        STAA    RAW_MAT_INV
        RTS

HAL_CAPTURE_REF_PERIOD:
        LDD     ASIC_REF_PERIOD
        STAA    RAW_REF_PERIOD_HI
        STAB    RAW_REF_PERIOD_LO
        RTS

; ---------------------------------------------------------------------------
; Build raw-input telemetry frame
; ---------------------------------------------------------------------------
HAL_DEBUG_BUILD_FRAME:
        CLR     TX_CHECKSUM
        LDX     #TX_BUFFER

        LDAA    #$A5
        JSR     HAL_DEBUG_APPEND_A
        LDAA    #$31
        JSR     HAL_DEBUG_APPEND_A
        LDAA    #DEBUG_FRAME_LENGTH
        JSR     HAL_DEBUG_APPEND_A
        LDAA    SAMPLE_SEQUENCE
        JSR     HAL_DEBUG_APPEND_A
        LDAA    SAMPLE_STATUS
        JSR     HAL_DEBUG_APPEND_A
        LDAA    RAW_TPS
        JSR     HAL_DEBUG_APPEND_A
        LDAA    RAW_MAP
        JSR     HAL_DEBUG_APPEND_A
        LDAA    RAW_O2
        JSR     HAL_DEBUG_APPEND_A
        LDAA    RAW_COOLANT
        JSR     HAL_DEBUG_APPEND_A
        LDAA    RAW_BATTERY
        JSR     HAL_DEBUG_APPEND_A
        LDAA    RAW_MAT_INV
        JSR     HAL_DEBUG_APPEND_A
        LDAA    RAW_REF_PERIOD_HI
        JSR     HAL_DEBUG_APPEND_A
        LDAA    RAW_REF_PERIOD_LO
        JSR     HAL_DEBUG_APPEND_A

        LDAA    TX_CHECKSUM
        NEGA
        STAA    0,X
        CLR     TX_INDEX
        RTS

HAL_DEBUG_APPEND_A:
        STAA    0,X
        ADDA    TX_CHECKSUM
        STAA    TX_CHECKSUM
        INX
        RTS

; ---------------------------------------------------------------------------
; Start stock-style ALDL transmit handoff
; ---------------------------------------------------------------------------
; Stock F637-F645:
;   LDD $3FFC / delay / ORAB #$04 / STD $3FFC / SCCR2=$88
; The ORAB operates on $3FFD, the LOW BYTE of the pair.
;
HAL_ALDL_START_TX:
        LDAA    TX_ACTIVE
        BNE     HAL_ALDL_START_DONE

        LDAA    #$01
        STAA    TX_ACTIVE
        CLR     TX_INDEX

        SEI
        LDD     GM_ASIC_IO_D
        JSR     HAL_GM_DELAY_RTS
        ORAB    #ALDL_DRIVER_BIT
        STD     GM_ASIC_IO_D

        LDAA    #SCI_TX_TIE_TE
        STAA    HC11_SCCR2
        CLI
HAL_ALDL_START_DONE:
        RTS

; ---------------------------------------------------------------------------
; SCI interrupt handler
; ---------------------------------------------------------------------------
; Mirrors the stock F7EA split between TDRE-driven transmit service and
; transmit-complete service. RX interrupts are not enabled in this milestone.
;
HAL_SCI_ISR:
        LDX     #HC11_REG_BASE

        BRCLR   HC11_SCCR2_OFF,X,#$80,HAL_SCI_CHECK_TC
        BRCLR   HC11_SCSR_OFF,X,#$80,HAL_SCI_ISR_DONE
        JSR     HAL_SCI_TX_SERVICE
        BRA     HAL_SCI_ISR_DONE

HAL_SCI_CHECK_TC:
        BRCLR   HC11_SCCR2_OFF,X,#$40,HAL_SCI_ISR_DONE
        BRCLR   HC11_SCSR_OFF,X,#$40,HAL_SCI_ISR_DONE
        JSR     HAL_SCI_TX_COMPLETE

HAL_SCI_ISR_DONE:
        RTI

; ---------------------------------------------------------------------------
; TDRE service: send frame bytes through $302F
; ---------------------------------------------------------------------------
HAL_SCI_TX_SERVICE:
        LDAB    TX_INDEX
        CMPB    #DEBUG_FRAME_LENGTH
        BCC     HAL_SCI_ARM_COMPLETE

        LDX     #TX_BUFFER
        ABX
        LDAA    0,X
        STAA    HC11_SCDR
        INC     TX_INDEX
        RTS

HAL_SCI_ARM_COMPLETE:
        ; Match stock transition from TX-empty service to TC-complete service.
        LDAA    HC11_SCSR
        LDAA    HC11_SCDR
        LDAA    #SCI_TCIE
        STAA    HC11_SCCR2
        RTS

; ---------------------------------------------------------------------------
; Transmit complete: release external ALDL driver
; ---------------------------------------------------------------------------
; Stock F807-F81B uses SCCR2=$26 then clears B/low-byte bit2. This bring-up
; image leaves only RE enabled ($04) to avoid unimplemented RX interrupts,
; while preserving the stock external-driver release sequence exactly.
;
HAL_SCI_TX_COMPLETE:
        LDAA    #SCI_RX_ONLY
        STAA    HC11_SCCR2

        LDD     GM_ASIC_IO_D
        JSR     HAL_GM_DELAY_RTS
        ANDB    #$FB
        STD     GM_ASIC_IO_D

        CLR     TX_ACTIVE
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
        FDB     HAL_SCI_ISR             ; $FFD6 SCI
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

; End 7427_aldl_tx_miniide.asm
