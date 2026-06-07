; -----------------------------------------------------------------------------
; EFI_PW_WRITE
;
; Minimal EFI pulsewidth writer for 7427 hardware-contract OS.
;
; Input:
;   D = EFI pulsewidth command in 1/65536 second units
;
; Unit:
;   PW_ms = D / 65.536
;
; Output:
;   Writes D to ASIC EFI pulsewidth handoff register $3FCE/$3FCF.
;
; Notes:
;   D = 0 is treated as no-fuel/off by design, pending bench confirmation.
;   This routine does not perform fuel math, clamping, deadtime, AE, PE, or DFCO.
;   Caller must provide final command value.
; -----------------------------------------------------------------------------

L3FCE          EQU   $3FCE

EFI_PW_WRITE:
               STD   L3FCE
               RTS
