; -----------------------------------------------------------------------------
; FUEL SLICE-0 BENCH HARNESS
;
; Bench-only. Not engine-runnable.
; Not scheduler-owned.
; Not reset-vector-owned.
; Not crank/run fuel control.
;
; Used only to prove EFI_PW_WRITE / $3FCE pulsewidth command path with fixed
; vectors. This file must not write $3FCE directly. The only fuel output path is:
;
;       LDD   #test_vector
;       JSR   EFI_PW_WRITE
;
; EFI_PW_WRITE remains the only routine allowed to contain the hardware store:
;
;       STD   L3FCE
;
; Forbidden in this harness:
;
;       direct $3FCE / L3FCE write
;       $3FE8 / $3FE6 / $3FF6 / $3FDC spark writes
;       L3062 IAC writes
;       SPARK_WRITE
;       IAC_WRITE
;       ALDL packet implementation
;       fuel math
;       sensor reads
;       VE table use
;       reset-vector or scheduler ownership
; -----------------------------------------------------------------------------

FUEL_SLICE0_WRITE_ZERO:
        LDD   #$0000
        JSR   EFI_PW_WRITE
        RTS

FUEL_SLICE0_WRITE_1MS:
        LDD   #$0042
        JSR   EFI_PW_WRITE
        RTS

FUEL_SLICE0_WRITE_2MS:
        LDD   #$0083
        JSR   EFI_PW_WRITE
        RTS

FUEL_SLICE0_WRITE_3MS:
        LDD   #$00C5
        JSR   EFI_PW_WRITE
        RTS

FUEL_SLICE0_WRITE_4MS:
        LDD   #$0106
        JSR   EFI_PW_WRITE
        RTS
