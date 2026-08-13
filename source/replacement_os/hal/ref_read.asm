; 7427 replacement OS - read-only REF/DRP period HAL
; -------------------------------------------------
; Source-proven $31 software-facing input:
;   ASIC $3FC0 = REF/DRP period basis
;
; This module only reads the timing source and forwards it to the semantic
; runtime. It performs no spark, fuel, IAC, pump, or authority writes.

ASIC_REF_PERIOD         EQU     $3FC0

; --------------------------------------------------
; HAL_CAPTURE_REF_PERIOD
; --------------------------------------------------
; Reads the current 16-bit period and delivers it to OS_REF_EVENT in D.
; Physical REF pin level/polarity remains endpoint bench work.
;
HAL_CAPTURE_REF_PERIOD:
        LDD     ASIC_REF_PERIOD
        JSR     OS_REF_EVENT
        RTS

; End ref_read.asm
