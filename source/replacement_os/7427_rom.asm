; 7427 replacement OS - ROM master
; --------------------------------
; First target-linked ROM skeleton for GM 16197427 / $31 BMHM hardware.
;
; ROM-FIRST RULE:
;   The executable image is the placement authority.
;   RAM and calibration objects are allocated as implementation requires them.
;   XDF/ADX definitions are generated/described from the built image later.
;
; FIRST-IMAGE SAFETY RULE:
;   No production output permission is ever enabled here.
;   No preserved output island is called from the main loop.
;   Unowned interrupts fall into a COP-serviced safe halt.

        INCLUDE "include/target_layout.inc"

; ---------------------------------------------------------------------------
; RAM allocation
; ---------------------------------------------------------------------------
; Keep placement simple: sequential allocation from low RAM. Do not create
; artificial subsystem address blocks. The assembly map is the authority.
;
        ORG     RAM_RUNTIME_BASE
        INCLUDE "include/runtime_abi.inc"
        INCLUDE "hal/hal_ram.inc"
RAM_ALLOC_END:

; ---------------------------------------------------------------------------
; Executable ROM
; ---------------------------------------------------------------------------
; Retain the stock $7100 executable origin for the first replacement image.
; Calibration/header packing below $7100 is deliberately deferred until real
; calibration objects are implemented.
;
        ORG     ROM_EXEC_BASE

RESET_ENTRY:
        SEI
        LDS     #STACK_TOP

        ; Source-proven HC11 relocation/configuration only.
        JSR     HAL_INIT_PROCESSOR_SAFE

        ; Clear only RAM actually allocated by this build.
        LDX     #RAM_RUNTIME_BASE
RESET_CLEAR_RAM:
        CLR     0,X
        INX
        CPX     #RAM_ALLOC_END
        BNE     RESET_CLEAR_RAM

        ; Semantic/runtime initialization keeps all actuator permissions false.
        JSR     OS_SAFE_INIT
        JSR     HAL_GM_IAC_STATE_INIT

; ---------------------------------------------------------------------------
; FIRST_ROM_IDLE_LOOP
; ---------------------------------------------------------------------------
; This initial ROM proves reset, CPU register relocation, RAM placement,
; vectors, and stable execution without taking control of any actuator.
; Read-only acquisition/scheduler/debug transport are added incrementally after
; this master layout assembles cleanly and its binary/vector map is verified.
;
FIRST_ROM_IDLE_LOOP:
        JSR     HAL_SERVICE_COP
        BRA     FIRST_ROM_IDLE_LOOP

; ---------------------------------------------------------------------------
; Linked implementation modules
; ---------------------------------------------------------------------------
        INCLUDE "hal/init_safe.asm"
        INCLUDE "core/safe_runtime.asm"
        INCLUDE "core/debug_frame.asm"
        INCLUDE "hal/adc_read.asm"
        INCLUDE "hal/ref_read.asm"
        INCLUDE "hal/gm_output_islands.asm"

ROM_CODE_END:

; ---------------------------------------------------------------------------
; HC11 vectors
; ---------------------------------------------------------------------------
; For the first image every unowned vector traps into HAL_FATAL_SAFE_LOOP.
; Only EXT RESET enters RESET_ENTRY. As individual interrupt owners are added,
; their vector entries replace the safe trap one at a time.
;
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

; $FFD6-$FFFE active HC11 vector window
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

; End 7427_rom.asm
