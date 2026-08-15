; 7427 replacement OS - Milestone A single-file ASM11 bootstrap
; -------------------------------------------------------------
; Target: GM 16197427 / mask $31 / BMHM hardware
; Assembler: MGTEK ASM11 (68HC11)
;
; PURPOSE
;   Prove the first replacement-ROM executable layout with the smallest
;   possible engine-off image before linking read-only acquisition/debug code.
;
; SAFETY
;   - no injector command writes
;   - no spark/EST command writes
;   - no IAC command writes
;   - no fuel-pump command writes
;   - no auxiliary-output command writes
;   - all unowned interrupt vectors enter a COP-serviced safe trap
;
; This file is deliberately self-contained. No INCLUDE files are required.

; ---------------------------------------------------------------------------
; Stock-proven / deliberately selected placement anchors
; ---------------------------------------------------------------------------
STACK_TOP               EQU     $03FF
ROM_EXEC_BASE           EQU     $7100
ROM_VECTOR_BASE         EQU     $FFC0

; Reset-time and relocated HC11 register blocks.
HC11_RESET_REG_BASE     EQU     $1000
HC11_REG_BASE           EQU     $3000

; Register offsets proven from stock BMHM reset sequence.
HC11_TMSK2_OFF          EQU     $24
HC11_BPROT_OFF          EQU     $35
HC11_OPT2_OFF           EQU     $38
HC11_OPTION_OFF         EQU     $39
HC11_COPRST_OFF         EQU     $3A
HC11_INIT_OFF           EQU     $3D

; Stock reset values.
HC11_INIT_RELOCATE      EQU     $03
HC11_OPTION_BOOT        EQU     $B8
HC11_TMSK2_BOOT         EQU     $03
HC11_BPROT_BOOT         EQU     $1B

; ---------------------------------------------------------------------------
; Executable ROM
; ---------------------------------------------------------------------------
        ORG     ROM_EXEC_BASE

RESET_ENTRY:
        SEI
        LDS     #STACK_TOP
        JSR     HAL_INIT_PROCESSOR_SAFE

; First-image idle loop: no production actuator routine exists in this file.
FIRST_ROM_IDLE_LOOP:
        JSR     HAL_SERVICE_COP
        BRA     FIRST_ROM_IDLE_LOOP

; ---------------------------------------------------------------------------
; Processor initialization
; ---------------------------------------------------------------------------
; Reproduce only source-proven CPU-side stock startup:
;   register block $1000 -> $3000
;   OPTION = $B8
;   TMSK2 = $03
;   OPT2 bit5 clear
;   BPROT = $1B
;
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

; ---------------------------------------------------------------------------
; COP service
; ---------------------------------------------------------------------------
HAL_SERVICE_COP:
        LDX     #HC11_REG_BASE
        LDAA    #$55
        STAA    HC11_COPRST_OFF,X
        COMA                    ; $55 -> $AA
        STAA    HC11_COPRST_OFF,X
        RTS

; ---------------------------------------------------------------------------
; Safe trap for every currently unowned interrupt
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

; End 7427_bootstrap_miniide.asm
