; Rev B deceleration spark: retain subtraction only during fuel cut and above
; requested idle + the shared IAC release margin. No post-fuel recovery tail.
; The active path preserves the resident byte wrap/subtract and latch semantics
; (the latch also selects the DFCO minimum spark limit at AAF7).
; Cleanup never writes 01F2: startup also owns that word.
    .org $9F40
decel_gate:
    BRCLR $46,#$08,decel_clear
    LDAA $0857
    ADDA $9F17
    BCS decel_clear
    CMPA $63
    BHS decel_clear
    BSET $51,#$20
    CLRA
    CLRB
    STD $01F2
    LDAB $4152
    LDAA $01F9
    SUBA $413C
    BMI decel_save
    ABA
    TAB
decel_save:
    STAB $0208
    LDD $01FD
    SUBB $0208
    SBCA #0
    STD $01FD
    JMP $A9E0
decel_clear:
    BCLR $51,#$20
    CLR $0208
    LDD $01FD
    JMP $A9E0
