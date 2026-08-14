; 7427 replacement OS - stock-proven processor bootstrap
; ------------------------------------------------------
; This module owns the HC11 reset-time register relocation and the minimum
; processor configuration needed by the first replacement-ROM skeleton.
;
; It intentionally does NOT initialize or command production actuators.
; Board-output initialization will be added only from preserved/proven stock
; behavior and remains separately permission-gated.

; Reset-time HC11 register block and relocated block.
HC11_RESET_REG_BASE     EQU     $1000
HC11_REG_BASE           EQU     $3000

; Register offsets proven by the stock BMHM reset sequence.
HC11_TMSK2_OFF          EQU     $24
HC11_BPROT_OFF          EQU     $35
HC11_OPT2_OFF           EQU     $38
HC11_OPTION_OFF         EQU     $39
HC11_COPRST_OFF         EQU     $3A
HC11_INIT_OFF           EQU     $3D

; Stock reset values from $7100 startup.
HC11_INIT_RELOCATE      EQU     $03
HC11_OPTION_BOOT        EQU     $B8
HC11_TMSK2_BOOT         EQU     $03
HC11_BPROT_BOOT         EQU     $1B

; --------------------------------------------------
; HAL_INIT_PROCESSOR_SAFE
; --------------------------------------------------
; Reproduces only the source-proven CPU-side portion of stock $7100-$711A:
;   register block $1000 -> $3000
;   OPTION = $B8
;   TMSK2 = $03
;   OPT2 bit5 clear
;   BPROT = $1B
;
; No ASIC/output register is touched here.
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

; --------------------------------------------------
; HAL_SERVICE_COP
; --------------------------------------------------
; Source-proven stock COP service sequence at relocated $303A.
;
HAL_SERVICE_COP:
        LDX     #HC11_REG_BASE
        LDAA    #$55
        STAA    HC11_COPRST_OFF,X
        COMA                    ; $AA
        STAA    HC11_COPRST_OFF,X
        RTS

; --------------------------------------------------
; HAL_FATAL_SAFE_LOOP
; --------------------------------------------------
; Common first-image sink for every interrupt/vector not explicitly owned yet.
; It never authorizes or commits an actuator command. The COP is serviced so a
; diagnostic bench can distinguish a trapped image from repeated reset cycling.
;
HAL_FATAL_SAFE_LOOP:
        SEI
        JSR     OS_DISABLE_ALL_ACTUATORS
        JSR     OS_ZERO_ALL_COMMANDS
HAL_FATAL_SAFE_LOOP_1:
        JSR     HAL_SERVICE_COP
        BRA     HAL_FATAL_SAFE_LOOP_1

; End init_safe.asm
