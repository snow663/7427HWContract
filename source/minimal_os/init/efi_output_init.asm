; -----------------------------------------------------------------------------
; EFI_OUTPUT_INIT
;
; Minimal EFI output hardware init candidate for 7427 hardware-contract OS.
;
; Purpose:
;   Establish one-time ASIC/output state required before runtime EFI_PW_WRITE.
;
; Status:
;   Static evidence: provisional
;   Bench evidence: pending
;
; Notes:
;   EFI_PW_WRITE owns the runtime pulsewidth command at $3FCE/$3FCF.
;   This routine owns only one-time setup/state.
; -----------------------------------------------------------------------------

L3FC0          EQU   $3FC0
L3FFA          EQU   $3FFA
L3FCC          EQU   $3FCC
L3FEA          EQU   $3FEA

EFI_OUTPUT_INIT:
               LDX   #L3FC0
               CLRA
               CLRB
EFI_INIT_CLEAR_LOOP:
               STD   0,X
               INX
               INX
               CPX   #L3FFA
               BNE   EFI_INIT_CLEAR_LOOP

; Optional pending bench proof:
;              LDD   #$D000
;              STD   L3FCC
;              LDD   #$DFFF
;              STD   L3FEA

               RTS
