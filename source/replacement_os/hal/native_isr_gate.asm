; ASM11 native ISR gateway. Its active vectors remain UNBOUND.
; HC11 hardware has stacked CCR,B,A,X,Y,PC (nine bytes).
; On entry TSX is the address of saved CCR, before our JSR adds bytes.
; When a target C compiler is available, HAL_ISR_C_ENTRY_WORD will point
; to a verified no-argument RTS thunk that uses the mailbox declared in
; hal/hal_ram.inc and invokes pcm_hc11_mailbox_dispatch.
; The default thunk DENIES return. Do not bind vectors until C+ASM11
; object ABI, stack budget, and interrupt admission are established.
;
; No production actuator output is enabled by this module.

HAL_ISR_RETURN_TOKEN    EQU     $A5
HAL_ISR_BUSY_TOKEN      EQU     $A5
HAL_ISR_BASIC_PROOF     EQU     $03

HAL_ISR_ENTRY_SCI:
        LDD     #$FFD6
        JMP     HAL_ISR_GATE_COMMON
HAL_ISR_ENTRY_SPI:
        LDD     #$FFD8
        JMP     HAL_ISR_GATE_COMMON
HAL_ISR_ENTRY_PA_EDGE:
        LDD     #$FFDA
        JMP     HAL_ISR_GATE_COMMON
HAL_ISR_ENTRY_PA_OVF:
        LDD     #$FFDC
        JMP     HAL_ISR_GATE_COMMON
HAL_ISR_ENTRY_TOV:
        LDD     #$FFDE
        JMP     HAL_ISR_GATE_COMMON
HAL_ISR_ENTRY_TOC3:
        LDD     #$FFE4
        JMP     HAL_ISR_GATE_COMMON
HAL_ISR_ENTRY_TOC2:
        LDD     #$FFE6
        JMP     HAL_ISR_GATE_COMMON
HAL_ISR_ENTRY_OC1:
        LDD     #$FFE8
        JMP     HAL_ISR_GATE_COMMON
HAL_ISR_ENTRY_TIC3:
        LDD     #$FFEA
        JMP     HAL_ISR_GATE_COMMON
HAL_ISR_ENTRY_TIC2:
        LDD     #$FFEC
        JMP     HAL_ISR_GATE_COMMON
HAL_ISR_ENTRY_TIC1:
        LDD     #$FFEE
        JMP     HAL_ISR_GATE_COMMON
HAL_ISR_ENTRY_RTI:
        LDD     #$FFF0
        JMP     HAL_ISR_GATE_COMMON
HAL_ISR_ENTRY_REF:
        LDD     #$FFF2
        JMP     HAL_ISR_GATE_COMMON

; No callable entry for TOC4/TOC5 output interrupts, XIRQ, SWI,
; illegal, COP failure, clock failure, or reset.

HAL_ISR_GATE_COMMON:
        STD     HAL_ISR_VECTOR_HI
        LDAA    HAL_ISR_BUSY
        BNE     HAL_ISR_GATE_FATAL
        TSX
        CPX     #$03B0
        BLO     HAL_ISR_GATE_FATAL
        CPX     #$03F7
        BHI     HAL_ISR_GATE_FATAL
        STX     HAL_ISR_CCR_ADDR_HI
        LDAA    #HAL_ISR_BUSY_TOKEN
        STAA    HAL_ISR_BUSY
        CLR     HAL_ISR_ACTION
        CLR     HAL_ISR_STATUS
        LDAA    #HAL_ISR_BASIC_PROOF
        STAA    HAL_ISR_PROOF
        JSR     HAL_ISR_C_ABI_CALL
        LDAA    HAL_ISR_ACTION
        CMPA    #HAL_ISR_RETURN_TOKEN
        BNE     HAL_ISR_GATE_FATAL
        LDAA    HAL_ISR_STATUS
        BNE     HAL_ISR_GATE_FATAL
        CLR     HAL_ISR_BUSY
        RTI

HAL_ISR_GATE_FATAL:
        JMP     HAL_FATAL_SAFE_LOOP

; This indirect call is the compiler/linker seam. It cannot be silently
; treated as a working C ABI. Until bound, every entry reaches the trap.
HAL_ISR_C_ABI_CALL:
        LDX     HAL_ISR_C_ENTRY_WORD
        JSR     0,X
        RTS

HAL_ISR_C_ENTRY_WORD:
        FDB     HAL_ISR_C_UNBOUND

HAL_ISR_C_UNBOUND:
        LDAA    #$01
        STAA    HAL_ISR_STATUS
        CLR     HAL_ISR_ACTION
        RTS
