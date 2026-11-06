; Single manual-transmission idle-air strategy. Simulation overlay only.
; The original reset/service guard, conversion and motor driver remain resident.
; RPM coordinates are 12.5 RPM. Air words are internal unsigned Q8.8 units.
; All normal state changes occur at the existing phase&3=3 main admission.

integral equ $029D
follower equ $02A0
start_air equ $02A2
start_div equ $02A3
qualify equ $02A4
signature equ $02A5
error equ $0858
p_word equ $086E
scratch equ $0871

.org $9411
mi_stopped:
    JSR mi_init
    JSR mi_target
    JSR mi_compose
    JMP $983D

.org $9537
mi_run:
    LDAA signature
    CMPA #$A5
    BEQ run_ready
    JSR mi_init
run_ready:
    JSR mi_target
    JSR mi_follower
    ; Fade startup air deterministically. No pedal/gear/speed latch.
    TST start_air
    BEQ startup_done
    DEC start_div
    BNE startup_done
    LDAA cal_start_div
    STAA start_div
    DEC start_air
startup_done:
    ; Keep shared bit5 and unowned bit6. Remove every gear-context dependency.
    LDAA <$36
    ANDA #$6C
    STAA <$36
    BRCLR $52,#$20,ac_done
    BSET $36,#$01
ac_done:
    LDAA <$63
    SUBA $0857
    BCS below_target
    BSET $36,#$80
    BRA save_error
below_target:
    NEGA
save_error:
    STAA error
    CLRB
    STD $0859
    ; Hysteresis follows requested RPM, not a fixed 1100/1200 boundary.
    BRSET $36,#$04,retained_capture
    LDAA $01D9
    CMPA cal_tps_enter
    BHI open_loop
    LDAA $0857
    ADDA cal_rpm_enter
    BCS capture
    CMPA <$63
    BCS open_loop
    BRA capture
retained_capture:
    LDAA $01D9
    CMPA cal_tps_exit
    BHI open_loop
    LDAA $0857
    ADDA cal_rpm_exit
    BCS capture
    CMPA <$63
    BCS open_loop
capture:
    BSET $36,#$04
    LDAA qualify
    CMPA cal_qualify
    BHS captured
    INCA
    STAA qualify
captured:
    LDAA qualify
    CMPA cal_qualify
    BLO control
    BSET $36,#$08
    BRA control
open_loop:
    BCLR $36,#$0C
    CLR qualify
control:
    ; No P or integral activity while DFCO owns torque/fuel.
    BRCLR $46,#$08,pi_admitted
    BCLR $36,#$08
    CLR qualify
pi_admitted:
    BRCLR $36,#$04,stall_checked
    LDAA <$63
    CMPA $0868
    BHS stall_checked
    BSET $36,#$10
stall_checked:
    JSR mi_pi
    JSR mi_compose
    JMP $983D

.org $989C
mi_init:
    ; The old retained dual-bank words no longer have controller semantics.
    ; Seed one baseline. No inherited fractional bytes or warm-valid flags.
    LDAA cal_seed
    CLRB
    STD integral
    STD $0862
    STAA $086A
    CLRA
    STD follower
    STD p_word
    STD $0880
    STD $0889
    LDD #$FFFF
    STD $087D
    CLR qualify
    CLR $087F
    CLR $085F
    CLR $086D
    BCLR $36,#$9F
    BCLR $09,#$30
    BCLR $18,#$08
    LDAA cal_start_air
    STAA start_air
    LDAA cal_start_div
    STAA start_div
    LDAA #$A5
    STAA signature
    RTS

mi_target:
    BRSET $38,#$40,target_stall
    LDAA $0283
    LDX #$FF60
    JSR $F4C1
    LDAB $085F
    BEQ target_publish
    CBA
    BHS target_publish
    DECB
    TBA
target_publish:
    STAA $085F
    STAA $0857
target_stall:
    LDAA $0857
    SUBA cal_stall_error
    BHS stall_publish
    CLRA
stall_publish:
    STAA $0868
    LDAA integral
    STAA $086A
    RTS

mi_follower:
    LDAA $01D9
    SUBA cal_tps_exit
    BHI follower_above_closed
    CLRA
follower_above_closed:
    CMPA cal_follower_cap
    BLS follower_requested
    LDAA cal_follower_cap
follower_requested:
    CLRB
    STD scratch
    SUBD follower
    BLS follower_decay
    LDD scratch
    BRA follower_store
follower_decay:
    LDD follower
    SUBD cal_follower_decay
    BHS follower_floor
    CLRA
    CLRB
follower_floor:
    STD follower
    SUBD scratch
    BHS follower_done
    LDD scratch
follower_store:
    STD follower
follower_done:
    LDD follower
    STD $0880
    RTS

mi_pi:
    CLRA
    CLRB
    STD p_word
    STAA $086D
    BRSET $36,#$04,pi_closed
    ; Closed-throttle overspeed can shed air before idle capture. Learning
    ; still requires the separate captured/qualified state below.
    LDAA $01D9
    CMPA cal_tps_exit
    BHI pi_not_admitted
    BRSET $36,#$80,pi_closed
pi_not_admitted:
    JMP pi_return
pi_closed:
    BRCLR $46,#$08,pi_fueled
    JMP pi_return
pi_fueled:
    LDAA error
    SUBA cal_deadband
    BLS pi_return
    STAA $0864
    LDAB cal_kp
    MUL
    SUBD cal_p_limit
    BLS p_uncapped
    LDD cal_p_limit
    BRA p_save
p_uncapped:
    LDAA $0864
    LDAB cal_kp
    MUL
p_save:
    STD p_word
    STAA $086D
    BRCLR $36,#$08,pi_return
    BRSET $3E,#$04,pi_return
    TST start_air
    BNE pi_return
    LDD follower
    BNE pi_return
    ; Directional anti-windup at the previous command rail. The integral also
    ; has explicit numeric bounds independent of the converted step target.
    BRSET $36,#$80,integrate_down
    LDD $0889
    ADDD #$0001
    BEQ pi_return
    LDAA $0864
    LDAB cal_ki_up
    MUL
    ADDD integral
    BCS integral_cap
    STD scratch
    SUBD cal_i_limit
    BHI integral_cap
    LDD scratch
    BRA integral_save
integral_cap:
    LDD cal_i_limit
    BRA integral_save
integrate_down:
    LDD $0889
    BEQ pi_return
    LDAA $0864
    LDAB cal_ki_down
    MUL
    STD scratch
    LDD integral
    SUBD scratch
    BHS integral_save
    CLRA
    CLRB
integral_save:
    STD integral
pi_return:
    LDD integral
    STD $0862
    STAA $086A
    RTS

mi_compose:
    LDAA $0283
    LDX #cal_cold_air
    JSR $F4C1
    STAA $086C
    CLRB
    ADDD integral
    BCC compose_start
    LDD #$FFFF
compose_start:
    ADDA start_air
    BCC compose_ac
    LDD #$FFFF
compose_ac:
    BRCLR $52,#$20,compose_p
    ADDA cal_ac_air
    BCC compose_p
    LDD #$FFFF
compose_p:
    BRSET $36,#$80,compose_sub_p
    ADDD p_word
    BCS compose_cap
    BRA compose_stall
compose_sub_p:
    SUBD p_word
    BHS compose_stall
    CLRA
    CLRB
compose_stall:
    BRCLR $36,#$10,compose_ae
    ADDA cal_stall_air
    BCS compose_cap
    BRA compose_ae
compose_cap:
    LDD #$FFFF
compose_ae:
    ; Preserve the factory IAC-change fuel term before follower and BARO.
    STD scratch
    SUBD $087D
    BCS ae_zero
    STAA $086B
    LDAA $01D9
    CMPA $50A9
    BHS ae_zero
    LDAA $086B
    CMPA $50A8
    BLO ae_zero
    ASLD
    BCS ae_cap
    ASLD
    BCC ae_lookup
ae_cap:
    LDAA #$FF
ae_lookup:
    LDX #$50A2
    JSR $F4B6
    BRA ae_save
ae_zero:
    CLRA
ae_save:
    STAA $087F
    LDD scratch
    STD $087D
    ADDD follower
    BCC compose_done
    LDD #$FFFF
compose_done:
    RTS

.org $9E99
mi_background:
    ; Main and startup own the same target. No cold/warm transfer housekeeping.
    JMP mi_target

.org $9F00
cal_cold_air:
    .byte 120,112,100,80,64,48,32,20,12,4,0,0,0,0,0,0,0
cal_seed:           .byte 38
cal_start_air:      .byte 60
cal_start_div:      .byte 4
cal_tps_enter:      .byte 2
cal_tps_exit:       .byte 3
cal_rpm_enter:      .byte 8
cal_rpm_exit:       .byte 16
cal_qualify:        .byte 16
cal_deadband:       .byte 2
cal_kp:             .byte 64
cal_ki_up:          .byte 4
cal_ki_down:        .byte 4
cal_p_limit:        .word $1800
cal_i_limit:        .word $B400
cal_follower_cap:   .byte 40
cal_follower_decay: .word $0080
cal_stall_error:    .byte 16
cal_stall_air:      .byte 12
cal_ac_air:         .byte 5

.org $A2B0
mi_slow:
    ; All strategy now runs once at the main IAC admission. No second updater.
    RTS
