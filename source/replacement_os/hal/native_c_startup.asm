; 16197427 / 68HC11 bare-metal C runtime initialization.
; This module does not turn outputs on or activate interrupt vectors.
; ASM11 reset already executes SEI, LDS #03FF and safe HAL init.
;
; New compiled-C executable image is stored in ROM and its uninitialized
; C state (.bss + .softregs) requires explicit zeroing before C is entered.
; A verified link step must patch 4 ROM fields below, using actual
; ASM11 listing and linked native ELF section/symbol addresses.
;
; The build as checked in is UNBOUND: token zero -> RTS, no C call.
; A partially patched or corrupted activation token fails into the
; original engine-off fatal handler rather than touching unknown RAM.
;
; LIVE ABI STILL REQUIRED: no-arg native C reset function must have an
; ordinary RTS convention and use only the verified C state region.

HAL_C_STARTUP_SIGNATURE EQU     $C3

HAL_NATIVE_C_INITIALIZE:
        LDAA    HAL_C_STARTUP_TOKEN
        BEQ     HAL_C_BOOT_SKIP
        CMPA    #HAL_C_STARTUP_SIGNATURE
        BNE     HAL_C_BOOT_FATAL

        ; The exact range [FIRST,END) is patched from native ELF output.
        ; NEVER deduce it from host sizeof(Pcm) or a guessed RAM mirror.
        LDX     HAL_C_STATE_START_WORD
        CPX     HAL_C_STATE_END_WORD
        BHI     HAL_C_BOOT_FATAL
        BEQ     HAL_C_BOOT_C_CALL

HAL_C_BOOT_CLEAR_LOOP:
        CLR     0,X
        INX
        CPX     HAL_C_STATE_END_WORD
        BNE     HAL_C_BOOT_CLEAR_LOOP

HAL_C_BOOT_C_CALL:
        LDX     HAL_C_RESET_CALL_WORD
        CPX     #HAL_C_BOOT_UNBOUND
        BEQ     HAL_C_BOOT_FATAL
        CPX     #$0000
        BEQ     HAL_C_BOOT_FATAL
        JSR     0,X
HAL_C_BOOT_SKIP:
        RTS

HAL_C_BOOT_FATAL:
        JMP     HAL_FATAL_SAFE_LOOP

; Provenance-backed patch fields: unchanged unless all have been
; checked against actual ASM11 bytes and target compiled-C link maps.
HAL_C_STARTUP_TOKEN:
        FCB     $00
HAL_C_STATE_START_WORD:
        FDB     $0000
HAL_C_STATE_END_WORD:
        FDB     $0000
HAL_C_RESET_CALL_WORD:
        FDB     HAL_C_BOOT_UNBOUND
HAL_C_BOOT_UNBOUND:
        JMP     HAL_C_BOOT_FATAL
