		;      OBJECT FILE: BMHM
		;
		;     DISASSEMBLED FOR THE P2
		;      BY THE CATS ECM ANALYZER
		;           RELEASE 4.4
		;
		;      06-26-1996
		;=============================================
       			ORG     $7100
          
7100:  L7100   	LDS     #$03FF

			;
			; SET UP CPU MODE'S
			;
7103:          LDX     #$1000				; INDEX CPU REG'
7106:          LDAA    #$03					; SET REG'S TO 3000h
7108:          STAA    $3D,X				; CPU INIT REG

			
710A:          LDX     #$3000				; NEW INDEX CPU REG'S

			;
			; SET OPTION REG 
			;
			; b7 1	ADPU	A/D SYS PWR ENABLED
			; b6 0  CSEL  	CLK SEL, 0 = A/D & EEPROM USE E CLK
			; b5 1  IRQE*	1 = IRQ ON FALLING EDGE
			; b4 1	DLY* 	4K E CLK CYCLES 
			;
			; b3 1  CME		CLK MON ENABLE, 1 = ENAB;ED
			; b2 0	FCME*	FORCE CLK MON 
			; b1 0  CR1*	COP TMR RATE MSB	00 = = E/2^15
			; b0 0	CR0*	COP TMR RATE LSB	(ABOUT 10 msec)
			;
710D:          LDAA    #$B8					; 1011 1000
710F:          STAA    $39,X				; OPTION REG

7111:          LDAA    #$03					; 
7113:          STAA    $24,X			    ; TMSK2

7115:          BCLR    $38,X,#$20			; CLR b5, OPT2, 4X CLK OUT

			;
			; SET OPTION REG 
			;
			; b7 0 -	
			; b6 0 - 
			; b5 0 - 
			; b4 1 PTCON  1 = CONFIG REG CAN NOT BE PGMED or ERASED	
			;
			; b3 1 BPRT3  1000b = 288 BYTES BLK PROT 
			; b2 0 BPRT2		( xEE0 - xFFF)
			; b1 0 BPRT1  
			; b0 0 BPRT0	
			;
7118:          LDAA    #$1B					; 0001 1011, 
711A:          STAA    $35,X				; BPROT

711C:          JSR     LCC7C

711F:          CLRA    
7120:          STAA    0,X
7122:          STAA    $08,X

7124:          LDAA    #$7F
7126:          LDAB    #$FF
7128:          STD     L306E

712B:          LDX     #$B93A

		;--------------------------------------------
		; AFR MD BYTE 1 0000 0100 
		;
		; b7 1 = DE-LATCH
		; b6 1 = MAT SENSOR
		; b5 1 = 180 DEG OFFSET 
		; b4 1 = ASDF CRANK
		;
		; b3 1 = ACCEL ENRICH LMT OPTION  
		; b2 1 = SYNC FUEL AT IDLE (TBI)
		; b1 1 = AIR MANAGE 
		; b0 1 = CPI/PFI MODE
		;--------------------------------------------
712E:          LDY     #$400B				; AFR MD BYTE 1, 0000 0100
7132:          BRCLR   0,Y,#$01,L713A		; BR IF b0, (1 = CPI/PFI MODE)

7137:          LDX     #$B91A				; 47,386d
713A:  L713A   STX     L3FFC				; I/O D PORT ..
713D:          JSR     LF3ED				; Very short delay (RTS) 

7140:          LDD     L3FFC          		; I/O D PORT ..
7143:          JSR     LF3ED				; Very short delay (RTS)
7146:          ANDB    #$FB					; 1111 1011
7148:          ORAB    #$08					; 0000 1000
714A:          STD     L3FFC          		; I/O D PORT ..



714D:          LDX     #$3000				; INDEX CPU REG'S
7150:          LDD     $2E,X				; SCSR, GET SCI STATUS & RX BYTE

7152:          LDAB    #$26
7154:          STAB    $2D,X	  			; SCI CNT'L REG #2 
7156:          LDX     #$3FC0				; HARDWARE
7159:          CLRA    
715A:          CLRB    
715B:  L715B   STD     0,X
715D:          INX     
715E:          INX     
715F:          CPX     #$3FFA				; HARDWARE
7162:          BNE     L715B

7164:          LDX     #$0036
7167:          LDD     #$00CA
716A:          JSR     LF2FD

716D:          LDX     #$0100
7170:          LDD     #$019D
7173:          JSR     LF2FD

7176:          LDX     #$0800
7179:          LDD     #$0100
717C:          JSR     LF2FD


			;
			; CLR RAM 
			; $0360 - $03FF
			;
717F:          LDX     #$0360				; 8192 MSG LEN CNT'R
7182:  L7182   CLR     0,X					; CLR RAM 
7184:          INX     						; NEXT ADDR
7185:          CPX     #$03FF				; CK FOR DONE
7188:          BNE     L7182				; LP TILL DONE

718A:          JSR     LF20D				;
718D:          JSR     LF245				;

7190:          JSR     LC56F				; A/D READ BATTERY VOLTAGE

			;
			; CK A/D VALUE
			;
7193:          LDAA    L082F				; A/D VAL
7196:          CMPA    #$64					; 1.20 VDC
7198:          BCC     L71C3				; BR IF A/D VAL GT 64, (1.20 VDC)

719A:          CMPA    #40					;
719C:          BCS     L71C3				; BR IF A/D VAL LT 40d (0.56 VDC)

719E:          BSET    L0050,#$08			; SET b3, IF A/D 0.56 VDC - 1.20 VDC

71A1:          LDAA    L00A6			   	; TPS A/D
71A3:          CMPA    #252				    ; 5.04 VDC
71A5:          BCS     L71C3				;

71A7:          LDAA    L082D
71AA:          CMPA    #252
71AC:          BCS     L71C3				;

71AE:          LDAA    L00A5
71B0:          CMPA    #5
71B2:          BHI     L71C3				;

71B4:          BSET    L0044,#$01			; SET b0, FACTORY TEST ENTERED

71B7:          CLR     L0001
71BA:          LDX     #$B93A
71BD:          STX     L3FFC           		; I/O D PORT ..
71C0:          JMP     L7459
 ;
71C3:  L71C3   BCLR    L0005,#$10
71C6:          LDAA    L303F
71C9:          CMPA    #$0B
71CB:          BEQ     L71D2				;

71CD:          BSET    L003A,#$04
71D0:          BRA     L71EC
		;----------------------------------------

71D2:  L71D2   LDX     #$4008				; EPROM ID BYTE
71D5:          JSR     LF2AA
71D8:          LDAA    L4008
71DB:          CPY     L4006
71DF:          BNE     L71E5				;

71E1:          CMPA    #$0031
71E3:          BEQ     L720C				;

71E5:  L71E5   CMPA    #$AA
71E7:          BEQ     L720C
71E9:          BSET    L003A,#$02
71EC:  L71EC   BSET    L0005,#$10

71EF:          LDD     L3FFC          		; I/O D PORT ..
71F2:          JSR     LF3ED				; Very short delay (RTS)
71F5:          ANDB    #$F7
71F7:          STD     L3FFC          		; I/O D PORT ..

71FA:          BSET    L001A,#$20			; SET b5
71FD:          BSET    L000F,#$20			; SET b5
											;
7200:          JSR     LF326				;
7203:          STAA    L0015				;
											;
7205:          LDAA    L082F				;
7208:  L7208   CMPA    #$64					;
720A:          BCC     L7208				;

720C:  L720C   JSR     LF326				;
720F:          CMPA    L0015				;
7211:          BEQ     L723C				; 

7213:          LDX     #$0000				;
7216:          LDD     #$0B					;
7219:          JSR     LF2FD				;
											;
721C:          LDX     #$000B
721F:          LDD     #$002B
7222:          JSR     LF2FD

7225:          LDX     #$029D
7228:          LDD     #$00B1
722B:          JSR     LF2FD
722E:          LDAA    L5B24				; 64d, TPS MIN BIN VAL, (IDLE)

7231:          LDAB    #$80					; 127
7233:          STD     L02F6				; FILT TPS (XMISH)
											;
7236:          JSR     LF280				;

7239:          BSET    L0046,#$40			; SET b6, NON VOL MEM BOMBED
723C:  L723C   BSET    L0086,#$08			; SET b3
											;
723F:          LDY     #$0000				;
7243:          LDX     #$032B				;
7246:          LDAB    #$0034
7248:          CLRA    
7249:          PSHB    
724A:  L724A   ADDA    0,X
724C:          BEQ     L7252				;

724E:          LDY     #$0001
7252:  L7252   DEX     
7253:          DECB    
7254:          BNE     L724A

7256:          PULB    
7257:          CPY     #$0000
725B:          BEQ     L7260

725D:          TSTA    
725E:          BEQ     L726B

7260:  L7260   LDAA    #$80
7262:  L7262   INX     
7263:          STAA    0,X

7265:          DECB    						;
7266:          BNE     L7262				;

7268:          BSET    L003A,#$40			; SET b6, 
											;
726B:  L726B   LDAA    L4132				; 3.8 Deg, INTIAL SPK (256/90)
											; (This val is sub'ed from total spk adv
726E:          CLRB    
726F:          STD     L01F6


			;
			; HOUSEKEEP ERR 21 CNT'R
			;  HIGH TPS
			;
7272:          LDAA    L001F				; ERR 21 CNT'R
7274:          BEQ     L727E				; BR IF ERR CNT = 0

7276:          CMPA    L5B1E				; IF ERR 21 CNT'S L.T. ENABLE RESET OF ERR  21
7279:          BCC     L727E				; BR IF CNTS LT 5

727B:          DECA   						; DECR CNT'R    
727C:          STAA    L001F				; ERR 21 CNT'R


			;
			; HOUSEKEEP ERR 22 CNT'R
			;  LOW TPS
			;
727E:  L727E   LDAA    L0020				; ERR 22 CNT'R
7280:          BEQ     L728A				; BR IF ERR CNT = 0

7282:          CMPA    L5B21				; IF ERR 22 CNT'S L.T. ENABLE RESET OF ERR 22
7285:          BCC     L728A

7287:          DECA   						; DECR CNT'R    
7288:          STAA    L0020				; ERR 22 CNT'R


			;
			; HOUSEKEEP ERR 24 CNT'R
			;
728A:  L728A   LDAA    L0021			    ; ERR 24 CNT'R
728C:          BEQ	   L7296				; BR IF ERR CNT = 0     

728E:          CMPA    L5B42				; 7 ERR CNTS MIN TO SET ERR 24
7291:          BCC     L7296				; BR IF ERR CNT LT 7

7293:          DECA    						; DECR CNT'R
7294:          STAA    L0021			    ; ERR 24 CNT'R


			;
			; HOUSEKEEP ERR 28 CNT'R
			; ERR 28, PRESS SW MANIFOLD
			;
7296:  L7296   LDAA    L0022				; ERR 28 CNT'R
7298:          BEQ     L72A2				; BR IF ERR CNT = 0

729A:          CMPA    L5B52				; 10 ERR CNTS MIN TO SET ERR 28
729D:          BCC     L72A2				; BR IF ERR CNT LT 10

729F:          DECA    
72A0:          STAA    L0022				; ERR 28 CNT'R

			;
			; HOUSEKEEP ERR 37 CNT'R
			;
72A2:  L72A2   LDAA    L0023				; ERR 37 CNT'R
72A4:          BEQ     L72AE				; BR IF ERR CNT = 0

72A6:          CMPA    L5B58				; 8 ERR CNTS MIN TO SET ERR 37
72A9:          BCC     L72AE				; BR IF CNT LT 8

72AB:          DECA   						; DECR CNT'R
72AC:          STAA    L0023				; ERR 37 CNT'R


			;
			; HOUSEKEEP ERR  CNT'R
			; ERR 38,  BRAKE ON 
			;
72AE:  L72AE   LDAA    L0024				; ERR 38 CNT'R
72B0:          BEQ     L72BA				; BR IF ERR CNT = 0
											; 
72B2:          CMPA    L5B5E				; ERR COUNT THRESH
72B5:          BCC     L72BA				; BR IF ERR CNT LT THRESH
											    
72B7:          DECA   						; DECR ERR CNT'R
72B8:          STAA    L0024				; ERR 38 CNT'R

			;
			; BOOKKEEPS ERR 38 CNT'R
			;	 ERR 38, BRAKE OFF
			;
72BA:  L72BA   LDAA    L0025			    ; ERR 38, BRAKE OFF
72BC:          BEQ     L72C6				; BR IF ERR CNT = 0
72BE:          CMPA    L5B62				; ERR COUNT THRESH
72C1:          BCC     L72C6				; BR IF ERR CNT LT THRESH

72C3:          DECA   						; DECR ERR CNT'R    
72C4:          STAA    L0025

			;
			; BOOKKEEPS ERR  CNT'R
			;  ERR 66,  3 -> 2 SHFT QUAD DVR FAIL
			;
72C6:  L72C6   LDAA    L0026				; ERR 66 CNT'R
72C8:          BEQ     L72D2				; BR IF ERR CNT = 0
72CA:          CMPA    L5B75				; ERR COUNT THRESH
72CD:          BCC     L72D2				; BR IF ERR CNT LT THRESH

72CF:          DECA   						; DECR ERR CNT'R    
72D0:          STAA    L0026				; ERR 66 CNT'R

			;
			; BOOKKEEPS ERR  CNT'R
			;  ERR 66,  3 -> 2 SHFT QUAD DVR FAIL
			;
72D2:  L72D2   LDAA    L0027				; ERR 66 CNT'R
72D4:          BEQ     L72DE				; BR IF ERR CNT = 0
72D6:          CMPA    L5B76				; ERR COUNT THRESH
72D9:          BCC     L72DE				; BR IF ERR CNT LT THRESH

72DB:          DECA       					; DECR ERR CNT'R    
72DC:          STAA    L0027				; ERR 66 CNT'R

			;
			; BOOKKEEPS ERR  CNT'R
			; ERR 68, XMISH SLIPPING
			;
72DE:  L72DE   LDAA    L0028				; ERR 68 CNT'R
72E0:          BEQ     L72EA				; BR IF ERR CNT = 0
72E2:          CMPA    L5B7A				; ERR COUNT THRESH
72E5:          BCC     L72EA				; BR IF ERR CNT LT THRESH

72E7:          DECA       					; DECR ERR CNT'R    
72E8:          STAA    L0028				; ERR 68 CNT'R

			;
			; BOOKKEEPS ERR 72  CNT'R
			; ERR 72, 
			;
72EA:  L72EA   LDAA    L0029				; ERR 72 CNT'R
72EC:          BEQ     L72F6				; BR IF ERR CNT = 0
72EE:          CMPA    L5B8C				; ERR COUNT THRESH
72F1:          BCC     L72F6				; BR IF ERR CNT LT THRESH
											;
72F3:          DECA    						; DECR ERR CNT'R    
72F4:          STAA    L0029				; ERR 72 CNT'R

			;
			; BOOKKEEPS ERR 72  CNT'R
			; ERR 73,  FORCE MOTOR CURRENT 
			;
72F6:  L72F6   LDAA    L002A				; ERR 73 CNT'R
72F8:          BEQ     L7302				; BR IF ERR CNT = 0
72FA:          CMPA    L5B90				; ERR COUNT THRESH
72FD:          BCC     L7302				; BR IF ERR CNT LT THRESH

72FF:          DECA    						; DECR ERR CNT'R    
7300:          STAA    L002A				; ERR 73 CNT'R

			;
			; BOOKKEEPS ERR   CNT'R
			; ERR 81, QUAD DVR 1 & SHFT B ERR 
			;
7302:  L7302   LDAA    L002B				; ERR 81 CNT'R
7304:          BEQ     L730E				; BR IF ERR CNT = 0
7306:          CMPA    L5BA3				; ERR COUNT THRESH
7309:          BCC     L730E				; BR IF ERR CNT LT THRESH

730B:          DECA    						; DECR ERR CNT'R    
730C:          STAA    L002B				; ERR 81 CNT'R

			;
			; BOOKKEEPS ERR   CNT'R
			; ERR 82, QUAD DVR 1 & SHFT A ERR 
			;
730E:  L730E   LDAA    L002C			    ; ERR 82 CNT'R
7310:          BEQ     L731A				; BR IF ERR CNT = 0
7312:          CMPA    L5BA5				; ERR COUNT THRESH
7315:          BCC     L731A		    	; BR IF ERR CNT LT THRESH

7317:          DECA     					; DECR ERR CNT'R    
7318:          STAA    L002C			    ; ERR 82 CNT'R

			;
			; BOOKEEP ERR .. CNTR 
			; ERR 83,  QUAD DVR 1 ERR
			;
731A:  L731A   LDAA    L002D				; ERR 83 CNT'R
731C:          BEQ     L7326				; BR IF ERR CNT = 0
731E:          CMPA    L5BA7				; ERR COUNT THRESH
7321:          BCC     L7326		    	; BR IF ERR CNT LT THRESH

7323:          DECA     					; DECR ERR CNT'R    
7324:          STAA    L002D				; ERR 83 CNT'R

			;
			; BOOKEEP ERR .. CNTR 
			; ERR 86,  LO RATIO
			;
7326:  L7326   LDAA    L002E				; ERR .. CNT'R
7328:          BEQ     L7332				; BR IF ERR CNT = 0
732A:          CMPA    L5BA9 				; ERR COUNT THRESH
732D:          BCC     L7332		    	; BR IF ERR CNT LT THRESH

732F:          DECA     					; DECR ERR CNT'R   
7330:          STAA    L002E

			;
			; BOOKEEP ERR .. CNTR 
			; ERR 86,  LO RATIO
			;
7332:  L7332   LDAA    L002F				; ERR 86 CNT'R
7334:          BEQ     L733E				; BR IF ERR CNT = 0

7336:          CMPA    L5BAB				; ERR COUNT THRESH
7339:          BCC     L733E			    ; BR IF ERR CNT LT THRESH

733B:          DECA    						; DECR ERR CNT'R    
733C:          STAA    L002F				; ERR 86 CNT'R

			;
			; BOOKEEP ERR .. CNTR 
			;  ERR ...         
			;
733E:  L733E   LDAA    L0030				; ERR .. CNT'R
7340:          BEQ     L734A				; BR IF ERR CNT = 0

7342:          CMPA    L5BC0				; ERR COUNT THRESH
7345:          BCC     L734A				; BR IF ERR CNT LT THRESH

7347:          DECA    						; DECR ERR CNT'R    
7348:          STAA    L0030				; ERR .. CNT'R


			;
			; BOOKEEP ERR 89 CNTR 
			; MAX ADPT LONG SHIFT
			;
734A:  L734A   LDAA    L0031				; ERR 89 ERR CNT'R 
734C:          BEQ     L7356				; BR IF ERR CNT = 0
734E:          CMPA    L5BCA				; ERR COUNT THRESH
7351:          BCC     L7356

7353:          DECA    						; DECR ERR CNT'R
7354:          STAA    L0031

7356:  L7356   BRCLR   L001E,#$04,L7368		; BR IF NOT b2, 


735A:          LDAA    L0031				; ERR 89 ERR CNT'R 
735C:          CMPA    L5BCA				; ERR 89 CNT'R THRESH 
735F:          BCC     L7368				; BR IF 
7361:          INCA    
7362:          INCA    
7363:          STAA    L0031				; ERR 89 ERR CNT'R 

7365:          BCLR    L001E,#$04
7368:  L7368   BCLR    L0019,#$04
736B:          BCLR    L0019,#$02

			;----------------------------------------------
			; AFR MD BYTE 5,	 0001 0000, (DIG I/O)
			;
			; b7 1 = MAN, (0 = TCC)
			; b6 1 = TCC (Non Elect xmish)
			; b5 1 = Not Used 
			; b4 1 = CONV OVER HEAT PROTECTION
			;
			; b3 1 = BURST KNOCK RETARD
			; b2 1 = A/C CLUTCH CNT'L, 0 = CPI TUNE
			; b1 1 = Not Used
			; b0 1 = 1 DO RPM/MPH LMT, (GOV'R OPT)
			;
			;----------------------------------------------
736E:          LDX     #$400F				; INDEX AFR MD WD
7371:          BRCLR   0,X,#$80,L7378		; BR IF NOT b7 

7375:          BCLR    L0017,#$20

    		;--------------------------------------------------
    		; ERR 89,  MAX ADPT LONG SHIFT
    		;                                  
    		;--------------------------------------------------
7378:  L7378   LDX     #$5B00				; INDEX ERR MASKS
											;
737B:          LDAA    L0032				;
737D:          CMPA    $C7,X			   	; $5BC7	
737F:          BCS     L7383				;

7381:          STAB    L0032				;
											;
7383:  L7383   LDAA    L0033				;
7385:          CMPA    $C8,X				;
7387:          BCS     L738B				;

											;
7389:          STAB    L0033				;
738B:  L738B   LDAA    L0034				;
738D:          CMPA    $C9,X				;
738F:          BCS     L7393				;

7391:          STAB    L0034				;

7393:  L7393   LDAA    L082E				; MAP A/D
7396:          STAA    L01C6				;
7399:          STAA    L01C3				; FILT TRANS MAP

739C:          SUBA    #26					;

739E:          LDAB    #151					;
73A0:          MUL     						;
73A1:          ADDD    #64					;
73A4:          ASLD    						;
73A5:          BCC     L73AA				;

73A7:          LDD     #$FFFF
73AA:  L73AA   STAA    L01C0				; CURRENT MAP VALUE
73AD:          STAA    L01C7
73B0:          JSR     LC614

73B3:          BSET    L004E,#$01			; SET b0
73B6:          BSET    L0043,#$80			; SET b7

73B9:   	   BCLR    L0004,#$10			; CLR b4, HOT RESTART

73BC:          LDAA    L0006				; COOL VALUE
73BE:          PSHA    
73BF:          JSR     LC96A				; DO COOL SUBROUTINE
73C2:          JSR     LC9F7
73C5:          JSR     LCA6B

73C8:          LDAA    L0006				; COOL VALUE
73CA:          STAA    L0282				; START UP COOL

73CD:          PULB    
73CE:          CMPB    L495A 				; 98c, Min shut down thresh for
											;		 HOT restart DETECT ENABLE 
73D1:          BCS     L73DB				; BR IF COOL LT 98c

73D3:          CMPA    L495B				; 77c, MIN START UP THRESH FOR HOT RESTART
73D6:          BCS     L73DB              	; BR IF COOL LT 77c


73D8:          BSET    L0004,#$10			; SET b4, HOT RESTART

                ;----------------
                ; INIT o2 VAL'S
                ;----------------
73DB:  L73DB   JSR     L925E				; GO SET UP IAC

			;
			; SET UP INITAL o2 VOLATAGE
			;
73DE:          LDAA    L48BE				; 450 Mv, INIT VALUE
73E1:          STAA    L01D5				; o2 VOLTS * 226 (A/D RESULT) 
73E4:          STAA    L01D0				; o2 VOLTAGE, 1
73E7:          STAA    L01D2				; o2 VOLTAGE, 2

73EA:          JSR     LB1AC
73ED:          JSR     LB0E4

73F0:          LDAA    L01D9
73F3:          STAA    L01DC
73F6:          STAA    L01DA
73F9:          STAA    L01DB
73FC:          STAA    L01DE

73FF:          LDAA    L48A5				; 77 A/D BIN MAX FOR CLOSED VALVE (EGR)
7402:          STAA    L01B5
7405:          JSR     LD14E

7408:          LDAA    L01A1				; A/D RESULT
740B:          CLRB    
740C:          STD     L01A2
740F:          JSR     L74D3

7412:          CLRB    
7413:          LDAA    L00A8
7415:          CMPA    L4071				; IF COOLANT G.T. 80c INIT CONV TEMP TO
                       						; L406E, (DEG c + 40) * (256/192)
7418:          BCS     L741D				;

741A:          LDAB    L4072				; 300 DEG C HOT COOL CONV INIT TEMP,  CAL = (DEG -300)/3
741D:  L741D   STAB    L0078				; CAT TEMP

741F:          LDD     L3FCA
7422:          STD     L0205

7425:          LDD     L3012				; GET TIC 2 VALUE
7428:          STD     L0851				; SAVE TIC 2 CNT

742B:          LDAA    L48E7				; 14.7,  STOCH AFR
742E:          STAA    L024A				; AFR

7431:          LDAA    #$0E					; INIT MJR LOOP CNT'R
7433:          STAA    L0002				; MAJOR LOOP COUNTER

7435:          LDAA    #128					; ZERO OUT BLM
7437:          STAA    L0248 				; BLM 

743A:          LDAA    #20					;
743C:          STAA    L0049				;

743E:          JSR     LF28E

			;
			; RESET COP 1 & 2
			;
7441:          LDAA    #$55					;
7443:          STAA    L303A				; ARM COP TIMER CLEARING MECHANISM

7446:          LDAA    #$AA					; 
7448:          STAA    L303A				; CLEAR COP

744B:          LDAA    #$40					;
744D:          STAA    L004C				;
											;
744F:          BRCLR   L0004,#$08,L7459		; BR IF NOT b3,  BAD SHUT DOWN

7453:          LDAA    L4D96				; IF STALL, INIT CRANK DRP COUNTER = 5
7456:          STAA    L02CE				; DRP COUNTER

7459:  L7459   LDAA    #$FF					; RESET ALL TFLG1
745B:          STAA    L3023				; TFLG 1

745E:          LDD     L300E				; 16 BIT FREE RUN CNT'R
7461:          ADDD    #8					;
7464:          STD     L301A				; TOC3

7467:          LDAA    #$A0					; TOC1, TOC 3 INT ENABLE
7469:          STAA    L3022				; TMSK1

746C:  L746C   BRCLR   L0051,#$04,L74B3		; BR IF NOT b2

7470:          LDX     L029B
7473:  L7473   CPX     #$0400				; 1024
7476:          BNE     L747E				; BR IF NOT 

7478:          LDX     #$0800				; 2084
747B:          STX     L029B
747E:  L747E   CPX     #$0900				; 2304
7481:          BEQ     L74AD				;

7483:          SEI     

7484:          LDD     0,X
7486:          STD     0,X

7488:          LDD     $02,X
748A:          STD     $02,X

748C:          LDD     $04,X
748E:          STD     $04,X

7490:          LDD     $06,X
7492:          STD     $06,X

7494:          LDD     $08,X
7496:          STD     $08,X

7498:          LDD     $0A,X
749A:          STD     $0A,X

749C:          LDD     $0C,X
749E:          STD     $0C,X

74A0:          LDD     $0E,X
74A2:          STD     $0E,X

74A4:          LDAB    #010
74A6:          ABX     
74A7:          STX     L029B

74AA:          CLI     
74AB:          BRA     L7473
		;----------------------------------------


74AD:  L74AD   CLR     L029B
74B0:          BCLR    L0051,#$04

74B3:  L74B3   CLI     
74B4:          LDX     #$03B0
74B7:  L74B7   LDAA    0,X
74B9:          BNE     L74C3
74BB:          CPX     #$03FF
74BE:          BCC     L74C3				;

74C0:          INX     

74C1:          BRA     L74B7
		;----------------------------------------

74C3:  L74C3   LDD     L02D1
74C6:          BEQ     L74CD				;

74C8:          CPX     L02D1
74CB:          BCC     L74D0				;

74CD:  L74CD   STX     L02D1
74D0:  L74D0   WAI     
74D1:          BRA     L746C
		;----------------------------------------

74D3:  L74D3   LDD     #$D000
74D6:          STD     L3FCC

74D9:          JSR     LF3ED				; Very short delay (RTS)
74DC:          LDD     #$DFFF
74DF:          STD     L3FEA

74E2:          JSR     LF3ED				; Very short delay (RTS)

74E5:          LDAA    #$01					; 2nd GR
74E7:          STAA    L00D9  				; CURRENT GEAR

74E9:          RTS     
	;---------------------------------------------


 	;*********************************************
	; IRQ INTERUPT VECTOR HANDLER
	;
	;
	;********************************************
74EA:          BRCLR   L0044,#$01,L74F1		; BR IF NOT b0, FACTORY TEST ENTERED

74EE:          JMP     LFC11
 

74F1:  L74F1   LDD     L300E				; 16 BIT FREE RUN CNT'R
74F4:          PSHB    
74F5:          PSHA  

        ;---------------------------------------------
    	; KNOCK WINDOW DELAY TIME vs RPM
    	; USES RPM/12.5
    	;
    	; TBL = MSEC * 131.072
        ;---------------------------------------------
74F6:          LDAB    L0062 				; ENGINE RPM/25
74F8:          LSRB    						; (RPM/12.5)/2
74F9:          ANDB    #$FE					; 1111 1110

74FB:          LDX     #$465D				; KNOCK WINDOW DELAY TIME
74FE:          ABX     						; ADJ THE INDEX FOR RPM VALUE

74FF:          PULA    						;
7500:          PULB    						;

7501:          ADDD    0,X					; ADD TBL VAL TO D
7503:          STD     L3016				; TOC 1


											
7506:          LDX     #$3062				; 
7509:          BCLR    0,X,#$40				; CLR b6
750C:          BSET    0,X,#$40				; SET b6
											;
750F:          BRSET   L0044,#$10,L7516		; BR IF b4, IGNITION OFF 

7513:          BSET    L0050,#$20			; SET b5

7516:  L7516   LDAB    #$FF					; 1111 1111
7518:          STAB    L306F				; 


			;
			; READ MAP A/D VALUE
			;
751B:          BRCLR   L0050,#$01,L752E		;

751F:          LDAA    #$05					' SET A/D MODE
7521:          STAA    L3030				; A/D CNT'L REG
			;
			; SHORT DELAY
			;
7524:          ASLD    
7525:          MUL     
7526:          MUL     
7527:          MUL     
7528:          LDAA    L3031				; GET A/D RESULT, CH 1
752B:          STAA    L082E				; SAVE MAP A/D

752E:  L752E   BRCLR   L004F,#$10,L7535		; BR IF NOT b4, RUN FUEL

7532:          JMP     L7650
			;----------------------------------------------



			;----------------------------------------------
			;
			;
			;
			;----------------------------------------------
7535:  L7535   LDD     L0068				; RPM/?
7537:          STD     L006A				;

7539:          BRSET   L0044,#$10,L7548		; BR IF b4, IGNITION OFF 

753D:          LDAB    L02CD				; DPR CNT'R
7540:          INCB    						; INCR DPR CNT'R
7541:          BEQ     L7552				; BR IF ZERO or ROLL OVER

7543:          STAB    L02CD				; DPR CNT'R

7546:          BRA     L7552
		;----------------------------------------

			;
			; LOOP HERE FOR DRP HOLD OFF
			;
7548:  L7548   LDX     #$3000				; INDEX CPU REG'S
											;
754B:          LDAA    #$01					; CLR TIC3 FLAG
754D:          STAA    $23,X				; TFLG1 
754F:          JMP     L77C6
        
            ;---------------------------------------------
        	; LK UP HOLD OFF FOR n DRP'S vs COOL
			;
        	; TBL = DRP'S
            ;---------------------------------------------
7552:  L7552   LDAA    L0006				; COOLANT
7554:          LDX     #$4DCD				; DPR TBL
7557:          JSR     LF4C1				; 2d LK UP 
755A:          CMPA    L02CD				; DPR CNT'R
755D:          BCC     L7548				; BR IF CURRENT DRP'S ARE < TBL VAL 

755F:          LDX     #$400C				; AFR MD BYTE 2	 1011 0111 <---****
7562:          BRCLR   0,X,#$04,L7579		; BR IF NOT b2, CRANK FUEL ALL INJ'S EACH DRP

7566:          LDD     L02CF				; BPW
7569:          JSR     L7827				;
											;
756C:          STD     L024C				; SYNC BPW


756F:          LDX     #$400B				; AFR MD BYTE 1 0000 0100
7572:          BRSET   0,X,#$10,L757C		; BR IF b4,  1 = ASDF CRANK 

7576:          JMP     L762A
 

7579:  L7579   JMP     L7630
 		;----------------------------------------------


		;----------------------------------------------
757C:  L757C   BRCLR   L0019,#$40,L7587		; BR IF NOT b6, 

7580:          LSRD    						; n/2
7581:          STD     L024C				; SYNC BPW

7584:          JMP     L762A
 

7587:  L7587   ADDB    L0256              	; BPW BIAS (Msec)
758A:          ADCA    #0					; ROUND OFF
758C:          BPL     L7591

758E:          LDD     #32767				; USE MAX VALUE FOR BPW
7591:  L7591   STD     L0250				; BPW


		;----------------------------------------------
7594:          LDX     #$3000				; INDEX CPU REG'S
											;
7597:          BRSET   $23,X,#$01,L75F7		; TFLG1, INPUT CAPT,  

759B:          LDAA    L02CD				; DPR CNT'R
759E:          CMPA    #$01					; 1 DRP ?
75A0:          BNE     L75A7				; BR IF DRP CNT NOT = 1

75A2:          BSET    L0053,#$20			; SET b5, (A) INJECTORS FIRED AT 1st DRP

75A5:          BRA     L75CB
		;----------------------------------------

75A7:  L75A7   BRCLR   L0053,#$20,L75CB		; BR IF NOT b5, (A) INJECTORS FIRED AT 1st DRP 

75AB:          PSHX    						;
75AC:          LDX     #$0250				; BPW
75AF:          LDAA    L4960				; 0 MULT, CRANK BPW FOR 2ND INJ ON 
75B2:          JSR     LF550				; MUL 8X16 Subroutine
											;
75B5:          PULX    						;
75B6:          ASLD    						; N x 2
75B7:          BCC     L75BC				; BR IF NO OVERFLOW

75B9:          LDD     #$FFFF				; USE MAX VALUE
75BC:  L75BC   STD     L0250				; SAVE BPW

75BF:          LDAA    L02CE				; DRP COUNTER
75C2:          DECA    						; DECR DRP COUNT
75C3:          CMPA    #255					; CK IF DRP CNT = 255
75C5:          BNE     L75C8				; BR IF NOT = 255

75C7:          INCA    						; INCR COUNTER
75C8:  L75C8   STAA    L02CE				; DRP COUNTER
											;
75CB:  L75CB   BSET    $20,X,#$03			; SET b0 & b1, TCTL1, 		
75CE:          BSET    $0B,X,#$08			; SET b3, COMP FORCE 5
											
75D1:          JSR     L785A				;
											

			;
			; SET UP FOR BPW TO CPU TIMER
			;
75D4:          LDD     L0250				; BPW
75D7:          ASLD    						; BPW x 2
75D8:          BCC     L75DD				; BR IF NO OVERFLOW

75DA:          LDD     #$FFFF				; USE MAX VALUE
75DD:  L75DD   ADDD    $0E,X				; 16 BIT FREE RUN CNT'R
75DF:          STD     L0825				; TIC4/TOC5 RESULT
											;
75E2:          BCLR    $20,X,#$01			; CLR b0, 
											;
75E5:          LDD     $0E,X				; 16 BIT FREE RUN CNT'R
75E7:          ADDD    #2					;
75EA:          CPD     L0825				; TIC4/TOC5 RESULT
75EE:          BPL     L75F3				;

75F0:          LDD     L0825				; TIC4/TOC5 RESULT
75F3:  L75F3   STD     $1E,X				; TIC4/TOC5

75F5:          BRA     L7630
		;----------------------------------------

75F7:  L75F7   LDAA    #$01					; IN CAPT, #3
75F9:          STAA    $23,X				; CLR TFLG 1 

75FB:          CLR     L084E
75FE:          BSET    $20,X,#$0C			; SET b2, b3
7601:          BSET    $0B,X,#$10			; SET b4
7604:          BCLR    L0053,#$20			; CLR b5,(A) INJECTORS FIRED AT 1st DRP

7607:          LDD     L0250				; BPW
760A:          ASLD    						; BPW x 2
760B:          BCC     L7610				; BR IF NO OVERFLOW

760D:          LDD     #$FFFF				; USE MAX VALUE
7610:  L7610   ADDD    $0E,X				; SET UP CPU TIMER
7612:          STD     L0827				; SAVE CURRENT TIMER FOR BPW

7615:          BCLR    $20,X,#$04

7618:          LDD     $0E,X				; GET CPU FREE RUN 16 BIT TIMER
761A:          ADDD    #$02
761D:          CPD     L0827
7621:          BPL     L7626

7623:          LDD     L0827
7626:  L7626   STD     $1C,X

7628:          BRA     L7630
		;----------------------------------------

762A:  L762A   LDD     L024C				; SYNC BPW
762D:          JSR     L8548


			;
			; HOUSEKEEP DRP COUNTER
			;
7630:  L7630   LDAA    L02CE				; DRP COUNTER
7633:          INCA    						; INCR DRP COUNTER
7634:          BNE     L7638				; BR IF DRP CNT = NZ

7636:          LDAA    #240					; SET DRP CNT = 240
7638:  L7638   STAA    L02CE				; DRP COUNTER

			;
			; CK BATTERY VOLTAGE
			;
763B:          LDAB    L0055				; BATTERY VOLTS * 10
763D:          CMPB    L4D98				; 2.0 VDC BATTERY
7640:          BHI     L764D				; BR IF BATTERY > 2.0 VDC

7642:          CMPA    L4D97				; 8 DRP'S
7645:          BLS     L764D				; BR IF ... 

7647:          LDAA    L4D97				; 8 DRP'S
764A:          STAA    L02CE				; DRP COUNTER

764D:  L764D   JMP     L77C6

 

7650:  L7650   LDAA    L02C9			   	; CRANK XISITION AFR
7653:          BEQ     L7696				; BR IF = 0

7655:          LDAA    L0268				; DRP'S RUN PRIOR TO CRANK
7658:          INCA    						;  INCR CNT'R
7659:          BEQ     L765E				; BR IF Z

    		;--------------------------------------------------
    		; DELAY TABLE PRIOR AFR  TRANSITION IS DECAYED Vs COOL 
    		; 
    		;
    		; TBL = COUNTS
    		;--------------------------------------------------
765B:          STAA    L0268				; DRP'S RUN PRIOR TO CRANK 
765E:  L765E   LDX     #$4CBF				; DELAY TABLE PRIOR AFR
7661:          LDAA    L0006				; COOL VALUE

7663:          JSR     LF4C1				; 2d LK UP

7666:          TAB 


    		;--------------------------------------------------
    		; AFR XISSITION DELAY TIME MULT Vs DRP'S
    		;
    		; TBL = MULT * 256
    		;--------------------------------------------------
7667:          LDX     #$4CD0				; AFR XISSITION DELAY TIME MULT
766A:          LDAA    L02CE				; DRP COUNTER
766D:          ASLA    						; MULT x4
766E:          ASLA    						;
766F:          BCC     L7673				; BR F OVERFLOW

7671:          LDAA    #$FF					; MAX DELAY VALUE
7673:  L7673   JSR     LF4C1				; 2d LK UP
7676:          MUL     						; TBL VLA * L4CBF TBL VAL 

7677:          CMPA    L0268				; DRP'S RUN PRIOR TO CRANK
767A:          BCC     L7696				;

767C:          INC     L081E				; INCR CNT'R
767F:          LDAA    L081E				; COUNTS AFR TRANS CNT'R
7682:          CMPA    L4964				; 2 COUNTS AFR TRANS CNT'R
7685:          BCS     L7696				; BR IF CNT'R < THRSH

7687:          CLR     L081E				; COUNTS AFR TRANS CNT'R

768A:          LDAA    L02C9				; CRANK XISITION AFR
768D:          SUBA    L0267				; CRANK XISITION DECAY AFR
7690:          BCC     L7693				; BR IF NO UNDER FLOW

7692:          CLRA    						; CLRE STARTUP AFR
7693:  L7693   STAA    L02C9				; STARTUP AFR (SUB'R)



7696:  L7696   LDAA    L400C				; AFR MD BYTE 2	 1011 0111 <---***
7699:          BITA    #$08					; b3,  1 = ASDF
769B:          BEQ     L76D9				; BR IF NOT b3

769D:          BRSET   L0019,#$40,L76D9		; BR IF b6

76A1:          BRSET   L0051,#$01,L76BA		; BR IF b0

76A5:          BRCLR   L0053,#$40,L771C		; BR IF b6, SINGLE FIRE ALT EXIT IS DESIRED

76A9:          BCLR    L0053,#$40			; CLR b6, SINGLE FIRE ALT EXIT IS DESIRED
											;
76AC:          LDD     L0254				; 

76AF:          ASLD    						; x2
76B0:          BCC     L76B5				; BR IF NO OVERFLOW

76B2:          LDD     #$FFFF				; MAX PW
76B5:  L76B5   STD     L0254				; ASYNC BPW

76B8:          BRA     L7702
		;----------------------------------------

76BA:  L76BA   INC     L0829
76BD:          LDAA    L0829
76C0:          CMPA    #$03
76C2:          BCC     L76DC				; 

76C4:          LDD     L0254				; ASYNC BPW
76C7:          CPD     L492A				; ASYNC to SYNC IF BPW G.T. 500 usec
76CB:          BCS     L771C				; 

76CD:          LDAA    L0829
76D0:          CMPA    #$01
76D2:          BNE     L7712				; 

76D4:          BSET    L0053,#$40			; SET b6, SINGLE FIRE ALT EXIT IS DESIRED

76D7:          BRA     L7712
		;----------------------------------------

76D9:  L76D9   JMP     L7765
			;----------------------------------------------
			
			 														   

			;----------------------------------------------
			;
			;
			;
			;----------------------------------------------
76DC:  L76DC   LDX     #$3000				; INDEX CPU REG'S

76DF:          LDAA    #$01
76E1:          STAA    $23,X

76E3:          LDD     L0254				; ASYNC BPW
76E6:          CPD     L492A				; ASYNC to SYNC IF BPW G.T. 500 usec
76EA:          BCC     L76F8

76EC:          LDAA    L0829
76EF:          CMPA    #$0004
76F1:          BNE     L7765

76F3:          CLR     L0829
76F6:          BRA     L7765
		;----------------------------------------

76F8:  L76F8   LDAA    L0829
76FB:          CMPA    #$0004
76FD:          BNE     L7702

76FF:          BSET    L0053,#$40			; SET b6, SINGLE FIRE ALT EXIT IS DESIRED

7702:  L7702   LDD     L0254				; ASYNC BPW
7705:          ADDB    L0256              	; BPW BIAS (Msec)
7708:          ADCA    #$00
770A:          BPL     L770F

770C:          LDD     #$#32767				; USE MAX VALUE FOR BPW
770F:  L770F   STD     L0250				; BPW

7712:  L7712   BCLR    L0051,#$01

7715:          CLRA    
7716:          STAA    L082A
7719:          STAA    L0829


		;--------------------------------------------
		; AFR MD BYTE 1 0000 0100 
		;
		; b7 1 = DE-LATCH
		; b6 1 = MAT SENSOR
		; b5 1 = 180 DEG OFFSET 
		; b4 1 = ASDF CRANK
		;
		; b3 1 = ACCEL ENRICH LMT OPTION  
		; b2 1 = SYNC FUEL AT IDLE (TBI)
		; b1 1 = AIR MANAGE 
		; b0 1 = CPI/PFI MODE
		;--------------------------------------------
771C:  L771C   LDY     #$400B				; AFR MD BYTE 1,  0000 0100
7720:          BRSET   0,Y,#$20,L7728		; BR IF b5,  180 DEG OFFSET

7725:          BSET    L0051,#$80

7728:  L7728   LDX     #$3000				; INDEX CPU REG'S
772B:          BRCLR   $23,X,#$01,L774C

772F:          LDAA    #$0001
7731:          STAA    $23,X

7733:          CLR     L084E
7736:          BRSET   0,Y,#$20,L7754

773B:  L773B   JSR     L77F7

773E:          BRSET   L0051,#$80,L7765

7742:          BSET    L0051,#$80

7745:          CLRA    
7746:          CLRB    
7747:          STD     L081F

774A:          BRA     L7754
		;----------------------------------------

774C:  L774C   JSR     L785A


774F:          BRSET   0,Y,#$20,L773B

7754:  L7754   JSR     L77C7

7757:          BRSET   L0051,#$80,L7765

775B:          BSET    L0051,#$80

775E:          CLRA    
775F:          CLRB    
7760:          STD     L081F

7763:          BRA     L773B
		;----------------------------------------

7765:  L7765   LDD     L3FFA
7768:          ORAA    L0073

776A:          BCLR    L0073,#$40

776D:          BITA    #$40
776F:          BEQ     L77C6

7771:          LDAB    L0067
7773:          CMPB    L4516				; 6375 RPM
7776:          BCS     L778E

7778:  L7778   LDAB    L01D9				; %TPS
777B:          CMPB    L48DA				; 2.3% TPS MAX IDLE FUEL TABLE
777E:          BHI     L778E				; BR IF TPS GT THRESH

7780:          LDD     L0068				; FILTER COEF IN B REG.
7782:          LDX     #$006A				; GET OLD FILTERED RPM
7785:          LDY     #$4518				; FILT RPM COEF LIMIT
7789:          JSR     LF479				; FILTER

778C:          BRA     L7790
		;----------------------------------------

778E:  L778E   LDD     L0068				; RPM/?
7790:  L7790   STD     L006A				; SAVE FILTERED RPM 

7792:          LDAA    L400B				; AFR MD BYTE 1,  0000 0100
7795:          BITA    #$01					; b0, 1 = CPI/PFI MODEE
7797:          BEQ     L77C6				; BR IF NOT b0	(EXIT VIA RTI)


7799:          LDAA    L400C				; AFR MD BYTE 2	 1011 0111 ,---***
779C:          BITA    #$08					; b3 1 = ASDF
779E:          BEQ     L77A4				; BR IF NOT b3

77A0:          BRCLR   L0019,#$40,L77C6		; BR IF NOT b6

77A4:  L77A4   BRCLR   L0051,#$01,L77B8		; BR IF NOT b0

77A8:          BRCLR   L003F,#$10,L77C3		; BR IF NOT b4

77AC:          LDD     L0254				; ASYNC BPW
77AF:          CPD     L492A				; ASYNC to SYNC IF BPW G.T. 500 usec
77B3:          BLS     L77B8

77B5:          BCLR    L0051,#$01			; CLR b0
77B8:  L77B8   BCLR    L003F,#$10			; CLR b4

77BB:          JSR     L77C7
77BE:          JSR     L77F7

77C1:          BRA     L77C6
		;----------------------------------------


77C3:  L77C3   BSET    L003F,#$10			; SET b4

77C6:  L77C6   RTI     
		;----------------------------------------

		;*********************************************
		;  HOUSEKEEP  TIC4/TOC5
		;  TYPE $31
		;*********************************************
77C7:  L77C7   LDX     #$3000				; INDEX CPU REG'S

77CA:          LDD     L081F				;
77CD:          CPD     #6					;
77D1:          BCC     L77D6				; BR IF 

77D3:          LDD     #$06					; 
77D6:  L77D6   ADDD    $0E,X				; 16 BIT FREE RUN CNT'R
77D8:          STD     L0821				; 
											;
77DB:          LDAA    #$08					;  b4,  TIC4/TOC5, FLAG
77DD:          STAA    $23,X				; CLR FLAG, TFLG1 
											;
77DF:          BSET    $22,X,#$08			; SET b3, TMSK1 TIC4/TOC5 INT ENABLE
77E2:          BRCLR   0,X,#$08,L77EE		;

77E6:          LDD     L0821				;
77E9:          CPD     $1E,X				; TIC4/TOC5	
77EC:          BPL     L77F6				;

77EE:  L77EE   BSET    $20,X,#$03			;
											;
77F1:          LDD     L0821				;
77F4:          STD     $1E,X				; TIC4/TOC5	VALUE

77F6:  L77F6   RTS     
		***************************************************


		***************************************************
		*  HOUSEKEEP TOC 4 
		*  TYPE $31
		***************************************************
77F7:  L77F7   LDX     #$3000				; INDEX CPU REG'S
											;
77FA:          LDD     L081F				;
77FD:          CPD     #$06					;
7801:          BCC     L7806				; BR IF 

7803:          LDD     #$06					; 
7806:  L7806   ADDD    $0E,X				; 16 BIT FREE RUN CNT'R 
7808:          STD     L0823				; 
											;
		;
		; SET UP TOC 4
		;
780B:          LDAA    #$10					; b4,  TOC 4, FLAG  
780D:          STAA    $23,X				; CLR FLAG, TFLG1
											; 
780F:          BSET    $22,X,#$10			; SET b4, TMSK1 TOC 4 INT ENABLE
											;
7812:          BRCLR   0,X,#$10,L781E		; BR IF NOT b4

7816:          LDD     L0823				;
7819:          CPD     $1C,X				; TOC 4
781C:          BPL     L7826				; BR IF 

			;
			; SET OC4 OUT LINE = 1
			;
781E:  L781E   BSET    $20,X,#$0C			; SET b2 & b3, TCTL1 OL4 & OM4
											;
7821:          LDD     L0823				; 
7824:          STD     $1C,X				; TOC 4 VALUE

7826:  L7826   RTS     
		***************************************************


		***************************************************
		*  CRANK FUEL MULT vs DRP'S 
		*
		* TYPE $31 PCM
		***************************************************
7827:  L7827   PSHB    
7828:          PSHA    
7829:          LDAB    L02CE				; DRP COUNTER
782C:          CMPB    #23					; 23 DRP'S ?
782E:          BLS     L7837				; BR IF DRP COUNT LT 23 

7830:          ANDB    #$07					; 0000 0111

    		;-----------------------------------------
			; CRANK FUEL MULT vs DRP'S 
			; (CYCLING TBL FOR DRP'S G.T. 24)
			;
			; TBL = MULT * 128
    		;-----------------------------------------
7832:          LDX     #$4E26				; CRANK FUEL MULT TBL

7835:          BRA     L784B
		;----------------------------------------

    		;-----------------------------------------
			; CRANK FUEL MULT vs DRP'S 
			; (HOT restart MODE)
			; 
			; TBL = MULT * 128
    		;-----------------------------------------
7837:  L7837   LDX     #$4E0E				; CRANK FUEL MULT TBL,
											;
783A:          BRSET   L0004,#$10,L784B		; BR IF b4, 1 = HOT restart

    		;-----------------------------------------
    		; CRANK FUEL MULT vs DRP'S 
    		; (For restart mode, NOT Hot restart)
			;
    		; TBL = MULT * 128
    		;-----------------------------------------
783E:          LDX     #$4DF6				; CRANK FUEL MULT TBL
7841:          LDAA    L0006				; COOL VALUE
7843:          CMPA    L4D99				; 46c COOL, MIN TO USE L4D4E, else use L4DCD
7846:          BCC     L784B				; BR IF COOL GT THRESH

    		;-----------------------------------------
    		; CRANK FUEL MULT vs DRP'S
    		;   (IF TEMP L.T. L4D88 & DPR'S L.T. 24)
			;
    		; Indexed lk up
    		;-----------------------------------------
7848:          LDX     #$4DDE				; CRANK FUEL MULT TBL (Cold Start Mode
											; 
784B:  L784B   ABX     						; ADJ INDEX FOR DRP
784C:          LDAA    0,X					; GET TBL VAL
784E:          TSX     						; 
784F:          JSR     LF550				; MUL 8X16 Subroutine
											;
7852:          PULX    						;
											;
7853:          ASLD    						; x2 MULT
7854:          BCC     L7859				; BR IF NOT OVERFLOW

7856:          LDD     #$FFFF				; USE MAX VALUE
											;
7859:  L7859   RTS     						;
 			;------------------------------------------
			***********************************************



 			;------------------------------------------
			; ERR 41, TX, (CAM) PULSE SENSOR FAIL
			;
			;
 			;------------------------------------------
785A:  L785A   LDAA    L5B03				; 1011 1100, ERR WD 4
785D:          BITA    #$40					; b6, 1 = ERR 41,
785F:          BEQ     L7874				; BR IF NOT b6

7861:          LDAA    L084E				; ERR 41 CNT'R  
7864:          CMPA    #255					; CK FO MAX
7866:          BEQ     L786C				;

7868:          INCA    						; INCR CNT'R
7869:          STAA    L084E				; ERR 41 CNT'R
786C:  L786C   CMPA    L4E6F				; DRP'S W/O CAM PULSE
786F:          BLS     L7874				;

7871:          BSET    L0019,#$40			; SET b6

7874:  L7874   RTS     
			;-----------------------------------------



 			;-----------------------------------------
			; TOC 5 INTERUPT VECTOR HANDLER
			;
			;
			;-----------------------------------------
7875:          LDX     #$3000				; INDEX CPU REG'S

7878:          LDAA    #$08					; b2 TIC4/TOC5 INT FLG
787A:          STAA    $23,X				; TFLAG

787C:          BRCLR   0,X,#$08,L78C5		; BR IF NOT b3, (NO INTERUPT)

7880:          BCLR    $22,X,#$08			; CLR b3, TMASK1, TIC4/TOC5 INHIB
7883:          BCLR    $20,X,#$01			; CLR b0, TCTL1, OL5 DISCON FM PIN 


7886:          BRCLR   L0046,#$01,L78A7		; BR IF NOT b0, SYNC ACELL ENRICH 

788A:          LDD     L0250 				; BPW
788D:          ADDD    L023A				;
7890:          BCS     L7895				; BR IF 

7892:          ASLD    						;
7893:          BCC     L7898				; BR IF 

7895:  L7895   LDD     #$FFFF				;
7898:  L7898   ADDD    $1E,X				; TIC4/TOC5    
789A:          STD     L0825				; TIC4/TOC5 RESULT
											;
789D:          CLRA    						;
789E:          CLRB    						;
789F:          STD     L023A				;
											;
78A2:          BCLR    L0046,#$01			; CLR b0, SYNC ACELL ENRICH 

78A5:          BRA     L78B5
		;----------------------------------------

		***************************************************
		*  HOUSEKEEP  TIC4/TOC5
		*  TYPE $31
		***************************************************
78A7:  L78A7   LDD     L0250				; BPW
78AA:          ASLD    
78AB:          BCC     L78B0				; BR IF 

78AD:          LDD     #$FFFF
78B0:  L78B0   ADDD    $1E,X 				; TIC4/TOC5
78B2:          STD     L0825				; TIC4/TOC5 RESULT

78B5:  L78B5   LDD     $0E,X				; 16 BIT FREE RUN CNT'R
78B7:          ADDD    #$02
78BA:          CPD     L0825				; TIC4/TOC5 RESULT
78BE:          BPL     L78D6				; BR IF 

78C0:          LDD     L0825				; TIC4/TOC5 RESULT

78C3:          BRA     L78D6
		;----------------------------------------

78C5:  L78C5   BSET    $20,X,#$01			; SET b0

78C8:          LDD     $0E,X				; 16 BIT FREE RUN CNT'R
78CA:          ADDD    #$02
78CD:          CPD     L0821
78D1:          BPL     L78D6

78D3:          LDD     L0821
78D6:  L78D6   STD     $1E,X 				; TIC4/TOC5	VALUE

78D8:          RTI     
		***************************************************



		***************************************************
		*  HOUSEKEEP  TOC4
		*  TYPE $31
		***************************************************
78D9:          LDX     #$3000				; INDEX CPU REG'S

78DC:          LDAA    #$10					;
78DE:          STAA    $23,X				; TFLG1, 
78E0:          BRCLR   0,X,#$10,L7929		; BR IF NOT b4, TOC3

78E4:          BCLR    $22,X,#$10			; SET b4, TOC4 INT ENABLE
78E7:          BCLR    $20,X,#$04			; SET b2, TCTL1, OL4 TGGLE OC LINE
											;
78EA:          BRCLR   L0046,#$01,L790B		; BR IF NOT b0,  SYNC ACELL ENRICH

78EE:          LDD     L0250				; BPW
78F1:          ADDD    L023A				;
78F4:          BCS     L78F9				;

78F6:          ASLD    						;
78F7:          BCC     L78FC				;

78F9:  L78F9   LDD     #$FFFF				;
											;
78FC:  L78FC   ADDD    $1C,X				; TOC4
78FE:          STD     L0827				;
7901:          CLRA    						;
7902:          CLRB    						;
7903:          STD     L023A				;
											;
7906:          BCLR    L0046,#$01			; CLR b0,  SYNC ACELL ENRICH
											;
7909:          BRA     L7919				;
		;----------------------------------------

790B:  L790B   LDD     L0250				; BPW
790E:          ASLD    						;
790F:          BCC     L7914				;

7911:          LDD     #$FFFF				;
7914:  L7914   ADDD    $1C,X				; TOC4
7916:          STD     L0827				;
											;
7919:  L7919   LDD     $0E,X				; TCNT, 16 BIT TIMER
791B:          ADDD    #$02					;
791E:          CPD     L0827				;
7922:          BPL     L793A				;

7924:          LDD     L0827				;
7927:          BRA     L793A				;
		;----------------------------------------

7929:  L7929   BSET    $20,X,#$04			; TCTL1, OL4 TOGGLE TOC4 OUT LINE
792C:          LDD     $0E,X				; TCNT, 16 BIT TIMER
792E:          ADDD    #$02					;
7931:          CPD     L0823				;
7935:          BPL     L793A				;

7937:          LDD     L0823				;
793A:  L793A   STD     $1C,X				; TOC4

793C:          RTI     
 			;-----------------------------------------


			;-----------------------------------------
			;
			;
			;
			;-----------------------------------------
793D:          LDD     L301A				; TOC3 
7940:          ADDD    #819
7943:          STD     L301A				; TOC3

7946:          LDAA    #$20
7948:          STAA    L3023

794B:          BSET    L0000,#$01			; SET b0
											;
794E:          BRCLR   L0044,#$01,L7958		; BR IF NOT b0, FACTORY TEST ENTERED


7952:          INC     L0002				; MAJOR LOOP COUNTER

7955:          JMP     LFA5B


7958:  L7958   CLI     
7959:          TSX     
795A:          PSHX    
795B:          PULX    
795C:          BRSET   L004F,#$04,L7967		; BR IF b2, LOOP OVERRAN 6,25 MS PERIOD

7960:          CPX     #$03F7
7963:          BLS     L796C

7965:          BRA     L7971
		;----------------------------------------

7967:  L7967   CPX     #$03EE
796A:          BHI     L7971				; BR IF 

796C:  L796C   CPX     #$03B0
796F:          BCC     L797A

7971:  L7971   BSET    L003A,#$08
7974:          BCLR    L004F,#$04			; CLR b2, LOOP OVERRAN 6,25 MS PERIOD

7977:          LDS     #$03F6
797A:  L797A   JSR     L7B6D
797D:          BRCLR   L004F,#$04,L7989		; BR IF NOT b2, LOOP OVERRAN 6,25 MS PERIOD

7981:          LDAA    L0002				; MAJOR LOOP COUNTER
7983:          STAA    L0003
7985:          BSET    L003A,#$20

7988:          RTI     
 		;---------------------------------------------


		;---------------------------------------------
		;
		;
		;
		;---------------------------------------------
7989:  L7989   BSET    L004F,#$04			; SET b2, LOOP OVERRAN 6,25 MS PERIOD

798C:          BRCLR   L003B,#$10,L79A4				;

7990:          LDAB    L038F
7993:          BITB    #$04
7995:          BEQ     L79A4				;

7997:          BCLR    L0072,#$80
799A:          LDAB    L0390
799D:          BITB    #$0004
799F:          BEQ     L79A4				;

79A1:          BSET    L0072,#$80

79A4:  L79A4   LDAA    L0002				; MAJOR LOOP COUNTER
79A6:          INCA    						; INCR LOOP COUNT
79A7:          CMPA    #$A0					; 
79A9:          BNE     L79C5				;

79AB:          LDAB    L0043
79AD:          EORB    #$20
79AF:          STAB    L0043

79B1:          BRCLR   L004F,#$80,L79C4		; BR IF NOT b7,	ENGINE RUNNING

79B5:          LDX     L00FD				; RUN TIMER
79B7:          INX     						; INCR RUN TIMER
79B8:          BEQ     L79BC				; BR IF TIMER = Z

79BA:          STX     L00FD				; RUN TIMER
79BC:  L79BC   CPX     L495D				; 10 SEC'S, HOT restart TIME AFTER RUN
79BF:          BCS     L79C4				; BR IF TIMER LT THRESH


			;----------------------------
			; MODE 1, WD #3, FLAGWORD,
			;		  b4 1 = HOT restart
			;----------------------------
79C1:          BCLR    L0004,#$10			; CLR b4, HOT restart

79C4:  L79C4   CLRA    
79C5:  L79C5   STAA    L0002				; MAJOR LOOP COUNTER
79C7:          SEI     
79C8:          LDAA    L003B
79CA:          ANDA    #$FB
79CC:          BRSET   L0051,#$08,L79D4		;

79D0:          BITA    #$18
79D2:          BEQ     L79D6				;

79D4:  L79D4   ORAA    #$0004
79D6:  L79D6   STAA    L003B
79D8:          CLI     
79D9:          BRCLR   L001A,#$20,L79F2
79DD:          BRCLR   L0002,#$01,L7A44	  	; MAJOR LOOP COUNTER
											;
79E1:          BSET    L0043,#$80
79E4:          JSR     LAC51
79E7:          LDD     #$AA55
79EA:          STAA    L303A
79ED:          STAB    L303A

79F0:          BRA     L7A44
		;----------------------------------------

79F2:  L79F2   JSR     L7BA7
79F5:          BRSET   L0002,#$01,L7A19	 	; MAJOR LOOP COUNTER
											;
79F9:          JSR     L9167
79FC:          JSR     LA466
79FF:          JSR     LD14E
7A02:          JSR     LD1F6
7A05:          JSR     LF5E8				; REMOTE BROADCAST ROUTINE
7A08:          BRCLR   L0002,#$02,L7A11		; MAJOR LOOP COUNTER
											;
7A0C:          JSR     LB56B

7A0F:          BRA     L7A44
		;----------------------------------------

7A11:  L7A11   JSR     LD03E
7A14:          JSR     LAE85

7A17:          BRA     L7A44
		;----------------------------------------

7A19:  L7A19   JSR     L7D4B
7A1C:          JSR     LCDF7
7A1F:          BRCLR   L003B,#$10,L7A32
7A23:          LDAA    L0391
7A26:          BITA    #$0080
7A28:          BEQ     L7A32
7A2A:          BSET    L0044,#$04			; SET b2, SKIP ERR 43 DUE TO ALDL
7A2D:          BSET    L0043,#$80

7A30:          BRA     L7A35
		;----------------------------------------

			;**********************************************
			; MAJOR LOOP ROUTINE
			;
			;
			;
			;**********************************************
7A32:  L7A32   JSR     LF3E4
7A35:  L7A35   BRCLR   L0002,#$02,L7A41	  	; MAJOR LOOP COUNTER
											;
7A39:          JSR     L93D0				;
7A3C:          JSR     LC4E5				;

7A3F:          BRA     L7A44				;
		;----------------------------------------

7A41:  L7A41   JSR     LB32D
7A44:  L7A44   LDAB    L0002				; MAJOR LOOP COUNTER
7A46:          ANDB    #$0F					; MASK
											;
7A48:          LDX     #$7A85				; INDEX ADDRESS TABLE
7A4B:          ASLB    						; ADJ FOR 2 BYTES
7A4C:          ABX     						; ADJ INDEX FOR CURRENT MJR LOOP
7A4D:          LDX     0,X					; GET MAJOR LOOP ADDRESS FM TBL
7A4F:          JSR     0,X					; CALL MAJOR LOOP SUB'S


7A51:          SEI     						; SECURE INTRERUPT

7A52:          BCLR    L004F,#$04			; CLR b2, LOOP OVERRAN 6,25 MS PERIOD

7A55:          BRCLR   L0086,#$40,L7A79		; BR IF NOT b6

7A59:          LDAB    L0002				; MAJOR LOOP COUNTER
7A5B:          ANDB    #$0F
7A5D:          ASLB    
7A5E:          LDX     #$02D3				; 
7A61:          ABX     						;
7A62:          LDD     L300E				; 16 BIT FREE RUN CNT'R
7A65:          SUBD    L301A				; TOC3 
7A68:          ADDD    #0819				; ADD 819 TO TOC 3
7A6B:          BRCLR   L003A,#$20,L7A72		; BR IF NOT B5,
 
7A6F:          ADDD    #0819				;
7A72:  L7A72   CPD     0,X					;
7A75:          BLS     L7A79				; 

7A77:          STD     0,X					;

7A79:  L7A79   BRCLR   L003A,#$20,L7A84		; BR IF NOT b5,
 
7A7D:          BCLR    L003A,#$20			; CLR b5
7A80:          CLI     						; CLR & RESTORE INTERUPTS

7A81:          JMP     L7989
 
7A84:  L7A84   RTI     
 			;-----------------------------------------

   			;------------------------------------------
   			;  MAJOR LOOP SUBROUTINE LK UP TBL
   			;
   			;------------------------------------------
        ORG  $7A85  ;      
                    ;----------------------------------
L7A85   FCB $7AA6   ; 0
L7A87   FCB $7AAD   ; 1
L7A89   FCB $7AB7   ; 2
L7A8B   FCB $7ABD   ; 3
L7A8D   FCB $7AC7   ; 4
L7A8F   FCB $7B03   ; 5
L7A91   FCB $7B14   ; 6
L7A93   FCB $7B1B   ; 7
L7A95   FCB $7B2B   ; 8
L7A97   FCB $7B2F   ; 9
L7A99   FCB $7B39   ; A
L7A9B   FCB $7B3D   ; B
L7A9D   FCB $7B44   ; C
L7A9F   FCB $7B48   ; D
L7AA1   FCB $7B52   ; E
L7AA3   FCB $7B5A   ; F
    		;------------------------------------------

7AA5:          RTS     
 			;------------------------------------------

   			;------------------------------------------
   			;  MAJOR LOOP 0
   			;
			;------------------------------------------
7AA6:          JSR     LC56F			   	; A/D READ BATTERY VOLTAGE
7AA9:          JSR     LCF15
7AAC:          RTS     
 			;------------------------------------------

   			;------------------------------------------
   			;  MAJOR LOOP 1
   			;
			;------------------------------------------
7AAD:          JSR     LC583
7AB0:          JSR     LC668
7AB3:          JSR     LADAA

7AB6:          RTS     
 			;------------------------------------------

   			;------------------------------------------
   			;  MAJOR LOOP 2
   			;
			;------------------------------------------
7AB7:          SEI     
7AB8:          JSR     LF20D
7ABB:          CLI  
   
7ABC:          RTS     
 			;------------------------------------------

   			;------------------------------------------
   			;  MAJOR LOOP 3
   			;
			;------------------------------------------
7ABD:  L7ABD   JSR     LF5CF				; HEADS UP
7AC0:          JSR     LD4EB
7AC3:          JSR     LC514

7AC6:          RTS     
 			;------------------------------------------

   			;------------------------------------------
   			;  MAJOR LOOP 4
   			;
			;------------------------------------------
7AC7:          JSR     LC8B1				;
											;
7ACA:          BRCLR   L0002,#$10,L7AE2		; MAJOR LOOP COUNTER

7ACE:          JSR     LB9EE
7AD1:          JSR     LB99F
7AD4:          JSR     LEAB1
7AD7:          JSR     LEAE4
7ADA:          JSR     LC8D6
7ADD:          JSR     LC8FD

7AE0:          BRA     L7AF1
		;----------------------------------------

7AE2:  L7AE2   JSR     LE75F				;
7AE5:   	   JSR     LE793				; ERR 15 PARAMS LOW COOLANT TEMP
7AE8:          JSR     LC96A				; DO COOL SUBROUTINE
7AEB:          JSR     LC9C0				;
7AEE:          JSR     LC9F7				;


7AF1:  L7AF1   BCLR    L006F,#$24

			;
			; ERR WD 
			;
7AF4:          BRCLR   L0016,#$01,L7AFB		; BR IF NOT b0, ERR 21, HI TPS 

7AF8:          BSET    L006F,#$04			; SET b2


7AFB:  L7AFB   BRCLR   L0017,#$80,L7B02		; BR IF NOT b7, 

7AFF:          BSET    L006F,#$20			; SET b5

7B02:  L7B02   RTS     
 			;------------------------------------------

   			;------------------------------------------
   			;  MAJOR LOOP 5
			;
   			;	CK IF 4L60 XMISH
			;------------------------------------------
7B03:          JSR     LD3B0
7B06:          JSR     LD472

7B09:          LDX     #$400F				; AFR MD BYTE 5, 0001 0000, (DIG I/O)
7B0C:          BRSET   0,X,#$40,L7B13		; BR IF b6,  1 = TCC (Non Elect xmish)

7B10:          JSR     LC6BB
7B13:  L7B13   RTS     
 			;------------------------------------------

   			;------------------------------------------
   			;  MAJOR LOOP 6
   			;
			;------------------------------------------
7B14:          JSR     LCB15
       L7B15
7B17:          JSR     LCE10

7B1A:          RTS     

 			;------------------------------------------

   			;------------------------------------------
   			;  MAJOR LOOP 7
   			;
			;------------------------------------------
7B1B:          JSR     LC514
7B1E:          JSR     LF5DC  	; CK IF HEADS UP IS CONNECTED
7B21:          JSR     L9E99
7B24:          JSR     LCA6B
7B27:          JSR     LACA7

7B2A:          RTS     
 			;------------------------------------------


   			;------------------------------------------
   			;  MAJOR LOOP 8
   			;
			;------------------------------------------
7B2B:          JSR     LCEBB

7B2E:          RTS     
 			;------------------------------------------

   			;------------------------------------------
   			;  MAJOR LOOP 9
   			;
			;------------------------------------------
7B2F:          JSR     LCF16
7B32:          JSR     LA2B0
7B35:          JSR     LD4DA

7B38:          RTS     
 			;------------------------------------------

   			;------------------------------------------
   			;  MAJOR LOOP A
   			;
			;------------------------------------------
7B39:          JSR     LD2B2

7B3C:          RTS     
 			;------------------------------------------

   			;------------------------------------------
   			;  MAJOR LOOP B
   			;
			;------------------------------------------
7B3D:          JSR     LD4EB
7B40:          JSR     LC514

7B43:          RTS     
 			;------------------------------------------

   			;------------------------------------------
   			;  MAJOR LOOP C
   			;
			;------------------------------------------
7B44:          JSR     LCC35

7B47:          RTS     
 			;------------------------------------------

   			;------------------------------------------
   			;  MAJOR LOOP D
   			;
			;------------------------------------------
7B48:          JSR     LCCC1				; FILTER ... o2 VALUES
											; A.I.R. MANAGE
											;
7B4B:          JSR     LDBFB				; GET MAT VALUE & ERR CK
											;
7B4E:          JSR     LDC89				;
											;

7B51:          RTS     
 			;------------------------------------------

   			;------------------------------------------
   			;  MAJOR LOOP E
   			;
			;------------------------------------------
7B52:          BRCLR   L0051,#$04,L7B59		; BR IF NOT b2

			;-------------------------------
			; MODE 1, WD 3, 
			;		   
			;-------------------------------
7B56:          BSET  	L0004,#$04			; SET b2, RAM REFRESH ERR OCCOURED

7B59:  L7B59   RTS     
 			;------------------------------------------


   			;------------------------------------------
   			;  MAJOR LOOP F
   			;
			;------------------------------------------
7B5A:          JSR     LC514
7B5D:          JSR     LC4F5
7B60:          JSR     LE62D
7B63:          JSR     LE6E5
7B66:          JSR     LE286

7B69:          BSET    L0051,#$04

7B6C:          RTS     
 			;-----------------------------------------



   			;------------------------------------------
   			; 
   			;
			;------------------------------------------
7B6D:  L7B6D   JSR     L91A3
7B70:          SEI     
7B71:          LDAA    #$07
7B73:          STAA    L3030

7B76:          LDX     #$3000				; INDEX CPU REG'S
7B79:  L7B79   BRCLR   $0030,X,#$80,L7B79

7B7D:          CLRA    
7B7E:          LDAB    L3031
7B81:          ADDB    L3032
7B84:          ADCA    #$00
7B86:          ADDB    L3033
7B89:          ADCA    #$00
7B8B:          ADDB    L3034
7B8E:          ADCA    #$00
7B90:          LSRD    
7B91:          LSRD    
7B92:          ADCB    #$00
7B94:          STAB    L014E  				; ACTUAL FM CURRENT FM SHUNT

7B97:          JSR     LF245
7B9A:          CLI     
7B9B:          JSR     L7C13
7B9E:          LDAB    L014C  				; FORCE MOTOR D.C.

7BA1:          LDAA    #$06
7BA3:          STD     L3068

7BA6:          RTS     
 		;------------------------------------------


		;------------------------------------------
		;
		;
		;
		;------------------------------------------
7BA7:  L7BA7   JSR     LF3EE

7BAA:          LDAA    L082E				;  MAP A/D

7BAD:          LDAB    L006F
7BAF:          BITB    #$48					; 0100 1000
7BB1:          BEQ     L7BDC				; BR IF NOT b3 or b6

7BB3:          BRCLR   L004F,#$10,L7BD9		; BR IF NOT b4, RUN FUEL

7BB7:          LDAA    L4E69				; MAP DEFAULT COEF
7BBA:          LDAB    L01D9				; %TPS
7BBD:          MUL     
7BBE:          ASLD    
7BBF:          BCS     L7BD9				;

7BC1:          ASLD    
7BC2:          BCS     L7BD9				;

7BC4:          PSHA    
7BC5:          LDAA    L0062 				; ENGINE RPM/25
7BC7:          LSRA    
		;------------------------
		; MAP DEFAULT BIAS vs RPM
		;------------------------
7BC8:          LDX     #$4E6A				; MAP DEFAULT BIAS TABLE
7BCB:          LDAB    #16					; ADDER ??
7BCD:          JSR     LF49A				;
											;
7BD0:          PULB    						;
7BD1:          ABA     						; ADD 16 TO TABLE VALUE
7BD2:          BCS     L7BD9				; BR IF OVERFLOW

7BD4:          CMPA    L4E68				; 90.8 Kpa DEFAULT MAP IF NOT RUNNING
											; ERR 33/34
7BD7:          BLS     L7BDC				;

7BD9:  L7BD9   LDAA    L4E68				; 90.8 Kpa DEFAULT MAP IF NOT RUNNING

7BDC:  L7BDC   LDAB    L4138				;  94% COEF TRANSIENT MAP

7BDF:          BRSET   L0047,#$01,L7BE6		; BR IF b0, TRANSIENT MAP FILTER


			;
			; FILTER MAP
			;
7BE3:          LDAB    L4137				; 25% COEF NORMAL MAP 
7BE6:  L7BE6   LDX     L01C3				; GET OLD TRANS MAP
7BE9:          JSR     LF459				; LAG FILT

7BEC:          STD     L01C3				; SAVE FILTERED MAP

7BEF:          ASLB    
7BF0:          ADCA    #$00
7BF2:          STAA    L01C6				; CURRENT MAP VAL

7BF5:          SEI     						; TURN OFF INTERUPTS     

7BF6:          LDD     L3FFA
7BF9:          STD     L0073

7BFB:          CLI     
7BFC:          BITA    #$04
7BFE:          BEQ     L7C0F

7C00:          LDD     L3FC4
7C03:          CPD     L080D
7C07:          BEQ     L7C0F

7C09:          INC     L080C
7C0C:          STD     L080D
7C0F:  L7C0F   JSR     L7D21

7C12:          RTS     
 			;------------------------------------------


7C13:  L7C13   BRSET   L004C,#$20,L7C25		; BR IF b5, 

7C17:          CLRA    
7C18:          CLRB    
7C19:          STD     L0150
7C1C:          STAA    L014C  				; FORCE MOTOR D.C
7C1F:          STAA    L014F
7C22:          JMP     L7CA8
 

7C25:  L7C25   LDAA    L014F
7C28:          LDAB    L0154
7C2B:          MUL     
7C2C:          TST     L014F
7C2F:          BPL     L7C34
7C31:          SUBA    L0154
7C34:  L7C34   PSHB    
7C35:          PSHA    
7C36:          LDAA    L014D				; REF CURRENT FORCE MTR CKT
7C39:          CMPA    #57
7C3B:          BLS     L7C3F

7C3D:          LDAA    #57
7C3F:  L7C3F   SUBA    L014E
7C42:          RORA    
7C43:          ROLA    
7C44:          BVC     L7C4A

7C46:          LDAA    #127
7C48:          ADCA    #$0000
7C4A:  L7C4A   CMPA    #$0001
7C4C:          BEQ     L7C52
7C4E:          CMPA    #$00FF
7C50:          BNE     L7C53
7C52:  L7C52   CLRA    
7C53:  L7C53   STAA    L014F
7C56:          LDAB    L0153
7C59:          MUL     
7C5A:          TST     L014F
7C5D:          BPL     L7C62
7C5F:          SUBA    L0153
7C62:  L7C62   TSX     
7C63:          SUBD    0,X
7C65:          BVC     L7C6E
7C67:          LDD     #$8000
7C6A:          SBCB    #$0000
7C6C:          SBCA    #$0000
7C6E:  L7C6E   ASRA    
7C6F:          RORB    
7C70:          ASRA    
7C71:          RORB    
7C72:          ADCB    #$0000
7C74:          ADCA    #$0000
7C76:          PULX    
7C77:          TSTA    
7C78:          BMI     L7C88
7C7A:          ADDD    L0150
       L7C7B
7C7D:          CPD     #$0E00
7C81:          BLS     L7C96
7C83:          LDD     #$0E00
7C86:          BRA     L7C96
		;----------------------------------------

7C88:  L7C88   ADDD    L0150
7C8B:          BCC     L7C93
7C8D:          CPD     #$0000
7C91:          BCC     L7C96
7C93:  L7C93   LDD     #$0000
7C96:  L7C96   STD     L0150
7C99:          LDX     #$0E00
7C9C:          FDIV    
7C9D:          XGDX    
7C9E:          ADDD    #$0080
7CA1:          BCC     L7CA5
7CA3:          LDAA    #$00FF
7CA5:  L7CA5   STAA    L014C  				; FORCE MOTOR D.C
7CA8:  L7CA8   BRSET   L008E,#$80,L7CE3
7CAC:          BRSET   L0086,#$01,L7CE3
7CB0:          LDD     L0150
7CB3:          CPD     #$0E00
7CB7:          BNE     L7CE3
7CB9:          LDAA    L00FC
7CBB:          INCA    
7CBC:          CMPA    L6E54
7CBF:          BLS     L7CE1
7CC1:          CLR     L00FC
7CC4:          LDAA    L6E56
7CC7:          SUBA    L6E55
7CCA:          LDAB    L00B5
7CCC:          MUL     
7CCD:          ADDD    #$80
7CD0:          ADDA    L6E55
7CD3:          CMPA    L00A7   				; BAT VOLTS, VDC/10
7CD5:          BLS     L7CDC				;

7CD7:          BSET    L0086,#$01
7CDA:          BRA     L7CE3
		;----------------------------------------

7CDC:  L7CDC   BSET    L008E,#$80
7CDF:          BRA     L7CE3
		;----------------------------------------

7CE1:  L7CE1   STAA    L00FC
7CE3:  L7CE3   BRSET   L008E,#$80,L7CF7
7CE7:          BRSET   L0086,#$01,L7CF7
7CEB:          LDD     L0150
7CEE:          CPD     #$0E00
7CF2:          BCC     L7CF7
7CF4:          CLR     L00FC
7CF7:  L7CF7   BRCLR   L0086,#$01,L7D20
7CFB:          LDAA    L6E58
7CFE:          SUBA    L6E57
7D01:          LDAB    L00B5
7D03:          MUL     
7D04:          ADDD    #$0080
7D07:          ADDA    L6E57
7D0A:          CMPA    L00A7   				; BAT VOLTS, VDC/10
7D0C:          BCC     L7D20
7D0E:          LDAA    L00FC
7D10:          INCA    
7D11:          CMPA    L6E54
7D14:          BLS     L7D1E
7D16:          CLR     L00FC
7D19:          BCLR    L0086,#$01
7D1C:          BRA     L7D20
		;----------------------------------------

7D1E:  L7D1E   STAA    L00FC

7D20:  L7D20   RTS     
			;------------------------------------
			; I/O PORT C
			;
			;------------------------------------
7D21:  L7D21   BRCLR   L004D,#$02,L7D2B		; BR IF NOT b1,  BRAKE SW ON 

7D25:          BRSET   L009C,#$01,L7D34		; BR IF b0, 

7D29:          BRA     L7D2F
		;----------------------------------------

7D2B:  L7D2B   BRCLR   L009C,#$01,L7D34		; BR IF NOT b0,
7D2F:  L7D2F   CLR     L00FB

7D32:          BRA     L7D4A
		;----------------------------------------

7D34:  L7D34   LDAB    L00FB
7D36:          CMPB    L5D06			    ; 25 msec, BRAKE SWITCH FILTER TIME
7D39:          BCC     L7D40
7D3B:          INCB    
7D3C:          STAB    L00FB

7D3E:          BRA     L7D4A
		;----------------------------------------

7D40:  L7D40   BCLR    L009C,#$01			; CLR b0
7D43:          BRSET   L004D,#$02,L7D4A		; BR IF b1,  BRAKE SW ON

7D47:          BSET    L009C,#$01			; SET b0

7D4A:  L7D4A   RTS     
		 ;------------------------------------------


7D4B:  L7D4B   LDX     L027E
7D4E:          BRCLR   L0044,#$10,L7D90		; BR IF NOT b4, IGNITION OFF 

7D52:          CPX     #$0008
7D55:          BCS     L7DAD



			;
			; CLEAR VAR'S
			;

			;----------------------------
			; MODE 1, WD #3, FLAGWORD,
			;		  b7 1 = 
			;		  b1 1 = 
			;		  b0 1 = HOT restart
			;----------------------------
7D57:          BCLR    L0004,#$83			; CLR ....

7D5A:          BCLR    L0019,#$40
7D5D:          BCLR    L0019,#$20

7D60:          CLRA    						; ZERO ACC'S
7D61:          CLRB    
7D62:          STD     L00FD				; RUN TIMER
7D64:          STD     L024C				; SYNC BPW
7D67:          STAA    L0062 				; ENGINE RPM/25
7D69:          STAA    L02CD				; DRP CNT'R
7D6C:          STAA    L02CE
7D6F:          STAA    L0268				; DRP'S RUN PRIOR TO CRANK
7D72:          BSET    L0051,#$08
7D75:          BCLR    L0086,#$08
7D78:          BCLR    L004F,#$80			; CLR b7, ENGINE RUNNING
7D7B:          BCLR    L004F,#$10			; CLR b4, RUN FUEL
7D7E:          BCLR    L0004,#$08			; CLR b3, BAD SHUT DOWN

7D81:          CPX     L4009
7D84:          BCS     L7DAD
7D86:          LDD     #$5008
7D89:          STAB    L3039

7D8C:          TAP     
7D8D:            *****
7D8E:  L7D8E   BRA     L7D8E
		;----------------------------------------

7D90:  L7D90   BRCLR   L0051,#$08,L7DA7
7D94:          BCLR    L0051,#$08

7D97:          BCLR    L0046,#$80			; CLR b7, HAS BEEN IN CLS LP ONCE SINCE START UP 
7D9A:          BCLR    L0044,#$08			; CLR b3, 1st DRP VALID
7D9D:          BCLR    L003E,#$08			; CLR b3,  A/F DECAY INT DONE FOR P/D


7DA0:          CLRA    						;
7DA1:          STAA    L0223    			; CLR ERR 32, EGR FAIL CNT'R
7DA4:          STAA    L027D				; CLR COLD PK/NEUT 5 SEC TMR
											;
7DA7:  L7DA7   BSET    L0086,#$08			; SET b3, 
											;
7DAA:          LDX     #$FFFF				;
7DAD:  L7DAD   INX     						;
7DAE:          STX     L027E				;

                ;-------------
                ; LD COP REG
                ;-------------
7DB1:          LDAA    #$55					; RESET COP1
7DB3:          STAA    L303A				; COP1

7DB6:          LDAA    L0041 				; TCC A/C & EGR MD WD
7DB8:          ANDA    #$10					;  A/C PRESSURE SW, (A/C ON)

			;----------------------------------------------
			; AFR MD BYTE 5,	 0001 0000, (DIG I/O)
			;
			; b7 1 = MAN, (0 = TCC)
			; b6 1 = TCC (Non Elect xmish)
			; b5 1 = Not Used 
			; b4 1 = CONV OVER HEAT PROTECTION
			;
			; b3 1 = BURST KNOCK RETARD
			; b2 1 = A/C CLUTCH CNT'L, 0 = CPI TUNE
			; b1 1 = Not Used
			; b0 1 = 1 DO RPM/MPH LMT, (GOV'R OPT)
			;
			;----------------------------------------------
7DBA:          TST     L400F				; AFR MD BYTE 5
7DBD:          BMI     L7DC4				;

7DBF:          LDAB    L0089				;
7DC1:          ANDB    #$20					; b5, (TCC IS IN LOCK ADJ MODE)
7DC3:          ABA     						;
											;
7DC4:  L7DC4   LDAB    L0047				;
7DC6:          ANDB    #$FE					; 1111 1110 
7DC8:          CBA     						;
7DC9:          BNE     L7DE7				; BR IF B ne A


			;
			; CK IF TRANSIENT RPM
			;
7DCB:          LDAB    L0063				; RPM/12.5
7DCD:          SUBB    L0065				; OLD RPM/12.5
7DCF:          BCC     L7DD2				; BR IF CURRENT RPM GT OLD RPM

7DD1:          NEGB    						;
7DD2:  L7DD2   CMPB    L413A				; 100 RPM DIFF FOR TRANSIENT MAP
7DD5:          BHI     L7DE7				; BR IF ABS DIFF RPM GT THRESH <----<<<<

7DD7:          BRCLR   L0050,#$80,L7DE7		; BR IF NOT b7, IDLE


        ;----------------------------------------------
		;  NWAF1, A/F MODE WD 1
		;
		; b7 1 = CLSD LOOP
		; b5 1 = CLSD LP 
		;----------------------------------------------
7DDB:          BRCLR   L003E,#$A0,L7DE7		; BR IF NOT b7 & b5, 

7DDF:          LDAB    L01C5				; GET OLD TRANSIENT MAP APPLY TIMER
7DE2:          BEQ     L7DEF				; BR IF TIMER = Z

7DE4:          DECB    						; DECR TRANSIENT MAP APPLY TIMER
											;
7DE5:          BRA     L7DEA				;
		;----------------------------------------

7DE7:  L7DE7   LDAB    L4139				; 800 Msec TRANSIENT MAP APPLY TIME
7DEA:  L7DEA   STAB    L01C5				; SAVE NEW TRANSIENT MAP APPLY TIMER
											;
7DED:          ORAA    #$01					; SET b0, DO TRANSIENT MAP
7DEF:  L7DEF   STAA    L0047				; TRANSIENT MAP APPLY TIMER FLAG
											;
7DF1:          LDAA    L01D9				; %TPS
7DF4:          STAA    L01DA				;
											;
7DF7:          JSR     LB1CF				;
											;
7DFA:          BRSET   L0098,#$01,L7E03		; BR IF b0, (XMISH TPS ERR)
											;
7DFE:          STAA    L01D9				; %TPS
											;
7E01:          BRA     L7E09
		;----------------------------------------

7E03:  L7E03   LDAA    L5B23				; 48 A/D TPS COUNTS DEFAULT
7E06:          STAA    L01D9 				; %TPS
											



    	;---------------------------------------------
    	; SLOW o2 TIME CONSTANT
    	; 
    	;---------------------------------------------
7E09:  L7E09   LDAB    L48BD				; 0.008 SLOW o2 FILTER FOR IDLE
											;
7E0C:          BRSET   L0050,#$80,L7E1A		; BR IF b7, IDLE FLAG

    	;---------------------------------------------
    	; SLOW o2 TIME CONSTANT vs AIR FLOW
    	; (non idle)
    	;
    	;  TBL =  255  * Const.
    	;---------------------------------------------
7E10:          LDAA    L027B				; AIR FLOW
7E13:          LDX     #$4D05				; INDEX SLOW o2 TIME CONSTANT Vs. AIR FLOW TBL
7E16:          JSR     LF4C1				; 2d LK UP 

7E19:          TAB     						; o2 TIME CONSTANT TO B Reg
			
			;
			; CK O2 LIMITS FOR FOR SLO o2 FILTER
			;
7E1A:  L7E1A   LDAA    L48BB				; 156 Mv LOW o2 LIMIT FOR SLO o2 FILTER
7E1D:          CMPA    L01D5				; o2 VOLTS * 226 (A/D RESULT)
7E20:          BHI     L7E2D				; BR IF o2 VDC GT THRESH

7E22:          LDAA    L48BC				; 799 Mv HI o2 LIMIT FOR SLO o2 FILTER
7E25:          CMPA    L01D5				; o2 VOLTS * 226 (A/D RESULT)
7E28:          BCS     L7E2D				; BR IF o2 VDC LT THRESH

			;
			; FILTER o2 VOLTS  
			;
7E2A:          LDAA    L01D5				; NEW o2 VOLTS * 226 (A/D RESULT)
7E2D:  L7E2D   LDX     L01D2				; OLD FILTERED o2 VOLTAGE
7E30:          JSR     LF459				; LAG FILT
											;
7E33:          STD     L01D2				; FILTERED o2 VOLTAGE

		;
		; CK DIG I/O MD WD
		;
7E36:          LDAA    L400F				; AFR MD BYTE 5, 0001 0000, (DIG I/O) <--***
7E39:          ANDA    #$01					; b0 1 = 1 DO RPM/MPH LMT, (GOV'R OPT)
7E3B:          BEQ     L7E40				; BR IF NOT b0

7E3D:          JSR     L90D3				;

7E40:  L7E40   LDAB    L01C6				; CURRENT MAP VAL
7E43:          CLRA    						;
7E44:          LDX     #$02B6				; 694d
7E47:          FDIV    						;
7E48:          XGDX    						;
7E49:          ADDD    #$0A59				; 2649
7E4C:          STD     L0257				;
											; 
7E4F:          BRSET   L004F,#$10,L7EA6		; BR IF b4, RUN FUEL

7E53:          JSR     LAE5C				;

7E56:          CLRB    						;
7E57:          LDAA    L01C0				; GET CURRENT MAP VALUE
7E5A:          STD     L01C7				; OLD MAP

7E5D:          LDAA    L01D9				; TPS
7E60:          STD     L01DE				;
7E63:          STD     L01DC				; OLD TPS

7E66:          JSR     L85B2				;

7E69:          ASLD    
7E6A:          BCC     L7E6F				; BR IF NO OVERFLOW

7E6C:          LDD     #$FFFF				; USE MAV VAL FOR ... PW'S
7E6F:  L7E6F   STD     L02CF				;... PW'S



    		;-----------------------------------------
    		; BPW MULT vs BATTERY
    		;
    		; FACTOR * 128
    		;-----------------------------------------
7E72:          JSR     LC56F

7E75:          LDAA    L0055				; BATTERY VOLTS * 10
7E77:          LDX     #$4988				; BPW MULT vs BATTERY
7E7A:          JSR     LF4C1				; 2d LK UP

7E7D:  L7E7D   LDX     #$02CF				; BPW 
7E80:          JSR     LF550				; MUL 8X16 Subroutine
7E83:          STD     L02CF				; BPW
											;
7E86:          LDX     #$400C				; AFR MD BYTE 2	 1011 0111 <-----*****
7E89:          BRSET   0,X,#$04,L7E9A		; BR IF b2, 1 = CRANK FUEL ALL INJ'S EACH DRP

        
    	;---------------------------------------------
    	; LK UP DRP'S Vs. COOL TEMP
    	;
    	; (HOLD OFF CRANKING FUEL FOR N DRP'S)
       	;---------------------------------------------
7E8D:          LDAA    L0006				; COOLANT
7E8F:          LDX     #$4DCD				; DRP TBL vs COOL
7E92:          JSR     LF4C1				; 

7E95:          CMPA    L02CD				; DPR CNT'R
7E98:          BLS     L7E9D				;

7E9A:  L7E9A   JMP     L852C				;


7E9D:  L7E9D   LDD     L02CF				; BPW
7EA0:          JSR     L7827				;

7EA3:          JMP     L84F5				;
 

7EA6:  L7EA6   JSR     LAE5C				;

			;-----------------------------
			; AFR MD WORD 0,	  
			;     b1 1 = VATS PASS/FAIL             
			;-----------------------------
7EA9:          BRSET   L003D,#$02,L7EB2		; BR IF b1, VATS PASSED 

7EAD:          CLRA    						;
7EAE:          CLRB    						;

7EAF:          JMP     L84F5				;


7EB2:  L7EB2   CLRB    						;
											;
7EB3:          LDAA    L01C0				; GET CURRENT MAP VALUE
7EB6:          SUBD    L01C7				; OLD MAP
7EB9:          BLS     L7F17				; BR IF MAP - OLD MAP IS ...

7EBB:          ADDD    #128					;
7EBE:          STAA    L01CA				;

			;
			; GET DIFF MAP THRESH 
			;										   	
7EC1:          LDAB    L48C0				; 4.0 Kpa DIFF (AT IDLE), TO ENABLE ACELL ENRICH
7EC4:          BRSET   L0050,#$80,L7ECB		; BR IF b7, IDLE

7EC8:          LDAB    L48BF				; 7.7 Kpa DIFF, TO ENABLE ACELL ENRICH

	
			;
			; CK %TPS FOR DIF MAP x2 THRESH
			;										
7ECB:  L7ECB   LDAA    L01D9				; %TPS
7ECE:          CMPA    L48C1				; IF TPS G.T. 14.8%, MULT L48AE & L48AF BY 2
                    						; FOR DIFF MAP TEST
7ED1:          BHI     L7ED8				; BR IF ...
	
7ED3:          ASLB    						; %TPS/2
7ED4:          BCC     L7ED8				; BR IF NO UNDERFLOW

7ED6:          LDAB    #255					; USE MAX VALUE
											;
7ED8:  L7ED8   LDAA    L01CA				;
7EDB:          CBA     						;
7EDC:          BLS     L7F1A				; BR IF ...


    	;----------------------------------------------
    	; ACELL DIFF MAP vs DIFF MAP
    	; STRECH'S ASYNC PULSE FOR DIFF MAP
    	;
    	; *** PUMP SHOT *********
    	; TABLE = 16.384 * MSEC
    	;----------------------------------------------
7EDE:          LDX     #$4B49				; ACELL DIFF MAP
7EE1:          JSR     LF4B6				; 2d Lk Up

7EE4:          LDAB    L01D9				; %TPS
7EE7:          CMPB    L48C2				; IF TPS G.T. 44.9%, DIFF MAP A.E. MULT * 2
                    						; (TABLE VAL FM TBL L4B38)
7EEA:          BLS     L7EF1				;

7EEC:          ASLA    						; N x 2
7EED:          BCC     L7EF1				; BR IF NO OVERFLOW

7EEF:          LDAA    #255					; USE MAX VALUE
											;
    	;----------------------------------------------
    	; ACELL ENRECH DIFF MAP CORRECTION FACTOR  vs RPM
    	;
    	;
    	; TBL = MULT * 128
    	;----------------------------------------------
7EF1:  L7EF1   PSHA    						;

7EF2:          LDAA    L0062 				; ENGINE RPM/25

7EF4:          LDAB    #16					; 
7EF6:          LDX     #$4BA4		 		; ACELL ENRECH DIFF MAP	TBL
7EF9:          JSR     LF49A				; 2D LK UP

7EFC:          PULB    						;
7EFD:          MUL     						; APPLY MULT
7EFE:          ASLD    						; N x 2
7EFF:          BCC     L7F03				; BR IF NO OVERFLOW

7F01:          LDAA    #255					; USE MAX VALUE

7F03:  L7F03   LDAB    L023D
7F06:          MUL     
7F07:          LSRD    						; n/32    
7F08:          LSRD    
7F09:          LSRD    
7F0A:          LSRD    
7F0B:          LSRD    
7F0C:          TSTA    
7F0D:          BEQ     L7F11				; BR IF NO OVERFLOW

7F0F:          LDAB    #255					; FORCE MAX VAL
7F11:  L7F11   TBA     
7F12:          BSET    L0005,#$80

7F15:          BRA     L7F1E
		;----------------------------------------

7F17:  L7F17   CLR     L01CA
7F1A:  L7F1A   CLRA    
7F1B:          BCLR    L0005,#$80
7F1E:  L7F1E   STAA    L023E

7F21:          LDAA    L01D9				; %TPS
7F24:          SUBA    L01DC				; OLD TPS
7F27:          BLS     L7F6C				; BR IF ... 

7F29:          TST     L01DD				; 
7F2C:          BPL     L7F31				; BR IF ...

7F2E:          DECA    						;
7F2F:          BEQ     L7F6C				;

7F31:  L7F31   BRSET   L0005,#$40,L7F3A		; BR IF b6,

7F35:          CMPA    L48C3				; IF DIFF TPS G.T. 2% DIFF MAP ACELL ENRICH IS X2
7F38:          BLS     L7F6C				; BR IF DIFF TPS LT THRESH

7F3A:  L7F3A   ASLA    						; n x 2
7F3B:          BCC     L7F3F				; BR IF NO OVERFLOW

7F3D:          LDAA    #255					; FORCE MAX XAL FOR TPS

    	***********************************************
    	* STRETCH ASYNC BPW FOR DIFF TPS ENRICH
    	*
    	* *** PUMP SHOT *********
    	*
    	* (L4921  12 MSEC MAX ASYNC BPW, SO MAX IS 196d)
    	*
    	* TABLE = 16.384 * MSEC
    	***********************************************
7F3F:  L7F3F   LDX     #$4B4F
7F42:          JSR     LF4C1				; 2d LK UP	

			;
			; ACCEL DIFF QUAL
			;
7F45:          LDAB    L0284				; Vss/1. (KPH = 1.61)
7F48:          CMPB    L48C5				; 30 MPH, IF MPH L.T. 30 MPH USE L48C2 FACTOR
7F4B:          BCC     L7F5A				; BR IF Vss GT THRESH

7F4D:          LDAB    L48C4				; IF MPH L.T. L48C3, Acell Enr = TPS AE * 1.1
7F50:          MUL     
7F51:          ADDD    #64					;
7F54:          ASLD    
7F55:          BCC     L7F5A				; BR OF NO OVERFLOW

7F57:          LDD     #65525				; FORCE MAX VALUE

7F5A:  L7F5A   LDAB    L01E4
7F5D:          MUL     
7F5E:          ADDD    #64
7F61:          ASLD    
7F62:          BCC     L7F67				;

7F64:          LDD     #65525				; FORCE MAX VALUE 

7F67:  L7F67   BSET    L0005,#$40			; SET b6

7F6A:          BRA     L7F70				
		;----------------------------------------

7F6C:  L7F6C   CLRA    						;
7F6D:          BCLR    L0005,#$40			; BLR b6 
7F70:  L7F70   STAA    L023F				;
											;
7F73:          BRCLR   L0002,#$02,L7F86		; MAJOR LOOP COUNTER


			;
			; FILTER ACCEL ENRICH TPS
			;
7F77:          LDAB    L01E5				; ACCEL ENRICH DIFF TPS COEF
7F7A:          LDAA    L01D9				; %TPS
7F7D:          LDX     L01DC				; OLD TPS
											;
7F80:          JSR     LF459				; LAG FILT
											;
7F83:          STD     L01DC				; SAVE FILTERED 
											

7F86:  L7F86   LDAB    L01C0				; GET CURRENT MAP VALUE
7F89:          CMPB    #64					; 34 Kpa
7F8B:          BLS     L7F92				; BR IF MAP 

7F8D:          LSRB    						; N/2
7F8E:          ADCB    #$00					;
7F90:          ADDB    #32					; 22 Kpa
											;

			;-----------------------------------------
			;  VE TABLE SLECTOR QUALS
			; (CK IDLE PARK TBL TPS & Vss QUALS)
			;-----------------------------------------

			;
			; CK TPS QUALS
			;
7F92:  L7F92   LDAA    L01D9				; %TPS
7F95:          CMPA    L48DA				; 2.3% TPS MAX IDLE FUEL TABLE
7F98:          BCC     L7FA8				; BR IF TPS GT THRESH



			;
			; CK Vss QUALS
			;
7F9A:          LDAA    L0284				; Vss/1
7F9D:          CMPA    L48D8				; 2 MPH, MAX FOR IDLE FUEL TABLE
7FA0:          BCC     L7FA8				; BR IF Vss GT THRESH
 

			;
			; CK RPM QUALS
			;
7FA2:          LDAA    L0062 				; ENGINE RPM/25
7FA4:          CMPA    #72					; 1800 RPM
7FA6:          BCS     L7FB5				; BR IF RPM < 1800 RPM

    		;--------------------------------------------------
    		; OPEN TPS FUEL vs MAP vs RPM, (FL1)
    		;
    		; TYPE  31 ECM
    		;  
    		;  TBL = %VE *  2.56 
    		;--------------------------------------------------
7FA8:  L7FA8   LDAA    L0062 				; ENGINE RPM/25
7FAA:          LDX     #$49D5				; OPEN TPS FUEL TBL
											;
7FAD:          BSET    L004F,#$08			; SET b3, OPEN TPS VE FLAG

7FB0:          JSR     LF4DE				; 3d LK UP

7FB3:          BRA     L7FD5
		;----------------------------------------

			;
			; INSURE RPM NOT OVER MAX LIMIT OF 1800 RPM
			;
7FB5:  L7FB5   LDAA    L0063				; RPM/12.5	
7FB7:          CMPA    #144					; 1800 RPM
7FB9:          BLS     L7FBD				; BR IF RPM ....

7FBB:          LDAA    #144					;

    		;--------------------------------------------------
    		; CLOSED TPS FUEL vs MAP vs RPM, (FL2)
    		; TYPE  31  ECM
    		;
    		; ___ MPH MAX
    		; ___ % TPS MAX
    		;
    		;  TBL = %VE *  2.56 
    		;--------------------------------------------------
7FBD:  L7FBD   LDX     #$4A88				; CLOSED TPS FUEL
7FC0:          JSR     LF4DE				; 3d LK UP

7FC3:          BRCLR   L004F,#$08,L7FD5		; BR IF NOT b3, OPEN TPS VE FLAG

7FC7:          LDAB    L020F				; CURRENT INTEGRATOR
7FCA:          CMPB    L490F				;	 CLSD LP INT FOR RESET WHEN
                        					; SWITCHING VE TABLES
7FCD:          BHI     L7FD2				;

7FCF:          BSET    L004F,#$20			; SET b5, VE INT RESET
7FD2:  L7FD2   BCLR    L004F,#$08			; CLR b3, OPEN TPS VE FLAG

7FD5:  L7FD5   STAA    L0231				; VE RESULTS <---<<<

7FD8:          LDD     L0257				; CURRENT MAP VALUE


			;
			; CALC CYL VOL
			;
7FDB:          LDX     L0236
7FDE:          FDIV    
7FDF:          PSHX    
7FE0:          TSX     
7FE1:          LDAA    L4D94				; 0.923 Litre  CYL VOL & UNIT CONV, (7.4l)
7FE4:          JSR     LF550				; 8 x 16 Mult w/16b result rounded to upper 16b
											;
7FE7:  L7FE7   PULX    						;
7FE8:          STD     L0238				;
											;
7FEB:          LDAA    L0231				; VE RESULTS <---<<<
7FEE:          LDX     #$0238				; 0568
7FF1:          JSR     LF550				; 8 x 16 Mult w/16b result rounded to upper 16b
											;
7FF4:          STD     L0234				; AFR


7FF7:          LDX     L01E8
7FFA:          IDIV    
7FFB:          PSHX    
7FFC:          LDX     L01E8
7FFF:          FDIV    
8000:          XGDX    
8001:          TAB     
8002:          PULA    
8003:          TSTA    
8004:          PULA    
8005:          BNE     L800A

8007:          ASLD    
8008:          BCC     L800D				; BR IF NO OVERFLOW

800A:  L800A   LDD     #$FFFF				; FORCE MAX VALUE
800D:  L800D   STD     L0232				; AIR FLOW

8010:          LDX     L0234
8013:          LDAA    L024A				; AFR
8016:          CLRB    
8017:          XGDX    
8018:          LSRD    
8019:          LSRD    
801A:          FDIV    
801B:          XGDX 

       	;---------------------------------
		; 8.55 GMS/SEC INJ FLOW RATE,
		;  (7.4l TBI V8)
		;
       	; CAL N * 819.2  FOR TBI
       	;       * 273.1  FOR CPI
       	;       * 1638.4 FOR PFI 
       	;---------------------------------
801C:          LDX     L4D92
801F:          IDIV    
8020:          PSHX    

       	;---------------------------------
		; 8.55 GMS/SEC INJ FLOW RATE,
		;  (7.4l TBI V8)
		;
       	; CAL N * 819.2  FOR TBI
       	;       * 273.1  FOR CPI
       	;       * 1638.4 FOR PFI 
       	;---------------------------------
8021:          LDX     L4D92
8024:          FDIV    
8025:          XGDX    
8026:          TAB     
8027:          PULA    
8028:          TSTA    
8029:          PULA    
802A:          BEQ     L802F				; BR IF ... Z

802C:          LDD     #65535				; 1000 msec
802F:  L802F   STD     L024E				; SYNC BPW 

8032:          LDD     L01B2
8035:          ADDD    #128
8038:          LDX     #$024E				; SYNC BPW
803B:          JSR     LF550 				; 8 x 16 Mult w/16b result rounded to upper 16b
											;
803E:          LSRD    						; n/4
803F:          LSRD    
8040:          STD     L0252

8043:          LDD     L024E				; SYNC BPW
8046:          SUBD    L0252				;
8049:          STD     L024E				; SYNC BPW

804C:          LDAA    L0248 				; BLM
804F:          BMI     L8055				; BR IF BLM >127


		;-----------------------------
		; AFR MD WORD 0,	  $003D
		;	 b5 1 = PWR ENR IS ACTIVE                
		;-----------------------------
8051:          BRSET   L003D,#$20,L8058		; BR IF b5, BLK LRN ADDR CHANGE 1 = CHANGED

8055:  L8055   JSR     L80EE

		;
		; CURRENT ERR MD 1
		;
8058:  L8058   BRSET   L0016,#$10,L809C		; BR IF b4, ERR 16, Vss BUFFER 


		;
		; CK MODE WD FOR 1 = MAN, (0 = TCC) 
		;
805C:          LDX     #$400F				; AFR MD BYTE 5,
805F:          BRSET   0,X,#$80,L8073		; BR IF NOT b7, MAN, (0 = TCC)

8063:          LDAA    L5155				; 25 msec XMISH ABUSE CHECK PERIOD
											;
8066:          BRSET   L0041,#$20,L8070		; BR IF b5, PARK/NEUTRAL

806A:          LDAA    L084D				;
806D:          BEQ     L809C				; BR IF = Z

806F:          DECA    						; DECR  XMISH ABUSE CHECK PERIOD
8070:  L8070   STAA    L084D				; XMISH ABUSE CHECK PERIOD
											;
8073:  L8073   LDAA    L0812				; Vss/1
8076:          CMPA    L5156				; 16 MPH, MIN Vss FOR ABUSE TEST
8079:          BHI     L809C				;  BR IF Vss < THRESH

807B:          LDAA    L01D9				; %TPS
807E:          CMPA    L5159				; 75% TPS MIN FOR ABUSE TEST
8081:          BLS     L809C				; BR IF TPS LT THRESH

8083:          LDAA    L5157
8086:          BRCLR   L0053,#$08,L808D		; BR IF NOT b3, HI RPM INDICATED 
											;				BY XMISH (ABUSE LOGIC)

808A:          LDAA    L5158				; 3800 RPM, (ABUSE TEST)
808D:  L808D   CMPA    L0061				; RPM/25
808F:          BCS     L8096				; BR IF RPM GT THRESH

8091:          BCLR    L0053,#$08			; CLR b3, HI RPM INDICATED 
											;			BY XMISH (ABUSE LOGIC) 

8094:          BRA     L809C
		;----------------------------------------

8096:  L8096   BSET    L0053,#$08			; SET b3, HI RPM INDICATED
											;			 BY XMISH (ABUSE LOGIC)
8099:          JMP     L821D
		;-------------------------------------------------

		;-------------------------------------------------
		;  RPM/MPH LIMITER
		;
		;
		;-------------------------------------------------

		;
		; CK IF DO RPM/MPH LMT ENABLED
		;
809C:  L809C   LDX     #$400F				; AFR MD BYTE 5
809F:          BRCLR   0,X,#$01,L80A7		; BR IF NOT b0, 1 DO RPM/MPH LMT, (GOV'R OPT)

80A3:          BRCLR   L006F,#$34,L8106		; BR IF NOT b2, b4 & b5

80A7:  L80A7   LDX     #$4967			    ; INDEX HI RPM FUEL CUT OFF 
80AA:          LDY     #$496B				; INDEX HI MPH FUEL CUT OFF
											;
80AE:          BRCLR   L0046,#$10,L80B5		; BR IF NOT b4,  OVERSPEED FUEL SHUT OFF 

80B2:          INX     						; ADJ INDEX FOR FUEL OFF/ON
80B3:          INY     						;
											; 

		  		;
				; CURRENT ERR MD 1
				;
80B5:  L80B5   BRSET   L0016,#$10,L80BD		; BR IF b4, ERR 16, Vss BUFFER

80B9:          BRCLR   L0099,#$03,L80BF		; BR IF NOT b0 & B1

80BD:  L80BD   INX     						; ADJ INDEX FOR FUEL OFF/ON
80BE:          INX     						;
80BF:  L80BF   LDAB    L0062 				; ENGINE RPM/25
80C1:          CMPB    0,X					;
80C3:          BHI     L80E2				;

80C5:          LDAB    L0284				; MPH/1
80C8:          CMPB    0,Y					;
80CB:          BLS     L8106				;

80CD:          LDAB    L0062 				; ENGINE RPM/25
80CF:          CMPB    L4966				; 1200 RPM FUEL ON
80D2:          BLS     L8106				; BR IF RPM < 1200 RPM 

80D4:          LDAB    L026A				; HI RPM Fuel C/O TIMER
80D7:          CMPB    L4965				; 1.5 sec QUAL TIME, HI RPM Fuel C/O
80DA:          BCC     L80E2				;

80DC:          INCB    						; INCR C/O TIMER
80DD:          STAB    L026A				; HI RPM Fuel C/O TIMER

80E0:          BRA     L8109
		;----------------------------------------

80E2:  L80E2   BSET    L0046,#$10			; SET b4, OVERSPEED FUEL SHUT OFF 
											
80E5:          LDD     #$0000				; ZERO OUT FUEL FOR CUT OFF
80E8:          STD     L024E				; SYNC BPW

80EB:          JMP     L821D
 		;----------------------------------------------


		;----------------------------------------------
80EE:  L80EE   PSHA    
80EF:          LDD     L024E				; SYNC BPW
80F2:          ASLD    						; x2
80F3:          BCC     L80F8				; BR IF OVERFLOW

80F5:          LDD     #65535				; USE MAX SYNC PW
80F8:  L80F8   STD     L024E				; SYNC BPW

80FB:          PULA    						;
80FC:  L80FC   LDX     #$024E				; 0590d,  SYNC BPW
80FF:          JSR     LF550				; MUL 8X16 Subroutine
											;
8102:          STD     L024E				; SYNC BPW 

8105:          RTS     


8106:  L8106   CLR     L026A				; HI RPM Fuel C/O TIMER

8109:  L8109   BCLR    L0046,#$10			; CLR b4,OVERSPEED FUEL SHUT OFF 

810C:          LDAA    L087F

			;----------------------------------------------
			; NWAF1, A/F MODE WD 1
			;
			; b0 1 = DECELL FUEL C/O TPS ACELL ENRICH
			;----------------------------------------------
810F:          BRCLR   L003E,#$01,L811B		; BR IF NOT b0, DECELL FUEL C/O TPS ACEL ENRICH 

8113:          BCLR    L003E,#$01			; CLR b0, DECELL FUEL C/O TPS ACEL ENRICH
											;
8116:          ADDA    L48C6				; 2.0 msec BPW, Acell Enr PW IF DECEL 
											;	CUT OFF OFF'ED BY TPS INCREASE
8119:          BCS     L8135				; BR IF OVERFLOW

811B:  L811B   BRSET   L0041,#$10,L8124		; BR IF b4, A/C PRESSURE SW, (A/C ON)

811F:          BCLR    L0041,#$08			; CLR b3, A/C ACCEL ENR ENABLED

8122:          BRA     L8130
		;----------------------------------------

8124:  L8124   BRSET   L0041,#$08,L8130		; BR IF b3, A/C ACCEL ENR ENABLED

8128:          BSET    L0041,#$08			; CLR b3, A/C ACCEL ENR ENABLED
											;
812B:          ADDA    L48C7				; 0 msec Acell Enr PW IF A/C OFF -> ON  XISITION 
812E:          BCS     L8135				;
											;
8130:  L8130   ADDA    L023F				;
8133:          BCC     L8137				; BR IF NO OVERFLOW

8135:  L8135   LDAA    #255					; FORCE MAX VALU
8137:  L8137   BNE     L813F				; BR IF NZ

8139:          BRSET   L0005,#$80,L814C		;

813D:          BRA     L8164				;
		;----------------------------------------

813F:  L813F   LDAB    L023C
8142:          MUL     
8143:          LSRD    
8144:          LSRD    
8145:          LSRD    
8146:          ADDD    L023A				; ASYNC BPW
8149:          STD     L023A				; ASYNC BPW

			;-----------------------------
			; AFR MD WORD 0,	  $003D
			;	 b6 1 = ACELL ENR IS ACTIVE
			;-----------------------------                 
814C:  L814C   BRSET   L003D,#$40,L8153		; BR IF b6, ACELL ENR IS ACTIVE

8150:          BSET    L006E,#$08			; Set b3, ACELL ENR 1st TIME

					;----------------------------
					; MAF, AFR MD WORD 0,
                    ; 		b7 1 = DELIVER ASYNC PULSE	
                    ; 		b6 1 = ACELL ENR IS ACTIVE   
					;----------------------------
8153:  L8153   BSET    L003D,#$C0			; SET b7, b6, 
8156:          BSET    L006E,#$01			; SET b0. EGR DIAG INT RESET
8159:          BSET    L0044,#$02			; SET b1, ACELL ENR CLAMP ACTIVE

815C:          LDAA    L48CA				; HOLD INT HI 1 SEC AFTER Acell Enr PW
815F:          STAA    L081D				;

8162:          BRA     L8175
		;----------------------------------------

8164:  L8164   BCLR    L003D,#$40			; CLR b6, ACELL ENR IS ACTIVE
 											;
8167:          LDAA    L081D				;
816A:          BEQ     L8172				;

816C:          DECA    						;
816D:          STAA    L081D				;

8170:          BRA     L8175
		;----------------------------------------

8172:  L8172   BCLR    L0044,#$02			; CLR b1, ACELL ENR CLAMP ACTIVE

8175:  L8175   LDAA    L0006				; COOL VALUE
8177:          CMPA    L4944				; 74c MIN TEMP FOR DECEL FUEL CUT OFF
817A:          BCC     L817F				; BR IF COOL GT THRESH

817C:          JMP     L824D


817F:  L817F   BRSET   L0041,#$20,L81E7		; BR IF b5, PARK/NEUTRAL

8183:          LDAB    L006F
8185:          BITB    #$24
8187:          BNE     L81A1

8189:          LDAB    #32

        ;---------------------------------------------
    	; DECEL FUEL CUT OFF THRESH vs RPM
    	;
    	;  TBL =  2.56  * %TPS
        ;---------------------------------------------
818B:          LDAA    L0062 				; ENGINE RPM/25
818D:          LDX     #$4C94				; DECEL FUEL CUT OFF THRESH vs RPM
8190:          JSR     LF49A				;
											;
8193:          CMPA    L01D9				; %TPS
8196:          BHI     L81A1				; 

8198:          BRCLR   L0046,#$08,L81FD		; BR IF NOT b3, DECEL FUEL C/O

819C:          BSET    L003E,#$01			; SET b0, DECELL FUEL C/O TPS ACELL ENRICH 

819F:          BRA     L81FD
		;----------------------------------------

81A1:  L81A1   LDAA    L0065				; OLD RPM/12.5
81A3:          SUBA    L0063				; RPM/12.5
81A5:          BLS     L81AC				; BR IF 

81A7:          CMPA    L4945				; DROP 100 RPM TO DISABLE DECEL FUEL CUT OFF
81AA:          BHI     L81E7				;

81AC:  L81AC   LDAB    L006F				;
81AE:          BITB    #$0048				;
81B0:          BNE     L81D5				;

81B2:          LDAA    L01CA				;
81B5:          CMPA    L4946				; 79.4 Kpa INCR TO DISABLE DECEL FUEL CUT OFF
81B8:          BHI     L81E7				;

81BA:          LDAA    L01CF				;


			;------------------------------
			; AFR MD BYTE 4,	 0000 0011 
			; b1 1 = USE ALT CMAP vs
			;    MAP LD FOR FUEL CUR HYST PAIR
			;------------------------------
81BD:          LDAB    L400E				;
81C0:          BITB    #$02					; b1
81C2:          BNE     L81C7				; BR IF

81C4:          LDAA    L01C0 				; GET CURRENT MAP VALUE
81C7:  L81C7   CMPA    L493D				; 24 KPa MAX FOR DECEL FUEL CUT OFF
81CA:          BCS     L81D5				; BR IF MAP LT THRESH

81CC:          BRCLR   L0046,#$08,L8200		; BR IF NOT b3, DECEL FUEL C/O

81D0:          CMPA    L493E				; 50.0 Kpa TO DISABLE DECEL FUEL CUT OFF
81D3:          BCC     L8200				;

		;
		; CK DECEL FUEL CUT OFF RPM THRESH
		;
81D5:  L81D5   LDAA    L0243				; DECEL FUEL CUT OFF RPM THRESH

81D8:          BRSET   L0046,#$08,L81E3		; BR IF b3, DECEL FUEL C/O 

81DC:          ADDA    L493A				; 500 RPM DECEL FUEL CUT OFF HYST
81DF:          BCC     L81E3				; BR IF NOT OVER FLOW

81E1:          LDAA    #255					; 6375 RPM
81E3:  L81E3   CMPA    L0062 				; ENGINE RPM/25
81E5:          BCS     L8205				; BR IF BPM > 6375

81E7:  L81E7   LDAA    L0245				;
81EA:          BEQ     L81FD				;

81EC:          LDD     L023A				;
81EF:          ADDD    L493F				; 2303, 35.14 Msec ??
81F2:          BCC     L81F7				;

81F4:          LDD     #$#32767		  		;
81F7:  L81F7   STD     L023A				;
											;
81FA:          BSET    L003D,#$80			; SET b7, DELIVER ASYNC PULSE
81FD:  L81FD   CLR     L0245				;
8200:  L8200   LDAA    L4941				;
											;
8203:          BRA     L8242				;
		;----------------------------------------

8205:  L8205   BRSET   L0016,#$10,L8218		; BR IF b4, ERR...  

8209:          LDAA    L493B				;
820C:          BRCLR   L0046,#$08,L8213		; BR IF NOT b3, DECEL FUEL C/O 

8210:          LDAA    L493C				; 7 MPH TO DISABLE DECEL FUEL CUT OFF
8213:  L8213   CMPA    L0284				; MPH/1 
8216:          BHI     L81E7				; BR IF Vss 

8218:  L8218   LDAA    L0246
821B:          BNE     L823B

821D:  L821D   BSET    L0046,#$08			; SET b3,  DECEL FUEL C/O
8220:          LDAA    L4942				; 500 Msec, MAX TIME AFTER EXIT TO DO L49-- BPW
8223:          STAA    L0245				;
											;
8226:          BSET    L003D,#$10			; SET b4, DECEL ENLEAN IS ACTIVE 
8229:          LDAA    L0244				; DECEL FUEL CUT OFF TIMER
822C:          SUBA    L4943				; 62.5%, DECEL FUEL C/O MULT, 
											;		(Decrement % per 12.5 msec LP)
822F:          BCC     L8232				; BR IF ... GT 160

8231:          CLRA    
8232:  L8232   STAA    L0244				; DECEL FUEL CUT OFF TIMER

8235:          JSR     L80FC
8238:          JMP     L82ED
			;-----------------------------------------
 
			
			;-----------------------------------------
823B:  L823B   LDAB    L0002				; MAJOR LOOP COUNTER
823D:          ANDB    #$0E					; 0000 1110
823F:          BNE     L8242				; BR IF ...

8241:          DECA    
8242:  L8242   STAA    L0246

8245:          LDAA    L0245
8248:          BEQ     L824D

824A:          DEC     L0245				;
											;
824D:  L824D   BCLR    L0046,#$08			; CLR b3, DECEL FUEL C/O 

8250:          LDAA    #255					; MAX VALUE
8252:          STAA    L0244				; DECEL FUEL CUT OFF TIMER

8255:          LDD     L01DE
8258:          ASLB    						; x 2 MULT
8259:          ADCA    #$00
825B:          BCC     L825E

825D:          DECA    
825E:  L825E   SUBA    L01D9				; %TPS
8261:          BCC     L8266				; BR IF POS RESULT

8263:          JMP     L82E7
 											
8266:  L8266   STAA    L082B				; DIFF %TPS
											;
8269:          LDX     #$400B				; AFR MD BYTE 1,  0000 0100
826C:          BRCLR   0,X,#$80,L8274		; BR IF NOT b7 (1 = DE-LATCH)

8270:          BRSET   L0053,#$02,L827F		;

8274:  L8274   LDAA    L082B				; DIFF %TPS 
8277:          CMPA    L4936				; NEG 1.2% DIFF TPS NEG ENABLE DECEL ENLEAN 
827A:          BLS     L82E7				; BR IF 

827C:          BSET    L0053,#$02			; SET b1, 
											;
827F:  L827F   LDD     L01C7
8282:          ASLB    
8283:          ADCA    #$00
8285:          BCC     L8288				;

8287:          DECA    
8288:  L8288   SUBA    L01C0				; GET CURRENT MAP VALUE
828B:          BCS     L82E7				;

828D:          CMPA    L4937
8290:          BLS     L82E7				;

8292:          CMPA    #160					;
8294:          BLS     L8298				;

8296:          LDAA    #160

        ;---------------------------------------------
    	; DECEL ENLEAN REDUCTION vs DIFF MAP
    	; (Set amt of fuel reduction as per DIFF MAP)
    	;
    	; TBL = %TPS * 2.56
        ;---------------------------------------------
8298:  L8298   LDX     #$4B20				; DECEL ENLEAN REDUCTION
829B:          JSR     LF4C1				; 2d LK UP

829E:          TAB     

    ;--------------------------------------------------
	;  DECEL ENLEAN REDUC Vs. DIFF %TPS
	;
	;		 17 LINES
	;
    ;--------------------------------------------------
829F:          LDX     #$4B2B
82A2:          LDAA    L082B				; DIFF %TPS
82A5:          JSR     LF4C1				; 2d LK UP
82A8:          ABA     						
82A9:          BCC     L82AD				; BR IF NO OVERFLOW

82AB:          LDAA    #255F

82AD:  L82AD   LDAB    L0242
82B0:          MUL     
82B1:          ASLD    
82B2:          BCS     L82BA				; BR IF OVERFLOW

82B4:          ASLD    
82B5:          BCS     L82BA				; BR IF OVERFLOW

82B7:          ASLD    
82B8:          BCC     L82BC				; BR IF NO OVERFLOW

82BA:  L82BA   LDAA    #255					; USE MAX VALUE

82BC:  L82BC   LDAB    L0284				; MPH/1
82BF:          CMPB    L4939				; 6 MPH, (DECEL ENLEAN)
82C2:          BCC     L82D1				; BR IF Vss GT THRESH

82C4:          LDAB    L4938				; 0.75 FILT FACTOR DECELL
82C7:          MUL     						; APPLY MULT
82C8:          ADDD    #64					;
82CB:          ASLD    
82CC:          BCC     L82D1

82CE:          LDD     #$FFFF
82D1:  L82D1   NEGA    
82D2:          BEQ     L82E7


82D4:          BSET    L003D,#$10			; SET b4, DECEL ENLEAN IS ACTIVE

82D7:          PSHA    
82D8:          LDX     #$023A				; 0570
82DB:          JSR     LF550				; MUL 8X16 Subroutine
82DE:          STD     L023A

82E1:          PULA    
82E2:          JSR     L80FC

82E5:          BRA     L82ED
		;----------------------------------------

 		;----------------------------------------------
		;  RPM DERIVITIVE SPK/FUEL CALIB'S
		;  SPARK CALIB'S
		;______________________________________________
82E7:  L82E7   BCLR    L003D,#$10			; CLR b4, DECEL ENLEAN IS ACTIVE
82EA:          BCLR    L0053,#$02			; CLR b1

82ED:  L82ED   LDAA    L0067				;
82EF:          CMPA    L4516				; 6375 RPM
82F2:          BCS     L830B				;

82F4:          LDAA    L01D9				; %TPS
82F7:          CMPA    L48DB				; 0%, TPS MAX FOR DERIVITVE RPM CALC
82FA:          BHI     L830B				;

82FC:          LDAA    L0284				; MPH/1
82FF:          CMPA    L48DC				; 0 MPH MAX FOR DERIVITIVE RPM CALC
8302:          BHI     L830B				; BR IF Vss GT THRESH

8304:          LDAA    L0006				; COOL VALUE
8306:          CMPA    L48DD				; 151 DEG c MIN FOR DERIVI RPM CALC
8309:          BCC     L8311				; BR IF COOL GT THRESH

830B:  L830B   LDAA    #128					;
830D:          STAA    L006C				; RPM RATIO
											
830F:          BRA     L8342
		;----------------------------------------

8311:  L8311   LDD     L006A				;
8313:          LSRD    						; x/2
8314:          LDX     L0068				; RPM/?
8316:          FDIV    						;
8317:          XGDX    						;
8318:          ADDD    #128					;
831B:          BCC     L831F				; BR IF NO OVERFLOW

831D:          LDAA    #255					; USE MAX VALUE
831F:  L831F   STAA    L006C				; RPM RATIO
8321:          CMPA    L451A			    ; LIMIT
8324:          BCS     L832B				;

8326:          LDAA    L451A			    ; LIMIT
8329:          BRA     L8333
		;----------------------------------------

832B:  L832B   CMPA    L4519				; MIN ADJ FM DRIVITIVE RPM/SPK/FUEL
832E:          BCC     L8333				;

8330:          LDAA    L4519				; MIM ADJ FM DRIVITIVE RPM/SPK/FUEL
8333:  L8333   LDX     #$024E				; SYNC BPW 
8336:          JSR     LF550				; MUL 8X16 Subroutine
											;
8339:          ASLD    						; x2
833A:          BCC     L833F				; BR IF NO OVERFLOW

833C:          LDD     #$FFFF
833F:  L833F   STD     L024E				; SYNC BPW

 
        ;---------------------------------------------
    	; BPW ALTIDUDE FACTOR vs BARO & MAP
    	;
    	; FACTOR * 128
        ;---------------------------------------------
8342:  L8342   LDAA    L01C6				;
8345:          CMPA    #216					;
8347:          BLS     L834B				;

8349:          LDAA    #216					;
834B:  L834B   LDAB    #$0097				;
834D:          MUL     						;
834E:          ADDD    #145					;
											;
8351:          LDAB    L01CC				; BARO VALUE (Kpa)
8354:          LDX     #$49AA				; BPW ALTIDUDE FACTOR TBL
8357:          JSR     LF4DE				; 3d LK UP

835A:          LDX     #$024E				; SYNC BPW
835D:          JSR     LF550				; MUL 8X16 Subroutine
8360:          ASLD    
8361:          BCC     L8366

8363:          LDD     #$FFFF
8366:  L8366   ASLD    
8367:          BCC     L836C

8369:          LDD     #$FFFF
836C:  L836C   STD     L024E				; SYNC BPW

836F:          LDAA    L0055				; BATTERY VOLTS * 10
8371:          LDX     #$4988				;
8374:          JSR     LF4C1				; 2d LK UP

8377:          LDX     #$024E				; SYNC BPW
837A:          JSR     LF550				; MUL 8X16 Subroutine
837D:          STD     L024E				; SYNC BPW

8380:          CLRA    
8381:          LDAB    L026F
8384:          BMI     L8390

8386:          ADDD    L024E				; SYNC BPW
8389:          BCC     L839C

838B:          LDD     #$FFFF
838E:          BRA     L839C
		;----------------------------------------

8390:  L8390   NEGB    
8391:          SUBD    L024E				; SYNC BPW
8394:          BCS     L8398

8396:          CLRA    
8397:          CLRB    
8398:  L8398   NEGA    
8399:          NEGB    
839A:          SBCA    #$00
839C:  L839C   STD     L024E				; SYNC BPW

839F:          CLRA    
83A0:          LDAB    L023E
83A3:          ADDD    L024E				; SYNC BPW
83A6:          BCC     L83AB

83A8:          LDD     #$FFFF
83AB:  L83AB   STD     L024E				; SYNC BPW
83AE:          STD     L0254				; ASYNC BPW

83B1:          BRCLR   L0044,#$10,L83BD		; BR IF NOT b4, IGNITION OFF 

83B5:          CLRA    
83B6:          CLRB    
83B7:          STD     L024E				; SYNC BPW

83BA:          JMP     L84BC
		;----------------------------------------------


		;-----------------------------------------------
83BD:  L83BD   LDX     #$400B				; AFR MD BYTE 1,  0000 0100 <---****
83C0:          BRCLR   0,X,#$01,L83FB		; BR IF NOT b0, 1 = CPI/PFI MODE
 
83C4:          BRCLR   L0051,#$01,L83CA		; BR IF NOT b0, 

											;
83C8:          BRA     L83F0				; 
		;----------------------------------------

83CA:  L83CA   SEI     
83CB:          LDAA    L082A
83CE:          INCA    
83CF:          BEQ     L83D4				;

83D1:          STAA    L082A				;
83D4:  L83D4   CLI     						;
83D5:          LDY     L0254				; ASYNC BPW
83D9:          CPY     L492C				; SYNC to ASYNC IF BPW L.T. or  E.Q 303 usec
83DD:          BHI     L83F9				;

83DF:          LDAA    L082A				;
83E2:          CMPA    L4974				; MIN PERIOD IN DBL FIRE
83E5:          BCS     L83F9				;

83E7:          BSET    L0051,#$01			; SET b0
83EA:          BSET    L003F,#$10			; SET b4

83ED:          LDD     L024E				; SYNC BPW
83F0:  L83F0   ASLD    						; x 2 MULT
83F1:          BCC     L83F6				;

83F3:          LDD     #$FFFF
83F6:  L83F6   STD     L024E				; SYNC BPW
83F9:  L83F9   BRA     L8472
		;----------------------------------------

			;
			; NOT CPI/PFI 
			;
83FB:  L83FB   LDX     #$400B				; AFR MD BYTE 1,  0000 0100	<---****
83FE:          BRCLR   0,X,#$04,L8406		; BR IF NOT b2, (1 = SYNC FUEL AT IDLE(TBI)) 

8402:          BRSET   L0050,#$80,L8469		; BR IF b7, IDLE 

8406:  L8406   LDX     #$492A				; ASYNC to SYNC IF BPW G.T. 500 usec

8409:          BRSET   L003E,#$10,L840F		; BR IF b4, ASYNC PULSE FLAG

840D:          INX     
840E:          INX     						; X To Sync to Async Min BPW

840F:  L840F   BSET    L003E,#$10			; SET b4, ASYNC PULSE FLAG

8412:          LDD     4,X					; MAP & RPM Limits
8414:          LDX     0,X					; 
8416:          CPX     L024E				; SYNC BPW
8419:          BCC     L8424				;

841B:          CMPA    L01C0				; GET CURRENT MAP VALUE
841E:          BCC     L8469				; BR IF MAP LT THRESH

8420:          CMPB    L0062 				; ENGINE RPM/25
8422:          BCC     L8469				; BR IF RPM LT THRESH
											;
8424:  L8424   CLRA    						;
8425:          CLRB    						;
8426:          STD     L3FCE				;

8429:          JSR     LF3ED				; Very short delay (RTS)


842C:          LDD     L3FC0				;
842F:          ASLD    						;
8430:          BCC     L8435				;

8432:          LDD     #$FFFF				;
8435:  L8435   XGDX    						;
8436:          LDD     L024E				; SYNC BPW
8439:          FDIV    						;

843A:          LDD     #$0050
843D:          XGDX    
843E:          IDIV    

843F:          PSHX    

8440:          LDX     #$0050
8443:          FDIV    
8444:          XGDX    

8445:          PULX    

8446:          ADDD    #$0080
8449:          STAA    L025E

844C:          XGDX    
844D:          BCC     L8452				;

844F:          ADDD    #$0001
8452:  L8452   STD     L025C

8455:          LDD     L025A
8458:          ADDD    L025D
845B:          STD     L025A

845E:          LDAA    L0259
8461:          ADCA    L025C
8464:          STAA    L0259

8467:          BRA     L8476
		;----------------------------------------

8469:  L8469   BCLR    L003E,#$10			; CLR b4, ASYNC PULSE FLAG

846C:          LDX     #$0000
846F:          STX     L0259


8472:  L8472   BRCLR   L003D,#$80,L84BC		; BR IF NOT b7, DELIVER ASYNC PULSE
 
8476:  L8476   LDD     L0259				; ASYNC PW
8479:          ADDD    L023A
847C:          CPD     L4932				; 11990 usec, MAX ASYNC BPW
8480:          BHI     L8493				; BR IF <11990 usec

8482:          CPD     L4934				; 1400 usec, MIN ASYNC
8486:          BLS     L84B6				; BR IF <1400 usec

8488:          LDX     #$0000
848B:          STX     L023A
848E:          STX     L0259

8491:          BRA     L84A9
		;----------------------------------------

8493:  L8493   LDD     L0259
8496:          SUBD    L4932				; 11990 usec, MAX ASYNC BPW
8499:          BCC     L84A3

849B:          ADDD    L023A
849E:          STD     L023A

84A1:          CLRA    
84A2:          CLRB    
84A3:  L84A3   STD     L0259

84A6:          LDD     L4932				; 11990 usec, MAX ASYNC BPW
84A9:  L84A9   SEI     
84AA:          JSR     L8548
84AD:          CLI
     
84AE:          BSET    L003D,#$80
84B1:          BCLR    L0046,#$01			; CLR b0, DELIVER ASYNC PULSE 

84B4:          BRA     L84BC
		;----------------------------------------

84B6:  L84B6   BSET    L0046,#$01			; SET b0, SYNC ACELL ENRICH
84B9:          BCLR    L003D,#$80			; CLR b7, DELIVER ASYNC PULSE 
											;
84BC:  L84BC   LDD     L024E				; SYNC BPW
84BF:          BRCLR   L003E,#$10,L84CB		; BR IF NOT b4, ASYNC PULSE FLAG

84C3:          STD     L024C				; SYNC BPW

84C6:          BCLR    L003F,#$80			; CLR b7

84C9:          BRA     L852C
		;----------------------------------------

84CB:  L84CB   BEQ     L84F5

84CD:          CPD     #$0100				;
84D1:          BCC     L84E6				;

84D3:          TBA     						;
84D4:          LDAB    #32					;

        ;---------------------------------------------
    	; LOW BPW OFFSET vs BPW
    	;
    	; SELECTED BY L400E BIT 4, (NOT USED THIS BMHM)
    	; TBL = (MSEC + L496F) * 65.536
        ;----------------------------------------------
84D6:          LDX     #$4979				;
84D9:          JSR     LF4BD				; 2D LU
											;
84DC:          TAB     						; Low BPW OFFSET
84DD:          CLRA    						; 0 MSB
84DE:          ADDD    L024E				; SYNC BPW
84E1:          SUBD    L4971				; 31 usec OFFSET BIAS FOR SMALL BPW
84E4:          BCS     L84EF				; BR IF LT 31 usec 

84E6:  L84E6   BCLR    L003F,#$80			; CLR b7, SHORT BPW FLAG

84E9:          CPD     L496D				; 488 usec MIN SYNC BPW
84ED:          BCC     L84F5				; BR IF 

84EF:  L84EF   BSET    L003F,#$80			; SET b7, SHORT BPW FLAG

		;
		; SET MIN BPW VALUE
		;
84F2:          LDD     L496F				; 488 usec SYNC BPW  USED IF BPW L.T. L496D
84F5:  L84F5   STD     L024C				; SYNC BPW
84F8:          BEQ     L8508				; BR IF SYNC BPW = Z 

84FA:          ADDB    L0256              	; BPW BIAS (Msec)
84FD:          ADCA    #$00					; ROUND
84FF:          CPD     #32767				; CK FOR MAX
8503:          BCS     L8508				; BR IF LT MAX 

8505:          LDD     #32767				; USE MAX FOR BPW
8508:  L8508   STD     L0250				; BPW


		;--------------------------------------------
		; AFR MD BYTE 1 0000 0100 
		;
		; b7 1 = DE-LATCH
		; b6 1 = MAT SENSOR
		; b5 1 = 180 DEG OFFSET 
		; b4 1 = ASDF CRANK
		;
		; b3 1 = ACCEL ENRICH LMT OPTION  
		; b2 1 = SYNC FUEL AT IDLE (TBI)
		; b1 1 = AIR MANAGE 
		; b0 1 = CPI/PFI MODE
		;--------------------------------------------
850B:          LDX     #$400B				; AFR MD BYTE 1,  0000 0100
850E:          BRSET   0,X,#$01,L8517		; BR IF b0, (1 = CPI/PFI MODE)

8512:          STD     L3FCE
8515:          BRA     L852C
		;----------------------------------------

  				;
  				; Deg DELAY FMR DRP TILL INJ FIRE
  				; CAL = DEG * (256/180)                                                          
8517:  L8517   LDAA    L4973				; DEG DLY FM DRP TILL INJECTION
851A:          LDX     #$005F				; LAST DPR PERIOD VAL, (MLT'CND)
851D:          JSR     LF550				; 8 x 16 Mult w/16b result rounded to upper 16b

8520:          ASLD    						; x2
8521:          BCS     L8526

8523:          ASLD    						; x2
8524:          BCC     L8529

8526:  L8526   LDD     #$FFFF
8529:  L8529   STD     L081F

852C:  L852C   BRSET   L0002,#$02,L8538		; MAJOR LOOP COUNTER

8530:          JSR     L863D
8533:          JSR     LD4A3

8536:          BRA     L8547
		;----------------------------------------

8538:  L8538   JSR     L8613
853B:          BRCLR   L0002,#$04,L8544		; MAJOR LOOP COUNTER

853F:          JSR     L891E
8542:          BRA     L8547
		;----------------------------------------

8544:  L8544   JSR     L8EB4
8547:  L8547   RTS     
		;----------------------------------------------

		;---------------------------------------------
		; b4 1 = USE L4979 WITH ASYNC FUEL DELIVERY
		;		 (LOW BPW OFSET vs BPW)
		;---------------------------------------------
8548:  L8548   LDX     #$400E				; AFR MD BYTE 4, 0000 0011
854B:          BRCLR   0,X,#$10,L856C		; BR IF	NOT b4, (USE L4979 WITH  
											; ASYNC FUEL DELIVERY

854F:          CPD     #$0100				;
8553:          BCC     L856C				; BR IF

8555:          PSHB    
8556:          PSHA    
8557:          TBA 
    
        ;---------------------------------------------
    	; LOW BPW OFSET vs BPW
    	;
    	; SELECTED BY L400E BIT 4, (NOT USED THIS BMHM)
    	; TBL = (MSEC + L496F) * 65.536
        ;---------------------------------------------
8558:          LDAB    #32
855A:          LDX     #$4979				; LOW BPW OFFSET vs BPW TBL
855D:          JSR     LF4BD				; 2d LK UP/W OFFSET

8560:          TAB     
8561:          PULX    
8562:          ABX     
8563:          XGDX    
8564:          SUBD    L4971				; .31 msec OFFSET BIAS FOR SMALL BPW,
8567:          BCC     L856C

8569:          LDD     #$0000
856C:  L856C   ADDB    L0256              	; BPW BIAS (Msec)
856F:          ADCA    #$00					; ROUND
8571:          STD     L3FF2

8574:          JSR     LF3ED				; Very short delay (RTS)

			;
			; CLR b2, I/O PORT D
			;
8577:          LDD     L3FFC          		; I/O D PORT ..
857A:          ANDA    #$FB					; 1111 1011
857C:          JSR     LF3ED				; Very short delay (RTS)
857F:          STD     L3FFC          		; I/O D PORT ..
											;
			;
			; SET b2, I/O PORT D
			;
8582:          ORAA    #$04					; SET b2
8584:          JSR     LF3ED				; Very short delay (RTS)
8587:          STD     L3FFC          		; I/O D PORT ..

858A:          RTS     
 		;------------------------------------------


 		;------------------------------------------
        ; CALC RPM
		;
 		;------------------------------------------
858B:  L858B   LDX     L3FC0              	; LAST REF PERIOD CNT'R
858E:          LDAA    L4141              	; 8, (8 CYL, 6 = 6 CYL)
8591:          LDAB    #32	              	;
8593:  L8593   MUL     		              	; 32 * 8 = 256 (OR 0)
8594:          TBA     					  	;
8595:          BEQ     L859E			  	;

8597:          PSHX    					  	;
8598:          TSX     					  	;
8599:          JSR     LF550              	; 8 x 16 MULT SUBROUTINE

859C:          PULX    
859D:          XGDX    
859E:  L859E   CPX     #$0000
85A1:          BHI     L85A6				; IF NON ZERO
              
85A3:          CLRA    						; A = 0
85A4:          BRA     L85B1				; EXIT VIA RET TO CALLER
		;----------------------------------------

85A6:  L85A6   LDD     #614               	; (30*(512/25), 65.5Khz CLK
85A9:          FDIV    
85AA:          XGDX    
85AB:          CMPA    #127					; CK limit
85AD:          BLS     L85B1				; EXIT W/RESULT
     
85AF:          LDAA    #127					; USE LIMIT

85B1:  L85B1   RTS     
    		;-------------------------------------------------

			**************************************************
			* CRANKING SUBROUTINE
			*  TYPE $31 PCM
			**************************************************
    		;-------------------------------------------------
    		; CRANK BPW vs COOL
    		;
    		; 
    		; TBL = MSEC * (65.536*256)/L4D89
    		;-------------------------------------------------
85B2:  L85B2   LDAA    L0006				; COOL VALUE
85B4:          LDX     #$4D9C
85B7:          JSR     LF4C1				; 2d LK UP

85BA:          LDX     #$4D9A				; 123.49, Scaler for tbl L4D9C (crank pw fuel)
                    						; CAL = SCALER * 65.536
85BD:          JSR     LF550				; 8 x 16 MULT SUBROUTINE 
											;
85C0:          PSHB    						;
85C1:          PSHA    						;
											;
85C2:          LDAA    L02CE				; DRP COUNTER
85C5:          CMPA    L4D95				; DRP'S MIN FOR USE OF L4DAD TRIM TBL TBL
85C8:          BLS     L85E1				; BR IF DRP's LT THRESH

85CA:          JSR     L858B				;

        ;---------------------------------------------
    	; CRANK FUEL MULT vs DRP'S 
    	; (HOT restart MODE)
    	; 
    	; TBL = MULT * 128
        ;---------------------------------------------
85CD:          LDX     #$4DAD				; CRANK FUEL MULT

		;
		; MODE 1, WD #3, FLAGWORD,
		;		  b4 1 = HOT restart
		;
85D0:      BRCLR   L0004,#$10,L85D7		; BR IF NOT b4, SET, 1 = HOT restart PROCEEDING 

        ;---------------------------------------------
    	; CRANK FUEL MULT Vs. RPM IF HOT restart
    	; 
    	; TBL = MULT * 256
        ;---------------------------------------------
85D4:          LDX     #$4DB6			; CRANK FUEL MULT
85D7:  L85D7   JSR     LF4C1			; 2d LK UP
85DA:          TSX     					;
										;
85DB:          JSR     LF550  			; MUL 8X16 Subroutine
										;
85DE:          PULX    					;
85DF:          PSHB    					;
85E0:          PSHA  					;
  
        ;---------------------------------------------
    	; CRANK FUEL MULT vs BARO
    	;
    	;
    	; TBL = MULT * 128
        ;---------------------------------------------
85E1:  L85E1   LDAA    L01CC			; BARO VALUE (Kpa)
85E4:          LDAB    #96				;
85E6:          LDX     #$4DBF			; CRANK FUEL MULT vs BARO
85E9:          JSR     LF4BD			;
85EC:          TSX     					;
85ED:          JSR     LF550			; MUL 8X16 Subroutine
85F0:          PULX    					;
85F1:          ASLD    					;
85F2:          BCC     L85F7			;

85F4:          LDD     #$FFFF			;
85F7:  L85F7   BCS     L8612			;
85F9:          PSHB    					;
85FA:          PSHA 					;
   
        ;---------------------------------------------
    	; CRANK FUEL MULT vs TPS
    	;
    	;
    	; TBL = MULT * 64
        ;---------------------------------------------
85FB:          LDAA    L01D9				; %TPS
85FE:          LDX     #$4DC3				; CRANK FUEL MULT
8601:          JSR     LF4B6				; 2d Lk Up

8604:          TSX     
8605:          JSR     LF550				; MUL 8X16 Subroutine

8608:          PULX    
8609:          ASLD    
860A:          BCS     L860F				; BR IF 

860C:          ASLD    
860D:          BCC     L8612				; BR IF 

860F:  L860F   LDD     #$FFFF

8612:  L8612   RTS     
 			;-----------------------------------------

            ;--------------------------------
            ; CK FOR LOW BATTERY
            ;
            ;--------------------------------
613:  L8613   LDAA    L00A7   				; BAT VOLTS, VDC/10
8615:          CMPA    #90					; 9 VDC
8617:          BCC     L8625				; BR IF Vbatt GT 9 VDC

8619:          CMPA    #40					; 4 VDC
861B:          BCC     L863C				; BR IF Vbatt GT 4 VDC

861D:          BSET    L0044,#$10			; SET b4, IGNITION OFF 
8620:          BCLR    L0050,#$01			; CLR b0

8623:          BRA     L863C
		;----------------------------------------

8625:  L8625   BRCLR   L0044,#$10,L862F		; BR IF NOT b4, IGNITION OFF 


                ;
                ; GET RPM FM COUNTER
                ;                        
8629:          LDX     L3FCA          		; 16 BIT RPM COUNTER
862C:          STX     L0205          		; 16 BIT RPM VAL

862F:  L862F   BCLR    L0044,#$10			; CLR b4, IGNITION OFF

8632:          LDAA    L400C				;  AFR MD BYTE 2, 1011 0111 <----***
8635:          BITA    #$01					; b0,  1 = SYNC MAP SENSOR READS
8637:          BEQ     L863C				; BR IF NOT b0

8639:          BSET    L0050,#$01

863C:  L863C   RTS     
        ***************************************************
		

  		***************************************************
        * IDLE & NON IDLE HYST PAIRS FOR o2 READY FLAG
		* Type $31 PCM
  		***************************************************
863D:  L863D   BRCLR   L004F,#$10,L8662		; BR IF NOT b4, RUN FUEL

8641:          LDX     #$48FF				; INDEX NON IDLE OPEN/CLOSED LP o2 QUAL'S
 											;
8644:          BRCLR   L0050,#$80,L864B		; BR IF NOT b7, IDLE 

8648:          LDX     #$4903				; INDEX IDLE OPEN/CLOSED LP o2 QUAL'S 
											;
864B:  L864B   BRSET   L003E,#$80,L865		; BR IF NOT b7,	CLOSED LOOP

864F:          INX     						; ADJ INDEX FOR IDLE o2 QUAL'S
8650:          INX   						;
  											;
8651:  L8651   LDAA    L01D5				; o2 VOLTS * 226 (A/D RESULT)
8654:          CMPA    0,X					; GET CLSD --> OPEN  o2 THRESH mvdc
8656:          BHI     L865C				;
 
8658:          CMPA    1,X					; GET OPEN --> CLSD  o2 THRESH mvdc
865A:          BCC     L8662				;
 
865C:  L865C   CLR     L0241				;

			;----------------------------
			; MODE 1, WD #3, FLAGWORD,
			;		  b0 1 = 
			;----------------------------
865F:          BSET    L0004,#$01			; SET b0, o2  o2 SENSOR READY
											;
8662:  L8662   LDAA    L0232				; AIR FLOW VALUE
8665:          LDAB    L4949              	; 0.75 AIR FLOW FACT  (Air Flow * 64)
8668:          MUL     		              	; APPLY MULT
8669:          ASLD    						; n x 2
866A:          BCS     L8673              	; IF OVERFLOW

866C:          ASLD    		              	; MULT x 2
866D:          BCS     L8673              	; IF OVERFLOW

866F:          CMPA    #$008              	; CK LMT VALUE0
8671:          BLS     L8675              	; IF L.T. 128       

8673:  L8673   LDAA    #128	              	; USE 128
8675:  L8675   STAA    L027B				; AIR FLOW (0-128)
											;
8678:          LDAB    #3					;
											;
867A:          BRCLR   L0050,#$80,L868B		; BR IF NOT b7, IDLE 


			;
			; LOAD  560 mvdc RICH o2 Thresh Rlp Tbl L4CF3 at IDLE
			;  		and
			;       477 mvdc LEAN o2 Thresh Rlp Tbl L4CFC at IDLE
			;  TO D REG, 
			;
867E:          LDD     L494A  				; RICH o2 Thresh Rlp Tbl's at IDLE
8681:          STD     L026D				; o2 R/L THRESH	(RICH 026Dh )
											;
8684:          LDAA    L494C			 	; 516 mvdc MEAN o2 Thresh Rlp Tbl L4C88 at IDLE
8687:          STAA    L026C				; o2 MEAN THRESH
											;
868A:          CLRB 						;
											
			;
			; JP TO HERE IF NOT IN IDLE
			;   
868B:  L868B   PSHB    
868C:          LDAA    #$09
868E:          MUL     

868F:          LDX     #$4CE1
8692:          ABX     
8693:          LDAA    L027B				; AIR FLOW
8696:          JSR     LF4C1				; 2d LK UP

8699:          LDX     #$026B
869C:          PULB    
869D:          TSTB    
869E:          BEQ     L86A6				;

86A0:          ABX     
86A1:          STAA    0,X
86A3:          DECB    
86A4:          BRA     L868B
		;----------------------------------------

86A6:  L86A6   BRCLR   L0070,#$04,L86AD	   	;

86AA:          LDAA    L4E58
86AD:  L86AD   STAA    L026B				;
											

86B0:          LDAB    L003E				; NWAF1, A/F MODE WD 1


			;
			; CK CURRENT o2 VOLTAGE Vs. MEAN TRESH
			; (NORM and FAST R/L)
			;											
86B2:          LDAA    L026C				; o2 MEAN THRESH
86B5:          ADDA    L4947				; 156 mvdc DIFF o2 WINDOW FAST R/L TEST
86B8:          BCS     L86BF				; BR IF OVERFLOW, (1.106 mvdc)

86BA:          CMPA    L01D5				; o2 VOLTS * 226 (A/D RESULT)
86BD:          BCS     L86D8				; BR IF o2 VDC GT o2 MEAN THRESH (FAST R/L) 

86BF:  L86BF   LDAA    L026C				;  o2 MEAN THRESH
86C2:          SUBA    L4947				; 156 mvdc DIFF o2 WINDOW FAST R/L TEST
86C5:          BCS     L86CC 				; BR IF o2 MEAN LT FAST R/L TEST

86C7:          CMPA    L01D5				; o2 VOLTS * 226 (A/D RESULT)
86CA:          BHI     L86D4				; BR IF CURRENT o2 IS > THRESH

86CC:  L86CC   LDAA    L01D5				; o2 VOLTS * 226 (A/D RESULT)
86CF:          CMPA    L01D4				;
86D2:          BHI     L86D8				; BR IF CURRENT o2 IS > THRESH 

86D4:  L86D4   ANDB    #$BF					; CLR b6,  b6 1 = RICH/ LEAN, 1 = RICH
86D6:          BRA     L86DA				
		;----------------------------------------

86D8:  L86D8   ORAB    #$40					; b6 1 = RICH/LEAN, 1 = RICH
86DA:  L86DA   CMPB    L003E				; FLAG WD
86DC:          BEQ     L86E7				; BR IF NOT R FLAG

86DE:          INC     L0275				; ALDL RICH LEAN CHAGE COUNTER (X Counts)
86E1:          BSET    L0043,#$10			; SET b4
86E4:          CLRA    

86E5:          BRA     L86ED
		;----------------------------------------

86E7:  L86E7   LDAA    L027C
86EA:          INCA    						; INCR CNT'R
86EB:          BEQ     L86F0				; BR IF NZ

86ED:  L86ED   STAA    L027C				; SAVE UPDATED COUNT

86F0:  L86F0   STAB    L003E				; NWAF1, A/F MODE WD 1


86F2:          BRCLR   L003B,#$10,L8706		; BR IF NOT b4

86F6:          LDX     #$0391
86F9:          BRCLR   0,X,#$01,L8706		; BR IF NOT b0

86FD:          BRCLR   1,X,#$01,L8703		; BR IF NOT b0, EXIT

8701:          BRA     L8779
		;----------------------------------------

8703:  L8703   JMP     L8790				; TO o2 R/L CHECK
		;----------------------------------------------


		;----------------------------------------------
8706:  L8706   BRSET   L003E,#$80,L870E		; BR IF NOT b7,	CLOSED LOOP
 
870A:          BRCLR   L0052,#$80,L877C		;				

870E:  L870E   BRSET   L0046,#$08,L8776		; BR IF b3,	 DECEL FUEL C/O
											; 
8712:          BRSET   L003D,#$20,L8776		; BR IF b5, PWR ENR IS ACTIVE

8716:          BRSET   L0052,#$40,L8776		;


871A:          LDX     #$400C				; AFR MD BYTE 2	 1011 0111 <---***
871D:          BRCLR   0,X,#$20,L872A		; BR IF NOT b5, INT RESET

8721:          BRCLR   L006E,#$08,L872A		;  ACELL ENR 1st TIME 

8725:          BCLR    L006E,#$08			; ACELL ENR 1st TIME 
											  
8728:          BRA     L8779
		;----------------------------------------

			;-----------------------------------------
			; AFR MD BYTE 2	 1011 0111 
			;
			; b7 1 = CAN PURGE
			; b6 1 = CONDITIONAL INT R/S ON BLM CELL CHNAGE
			; b5 1 = INT R/S IF ACELL ENRICH
			; b4 1 = INT RESET IN BLM CELL CHANGE
			;
			; b3 1 = ASDF 
			; b2 1 = CRANK FUEL ALL INJ'S EACH DRP
			; b1 1 = ERR 44/45 BLM LMT
			; b0 1 = SYNC MAP SENSOR READS  
			;-----------------------------------------                         
872A:  L872A   LDX     #$400C
872D:          BRSET   0,X,#$10,L8735
8731:          BRCLR   0,X,#$40,L8739

8735:  L8735   BRSET   L003D,#$04,L8779		; BR IF b2, BLK LRN ADDR CHANGE 1 = CHANGED
 
8739:  L8739   BRCLR   L004F,#$20,L8742		; BR IF NOT b5, VE INT RESET

873D:          BCLR    L004F,#$20			; CLR b5, VE INT RESET
											; 
8740:          BRA     L8779
		;----------------------------------------

8742:  L8742   BRCLR   L003D,#$10,L8751		; BR IF NOT b4, DECEL ENLEAN IS ACTIVE 

8746:          BRSET   L003E,#$40,L8790		; BR IF b6, RICH/ LEAN, 1 = RICH 

874A:          LDAA    L020F				; INTEGRATOR COUNTS
874D:          BPL     L8790				; TO o2 R/L CHECK

874F:          BRA     L8779
		;----------------------------------------

        ****************************
        * CLS LP LEAN DECEL CAL
        *  BMHM, 7.4L V8
        ****************************
8751:  L8751   LDAB    L01C0				; GET CURRENT MAP VALUE
8754:          CMPB    L490B				; 20 Kpa CLSD LP LEAN DECEL MAP THRESH
8757:          BHI     L8790				; TO o2 R/L CHECK

8759:          LDAB    L0062  				; ENGINE RPM/25
875B:          CMPB    L490C				;  50 RPM, CLSD LP LEAN DECEL LO RPM THRESH
875E:          BLS     L8790				; TO o2 R/L CHECK

8760:          CMPB    L490D				; 800 RPM, CLSD LP LEAN DECEL HI RPM THRESH
8763:          BHI     L8790				; TO o2 R/L CHECK

8765:          LDAB    L0284				; MPH/1
8768:          CMPB    L490E				; 15 MPH, CLSD LP LEAN DECEL LO Vss THRESH
876B:          BCS     L8790				; BR IF Vss LT THRESH, (TO o2 R/L CHECK)

876D:          BRSET   L003E,#$40,L8790		; BR IF b6, RICH/ LEAN, 1 = RICH
											;		   (TO o2 R/L CHECK)

8771:          LDAA    L020F				; INTEGRATOR COUNTS
8774:          BPL     L8790				; TO o2 R/L CHECK

8776:  L8776   BSET    L0071,#$04			; SET b2
8779:  L8779   BSET    L006E,#$01			; SET b0, EGR DIAG INT RESET

877C:  L877C   LDAA    #128					; STOCH INT
877E:          STAA    L020F				; INTEGRATOR COUNTS

8781:          LDAA    #102					; 443 mvdc
8783:          STAA    L01D2				; INIT. o2 VOLTAGE, 2

			;
			; ZERO OUT INT DELAY & PROP COUNT'S
			;
8786:          CLRA    						; ZERO OUT ... 
8787:          STAA    L025F 				; INTEGRATOR DELAY VAL
878A:          STAA    L027A 				; PROPOTIONAL COUNTS (Fuel corr)

878D:          JMP     L8911
		;----------------------------------------------


		;----------------------------------------------
		; R/L LEAN CHECK Vs o2 V2
		;
		;----------------------------------------------
8790:  L8790   LDAA    L01D2				; o2 VOLTAGE, 2
8793:          CMPA    L026D				; o2 Rich THRESH	
8796:          BHI     L87A6				; BR IF o2 V2 GT (Rich) THRESH

8798:          SUBA    L026E				; o2 Lean THRESH
879B:          BCS     L87A0				; BR IF o2 V2 LT (Lean) THRESH
879D:          CLRA    

879E:          BRA     L87BE
		;----------------------------------------

		;----------------------------------------------
		;
		;
		;----------------------------------------------
87A0:  L87A0   NEGA    						;
											;
87A1:          BCLR    L0046,#$02			; CLR b1, SLOW RICH/LEAN, 1 = RICH 
											;
87A4:          BRA     L87B0
		;----------------------------------------

    	;-----------------------------------------------
    	; PROPORTIONAL COUNTS vs SLOW o2 ERROR
    	; (Sel num of counts to correct fuel delivery)
    	; TBL = COUNTS * 1
    	;-----------------------------------------------
87A6:  L87A6   SUBA    L026D				; o2 R/L THRESH	(HI & LOW)
87A9:          LDAB    L4955				; 0.906 FACTOR APPLIED TO ERR FOR RICH COND
87AC:          MUL     

87B0:  L87B0   BRCLR   L0050,#$80,L87B8		; BR IF NOT b7, IDLE

87B4:          LDAB    L4956				; 0.750 MULT APPLIED TO ERR AT IDLE
87B7:          MUL     						; APPLY MULT TO o2 ERR
87B8:  L87B8   CMPA    #96					; MAX VAL FOR SLOW o2 BIN
87BA:          BLS     L87BE				; BR IF LT 96

87BC:          LDAA    #96					; LIMIT TO MAX VAL FOR SLOW o2 BIN
87BE:  L87BE   STAA    L0280			    ; SLOW o2 ERROR
87C1:          ASLA    						; N x 2
87C2:          LDX     #$4D0E				; PROP COUNTS vs SLOW o2 ERROR Table				
87C5:          JSR     LF4C1				; 2d LK UP
											;
87C8:          STAA    L027A				; PROPOTIONAL COUNTS (Fuel corr)
											;
87CB:          BRCLR   L0050,#$80,L8813		; BR IF NOT b7, IDLE

87CF:          LDAA    L494D				; 140 msec PROP DURATION OFF SET AT IDLE
                    						;  (INSTEAD OF TBL L4...) 

				;
				; INDEX 
				; 	1. R or L PROPORTIONAL CNT'S (2 ea)
				; 	2. INTEGRATOR DELAY, (2 ea)
				;    
				;   
87D2:          PSHA    						; 
87D3:          LDX     #$494F				; INDEX R or L PROPORTIONAL MULT'S (3 ea)
87D6:          LDY     #$4952				; INDEX INTEGRATOR DELAY, (2 ea)

87DA:          BRSET   L003E,#$40,L87E6		; BR IF b6, RICH
											;
87DE:          SEI     						;
											;
87DF:          LDAA    L003F				;
87E1:          EORA    #$05					; TOGGLE b0 & b2
87E3:          STAA    L003F				;
											;
87E5:          CLI     						; RESTORE INTERUPTS
87E6:  L87E6   BRSET   L003F,#$03,L87F8		; BR IF b0 & b1
											;
87EA:          BRSET   L003F,#$0C,L87F8		; BR IF b2 & b3	
											;
87EE:          LDAA    1,Y					; GET INTEGRATOR DELAY, (msec's)
87F1:          STAA    L0262				; INTEGRATOR DELAY OFFSET
											;
87F4:          INX     						; INCR PROPORTIONAL MULT INDEX     
87F5:          INX     						;
											;
87F6:          BRA     L8803				;
		;----------------------------------------

87F8:  L87F8   LDAA    0,Y
87FB:          STAA    L0262				; INTEGRATOR DELAY OFFSET

87FE:          BRSET   L003E,#$40,L8803		; BR IF b6, RICH/LEAN, 1 = RICH

8802:          INX     						; INCR PROP GAIN SELECT INDEX
8803:  L8803   LDAA    0,X					; GET INTEGRATOR DELAY

8805:          LDAB    L027A				; PROPOTIONAL COUNTS (FUEL CORR)
8808:          MUL     						; APPLY PROPOTIONAL MULT 
8809:          ASLD    						; n x 2
880A:          BCS     L880F				; BR IF OVERFLOW
											;
880C:          ASLD    						; n x 2    
880D:          BCC     L883C				; BR IF NO OVERFLOW
											;
880F:  L880F   LDAA    #255					; USE MAX VALUE
											
8811:          BRA     L883C
		;----------------------------------------

        ;---------------------------------------------
    	; PROPORTIONAL DURATION OFFSET vs SLOW o2 ERROR
    	;
    	; TBL = SEC'S * 40
        ;---------------------------------------------
8813:  L8813   LDAA    L027B				; AIR FLOW
8816:          LDX     #$4D28				; PROPORTIONAL DURATION OFFSET TBL
8819:          JSR     LF4C1				; 2d LK UP
881C:          PSHA    

    	;----------------------------------------------
    	; PROPORTIONAL FLOW GAIN MULT vs MAP & RPM
    	;
    	; TBL = FACTOR * 128
    	;----------------------------------------------
881D:          LDAA    L0062				; ENGINE RPM/25
881F:          CMPA    #144					; 3600 RPM, (MAX FOR TBL)
8821:          BLS     L8825				; BR IF LT 3600 RPM
											;
8823:          LDAA    #144					; FORCE 3600 RPM
8825:  L8825   LDAB    L01C0				; GET CURRENT MAP VALUE
8828:          LSRB    						; MAP/2 FOR LK UP, (9 lines)


8829:          LDX     #$4D31				; PROPORTIONAL FLOW GAIN MULT Table
882C:          JSR     LF4DE				; 3d LK UP

882F:          LDAB    L027A				; PROPOTIONAL COUNTS (FUEL CORR)
8832:          MUL     						; Apply Mult.
8833:          ADDD    #64					; (scaler)
8836:          ASLD    						; MULT n x 2
8837:          BCC     L883C				; BR IF NO OVERFLOW
											;
8839:          LDD     #$FFFF				; MAX VALUE
883C:  L883C   STAA    L027A				; PROPORTIONAL VALUE
		;----------------------------------------------


    	;----------------------------------------------
    	; PROPORTIONAL COUNTS vs SLOW o2 ERROR
    	; (Select num counts to correct fuel delivery)
    	;
    	; TBL = COUNTS
    	;----------------------------------------------
883F:          LDAA    L0280			    ; SLOW o2 ERROR  
8842:          ASLA    						; 2x o2 ERR
8843:          LDX     #$4D1B				; PROPORTIONAL COUNTS TBL
8846:          JSR     LF4C1				; 2d LK UP
											;
8849:          PULB    						;
884A:          ABA     						; ADD PROP CORRECTION
884B:          BCC     L884F				; BR IF NO OVERFLOW
											;
884D:          LDAA    #255					; USE MAX VALUE
884F:  L884F   PSHA    						; SAV CORR TO STX


    	;------------------------------------------
    	; INTEGRATOR DELAY MULT vs SLOW FILT o2
    	;
    	; TBL = MULT * 256 
    	;------------------------------------------
8850:          LDAA    L0280			    ; SLOW o2 ERROR
8853:          ASLA    						; n x 2 (for lk up)
8854:          LDX     #$4D85				; INTEGRATOR DELAY MULT
8857:          JSR     LF4C1				; 2d LK UP

885A:          LDAB    L026B				; INTEGRATOR DELAY
885D:          MUL     						; APPLY DELAY MULT
											;
885E:          BRCLR   L0050,#$80,L8869		; BR IF NOT b7, IDLE 
											;
8862:          ADDA    L0262				; INTEGRATOR DELAY OFFSET
8865:          BCC     L8869				; IF NO OVERFLOW
											; 
8867:          LDAA    #255					; MAX VALUE
8869:  L8869   STAA    L026B				; INTEGRATOR DELAY
886C:          STAA    L0281				;
											;
886F:          LDAA    L0046				; MODE 1, WD# 26
8871:          ANDA    #$02					; b1,  SLOW RICH/LEAN, 1 = RICH
                                                             
8873:          LDAB    L003E				; A/F MD WD #1	
8875:          ANDB    #$40					; CLR b6,  RICH/LEAN, 1 = RICH
8877:          ABA     						;

8878:          PULB    						;
8879:          BEQ     L887F				;
											;
887B:          CMPA    #66					;
887D:          BNE     L88CD				;
											;
887F:  L887F   LDAA    L0280				; SLOW o2 ERROR
8882:          ASLA    						; 2 x SLOW o2
8883:          CMPA    L4948				; 8 COUNTS SLO o2 ERR MIN TO DO INTEGRATOR
8886:          BHI     L888D				; BR IF SLO o2 ....
											;
8888:          CLR     L025F				; INTEGRATOR DELAY VAL

888B:          BRA     L88CD
		;----------------------------------------

		;
		; CK INT DELAY TIMER
		;
888D:  L888D   LDAA    L025F				; INTEGRATOR DELAY VAL
8890:          CMPA    L026B				; INTEGRATOR DELAY
8893:          BCS     L8898				; BR IF INT DELAY LT THRESH
											;
8895:          CLRA    

8896:          BRA     L8899
		;----------------------------------------

		;
		; CK INT UPDATE DELAY TIMER
		: If time out, update int value
		;
8898:  L8898   INCA    						; INCR INTEGRATOR DELAY VAL
8899:  L8899   STAA    L025F				; INTEGRATOR DELAY VAL
889C:          BNE     L88CD				; BR IF INT DELAY IS NZ
											;
889E:          LDAA    L020F				; GET INTEGRATOR COUNTS
88A1:          BRSET   L0046,#$02,L88B5	    ; BR IF b1, SLOW RICH/LEAN, 1 = RICH
											;
88A5:          CMPA    L4911				; CLS LP MAX INTEGRATOR
                   							; (Lean mixture, max value)
88A8:          BEQ     L88CA				;
											;
88AA:          BRCLR   L0052,#$80,L88B2		; BR IF NOT b7, 
											;
88AE:          CMPA    #128					; CK IS INT IS NEUTRAL (STOCH)
88B0:          BCC     L88CA				; BR IF INT IS GT 128 
											;
88B2:  L88B2   INCA    						; INCR INT VAL (Ask FOR Enrich)
											; 
88B3:          BRA     L88CA
		;----------------------------------------

88B5:  L88B5   LDX     #$400B				; AFR MD BYTE 1,  0000 0100
88B8:          BRCLR   0,X,#$08,L88C0		; BR IF NOT b3 (1 = ACCEL ENRICH LMT OPT)
											;
88BC:          BRSET   L0044,#$02,L88CD		; BR IF b1, ACELL ENR CLAMP ACTIVE
											;

			;
			; APPLY ACCEL ENRICH LMT 
			; 
88C0:  L88C0   CMPA    L4910				; 40, CLS LP MIN INTEGRATOR
88C3:          BEQ     L88CA				; BR IF ...
											;
88C5:          BRSET   L003F,#$80,L88CA	   	; BR IF b7, 
											;
88C9:          DECA    						; dec int value
88CA:  L88CA   STAA    L020F				; INTEGRATOR COUNTS

			;
			; APPLY ACELL ENR CLAMP  
			; 
88CD:  L88CD   LDAA    L027C				; CNT'R
88D0:          CBA     
88D1:          BLS     L88E2				;
											;

88D3:          ADDB    L494E				; 100 msec SEC'S PC CNT USE TRIGGER OFF SET
88D6:          BCC     L88DA				; BR IF NO OVERFLOW
											;
88D8:          LDAB    #255					; USE MAX VAL

88DA:  L88DA   CBA     						; COMP B to A
88DB:          BCC     L88E2				;
											;
88DD:          CLR     L027A				; PROPORTIONAL VALUE

88E0:          BRA     L88E9
		;----------------------------------------

88E2:  L88E2   BRCLR   L0052,#$80,L88E9		; BR IF NOT b7, 
											;
88E6:          CLR     L027A				; PROPORTIONAL VALUE

88E9:  L88E9   LDAA    L027A				; PROPORTIONAL VALUE
											;
88EC:          BRCLR   L003E,#$40,L8911		; BR IF b6, RICH/LEAN, 1 = RICH


		;--------------------------------------------
		; AFR MD BYTE 1 0000 0100 
		;
		; b7 1 = DE-LATCH
		; b6 1 = MAT SENSOR
		; b5 1 = 180 DEG OFFSET 
		; b4 1 = ASDF CRANK
		;
		; b3 1 = ACCEL ENRICH LMT OPTION  
		; b2 1 = SYNC FUEL AT IDLE (TBI)
		; b1 1 = AIR MANAGE 
		; b0 1 = CPI/PFI MODE
		;--------------------------------------------
88F0:          LDX     #$400B				; AFR MD BYTE 1,  0000 0100
88F3:          BRCLR   0,X,#$08,L8906		; BR IF NOT, (b3 1 = ACCEL ENRICH LMT OPT)

88F7:          BRCLR   L0044,#$02,L8906		; BR IF NOT b1, ACELL ENR CLAMP ACTIVE
											;
88FB:          LDAA    L4912				; PROP CNT'L LIMIT IF ACELL LMT IN EFFECT
88FE:          CMPA    L027A				; PROPORTIONAL VALUE
8901:          BCC     L8906				; BR IF 
											;
8903:          STAA    L027A				; PROPORTIONAL VALUE

8906:  L8906   LDAA    L020F				; INTEGRATOR COUNTS
8909:          SUBA    L027A				; PROPORTIONAL VALUE
890C:          BCC     L8918				; BR IF INT GT PROP VALUE
											;
890E:          CLRA   
 
890F:          BRA     L8918
		;----------------------------------------

8911:  L8911   ADDA    L020F				; INTEGRATOR COUNTS
8914:          BCC     L8918				; BR IF NO OVERFLOW
											;
8916:          LDAA    #255					; USE MAX VALUE

8918:  L8918   SUBA    #128					; NEUT INT (STOCH)
891A:          STAA    L026F

891D:          RTS     
        ;---------------------------------------------


891E:  L891E   LDAA    L48E7				; 14,7, STOCH AFR

        ;-----------------------------
   		; NWAF1, A/F MODE WD 1
		;
        ; b7 1 = CLSD LOOP	
        ; b5 1 = CLSD LP 
        ;-----------------------------
8921:          LDAB    L003E				; 
8923:          BITB    #$A0					; 1010 0000, 
8925:          BEQ     L8938				; to OPEN LOOP AFR vs VAC
											;
8927:          STAA    L024A				; AFR

        ;---------------------------------------------
		; AFR MD BYTE 3, 1000 0010
		;
		; b0 1 = USE TBL L4BBA FOR CLS LP AFR
		;        IF COOL L.T. L48D1
        ;---------------------------------------------
892A:          LDX     #$400D				; AFR MD BYTE 3, 1000 0010
892D:          BRCLR   0,X,#$01,L896D		; BR IF NOT  b0,USE TBL L4BBA FOR CLS LP AFR
											;
8931:          LDAB    L0006				; CURRENT COOL VALUE
8933:          CMPB    L48D1				; IF COOL L.T. -40 c, USE TBL L4BBA
8936:          BHI     L8952				; BR IF COOL  GT THRESH
											;


        ;---------------------------------------------
    	; OPEN LOOP AFR vs VAC
    	;
    	; TABLE = AFR * 10
        ;---------------------------------------------
8938:  L8938   LDX     #$4BBA				; OPN LOOP AFR TBL.
893B:          LDAB    L01C9				; Kpa VACUUM
893E:          LDAA    0,X					; GET LOAD SELECTOR
8940:          BEQ     L8945				; BR IF 
											;
8942:          LDAB    L01C0				; GET CURRENT MAP VALUE

8945:  L8945   INX     						;
8946:          LSRB    						; N/2

8947:          LDAA    L0006				; COOL VALUE
8949:          CMPA    #192					; 104c
894B:          BLS     L894F				;
											;
894D:          LDAA    #192					; 104c
894F:  L894F   JSR     LF4DE				; 3d LK UP
											;
8952:  L8952   SUBA    L02C8				; 
8955:          BCC     L8958				;
											;
8957:          CLRA    						;
8958:  L8958   BRCLR   L0050,#$80,L896F		; BR IF NOT b7, IDLE
											;
895C:          CMPA    L0272				; AFR
895F:          BLS     L8964				; BR IF AFR ...
											;
8961:          LDAA    L0272				; AFR

8964:  L8964   LDAB    #60					;
8966:          STAB    L0266				; AFR COUNTER
8969:          CLRB    						;

896A:          STD     L0264				; FILT AFR

896D:  L896D   BRA     L8998
		;----------------------------------------

			;
			; 
			; FILTER ????
			;
896F:  L896F   LDAB    L0266				; AFR COUNTER
8972:          BEQ     L8988				; BR IF COUNT EQ Z
											;
8974:          DECB    						;
8975:          STAB    L0266				; DECR AFR COUNTER

8978:          CMPA    L0264				; GET OLD FILT AFR
897B:          BLS     L8988				;
											;
897D:          LDX     L0264				; GET OLD FILT AFR
8980:          LDAB    L48EC  				; 50% FILT, CONST FOR AFR FILTERING 
											; 	FOR IDLE TO LEANER OFF IDLE XISITION
8983:          JSR     LF459				; LAG FILT

8986:          BRA     L898E
		;----------------------------------------

8988:  L8988   CLRB    
8989:          STD     L0264				; SAVE NEW FILT AFR

898C:          BRA     L8998
		;----------------------------------------

898E:  L898E   STD     L0264				; SAVE FILTERED AFR

8991:          ASLB    
8992:          ADCA    #$00					; ROUND
8994:          BCC     L8998				;
											;
8996:          LDAA    #$FF					; MAX VALUE 
8998:  L8998   STAA    L024A				; AFR
											;
899B:          LDAA    L0284				; Vss/1
899E:          CMPA    L48D9				; 2 MPH, MAX FOR IDLE SPK TBL 
89A1:          BHI     L8A0B				; BR IF Vss ... THRESH
											;
89A3:          LDAA    L01D9				; %TPS
89A6:          CMPA    L48DA				; 2.3% TPS MAX IDLE FUEL TABLE
89A9:          BHI     L8A0B				; BR IF %TPS ...
											;
89AB:          BSET    L0050,#$80			; SET b7, IDLE
											;
89AE:          LDAA    L0272				; AFR 
89B1:          CMPA    L024A				; AFR
89B4:          BHI     L8A19				;

89B6:          LDAB    L0006				; COOL VALUE
89B8:          CMPB    L48E2				; 50c COOL, OPEN LP IDLE TEMP THRES
89BB:          BLS     L8A06				; BR IF COOL LT THRESH
											;
89BD:          LDAB    L48DE				; IF IDLE TIME => 255 sec, SET IDLE FOR AIR MAN'T
89C0:          BEQ     L89E6				; BR IF TIME = Z
											;


		;--------------------------------------------
		; AFR MD BYTE 1 0000 0100 
		;
		; b7 1 = DE-LATCH
		; b6 1 = MAT SENSOR
		; b5 1 = 180 DEG OFFSET 
		; b4 1 = ASDF CRANK
		;
		; b3 1 = ACCEL ENRICH LMT OPTION  
		; b2 1 = SYNC FUEL AT IDLE (TBI)
		; b1 1 = AIR MANAGE 
		; b0 1 = CPI/PFI MODE
		;--------------------------------------------
89C2:          LDX     #$400B				; AFR MD BYTE 1,  0000 0100
89C5:          BRSET   0,X,#$02,L89CD		; BR IF b1, (1 = AIR MANAGE)
											;
89C9:          BRSET   L0041,#$20,L8A19		; BR IF b5, PARK/NEUTRAL
											;
89CD:  L89CD   BRCLR   L0050,#$02,L89DE		;
											;
89D1:          LDAB    L0271				; IDLE TIME
89D4:          CMPB    L48DF				; __SEC'S AFTER OPN LP AIR MANAGEMENT SET
											;  USE OPN LP IDLE AFR
											;
89D7:          BLS     L89F6				;
											;
89D9:          LDAA    L0272				; AFR
89DC:          BRA     L8A22
		;----------------------------------------

89DE:  L89DE   LDAB    L48DE				; IF IDLE TIME => 255 SEC, SET IDLE FOR AIR MAN'T
89E1:          CMPB    L0271				; IDLE TIME
89E4:          BCC     L89F6				; BR IF TIME LT THRESH
											;
89E6:  L89E6   LDAB    #128					; MID POINT VALUE

89E8:          LDAA    L020F				; INTEGRATOR COUNTS
89EB:          CMPA    #128					; MID POINT VALUE
89ED:          BCC     L89F0				; BR IF INT VALUE IS LT 128
											;
89EF:          NEGA    						; INVERT INTEGRATOR COUNTS
89F0:  L89F0   ABA     						; ADD 
89F1:          CMPA    L48F8				; 4, CLSD LP IDLE INT WINDOW
89F4:          BLS     L8A01				;
											;
89F6:  L89F6   LDAB    L0002				; MAJOR LOOP COUNTER
89F8:          CMPB    #39
89FA:          BNE     L8A1F
											;
89FC:          INC     L0271				; IDLE TIME

89FF:          BRA     L8A1F
		;----------------------------------------

8A01:  L8A01   BSET    L0050,#$02

8A04:          BRA     L8A1C
		;----------------------------------------

8A06:  L8A06   BSET    L0050,#$02

8A09:          BRA     L8A22
		;----------------------------------------

8A0B:  L8A0B   LDD     L00FD				; RUN TIMER
8A0D:          CPD     L48E0				; 1 SEC RUN TIME, 1ST IDLE TO OFF IDLE THRESH
8A11:          BCS     L8A16				; BR IF TIMER LT 1 SEC
											;
8A13:          BSET    L003F,#$40			; CLR b6
8A16:  L8A16   BCLR    L0050,#$80			; CLR b7, IDLE
8A19:  L8A19   BCLR    L0050,#$02			; CLR b1

8A1C:  L8A1C   CLR     L0271				; IDLE TIME

8A1F:  L8A1F   LDAA    L024A				; AFR

8A22:  L8A22   BRSET   L003E,#$80,L8A5C		; BR IF NOT b7,	CLOSED LOOP
											;
8A26:          BRCLR   L0004,#$10,L8A30		; BR IF NOT b4, HOT restart 
											;
8A2A:          SUBA    L495C				; 1.5:1 AFR OPN LP AFR RICH 
											; BIAS FOR A HOT restart BIAS
8A2D:          BCC     L8A30				; BR IF AFR OK
											;
8A2F:          CLRA    						; ZERO AFR VALUE
8A30:  L8A30   LDAB    L0006				; COOLANT 

8A32:          CMPB    L48E4				; -40c  COOL, OPEN LP RICH IDLE PK/NEUT
											;  OR DRIVE, LO THRESH
8A35:          BLS     L8A5C				;   											
											;
8A37:          CMPB    L48E5				;  29.8c COOL, OPEN LP RICH IDLE PK/NEUT
											;  OR DRIVE, HI THRESH
8A3A:          BCC     L8A5C				;
											;
8A3C:          BRSET   L0041,#$20,L8A56		; BR IF b5, PARK/NEUTRAL
											;
8A40:          LDAB    L082C				;
8A43:          CMPB    L48E6				; 8 SEC'S MAX TIME FOR RICH IDLE IF IN DRIVE
8A46:          BHI     L8A5C				;
											;
8A48:          INCB    						;
8A49:          BEQ     L8A4E				;
											;
8A4B:          STAB    L082C				; AFR


8A4E:  L8A4E   SUBA    L48EA				; 2.0:1 AFR RICH BIAS FOR OPN LP DRIVES
8A51:          BCC     L8A5C				;
											;
8A53:          CLRA    						;

8A54:          BRA     L8A5C
		;----------------------------------------

8A56:  L8A56   SUBA    L48EB				; 0:1 AFR RICH BIAS FOR OPN LP PK/NEUT
8A59:          BCC     L8A5C				;
											;
8A5B:          CLRA    						;
8A5C:  L8A5C   LDAB    L4913				; 16.0 MAX AFR
											;
8A5F:          BRCLR   L0072,#$40,L8A66		;
											;
8A63:          LDAB    L4E7B				; 16.4 MAX AFR IF ERROR
8A66:  L8A66   CBA     						;
8A67:          BLS     L8A6A				;
											;
8A69:          TBA     						;

8A6A:  L8A6A   LDAB    L0268				; DRP'S RUN PRIOR TO CRANK 
8A6D:          CMPB    L495F				; 0 DRP'S RUN PRIOR TO CRANK TO RUN XISITION AFR
8A70:          BCS     L8A88				; BR IF DRP'S LT THRESH
											;
8A72:          LDAB    L0006				; COOL TEMP
8A74:          CMPB    L4961				; -40 C, CRANK TO RUN AFR DECAY COOL ADD OR SUB
8A77:          BHI     L8A81				;
											;
8A79:          SUBA    L02C9				; STARTUP AFR (SUB'R)
8A7C:          BCC     L8A88				; BR IF AFR VALU IS OG
											;
8A7E:          CLRA    						; ZERO AFR VALUE

8A7F:          BRA     L8A88				
		;----------------------------------------

8A81:  L8A81   ADDA    L02C9				; STARTUP AFR (SUB'R)
8A84:          BCC     L8A88				;
											;
8A86:          LDAA    #255					; FORCE MAX AFR
8A88:  L8A88   STAA    L024A				; AFR
											;
8A8B:          BRSET   L004F,#$10,L8A92		; BR IF b4, RUN FUEL
											;
8A8F:          JMP     L8C6D				;



8A92:  L8A92   LDAA    L0284				; MPH/1
8A95:          CMPA    L4921				; IF L.T. 0 MPH &  TPS L.T. 
											; L4920 THEN BY PASS PE DLY
8A98:          BCC     L8AAA				;
											;
8A9A:          LDAA    L01D9				; %TPS
8A9D:          CMPA    L4922				; 0% TPS PWR ENR THRESH
8AA0:          BHI     L8AAA				;
											;
8AA2:          BSET    L003D,#$01			; SET b0, PWR ENR DELAY TIME COMPLETE 
8AA5:          CLR     L0263				; ZERO PWR ENRICH DELAY TIMER

8AA8:          BRA     L8AB9
		;----------------------------------------

8AAA:  L8AAA   LDAA    L0263				; TIMER 
8AAD:          CMPA    L4923				; 0 SEC AFTER
8AB0:          BCC     L8AB9				; BR IF TIMER GT THRESH
											;
8AB2:          INCA    						; INCR PWR ENRICH DELAY TIMER
8AB3:          STAA    L0263				; PWR ENRICH DELAY TIMER

8AB6:          BSET    L003D,#$01			; CLR b0, PWR ENR DELAY TIME COMPLETE


    		***************************************************
    		* HIGH TPS% WOT ENTRY THRESH vs RPM
    		*
    		* ESTABLISH A HI TPS THRES FOR FAST WOT ENTRY
    		*
    		* TBL = %TPS * 2.56
    		***************************************************
8AB9:  L8AB9   LDAB    #32
8ABB:          LDX     #$4C5A				; HIGH TPS% WOT ENTRY THRESH

8ABE:          LDAA    L0062				; ENGINE RPM/25
8AC0:          JSR     LF49A

8AC3:          STAA    L01E0				; SAVE HIGH TPS WOT TPS THRESH


    		***************************************************
    		* HIGH TPS% WOT ENTRY 
    		*
    		* IF TPS G.T. L4C5A TBL WOT DELAY TIME IS DECRESED
    		* AT THIS FASTER RATE, TBL VAL OF 5 WILL DECREMENT
    		* TIMER VAL AT L4908 BY FACTOR OF 5
    		*
    		* TBL = SEC'S
    		***************************************************
8AC6:          LDX     #$4C7F				; HIGH TPS% WOT ENTRY TBL
8AC9:          LDAA    L0062				; ENGINE RPM/25
8ACB:          JSR     LF49A
8ACE:          STAA    L01E1

    		*************************************
    		* TPS% THRESH FOR WOT ENABLE
    		*
    		* 
    		* TBL = %TPS * 2.56
    		*************************************
8AD1:          LDX     #$4C64				; TPS% THRESH TBL
8AD4:          LDAA    L0062				; ENGINE RPM/25
8AD6:          JSR     LF49A

8AD9:          STAA    L01E2				; TPS% THRESH FOR WOT ENABLE 

8ADC:          TAB   

  
8ADD:          BRCLR   L003D,#$20,L8AE7		; BR IF NOT b5, PWR ENR IS ACTIVE 
											;
8AE1:          SUBB    L4917				; 10% TPS FOR PE TBL TPBL L4C53 (WOT THRESH TBL)
8AE4:          BCC     L8AE7				; BR IF TPS GT THRESH
											;	
8AE6:          CLRB    
8AE7:  L8AE7   CMPB    L01D9				; %TPS
8AEA:          BCS     L8AEF
											;
8AEC:          JMP     L8BFC
 
8AEF:  L8AEF   BRSET   L003F,#$20,L8B51		; BR IF b5, 
											;
8AF3:          LDAA    L0063				; RPM/12.5
8AF5:          SUBA    L0065				; OLD RPM/25
8AF7:          BCC     L8AFA				; BR IF DIFF ... 
											;
8AF9:          CLRA    
8AFA:  L8AFA   CMPA    L4914				; 125 RPM, POS RPM DIFF TO BYPASS PE DELAY
8AFD:          BLS     L8B05
											;
8AFF:          BSET    L003F,#$20
8B02:          JMP     L8B51
 
 
			
			;
			; CK COOL TO BYPASS PE DELAY QUAL'S
			;
8B05:  L8B05   LDAB    L0006				; COOL VALUE
8B07:          CMPB    L4916				; IF COOL G.T. 105 DEG c, BYPASS PE DELAY
8B0A:          BHI     L8B51				; BR IF COOL
											;
8B0C:          CMPB    L4915				; IF COOL E.Q. or L.T. 55 DEG c, BYPASS PE DELAY
8B0F:          BLS     L8B51				; BR IF COOL 
											;
8B11:          LDAB    L4918				; IF  RPM E.Q. or G.T 4300 RPM, BYPASS PE DELAY
8B14:          CMPB    L0062				; ENGINE RPM/25
8B16:          BLS     L8B51				; BR IF RPM 
											;
8B18:          LDAA    L01E3

8B1B:          LDAB    L01D9				; %TPS
8B1E:          SUBB    L01DB
8B21:          BCS     L8B26				; BR IF DIFF TPS ....

8B23:          CBA     
8B24:          BLS     L8B4E				; BR IF ...
											;
8B26:  L8B26   LDAA    L01CD
8B29:          CMPA    L0062				; ENGINE RPM/25
8B2B:          BLS     L8B34				; BR IF RPM ......
											;
8B2D:          BRSET   L003D,#$20,L8B34		; BR IF b5,  PWR ENR IS ACTIVE
											;

8B31:          JMP     L8BFC


8B34:  L8B34   BRSET   L003D,#$01,L8B3B		; BR IF b0,  PWR ENR DELAY TIME COMPLETE
											; 
8B38:          JMP     L8BF3


8B3B:  L8B3B   LDAB    L0277				; PWR ENTR SLER RATE TIMER
8B3E:          CMPB    L491A				; 640 msec DLY, PWR ENRICH SLEW RATE 
8B41:          INCB    						; INCR TIMER
8B42:          BCS     L8B57				; BR IF TIMER ROLLED OVER
											;
8B44:          LDAB    L0278				; PWR ENR AFR SLEW MULT
8B47:          ADDB    L491B			   	; 19.9% ADJ TO PWR ENR AFR SLEW MULT
8B4A:          BCC     L8B53				; BR IF NO OVERFLOW
											;
8B4C:          BRA     L8B51
		;----------------------------------------

8B4E:  L8B4E   BSET    L003F,#$20			; SET b5,

8B51:  L8B51   LDAB    #255					; FORCE MAX VALUE
8B53:  L8B53   STAB    L0278				; PWR ENR AFR SLEW MULT

8B56:  L8B56   CLRB    
8B57:  L8B57   STAB    L0277				; PWR ENTR SLER RATE TIMER

8B5A:          BSET    L003D,#$20			; SET b5, PWR ENR IS ACTIVE
    
    	;*********************************************
    	; WOT AFR vs RPM
    	;
    	; TBL = AFR * 10
    	;*********************************************
8B5D:          LDX     #$4C6E				; INDEX WOT AFR TBL
8B60:          LDAA    L0062				; ENGINE RPM/25
8B62:          JSR     LF4C1				; 2d LK UP

8B65:          TAB     

8B66:          LDAA    L0269				; PWR ENRICH TIMER
8B69:          CMPA    L491D				; IF IN PWR ENRICH 10 SEC, DISABLE PWR ENRT RAMP
8B6C:          BHI     L8BC1				; BR IF TIMED OUT
											;
8B6E:          LDAA    L0002				; MAJOR LOOP COUNTER
8B70:          CMPA    #$07					;
8B72:          BNE     L8B77				;
											;
8B74:          INC     L0269				; PWR ENRICH TIMER

8B77:  L8B77   LDAA    L0062				; ENGINE RPM/25
8B79:          CMPA    L4918				; BYPASS PE DELAY RPM
8B7C:          BCC     L8BC1				; BR IF RPM GT THRESH
											;
8B7E:          LDAA    L0006				; COOL VALUE
8B80:          CMPA    L491E				; DISABLE PWR ENR RAMP IF COOL G.T. 105
8B83:          BHI     L8BC1				; BR IF COOL GT THRESH
											;
8B85:          CMPA    L4915				; IF COOL E.Q. or L.T. 55 DEG c, BYPASS PE DELAY
8B88:          BLS     L8BC1
											;
		;
		; CK TPS QUALS FOR WOT PE
		;
8B8A:          LDAA    L01D9				; %TPS
8B8D:          CMPA    L01E0				; SAVE HIGH TPS WOT TPS THRESH
8B90:          BHI     L8BC1				; BR IF %TPS GT THRESH
											;
8B92:          SUBA    L01E2				; TPS% THRESH FOR WOT ENABLE
8B95:          BCC     L8B99				; BR IF %TPS GT THRESH
											;
8B97:          LDAA    #$00
8B99:  L8B99   PSHB    
8B9A:          PSHA    

		;
		; CK TPS QUALS FOR WOT PE
		;
8B9B:          LDAA    L01E0				; SAVE HIGH TPS WOT TPS THRESH
8B9E:          SUBA    L01E2				; TPS% THRESH FOR WOT ENABLE
8BA1:          BCC     L8BA5
											;
8BA3:          LDAA    #$00

8BA5:  L8BA5   CLRB    
8BA6:          XGDX    
8BA7:          PULA    
8BA8:          CLRB    
8BA9:          FDIV    
8BAA:          XGDX    

8BAB:          LDAB    L4925				; 1.5 AFR ADJ IF IN PWR ENR RAMP MODE
8BAE:          MUL     
8BAF:          ADCA    #$00
8BB1:          TAB
     
8BB2:          LDAA    L4925				; 1.5 AFR ADJ IF IN PWR ENR RAMP MODE
8BB5:          SBA     
8BB6:          BCC     L8BBA
											;
8BB8:          LDAA    #$00
8BBA:  L8BBA   PULB    
8BBB:          ABA     
8BBC:          BCC     L8BC0
											;
8BBE:          LDAA    #255
8BC0:  L8BC0   TAB     

		;
		; CK OWR ENRICH QUAL'S
		;
8BC1:  L8BC1   LDAA    L0006				; COOL VALUE
8BC3:          CMPA    L491C				; 50c COOL, COLD PWR ENR THRESH
8BC6:          BHI     L8BDD				; BR IF COOL GT THRESH
											;
8BC8:          LDAA    L0062				; ENGINE RPM/25
8BCA:          CMPA    L491F				; 2000 RPM COLD PWR ENR THRESH
8BCD:          BCC     L8BDD				; BR IF RPM/25 GT THRSH
											;
8BCF:          LDAA    L0284				; MPH/1
8BD2:          CMPA    L4920				; 25 MPH COLD PWR ENR THRES
8BD5:          BCC     L8BDD				; BR IF Vss GT THRESH
											;
8BD7:          SUBB    L4924				; 0.7 AFR COLD PWR ENRICH
8BDA:          BCC     L8BDD				; BR IF 
											;
8BDC:          CLRB    

8BDD:  L8BDD   LDAA    L024A				; AFR
8BE0:          SBA     						; SUB OFF ...
8BE1:          BLS     L8C38				; BR IF UNDERFLOW
											;
8BE3:          LDAB    L0278				; PWR ENR AFR SLEW MULT
8BE6:          MUL     						; APPLY MULT
8BE7:          ADCA    #$00
8BE9:          TAB     

8BEA:          LDAA    L024A				; AFR
8BED:          SBA     						; SUB OFF 
8BEE:          STAA    L024A				; AFR

8BF1:          BRA     L8C38
		;----------------------------------------

			;
			; CK POWER ENRICH DELAY TIMER 
			;
8BF3:  L8BF3   LDD     L0818				; MPH, 16 BIT
8BF6:          CPD     L4926				; 0 MPH , DO NOT ALLOW PWR ENRICH IF
8BFA:          BCC     L8C0D				; BR IF MPH GT THRESH 
											;
8BFC:  L8BFC   LDAB    L0276				; POWER ENRICH TIMER
8BFF:          CMPB    L4919				; 70 SEC DELAY AFTER QUAL'S TO ENTER PWR ENRICH
8C02:          INCB    						; DECREMENT DELAY COUNTER
8C03:          BCS     L8C29				; BR IF COUNTER ROLLS OVER
											;
8C05:          CLR     L0278				; PWR ENR AFR SLEW MULT
8C08:          CLR     L0269				; PWR ENRICH TIMER

8C0B:          BRA     L8C32
		;----------------------------------------

8C0D:  L8C0D   LDAB    L0276				; POWER ENRICH DELAY TIMER
8C10:          BNE     L8C18				; BR IF TIMER = NZ
											;
8C12:          BSET    L003D,#$01			; SET b0, PWR ENR DELAY TIME COMPLETE
 
8C15:          JMP     L8B56


		;
		; CK TPS QUALS FOR WOT PE
		;
8C18:  L8C18   LDAA    L01D9				; %TPS
8C1B:          CMPA    L01E0				; SAVE HIGH TPS WOT TPS THRESH
8C1E:          BLS     L8C28				; BR IF TIMER LT THRESH
											;
8C20:          SUBB    L01E1
8C23:          BCC     L8C29
											;
8C25:          CLRB    
8C26:          BRA     L8C29
		;----------------------------------------

8C28:  L8C28   DECB   						; DECR POWER ENRICH TIMER
 											;
8C29:  L8C29   LDAA    L0002				; MAJOR LOOP COUNTER
8C2B:          CMPA    #$17					;
8C2D:          BNE     L8C32				; BR IF b3 or b4
											;
8C2F:          STAB    L0276				; POWER ENRICH TIMER

		;----------------------------
		; MWAF, AFR MD WORD 0,
        ; 		b5 1 = PWR ENR IS ACTIVE   
        ; 		b0 1 = PWR ENR DELAY TIME COMPLETE    
		;----------------------------
8C32:  L8C32   BCLR    L003D,#$21			; CLR b5 & b0
8C35:          BCLR    L003F,#$20


8C38:  L8C38   LDAA    L01D9				; %TPS
8C3B:          STAA    L01DB

8C3E:          BRCLR   L0052,#$40,L8C53		; BR IF NOT b6,
											;

    	;----------------------------------------------
    	; AFR USED IF CAT OVER TEMP vs  AIRFLOW
    	; 
    	;
    	; AFR * 10
    	;----------------------------------------------
8C42:          LDAA    L0232				; AIR FLOW
8C45:          LDX     #$4999
8C48:          JSR     LF4C1				; 2d LK UP

8C4B:          CMPA    L024A				; AFR
8C4E:          BHI     L8C53
											;
8C50:          STAA    L024A				; AFR

8C53:  L8C53   BRCLR   L003B,#$10,L8C66

8C57:          LDAA    L0395
8C5A:          BITA    #$04
8C5C:          BEQ     L8C66
											;
8C5E:          LDAA    L0397
8C61:          STAA    L024A				; AFR

8C64:          BRA     L8C6D
		;----------------------------------------

8C66:  L8C66   BRCLR   L0086,#$40,L8C6D		; BR IF NOT b6, 
											;
8C6A:          JSR     L1800				; TO HEADS UP

8C6D:  L8C6D   LDAA    L024A				; AFR
8C70:          STAA    L024B				; SAVE AFR VALUE

8C73:          LDAA    L0002				; MAJOR LOOP COUNTER
8C75:          CMPA    #159
8C77:          BNE     L8C8E
											;
8C79:          LDD     L0284				; MPH/1
8C7C:          SUBD    L081A				; MPH
8C7F:          BCC     L8C85				; BR IF MPH LT ... 
											;
8C81:          NEGA    
8C82:          NEGB    
8C83:          SBCA    #$00
8C85:  L8C85   STD     L0818				; MPH, 16 BIT

8C88:          LDD     L0284				; MPH/1
8C8B:          STD     L081A				; MPH

8C8E:  L8C8E   BCLR    L003D,#$04			; CLR b2, BLK LRN ADDR CHANGE 1 = CHANGED 

			;
			; CK IF SEPERATE BLM IDLE CELLS SELECTED
			;
8C91:          LDAA    L48F6				; BLM OPT WD
8C94:          BITA    #$01					; b0, SEPARATE BLM IDLE CELLS
8C96:          BEQ     L8CCB				; BR IF NOT b0, 
											;
8C98:          LDAB    L01D9				; %TPS
8C9B:          CMPB    L48DA				; 2.3% TPS MAX IDLE FUEL TABLE
8C9E:          BCC     L8CCB				; BR IF TPS GT THRESH
											;
8CA0:          LDAB    L0284				; MPH/1
8CA3:          CMPB    L48D9				; 2 MPH, MAX FOR IDLE SPK TBL
8CA6:          BCC     L8CCB				; BR IF Vss GT THRESH
											;
8CA8:          LDAB    #16					; CK IF IN IDLE CELL

			;
			; CK IF SEPERATE BLM A/C IDLE CELLS SELECTED
			;
8CAA:          BITA    #$02					; b1, SEPARATE BLM A/C IDLE CELLS
8CAC:          BEQ     L8CB3				; BR IF NOT b1
											;
8CAE:          BRCLR   L0041,#$10,L8CB3		; BR IF NOT b4, A/C PRESSURE SW, (A/C ON)
											;
8CB2:          INCB 

			;
			; CK IF SEPERATE BLM PK/NEUT CELLS SELECTED
			;
8CB3:  L8CB3   BITA    #$04					; b2, SEPERATE BLM PK/NEUT CELLS
8CB5:          BEQ     L8CBD				; BR IF NOT b2
											;
8CB7:          BRCLR   L0041,#$20,L8CBD		; BR IF b5, PARK/NEUTRAL
											;
8CBB:          ADDB    #$02					; 


8CBD:  L8CBD   BRCLR   L0051,#$01,L8CC3		; BR IF NOT b0, (PK/NEUT CELL) 

8CC1:          LDAB    #20					; CK FOR CELL 20 

8CC3:  L8CC3   CMPB    L0247			 	; BLM CELL NUM
8CC6:          BEQ     L8D3A				; BR IF ..
											;
8CC8:          JMP     L8D73
 			;-----------------------------------------



			;
			; HERE IF NOT SEPERATE BLM IDLE CELLS SELECTED
			;
8CCB:  L8CCB   LDAB    L0247			 	; BLM CELL
8CCE:          CMPB    #16					; CK IF IN IDLE CELL
8CD0:          BCC     L8D3C
											;
8CD2:          ANDB    #$03

		
8CD4:          LDX     #$48EE				; INDEX BLM RPM BOUNDS TBL
8CD7:          ABX     						; ADJ FOR CURRENT BOUND
8CD8:          DEX     
8CD9:          TSTB    						; CK FOR Z
8CDA:          BEQ     L8CEB				; BR IF Z
											;
8CDC:          LDAA    0,X
8CDE:          SUBA    L48F4				; BLM WINDOW HYST 75 RPM
8CE1:          BCS     L8CE7
											;
8CE3:          CMPA    L0062				; ENGINE RPM/25
8CE5:          BHI     L8D3C
											;
8CE7:  L8CE7   CMPB    #$03
8CE9:          BEQ     L8CF6				; BR IF 3
											;
8CEB:  L8CEB   LDAA    1,X
8CED:          ADDA    L48F4				; BLM WINDOW HYST 75 RPM
8CF0:          BCS     L8CF6
											;
8CF2:          CMPA    L0062				; ENGINE RPM/25
8CF4:          BCS     L8D3C
											;
8CF6:  L8CF6   LDAB    L0247			 	; BLM CELL
8CF9:          ANDB    #$0C					; MASK FOR BITS 2 & 3
8CFB:          LSRB    						; SHIFT TO b0 & 1
8CFC:          LSRB    						;
8CFD:          LDX     #$48F1				; INDEX BLM MAP CELLS
8D00:          ABX     						; ADX INDEX FOR CURRENT BOUND
8D01:          DEX     						;
8D02:          TSTB    						;
8D03:          BEQ     L8D21				;
											;
8D05:          LDAA    0,X					;
8D07:          SUBA    L48F5				; HYST KPA, 2.5 Kpa
8D0A:          BCS     L8D1D				;
											;
8D0C:          LDY     #$400E				; AFR MD BYTE 4, 0000 0011
8D10:          CMPA    L01CF				; 
											;
8D13:          BRSET   0,Y,#$01,L8D1B		; BR IF b0, USE ALT CMAP vs MAP 
											; LD & AD MAP FOR BLM ENABLE 

8D18:          CMPA    L01C0				; GET CURRENT MAP VALUE
8D1B:  L8D1B   BHI     L8D3C				;
											;
8D1D:  L8D1D   CMPB    #$03					;
8D1F:          BEQ     L8D37				;
											;
8D21:  L8D21   LDAA    1,X					;
8D23:          ADDA    L48F5				; HYST KPA, 2.5 Kpa
8D26:          BCS     L8D37				;
											;
8D28:          CMPA    L01CF				;
											;
8D2B:          LDX     #$400E				; AFR MD BYTE 4
8D2E:          BRSET   0,X,#$01,L8D35		; BR IF	b0,  USE ALT CMAP vs MAP LD &
											;  AD MAP FOR BLM ENABLE 

8D32:          CMPA    L01C0				; CURRENT MAP VALUE
8D35:  L8D35   BCS     L8D3C
											;
8D37:  L8D37   LDAB    L0247			 	; BLM CELL


8D3A:  L8D3A   BRA     L8D79
		;----------------------------------------

8D3C:  L8D3C   CLRB    
8D3D:          LDAA    L0062				; ENGINE RPM/25
8D3F:          CMPA    L48EE
8D42:          BCS     L8D51
											;
8D44:          INCB    
8D45:          CMPA    L48EF
8D48:          BCS     L8D51
											;
8D4A:          INCB    
8D4B:          CMPA    L48F0
8D4E:          BCS     L8D51
											;
8D50:          INCB    
8D51:  L8D51   LDAA    L01CF

			;------------------------------
			; AFR MD BYTE 4,	 0000 0011 
			;
			; b7 1 = Not Used
			; b6 1 = Not Used
			; b5 1 = LATCH ERR 45
			; b4 1 = USE L4979 WITH ASYNC FUEL DELIVERY
			;
			; b3 1 = CPI MANAFOLD TUNE CNT'L
			; b2 1 = SHIFT LIGHT ENABLE 
			; b1 1 = USE ALT CMAP vs
			;    MAP LD FOR FUEL CUR HYST PAIR
			; b0 1 = USE ALT CMAP vs
			;    MAP LD & AD MAP FOR BLM ENABLE 
			;------------------------------
8D54:          LDX     #$400E				;
8D57:          BRSET   0,X,#$01,L8D5E		; BR IF


			;
			;
			; CK BLM QUAL MAP VALUES
			;
8D5B:          LDAA    L01C0				; GET CURRENT MAP VALUE
8D5E:  L8D5E   CMPA    L48F1				; 26 Kpa Lo  MAP
8D61:          BCS     L8D73				; BR IF MAP LT LOW THRESH
											;
8D63:          ADDB    #$04					; INCR CELL POINTER
8D65:          CMPA    L48F2				; 55 Kpa Mid MAP
8D68:          BCS     L8D73				; BR IF MAP LT MID THRESH
											;
8D6A:          ADDB    #$04					; INCR CELL POINTER
8D6C:          CMPA    L48F3				; 80 Kpa Hi  MAP
8D6F:          BCS     L8D73				; BR IF MAP LT HI THRESH
											;
8D71:          ADDB    #$04


					;----------------------------
					; MWAF, AFR MD WORD 0,
                    ; 		b3 1 = DELAY BLM UPDATE   
                    ; 		b2 1 = BLK LRN ADDR CHANGE 1 = CHANGED
					;----------------------------
8D73:  L8D73   BSET    L003D,#$0C			; SET b2 & b3
8D76:          BSET    L006E,#$01			; EGR DIAG INT RESET

8D79:  L8D79   LDX     #$02B3
8D7C:          ABX     
8D7D:          LDAA    0,X
8D7F:          CMPA    L48FC				; MAX BLM 
8D82:          BHI     L8D92
											;
8D84:          CMPB    #$0010
8D86:          BCS     L8D8D
											;
8D88:          CMPA    L48FA

8D8B:          BRA     L8D90
		;----------------------------------------

8D8D:  L8D8D   CMPA    L48F9
8D90:  L8D90   BCC     L8D98
											;
8D92:  L8D92   BSET    L0046,#$40			; SET b6, NON VOL MEM BOMBED

8D95:          JSR     LF280				; RESET BLM CELLS to 128

8D98:  L8D98   STAA    L0248  				; BLM
8D9B:          STAB    L0247			 	; BLM CELL

			;-----------------------------------------
			; AFR MD BYTE 2	 1011 0111 
			;
			; b7 1 = CAN PURGE
			; b6 1 = CONDITIONAL INT R/S ON BLM CELL CHNAGE
			; b5 1 = INT R/S IF ACELL ENRICH
			; b4 1 = INT RESET IN BLM CELL CHANGE
			;
			; b3 1 = ASDF 
			; b2 1 = CRANK FUEL ALL INJ'S EACH DRP
			; b1 1 = ERR 44/45 BLM LMT
			; b0 1 = SYNC MAP SENSOR READS  
			;-----------------------------------------                         
8D9E:          LDX     #$400C				; INDEX AFR MD BYTE 2
8DA1:          BRSET   0,X,#$10,L8DEF		; BR IF b4, INT RESET
											;
8DA5:          LDAA    L01D9				; %TPS
8DA8:          CMPA    L48DA				; 2.3% TPS MAX IDLE FUEL TABLE
8DAB:          BCS     L8DB6
8DAD:          BRCLR   L0052,#$04,L8DBF
8DB1:          BCLR    L0052,#$04
8DB4:          BRA     L8DE9
		;----------------------------------------

8DB6:  L8DB6   BRSET   L0052,#$04,L8DBF
8DBA:          BSET    L0052,#$04
8DBD:          BRA     L8DE9
		;----------------------------------------

8DBF:  L8DBF   LDAA    L0249				; OLD BLM
8DC2:          SUBA    L0248				; BLM
8DC5:          BEQ     L8DE6				; BR IF Z

8DC7:          BMI     L8DD8

8DC9:          CMPA    L4909
8DCC:          BCS     L8DE6

8DCE:          LDAA    L020F				; INTEGRATOR COUNTS
8DD1:          CMPA    L4907
8DD4:          BHI     L8DE6
											;
8DD6:          BRA     L8DE9
		;----------------------------------------

8DD8:  L8DD8   NEGA    
8DD9:          CMPA    L490A			   	; LEAN to RICH DIFF BLM THRSH IF
											; BLM CELL CHANGE, R/S INT
8DDC:          BCS     L8DE6				; BR IF BLM GT THRESH
											;
8DDE:          LDAA    L020F				; INTEGRATOR COUNTS
8DE1:          CMPA    L4908				; 122 INT, TO RESET INT IF BLM L -> R
8DE4:          BCC     L8DE9				; BR IF NIT GT THRESH
											;
8DE6:  L8DE6   BCLR    L003D,#$04			; CLR b2, LEAN to RICH DIFF BLM THRSH
											;	 IF BLM CELL CHANGE, R/S INT
											;
8DE9:  L8DE9   LDAA    L0248  				; BLM
8DEC:          STAA    L0249				; OLD BLM
											;
8DEF:  L8DEF   LDAA    L0240				;
8DF2:          BNE     L8E1A				;
											;
8DF4:          LDAA    L48C8				; 0.1 SEC  XISITION CALC INTERVAL
8DF7:          STAA    L0240				;

			;
			; FILTER TPS
			;
8DFA:          LDAB    L48C9				; 6.3% TPS FILTER COEF 
8DFD:          LDX     L01DE				; GET OLD TPS
8E00:          LDAA    L01D9				; %TPS
8E03:          JSR     LF459				; LAG FILT
8E06:          STD     L01DE				; SAVE FILT TPS

			;
			; FILTER ..
			;
8E09:          LDAB    L01CB				;
8E0C:          LDX     L01C7				;
8E0F:          LDAA    L01C0				; GET CURRENT MAP VALUE
8E12:          JSR     LF459				; LAG FILT
8E15:          STD     L01C7				;

8E18:          BRA     L8E1D
		;----------------------------------------

8E1A:  L8E1A   DEC     L0240

8E1D:  L8E1D   BRCLR   L003E,#$02,L8E68		; BR IF NOT b1,DECELL FUEL C/O TPS ACEL ENRICH 
											; 
8E21:          BRSET   L003D,#$08,L8E68		; BR IF b3, DELAY BLM UPDATE 
											;
8E25:          LDAA    L020F				; INTEGRATOR COUNTS
8E28:          CMPA    #128					; MID POINT VALUE
8E2A:          BEQ     L8E68				; BR IF INT GT 128
											;
8E2C:          LDAB    L0274				;
8E2F:          INCB    						;
8E30:          BMI     L8E3B				;
											;
8E32:          STAB    L0274				;
8E35:          ASLB    						;
8E36:          CMPB    L026B				;
8E39:          BCS     L8EA6				;
											;
8E3B:  L8E3B   LDAB    L0273				; BLM UPDATE TIMER
8E3E:          INCB    	   					; INCR BLM UPDATE TIMER
8E3F:          BEQ     L8E49				; BR IF TIMER = Z
											;
8E41:          STAB    L0273				; BLM UPDATE TIMER
8E44:          CMPB    L48ED				; 650 msec FREQ BLM UPDATE
8E47:          BCS     L8EA6				; BR IF TIMER LT THRESH
											;
8E49:  L8E49   LDX     #$48F7				; 2, CLSD LP INT WINDOW ERR 32
8E4C:          LDY     #$48F9

8E50:          LDAB    L0247			 	; BLM CELL
8E53:          CMPB    #16					; idle cell 
8E55:          BCS     L8E5A				; BR IF CELL VALUE ....
											;
8E57:          INX     
8E58:          INY     
8E5A:  L8E5A   SUBA    #128					; MID POINT VALUE
8E5C:          BCS     L8E6B				; BR IF VALUE IS LT 128
											;
8E5E:          CMPA    0,X
8E60:          BLS     L8EA6
											;
8E62:          BRSET   L003E,#$40,L8EA6		; BR IF b6, RICH/ LEAN, 1 = RICH

8E66:          BRA     L8E74
		;----------------------------------------

8E68:  L8E68   JMP     L8E9F
 
 
8E6B:  L8E6B   NEGA    						; INVERT BLM VAKUE
8E6C:          CMPA    0,X					;
8E6E:          BLS     L8EA6				;
											; 
8E70:          BRCLR   L003E,#$40,L8EA6		; BR IF NOT b6, RICH/LEAN, 1 = RICH

		;
		; SET UP BLM ARRAY
		;
8E74:  L8E74   LDX     #$02B3
8E77:          ABX     						; ADJUST FOR CELL NUMBER
8E78:          LDAA    0,X					; GET BLM FOR THIS CELL
											;
8E7A:          BRCLR   L003E,#$40,L8E8D		; BR IF NOT b6, RICH/ LEAN, 1 = RICH


		;
		; AFR IS RICH, SUB FROM BLM
		; 
8E7E:          SUBA    L48FB				; 1, BLM UPDATE VALUE
8E81:          BCS     L8E88				; BR IF UNDERFLOW
											;
8E83:          CMPA    0,Y					; 
8E86:          BCC     L8E9A				;
											;
8E88:  L8E88   LDAA    0,Y					;
											'
8E8B:          BRA     L8E9A				
		;----------------------------------------

		;
		; AFR IS LEAN, ADD TO FROM BLM
		; 
8E8D:  L8E8D   ADDA    L48FB				; 1, BLM UPDATE VALUE
8E90:          BCS     L8E97				; BR IF OVERFLOW
											;
8E92:          CMPA    L48FC				; MAX BLM
8E95:          BLS     L8E9A				; BR IF BLM IS LT MAX LIMIT
											;
8E97:  L8E97   LDAA    L48FC				; FORCE MAX (172) BLM VALUE
8E9A:  L8E9A   STAA    0,X					; SAVE NEW BLM VALUE
8E9C:          STAA    L0248 				; BLM

8E9F:  L8E9F   CLRB    
8EA0:          STAB    L0274
8EA3:          STAB    L0273				; BLM UPDATE TIMER

8EA6:  L8EA6   BCLR    L003D,#$08			; CLR b3, DELAY BLM UPDATE 
 
8EA9:          LDAA    L0063				; RPM/12.5
8EAB:          STAA    L0065				; OLD RPM/12.5

8EAD:          LDAA    L01D5				; o2 VOLTS * 226 (A/D RESULT)
8EB0:          STAA    L01D4

8EB3:          RTS     
 			;----------------------------------------------


			;----------------------------------------------
8EB4:  L8EB4   LDX     #$400F				; AFR MD BYTE 5
8EB7:          BRCLR   0,X,#$01,L8EC3		; BR IF NOT b0, DO RPM/MPH LMT, (GOV'R OPT)
											;
8EBB:          BRCLR   L004F,#$80,L8EC3		; BR IF NOT b7, ENGINE RUNNING
											;
8EBF:          BRCLR   L006F,#$34,L8EC9
											;
8EC3:  L8EC3   LDAA    #255					; 
8EC5:  L8EC5   STAA    L0299 				;  DESIRED GOVENERING TPS TO BE OUTPUT
				
8EC8:          RTS     
 			;------------------------------------------


8EC9:  L8EC9   BCLR    L0075,#$04			; CLR b2,

8ECC:          LDAA    L50D8				;  ELECT GOVERNOR CNT'L PARAM
8ECF:          SUBA    L028E				;
8ED2:          BCC     L8ED8				;
											; 
8ED4:          NEGA    
8ED5:          BSET    L0075,#$04			;  SET b2
8ED8:  L8ED8   STAA    L0293				;

		;
		; CHECK FOR HEADS UP ON LINE
		; (GOVERNOR)
		;
8EDB:          BRCLR   L0086,#$40,L8EE4		; BR IF NOT b6, HU ON LINE

8EDF:          JSR     L1809				; TO HEADS UP
8EE2:          BCS     L8EC5				; BR IF HU RESULT LT Z

8EE4:  L8EE4   LDAA    L50DA				; 0 MPH
8EE7:          BEQ     L8F38				; BR IF Vss = Z
											;
8EE9:          LDD     L0284				; MPH/1
8EEC:          SUBA    L50DA				; 0 MPH
8EEF:          BCS     L8F17				; BR IF Vss LT THRESH
											;
8EF1:          ASLD    
8EF2:          BCS     L8EF7				;

8EF4:          ASLD    
8EF5:          BCC     L8EFA				;

8EF7:  L8EF7   LDD     #$FFFF
8EFA:  L8EFA   STAA    L0294

8EFD:          BSET    L0075,#$40
8F00:          BRSET   L0075,#$80,L8F33				;

8F04:          LDAA    L50E1				; 0 %TPS,
8F07:          CMPA    L01D9				; %TPS
8F0A:          BCS     L8F0F				;

8F0C:          LDAA    L01D9				; %TPS
8F0F:  L8F0F   STAA    L0286
8F12:          BSET    L0075,#$80

8F15:          BRA     L8F33
		;----------------------------------------

8F17:  L8F17   NEGA    
8F18:          NEGB    
8F19:          SBCA    #$0000
8F1B:          ASLD    
8F1C:          BCS     L8F21				;

8F1E:          ASLD    
8F1F:          BCC     L8F24
8F21:  L8F21   LDD     #$FFFF
8F24:  L8F24   STAA    L0294
8F27:          BCLR    L0075,#$40
8F2A:          BRCLR   L0075,#$80,L8F38
8F2E:          CMPA    L50DB
8F31:          BCC     L8F38
8F33:  L8F33   BCLR    L0075,#$13
8F36:          BRA     L8F3B
		;----------------------------------------

8F38:  L8F38   BCLR    L0075,#$80
8F3B:  L8F3B   BRCLR   L0075,#$04,L8F56
8F3F:          LDAB    L0075
8F41:          BITB    #$0081
8F43:          BNE     L8F50
8F45:          LDAA    L01D9				; %TPS
8F48:          CMPA    L0286
8F4B:          BHI     L8F50
8F4D:          STAA    L0286
8F50:  L8F50   BSET    L0075,#$01
8F53:          BCLR    L0075,#$12
8F56:  L8F56   LDAB    L0075
8F58:          BITB    #$0081
8F5A:          BNE     L8F5F
8F5C:          JMP     L9010


		;--------------------------------------------------
		; INTEGRAL GAIN FACTOR vs %TPS
		; (GOVENER)
		;
		; TBL = GAIN FACTOR * 32
		;----------------------------------------------
8F5F:  L8F5F   LDX     #$50E8
8F62:          LDAA    L0299 				;  DESIRED GOVENERING TPS TO BE OUTPUT
8F65:          LSRA    
8F66:          JSR     LF499
8F69:          LDAB    L0294

8F6C:          LDX     #$50DF

8F6F:          BRCLR   L0075,#$01,L8F77		; BR IF NOT b0,
											;
8F73:          INX     
8F74:          LDAB    L0293
8F77:  L8F77   MUL     
8F78:          ASLD    
8F79:          BCS     L8F81

8F7B:          ASLD    
8F7C:          BCS     L8F81

8F7E:          ASLD    
8F7F:          BCC     L8F84
											;
8F81:  L8F81   LDD     #$FFFF
8F84:  L8F84   STD     L028A

8F87:          LDAA    0,X
8F89:          LDX     #$028A				; 0650
8F8C:          JSR     LF550				; MUL 8X16 Subroutine
8F8F:          STD     L028A
8F92:          LDAA    L50DD
8F95:          LDAB    L0293
8F98:          MUL     
8F99:          ASLD    
8F9A:          BCS     L8F9F
8F9C:          ASLD    
8F9D:          BCC     L8FA2
8F9F:  L8F9F   LDD     #$FFFF
8FA2:  L8FA2   STD     L0290
8FA5:          CLR     L0292
8FA8:          BRCLR   L0075,#$80,L8FCC
8FAC:          LDAA    L0294
8FAF:          LDAB    L50DE
8FB2:          MUL     
8FB3:          ASLD    
8FB4:          BCS     L8FBF
8FB6:          ASLD    
8FB7:          BCS     L8FBF
8FB9:          ASLD    
8FBA:          BCS     L8FBF
8FBC:          ASLD    
8FBD:          BCC     L8FC2
8FBF:  L8FBF   LDD     #$FFFF
8FC2:  L8FC2   STAA    L0292
8FC5:          BRSET   L0075,#$04,L8FCC
8FC9:          STD     L0290
8FCC:  L8FCC   LDAB    L0075
8FCE:          BITB    #$0044
8FD0:          BEQ     L8FF8
8FD2:          LDD     L0286
8FD5:          SUBD    L028A
8FD8:          BCS     L8FDF
8FDA:          CMPA    L50E2
8FDD:          BCC     L8FE5
8FDF:  L8FDF   LDAA    L50E2
8FE2:          JMP     L9093
 ;
8FE5:  L8FE5   STD     L0286
8FE8:          SUBD    L0290
8FEB:          BCS     L8FF2
8FED:          CMPA    L50E2
8FF0:          BCC     L8FF5
8FF2:  L8FF2   LDAA    L50E2
8FF5:  L8FF5   JMP     L9097
 ;
8FF8:  L8FF8   LDD     L0286
8FFB:          ADDD    L028A
8FFE:          BCC     L9003
9000:          LDD     #$FFFF
9003:  L9003   STD     L0286
9006:          ADDD    L0290
9009:          BCC     L900D
900B:          LDAA    #$00FF
900D:  L900D   JMP     L9097
 ;
9010:  L9010   CLR     L0292
9013:          BRSET   L0075,#$02,L903D
9017:          LDAA    L028D
901A:          BMI     L9061
901C:          CMPA    #$0020
901E:          BLS     L9022
											;
		;----------------------------------------------
		; LEAD RPM vs RPM/SEC
		; (GOVENOR)
		;
		; TBL = GAIN FACTOR * 32
		;----------------------------------------------
9020:          LDAA    #$0020

9022:  L9022   LDX     #$50EE				; LEAD RPM
9025:          JSR     LF4B6				; 2d Lk Up
9028:          CMPA    L028E
902B:          BCC     L9061

902D:          BSET    L0075,#$02
9030:          LDAA    L50E1
9033:          CMPA    L01D9				; %TPS
9036:          BLS     L908B
9038:          LDAA    L01D9				; %TPS
903B:          BRA     L908B
		;----------------------------------------

903D:  L903D   BRSET   L0075,#$10,L9047
9041:          CLRA    
9042:          SUBA    L028D
9045:          BLT     L9065
9047:  L9047   BSET    L0075,#$10
904A:          LDAA    L0299 				;  DESIRED GOVENERING TPS TO BE OUTPUT
904D:          LDAB    L50E6
9050:          CMPA    L50E5
9053:          BCC     L9058
9055:          LDAB    L50E7
9058:  L9058   LDAA    L0293
905B:          MUL     
905C:          ADDD    L0286
905F:          BCC     L9094
9061:  L9061   LDAA    #$00FF
9063:          BRA     L9093
		;----------------------------------------

9065:  L9065   LDX     #$50FA
9068:          LDAA    L0006				; COOL VALUE
906A:          CMPA    #$0080
906C:          BLS     L9070
906E:          LDAA    #$0080
9070:  L9070   LSRA    
9071:          JSR     LF4C1				; 2d LK UP
9074:          LDAB    L028D
9077:          MUL     
9078:          ASLD    
9079:          BCS     L907E
907B:          ASLD    
907C:          BCC     L9081
907E:  L907E   LDD     #$FFFF
9081:  L9081   TAB     
9082:          LDAA    L0286
9085:          SBA     
9086:          LDAB    L0287
9089:          BCS     L9090
908B:  L908B   CMPA    L50E3
908E:          BCC     L9093
9090:  L9090   LDAA    L50E3
9093:  L9093   CLRB    
9094:  L9094   STD     L0286
9097:  L9097   LDAB    L0075
9099:          BITB    #$0084
909B:          BEQ     L90B7
909D:          BRSET   L0075,#$40,L90AA
90A1:          ADDA    L0292
90A4:          BCC     L90B7
90A6:          LDAA    #$00FF
90A8:          BRA     L90B7
		;----------------------------------------

90AA:  L90AA   SUBA    L0292
90AD:          BCS     L90B4
90AF:          CMPA    L50E2
90B2:          BCC     L90B7
90B4:  L90B4   LDAA    L50E2
90B7:  L90B7   STAA    L0299 				;  DESIRED GOVENERING TPS TO BE OUTPUT
90BA:          BITB    #$0011
90BC:          BEQ     L90D2
90BE:          LDAB    L0288
90C1:          BNE     L90D2
90C3:          BRCLR   L0075,#$01,L90CF
90C7:          LDAA    L028E
90CA:          CMPA    L50D9
90CD:          BCC     L90D2
90CF:  L90CF   BCLR    L0075,#$13

90D2:  L90D2   RTS     
 		;----------------------------------------------



90D3:  L90D3   LDAB    L0299 				;  DESIRED GOVENERING TPS TO BE OUTPUT
90D6:          SUBB    L01D9				; %TPS
90D9:          BCC     L90DC
90DB:          NEGB    

    	;-----------------------------------------------
		; ACTUATOR D.C. PROPORTIONAL GAIN vs %TPS ERROR
		; (GOVERNOR)
    	;  
		; TBL = FACTOR * 64
    	;-----------------------------------------------
90DC:  L90DC   STAB    L029A				; %TPS ERROR
90DF:          LDX     #$50FF				; ACTUATOR D.C. PROPORTIONAL GAIN
90E2:          LDAA    L029A				; %TPS ERROR
90E5:          JSR     LF4B6				; 2d Lk Up

90E8:          LDAB    L029A				; %TPS ERROR
90EB:          MUL     
90EC:          ASLD    
90ED:          BCS     L90F2

90EF:          ASLD    
90F0:          BCC     L90F5

90F2:  L90F2   LDD     #$FFFF
90F5:  L90F5   STD     L0295

    	;---------------------------------------------
		; ACTUATOR D.C. INTEGRAL GAIN FACTOR vs TPS ERROR
		; (GOVERNOR)
    	;  
		; TBL = FACTOR * 64
    	;----------------------------------------------
90F8:          LDX     #$5109
90FB:          LDAA    L029A				; %TPS ERROR
90FE:          JSR     LF4B6

9101:          LDAB    L029A				; %TPS ERROR
9104:          MUL     
9105:          STD     L0297

9108:          XGDX    
9109:          LDAA    L0299 				;  DESIRED GOVENERING TPS TO BE OUTPUT
910C:          CMPA    L01D9				; %TPS
910F:          XGDX    
9110:          BCC     L912B				; BR IF NO OVERFLOW

9112:          ADDD    L0288
9115:          BCC     L911A				; BR IF NO OVERFLOW
											;
9117:          LDD     #$FF00				; USE MAX VALUE
911A:  L911A   STD     L0288

911D:          ADDD    L0295
9120:          BCS     L9127
											;
9122:  L9122   ADDD    #128
9125:          BCC     L913E				; BR IF NO OVERFLOW
											;
9127:  L9127   LDAA    #255
9129:          BRA     L913E
		;----------------------------------------

912B:  L912B   LDD     L0288
912E:          SUBD    L0297
9131:          BCC     L9135				; BR IF NO UNDERFLOW
											;
9133:          CLRA    
9134:          CLRB    
9135:  L9135   STD     L0288
9138:          SUBD    L0295
913B:          BCC     L9122
											;
913D:          CLRA    
913E:  L913E   LDAB    L0299
9141:          CMPB    #255
9143:          BNE     L914B
											;
9145:          LDX     #$0000
9148:          STX     L0288
914B:  L914B   TAB     
914C:          BRCLR   L0051,#$10,L9153		; BR IF NOT b4,
											;
9150:          CLRB    
9151:          BRA     L9161
		;----------------------------------------

9153:  L9153   BRCLR   L003B,#$10,L9161
9157:          LDAA    L0393
915A:          BITA    #$0001
915C:          BEQ     L9161
											;
915E:          LDAB    L0394
9161:  L9161   LDAA    #$1F
9163:          STD     L306C

9166:          RTS     
 		;----------------------------------------------

9167:  L9167   LDAB    #$00AA
9169:          STAB    L303A

			;----------------------------------------------
			; AFR MD BYTE 5,	 0001 0000, (DIG I/O)
			;
			; b7 1 = MAN, (0 = TCC)
			; b6 1 = TCC (Non Elect xmish)
			; b5 1 = Not Used 
			; b4 1 = CONV OVER HEAT PROTECTION
			;
			; b3 1 = BURST KNOCK RETARD
			; b2 1 = A/C CLUTCH CNT'L, 0 = CPI TUNE
			; b1 1 = Not Used
			; b0 1 = 1 DO RPM/MPH LMT, (GOV'R OPT)
			;
			;----------------------------------------------
916C:          LDAA    L400F
916F:          BITA    #$04					; b2
9171:          BNE     L9185				; BR IF b2
											;

			;
			;  I/O PORT C
			;
9173:          BRSET   L004D,#$01,L917F		; BR IF b0, A/C REQUEST ON
											; 
9177:          BCLR    L0052,#$20			; CLR b5
917A:          BCLR    L0041,#$10			; CLR b4, A/C PRESSURE SW, (A/C ON)
											
917D:          BRA     L9185
		;----------------------------------------

917F:  L917F   BSET    L0052,#$20			; SET b5
9182:          BSET    L0041,#$10			; SET b4, A/C PRESSURE SW, (A/C ON)
9185:  L9185   BCLR    L0041,#$20			; CLR b5,  PARK/NEUTRAL
											

			;----------------------------------------------
			; AFR MD BYTE 5,	 0001 0000, (DIG I/O)
			;
			; b7 1 = MAN, (0 = TCC)
			; b6 1 = TCC (Non Elect xmish)
			; b5 1 = Not Used 
			; b4 1 = CONV OVER HEAT PROTECTION
			;
			; b3 1 = BURST KNOCK RETARD
			; b2 1 = A/C CLUTCH CNT'L, 0 = CPI TUNE
			; b1 1 = Not Used
			; b0 1 = 1 DO RPM/MPH LMT, (GOV'R OPT)
			;
			;----------------------------------------------
9188:          LDX     #$400F				; AFR MD BYTE 5
											;
918B:          BRSET   0,X,#$40,L9199		; BR IF b6,TCC (Non Elect xmish)
											;
918F:          LDAA    L004D				;  I/O PORT C
9191:          ANDA    #$1C					; MASK FOR PRNDL RANGE BITS 
9193:          CMPA    #$14					; b2, RANGE SW 1 OFF
											; b4, RANGE SW 3 OFF
9195:          BNE     L91A2
											;
9197:          BRA     L919F
		;----------------------------------------

9199:  L9199   LDAA    L004D
919B:          BITA    #$10					; b4, RANGE SW 3 OFF 
919D:          BNE     L91A2
											;
919F:  L919F   BSET    L0041,#$20			; SET b5, PARK/NEUTRAL
											
91A2:  L91A2   RTS     
 		;----------------------------------------



91A3:  L91A3   LDAB    L000A				; 

91A5:          LDAA    L00A7   				; BAT VOLTS, VDC/10
91A7:          CMPA    #169					; 16.9 VDC, 
91A9:          BLS     L91AF

91AB:          ANDB    #$EF					; 1110 1111
91AD:          BRA     L91B8
		;----------------------------------------

91AF:  L91AF   BRSET   L0044,#$10,L91BD		; BR IF b4, IGNITION OFF 
											;
91B3:          CMPA    L4EB6
91B6:          BHI     L91BD

91B8:  L91B8   BSET    L003E,#$04			; SET b2, LOW BATTERY 
91BB:          BRA     L9200
		;----------------------------------------

91BD:  L91BD   BCLR    L003E,#$04			; CLR b2, LOW BATTERY 
91C0:          ORAB    #$10

91C2:          LDAA    L0007				; IAC MOTOR POSIT
91C4:          CMPA    L0008
91C6:          BNE     L91CC

91C8:          ANDB    #$00FE
91CA:          BRA     L9200
		;----------------------------------------

91CC:  L91CC   BRCLR   L0009,#$01,L91D4		; BR IF NOT b0, IAC MOTOR Reset IN WORK
											;
91D0:          BRSET   L0002,#$03,L9200		; MAJOR LOOP COUNTER
91D4:  L91D4   BCC     L91DF				;
											;
91D6:          ANDB    #$FE					;
											;
91D8:          BRSET   L000A,#$01,L9200		; BR IF b0, MOTOR DIRECTION, 1=EXTEND
											;
91DC:          INCA    

91DD:          BRA     L91E6
		;----------------------------------------

91DF:  L91DF   ORAB    #$01

91E1:          BRCLR   L000A,#$01,L9200		; BR IF NOT b0, MOTOR DIRECTION, 1=EXTEND
											;
91E5:          DECA    
91E6:  L91E6   STAA    L0007				; IAC MOTOR POSIT
91E8:          BRSET   L000A,#$0C,L91F6		; BR IF b3 & B2, COIL A & B STATE ON
											;
91EC:          BRCLR   L000A,#$0C,L91F6		; BR IF NOT b3 & B2, COIL A & B STATE ON
											;
91F0:          BITB    #$01
91F2:          BNE     L91FA
91F4:          BRA     L91FE
		;----------------------------------------

91F6:  L91F6   BITB    #$0001
91F8:          BNE     L91FE
91FA:  L91FA   EORB    #$0004
91FC:          BRA     L9200
		;----------------------------------------

91FE:  L91FE   EORB    #$0008
9200:  L9200   STAB    L000A
9202:          SEI     
9203:          LDAA    L004C
9205:          ANDA    #$00E3
9207:          ANDB    #$001C
9209:          ABA     
920A:          STAA    L004C
920C:          CLI     
920D:          RTS     
 ; ------------------------------------------
920E:  L920E   BCLR    L0037,#$18			; CLR b4 & b3

9211:          BRCLR   L0037,#$04,L921B		; BR IF NOT b2, THROTTLE KICKER ACTIVE
											;
9215:          CLR     L088D				; THROTTLE KICKER TIMER

9218:          BCLR    L0037,#$04			; CLR b2, TTHROTTLE KICKER ACTIVE
											; 

				;
				; DIACMW2, NON-VOL IDLE CNT'L MD WD 
				; 
921B:  L921B   BRSET   L0036,#$40,L9222		;  BR IF b6,THROTTLE KICKER 
											;			HAS BEEN DISABLED ONCE 
											;
921F:          BSET    L0036,#$40			; SET b6,, THROTTLE KICKER
											;	 HAS BEEN DISABLED ONCE 
9222:  L9222   BSET    L004B,#$80			; SET b7. 

9225:          RTS     
 			;------------------------------------------


9226:  L9226   BRSET   L0037,#$04,L923C		; BR IF b2, THROTTLE KICKER ACTIVE
											;
922A:          LDAA    L02B1
922D:          ADDA    L50D5			    ; A/D TPS COMP FOR TPS OFFSET WHEN TPS RE-ENABLED
9230:          STAA    L02F6				; FILT TPS (XMISH)

9233:          LDAA    L50D3				; 32 Sec's, HYST TIME IF RE-ENBLED MUST STAY ON
9236:          STAA    L088D				; THROTTLE KICKER TIMER

9239:          BSET    L0037,#$04 			; SET b2, THROTTLE KICKER ACTIVE
											; 
923C:  L923C   BCLR    L004B,#$80			; CLR b7

923F:          RTS     
 			;------------------------------------------


9240:  L9240   LDX     #$004C				; INDEX XMISH MD WD 
9243:          BSET    0,X,#$10				; SET b4, 

9246:          RTS     
 			;------------------------------------------

			;
			; I/O PORT C
			;
9247:  L9247   BRSET   L004D,#$80,L924E		; BR IF b7, FWD LOW SW (NO) 1=ON 
											;
924B:          SEC     						; SECURE INTERUPTS

924C:          BRA     L924F
		;----------------------------------------

924E:  L924E   CLC     						; CLEAR AND RESTORE INTERUPTS

924F:  L924F   RTS     
 			;------------------------------------------

9250:  L9250   PSHA    
9251:          LDAA    L3008				; CPU PORT D
9254:          BITA    #$04					; b2, 
9256:          PULA    
9257:          BEQ     L925C
											;
9259:          SEC     
925A:          BRA     L925D
		;----------------------------------------

925C:  L925C   CLC     

925D:  L925D   RTS     
 		;------------------------------------------

 		;------------------------------------------
		; SET UP IAC ROUTINE
		;
 		;------------------------------------------
925E:  L925E   LDAA    L4EF2				; 16% TPS UPPR LMT FOR CLSD, (IAC)
9261:          ASLA    
9262:          ASLA    
9263:          STAA    L0885

9266:          BRCLR   L0046,#$40,L9272		; BR IF NOT b6, NON VOL MEM BOMBED 
											;
926A:          LDAA    L4EB0				; 145 STEPS IAC PARK DOWN
926D:          STAA    L0007				; IAC MOTOR POSIT

926F:          JSR     L92A4

9272:  L9272   BRSET   L0004,#$08,L927B		; BR IF b3,	 BAD SHUT DOWN

											;
9276:          JSR     L92F1

9279:          BRA     L927E
		;----------------------------------------

927B:  L927B   JSR     L93C5				;

927E:  L927E   LDAA    L4E8F				; 0000 1110, IAC MD WD #1
9281:          BITA    #$04               	; b2, 1 = THROTLE KICKER IN USE  
9283:          BEQ     L929C				; BR IF NOT 
											;
9285:          LDAA    L02F4				; BARO
9288:          CMPA    L50CE				; 85 Kpa,  BARO THRESH
928B:          BLS     L9294				; BR IF BARO LT THRESH
											;
928D:          LDAA    L0006				; COOL VALUE
928F:          CMPA    L50C7				; 54.5c COOL THRESH MAX FOR THROT KICKER
9292:          BCC     L9299				; BR OF COOL GT THRESH
											;
9294:  L9294   BSET    L0037,#$04			; SET b2, THROTTLE KICKER ACTIVE
											;
9297:          BRA     L929C
		;----------------------------------------

9299:  L9299   JSR     L920E
929C:  L929C   LDAA    L0007				; IAC MOTOR POSIT
929E:          STAA    L0008				; IAC

92A0:          JSR     L9240

92A3:          RTS     
 		;------------------------------------------


		;------------------------------------------
92A4:  L92A4   LDAA    L0006				; COOL VALUE
92A6:          CMPA    L4EB5
92A9:          TPA     

92AA:          LDAB    L4EB2				; 14.8%FLOW OF IDLE CELL IN DRV AFTER 
											; NON VOL MEM FAIL
92AD:          STAB    L02A7
92B0:          STAB    L02A9

92B3:          TAP     
92B4:          BCS     L92BD
92B6:          ADDB    L4EB3
92B9:          BCS     L92C2
92BB:          BRA     L92C4
		;----------------------------------------

92BD:  L92BD   ADDB    L4EB4
92C0:          BCC     L92C4
92C2:  L92C2   LDAB    #$00FF
92C4:  L92C4   STAB    L02AA
92C7:          STAB    L02AC

92CA:          LDAB    L4EB1				; 8.2% FLOW OF IDLE CELL IN PK AFTER
											;  NON VOL MEM FAIL
92CD:          STAB    L029D
92D0:          STAB    L029F

92D3:          TAP     
92D4:          BCS     L92DD

92D6:          ADDB    L4EB3
92D9:          BCS     L92E2
92DB:          BRA     L92E4
		;----------------------------------------

92DD:  L92DD   ADDB    L4EB4
92E0:          BCC     L92E4
92E2:  L92E2   LDAB    #$00FF
92E4:  L92E4   STAB    L02A0
92E7:          STAB    L02A2
92EA:          LDAA    L50D4
92ED:          STAA    L02B1
92F0:          RTS     
 ; ------------------------------------------
92F1:  L92F1   BRCLR   L0009,#$10,L930F		; BR IF NOT b4, WARM IDLE STABLE, A/C OFF
											;
92F5:          LDAA    L02A9
92F8:          CLRB    
92F9:          ADDA    L5098			    ; FLOW, IGN OFF, DRIVE & A/C OFF
92FC:          BCC     L9301
											;
92FE:          LDAA    L50C3				; 39% FLOW MAX IDLE INTEGRAL FOR NO A/C
9301:  L9301   STAA    L02A9

9304:          CMPA    L02A7
9307:          BLS     L930C
											;
9309:          STD     L02A7

930C:  L930C   BCLR    L0009,#$10			; CLR b4, WARM IDLE STABLE, A/C OFF
											;
930F:  L930F   BRCLR   L0009,#$20,L932D		; BR IF NOT b5, WARM IDLE STABLE, A/C ON
											;
9313:          CLRB    
9314:          LDAA    L02AC
9317:          ADDA    L5099				;  	 FLOW ,IGN OFF, DRIVE & A/C ON
931A:          BCC     L931F
											;
931C:          LDAA    L50C4				; 56.4% FLOW MAX IDLE INTEGRAL FOR A/C ON
931F:  L931F   STAA    L02AC
9322:          CMPA    L02AA
9325:          BLS     L932A
											;
9327:          STD     L02AA

932A:  L932A   BCLR    L0009,#$20			; CLR b5, WARM IDLE STABLE, A/C ON
											; 

         	;--------------------------------------
		 	; 0000 0001  IAC MD WD #2
		 	;
         	; b1 = 1 = PWR STEER SW IN USE
         	; b0 = 1 = INIT 16 BIT INTEGRALS FM 8 BIT WARM CELLS
         	;        = 0 = NORMAL INTEGRAL INIT
         	;--------------------------------------
932D:  L932D   LDAB    L4E90				; IAC MD WD #2
9330:          BITB    #$01					; b0
9332:          BEQ     L9340				; BR IF NOT b0
											;
9334:          LDAA    L029F
9337:          STAA    L029D

933A:          LDAA    L02A9
933D:          STAA    L02A7


        ;---------------------------------------------
       	;
       	; b3 = 1 = INIT A/C ON INTEGRAL CELLS TO A/C OFF CELLS 
       	; b2 = 1 =
       	; b1 = 1 = USE ETC IN DECELL FUEL CUT OFF
       	;      0 = DONT USE ETC IN DECELL FUEL CUT OFF   
	   	;
       	; b0 = 1 = MAN  TRANS IN USE,DISABLE CLSD LP IDLE IF 
       	;               QUALS NOT OK                       
       	;      0 = AUTO  TRANS IN USE,ENABLE CLSD IF RPM LOW
	   	;---------------------------------------------
9340:  L9340   LDAA    L4E8F				; 0000 1110, IAC MD WD #1
9343:          BITA    L0008
9345:          BEQ     L93B1

9347:          LDAA    L0006				; COOL VALUE
9349:          CMPA    L4EB5
934C:          TPA     
934D:          LDAB    L029D
9350:          TAP     
9351:          BCS     L935A
9353:          ADDB    L4EB3
9356:          BCS     L935F
9358:          BRA     L9364
		;----------------------------------------

935A:  L935A   ADDB    L4EB4
935D:          BCC     L9364
935F:  L935F   LDAB    #$00FF
9361:          STAB    L02A1
9364:  L9364   STAB    L02A0
9367:          LDAB    L029F
936A:          TAP     
936B:          BCS     L9374
936D:          ADDB    L4EB3
9370:          BCS     L9379
9372:          BRA     L937B
		;----------------------------------------

9374:  L9374   ADDB    L4EB4
9377:          BCC     L937B
9379:  L9379   LDAB    #$00FF
937B:  L937B   STAB    L02A2

937E:          LDAB    L02A7
9381:          TAP     
9382:          BCS     L938B
9384:          ADDB    L4EB3
9387:          BCS     L9390
9389:          BRA     L9395
		;----------------------------------------

938B:  L938B   ADDB    L4EB4
938E:          BCC     L9395
9390:  L9390   LDAB    #$00FF
9392:          STAB    L02AB
9395:  L9395   STAB    L02AA
9398:          LDAB    L02A9
939B:          TAP     
939C:          BCS     L93A5
939E:          ADDB    L4EB3
93A1:          BCS     L93AA
93A3:          BRA     L93AC
		;----------------------------------------

93A5:  L93A5   ADDB    L4EB4
93A8:          BCC     L93AC
93AA:  L93AA   LDAB    #$00FF
93AC:  L93AC   STAB    L02AC
93AF:          BRA     L93C4
		;----------------------------------------

         	;--------------------------------------
		 	; 0000 0001  IAC MD WD #2
		 	;
         	; b1 = 1 = PWR STEER SW IN USE
         	; b0 = 1 = INIT 16 BIT INTEGRALS FM 8 BIT WARM CELLS
         	;        = 0 = NORMAL INTEGRAL INIT
         	;--------------------------------------
93B1:  L93B1   LDAB    L4E90				; IAC MD WD #2
93B4:          BITB    #$01					; b0
93B6:          BEQ     L93C4				; BR IF NOT b0
											;
93B8:          LDAA    L02A2
93BB:          STAA    L02A0

93BE:          LDAA    L02AC
93C1:          STAA    L02AA 

93C4:  L93C4   RTS     
 		;------------------------------------------


93C5:  L93C5   BRSET   L0009,#$01,L93CF		; BR IF b0, IAC MOTOR Reset IN WORK
											;
93C9:          LDAA    L000A
93CB:          ANDA    #$0C
93CD:          STAA    L000A

93CF:  L93CF   RTS     
 		;------------------------------------------

		;
		; CHECK FOR HEADS UP ON LINE
		;
93D0:  L93D0   BRCLR   L0086,#$40,L93D7		; BR IF NOT HU,
93D4:          JSR     L1803				; TO HEADS UP
93D7:  L93D7   BCLR    L0038,#$40			; CLR b6
93DA:          BRCLR   L003B,#$10,L93E1		; BR IF NOT b4
93DE:          JSR     LA407

93E1:  L93E1   BRCLR   L0009,#$01,L93F9		; BR IF NOT b0, IAC MOTOR Reset IN WORK
											;
93E5:          CLR     L0008
93E8:          TST     L0007				; IAC MOTOR POSIT
93EB:          BEQ     L93F0
93ED:          JMP     L989B
 ;
93F0:  L93F0   BCLR    L0009,#$01			; CLR b0, IAC MOTOR Reset IN WORK
93F3:          BSET    L0009,#$04			; SET b2, R/S REQUESTED IF BIT CLEAR
93F6:          JSR     L92A4
93F9:  L93F9   BRCLR   L0044,#$10,L940A		; BR IF NOT b4, IGNITION OFF 
											;
93FD:          BRCLR   L0009,#$04,L9407		; BR IF NOT b2, R/S REQUESTED IF BIT CLEAR
											;
9401:          LDAA    L4EB0				; 145 STEPS IAC PARK DOW
9404:          JMP     L9899
 

9407:  L9407   JMP     LA3FA
 


940A:  L940A   BRCLR   L004F,#$80,L9411		; BR IF NOT b7, ENGINE RUNNING
											;
940E:          JMP     L9537


        
        ;---------------------------------------------
    	; IAC CLSD LP ENABLE DELAY AFTER STARTUP vs COOL
    	; (RPM HI)
    	; 
    	;  TBL =  10  * Sec's
        ;---------------------------------------------
9411:  L9411   LDAA    L0283				; RANGE LMT'ED COOL (-28 - 104c)
9414:          LDX     #$4EF5				; IAC CLSD LP ENABLE DELAY TBL
9417:          JSR     LF4C1				; 2d LK UP
941A:          STAA    L0866

        ;---------------------------------------------
    	; IAC CLSD LP ENABLE DELAY AFTER STARTUP vs COOL
    	; (RPM LO)
    	; 
    	;  TBL =  10  * SEC'S
        ;---------------------------------------------
941D:          LDAA    L0283				; RANGE LMT'ED COOL (-28 - 104c)
9420:          LDX     #$4F02
9423:          JSR     LF4C1				; 2d LK UP

9426:          STAA    L0867

9429:          LDAA    L4EB8				; 23% FLOW ADDED AFTER START UP (REPLACE'S TPS)
942C:          STAA    L086B

942F:          LDAA    L4EB9				; 100 msec DECAY PERIOD
9432:          STAA    L086C

9435:          LDAA    L0283				; RANGE LMT'ED COOL (-28 - 104c)
9438:          CMPA    #160					; 80c
943A:          BLS     L9441
											;
943C:          SUBA    #160
943E:          ASLA    
943F:          ADDA    #160

        ;---------------------------------------------
    	; DESIRED RPM IDLE vs COOLANT
    	; (PK.NEUT & A/C OFF)
    	;
    	; TBL = RPM/12.5
        ;---------------------------------------------
9441:  L9441   PSHA    
9442:          LDX     #$4F32


        ;---------------------------------------------
       	;
       	; b3 = 1 = INIT A/C ON INTEGRAL CELLS TO A/C OFF CELLS 
       	; b2 = 1 =
       	; b1 = 1 = USE ETC IN DECELL FUEL CUT OFF
       	;      0 = DONT USE ETC IN DECELL FUEL CUT OFF   
	   	;
       	; b0 = 1 = MAN  TRANS IN USE,DISABLE CLSD LP IDLE IF 
       	;               QUALS NOT OK                       
       	;      0 = AUTO  TRANS IN USE,ENABLE CLSD IF RPM LOW
	   	;---------------------------------------------
9445:          LDAB    L4E8F				; 0000 1110, IAC MD WD #1
9448:          BITB    #$01					; b0
944A:          BEQ     L944F				; BR IF NOT b0
											;
        ;---------------------------------------------
    	; DESIRED RPM IDLE vs COOLANT
    	; (PK.NEUT & A/C ON)
    	;
    	;  TBL =  .08  * RPM/12.5
        ;---------------------------------------------
944C:          LDX     #$4F50				; INDEX  DESIRED RPM IDLE 
											;
944F:  L944F   JSR     LF4C1				; 2d LK UP

9452:          PULB    
9453:          PSHA    
9454:          TBA  
   
        ;---------------------------------------------
    	; DESIRED RPM IDLE vs COOLANT
    	; (IN DRIVE & NOT RUNNING)
    	;
    	;  TBL = .08  * RPM/12.5
        ;---------------------------------------------
9455:          LDX     #$4F6E				; INDEX  DESIRED RPM IDLE
											;
9458:          JSR     LF4C1				; 2d LK UP
945B:          STAA    L085C


        ;---------------------------------------------
       	;
       	; b3 = 1 = INIT A/C ON INTEGRAL CELLS TO A/C OFF CELLS 
       	; b2 = 1 =
       	; b1 = 1 = USE ETC IN DECELL FUEL CUT OFF
       	;      0 = DONT USE ETC IN DECELL FUEL CUT OFF   
	   	;
       	; b0 = 1 = MAN  TRANS IN USE,DISABLE CLSD LP IDLE IF 
       	;               QUALS NOT OK                       
       	;      0 = AUTO  TRANS IN USE,ENABLE CLSD IF RPM LOW
	   	;---------------------------------------------
945E:          LDAB    L4E8F				; 0000 1110, IAC MD WD #1
9461:          BITB    #$01					; b0
9463:          BNE     L946E				; BR IF b0
											;
9465:          LDAB    L4EBC				; 100 % PK/NUT MULT TO L4F__ DRIVE MULT TBL
9468:          MUL     
9469:          ASLD    
946A:          BCC     L946E
946C:          LDAA    #255

946E:  L946E   PULB    
946F:          ABA     
9470:          STAA    L0857  				; DESIRED IDLE RPM/12.5

9473:          LDAA    L4EBB				; 500 msec DECAY PERIOD AFTER L4EB8,
9476:          STAA    L085D

9479:          LDAA    L4EBA				; 10 SEC'S RUN TIME TO START OF DECAY
947C:          STAA    L085E

947F:          CLRA    
9480:          STAA    L086D
9483:          STAA    L0879
9486:          STAA    L087A
9489:          STAA    L0876
948C:          STAA    L0877
948F:          STAA    L0887
9492:          STAA    L087B
9495:          STAA    L0864				; msec CLSD LP ENABLE DELAY AFTER IAC QUAL'S

9498:          LDAA    #128
949A:          STAA    L086E

949D:          BCLR    L0036,#$BD
94A0:          BCLR    L0037,#$9B
94A3:          BCLR    L0038,#$0F
94A6:          BCLR    L0038,#$70
94A9:          BCLR    L0039,#$C7

94AC:          LDAA    L4FBE				; 25 RPM, DEADBAND FOR UP DATING IDLE CELLS
94AF:          STAA    L0859				; RPM/12.5
											
94B2:          BCLR    L0009,#$02			; CLR b1, 1st DRIVE AWAY FLAG FOR
											;		  IAC KICK DOWN LOGIC


        ;---------------------------------------------
    	; IAC FLOW vs COOL (IN DRIVE)
    	; (COLD OFF SET)
    	; (NOT USED IF RUNNING)
    	;
    	;  TBL =  2.56  * %IAC FLOW
        ;---------------------------------------------
94B5:          LDAA    L0283				; RANGE LMT'ED COOL (-28 - 104c)
94B8:          LDX     #$4ECF
94BB:          JSR     LF4C1				; 2d LK UP

94BE:          CLRB    
94BF:          STD     L02AD
94C2:          STD     L02AF


        ;---------------------------------------------
    	; IAC FLOW vs COOL (PK/NEUT)
    	; (COLD OFF SET)
    	;
    	;   (NOT USED IF RUNNING)
    	;
    	; TBL = %IAC FLOW * 2.56
        ;---------------------------------------------
94C5:          LDAA    L0283				; RANGE LMT'ED COOL (-28 - 104c)
94C8:          LDX     #$4EC2				;
94CB:          JSR     LF4C1				; 2d LK UP
94CE:          CLRB    						;
94CF:          STD     L02A3				;
94D2:          STD     L02A5				;

        ;---------------------------------------------
    	; IAC COLD OFFSET DELAY PERIOD vc COOL
    	;
    	;
    	;  TBL =  10  * Sec's
        ;---------------------------------------------
94D5:          LDAA    L0283				; RANGE LMT'ED COOL (-28 - 104c)
94D8:          LDX     #$4EDC				;
94DB:          JSR     LF4C1				; 2d LK UP
											;
94DE:          STAA    L0875				; SAVE IAC COLD OFFSET DELAY PERIOD


                    ;------------------------------------
				   	; IAC MD WD #1
                    ; 	b5 = 1 = INIT INTEGRAL WITH L___, NOT RUNNING
                    ;---------------------------------
94E1:          LDAA    L4E8F				; 0000 1110, IAC MD WD #1
94E4:          BITA    #$20					; b5,
94E6:          BEQ     L94F7				; BR IF NOT b5
											;
94E8:          CLRB    
94E9:          BITA    #$01
94EB:          BNE     L94F2				;
											;
94ED:          LDAA    L4EB1				; 8.2% FLOW OF IDLE CELL IN PK AFTER
											;  NON VOL MEM FAIL
94F0:          BRA     L9508
		;----------------------------------------

94F2:  L94F2   LDAA    L4EB2				; 14.8%FLOW OF IDLE CELL IN DRV AFTER 
											; NON VOL MEM FAIL
											;
94F5:          BRA     L9503
		;----------------------------------------

94F7:  L94F7   BITA    #$01
94F9:          BNE     L9500				;
											;
94FB:          LDD     L029D
94FE:          BRA     L9508
		;----------------------------------------

9500:  L9500   LDD     L02A7
9503:  L9503   LDX     L02AD
9506:          BRA     L950B
		;----------------------------------------

9508:  L9508   LDX     L02A3
950B:  L950B   STD     L0862
950E:          STX     L0871

9511:          LDX     #$FFFF
9514:          STX     L087D

9517:          LDAA    L0006				; COOL VALUE
9519:          CMPA    L4E91				; 0 Deg c (32f), MIN COOL FOR IAC MOVED	
											; PRIOR TO STAR
951C:          BCS     L9531				;
											;
951E:          LDD     L0862
9521:          ADDA    L086B
9524:          BCS     L952B				;
											;
9526:          ADDD    L0871
9529:          BCC     L952E				;
											;
952B:  L952B   LDD     #$FFFF
952E:  L952E   JMP     L983D
 

9531:  L9531   LDAA    L4EB0				; 145 STEPS IAC PARK DOW
9534:          JMP     L9899
 

9537:  L9537   LDAB    L0036
9539:          PSHB    

			;----------------------------------------------
			; AFR MD BYTE 5,	 0001 0000, (DIG I/O)
			;
			; b7 1 = MAN, (0 = TCC)
			; b6 1 = TCC (Non Elect xmish)
			; b5 1 = Not Used 
			; b4 1 = CONV OVER HEAT PROTECTION
			;
			; b3 1 = BURST KNOCK RETARD
			; b2 1 = A/C CLUTCH CNT'L, 0 = CPI TUNE
			; b1 1 = Not Used
			; b0 1 = 1 DO RPM/MPH LMT, (GOV'R OPT)
			;
			;----------------------------------------------
953A:          LDAA    L400F
953D:          BITA    #$40
953F:          BEQ     L9547				;
											;
9541:          BRSET   L0041,#$20,L9571		; BR IF b5, PARK/NEUTRAL
											;
9545:          BRA     L954F				;
		;----------------------------------------

9547:  L9547   BRSET   L00A2,#$40,L9571		;
											;
954B:          BRSET   L00A2,#$10,L9571		;
											;
954F:  L954F   BSET    L0036,#$02			; SET b1, DRIVE

9552:          BITB    #$02					; b1
9554:          BNE     L95A1				; BR IF NOT b1
											;
9556:          LDAA    L4F23				; ___ Msec, DECAY PERIOD
9559:          PSHA    

955A:          LDAA    L4F25				; ___ Msec, PERIOD OF Pk/Neut TO Dr SHIFT
955D:          LDAB    L4F24
9560:          XGDX    

9561:          LDAA    L0006				; COOL VALUE
9563:          CMPA    L4F29				; -40c, COOL THRESH FOR ADDED TIME TO 
											;		PERIOD &  Clsd Lp DELAY
9566:          XGDX    
9567:          BCC     L9591				;
											;
9569:          ADDA    L4F2A				; 0  Msec ADD'NL DELAY IF IN DRIVE & COOL LO
956C:          ADDB    L4F2B				; 0  Sec's, ADD'NL DELAY IF DRIVE & COOL LO

956F:          BRA     L9591
		;----------------------------------------

9571:  L9571   BCLR    L0036,#$02			; CLR b1, DRIVE
9574:          BITB    #$02					; b1, 
9576:          BEQ     L95A1				;
											;
9578:          LDAA    L4F26
957B:          PSHA    
957C:          LDAA    L4F28
957F:          LDAB    L4F27
9582:          XGDX    
9583:          LDAA    L0006				; COOL VALUE
9585:          CMPA    L4F29
9588:          XGDX    
9589:          BCC     L9591				;
											;
958B:          ADDA    L4F2C				; 0 msec'S Add'nl DELAY IF PK/NEUT & COOL LOW
958E:          ADDB    L4F2D				; 0 Sec's  Add'nl DELAY IF PK/NEUT & COOL LOW
9591:  L9591   STAB    L087A
9594:          ABA     
9595:          PULB    
9596:          STAB    L0879
9599:          CMPA    L0864				; msec CLSD LP ENABLE DELAY AFTER IAC QUAL'S
959C:          BLS     L95A1				;
											;
959E:          STAA    L0864				; msec CLSD LP ENABLE DELAY AFTER IAC QUAL'S
											;
95A1:  L95A1   BRSET   L0036,#$02,L95AD		; BR IF b1, DRIVE
											;
95A5:          LDAA    L02A0
95A8:          SUBA    L029D
95AB:          BRA     L95B3
		;----------------------------------------

95AD:  L95AD   LDAA    L02AA
95B0:          SUBA    L02A7
95B3:  L95B3   PULB    
95B4:          PSHB    
95B5:          BRSET   L0052,#$20,L95E2		;
											;
95B9:          BCLR    L0036,#$01			; CLR b0, A/C ON
											;
95BC:          BITB    #$01					; b0
95BE:          BEQ     L962C				;
											;
95C0:          TST     L0877
95C3:          BNE     L962C				;
											;
95C5:          LDAB    L4F0F				;
95C8:          MUL     						;
95C9:          CMPA    L4F10				; ___% MIN A/C FLOW STEP FOR ON/OFF XISTION
95CC:          BCC     L95D1				;
											;
95CE:          LDAA    L4F10				; ___% MIN A/C FLOW STEP FOR ON/OFF XISTION
95D1:  L95D1   CMPA    L4F11				; ___ FLOW MAX A/C FLOW STEP FOR ON/OFF XISTION
95D4:          BLS     L95D9				;
											;
95D6:          LDAA    L4F11				; ___ FLOW MAX A/C FLOW STEP FOR ON/OFF XISTION
											;
95D9:  L95D9   LDAB    L4F13				;
95DC:          PSHB    						;
95DD:          LDAB    L4F12				;
											
95E0:          BRA     L961C
		;----------------------------------------

95E2:  L95E2   BSET    L0036,#$01			; SET 0, A/C ON
95E5:          BITB    #$01					;
95E7:          BNE     L962C				;
											;
95E9:          LDAB    L4F22				; ___ % FLOW
95EC:          STAB    L0878


           ;-----------------------------------------------
       	;
       	; b3 = 1 = INIT A/C ON INTEGRAL CELLS TO A/C OFF CELLS 
       	; b2 = 1 =
       	; b1 = 1 = USE ETC IN DECELL FUEL CUT OFF
       	;      0 = DONT USE ETC IN DECELL FUEL CUT OFF   
	   	;
       	; b0 = 1 = MAN  TRANS IN USE,DISABLE CLSD LP IDLE IF 
       	;               QUALS NOT OK                       
       	;      0 = AUTO  TRANS IN USE,ENABLE CLSD IF RPM LOW
	   	;----------------------------------------------------
95EF:          LDAB    L4E8F				; 0000 1110, IAC MD WD #1
95F2:          BITB    #$40					; b6, 
95F4:          BEQ     L9601				; BR IF NOT b6
											;
95F6:          LDX     #$4F14				; -40 Deg c (A/C VALUE)
95F9:          LDAA    L022F				; LINEAR IAT VALUE
95FC:          JSR     LF4A4

95FF:          BRA     L9615
		;----------------------------------------

9601:  L9601   LDAB    L4F1C				; __ % FLOW STEP OFF/ON MULT
9604:          MUL     
9605:          CMPA    L4F1D				; ___% FLOW MIN STEP FOR A/C OFF/ON
9608:          BCC     L960D				;
											;
960A:          LDAA    L4F1D				; ___% FLOW MIN STEP FOR A/C OFF/ON
960D:  L960D   CMPA    L4F1E				; ___% FLOW MAX STEP FOR A/C OFF/ON
9610:          BLS     L9615				;
											;
9612:          LDAA    L4F1E				; ___% FLOW MAX STEP FOR A/C OFF/ON
9615:  L9615   LDAB    L4F20
9618:          PSHB    

9619:          LDAB    L4F1F
961C:  L961C   STAA    L0876

961F:          STAB    L0877

9622:          PULA    
9623:          ABA     
9624:          CMPA    L0864				; msec CLSD LP ENABLE DELAY AFTER IAC QUAL'S
9627:          BLS     L962C				;
											;
9629:          STAA    L0864				; msec CLSD LP ENABLE DELAY AFTER IAC QUAL'S
962C:  L962C   PULA    
962D:          PSHA    
962E:          EORA    L0036
9630:          ANDA    #$03					; b0,1 A/C ON, DRIVE
9632:          BNE     L9637				; BR IF A/C ON & DRIVE
											;
9634:          PULA    

9635:          BRA     L969E
		;----------------------------------------

9637:  L9637   LDAB    L0036
9639:          BITB    #$02					; b1, DRIVE
963B:          BNE     L9659				; BR IF b1, DRIVE
											;
963D:          BITB    #$01					; b0, A/C ON
963F:          BNE     L964D				; BR IF b0, A/C ON
											;
9641:          BRCLR   L0038,#$01,L9673		;
											;
9645:          LDX     L088F
9648:          STX     L029D

964B:          BRA     L9673
		;----------------------------------------

964D:  L964D   BRCLR   L0038,#$02,L9673		;
											; 
9651:          LDX     L0891
9654:          STX     L02A0
9657:          BRA     L9673
		;----------------------------------------

9659:  L9659   BITB    #$01					;
965B:          BNE     L9669				;
											;
965D:          BRCLR   L0038,#$04,L9673		;
											;
9661:          LDX     L0895				;
9664:          STX     L02A7				;
9667:          BRA     L9673				;
		;----------------------------------------

9669:  L9669   BRCLR   L0038,#$08,L9673		;
											;
966D:          LDX     L0897				;
9670:          STX     L02AA				;

9673:  L9673   PULB    						;
9674:          BRCLR   L0038,#$10,L969B		; 
											;
9678:          LDAA    L02A5				;
967B:          ORAA    L02AF				;
967E:          BEQ     L9698				; 
											;
9680:          EORB    L0036				;
9682:          BITB    #$02					; b1, DRIVE
9684:          BEQ     L969B				; BR IF NOT b1, DRIVE
											;
9686:          BRSET   L0036,#$02,L9692		; BR IF b1, DRIVE
											;
968A:          LDD     L0893
968D:          STD     L02A3

9690:          BRA     L9698
		;----------------------------------------

9692:  L9692   LDD     L0899
9695:          STD     L02AD

9698:  L9698   BCLR    L0038,#$10			; CLR b4,
969B:  L969B   BCLR    L0038,#$0F			; CLR 0000 1111

969E:  L969E   LDAA    L4E90				; IAC MD WD #2, 0000 0001
96A1:          BITA    #$02					; b1,  1 = PWR STEER SW IN USE
96A3:          BEQ     L96C2				; BR IF NOT b1
											;
96A5:          JSR     L9247				;
96A8:          BCC     L96BF				; 
											;
96AA:          BSET    L0036,#$20			;
											;
96AD:          LDAA    L4F2E				; 0% ADDED AIR FOR PWR STEER
96B0:          STAA    L087B				;
											;
96B3:          LDAA    L4F30 				; 0 Sec's, DECAY PERIOD FOR PWR STEER
96B6:          STAA    L087C				; Decay period for pwr steer
											;
96B9:          LDAA    L4F2F				; 0 SEC'S FOR PWR STEER SIG = 1
96BC:          STAA    L0864 				; msec CLSD LP ENABLE DELAY AFTER IAC QUAL'S
											;
96BF:  L96BF   BCLR    L0036,#$20			; CLR b5


			;----------------------------------------------
			; HOUSE KEEP  TMR
			;
			;----------------------------------------------
96C2:  L96C2   LDAA    L087A				;
96C5:          BNE     L96CC				; BR IF TIMER = Z 
											;
96C7:          STAA    L0879

96CA:          BRA     L96D0
		;----------------------------------------

96CC:  L96CC   DECA    						; DECR TIMER (40d = 1 Sec)    
96CD:          STAA    L087A
			;----------------------------------------------

			;----------------------------------------------
			; HOUSE KEEP TMR
			;
			;----------------------------------------------
96D0:  L96D0   LDAA    L0877
96D3:          BEQ     L96D9				; 
											;
96D5:          DECA    		    			; DECR TIMER (40d = 1 Sec)
96D6:          STAA    L0877
			;----------------------------------------------


			;----------------------------------------------
			; HOUSE KEEP STALL SVR DELAY TO RE-ENABLE, DRIVE TMR
			;
			;----------------------------------------------
96D9:  L96D9   LDAA    L0869				; STALL SVR DELAY TO RE-ENABLE, DRIVE
96DC:          BNE     L96E3				; BR IF TIMER = Z
											;
96DE:          BCLR    L0036,#$10			; CLR b4

96E1:          BRA     L96E7
		;----------------------------------------

96E3:  L96E3   DECA    						; DECR TIMER (40d = 1 Sec)
96E4:          STAA    L0869			   	; STALL SVR DELAY TO RE-ENABLE, DRIVE
			;----------------------------------------------

			;----------------------------------------------
			; HOUSE KEEP FILTERED TPS DELAY TMR
			;
			;----------------------------------------------
96E7:  L96E7   LDAA    L0884				; FILTERED TPS DELAY TMR
96EA:          BEQ     L96F0				; BR IF TIME = Z 
											;
96EC:          DECA    						; DECR TIMER
96ED:          STAA    L0884				; FILTERED TPS DELAY TMR
			;----------------------------------------------


96F0:  L96F0   LDAA    L0063				; RPM/12.5
96F2:          SUBA    L0857  				; DESIRED IDLE RPM/12.5
											;
96F5:          BSET    L0036,#$80		    ; SET IDLE RPM TOO HIGH
											;
96F8:          BCC     L96FE				; BR IF NO UNDERFLOW 
											;
96FA:          NEGA    
96FB:          BCLR    L0036,#$80			; CLR IDLE RPM TOO HIGH
96FE:  L96FE   STAA    L0858				; RPM ERROR/12.5

9701:          CLRB    
9702:          TST     L087A
9705:          BEQ     L970A				; 
											;
9707:          LDAB    L4F80				; 0 RPM, Pk/Drv Xisition (IAC)
970A:  L970A   TST     L0877
970D:          BEQ     L9717				; 
											;
970F:          CMPB    L4F81				; 0 RPM, A/C Xisition, (IAC)
9712:          BCC     L9717				; 
											;
9714:          LDAB    L4F81				; 0 RPM, A/C Xisition, (IAC)
9717:  L9717   TST     L087C			   	; Decay period for pwr steer
971A:          BEQ     L9724				; 
											;
971C:          CMPB    L4F82				; 0 RPM, Pwr Steer Sw = 1 (IAC)
971F:          BCC     L9724				; 
											;
9721:          LDAB    L4F82
9724:  L9724   PSHB    
9725:          LDAB    L0882
9728:          CMPB    L0885
972B:          PULB    
972C:          BLS     L9736				; BR IF
											;
972E:          CMPB    L4F7F				; 500 RPM, TPS OPEN, (IAC)
9731:          BCC     L9736				; 
											;
9733:          LDAB    L4F7F				; 500 RPM, TPS OPEN, (IAC)
9736:  L9736   TSTB    						;
9737:          BEQ     L973D				; 
											;
9739:          TBA     
973A:          CLRB    

973B:          BRA     L9746
		;----------------------------------------

			;
			; FILTER RPM 
			; (COEF IN B REG, RPM IN A REG)
			;
973D:  L973D   LDX     L0859				; GET OLD RPM
9740:          LDAB    L4F7E				; 1.25 COEF FOR RPM VARIATIONS
9743:          JSR     LF459				; LAG FILT
9746:  L9746   STD     L0859				; SAVE FILTERED RPM

9749:          JSR     L99C5
974C:          JSR     L9C20
974F:          JSR     L9CA6

9752:          LDD     L0862
9755:          ADDD    L0871
9758:          BCC     L975D				; 
											;
975A:          LDD     #$FFFF
975D:  L975D   BRSET   L0036,#$80,L976B		; BR IF b7, IDLE RPM TOO HIGH
9761:          ADDA    L086D
9764:          BCC     L9772				; 
											;
9766:          LDD     #$FFFF
9769:          BRA     L9772
		;----------------------------------------

976B:  L976B   SUBA    L086D
976E:          BCC     L9772				; 
											;
9770:          CLRA    						;
9771:          CLRB    						;
											;
9772:  L9772   BRCLR   L0037,#$80,L9780		; BR IF NOT b7, ADD DERIV TERM 
											;				TO g/SEC FLOW, (0 = SUB)
											;
9776:          ADDA    L0870				;
9779:          BCC     L9787				; 
											;
977B:          LDD     #$FFFF

977E:          BRA     L9787
		;----------------------------------------

9780:  L9780   SUBA    L0870
9783:          BCC     L9787				; 
											;
9785:          CLRA    
9786:          CLRB    
9787:  L9787   ADDA    L086B
978A:          BCS     L9791				; 
											;
978C:          ADDA    L087B
978F:          BCC     L9794				; 
											;
9791:  L9791   LDD     #$FFFF
9794:  L9794   TST     L0876
9797:          BEQ     L97AE				; 
											;
9799:          BRCLR   L0036,#$01,L97A7		; BR IF NOT b0, A/C ON

979D:          ADDA    L0876				
97A0:          BCC     L97AE				; 
											;
97A2:          LDD     #$FFFF
97A5:          BRA     L97AE
		;----------------------------------------

97A7:  L97A7   SUBA    L0876
97AA:          BCC     L97AE				; 
											;
97AC:          CLRA    
97AD:          CLRB    
97AE:  L97AE   ADDA    L0879
97B1:          BCC     L97B6				; 
											;
97B3:          LDD     #$FFFF
97B6:  L97B6   LDX     L087D
97B9:          STD     L087D
97BC:          PSHA    
97BD:          LDAA    L01D9				; %TPS
97C0:          CMPA    L50A9
97C3:          PULA    
97C4:          BCC     L97D2				; 
											;
97C6:          PSHX    
97C7:          TSX     
97C8:          SUBD    0,X
97CA:          PULX    
97CB:          BCS     L97D2				; 
											;
97CD:          CMPA    L50A8
97D0:          BCC     L97D5				; 
											;
97D2:  L97D2   CLRA    

97D3:          BRA     L97E3
		;----------------------------------------

97D5:  L97D5   ASLD    
97D6:          BCS     L97DB				; 
											;
97D8:          ASLD    
97D9:          BCC     L97DD				; 
											;

    		;------------------------------------------------------
    		; Acell Enrich vs Diff IAC %Flow 
    		;   
			;                        
			; TBL = 16.384 * Msec       
    		;------------------------------------------------------
97DB:  L97DB   LDAA    #255
97DD:  L97DD   LDX     #$50A2				; Acell Enrich TBL
97E0:          JSR     LF4B6				; 2D LK UP

97E3:  L97E3   STAA    L087F


97E6:          LDD     L087D
97E9:          ADDA    L0880
97EC:          BCC     L97F3
											;
97EE:          LDD     #$FFFF

97F1:          BRA     L9830
		;----------------------------------------

97F3:  L97F3   BRCLR   L0046,#$08,L981A		; BR IF NOT b3, DECEL FUEL C/O
											; 
97F7:          PSHB    
97F8:          PSHA    

		;--------------------------------------------------
		;  TABLE
		;
		;
		;--------------------------------------------------
97F9:          LDX     #$50AD
97FC:          LDAA    L0062

97FE:          JSR     LF4C1				; 2d LK UP
9801:          SUBA    L50AC				; TBL CONSTANT
9804:          BCS     L980B				;
											;
9806:          BCLR    L0038,#$20

9809:          BRA     L980F
		;----------------------------------------

980B:  L980B   BSET    L0038,#$20

980E:          NEGA    
980F:  L980F   STAA    L0887

9812:          LDAA    L50BF				; 100 MSec's decay rate
9815:          STAA    L0888

9818:          PULA    
9819:          PULB    
981A:  L981A   BRSET   L0038,#$20,L9828		; BR IF b5, 
											;
981E:          ADDA    L0887
9821:          BCC     L9830
											;
9823:          LDD     #$FFFF
9826:          BRA     L9830
		;----------------------------------------

9828:  L9828   SUBA    L0887
982B:          BCC     L9830
											;
982D:          LDD     #$0000

9830:  L9830   BRCLR   L003D,#$20,L983D		; BR IF NOT b5, PWR ENR IS ACTIVE
											;
9834:          CPD     L50AA				; 65535d
9838:          BLS     L983D
											;
983A:          LDD     L50AA				; 65535d
983D:  L983D   STD     L0889

        ;---------------------------------------------
        ; IAC ALTITUDE COMP
        ;
        ; TABLE = FACTOR * 128
        ;---------------------------------------------
9840:          LDX     #$4EA3
9843:          LDAA    L01CC				; BARO VALUE (Kpa)
9846:          JSR     LF4A4

9849:          LDX     #$0889				; 2185
984C:          JSR     LF550				; MUL 8X16 Subroutine
984F:          ASLD    
9850:          BCC     L9855
9852:          LDD     #$FFFF


        ;---------------------------------------------
       	;
       	; b3 = 1 = INIT A/C ON INTEGRAL CELLS TO A/C OFF CELLS 
       	; b2 = 1 =
       	; b1 = 1 = USE ETC IN DECELL FUEL CUT OFF
       	;      0 = DONT USE ETC IN DECELL FUEL CUT OFF   
	   	;
       	; b0 = 1 = MAN  TRANS IN USE,DISABLE CLSD LP IDLE IF 
       	;               QUALS NOT OK                       
       	;      0 = AUTO  TRANS IN USE,ENABLE CLSD IF RPM LOW
	   	;---------------------------------------------
9855:  L9855   LDX     #$4E8F				; 0000 1110, IAC MD WD #1
9858:          BRCLR   0,X,#$04,L9880		; BR IF NOT b2, 
											;
985C:          BRCLR   L0037,#$04,L986C		; BR IF NOT b2, THROTTLE KICKER ACTIVE
											;
9860:          SUBA    L50C8
9863:          BCC     L986C
9865:          BSET    L0037,#$08			; SET B3, THROTTLE KICKER DISABLE REQUESTED

9868:          CLRA    
9869:          CLRB    
986A:          BRA     L9880
		;----------------------------------------

986C:  L986C   XGDX    
986D:          PSHX    
986E:          PSHX    
986F:          TSX     
9870:          LDAA    L50C9				; 50% FACTOR, TPS KICKER
9873:          JSR     LF550				; MUL 8X16 Subroutine
9876:          PULX    
9877:          TSX     
9878:          ADDD    0,X
987A:          PULX    
987B:          BCC     L9880

987D:          LDD     #$FFFF
9880:  L9880   STD     L088B

9883:          LDX     #$4E92
9886:          LSRD    
9887:          LSRD    
9888:          LSRD    
9889:          LSRD    
988A:          ADCB    #$0000
988C:          ADCA    #$0000
988E:          PSHB    
988F:          TAB     
9890:          ABX     
9891:          LDD     0,X
9893:          SBA     
9894:          PULB    
9895:          NEGA    
9896:          MUL     
9897:          ADCA    0,X
9899:  L9899   STAA    L0008
989B:  L989B   RTS     
 ; ------------------------------------------
989C:  L989C   BRCLR   L0038,#$40,L98A3
98A0:          JMP     L99C4
 ;
98A3:  L98A3   LDAA    L0283				; RANGE LMT'ED COOL (-28 - 104c)
98A6:          CMPA    #160
98A8:          BLS     L98AF

98AA:          SUBA    #160
98AC:          ASLA    
98AD:          ADDA    #160

98AF:  L98AF   BRCLR   L0036,#$01,L98BF		; BR IF NOT b0, A/C ON
											;
    	;-----------------------------------
    	; DESIRED RPM IDLE vs COOLANT
    	; (PK.NEUT & A/C ON)
    	; 
    	;  TBL =  .08  * RPM/12.5
    	;-----------------------------------
98B3:          LDX     #$4F41				; INDEX DESIRED RPM IDLE
											;
98B6:          BRCLR   L0036,#$02,L98C9		; BR IF NOT b1, DRIVE
											;

    	;-----------------------------------
    	; DESIRED RPM IDLE vs COOLANT
    	; (IN DRIVE & A/C ON)
    	;
    	;  TBL =  .08  * RPM/12.5
    	;-----------------------------------
98BA:          LDX     #$4F5F				; INDEX DESIRED RPM IDLE
98BD:          BRA     L98C9
		;----------------------------------------

    	;-----------------------------------
    	; DESIRED RPM IDLE vs COOLANT
    	; (PK.NEUT & A/C OFF)
    	; 
    	; TBL = RPM/12.5
    	;-----------------------------------
98BF:  L98BF   LDX     #$4F32				; INDEX DESIRED RPM IDLE

98C2:          BRCLR   L0036,#$02,L98C9		; BR IF NOT b1, DRIVE
											;
    	;-----------------------------------
    	; DESIRED RPM IDLE vs COOLANT
    	; (IN DRIVE & A/C OFF)
    	; 
    	; TBL = RPM/12.5
    	;-----------------------------------
98C6:          LDX     #$4F50

98C9:  L98C9   JSR     LF4C1				; 2d LK UP
    	;-----------------------------------


98CC:          PSHA    
98CD:          LDAB    L4F84
98D0:          SUBB    L00A7    			; BAT VOLTS, VDC/10
98D2:          BLS     L98E3
98D4:          LDAA    L4F85
98D7:          MUL     
98D8:          CMPA    L4F86
98DB:          BCS     L98E0
98DD:          LDAA    L4F86
98E0:  L98E0   PULB    
98E1:          ABA     
98E2:          PSHA    
98E3:  L98E3   LDAB    L0859				; RPM

98E6:          LDAA    L4F7D				; 99.6 GAIN (RPM/RPM) FOR UNSTABLE IDLE
98E9:          MUL     						; APPLY MULTIPLIER
98EA:          CMPA    L4F83				; 38 RPM, MAX DESIRED RPM DIFF FOR ROUGH IDLE
98ED:          BCS     L98F2				; BR IF ....
											;
98EF:          LDAA    L4F83 				; 38 RPM, MAX DESIRED RPM DIFF FOR ROUGH IDLE
98F2:  L98F2   PULB    
98F3:          ABA     
98F4:          LDAB    L0247			 	; BLM CELL
98F7:          CMPB    #16					; CELL 16 ?
98F9:          BCS     L990A				; BR IF CURRENT CELL LT 16
											;
98FB:          LDAB    L0248 				; CURRENT BLM
98FE:          CMPB    L4F87				; 118, MAX BLM THRESH FOR ADDING HOT IDLE PURGE COMP 
9901:          BCC     L990A				; BR IF 
											;
9903:          LDAB    L0006				; COOL VALUE
9905:          CMPB    L4F89				; 105 c, THRESH FOR HOT IDLE PURGE COMP
9908:          BHI     L990F				; BR IF 
											;
990A:  L990A   CLR     L085B

990D:          BRA     L993D
		;----------------------------------------

990F:  L990F   LDAB    L085B
9912:          CMPB    L4F88				; 5 Sec's MIN WAIT AT HOT IDLE FOR ADDING
											;	       PURGE COMP
9915:          BCC     L9922				; BR IF 
											;
9917:          BRCLR   L0002,#$F0,L991D		; BR IF NOT 1111 0000,  MAJOR LOOP COUNTER
											;
991B:          BRA     L993D
		;----------------------------------------

991D:  L991D   INC     L085B

9920:          BRA     L993D
		;----------------------------------------

9922:  L9922   BRSET   L0036,#$02,L9932		; BR IF b1, DRIVE 
											;
9926:          LDAB    L4F8A				; 50 RPM HOT IDLE PURGE COMP, Pk/Necu, A/C OFF
9929:          BRCLR   L0036,#$01,L993C		; BR IF NOT b0, A/C ON
											;
992D:          LDAB    L4F8B				; 50 RPM HOT IDLE PURGE COMP, Pk/Necu, A/C ON

9930:          BRA     L993C
		;----------------------------------------

9932:  L9932   LDAB    L4F8C				; 25 RPM HOT IDLE PURGE COMP, Drive, A/C OFF
											;
9935:          BRCLR   L0036,#$01,L993C		; BR IF NOT b1, A/C ON
											;
9939:          LDAB    L4F8D				; 25 RPM HOT IDLE PURGE COMP, Drive, A/C ON
993C:  L993C   ABA     
993D:  L993D   PSHA    
993E:          LDAA    L085C
9941:          BEQ     L994E				; BR IF
											;
9943:          BRSET   L0036,#$02,L994E		; BR IF b1, DRIVE 
											;
9947:          ASLA    						;
9948:          LDAB    L4EBC				; 100 % PK/NUT MULT TO L4F__ DRIVE MULT TBL
994B:          MUL     
994C:          ADCA    #$00
994E:  L994E   PULB    
994F:          ABA     
9950:          CMPA    L085F
9953:          BCC     L9959				; BR IF
											;
9955:          LDAA    L085F
9958:          DECA    
9959:  L9959   STAA    L085F

995C:          LDX     #$4E8F				; 0000 1110, IAC MD WD #1
995F:          BRCLR   0,X,#$10,L99A8		; BR IF NOT b4, A/C HI PRESSURE SW IN USE 
											;
9963:          LDAB    L4F8E				; 0 RPM MAX REQUESTED, HI A/C HEAD PRESS, Pk/Neut
9966:          BRCLR   L0036,#$02,L996D		; BR IF NOT b1, DRIVE 
											;
996A:          LDAB    L4F8F				; 0 RPM MAX REQUESTED, HI A/C HEAD PRESS, Drive
996D:  L996D   CBA     						;
996E:          BCS     L9973				; BR IF
											;
9970:          CLRA    

9971:          BRA     L999C
		;----------------------------------------

9973:  L9973   JSR     L9250
9976:          BCS     L9988

9978:          LDAA    L0860
997B:          BEQ     L9983				; BR IF
											;
997D:          LDAB    L0861
9980:          BNE     L9998				; BR IF
											;
9982:          DECA    
9983:  L9983   LDAB    L4F91				; 0 Sec's, PERIOD TO INCR RPM FOR
											;		   HI PRESS IF LO LOAD
9986:          BRA     L999F
		;----------------------------------------

9988:  L9988   CMPB    L0857  				; DESIRED IDLE RPM/12.5
998B:          BHI     L9990				; BR IF
											;
998D:          TBA     

998E:          BRA     L99A8
		;----------------------------------------

9990:  L9990   LDAA    L0860
9993:          LDAB    L0861
9996:          BEQ     L999B				; BR IF
											;
9998:  L9998   DECB    

9999:          BRA     L999F
		;----------------------------------------

999B:  L999B   INCA    
999C:  L999C   LDAB    L4F90				; 0 Sec's, PERIOD TO INCR RPM FOR
											;			 HI PRESS IF HI LOAD
999F:  L999F   STAA    L0860

99A2:          ADDA    L085F
99A5:          STAB    L0861
99A8:  L99A8   STAA    L0857  				; DESIRED IDLE RPM/12.5
		
		;--------------------------------------------------			 
		; RPM DIFF QUAL FOR STALL SAVER TBL
		; TBL = RPM DIFF * 2.56
		;--------------------------------------------------			 
99AB:          LDX     #$504D
99AE:          LDAB    #$0003
99B0:          ANDB    L0036				; MASK b0,b1 DRIVE & A/C ON
99B2:          ABX     

99B3:          LDAB    L4E8F				; 0000 1110, IAC MD WD #1
99B6:          BITB    #$80					; b7,  STALL SVR THRESH ARE RPM
99B8:          BEQ     L99BE				; BR IF NOT b7
											;
99BA:          LDAA    0,X
99BC:          BRA     L99C1
		;----------------------------------------

99BE:  L99BE   LDAB    0,X
99C0:          MUL     
99C1:  L99C1   STAA    L0868
99C4:  L99C4   RTS     
 ; ------------------------------------------
99C5:  L99C5   LDX     #$02A7

99C8:          BRSET   L0036,#$02,L99CF		; BR IF b1, DRIVE 
											;
99CC:          LDX     #$029D
99CF:  L99CF   LDD     3,X

99D1:          BRSET   L0036,#$01,L99D7		; BR IF b0, A/C ON
											;
99D5:          LDD     0,X
99D7:  L99D7   PSHB    
99D8:          PSHA    
99D9:          LDD     6,X
99DB:          PSHB    
99DC:          PSHA    
99DD:          CLRB    
99DE:          PSHB    
99DF:          PSHB    
99E0:          TSY     

99E2:          LDAA    L01D9				; %TPS
99E5:          CMPA    L4EF2				; 16% TPS UPPR LMT FOR CLSD, (IAC)
99E8:          BCS     L99EF				; BR IF %TPS LT THRESH
											;
99EA:          BSET    L0039,#$80			; SET b7, 

99ED:          BRA     L99FA
		;----------------------------------------

99EF:  L99EF   BCLR    L0039,#$80

99F2:          LDAA    L0284				; MPH/1
99F5:          CMPA    L4EF3				; 2  MPH UPPER LMT FOR IAC CLSD
99F8:          BCS     L9A05				; BR IF Vss LT 
											;
99FA:  L99FA   LDAB    L4EF4				; 500 Msec CLSD LP ENABLE DELAY AFTER IAC QUAL'S
99FD:          STAB    L0864				; msec CLSD LP ENABLE DELAY AFTER IAC QUAL'S

9A00:          BCLR    L0036,#$04			; CLR b2

9A03:          BRA     L9A2D
		;----------------------------------------

9A05:  L9A05   BSET    L0036,#$04			; SET b2, 

9A08:          LDAA    L0882
9A0B:          CMPA    L0885
9A0E:          BHI     L9A2D				; BR IF 
											;
9A10:          LDAA    L0864				; msec CLSD LP ENABLE DELAY AFTER IAC QUAL'S
9A13:          BEQ     L9A1B				; BR IF TIMER = Z
											;
9A15:          DECA    						; DECR TIMER
9A16:          STAA    L0864				; msec CLSD LP ENABLE DELAY AFTER IAC QUAL'S

9A19:          BRA     L9A2D
		;----------------------------------------

9A1B:  L9A1B   BRSET   L0036,#$80,L9A26		; BR IF b7, IDLE RPM TOO HIGH
9A1F:          LDAA    L0866
9A22:          BEQ     L9A47				;
											;
9A24:          BRA     L9A58
		;----------------------------------------

9A26:  L9A26   LDAA    L0867
9A29:          BEQ     L9A47				;
											;
9A2B:          BRA     L9A58
		;----------------------------------------

9A2D:  L9A2D   BRSET   L0036,#$80,L9A58		; BR IF b7, IDLE RPM TOO HIGH
9A31:          LDAA    L0866
9A34:          ORAA    L087A
9A37:          ORAA    L0877
9A3A:          BNE     L9A58
9A3C:          BRSET   L0036,#$04,L9A47


        ;---------------------------------------------
       	;
       	; b3 = 1 = INIT A/C ON INTEGRAL CELLS TO A/C OFF CELLS 
       	; b2 = 1 =
       	; b1 = 1 = USE ETC IN DECELL FUEL CUT OFF
       	;      0 = DONT USE ETC IN DECELL FUEL CUT OFF   
	   	;
       	; b0 = 1 = MAN  TRANS IN USE,DISABLE CLSD LP IDLE IF 
       	;               QUALS NOT OK                       
       	;      0 = AUTO  TRANS IN USE,ENABLE CLSD IF RPM LOW
	   	;---------------------------------------------
9A40:          LDAA    L4E8F				; 0000 1110, IAC MD WD #1
9A43:          BITA    #$01					; b0, 
9A45:          BNE     L9A58


9A47:  L9A47   BRSET   L003E,#$04,L9A58		; BR IF b2, LOW BATTERY
											;
9A4B:          BRCLR   L0037,#$04,L9A5E		; BR IF NOT b2, TTHROTTLE KICKER ACTIVE
											;
9A4F:          LDD     L088B
9A52:          BNE     L9A5E	   			;
											;
9A54:          BRCLR   L0036,#$80,L9A5E		; BR IF NOT b7, IDLE RPM TOO HIGH
											;
9A58:  L9A58   BCLR    L0036,#$08

9A5B:          JMP     L9C06
 

9A5E:  L9A5E   BSET    L0036,#$08			;
											;
9A61:          BRCLR   L0036,#$10,L9A6D	   	; BR IF not b4,
											;
9A65:          BRCLR   L0036,#$80,L9A9F		; BR IF NOT b7, IDLE RPM TOO HIGH
											;
9A69:          CLRA    
9A6A:          CLRB    

9A6B:          BRA     L9A8D
		;----------------------------------------

9A6D:  L9A6D   LDAA    L0868
9A70:          CMPA    L0063				; RPM/12.5
9A72:          BLS     L9A9F	   			;
											;
9A74:          BSET    L0036,#$10
9A77:          PSHX    
				;------------------------------------------

				;------------------------------------------
				;
				;
				;
				;------------------------------------------
9A78:          LDX     #$5051
9A7B:          LDAB    #$03
9A7D:          ANDB    L0036				; MASK b0,1 A/C ON & DRIVE
9A7F:          ABX     						; 
9A80:          LDAA    0,X
9A82:          PULX    
9A83:          LDAB    L5055				; 1.5 Sec's STALL SVR DELAY TO RE-ENABLE, PK/NEUT

9A86:          BRCLR   L0036,#$02,L9A8D		; BR IF NOT b1, DRIVE

9A8A:          LDAB    L5056				; 1.5 Sec's STALL SVR DELAY TO RE-ENABLE, DRIVE

9A8D:  L9A8D   STAB    L0869				; STALL SVR DELAY TO RE-ENABLE, DRIVE
9A90:          CLRB    
9A91:          ADDD    4,Y
9A94:          BCC     L9A99	   			;
											;
9A96:          LDD     #$FFFF
9A99:  L9A99   STD     4,Y

9A9C:          JMP     L9BDA
 ;
9A9F:  L9A9F   LDAA    L0858				; RPM ERROR/12.5
9AA2:          CMPA    #40
9AA4:          BLS     L9AAA	   			;
											;
9AA6:          LDAA    #$00A0
9AA8:          BRA     L9ABE
		;----------------------------------------

9AAA:  L9AAA   ASLA    
9AAB:          CMPA    #$20
9AAD:          BLS     L9AB3
9AAF:          ADDA    #$0050
9AB1:          BRA     L9ABE
		;----------------------------------------

9AB3:  L9AB3   ASLA    
9AB4:          CMPA    #$10
9AB6:          BLS     L9ABC	   			;
											;
9AB8:          ADDA    #$30

9ABA:          BRA     L9ABE
		;----------------------------------------

9ABC:  L9ABC   ASLA    
9ABD:          ASLA    
9ABE:  L9ABE   PSHX    
9ABF:          BRSET   L0036,#$80,L9ACF		; BR IF b7, IDLE RPM TOO HIGH

9AC3:          LDX     #$4FA8

9AC6:          BRSET   L0036,#$02,L9AD9		; BR IF b1, DRIVE
											;

        ;---------------------------------------------
		; IDLE INTEGRAL GAIN vs RPM ERROR
		; 	(LOW RPM & PK/NEUT)
		;
    	;  TYPE $31 PCM
		;
		; TBL = GAIN * 0.488
        ;---------------------------------------------
9ACA:          LDX     #$4F92

9ACD:          BRA     L9AD9
		;----------------------------------------

9ACF:  L9ACF   LDX     #$4FB3

9AD2:          BRSET   L0036,#$02,L9AD9		; BR IF b1, DRIVE
											;
9AD6:          LDX     #$4F9D				; IDLE INTEGRAL GAIN vs RPM ERROR TBL
9AD9:  L9AD9   JSR     LF4C1				; 2d LK UP
											;
9ADC:          PULX    						;
9ADD:          LDAB    L0858				; RPM ERROR/12.5
9AE0:          MUL     						;
9AE1:          STD     0,Y					;
											;
9AE4:          BRSET   L0036,#$80,L9B4E		; BR IF NOT b7, IDLE RPM TOO HIGH
											;
9AE8:          LDAA    L0006				; COOL VALUE
9AEA:          CMPA    L50C2				; 72.5c COOL, IAC HI OUT OF POSIT COOL THRESH 
9AED:          BLS     L9B16				; BR IF COOL ...
											;
9AEF:          LDAA    L50C3				; 39% FLOW MAX IDLE INTEGRAL FOR NO A/C
											;
9AF2:          BRCLR   L0036,#$01,L9AF9	   	; BR IF NOT b0, A/C ON
											;
9AF6:          LDAA    L50C4				; 56.4% FLOW MAX IDLE INTEGRAL FOR A/C ON
9AF9:  L9AF9   CMPA    4,Y					;
9AFC:          BCC     L9B16				;
											;
9AFE:          BRSET   L003B,#$10,L9B16	   	;
											;
9B02:          BRSET   L0050,#$10,L9B16	   	;
											;
9B06:          BCLR    L0009,#$04			; CLR b2, R/S REQUESTED IF BIT CLEAR
											;
9B09:          LDAA    L0002				; MAJOR LOOP COUNTER
9B0B:          CMPA    L50C6
9B0E:          BCC     L9B13
											;
9B10:          DEC     L0007				; IAC MOTOR POSIT

9B13:  L9B13   JMP     L9C06
 

9B16:  L9B16   LDD     L088B
9B19:          CPD     #$FFFF
9B1D:          BEQ     L9B7C	   			;
											;
9B1F:          LDAA    2,X					;
											;
9B21:          BRCLR   L0036,#$01,L9B27	   	; BR IF NOT b0, A/C ON
											;
9B25:          LDAA    $0005,X
9B27:  L9B27   CMPA    $0004,Y
9B2A:          BHI     L9B40
9B2C:          LDD     6,X
9B2E:          CPD     8,X
9B31:          BCC     L9B40
9B33:          ADDD    0,Y
9B36:          BCC     L9B3B
9B38:          LDD     #$FFFF
9B3B:  L9B3B   STD     $0002,Y
9B3E:          BRA     L9B7C
		;----------------------------------------

9B40:  L9B40   LDD     $0004,Y
9B43:          ADDD    0,Y
9B46:          BCC     L9B4B
9B48:          LDD     #$FFFF
9B4B:  L9B4B   JMP     L9BDA
 ;
9B4E:  L9B4E   LDAA    L087B
9B51:          BEQ     L9B66
9B53:          SUBA    0,Y
9B56:          BCC     L9B5B
9B58:          CLRA    
9B59:          BRA     L9B61
		;----------------------------------------

9B5B:  L9B5B   CMPA    L087B
9B5E:          BNE     L9B61
9B60:          DECA    
9B61:  L9B61   STAA    L087B
9B64:          BRA     L9B7C
		;----------------------------------------

9B66:  L9B66   LDAA    L086B
9B69:          BEQ     L9B7F
9B6B:          SUBA    0,Y
9B6E:          BCC     L9B73
9B70:          CLRA    
9B71:          BRA     L9B79
		;----------------------------------------

9B73:  L9B73   CMPA    L086B
9B76:          BNE     L9B79
9B78:          DECA    
9B79:  L9B79   STAA    L086B
9B7C:  L9B7C   JMP     L9C06
 ;
9B7F:  L9B7F   LDD     $0004,Y
9B82:          SUBD    0,Y
9B85:          BCC     L9B8A
9B87:          LDD     #$0000

			;
			; ERR WD
			;
9B8A:  L9B8A   BRSET   L0016,#$10,L9BB1		; BR IF b4, ERR
9B8E:          PSHX    
9B8F:          LDX     2,Y
9B92:          PULX    
9B93:          BEQ     L9BB1
9B95:          PSHB    
9B96:          LDAB    5,X

9B98:          BRSET   L0036,#$01,L9B9E		; BR IF NOT b0, A/C ON
											;
9B9C:          LDAB    2,X
9B9E:  L9B9E   CBA     
9B9F:          PULB    
9BA0:          BCC     L9BDA
9BA2:          LDD     2,Y
9BA5:          SUBD    0,Y
9BA8:          BCC     L9BAC
9BAA:          CLRA    
9BAB:          CLRB    
9BAC:  L9BAC   STD     2,Y
9BAF:          BRA     L9C06
		;----------------------------------------

9BB1:  L9BB1   CPD     #$0000
9BB5:          BNE     L9BDA
9BB7:          BRSET   L0009,#$40,L9BDA		; BR IF b6, 1st PASS OF ERR 36 HAS FAILED

9BBB:          PSHA    
9BBC:          LDAA    L0858				; RPM ERROR/12.5
9BBF:          CMPA    L50C5
9BC2:          BLS     L9BD9
9BC4:          BRSET   L003B,#$10,L9BD9
9BC8:          BRSET   L0050,#$10,L9BD9
											;
9BCC:          BCLR    L0009,#$04			; CLR b2, R/S REQUESTED IF BIT CLEAR

9BCF:          LDAA    L0002				; MAJOR LOOP COUNTER
9BD1:          CMPA    L50C6
9BD4:          BCC     L9BD9
9BD6:          INC     L0007				; IAC MOTOR POSIT
9BD9:  L9BD9   PULA    

9BDA:  L9BDA   BRCLR   L0016,#$10,L9BF9		; BR IF NOT b4, ERR..

9BDE:          PSHB    
9BDF:          LDAB    L4EB2				; 14.8%FLOW OF IDLE CELL IN DRV AFTER NON VOL MEM FAIL 
9BE2:          BRSET   L0036,#$02,L9BE9		; BR IF b1, DRIVE
											;
9BE6:          LDAB    L4EB1				; 8.2% FLOW OF IDLE CELL IN PK AFTER
											;  NON VOL MEM FAIL
9BE9:  L9BE9   BRCLR   L0036,#$01,L9BF0 	; BR IF NOT b0, A/C ON
											;
9BED:          ADDB    L4EB3
9BF0:  L9BF0   CBA     
9BF1:          BCS     L9BF6
9BF3:          PULB    
9BF4:          BRA     L9BF9
		;----------------------------------------


9BF6:  L9BF6   TBA     
9BF7:          PULB    
9BF8:          CLRB    
9BF9:  L9BF9   STD     4,Y

9BFC:          BRCLR   L0036,#$01,L9C04 	; BR IF NOT b0, A/C ON

9C00:          STD     3,X
9C02:          BRA     L9C06
		;----------------------------------------

9C04:  L9C04   STD     0,X

9C06:  L9C06   LDD     2,Y
9C09:          STD     6,X
9C0B:          STD     L0871

9C0E:          LDD     8,X
9C10:          STD     L0873

9C13:          LDD     4,Y
9C16:          STD     L0862

9C19:          LDAB    #$06
9C1B:          ABY     
9C1D:          TYS     
9C1F:          RTS     
 		;------------------------------------------

9C20:  L9C20   BRSET   L0036,#$02,L9C30		; BR IF b1, DRIVE
											;
9C24:          LDX     #$4FCC				;

9C27:          BRCLR   L0036,#$80,L9C70		; BR IF NOT b7, IDLE RPM TOO HIGH
											;
		;--------------------------------------------------
		;  PROPORTIONAL,(%FLOW) vs RPM
		; (PK/NEUT,HI RPM)
		;
		;
		; TBL = %FLOW * 2.56
        ;---------------------------------------------
9C2B:          LDX     #$4FD7

9C2E:          BRA     L9C70
		;----------------------------------------

9C30:  L9C30   CLRB    
9C31:          BRCLR   L0036,#$01,L9C37		; BR IF NOT b0, A/C ON
											;
9C35:          ADDB    #$08

9C37:  L9C37   BRCLR   L0036,#$08,L9C3D
											;
9C3B:          ADDB    #$04
9C3D:  L9C3D   BRCLR   L0036,#$80,L9C43		; BR IF NOT b7, IDLE RPM TOO HIGH
											;
		;--------------------------------------------------
		; IAC FLOW VS RPM TABLE ADDRESSES
		;
		; TYPE $31 PCM
		;--------------------------------------------------
9C41:          ADDB    #2					;
9C43:  L9C43   LDX     #$9C96             	; INDEX IAC FLOW VS RPM TABLES
9C46:          ABX     						; ADJ INDEX 
9C47:          LDX     0,X					; GET TABLE ADDRESS
											;
9C49:          BRCLR   L0036,#$80,L9C70		; BR IF NOT b7, IDLE RPM TOO HIGH
											;
		;
		; CHECK MPH QUAL'S
		;
9C4D:          LDAA    L0284				; MPH/1
9C50:          CMPA    L4FC9				; 255 MPH
9C53:          BCS     L9C5A				; BR IF Vss LT THRESH
											; ... ese
9C55:          BSET    L0037,#$40			; SET b6, PRORP LIMITING ATHORITY BEING EXERCISED

9C58:          BRA     L9C68
		;----------------------------------------

9C5A:  L9C5A   CMPA    L4FCA				; 100 MPH
9C5D:          BCC     L9C64				; BR IF MPH GT THESH
											;
9C5F:          BCLR    L0037,#$40			; CLR b6, PRORP LIMITING ATHORITY BEING EXERCISED

9C62:          BRA     L9C70
		;----------------------------------------

9C64:  L9C64   BRCLR   L0037,#$40,L9C70	  	; BR IF NOT b6, PRORP LIMITING ATHORITY
											;				BEING EXERCISED
											;
9C68:  L9C68   LDAA    L4FCB				; 0d
9C6B:          CMPA    L0858			    ;
9C6E:          BLS     L9C73

9C70:  L9C70   LDAA    L0858
9C73:  L9C73   CMPA    #$28
9C75:  L9C75   BLS     L9C7B

9C77:          LDAA    #$A0

9C79:          BRA     L9C8F
		;----------------------------------------

9C7B:  L9C7B   ASLA    
9C7C:          CMPA    #$0020
9C7E:          BLS     L9C84
9C80:          ADDA    #$0050
9C82:          BRA     L9C8F
		;----------------------------------------

9C84:  L9C84   ASLA    
9C85:          CMPA    #$0010
9C87:          BLS     L9C8D
9C89:          ADDA    #$0030
9C8B:          BRA     L9C8F
		;----------------------------------------

9C8D:  L9C8D   ASLA    
9C8E:          ASLA    
9C8F:  L9C8F   JSR     LF4C1				; 2d LK UP
9C92:          STAA    L086D

9C95:          RTS     
		;--------------------------------------------------

        ;---------------------------------------------
    	;  IAC FLOW TABLE vs VEHICLE CONDITIONS,
		;  TYPE $31
		;
    	;  TBL = %FLOW * 2.56 vs RPM ERROR Vs SPEC'ED CONDITIONS                            
        ;---------------------------------------------
       ORG  $9C96	;
					; VEHICLE CONDITIONS
                    ;----------------------------------
L9C96   FDB $4FE2   ; DRIVE, A/C OFF, OPEN LP, IDLE, LO RPM
L9C98   FDB $4FED   ; DRIVE, A/C OFF, OPEN LP, IDLE, HI RPM

L9C9A   FDB $4FF8   ; DRIVE, A/C OFF, CLSD LP, IDLE, LO RPM
L9C9C   FDB $5003   ; DRIVE, A/C OFF, CLSD LP, IDLE HIGH RPM

L9C9E   FDB $500E   ; DRIVE, A/C OFF, CLSD LP, IDLE, LO RPM
L9CA0   FDB $5019   ; DRIVE, A/C ON,  OPEN LP, RPM HIGH

L9CA2   FCB $5024   ; DRIVE, A/C ON,  CLSD LP, IDLE, RPM LOW
L9CA4   FDB $502F   ; DRIVE, A/C ON,  CLSD LP, IDLE, RPM HIGH 					
					;
	;---------------------------------------------------
                                                             

9CA5:          BLE     L9C75
											;
9CA7:          NEGB    
9CA8:          PSHX    

9CA9:          LDAA    L006C				; RPM RATIO
9CAB:          SUBA    #96					;
9CAD:          BCC     L9CB2				; BR IF NO UNDERFLOW
											;
9CAF:          CLRA    						; USE ZERO VALUE

9CB0:          BRA     L9CBC
		;----------------------------------------

9CB2:  L9CB2   CMPA    #$40
9CB4:          BCS     L9CBA
											;
9CB6:          LDAA    #255               	; FORCE MAX VALUE

9CB8:          BRA     L9CBC
		;----------------------------------------

9CBA:  L9CBA   ASLA    
9CBB:          ASLA    
9CBC:  L9CBC   JSR     LF4C1				; 2d LK UP


9CBF:          LDX     L086E

9CC2:          CLRB    
9CC3:          CMPA    L086E
9CC6:          BEQ     L9CFC
											;
9CC8:          BRSET   L0037,#$80,L9CD4		; BR IF b7, ADD DERIV TERM 
											;				TO g/SEC FLOW, (0 = SUB)
											;
9CCC:          BHI     L9CDF
9CCE:          BRCLR   L0036,#$80,L9CDF		; BR IF NOT b7, IDLE RPM TOO HIGH
9CD2:          BRA     L9CE5
		;----------------------------------------

9CD4:  L9CD4   BCS     L9CDA

9CD6:          BRCLR   L0036,#$80,L9CE5		; BR IF NOT b7, IDLE RPM TOO HIGH
9CDA:  L9CDA   LDAB    L503A				; 0.996 COEF FOR IAC DIRIVITVE, (FAST COEF)

9CDD:          BRA     L9CE2
		;----------------------------------------

			;
			; FILTER ..
			;
9CDF:  L9CDF   LDAB    L503B				; 0.996 COEF FOR IAC DIRIVITVE, (SLOW COEF)
9CE2:  L9CE2   JSR     LF459				; LAG FILTER
9CE5:  L9CE5   STD     L086E				;

9CE8:          SUBA    #128
9CEA:          BCC     L9CF2				; BR IF FILTERED ... LT 128d

9CEC:          NEGA    						;

9CED:          BCLR    L0037,#$80			; CLR b7, ADD DERIV TERM TO g/SEC FLOW, (0 = SUB)
											;
9CF0:          BRA     L9CF5
		;----------------------------------------

9CF2:  L9CF2   BSET    L0037,#$80			; SET b7, ADD DERIV TERM TO g/SEC FLOW, (0 = SUB)
											;
9CF5:  L9CF5   LSRA    
9CF6:          LSRA    
9CF7:          ADCA    #$0000
9CF9:          STAA    L0870

9CFC:  L9CFC   RTS     
 			;------------------------------------------


9CFD:  L9CFD   LDAA    L01D9				; %TPS
9D00:          ASLA    						; TPS x 2
9D01:          BCS     L9D06				; BR IF OVERFLOW
											;
9D03:          ASLA    						; TPS x 2
9D04:          BCC     L9D08				; BR IF NO OVERFLOW
											;
9D06:  L9D06   LDAA    #255					;
9D08:  L9D08   CMPA    L0882				;
9D0B:          BLS     L9D33				;
											;
9D0D:          LDAB    L506E				;  MAX PK/NEUT TPS FOR T/F
9D10:          BRCLR   L0036,#$02,L9D2C		; BR IF NOT b1,	DRIVE
											;
9D14:          PSHA    


    		;--------------------------------------------------
    		; FILTERED TPS DELAY TMR vs Vss
    		;
    		;
    		; TBL = SEC'S * 40
    		;--------------------------------------------------
			;
			; LIMIT Vss TO 80 MPH FOR LK UP
			;
9D15:          LDAA    L0284				; MPH/1
9D18:          CMPA    #80					; 80 MPH
9D1A:          BLS     L9D1E				; BR IF Vss LT 80 MPH
											;
			;
			; LIMIT Vss TO 80 MPH FOR LK UP
			;
9D1C:          LDAA    #80 					; 80 MPH
9D1E:  L9D1E   ASLA    						; x 2

9D1F:          LDX     #$5071				; FILTERED TPS DELAY TMR TBL
9D22:          JSR     LF4C1				; 2d LK UP

9D25:          STAA    L0884				; FILTERED TPS DELAY TMR

9D28:          PULA    

9D29:          LDAB    L506F				;  50.0% MAX DRIVE TPS FOR T/F
9D2C:  L9D2C   CBA     						;
9D2D:          BLS     L9D30				;
											;
9D2F:          TBA     
9D30:  L9D30   CLRB    

9D31:          BRA     L9D6E
		;----------------------------------------

9D33:  L9D33   LDAB    L0884				; FILTERED TPS DELAY TMR
9D36:          BEQ     L9D3D				; BR IF TIME = 0
											;
9D38:          LDD     L0882

9D3B:          BRA     L9D6E
		;----------------------------------------

9D3D:  L9D3D   PSHA    
9D3E:          BRSET   L0036,#$02,L9D47		; BR IF b1, DRIVE 
											;
9D42:          LDAA    L5070				;  0.625 COEF,  PK/NEUT FILT TIME CONST

9D45:          BRA     L9D57
		;----------------------------------------

9D47:  L9D47   LDAA    L0284				; MPH/1
9D4A:          CMPA    #80					; 80 MPH
9D4C:          BLS     L9D50				; BR IF Vss LT 80 MPH
											;
9D4E:          LDAA    #80					; 80 MPH
9D50:  L9D50   ASLA    						; N x 2


    		;--------------------------------------------------
	   		; FILTERED TPS FILT COEF vs Vss
	   		;
	   		;
	   		; TBL = FILT COEF * 256
       		;--------------------------------------------------
9D51:          LDX     #$507C				; FILTERED TPS FILT COEF TBL
9D54:          JSR     LF4C1				; 2d LK UP

9D57:  L9D57   LDAB    L01C0				; GET CURRENT MAP VALUE
9D5A:          CMPB    L5088				; 60 Kpa, MIN MAP FOR MOD'ING FILT COEF
9D5D:          BCC     L9D63				; BR IF MAP GT THRESSH
											;
9D5F:          LDAB    L5089				; 0.5 MUL 
9D62:          MUL     
9D63:  L9D63   TAB     
9D64:          BNE     L9D67
											;
9D66:          INCB    

9D67:  L9D67   PULA    

9D68:          LDX     L0882
9D6B:          JSR     LF459				; LAG FILTER

9D6E:  L9D6E   PSHB    
9D6F:          PSHA    
9D70:          BRSET   L0037,#$01,L9D8D		; BR IF b0, ETC ONCE FLAG 
											;
9D74:          LDAB    L0282				; START UP COOL
9D77:          CMPB    L509A				; 15 Deg c, START UP COOL FOR COLD ENG MODE
9D7A:          BCS     L9D8A				; BR IF S/U COOL 
											;
9D7C:          CMPB    L509B				; 15 Deg c, START UP COOL FOR COLD ENG MODE
9D7F:          BCC     L9D8A				; BR IF S/U COOL GT THRESH
											;
9D81:          LDX     L00FD				; RUN TIMER
9D83:          CPX     L509C				; 50 SEC'S MOD'ED THROT FOLLOWER RUN TIME
											;  MAX COLD ENG TIME)
											;
9D86:          BHI     L9D8A				; BR IF TIMER GT THRESH
											;
9D88:          BRA     L9D8D
		;----------------------------------------

9D8A:  L9D8A   BSET    L0037,#$01			; SET b0, ETC ONCE FLAG
											;
9D8D:  L9D8D   BRSET   L0039,#$80,L9DCF		; BR IF b7, 
											;
9D91:          TST     L0884				; FILTERED TPS DELAY TMR
9D94:          BNE     L9DCF				;
											;
9D96:          BRSET   L0036,#$04,L9DCF		; BR IF b2
											;
9D9A:          BRCLR   L0046,#$08,L9DAA		; BR IF NOT b3, DECEL FUEL C/O 
											;
       		;----------------------------------------------------
       		;
       		; b3 = 1 = INIT A/C ON INTEGRAL CELLS TO A/C OFF CELLS 
       		; b2 = 1 =
       		; b1 = 1 = USE ETC IN DECELL FUEL CUT OFF
       		;      0 = DONT USE ETC IN DECELL FUEL CUT OFF   
	   		;
       		; b0 = 1 = MAN  TRANS IN USE,DISABLE CLSD LP IDLE IF 
       		;               QUALS NOT OK                       
       		;      0 = AUTO  TRANS IN USE,ENABLE CLSD IF RPM LOW
	   		;----------------------------------------------------
9D9E:          LDAB    L4E8F				; 0000 1110, IAC MD WD #1
9DA1:          BITB    #$02					; b1, 
9DA3:          BNE     L9DAA

9DA5:          BSET    L0039,#$40
9DA8:          BRA     L9DEC
		;----------------------------------------

       ;--------------------------------------------------
	   ; IAC EXTENDED THROTTLE CRACKER TPS FOLLOWER 
	   ;	MIN VAL'S vs COOL
	   ;
       ;  SEE L5... FOR TBL MODIFIER
	   ;
	   ; TBL = 2.56 * 4 * %TF TPS
       ;--------------------------------------------------
9DAA:  L9DAA   LDAA    L0283				; RANGE LMT'ED COOL (-28 - 104c
9DAD:          LDX     #$508A				; IAC EXTENDED THROTTLE CRACKER TBL
9DB0:          JSR     LF4C1				; 2d LK UP
9DB3:          CLRB    						;
9DB4:          BRSET   L0037,#$01,L9DC5		; BR IF b0, ETC ONCE FLAG 
											;
9DB8:          LDAB    L50A0				; 25% EXTENDED THROTTLE CRACKER IF IN COLD MODE
9DBB:          MUL     						;
9DBC:          ASLD    						;
9DBD:          BCS     L9DC2				;
											;
9DBF:          ASLD    						;
9DC0:          BCC     L9DC5				;
											;
9DC2:  L9DC2   LDD     #$FFFF				;
9DC5:  L9DC5   TSX     						;
9DC6:          CPD     0,X					; 
9DC9:          BLS     L9DDB				;
											;
9DCB:          STD     0,X					;

9DCD:          BRA     L9DDB
		;----------------------------------------

9DCF:  L9DCF   LDAB    #255

9DD1:          BRSET   L0036,#$04,L9DE9
											;
9DD5:          CLRB    

9DD6:          BCLR    L0037,#$02			; CLR b1,  ETC * KONST 

9DD9:          BRA     L9DE9
		;----------------------------------------

9DDB:  L9DDB   LDAB    L0886
9DDE:          CMPB    L5097
9DE1:          BCS     L9DE8
											;
9DE3:          BSET    L0037,#$02			; SET b1, ETC * KONST 

9DE6:          BRA     L9DEC
		;----------------------------------------

9DE8:  L9DE8   INCB    
9DE9:  L9DE9   STAB    L0886
9DEC:  L9DEC   PULA    
9DED:          PULB    
9DEE:          STAA    L0882
9DF1:          BNE     L9DF8
9DF3:          CMPB    #$0028
9DF5:          BCC     L9DF8
9DF7:          CLRB    
9DF8:  L9DF8   STAB    L0883
9DFB:          SUBA    L0885
9DFE:          BCC     L9E06
9E00:          LDD     #$0000
9E03:          JMP     L9E95
 ;
9E06:  L9E06   BRCLR   L0037,#$02,L9E1B		; BR IF NOT b1, ETC * KONST  
											;
9E0A:          PSHB    
9E0B:          PSHA    
9E0C:          TSX     
9E0D:          LDAA    L509E
9E10:          BRCLR   L0037,#$01,L9E17		; BR IF NOT b0, ETC ONCE FLAG 
											;
9E14:          LDAA    L509F
9E17:  L9E17   JSR     LF550				; MUL 8X16 Subroutine
9E1A:          PULX    
9E1B:  L9E1B   PSHB    
9E1C:          PSHA 

   
        ;---------------------------------------------
		; IAC THROTTLE FOLLOWER GAIN vs RPM
		;
		;
  		;
		; TBL = GAIN FACTOR * 16
        ;---------------------------------------------
9E1D:          LDAA    L0063				; RPM/12.5
9E1F:          LDX     #$5064
9E22:          JSR     LF4B6				; 2D LK UP

9E25:          TSX     
9E26:          JSR     LF550				; MUL 8X16 Subroutine
9E29:          PULX    
9E2A:          ASLD    
9E2B:          BCS     L9E30
9E2D:          ASLD    
9E2E:          BCC     L9E35
9E30:  L9E30   LDD     #$FFFF

9E33:          BRA     L9E4E
		;----------------------------------------

9E35:  L9E35   PSHB    
9E36:          PSHA    
				;------------------------------------------

				;------------------------------------------
				;
				;
				;
				;------------------------------------------
9E37:          LDX     #$5057
9E3A:          LDAA    L0283				; RANGE LMT'ED COOL (-28 - 104c
9E3D:          JSR     LF4C1				; 2d LK UP
9E40:          TSX     
9E41:          JSR     LF550				; MUL 8X16 Subroutine
9E44:          PULX    
9E45:          ASLD    
9E46:          BCS     L9E4B

9E48:          ASLD    
9E49:          BCC     L9E4E

9E4B:  L9E4B   LDD     #$FFFF
9E4E:  L9E4E   BRSET   L0037,#$01,L9E65		; BR IF b0, ETC ONCE FLAG 
											;
9E52:          PSHB    
9E53:          PSHA    
9E54:          TSX     
9E55:          LDAA    L50A1
9E58:          JSR     LF550				; MUL 8X16 Subroutine
9E5B:          PULX    
9E5C:          ASLD    
9E5D:          BCS     L9E62
9E5F:          ASLD    
9E60:          BCC     L9E65				; BR IF 
											;
9E62:  L9E62   LDD     #$FFFF
9E65:  L9E65   BRCLR   L0039,#$80,L9E7D	   	; BR IF 
											;
9E69:          PSHB    
9E6A:          PSHA    
9E6B:          PULX    
9E6C:          SUBD    L0880
9E6F:          BCC     L9E75				; BR IF 
											;
9E71:          NEGB    
9E72:          ADCA    #$0000
9E74:          NEGA    
9E75:  L9E75   CMPA    L5087
9E78:          BCS     L9E98				; BR IF 
											;
9E7A:          XGDX    
9E7B:          BRA     L9E95
		;----------------------------------------

9E7D:  L9E7D   BRSET   L0046,#$08,L9E8A		; BR IF b3, DECEL FUEL C/O 
											;
9E81:          BRCLR   L0039,#$40,L9E8A
9E85:          BCLR    L0039,#$40
9E88:          BRA     L9E95
		;----------------------------------------

9E8A:  L9E8A   LDX     L0880
9E8D:          BEQ     L9E95
9E8F:          CPD     L0880
9E93:          BCC     L9E98
9E95:  L9E95   STD     L0880

9E98:  L9E98   RTS     


 			;------------------------------------------
9E99:  L9E99   BRSET   L004F,#$80,L9EA0		; BR IF b7, ENGINE RUNNING
											;
9E9D:          JMP     LA29A


9EA0:  L9EA0   JSR     L989C
9EA3:          BRSET   L0009,#$02,L9ECA		; BR OF b1, 1st DRIVE AWAY FLAG 
											;			FOR IAC KICK DOWN LOGIC
											;
9EA7:          LDAA    L0284				; MPH/1
9EAA:          CMPA    L4EC0				; 255 MPH COLD OFFSET THRESH
9EAD:          BLS     L9ECA

9EAF:          LDAA    L4EC1				; 99.6% COLD OFFSET KICK DOWN MULT
9EB2:          LDX     #$02A3				; 0675
9EB5:          JSR     LF550				; MUL 8X16 Subroutine

9EB8:          STD     L02A3

9EBB:          LDAA    L4EC1				; 99.6% COLD OFFSET KICK DOWN MULT
9EBE:          LDX     #$02AD				; 0685
9EC1:          JSR     LF550				; MUL 8X16 Subroutine
9EC4:          STD     L02AD

9EC7:          BSET    L0009,#$02			; SET b1, 1st DRIVE AWAY FLAG FOR
											;		   IAC KICK DOWN LOGIC

9ECA:  L9ECA   LDAA    L0887
9ECD:          BEQ     L9EEA
											;
9ECF:          BRSET   L0046,#$08,L9EEA		; BR IF b3, DECEL FUEL C/O 
											;
9ED3:          DEC     L0888
9ED6:          BNE     L9EEA
9ED8:          LDAB    L50BF
9EDB:          STAB    L0888
9EDE:          SUBA    L50BE
9EE1:          BCC     L9EE7
9EE3:          CLRA    
9EE4:          BCLR    L0038,#$20
9EE7:  L9EE7   STAA    L0887


9EEA:  L9EEA   LDAA    L4E8F				; 0000 1110, IAC MD WD #1
9EED:          BITA    #$04					; b2, USED FOR ***-----> ??????
9EEF:          BNE     L9EF3

9EF1:          BRA     L9F46
		;----------------------------------------

9EF3:  L9EF3   BRCLR   L003B,#$10,L9F00
9EF7:          LDAA    L038F
9EFA:          BITA    #$0040
9EFC:          BEQ     L9F00

9EFE:          BRA     L9F46
		;----------------------------------------

9F00:  L9F00   BRSET   L0037,#$04,L9F07		; BR IF  b2, THROTTLE KICKER ACTIVE
											;
9F04:          JMP     L9F89

9F07:  L9F07   BRSET   L0036,#$0C,L9F0D
9F0B:          BRA     L9F16
		;----------------------------------------

9F0D:  L9F0D   LDAA    L02F6				; FILT TPS (XMISH)
9F10:          STAA    L02B1

9F13:          BSET    L0039,#$01			; SET b0
											;
9F16:  L9F16   BRSET   L0037,#$08,L9F5B		; BR IF b3, THROTTLE KICKER DISABLE REQUESTED
											;
9F1A:          LDAA    L0006				; COOL VALUE
9F1C:          CMPA    L50C7				; 55c COOL THRESH MAX FOR THROT KICKER
9F1F:          BCC     L9F2A				; BR IF COOL GT THRESH
 											;
9F21:          LDAA    L50CC				; 1.8 SEC, MAX RUN TIME FOR THROT KICKER
9F24:          STAA    L088D				; THROTTLE KICKER TIMER

9F27:          JMP     L9FDB
 ;
9F2A:  L9F2A   BRSET   L0037,#$10,L9F5B		; BR IF b4, THROTTLE KICKER BARO DISABLE REQUESTED
											;
9F2E:          LDAA    L02F4				; BARO
9F31:          CMPA    L50CD				; 93 Kpa,  BARO THRESH
9F34:          BCC     L9F5B				; BR IF BAOR GT THRESH
											; ... ele
9F36:          BRCLR   L0036,#$80,L9F46		; BR IF NOT b7, IDLE RPM TOO HIGH
											;
9F3A:          LDAA    L02A7
9F3D:          CMPA    L50CF
9F40:          BCC     L9F46

9F42:          BRSET   L0036,#$08,L9F49
9F46:  L9F46   JMP     L9FDE
 ;
9F49:  L9F49   LDAA    L50D1
9F4C:          BRSET   L0036,#$02,L9F53		; BR IF b1, DRIVE 
											;
9F50:          LDAA    L50D2
9F53:  L9F53   CMPA    L0858
9F56:          BLS     L9F5B

9F58:          BSET    L0037,#$10			; SET b4, THROTTLE KICKER BARO DISABLE REQUESTED
											;
 				;
				; DIACMW2, NON-VOL IDLE CNT'L MD WD 
				;
9F5B:  L9F5B   BRCLR   L0036,#$40,L9F64		; BR IF NOT b6, DIAG MD WD #3
											;
9F5F:          LDAA    L088D				; THROTTLE KICKER TIMER
9F62:          BNE     L9F7D				;
											;
9F64:  L9F64   LDAA    L01D9				; %TPS
9F67:          CMPA    L50CB				;  9.7% TPS MAX FOR THROT KICKER
9F6A:          BHI     L9FB3				; BR IF TPS GT 9.7%
											;
9F6C:          LDAA    L0284				; MPH/1
9F6F:          CMPA    L50CA				; 10 MPH vss MAX FOR THROT KICKER
9F72:          BHI     L9FB3				; BR IF Vss GT 10 MPH 
											;
9F74:          BRSET   L0036,#$40,L9FDB		; BR IF b6, 
											;
9F78:          LDAA    L088D				; THROTTLE KICKER TIMER
9F7B:          BEQ     L9FB3				; BR IF TIMER = Z
											;
9F7D:  L9F7D   LDAB    L0002				; MAJOR LOOP COUNTER
9F7F:          ANDB    #$F0					; MASK 1111 0000
9F81:          BNE     L9FDB				; BR IF 
											;
9F83:          DECA    						; DECR TIMER    
9F84:          STAA    L088D				; THROTTLE KICKER TIMER

9F87:          BRA     L9FDB
		;----------------------------------------

9F89:  L9F89   LDAA    L088D				; THROTTLE KICKER TIMER
9F8C:          CMPA    #$0F					;
9F8E:          BLS     L9FA7				;


9F90:          BRSET   L0036,#$0C,L9F96
											;
9F94:          BRA     L9F9F
		;----------------------------------------

9F96:  L9F96   LDAA    L02F6				; FILT TPS (XMISH)
9F99:          STAA    L02B2

9F9C:          BSET    L0039,#$02			; SET b1
											;
9F9F:  L9F9F   LDAA    L088D				; THROTTLE KICKER TIMER
9FA2:          CMPA    L50D7				; 96 Sec's, HYST TIME KICKER MUST
											;		 BE OFF TO BR RE-ENABLED
9FA5:          BEQ     L9FB3				;

9FA7:  L9FA7   LDAB    L0002				; MAJOR LOOP COUNTER
9FA9:          ANDB    #$F0					; MASK 1111 0000,
9FAB:          BNE     L9FC6				;

9FAD:          INCA    						; INCR TIMER
9FAE:          STAA    L088D				; THROTTLE KICKER TIMER

9FB1:          BRA     L9FC6
		;----------------------------------------

9FB3:  L9FB3   LDAA    L02F4				; BARO
9FB6:          CMPA    L50CE				; 85 Kpa,  BARO THRESH
9FB9:          BLS     L9FCB				; BR IF BARO LT THRESH

9FBB:          LDD     L02A7
9FBE:          ADDD    L02AD
9FC1:          CMPA    L50D0				; 50% FLOW FOR DISABLING THROTTLE KICKER
9FC4:          BHI     L9FCB				;


9FC6:  L9FC6   JSR     L920E
9FC9:          BRA     L9FDE
		;----------------------------------------

9FCB:  L9FCB   LDAA    L01D9				; %TPS
9FCE:          CMPA    L50CB
9FD1:          BHI     L9FDB				;


9FD3:          LDAA    L0284				; MPH/1
9FD6:          CMPA    L50CA
9FD9:          BLS     L9FDE				;


9FDB:  L9FDB   JSR     L9226

9FDE:  L9FDE   LDAA    L02A5
9FE1:          ORAA    L02AF
9FE4:          BNE     L9FE9				;


9FE6:          JMP     LA0D8
		;--------------------------------------------------


		;--------------------------------------------------
		; HOUSE KEEP IAC COLD OFFSET DELAY PERIOD
		;
		;--------------------------------------------------
9FE9:  L9FE9   LDAA    L0875				; IAC COLD OFFSET DELAY PERIOD
9FEC:          BEQ     L9FF1				; BR IF TIME = Z

9FEE:          DECA    						; DECR TIMER

9FEF:          BRA     LA069
		;----------------------------------------

9FF1:  L9FF1   LDAA    L4EBD				; 97.6% DECAY MULT FOR IAC MAX COLD OFFSET
9FF4:          LDX     #$02A5				; 0677
9FF7:          JSR     LF550 				; MUL 8X16 Subroutine
											;
9FFA:          TSTA    						; 
9FFB:          BNE     L9FFF				;


9FFD:          CLRA    
9FFE:          CLRB    
9FFF:  L9FFF   STD     L02A5
A002:          BEQ     LA016				;


A004:          LDAA    L4EBE				; 95.7% DECAY MULT FOR PARK, (IAC)
A007:          LDX     #$02A3				; 075
A00A:          JSR     LF550 				; MUL 8X16 Subroutine
											;
A00D:          CPD     L02A5				;
A011:          BLS     LA016				;


A013:          LDD     L02A5
A016:  LA016   STD     L02A3

A019:          LDAA    L4EBD				; 97.6% DECAY MULT FOR IAC MAX COLD OFFSET
A01C:          LDX     #$02AF				; 0687
A01F:          JSR     LF550				; MUL 8X16 Subroutine
A022:          TSTA    
A023:          BNE     LA027				;


A025:          CLRA    
A026:          CLRB    
A027:  LA027   STD     L02AF
A02A:          BEQ     LA03E				;


A02C:          LDAA    L4EBF				; 95.3% DECAY MULT FOR DRIVE, (IAC)
A02F:          LDX     #$02AD				; 685
A032:          JSR     LF550				; MUL 8X16 Subroutine

A035:          CPD     L02AF
A039:          BLS     LA03E				;


A03B:          LDD     L02AF
A03E:  LA03E   STD     L02AD
A041:          LDAA    L02A5
A044:          ORAA    L02AF
A047:          BEQ     LA069
											; ... els
        ;---------------------------------------------
    	; IAC COLD OFFSET DELAY PERIOD vc COOL
    	;
    	;  TBL =  10  * Sec's
        ;---------------------------------------------
A049:          LDAA    L0283				; RANGE LMT'ED COOL (-28 - 104c)
A04C:          LDX     #$4EDC				; IAC COLD OFFSET DELAY TBL
A04F:          JSR     LF4C1				; 2d LK UP
											;
A052:          PSHA    						; SAVE DELAY PERIOD TO STX
		
	
		;---------------------------------------------
		; IAC MULT vs FLOW
		;  
		;
		; TBL = MULT * 128  
		;---------------------------------------------
A053:          LDX     #$4EE9				; MULT vs FLOW
											;
A056:          LDAA    L0232				; AIR FLOW, (0-64)
A059:          CMPA    #64					; MAX AIR FLOW VALUE
A05B:          BLS     LA05F				; BR IF AIR FLOW 
											;
A05D:          LDAA    #64					; FORCE MAX AIR FLOW VALUE FOR LK UP
A05F:  LA05F   JSR     LF4C1				; 2d LK UP
A062:          PULB    						;
A063:          MUL     						; APPLY MULT
A064:          ASLD    						; n x 2
A065:          BCC     LA069				; BR IF NO OVERFLOW
											;
A067:          LDAA    #255					; USE MAX VAL
A069:  LA069   STAA    L0875				; SAVE IAC COLD OFFSET DELAY PERIOD


A06C:          BRSET   L0036,#$02,LA0A0		; BR IF b1, DRIVE
											;
A070:          LDAA    L02A3				;
A073:          BEQ     LA0D6				; BR IF = Z
											;
A075:          LDAB    L4EF0				; 0% MIN ALLOWABLE DIFF
A078:          BEQ     LA085				; BR IF = Z
											;
A07A:          MUL     						;
A07B:          ADCA    L02A3				;
A07E:          BCS     LA085				;
											;
A080:          CMPA    L02AD				;
A083:          BCS     LA09A				;
											;
A085:  LA085   LDAA    L02A3				;
A088:          LDAB    L4EF1				; 0% MIN ALLOWABLE DIFF
A08B:          BEQ     LA0D6				; BR IF = Z
											;
A08D:          MUL     
A08E:          ADCA    #$00
A090:          TAB     

A091:          LDAA    L02A3
A094:          SBA     
A095:          CMPA    L02AD
A098:          BCS     LA0D3				;
											;
A09A:  LA09A   CLRB    
A09B:          STD     L0899

A09E:          BRA     LA0CE
		;----------------------------------------

A0A0:  LA0A0   LDAA    L02AD
A0A3:          BEQ     LA0D6				; BR IF Z
											;
A0A5:          LDAB    L4EEE				; 0% MAX ALLOWABLE DIFF
A0A8:          BEQ     LA0B5				; BR IF = Z

A0AA:          MUL     
A0AB:          ADCA    L02AD
A0AE:          BCS     LA0B5
											;
A0B0:          CMPA    L02A3
A0B3:          BCS     LA0CA				;
											;
A0B5:  LA0B5   LDAA    L02AD
A0B8:          LDAB    L4EEF				; 0% MIN ALLOWABLE DIFF
A0BB:          BEQ     LA0D6				; BR IF = Z
											;
A0BD:          MUL     
A0BE:          ADCA    #$00
A0C0:          TAB     
A0C1:          LDAA    L02AD
A0C4:          SBA     
A0C5:          CMPA    L02A3
A0C8:          BCS     LA0D3
A0CA:  LA0CA   CLRB    
A0CB:          STD     L0893
A0CE:  LA0CE   BSET    L0038,#$10
A0D1:          BRA     LA12D
		;----------------------------------------

A0D3:  LA0D3   BCLR    L0038,#$10

A0D6:  LA0D6   BRA     LA12D
		;----------------------------------------

A0D8:  LA0D8   BRSET   L0036,#$0C,LA0DE

A0DC:          BRA     LA12D
		;----------------------------------------

		;
		; CKECK QUAL'S
		;
A0DE:  LA0DE   LDAA    L0006				; COOL VALUE
A0E0:          CMPA    L4FBF				;  85c COOL, LOW THRESH FOR WARM IDLE
A0E3:          BCS     LA12D				; BR IF COOL 
											;
A0E5:          CMPA    L4FC0				; 100c COOL, Hi  THRESH FOR WARM IDLE
A0E8:          BHI     LA12D				; BR IF COOL
											;
A0EA:          LDAA    L0858				; RPM/12.5
A0ED:          CMPA    L4FBE				; 25 RPM, DEADBAND FOR UP DATING IDLE CELLS
A0F0:          BHI     LA12D				;
											;
A0F2:          LDAA    L0859				; RPM/12.5
A0F5:          CMPA    L4FBE 				; 25 RPM, DEADBAND FOR UP DATING IDLE CELLS
A0F8:          BHI     LA12D				; BR IF RPM 
											;
A115:  LA115   BRSET   L0036,#$01,LA124		; BR IF NOT b0, A/C ON
											;
A119:          LDAA    L02A7
A11C:          STAA    L02A9

A11F:          BSET    L0009,#$10			; SET b4, WARM IDLE STABLE, A/C OFF
											; 
A122:          BRA     LA12D
		;----------------------------------------

A124:  LA124   LDAA    L02AA
A127:          STAA    L02AC

A12A:          BSET    L0009,#$20			; SET b5, WARM IDLE STABLE, A/C ON
											;
A12D:  LA12D   LDAA    L0876
A130:          BEQ     LA154				;
											;
A132:          LDAB    L0877
A135:          BNE     LA154				;
											;
A137:          BRCLR   L0036,#$01,LA150		; BR IF NOT b0, A/C ON 
											;
A13B:          LDAB    L0878
A13E:          BEQ     LA145				;
											;
A140:          DEC     L0878
A143:          BNE     LA154				;
											;
A145:  LA145   LDAB    L4F22				; ___ % FLOW
A148:          STAB    L0878
											;
A14B:          SUBA    L4F21				; 125 Msec, CLS LP IDLE DELAY
A14E:          BCC     LA151				; BR IF TIMER = NZ
											;
A150:  LA150   CLRA    
A151:  LA151   STAA    L0876

A154:  LA154   LDAB    L0036
A156:          BITB    #$08					; b3, 
A158:          BEQ     LA162				; BR IF NOT b3
											;
A15A:          BITB    #$10					; b4
A15C:          BNE     LA162				; BR IF b4
											;
A15E:          BRCLR   L003E,#$04,LA165		; BR IF NOT b2, LOW BATTERY
											;
A162:  LA162   JMP     LA288


A165:  LA165   CLRB    
A166:          BRSET   L0036,#$01,LA173		; BR IF b0, A/C ON
											;
A16A:          LDX     #$029D
A16D:          LDY     #$088F
A171:          BRA     LA17A
 ;
A173:  LA173   LDX     #$02A0
A176:          LDY     #$0891
A17A:  LA17A   LDAA    0,X
A17C:          SUBA    $0A,X
A17E:          BCS     LA19D
											; .... lese
A180:          CMPA    L4FC6
A183:          BLS     LA1BB
											; .... lese
A185:          BRSET   L0036,#$02,LA193		; BR IF NOT b1, DRIVE 
A189:          LDAA    0,X
A18B:          SUBA    L4FC6
A18E:          STD     $06,Y

A191:          BRA     LA1DB


A193:  LA193   LDAA    $0A,X
A195:          ADDA    L4FC6
A198:          STD     0,Y

A19B:          BRA     LA1DB


A19D:  LA19D   NEGA    
A19E:          CMPA    L4FC5				;  30%   FLOW, MAX Diff 
A1A1:          BLS     LA1BB

A1A3:          BRSET   L0036,#$02,LA1B1		; BR IF b1, DRIVE 

A1A7:          LDAA    0,X
A1A9:          ADDA    L4FC5
A1AC:          STD     6,Y

A1AF:          BRA     LA1DB


A1B1:  LA1B1   LDAA    $0A,X
A1B3:          SUBA    L4FC5
A1B6:          STD     0,Y

A1B9:          BRA     LA1DB


A1BB:  LA1BB   BRSET   L0036,#$02,LA1CD		; BR IF b1, DRIVE 
											;
A1BF:          BRSET   L0036,#$01,LA1C8		; BR IF A/C ON
											;
A1C3:          BCLR    L0038,#$04
A1C6:          BRA     LA1F9
 ;
A1C8:  LA1C8   BCLR    L0038,#$08

A1CB:          BRA     LA1F9


A1CD:  LA1CD   BRSET   L0036,#$01,LA1D6		; BR IF b0, A/C ON

A1D1:          BCLR    L0038,#$01
A1D4:          BRA     LA1F9
 ;
A1D6:  LA1D6   BCLR    L0038,#$02
A1D9:          BRA     LA1F9
 ;
A1DB:  LA1DB   BRSET   L0036,#$02,LA1ED		; BR IF b1, DRIVE 
											;
A1DF:          BRSET   L0036,#$01,LA1E8		; BR IF b0, A/C ON
											;
A1E3:          BSET    L0038,#$04
A1E6:          BRA     LA1F9
 ;
A1E8:  LA1E8   BSET    L0038,#$08
A1EB:          BRA     LA1F9
 ;
A1ED:  LA1ED   BRSET   L0036,#$01,LA1F6		; BR IF b0, A/C ON
											;
A1F1:          BSET    L0038,#$01
A1F4:          BRA     LA1F9
 ;
A1F6:  LA1F6   BSET    L0038,#$02
A1F9:  LA1F9   BRSET   L0036,#$02,LA20A		; BR IF b1, DRIVE 
A1FD:          LDX     #$088F
A200:          PSHX    
A201:          LDX     #$029D
A204:          LDY     #$4FC1
A208:          BRA     LA215
 ;
A20A:  LA20A   LDX     #$0895
A20D:          PSHX    
A20E:          LDX     #$02A7
A211:          LDY     #$4FC3
A215:  LA215   LDAB    0,Y
A218:          PSHB    
A219:          LDD     $0003,X
A21B:          SUBD    0,X
A21D:          PULB    
A21E:          BLS     LA229
A220:          CBA     
A221:          BCS     LA229
A223:          LDAB    $0001,Y
A226:          CBA     
A227:          BLS     LA249
A229:  LA229   BRSET   L0036,#$01,LA23D		; BR IF b0, A/C ON
											;
A22D:          LDAA    0,X
A22F:          ABA     
A230:          BCC     LA237
A232:          LDD     #$FFFF
A235:          BRA     LA238
 ;
A237:  LA237   CLRB    
A238:  LA238   PULX    
A239:          STD     $0002,X
A23B:          BRA     LA26A
 ;
A23D:  LA23D   LDAA    $0003,X
A23F:          SBA     
A240:          BCC     LA243
A242:          CLRA    
A243:  LA243   CLRB    
A244:          PULX    
A245:          STD     0,X
A247:          BRA     LA26A
 ;
A249:  LA249   PULX    
A24A:          BRSET   L0036,#$02,LA25C		; BR IF b1, DRIVE 
A24E:          BRSET   L0036,#$01,LA257		; BR IF b0, A/C ON
											;
A252:          BCLR    L0038,#$02
A255:          BRA     LA288
 ;
A257:  LA257   BCLR    L0038,#$01
A25A:          BRA     LA288
 ;
A25C:  LA25C   BRSET   L0036,#$01,LA265		; BR IF b0, A/C ON
											;
A260:          BCLR    L0038,#$08
A263:          BRA     LA288
 ;
A265:  LA265   BCLR    L0038,#$04
A268:          BRA     LA288
 ;
A26A:  LA26A   BRSET   L0036,#$02,LA27C		; BR IF b1, DRIVE 
A26E:          BRSET   L0036,#$01,LA277		; BR IF b0, A/C ON
											;
A272:          BSET    L0038,#$02
A275:          BRA     LA288
 ;
A277:  LA277   BSET    L0038,#$01
A27A:          BRA     LA288
 ;
A27C:  LA27C   BRSET   L0036,#$01,LA285		; BR IF b0, A/C ON
											;
A280:          BSET    L0038,#$08
A283:          BRA     LA288
 ;
A285:  LA285   BSET    L0038,#$04
A288:  LA288   LDAA    L0866
A28B:          BEQ     LA291
A28D:          DECA    
A28E:          STAA    L0866
A291:  LA291   LDAA    L0867
A294:          BEQ     LA29A
A296:          DECA    
A297:          STAA    L0867

A29A:  LA29A   LDX     #$02A7
A29D:          BRSET   L0036,#$02,LA2A4		; BR IF b1, DRIVE 

A2A1:          LDX     #$029D
A2A4:  LA2A4   LDAA    2,X
A2A6:          BRCLR   L0036,#$01,LA2AC		; BR IF b0, A/C ON
											;
A2AA:          LDAA    5,X
A2AC:  LA2AC   STAA    L086A

A2AF:          RTS     
 		;--------------------------------------------------


A2B0:  LA2B0   BRSET   L004F,#$80,LA2B7		; BR IF b7, ENGINE RUNNING
											;
A2B4:          JMP     LA406


A2B7:  LA2B7   JSR     L9CFD
A2BA:          LDAA    L087B
A2BD:          BEQ     LA2DA				;
											;
A2BF:          LDAB    L087C				; Decay period for pwr steer
A2C2:          BEQ     LA2C9				; BR IF TIMER = Z
											;
A2C4:          DEC     L087C				; DECR Decay period for pwr steer
A2C7:          BNE     LA2DA				; BR IF TIMER = Z
											;
A2C9:  LA2C9   SUBA    L4F31				; 0% FLOW, PWR STEER DECAY AMT.
A2CC:          BCC     LA2CF				;
											;
A2CE:          CLRA    
A2CF:  LA2CF   STAA    L087B
A2D2:          BEQ     LA2D7				;
											;
A2D4:          LDAA    L4F30				; 0 Sec's, DECAY PERIOD FOR PWR STEER
A2D7:  LA2D7   STAA    L087C				; Decay period for pwr steer
											;
A2DA:  LA2DA   LDAA    L086B				;
A2DD:          BEQ     LA2FA				;
											;
A2DF:          BRCLR   L003F,#$40,LA2E6		;
A2E3:          CLRA    						;

A2E4:          BRA     LA2F7


A2E6:  LA2E6   LDAB    L086C
A2E9:          BEQ     LA2F0				;
											;
A2EB:          DEC     L086C				;
A2EE:          BNE     LA2FA				;
											;
A2F0:  LA2F0   LDAB    L4EB9				;
A2F3:          STAB    L086C				;
											;
A2F6:          DECA    						;
A2F7:  LA2F7   STAA    L086B				;


A2FA:  LA2FA   LDAA    L085C
A2FD:          BEQ     LA32A				;
											;
A2FF:          BRCLR   L003F,#$40,LA306		;
											;
A303:          CLRA    						;
A304:          BRA     LA327				


A306:  LA306   LDAB    L085E				;
A309:          BEQ     LA316				;
											;
A30B:          LDAB    L0002 				; MAJOR LOOP COUNTER
A30D:          BITB    #$F0					;
A30F:          BNE     LA32A				;
											;
A311:          DEC     L085E				;
A314:          BRA     LA32A


A316:  LA316   LDAB    L085D				;
A319:          BEQ     LA320				;
											;
A31B:          DEC     L085D				;
A31E:          BNE     LA32A				;
											;
A320:  LA320   LDAB    L4EBB				;
A323:          STAB    L085D				;

A326:          DECA    						;
A327:  LA327   STAA    L085C				;
											;
A32A:  LA32A   LDAA    L0036				;
A32C:          BITA    #$02					; b1, DRIVE
A32E:          BEQ     LA35C				; BR IF NOT b1, DRIVE
											;
A330:          BITA    #$0C					;
A332:          BNE     LA35C				;
											;
A334:          BITA    #$01					;
A336:          BNE     LA34B				;
											;
A338:          LDAA    L02A9				;
A33B:          ADDA    L4FC7				; 5.9%,	FLOW LMT IF NOT IN CLSD LP IAC 
A33E:          BCS     LA35C				;
											; 
A340:          CMPA    L02A7				;
A343:          BCC     LA35C				;
											; 
A345:          CLRB    						;
A346:          STD     L02A7				;
											
A349:          BRA     LA35C


A34B:  LA34B   LDAA    L02AC				;
A34E:          ADDA    L4FC8				; 6.6%, FLOW LMT IF NOT IN CLSD LP IAC
A351:          BCS     LA35C				;		  
											;
											; 
A353:          CMPA    L02AA				;
A356:          BCC     LA35C				;				;
											;
A358:          CLRB    						;
A359:          STD     L02AA				;

A35C:  LA35C   LDAA    L4E8F				; 0000 1110, IAC MD WD #1
A35F:          BITA    #$04					; b2, 1 = USED FOR ***-----> ??????
A363:          BEQ     LA398				; BR IF NOT b4
											;

			;
			; CK ERR WD 3
			; ERR 36, IAC TPS KICKER FAIL
			;
		       LDAA    L5B02				; ERR WD 3 MASK
A366:          BITA    #$04					; b2, ERR 36, IAC TPS KICKER FAIL 
A368:          BEQ     LA398				; BR IF NOT b2
											;
A36A:          BRSET   L0039,#$04,LA398		;
											;
A36E:          BRSET   L0039,#$03,LA374		;
											;
A372:          BRA     LA398


A374:  LA374   LDAA    L02B1				; TPS A/D
A377:          SUBA    L02B2				; OLD TPS A/D 
A37A:          BCS     LA381				; BR IF OLD TPS A/D TPS
											;
A37C:          CMPA    L50D6				; A/D TPS MIN DIFF FOR ENABLE
A37F:          BCC     LA38F				;
											;
A381:  LA381   BRSET   L0009,#$40,LA38		; BR IF b6, 1st PASS OF ERR 36 HAS FAILED

A385:          BSET    L0009,#$40			; SET b6, 1st PASS OF ERR 36 HAS FAILED
											
A388:          BRA     LA395

 

				;
				; CURRENT ERR WD 3
				; $F5
				;
A38A:  LA38A   BSET    L0018,#$04			; SET b2, ERR 36, IAC THROTTLE KICKER FAIL
A38D:          BRA     LA395				
 

A38F:  LA38F   BCLR    L0018,#$04			;
A392:          BCLR    L0009,#$40			; CLR b6, 1st PASS OF ERR 36 HAS FAILED
A395:  LA395   BSET    L0039,#$04			;
											;
A398:  LA398   BRSET   L0002,#$20,LA406		; BR IF 				; MAJOR LOOP COUNTER
 											;
A39C:          LDAA    L5B02				; ERR WD 3 MASK
A39F:          BITA    #$08					; b3 1 = ERR 35, IAC FAIL
A3A1:          BEQ     LA3E6				; 
 											;
A3A3:          BRSET   L0016,#$10,LA3E0		; BR IF b4 
 											;
A3A7:          BRSET   L0016,#$01,LA3E0		; BR IF b0, ERR 21, HI TPS
 											;
A3AB:          BRSET   L0017,#$80,LA3E0		; BR IF b7 
 											;
A3AF:          BRSET   L003E,#$04,LA3E0		; BR IF b2, LOW BATTERY
 											; 
A3B3:          BRCLR   L0036,#$08,LA3E0		; BR IF NOT b3
 											;
A3B7:          BRSET   L0009,#$40,LA3E0		; BR IF b6, 1st PASS OF ERR 36 HAS FAILED
											;
A3BB:          LDX     L02AD				;
A3BE:          BNE     LA3E0
 											;
A3C0:          LDX     L02A3				; IAC FLOW vs COOL
A3C3:          BNE     LA3E0				;
 											;
A3C5:          LDAB    L0859				; RPM/12.5
A3C8:          CMPB    L50C0				; 125.5 RPM, IF CLS LP IDLE ON AND 
											; REQUESTED RPM - RPM LT 125 SET ERR 35
A3CB:          BLS     LA3E0				;
											;
A3CD:          LDAB    L088E              	; ERR 35 TIMER
A3D0:          CMPB    L50C1				; 10 SEC'S ERR 35 TIME THRESH
A3D3:          BHI     LA3DB				;
											;
A3D5:          INCB    						;
A3D6:          STAB    L088E				;

A3D9:          BRA     LA3E6

 
 
A3DB:  LA3DB   BSET    L0018,#$08			; SET b3, CURRENT ERR WD #3
A3DE:          BRA     LA3E6
 

A3E0:  LA3E0   CLR     L088E				;
A3E3:          BCLR    L0018,#$08			; CLR b3, CURRENT ERR WD #3
											;
A3E6:  LA3E6   BRSET   L0009,#$01,LA406		; BR IF b0, IAC MOTOR Reset IN WORK
											;
A3EA:          BRSET   L0009,#$04,LA40		; BR IF b2, R/S REQUESTED IF BIT CLEAR
											;
A3EE:          BRSET   L0044,#$10,LA3FA		; BR IF b4, IGNITION OFF 
											;
A3F2:          LDAA    L0284              	; MPH/1
A3F5:          CMPA    L4EB7              	; 30 MPH IAC MOTOR RESET THRES
A3F8:          BCS     LA406				; BR IF Vss LT THRESH
											;
A3FA:  LA3FA   BSET    L0009,#$01         	; SET b0, IAC MOTOR Reset IN WORK
A3FD:          BCLR    L0036,#$1C			; CLR ... 0001 1100

A400:          CLRA    
A401:          STAA    L0008				; IAC
A403:          DECA    
A404:          STAA    L0007			    ; IAC, PRESSENT MOTOR POSIT

A406:  LA406   RTS     
 		;--------------------------------------------------


A407:  LA407   BRSET   L0044,#$10,LA465		; BR IF b4, IGNITION OFF 
											;
A40B:          BRSET   L0009,#$01,LA4656	; BR IF b0, IAC MOTOR Reset IN WORK
											;
A40F:          LDAB    L0391
A412:          BITB    #$0020				; b5
A414:          BEQ     LA41A				; BR IF NOT b5
A416:          PULX    
A417:          JMP     LA3FA
 ;
A41A:  LA41A   LDAB    L0395				;
A41D:          ANDB    #1					; 0000 0001
A41F:          LDAA    L038F				;
A422:          ANDA    #64					; 0100 0000
A424:          ABA     						;
A425:          BEQ     LA465				;
A427:          CMPA    #65					;
A429:          BEQ     LA465				;
A42B:          BITA    #$01					; 0000 0001
A42D:          BEQ     LA44B				; BR IF NOT b0
A42F:          LDAA    L0395				;
A432:          BITA    #$02					; 0000 0010
A434:          BNE     LA440				; BR IF b1
A436:          BCLR    L0036,#$0C			;
A439:          PULX    						;
A43A:          LDAA    L0396				;
A43D:          JMP     L9899				;
 ;
A440:  LA440   LDAA    L0396
A443:          STAA    L0857   				; DESIRED IDLE RPM/12.5
A446:          BSET    L0038,#$40
A449:          BRA     LA465
 ;
A44B:  LA44B   PULX    
A44C:          LDAA    L0390
A44F:          BITA    #$40					; 0100 0000 B6
A451:          BEQ     LA45C				; BR IF NOT B6,

A453:          JSR     L923C

A456:          BSET    L0037,#$04			; SET b2, THROTTLE KICKER ACTIVE
											;
A459:          JMP     L989B
 ;
A45C:  LA45C   JSR     L9222
A45F:          BCLR    L0037,#$04			; CLR b2, THROTTLE KICKER ACTIVE
											; 
A462:          JMP     L989B
 ;
A465:  LA465   RTS     
 ; ------------------------------------------
A466:  LA466   LDAB    #151
A468:          LDAA    L02F4				; BARO
A46B:          SUBA    L01C6
A46E:          BHI     LA472
A470:          LDAA    #1
A472:  LA472   MUL     
A473:          ADDD    #64
A476:          ASLD    
A477:          BCC     LA47C
A479:          LDD     #$FFFF
A47C:  LA47C   NEGA    
A47D:          STAA    L01C9				; Kpa VACUUM
A480:          LDAB    #151
A482:          LDAA    L01C6
A485:          SUBA    #26
A487:          BCC     LA48C
A489:          CLRA    
A48A:          BRA     LA496
 ;
A48C:  LA48C   MUL     
A48D:          ADDD    #64
A490:          ASLD    
A491:          BCC     LA496
											;
A493:          LDD     #$FFFF

A496:  LA496   STAA    L01C0				; GET CURRENT MAP VALUE

A499:          LDAA    L01CE
A49C:          CLRB    
A49D:          LDX     L0257
A4A0:          XGDX    
A4A1:          FDIV    
A4A2:          XGDX    
A4A3:          SUBD    #$2000
A4A6:          BCC     LA4AB
A4A8:          LDD     #$0000
A4AB:  LA4AB   ASLD    
A4AC:          BCC     LA4B0
A4AE:          LDAA    #255
A4B0:  LA4B0   STAA    L01CF
A4B3:          BCLR    L0018,#$10
A4B6:          BCLR    L006F,#$08
A4B9:          BRSET   L006F,#$04,LA4E1

A4BD:          LDAA    L082E				; MAP A/D
A4C0:          CMPA    L4E64				; 24.4 Kpa MAP Lmt, ERR 34, (LO MAP) 
A4C3:          BCC     LA4E1				; BR IF MAP GT THRESH
A4C5:          LDAA    L0229				; ERR 34 time Lmt
A4C8:          CMPA    L4E66				; 25 Msec time Lmt
A4CB:          BHI     LA4E6				; BR IF ERR 34 TIMER DONE
A4CD:          LDAA    L0061				; RPM/25
A4CF:          CMPA    L4E65				; 1200 RPM Max Lmt, ERR 34, (LO MAP)
A4D2:          BCS     LA4DC
A4D4:          LDAA    L01D9				; %TPS, ERR 34, (LO MAP)
A4D7:          CMPA    L4E67
A4DA:          BLS     LA4E1
A4DC:  LA4DC   INC     L0229				; ERR 34 time Lmt
A4DF:          BRA     LA4EC
 ;
A4E1:  LA4E1   CLR     L0229				; ERR 34 time Lmt
A4E4:          BRA     LA4EC
 ;
A4E6:  LA4E6   BSET    L0018,#$10			; SET b4
A4E9:          BSET    L006F,#$08			; SET b3
A4EC:  LA4EC   BRCLR   L0050,#$20,LA53D		; BR IF NOT b5
A4F0:          BCLR    L0050,#$20			; CLR b5
A4F3:          BSET    L0050,#$04			; CLR b2
A4F6:          CLRA    
A4F7:          CLRB    
A4F8:          STD     L0260				; FUEL PUMP RUN TIMER
A4FB:          LDD     L01EA
A4FE:          LSRD    
A4FF:          LSRD    
A500:          LSRD    
A501:          COMA    
A502:          COMB    
A503:          ADDD    L01EA
A506:          BPL     LA50A
A508:          CLRA    
A509:          CLRB    
A50A:  LA50A   STD     L01EA
A50D:          CLR     L0202

A510:          BRCLR   L004F,#$80,LA540		; BR IF NOT b7, ENGINE RUNNING
											;
A514:          BRSET   L004F,#$10,LA51B		; BR IF b4, RUN FUEL
											;
A518:          JSR     LA581				;
											;
A51B:  LA51B   BRCLR   L004F,#$40,LA57F		; BR IF NOT b6, MAJOR LOOP EST MONITOR ENABLE
											;
A51F:          BRSET   L0051,#$40,LA57F		; BR IF b6, 
											;

			;
			; FILTER START UP SPK
			;
A523:          LDAB    L414E				; 62.5% COEF START UP SPK MULT COEF
A526:          LDX     L01F2				; GET OLD START UP SPARK
A529:          CPX     #$FEF0				;
A52C:          BHI     LA538				; BR IF 
											;
A52E:          LDAA    #$00FF				;
A530:          JSR     LF459				; LAG FILTER
A533:          STD     L01F2				; SAVE FILTERED START UP SPARK

A536:          BRA     LA57F



A538:  LA538   BSET    L0051,#$40			; SET b6

A53B:          BRA     LA57F

 
 
A53D:  LA53D   JMP     LA59B

 
 
A540:  LA540   BRSET   L0044,#$08,LA54A		; BR IF b3, 1st DRP VALID
											;
A544:          BSET    L0044,#$08			; SET b3, 1st DRP VALID

A547:          JMP     LAC51
 

A54A:  LA54A   BRSET   L004F,#$10,LA551		; BR IF b4, RUN FUEL
											;
A54E:          JSR     LA581
A551:  LA551   LDD     L3FC0
A554:          CPD     L4133				; 450 RPM BYPASS TO RUN ENABLE IN REF PERIOD
A558:          BCS     LA560
A55A:          CLR     L0210
A55D:          JMP     LAC51
 ;
A560:  LA560   INC     L0210
A563:          LDAA    L0210
A566:          CMPA    L4142				; NUM CNT'S SPK RUN FLAG SET IF RPM GT 2 DRP'S
A569:          BCC     LA56E				; BR IF DRP GT 2

A56B:          JMP     LAC51				;
 ;
A56E:  LA56E   BSET    L004F,#$80			; SET b7, ENGINE RUNNING
											;
A571:          CLR     L0210
A574:          BSET    L0004,#$08			; SET b3, BAD SHUT DOWN

A577:          BCLR    L0051,#$40
A57A:          CLRA    
A57B:          CLRB    
A57C:          STD     L01F2				; START UP SPARK

A57F:  LA57F   BRA     LA5E5



A581:  LA581   LDD     L3FC0				; RPM = ((65536 * 120)/8)/CAL
A584:          CPD     L4135				; 300 RPM, IN REF PERIOD FOR CRANK TO RUN FUEL ENABLE
A588:          BCC     LA596				: BR IF RPM GT THRESH
											; 
A58A:          LDAA    L0211				; Counter
A58D:          INCA    						; INC Counter
A58E:          CMPA    L4143				; CNT'S FUEL RUN FLG  IF RPM G.T. 2 DRP'S
A591:          BCS     LA597
											;
A593:          BSET    L004F,#$10			; SET b4, RUN FUEL
											;
A596:  LA596   CLRA    
A597:  LA597   STAA    L0211

A59A:          RTS     
 		; ------------------------------------------

			;-----------------------------------------
			; FUEL PUMP AT START UP ROUTINE
			;
			; MY95, L19
			; TYPE $31 (12.5 msec loop)
			;-----------------------------------------
A59B:  LA59B   LDX     L0260				; FUEL PUMP RUN TIMER 
A59E:          CPX     L4962 				; 3 SEC'S,  DISABLE FUEL PUMP 
											;			IF NO DRPS FOR 3-2 Sec's
A5A1:          BCC     LA5A9				; BR IF TIME GT THRESH
											;
A5A3:          INX     						; INCR TIMER, (12.5 msec loop) 
A5A4:          STX     L0260				; SAVE NEW FUEL PUMP RUN TIMER VALUE

A5A7:          BRA     LA5AD


			;
			; CLEAR FUEL PUMP RELAY SIGNAL
			;
A5A9:  LA5A9   CLRA    
A5AA:          STAA    L306F
A5AD:  LA5AD   CPX     #0160				; 2sec's ?
A5B0:          BCS     LA5BE				; BR IF TIMER LT 2 SEC'S
											;
A5B2:          SEI     						; SECURE INTERUPTS
											;
A5B3:          LDAA    L4D96 				; IF STALL, INIT CRANK DRP COUNTER = 5
A5B6:          CMPA    L02CE				; DRP COUNTER
A5B9:          BCC     LA5BE				; BR IF DPR CNT'R LT 2
											;
A5BB:          STAA    L02CE				; DRP COUNTER

A5BE:  LA5BE   CLI     						; RESTORE INTRUPTS
     
A5BF:          LDAA    L0202
A5C2:          CMPA    #23
A5C4:          BCS     LA5DA				; BR IF CNT LT 23
											;
A5C6:          BCLR    L004F,#$90			; CLR b7 & b4
A5C9:          BCLR    L0044,#$08			; CLR b3,  1 = 1st DRP VALID

A5CC:          LDD     #$FFFF				; FORCE MAX DRP PERIOD
A5CF:          STD     L005F				; LAST DRP PERIOD

A5D1:          LDX     #$3060				; I/O PORT ???
A5D4:          BCLR    0,X,#$10				; CLR b4, 


                **********************************
                * LOOP HERE TILL INTERUPT
                **********************************
A5D7:  LA5D7   SWI     

A5D8:          BRA     LA5D7
                **********************************

			;----------------------------------------------
			;
			;
			;
			;----------------------------------------------
A5DA:  LA5DA   BRSET   L004F,#$80,LA5E1		; BR IF b7, ENGINE RUNNING
											;
A5DE:          JMP     LAC51


A5E1:  LA5E1   INCA                       ; INC CNT'R    
A5E2:          STAA    L0202

                *********************************
                * EST MONOR LOOP
                *
                *********************************
                ;----------------------
                ; CALC RPM
                ; RPM/25 AND RPM 12/5
                ; PERIOD = 1/65.535 Khz
                ;----------------------
A5E5:  LA5E5   LDD     L3FC0				; LAST DRP PERIOD CNTR
											; RPM = ((65536 * 120)/8)/CAL
A5E8:          STD     L005F				; LAST DRP PERIOD VAL
A5EA:          STD     L01E8				; LAST DRP PERIOD VAL
											;
A5ED:          LDX     #$005F				; LAST DPR PERIOD VAL, (MLT'CND)
A5F0:          LDAA    L4141				; 8 CYLS, (MULTIPLIER)
A5F3:          LDAB    #$0020				;
A5F5:          MUL     						; 32 * 8 = 256 or 0     
A5F6:          TBA     						;
A5F7:          BEQ     LA5FE				; BR IF Z
											;
A5F9:          JSR     LF550				; MUL 8X16 Subroutine


A5FC:          STD     L005F				; SAVE 16 BIT RPM VALUE
											;
A5FE:  LA5FE   LDD     L005F				; LAST DRP PERIOD VAL
A600:          ASLD    						; MULT * 2
A601:          XGDX    						;
A602:          LDD     #$0133				; 15 * (512/25) 65.5Khz CLK
A605:          FDIV    
A606:          XGDX    
A607:          STD     L083D

A60A:          CMPA    #96					; 2400 RPM
A60C:          BCS     LA617				; IF <= 2400 RPM, (LOW RANGE)
											;
A60E:          ADDD    #65512             	; ROUND AND ADJ TO 
A611:          BCC     LA61E				; IF HIGH RANGE, (NO OVERFLOW)
											;
A613:          LDAA    #255					; 4800 RPM DEFAULT VALUE LIMIT

A615:          BRA     LA61E
 

A617:  LA617   ASLD    						; MULT * 2, (RPM/12.5) 
A618:          SUBD    #$1F80				;
A61B:          BCC     LA61E				; IF NO OVER FLOW

        ;-------------
        ; HIGH RANGE
        ;-------------
A61D:          CLRA    
A61E:  LA61E   STAA    L0061				; RPM/25
											;
A620:          LDD     L083D				;
A623:          ADDD    #128					; ROUND OFF
A626:          SBCA    #000					;
A628:          STAA    L0062				; RPM/25; ENGINE RPM/25


        ;-------------------------
        ; FILTER RPM FOR GOVENOR
        ;-------------------------
A62A:          LDX     L028E				; OLD RPM/25
A62D:          LDAB    L50E4				; RPM FILTER COEF FOR GOVERNOR RPM
A630:          JSR     LF459				; LAG FILT ROUTINE
A633:          STD     L028E				; SAVE FLITERED RPM/25

A636:          ADDD    #128

A639:          LDAB    L0002				; MAJOR LOOP COUNTER
A63B:          ANDB    #$1F
A63D:          CMPB    #$0004
A63F:          BNE     LA64B
                                            ;                  
A641:          TAB     
A642:          SUBB    L028C
A645:          STAB    L028D
A648:          STAA    L028C
A64B:  LA64B   LDD     L083D
A64E:          ASLD    
A64F:          BCS     LA659
                                            ;                  
A651:          ASLD    
A652:          BCS     LA659
                                            ;                  
A654:          ADDD    #128
A657:          BCC     LA65B
                                            ;                  
A659:  LA659   LDAA    #255
A65B:  LA65B   STAA    L0067
A65D:          CLRB    
A65E:          LDX     L0068				; FILT RPM/?, (RPM DERIVITIVE)
A660:          BEQ     LA66C				;
                                            ;                  

		;
		;  RPM DERIVITIVE RPM FILTER
		;
A662:          LDX     #$0068				; FILT RPM/? (RPM DERIVITIVE)
A665:          LDY     #$4517				; 221d, FILT RPM COEF LIMIT,
											; (RPM derivitive)
A669:          JSR     LF479				; FILTER ROUTINE

A66C:  LA66C   STD     L0068				; SAVE FILT RPM/? (DERIVITIVE)

A66E:          LDD     L083D
A671:          ASLD    
A672:          BCC     LA677
											;
A674:          LDD     #$FFFF
A677:  LA677   STAA    L0837


		;
		; FILTER RPM/12.5 
		;
A67A:  LA67A   LDX     L0063				; OLD RPM/12.5 VALE
A67C:          BEQ     LA685				; BR IF RPM = Z
											;
A67E:          LDY     #$4153				; 0.938, RPM FILT TIME CONST
A682:          JSR     LF436				; LAG FILTER SUB ROUTINE, XMSIH
A685:  LA685   STD     L0063				; SAVE NEW FILT RPM/12.5 VALUE

A687:          LDAA    #255					; FORCE MAX VALUE

A689:          LDAB    L01C0				; GET CURRENT MAP VALUE
A68C:          SUBB    L01C2
A68F:          BCS     LA695
											;
A691:          CMPB    #32
A693:          BCC     LA6A4
											;
A695:  LA695   LDD     L01E6
A698:          SUBD    L01E8
A69B:          ASLD    
A69C:          SUBD    L01EA
A69F:          BMI     LA6A7
											;
A6A1:          ADDD    L01EA
A6A4:  LA6A4   STD     L01EA

A6A7:  LA6A7   LDD     L01E8
A6AA:          LSRD    
A6AB:          LSRD    
A6AC:          LSRD    
A6AD:          SUBD    L01EA
A6B0:          BCC     LA6B8
											;
A6B2:          ADDD    L01EA
A6B5:          STD     L01EA

A6B8:  LA6B8   LDD     L01E8
A6BB:          STD     L01E6

A6BE:          LSRD    
A6BF:          SUBD    #229
A6C2:          BCC     LA6C9
											;
A6C4:          ADDD    #0308

A6C7:          BRA     LA6D9



A6C9:  LA6C9   LSRD    
A6CA:          SUBD    #0295
A6CD:          BCS     LA6D4
A6CF:          ADDD    #0382
A6D2:          BRA     LA6D9
 ;
A6D4:  LA6D4   ADDD    #1527
A6D7:          LSRD    
A6D8:          LSRD    
A6D9:  LA6D9   STD     L083F
A6DC:          LDAA    #120					; 2.4 VDC
A6DE:          SUBA    L00A7   				; BAT VOLTS, VDC/10
A6E0:          BCC     LA6E3				; BR IF BATT V LT THRESH

A6E2:          CLRA    

A6E3:  LA6E3   LDAB    #4
A6E5:          MUL     
A6E6:          ADDD    L083F
A6E9:          ADDD    L01EA
A6EC:          STD     L01EC

A6EF:          LDD     L3FC0
A6F2:          SUBD    #39
A6F5:          SUBD    L01EC
A6F8:          BCC     LA700

A6FA:          ADDD    L01EC
A6FD:          STD     L01EC

A700:  LA700   LDAB    L01C1
A703:          STAB    L01C2

A706:          LDAB    L01C0				; GET CURRENT MAP VALUE
A709:          STAB    L01C1

    	;----------------------------------------------
    	; OPEN THROTTLE SPARK Vs. MAP Vs. RPM
    	;  
    	;  BIAS =  0  Deg
    	;  TBL = (SPK + BIAS) * (256/90)
    	;----------------------------------------------
A70C:          LDX     #$4166				; OPEN TPS SPK 
											; 
A70F:          BRCLR   L0050,#$40,LA716		; BR IF NOT b6, OPEN TPS SPK
											;


    	;----------------------------------------------
    	;  CLOSED THROTTLE SPARK Vs. MAP Vs. RPM 
    	;  
    	;  TYPE   $31 ECM
    	;  
    	;  BIAS =  0  Deg
    	;  TBL = (SPK + BIAS) * (256/90)
    	;----------------------------------------------
A713:          LDX     #$428A				; INDEX CLOSED TPS SPARK TABLE

A716:  LA716   LDAB    L01C0				; GET CURRENT MAP VALUE

A719:          LDAA    L0061				; RPM/25
A71B:          CMPA    #64					; 1600 RPM, 
A71D:          BLS     LA727			    ; BR IF RPM LT 1600 RPM
											;
A71F:          LDAA    L0062				; ENGINE RPM/25
A721:          ADDA    #16					; 400 RPM, MIN TBL VAL
A723:          BCC     LA727
											;
A725:          LDAA    #255					; FORCE MAX VAL FOR RPM

A727:  LA727   JSR     LF4DE				; 3d LK UP
A72A:          STAA    L01F8

A72D:          LDX     #$43AE
A730:          LDAB    L01C9				; Kpa VACUUM

A733:          LDAA    0,X
A735:          BEQ     LA73A
											;
A737:          LDAB    L01C0				; GET CURRENT MAP VALUE

A73A:  LA73A   INX     
A73B:          LSRB    
A73C:          LDAA    L0006				; COOL VALUE
A73E:          CMPA    #176
A740:          BLS     LA74B
											;
A742:          CMPA    #208
A744:          BLS     LA748
											;
A746:          LDAA    #208
A748:  LA748   SUBA    #88
A74A:          ASLA    

A74B:  LA74B   JSR     LF4DE				; 3d LK UP

A74E:          LDAB    L0050
A750:          BPL     LA761
											;
A752:          LDAB    L0006				; COOL VALUE
A754:          CMPB    L4140
A757:          BCC     LA761
											;
A759:          CMPA    L413C				; 20 DEG  COOLANT SPK BIAS
A75C:          BCC     LA761
											;
A75E:          LDAA    L413C
A761:  LA761   STAA    L01F9

			;-----------------------------------------                         
			; AFR MD BYTE 3, 1000 0010
			;
			; b7 1 = SINGLE PASS EGR TEST
			; b6 1 = VATS
			; b5 1 = USE L4479 TBL FOR %EGR
			; b4 1 = EGR = 0 AT IDLE
			;
			; b3 1 = OPN LP FUEL DISABLE EGR
			; b2 1 = BACK PRESS EGR
			; b1 1 = LINEAR EGR/ 0 = EVRV EGR
			; b0 1 = USE TBL L4BA9 FOR CLS LP AFR
			;        IF COOL L.T. L48C0
			;-----------------------------------------
A764:          LDAA    L400D
A767:          BITA    #$04					; BACK PRESS EGR
A769:          BEQ     LA77A				; BR IF NOT BP EGR

    	;---------------------------------------------
    	; ALTITUDE SPK ADV CORR vs BARO & VAC
    	;
    	;  Dissassemby of BMHM
    	;
    	; TBL = (SPK + BAIS) * 256/90
    	;---------------------------------------------
A76B:          LDAA    L01CC				; BARO VALUE (Kpa)
A76E:          LDAB    L01C9				; Kpa VACUUM
A771:          LDX     #$44D5				; ALTITUDE SPK ADV CORR TBL
A774:          JSR     LF4DE				; 3d LK UP
A777:          STAA    L01FB				; SAVE ALT COMP SPK



    	;---------------------------------------------
    	; LOW OCTAINE SPK RETARD MULT vs MAP
    	;
    	; APPLIED TO BASE SPARK RETARD
    	;
    	;  Dissassemby of BDKJ
    	;  12-01-1993, 13:47:46
    	;
    	; TBL = MULT * 2.56
    	;---------------------------------------------
A77A:  LA77A   LDAB    L0841

A77D:          LDAA    L01C0				; GET CURRENT MAP VALUE
A780:          LDX     #$45C7				; LOW OCTAINE SPK RETARD MULT
A783:          JSR     LF4C1				; 2d LK UP
A786:          MUL     						; APPLY MULT
A787:          ADCA    #$00					; ROUND OFF
											;
A789:          LDAB    L020A				;
A78C:          MUL     						;
A78D:          ADCA    #$00					; ROUND OFF
A78F:          STAA    L020B				; LOW OCTAINE SPK RETARD 


A792:          LDAA    L413E				; 0  DEG  EGR BIA
A795:          CLRB    						
A796:          BRCLR   L006E,#$80,LA7D4		; BR IF NOT b7,	 EGR ON

     	;----------------------------------------------
     	; EGR SPK CORRECTION vs RPM & LOAD
     	; (Load = %EGR OR Vac)
     	;
     	; SEE BIAS AT L413A, (0 DEG)
     	;
     	; 13 X 5 LINES
     	; TABLE = SPK * 256/90
     	;----------------------------------------------
A79A:          LDX     #$485F				; EGR SPK CORRECTION vs RPM & LOAD

A79D:          LDAB    L01B2				;
A7A0:          LDAA    #192					; 
A7A2:          MUL     
A7A3:          TAB     
A7A4:          LDAA    0,X
A7A6:          BEQ     LA7BE				; Check Load Select (EGR or VAC)
											;
A7A8:          LDAB    L01C9
A7AB:          NEGB    
A7AC:          CMPB    #64
A7AE:          BHI     LA7B3
											;
A7B0:          ASLB    

A7B1:          BRA     LA7BE
 

A7B3:  LA7B3   SUBB    #64
A7B5:          LSRB    						; N/2
A7B6:          ADDB    #127
A7B8:          CMPB    #192
A7BA:          BLS     LA7BE
											;
A7BC:          LDAB    #160

A7BE:  LA7BE   LDAA    L0062				; ENGINE RPM/25
A7C0:          CMPA    #160					; 4000 RPM 
A7C2:          BLS     LA7C6
											;
A7C4:          LDAA    #160					; 4000 RPM 
A7C6:  LA7C6   LSRA    
A7C7:          INX     
A7C8:          JSR     LF4DE				; 3d LK UP

			;
			; FITER
			;
A7CB:          LDAB    L485E				; EGR ON SPARK FILTER COEF
A7CE:          LDX     L01F4				; GET OLD SPARK 
A7D1:          JSR     LF459				; LAG FILTER
A7D4:  LA7D4   STD     L01F4				; SAVE NEW SPARK



			;
			; ADD SPARK VALUES
			;
A7D7:          ADDD    #128
A7DA:          TAB     

A7DB:          LDX     #$0000				; ZERO OUT MAIN SPARK ADVANCE
A7DE:          ABX      					; ADD TO MAIN SPK    
A7DF:          LDAB    L01FB				; ALT COMP SPK
A7E2:          ABX     						; ADD TO MAIN SPK     
A7E3:          LDAB    L01F8
A7E6:          ABX     						; ADD TO MAIN SPK     
A7E7:          LDAB    L01FC				; FROM TABLE L44BF
A7EA:          ABX     						; ADD TO MAIN SPK     
A7EB:          LDAB    L01F9
A7EE:          ABX     						; ADD TO MAIN SPK     
A7EF:          LDAB    L02CB				; START UP SPK ADV
A7F2:          ABX     						; ADD TO MAIN SPK
A7F3:          XGDX    						;

			;
			; SUB OFF SPARK BIAS VALUES
			; (RETARD)
			;
A7F4:          SUBB    L413B				;  0 Deg  MAIN SPK BIAS
A7F7:          SBCA    #$00					;
A7F9:          SUBB    L413C				; 20 Deg  COOLANT SPK BIAS
A7FC:          SBCA    #$00					;
A7FE:          SUBB    L413D				; 10 Deg  BIAS ALT ADV CORR BIAS
A801:          SBCA    #$00					;
A803:          SUBB    L413E				; 0  Deg  EGR BIAS 
A806:          SBCA    #$00					; 

A808:          BRCLR   L00A4,#$0F,LA811		; BR IF NOT 0000 1111
											;
A80C:          SUBB    L55F2				; GEAR, CURRENT GEAR
A80F:          SBCA    #$00					;
A811:  LA811   SUBB    L020B				; LOW OCTAINE SPK RETARD
A814:          SBCA    #$00					;
A816:          SUBB    L015A				; 
A819:          SBCA    #$00					; 
A81B:          STD     L01FD				; FINAL SPK  ADV

    	;----------------------------------------------
    	; MAT SPK ADV CORRECTION  Vs. MAP
    	; FOR NEGITIVE SPK ADVANCE
		;
		;
		; TBL = 2.56 * MULT 
    	;---------------------------------------------
A81E:          LDAA    L01C0				; GET CURRENT MAP VALUE
										    ;
A821:          LDX     #$449D				; 0'ed OUT TABLE
											;
A824:          BRSET   L0041,#$02,LA82B		; BR IF NOT b1, 


A828:          LDX     #$44AE				; 0'ed OUT TABLE
A82B:  LA82B   JSR     LF4C1				; 2d LK UP

A82E:          LDAB    L01FA
A831:          MUL     						; APPLY MULT 
A832:          STAA    L083C

A835:          BRCLR   L0041,#$02,LA846		; BR IF NOT b1

A839:          LDD     L01FD				; FINAL SPK  ADV
A83C:          SUBB    L083C
A83F:          SBCA    #$00
A841:          STD     L01FD				; FINAL SPK  ADV				

A844:          BRA     LA84E


A846:  LA846   TAB     
A847:          LDX     L01FD				; FINAL SPK  ADV
A84A:          ABX     
A84B:          STX     L01FD				; FINAL SPK  ADV

A84E:  LA84E   LDX     L00FD				; RUN TIMER
A850:          CPX     L415E				; 0 SEC MIN RUN TIME FOR IDLE SPK
A853:          BCC     LA857				; BR IF TIMER gt THRESH
											;
A855:          BRA     LA8B1

    	;----------------------------------------------
    	; UNDER SPEED IDLE SPK ADV vs RPM ERR
		;
    	; TBL =  2.844  * Deg Spk
    	;----------------------------------------------
A857:  LA857   LDX     #$4502				; UNDER SPEED IDLE SPK ADV
											;
A85A:          LDAA    L0284				; MPH/1
A85D:          CMPA    L415A				; 3 MPH MAX FOR IDLE SPK
A860:          BCC     LA8B1				; BR IF Vss GT THRESH 
											;
A862:          LDAA    L415B				; 1.9% TPS MAX FOR IDLE SPK
											;
A865:          BRCLR   L0050,#$40,LA86C		; BR IF NOT b6, OPEN TPS SPK
											;
A869:          LDAA    L415C				; 1.5% TPS MAX FOR IDLE SPK
A86C:  LA86C   CMPA    L01D9				; %TPS
A86F:          BHI     LA873				;
											;
A871:          BRA     LA8B1
 

A873:  LA873   LDAB    L0006				; COOL VALUE
A875:          CMPB    L415D				; -40 DEG c MIN FOR IDLE SPK
A878:          BLS     LA8B1				; BR IF COOL LT THRESH

A87A:          CLRB    						;
											;
A87B:          LDAA    L0857  				; DESIRED IDLE RPM/12.5
											;
A87E:          BRSET   L0050,#$80,LA88E		; BR IF b7, IDLE
											;
A882:          ADDA    L4160				; 0 RPM OFFSET TO DESIRED RPM IF NOT AT IDLE
A885:          BCC     LA88E				; BR IF NO OVERFLOW

A887:          BCLR    L0053,#$01			;
											;
A88A:          SUBD    L0063				; RPM/12.5

A88C:          BRA     LA8B1



A88E:  LA88E   SUBD    L0063				; RPM/12.5
A890:          BCS     LA897				; BR IF UNDERFLOW
											;
A892:          BCLR    L0053,#$01

A895:          BRA     LA8A1
 

A897:  LA897   BSET    L0053,#$01

A89A:          NEGA    
A89B:          NEGB    
A89C:          SBCA    #$00

    	;---------------------------------------------
    	; IAC OVERSPEED SPARK RETARD CORRECTION
    	; (SPK RETARD Vs. RPM ERR)
    	;
		; LINES = 7
		;
    	; TBL = SPK ADV 256/90
    	;---------------------------------------------
A89E:          LDX     #$44F0			    ;
A8A1:  LA8A1   PSHX   						;
 											;
A8A2:          ASLD    						;
A8A3:          BCS     LA8AD				; BR IF OVERFLOW
											;
A8A5:          CMPA    #8					;
A8A7:          BCS     LA8B7				;
											;
A8A9:          ADDA    #56					;
A8AB:          BCC     LA8BA				; BR IF NO OVERFLOW
											;
A8AD:  LA8AD   LDAA    #255					; FORCE MAX VALUE

A8AF:          BRA     LA8BA


A8B1:  LA8B1   BCLR    L0050,#$40			; CLR b6, OPEN TPS SPK6, 

A8B4:          JMP     LA906
 
 
A8B7:  LA8B7   ASLD    						; n x 8
A8B8:          ASLD    
A8B9:          ASLD 
   
A8BA:  LA8BA   JSR     LF499

A8BD:          PULX    
A8BE:          PSHA    

A8BF:          LDAB    #$0008
A8C1:          ABX     

A8C2:          LDAA    L01C0				; GET CURRENT MAP VALUE

A8C5:          JSR     LF499

A8C8:          PULB    
A8C9:          MUL     
A8CA:          BRCLR   L0053,#$01,LA8CF
A8CE:          NEGA    
A8CF:  LA8CF   PSHA   
 
		;-----------------------------------------
		; DERIVATIVE SPK/FUEL IDLE SA Vs. RPM RATIO
		;
		; IDLE SA vs RPM RATIO
		;
		; VAL = DEG + K L4514 (0 Deg spk bias)
		;---------------------------------------------
A8D0:          LDX     #$451B				;
A8D3:          LDAA    L006C				; RPM RATIO
A8D5:          SUBA    #96					;
A8D7:          BCC     LA8DC				; BR IF RPM RATIO GT 96
											;
A8D9:          CLRA    						; CLR RPM RATIO
A8DA:          BRA     LA8E2
 ;
A8DC:  LA8DC   CMPA    #63					; 
A8DE:          BLS     LA8E2				; BR IF RPM RATIO LT 63
											;
A8E0:          LDAA    #63					; RPM RATIO = 63
A8E2:  LA8E2   ASLA    						; X4
A8E3:          ASLA    						;
A8E4:          JSR     LF4C1				; 2d LK UP
A8E7:          PULB    
A8E8:          ABA     
A8E9:          SUBA    L4514				; 0 Deg, IDLE SPK BIAS FOR TBL L451B
A8EC:          BMI     LA8FA				; BR IF IDLE SPK ...
											;
A8EE:          CMPA    L4515				; 0 Deg, MAX IDLE SPK
A8F1:          BLS     LA8F6
											;
A8F3:          LDAA    L4515				; 0 Deg, MAX IDLE SPK
A8F6:  LA8F6   TAB     
A8F7:          CLRA 
   
A8F8:          BRA     LA8FD


A8FA:  LA8FA   TAB     

A8FB:          LDAA    #255					; FORCE MAX VALUE
A8FD:  LA8FD   ADDD    L01FD				; FINAL SPK  ADV
A900:          STD     L01FD				;
											;
A903:          BSET    L0050,#$40			; SET b6, OPEN TPS SPK
											;
A906:  LA906   LDAA    L0006				; COOL VALUE
A908:          CMPA    L46F2				; -40c COOL
A90B:          BCS     LA97A				; BR IF COOL ...

A90D:          CMPA    L46F3				; -40c COOL
A910:          BHI     LA97A				; BR IF COOL ...

A912:          LDAA    L400F				; MODE WD
A915:          BITA    #$80					; b7, 1 = MAN, (0 = TCC)
A917:          BEQ     LA97A				; BR IF NOT b7
											;
A919:          BRCLR   L0050,#$80,LA926		; BR IF NOT b7, IDLE
											;
A91D:          LDAA    L0837
A920:          CLRB    
A921:          STD     L0838

A924:          BRA     LA97A

 

A926:  LA926   LDAA    L0063				; RPM/12.5
A928:          SUBA    L0838
A92B:          STAA    L083A				;  


		;----------------------------------------------
		; lk up ... Vs. %TPS
		;
		;----------------------------------------------
A92E:          LDX     #$46F4				;
A931:          LDAA    L01D9				; %TPS
A934:          LSRA    						; TPS/4
A935:          LSRA    
A936:          JSR     LF4C1				; 2d LK UP
A939:          TAB     
A93A:          LDAA    L0837
A93D:          LDX     L0838
A940:          JSR     LF459				; LAG FILTER
A943:          STD     L0838				; SAVE FILTERED

A946:          LDX     #$46EC
A949:          LDAA    L083A
A94C:          BPL     LA952
A94E:          INX     
A94F:          INX     
A950:          INX     
A951:          NEGA    
A952:  LA952   LDAB    0,X
A954:          MUL     
A955:          ADDA    1,X
A957:          CMPA    2,X
A959:          BLS     LA95D
											;
A95B:          LDAA    2,X
A95D:  LA95D   STAA    L083B

A960:          LDAA    L083A
A963:          BPL     LA96F
											;
A965:          LDD     L01FD				; FINAL SPK  ADV
A968:          ADDB    L083B
A96B:          ADCA    #$0000

A96D:          BRA     LA977


A96F:  LA96F   LDD     L01FD				; FINAL SPK  ADV
A972:          SUBB    L083B
A975:          SBCA    #$00
A977:  LA977   STD     L01FD				; FINAL SPK  ADV

A97A:  LA97A   LDD     L01FD				; FINAL SPK  ADV

A97D:          BRCLR   L0046,#$08,LA9A3		; BR IF NOT b3, DECEL FUEL C/O 
											;
A981:          BSET    L0051,#$20
A984:          CLRA    
A985:          CLRB    
A986:          STD     L01F2				; START UP SPARK

A989:          LDAB    L4152			    ; 15 DEG DECEL FOR CUT SPK ADV

A98C:          LDAA    L01F9
A98F:          SUBA    L413C				; 20 DEG  COOLANT SPK BIAS
A992:          BMI     LA996
											;
A994:          ABA     
A995:          TAB     
A996:  LA996   STAB    L0208

A999:          LDD     L01FD				; FINAL SPK  ADV
A99C:          SUBB    L0208
A99F:          SBCA    #$00

A9A1:          BRA     LA9DD

 
A9A3:  LA9A3   BRCLR   L0051,#$20,LA9E0
A9A7:          LDAB    L414F
A9AA:          LDAA    L01D9				; %TPS
A9AD:          CMPA    L4151
A9B0:          BLS     LA9B5

A9B2:          LDAB    L4150
A9B5:  LA9B5   LDX     L01F2				; START UP SPARK
A9B8:          CPX     #$FEF0
A9BB:          BHI     LA9C7

A9BD:          LDAA    #$00FF
A9BF:          JSR     LF459				; LAG FILTER
A9C2:          STD     L01F2

A9C5:          BRA     LA9CA



A9C7:  LA9C7   BCLR    L0051,#$20

A9CA:  LA9CA   LDAB    L0208
A9CD:          LDAA    L01F2				; START UP SPARK
A9D0:          MUL     
A9D1:          ADCA    #$0000
A9D3:          TAB     
A9D4:          CLRA    

A9D5:          ADDD    L01FD				; FINAL SPK  ADV
A9D8:          SUBB    L0208
A9DB:          SBCA    #$00
A9DD:  LA9DD   STD     L01FD				; FINAL SPK  ADV

A9E0:  LA9E0   BRCLR   L0086,#$40,LA9E7		; BR IF NOT HEADS UP
											;
A9E4:          JSR     L1812				; TO HEADS UP ROUTINE

         	;--------------------------------------
		 	; 0000 0001  IAC MD WD #2
		 	;
         	; b1 = 1 = PWR STEER SW IN USE
         	; b0 = 1 = INIT 16 BIT INTEGRALS FM 8 BIT WARM CELLS
         	;        = 0 = NORMAL INTEGRAL INIT
         	;--------------------------------------
A9E7:  LA9E7   LDAA    L4E90				; IAC MD WD #2
A9EA:          BITA    #$02					; b1
A9EC:          BEQ     LAA1A				; BR IF NOT b1
											;
A9EE:          BRCLR   L0036,#$20,LAA17		; BR IF NOT b5
A9F2:          LDAA    L0006				; COOL VALUE
A9F4:          CMPA    L4161				; 151c COOL THRESH FOR PWR STEER SPK
A9F7:          BLS     LAA17				; BR IF COOL LT THRESH
											;
A9F9:          LDAA    L01D9				; %TPS

A9FC:          BRSET   L0053,#$10,LAA07		; BR IF b4, PWR STEER CRAMP STALL SAVER
											;
AA00:          CMPA    L4164				; 0% TPS THRESH FOR SETTING PWR STEER SPK ADV
AA03:          BHI     LAA17
											;
AA05:          BRA     LAA0C


AA07:  LAA07   CMPA    L4165				; 0% TPS THRESH FOR EXITING PWR STEER SPK 
AA0A:          BHI     LAA17				; BR IF TPS 
											;
AA0C:  LAA0C   LDD     L4162				; 0 DEG PWR STEER FORCED SPK ADV
AA0F:          STD     L01FD				; FINAL SPK  ADV
									
AA12:          BSET    L0053,#$10			; SET b4, PWR STEER CRAMP STALL SAVER
											;
AA15:          BRA     LAA1A

AA17:  LAA17   BCLR    L0053,#$10			; CLR b4	
											;
			;
			; ACCOMDATE INITIAL DIST SETTING
			; AND CURRENT RETARD VALUES
			;											
AA1A:  LAA1A   LDD     L01FD				; FINAL SPK  ADV
AA1D:          SUBB    L4132				; SUB OFF, 3.8 Deg, INTIAL SPK (256/90)
AA20:          SBCA    #$00					; 
AA22:          STD     L01EE				; CURRENT RESTARD (2's CMP)
											;
AA25:          LDD     L4144				; MAX ADV 42 DEG
AA28:          SUBD    L01EE				; CURRENT RETARD (2's CMP)
AA2B:          BGT     LAA33				;
											;
AA2D:          ADDD    L01EE				; CURRENT RETARD (2's CMP)
AA30:          STD     L01EE				; CURRENT RETARD (2's CMP)

			;------------------------------------
			; CK IF BURST KNOCK IS SELECED
			;
			;------------------------------------
AA33:  LAA33   LDAA    L400F				; AFR MD BYTE 5, 0001 0000, (DIG I/O) <---***
AA36:          BITA    #$08					; b3,  1 = BURST KNOCK RETARD SELECTED
AA38:          BEQ     LAA81				; BR IF NOT b8
											;
AA3A:          BRSET   L0050,#$10,LAA81		; BR IF NOT b4
											;
AA3E:          LDAA    L0006				; COOLANT VALUE
AA40:          CMPA    L45DA				; 35 c MIN COOL FOR SPK RETARD
AA43:          BLS     LAA81				;
											;
AA45:          BRCLR   L006E,#$02,LAA5E		; BR IF NOT b1, BURST KNOCK RETARD ACTIVE
											;
AA49:          DEC     L020E
AA4C:          BNE     LAA51				;
											;
AA4E:          BCLR    L006E,#$02			; CLR b1, BURST KNOCK RETARD ACTIVE 

AA51:  LAA51   LDD     L01EE				; CURRENT RESTARD (2's CMP
AA54:          SUBB    L0842				;
AA57:          SBCA    #$00					;
AA59:          STD     L01EE				; CURRENT RESTARD (2's CMP

AA5C:          BRA     LAA81

			;
			; BURST KNOCK PARAM'S
			;
AA5E:  LAA5E   LDAA    L01C0				; GET CURRENT MAP VALUE 
AA61:          CMPA    L46DF				; 50 Kpa MAX MAP FOR BURST KNK RETARD
AA64:          BCC     LAA81				;
											;
AA66:          LDAB    L01D9				; %TPS
AA69:          CMPB    L46E0				; 14.8% TPS MAX TPS FOR BURST KNK RETARD
AA6C:          BCC     LAA81				;
											;
AA6E:          SUBB    L01DA			    ;
AA71:          BCS     LAA81				;
											;
AA73:          CMPB    L46E1				; 4.2% DIFF TPS MIN FOR BURST KNK RETARD
AA76:          BCS     LAA81				;
											;
AA78:          BSET    L006E,#$02			; SET b1  BURST KNOCK RETARD ACTIVE
AA7B:          LDAA    L46E2				; 262 Msec's PERIOD FOR BURST KNK RETARD
AA7E:          STAA    L020E

AA81:  LAA81   SEI     
AA82:          LDAB    L020D
AA85:          CLR     L020D
AA88:          CLI     
AA89:          BRSET   L006E,#$02,LAA9A		; BR IF b1,	BURST KNOCK RETARD ACTIVE
											;
AA8D:          BRCLR   L0016,#$60,LAA93		; BR IF NOT b5 & b4
											;
AA91:          BRA     LAA9D



AA93:  LAA93   LDAA    L0006				; COOLANT VALUE
AA95:          CMPA    L45DA				; 35 c MIN COOL FOR SPK RETARD
AA98:          BCC     LAA9D				; BR IF COOL < 35c
											;
AA9A:  LAA9A   CLRA    
AA9B:          BRA     LAACB

AA9D:  LAA9D   LDAA    L0284				; Vss/1
AAA0:          CMPA    L45D8				; 2 MPH MIN VSS FOR SPK RETARD
AAA3:          BCC     LAAAC				; BR IF Vss < 2 MPH

AAA5:          LDAA    L0063				; RPM/12.5 
AAA7:          CMPA    L45D9				; 800 RPM MIN FOR SPK RETARD
AAAA:          BCS     LAADC				; BR IF RPM < 800 RPM

AAAC:  LAAAC   BRCLR   L0019,#$10,LAAB5		; BR IF NOT b4, KNOCK SENSOR ERR 



			;
			; SET KNOCK SENSOR FAIL DEFAULT VALUE
			; (4 Deg)
			;
AAB0:          LDAA    L4E77				; 4 DEG, KNK FAIL RETARD

AAB3:          BRA     LAACB
 

AAB5:  LAAB5   LDAA    L0843				; KNOCK RECOVERY RATE vs RPM
AAB8:          MUL     
AAB9:          ASLD    						; n x2
AABA:          BCS     LAAC1				;

AABC:          ADDA    L020C				; Deg, KNOCK RETARD
AABF:          BCC     LAAC3				;

AAC1:  LAAC1   LDAA    #255					; FORCE MAX VALUE
AAC3:  LAAC3   TAB     
AAC4:          LDAA    L0844				; MAX KNOCK RETARD NOT IN WOT vs VAC
AAC7:          CBA     
AAC8:          BLS     LAACB				;

AACA:          TBA     

AACB:  LAACB   STAA    L020C				; DEG, KNOCK RETARD
AACE:          LSRA    
AACF:          PSHA    
AAD0:          TSX     

AAD1:          LDD     L01EE				; CURRENT RESTARD (2's CMP
AAD4:          SUBB    0,X
AAD6:          SBCA    #$00
AAD8:          STD     L01EE				; CURRENT RESTARD (2's CMP

AADB:          INS     

AADC:  LAADC   LDAA    L015A				;
AADF:          BEQ     LAAF7				; BR IF ... = Z
											;
AAE1:          LDD     L414A				; MAX RETARD DURING TORQUE MANAGMENT FUEL C/O

AAE4:          BRSET   L00A4,#$08,LAAEF		;
											;
AAE8:          BRCLR   L00A4,#$17,LAAF7		;
											;
AAEC:          LDD     L414C				; 0,  MAX RETARD DURING TQ MANAGMENT FUEL C/O
AAEF:  LAAEF   CPD     L01EE				; CURRENT RESTARD (2's CMP
AAF3:          BLT     LAB1A				;
											;
AAF5:          BRA     LAB17
 


AAF7:  LAAF7   BRCLR   L0051,#$20,LAB0E		; BR IF NOT b5,
											;
AAFB:          LDAA    L01D9				; %TPS
AAFE:          CMPA    L48DA				; 2.3% TPS MAX IDLE FUEL TABLE
AB01:          BHI     LAB0E				; BR IF TPS GT THRESH
											;
AB03:          LDD     L4148				;     DEG, MAX RETARD DURING FUEL C/O
AB06:          CPD     L01EE				; CURRENT RESTARD (2's CMP
AB0A:          BLT     LAB1A				;
											;
AB0C:          BRA     LAB17
 

AB0E:  LAB0E   LDD     L4146				; MAX RETARD
AB11:          CPD     L01EE				; CURRENT RESTARD (2's CMP)
AB15:          BLT     LAB1A				;
											;
AB17:  LAB17   STD     L01EE				; CURRENT RESTARD (2's CMP
AB1A:  LAB1A   LDD     L01EE				; CURRENT RESTARD (2's CMP

				;
				; SERIAL DATA MD WORD
				;  CK FOR  ENG CONTROLLER MODE
				;
AB1D:          BRCLR   L003B,#$10,LAB3E		;
											;
AB21:          LDX     #$0395				;
AB24:          BRCLR   0,X,#$08,LAB3E		;
											;
AB28:          BRSET   0,X,#$10,LAB2E		;
											;
AB2C:          CLRA    
AB2D:          CLRB    
AB2E:  LAB2E   BRSET   0,X,#$20,LAB39
AB32:          ADDB    L0398
AB35:          ADCA    #$0000
AB37:          BRA     LAB3E
 ;
AB39:  LAB39   SUBB    L0398
AB3C:          SBCA    #$0000

AB3E:  LAB3E   STD     L01EE				; CURRENT RESTARD (2's CMP
AB41:          STD     L01F0				;
AB44:          BCLR    L004F,#$01			; CLR b0, 1 = RETARD, 0 = ADVANCE
											;
AB47:          LDD     L01EE				; CURRENT RESTARD (2's CMP
AB4A:          BPL     LAB50				;
AB4C:          BSET    L004F,#$01			; SET b0, 1 = RETARD, 0 = ADVANCE
											;
AB4F:          NEGB    						;
AB50:  LAB50   TBA     						;
AB51:          BRSET   L0051,#$40,LAB62		; BR IF 
											;
AB55:          LDAB    L01F2				; START UP SPARK
AB58:          LDX     #$01F3				;
AB5B:          BRCLR   0,X,#$80,LAB60		; BR IF		
											;
AB5F:          INCB    						; 
AB60:  LAB60   MUL     						;
AB61:          INCA    						;
AB62:  LAB62   BRCLR   L0086,#$40,LAB69		; BR IF	NOT HEADS UP
											;
AB66:          JSR     L180F				; BR TO HEADS UP

        ;---------------------------------------------
    	; LK UP SPARK LATENCIES
    	; 5.7L V8 TYPE $0D ECM
    	;
		;
		;--------------------------------------------------
AB69:  LAB69   PSHA    
AB6A:          LDAA    L0062				; ENGINE RPM/25
AB6C:          LDX     #$454A				; INDEX TBL 
AB6F:          JSR     LF499				; 2D LK UP ENTRY

AB72:          STAA    L0201

AB75:          PULA    
AB76:          LDX     #$005F				; LAST DPR PERIOD VAL ADDR, (MLT'CND)
AB79:          JSR     LF550				; MUL 8X16 Subroutine


AB7C:          BRSET   L004F,#$01,LAB84   	; BR IF b0, 1 = RETARD, 0 = ADVANCE
											;
AB80:          NEGA    
AB81:          NEGB    
AB82:          SBCA    #$00
AB84:  LAB84   SUBB    L0201
AB87:          SBCA    #$00
AB89:          PSHB    
AB8A:          PSHA    
AB8B:          TSX     
AB8C:          CLRA    
AB8D:          CLRB    
AB8E:          SUBD    L3FC0
AB91:          LSRD    
AB92:          LSRD    
AB93:          LSRD    
AB94:          LSRD    
AB95:          ORAA    #$F0
AB97:          ADDD    L3FF6				; EST FALL CNT'R
AB9A:          SUBD    0,X
AB9C:          BMI     LABA2
AB9E:          ADDD    0,X
ABA0:          STD     0,X

ABA2:  LABA2   LDD     0,X
ABA4:          SUBD    L3FF6				; EST FALL CNT'R
ABA7:          JSR     LF3ED				; Very short delay (RTS)
ABAA:          STD     L3FE8				

ABAD:          JSR     LF3ED				; Very short delay (RTS)

ABB0:          ADDD    L3FDC
ABB3:          SUBD    L01EC
ABB6:          NOP     
ABB7:          LDX     L01EC
ABBA:          STD     L3FE6

ABBD:          JSR     LF3ED				; Very short delay (RTS)

ABC0:          STX     L3FDC

ABC3:          JSR     LF3ED				; Very short delay (RTS)			

ABC6:          PULA    
ABC7:          PULB    
ABC8:          STD     L3FF6              	; EST FALL CNT'R

                    ;---------------------------------    
					; MINOR LOOP MODE WD	
                    ; 	b3 1 = 1st DRP VALID 
                    ;---------------------------------    
ABCB:          BRCLR   L0044,#$08,LAC31		; BR IF NOT b3, 1st DRP VALID

ABCF:          BRCLR   L0050,#$04,LAC10		; BR IF NOT b2, DRP OCCOURED 6.25msec TEST
											;
ABD3:          LDD     L3FCA
ABD6:          PSHB    
ABD7:          PSHA    
ABD8:          PULX 
   
  			;
			; CK IS EST ERR, (ERR 42)
			;
ABD9:          LDY     #$5B03				; 1011 1100, ERR WD 4 <---***
ABDD:          BRCLR   0,Y,#$20,LAC1C		; BR IF NOT b5, ERR 42, EST MONITOR ERROR
											;
ABE2:          BRSET   L004F,#$40,LAC25		; BR IF b6, MAJOR LOOP EST MONITOR ENABLE
											;
ABE6:          BRSET   L0044,#$80,LAC16		; BR IF b3, LOCKED IN ERR 42A

ABEA:          SUBD    L0205
ABED:          TSTA    
ABEE:          BNE     LABFE				;

ABF0:          CMPB    L4E71				; NUM PA1 CNT'S FOR ERROR
ABF3:          BHI     LABFE				;


ABF5:          BRSET   L0044,#$40,LAC1C		; BR IF b6, 1st GOOD ERR 42A FLAG
											;
ABF9:          BSET    L0044,#$40			; SET b6, 1st GOOD ERR 42A FLAG


ABFC:          BRA     LAC0D
 
 
 
ABFE:  LABFE   LDAB    L022C				; EST ERR CNT'R
AC01:          CMPB    L4E72				; 4, NUM EST ERR'S FR 42A
AC04:          BHI     LAC13				; 
											;
AC06:          INCB    						; INCR EST ERR CNT'R
AC07:          STAB    L022C				; EST ERR CNT'R
											;
AC0A:          BCLR    L0044,#$40			; CLR b6, 1st GOOD ERR 42A FLAG
											;
AC0D:  LAC0D   STX     L0205				;

AC10:  LAC10   JMP     LACA3				


AC13:  LAC13   BSET    L0044,#$80			; SET b3, LOCKED IN ERR 42A
											  
AC16:  LAC16   BSET    L0019,#$20			;

AC19:          JMP     LACA3				


AC1C:  LAC1C   BSET    L004F,#$40			; SET b6, MAJOR LOOP EST MONITOR ENABLE
											; 
AC1F:          CLR     L022C				;
AC22:          STX     L0205				;

                    ;---------------------------------    
					; MINOR LOOP MODE WD	
                    ; 	b3 1 = 1st DRP VALID 
                    ;---------------------------------    
AC25:  LAC25   BCLR    L0044,#$08			; CLR b3, 1st DRP VALID
											;
AC28:          LDX     L3FEC				;
AC2B:          JSR     LF3ED				; VERY SHORT DELAY
											;
AC2E:          STX     L3FE4				;
											;
AC31:  LAC31   BSET    L004B,#$10			; SET b4


					;----------------------------
					; MODE 1, WD #3, FLAGWORD,
					;		  b7 1 =  ERR 42 (EST) 
					;----------------------------
AC34:          BRCLR   L0004,#$80,LAC41		; BR IF NOT b7, ERR 42 (EST) 

AC38:          BRSET   L0044,#$04,LAC41		; BR IF b2, SKIP ERR 43 DUE TO ALDL
											;
AC3C:          BSET    L0019,#$20			; SET b2

AC3F:          BRA     LACA0
			;---------------------------------------------



				;
				; SERIAL DATA MD WORD
				;  CK FOR  ENG CONTROLLER MODE
				;
AC41:  LAC41   BRCLR   L003B,#$10,LACA3		; 
											;
AC45:          LDAA    L0391
AC48:          BITA    #$08
AC4A:          BEQ     LACA3

                    ;---------------------------------    
					; MINOR LOOP MODE WD	
                    ;	 b2 1 = SKIP ERR 43 DUE TO ALDL
                    ;---------------------------------    
AC4C:          BSET    L0044,#$04			; SET b2, SKIP ERR 43 DUE TO ALDL
											;
AC4F:          BRA     LACA0

AC51:  LAC51   LDX     #$FFFF

                    ;---------------------------------    
					; MINOR LOOP MODE WD	
                    ; 	b3 1 = 1st DRP VALID 
                    ;---------------------------------    
AC54:          BRCLR   L0044,#$08,LAC9E		; BR IF NOT b3, 1st DRP VALID
											;
AC58:          LDD     L3FC0
AC5B:          STD     L005F
AC5D:          STD     L01E8
AC60:          LDX     #$005F				; LAST DPR PERIOD ADDR,
											; 8, (8 CYL, 6 = 6 CYL
AC63:          LDAA    L4141

AC66:          LDAB    #32
AC68:          MUL     
AC69:          TBA     
AC6A:          BEQ     LAC71
											;
AC6C:          JSR     LF550 				; MUL 8X16 Subroutine

AC6F:          STD     L005F				; LAST DPR PERIOD
AC71:  LAC71   LDD     L005F				; LAST DPR PERIOD
AC73:          ASLD    						; x2
AC74:          XGDX    
AC75:          LDD     #$0133
AC78:          FDIV    
AC79:          PSHX    
AC7A:          PULA    
AC7B:          PULB    
AC7C:          CMPA    #$0060
AC7E:          BCS     LAC89
											;
AC80:          ADDD    #$4080
AC83:          BCC     LAC90
AC85:          LDAA    #255

AC87:          BRA     LAC90



AC89:  LAC89   ASLD    
AC8A:          SUBD    #$1F80
AC8D:          BCC     LAC90
AC8F:          CLRA    
AC90:  LAC90   STAA    L0061				; RPM/25
AC92:          PSHX    
AC93:          PULA    
AC94:          PULB    
AC95:          ADDD    #128
AC98:          SBCA    #$00
AC9A:          STAA    L0062				; ENGINE RPM/25
AC9C:          BRA     LACA0
 ;
AC9E:  LAC9E   STX     L005F
ACA0:  LACA0   BCLR    L004B,#$10
ACA3:  LACA3   BCLR    L0050,#$04		    ; CLR b2, DRP OCCOURED 6.25msec TEST

ACA6:          RTS     
			;-----------------------------------------



			;-----------------------------------------
ACA7:  LACA7   LDX     #$400E				; MODE WD, 0000 0000 AFR 4
ACAA:          BRSET   0,X,#$04,LACB1		; BR IF b2, (SHIFT LIGHT ENABLE)

ACAE:          JMP     LADA9
 ;

ACB1:  LACB1   BRCLR   L0050,#$10,LACBB		; bR IF NOT b4, DIAG SW IN DIAG POSIT.
											;
ACB5:          BRSET   L004F,#$80,LACBB		; BR IF b7, ENGINE RUNNING
											;
ACB9:          BRA     LACD0


				;
				; SERIAL DATA MD WORD
				;  CK FOR  ENG CONTROLLER MODE
				;
ACBB:  LACBB   BRCLR   L003B,#$10,LACD3
ACBF:          LDX     #$038F
ACC2:          BRCLR   0,X,#$01,LACD3

ACC6:          LDX     #$0390
ACC9:          BRSET   0,X,#$01,LACD0

ACCD:          JMP     LAD48


ACD0:  LACD0   JMP     LAD4D
 ;
ACD3:  LACD3   LDD     L3FE0
ACD6:          PSHB    
ACD7:          PSHA    
ACD8:          SUBD    L0847
ACDB:          STD     L0849
ACDE:          PULA    
ACDF:          PULB    
ACE0:          STD     L0847


   			;-----------------------------------------------
			; HIGH ET RATIOS FOR UPPER ENG RPM/TRANS RPM 
			; OF A PAIR USED  
   			;  ESTAB CORRECT GEAR RANGE FOR SPECIFIED GEAR
   			;  TO ESTAB SHIFT LIGHT TRIP POINT
			;-----------------------------------------------
ACE3:          LDX     #$5113
ACE6:          LDAA    L0006				; COOL VALUE
ACE8:          CMPA    $0C,X
ACEA:          BLS     LAD38
											;
ACEC:          LDAA    $0D,X
ACEE:          LDAB    L0845
ACF1:          CMPB    #$02
ACF3:          BLS     LACF7

ACF5:          LDAA    $0E,X
ACF7:  LACF7   CMPA    L01D9				; %TPS
ACFA:          BHI     LAD38				;
											;
ACFC:          LDAA    L0284				; MPH/1
ACFF:          CMPA    #5					; 5 MPH
AD01:          BCS     LAD38				; BR IF Vss LT 5 MPH
											;
AD03:          LDAA    L0062				; ENGINE RPM/25
AD05:          CMPA    $0F,X				;
AD07:          BHI     LAD4D				;

AD09:          CMPA    #40
AD0B:          BCS     LAD38
											;
AD0D:          LDAB    #$01
AD0F:          STAB    L0845
AD12:          PSHX    
AD13:          LDD     #$000F
AD16:          LDX     L005F
AD18:          FDIV    
AD19:          LDD     L0849
AD1C:          LSRD    
AD1D:          ADDD    L0849
AD20:          XGDX    
AD21:          IDIV    
AD22:          PSHX    
AD23:          PULA    
AD24:          PULB    
AD25:          STAB    L084B
AD28:          PULX    
AD29:  LAD29   CMPB    0,X
AD2B:          BCC     LAD52
AD2D:          INC     L0845
AD30:          INX     						;
AD31:          LDAA    L0845				;
AD34:          CMPA    #$05					;
AD36:          BCS     LAD29				;
											;
AD38:  LAD38   LDAA    L5123				;
AD3B:          LDAB    L0845				;
AD3E:          CMPB    #$02					;
AD40:          BLS     LAD45				;
											;
AD42:          LDAA    L5124				;
AD45:  LAD45   STAA    L0846				;
AD48:  LAD48   BCLR    L0053,#$04			; CLR b2, SHIFT LIGHT ON

AD4B:          BRA     LADA9


AD4D:  LAD4D   BSET    L0053,#$04			; CLR b2, SHIFT LIGHT O

AD50:          BRA     LADA9


AD52:  LAD52   LDAA    L0062				; ENGINE RPM/25
AD54:          CMPA    $04,X				;
AD56:          BLS     LAD38				;
											;
AD58:          LDAA    8,X					;
											;
AD5A:          LDAB    L01D9				; %TPS
AD5D:          MUL     
AD5E:          ASLD    						;
AD5F:          BCS     LAD66				;
											;
AD61:          ADDD    #128					;
AD64:          BCC     LAD68				;
											;
AD66:  LAD66   LDAA    #255					; FORCE MAX VALUE
AD68:  LAD68   PSHA    
 					
    		;--------------------------------------------------
			; LK UP LOAD LMT vs RPM
			; TH700R4, (NON-ELECTRONIC)
			; USED BY UPSHIFT LIGHT CODE TO GET A TPS THRESH 
			;
			;---------------------------------------------------
AD69:          LDX     #$5125				; INDEX LOAD LMT vs RPM TBL
AD6C:          LDAB    L0845				;
AD6F:          CMPB    #$02					;
AD71:          BLS     LAD76				;
											;
    		;--------------------------------------------------
			; LK UP LOAD LMT vs RPM
			; TH700R4, (NON-ELECTRONIC)
			; USED BY UPSHIFT LIGHT CODE TO GET A TPS THRESH 
			;
			;--------------------------------------------------
AD73:          LDX     #$513B				; INDEX	LOAD LMT vs RPM
											;
AD76:  LAD76   LDAB    #11					;
AD78:          BRSET   L0053,#$04,LAD7D		; BR IF b2, SHIFT LIGHT ON
											;
AD7C:          ABX     						;
AD7D:  LAD7D   LDAB    #40					;
AD7F:          LDAA    L0062				; ENGINE RPM/25
AD81:          CMPA    #200					; 5000 RPM
AD83:          BCS     LAD87				; BR IF RPM LT 5000 RPM
											;
AD85:          LDAA    #200					; FORCE 5000 RPM
AD87:  LAD87   JSR     LF4BD				; 2D LK UP W/OFFSET
											;
AD8A:          PSHA    						;

    		;--------------------------------------------------
			; BARO CORRECTION TO TBL'S L5113 th L513E (ABOVE)
			; TH700R4, (NON-ELECTRONIC)
			;
			;--------------------------------------------------
AD8B:          LDAA    L01CC				; BARO
AD8E:          LDAB    #96					; OFFSET VALUE

											
    		;--------------------------------------------------
			; BARO CORRECTION TO TBL'S L5... th L.... (ABOVE)
			; TH700R4, (NON-ELECTRONIC)
			;
			;--------------------------------------------------
AD90:          LDX     #$5151				; INDEX BARO CORRECTION TBL
AD93:          JSR     LF4BD				; 2d LK UP W/OFFSET
											;
AD96:          PULB    						;
AD97:          MUL     						;
AD98:          ASLD    						;
AD99:          BCC     LAD9D				;
											;
AD9B:          LDAA    #255					; FORCE MAX VALUE
AD9D:  LAD9D   PULB    
AD9E:          CBA     
AD9F:          BCS     LAD38
											;
ADA1:          LDAA    L0846
ADA4:          BEQ     LAD4D
											;
ADA6:          DECA    
ADA7:          BRA     LAD45


ADA9:  LADA9   RTS     
 			;-----------------------------------------



			;-----------------------------------------
ADAA:  LADAA   LDAA    L400F				; MODE WD, DIG I/O
ADAD:          BITA    #$40					; b6. TCC (Non Elect xmish)
ADAF:          BNE     LADB4				; BR IF b6
											;
ADB1:          JMP     LAE5B
 

											
	;--------------------------------------------------
	; LK UP LD vs MPH (filt)
	; TH700R4, (NON-ELECTRONIC)
	;
	;-------------------------------------------------- 
ADB4:  LADB4   LDAA    L0284				; MPH/1

ADB7:          LDAB    #205					; TOS
ADB9:          MUL     
ADBA:          ASLA    

ADBB:          LDX     #$5168			    ; INDEX LD vs MPH TBL
ADBE:          JSR     LF4C1				; 2d LK UP

ADC1:          TAB     
ADC2:          LDX     #$5160				; INDEX MPH, TCC LK/UN LK UPPER THRES
ADC5:          BRCLR   L0089,#$20,LADD0		; BR IF NOT b5
											;
ADC9:          INX     						;
ADCA:          SUBB    L515B				; ... TPS HYST FOR COAST 1 & 2
ADCD:          BCC     LADD0				;
ADCF:          CLRB    						;
ADD0:  LADD0   LDAA    L01D9				; TPS; %TPS
ADD3:          CBA     						;
ADD4:          BCC     LADDE				;
											;

	;----------------------					
	; TCC TPS Un-lk window
	;----------------------
ADD6:          LDAA    L515F				; 0 SEC COAST DELAY
ADD9:          STAA    L0853				; 

ADDC:          BRA     LAE52


ADDE:  LADDE   LDAA    L0284				; MPH/1
ADE1:          CMPA    0,X					;
ADE3:          BCS     LADE7				;

ADE5:          BRA     LAE47
 

ADE7:  LADE7   LDAA    L0006				; COOL VALUE
ADE9:          CMPA    L515A				; -40 Deg c, LOWER TCC TEMP LMT
ADEC:          BCS     LAE4C				; BR IF COOL LT 65c
											;
ADEE:          LDAA    L01D9				; %TPS
ADF1:          SUBA    L0854				;
ADF4:          BCC     LADFC				;
											;
ADF6:          NEGA    						;
ADF7:          LDAB    L515C				; 0 NEG DIFF TPS UN-LK LMT

ADFA:          BRA     LADFF
 

ADFC:  LADFC   LDAB    L515D				; 0% POS DIFF TPS UN-LK LM
ADFF:  LADFF   CBA     
AE00:          BHI     LAE4C				;

											;
											;-------------------------
											; TCC RD SPD LMTS PAIRS
											;-------------------------
    										; 0	MPH UPPER FOR LK 
    										; 0	MPH LOWER FOR UN-LK
    										; 0	MPH UPPER FOR LK
    										; 0	MPH LOWER FOR UN-LK
											;-------------------------
AE02:          LDX     #$5164 				;  TCC RD SPD LMTS PAIRS INDEX
AE05:          CLRB    

			;
			;  I/O PORT C
			;
AE06:          BRCLR   L004D,#$01,LAE0C		; BR IF NOT b0,  A/C REQUEST ON
											; 
AE0A:          INX     						; INCR INDEX FOR LOCK/UNLOCK TBL
AE0B:          INX     						;
AE0C:  LAE0C   BRCLR   L0089,#$20,LAE11		; BR IF NOT b5
											;
AE10:          INX     						;
											;
AE11:  LAE11   LDAA    L0284				; MPH/1
AE14:          CMPA    0,X					;
AE16:          BLS     LAE4C				;
											;
    ;--------------------------------------------------
	; LD LMT vs MPH, 3RD GR UPPER
	; TH700R4, (NON-ELECTRONIC)
	;
	;--------------------------------------------------
AE18:          LDY     #$5162				; 0  RPM, TCC LK/UN LK LOWER THRESH
AE1C:          LDX     #$5171				; LD LMT vs MPH, 3RD GR UPPER
AE1F:          BRSET   L0089,#$20,LAE28		; BR IF b5
											;
    ;--------------------------------------------------
    ; LD LMT vs MPH	3RD GR LOWER
    ; TH700R4, (NON-ELECTRONIC XMISH)
	;
	;--------------------------------------------------
AE23:          LDX     #$517E			    ; INDEX TBL
AE26:          INY     						;
AE28:  LAE28   ABX     						;
AE29:          LDAB    #205					; TOS
AE2B:          MUL     						;
AE2C:          ASLA    						;
AE2D:          ASLA    						;
AE2E:          LDAB    #64					; OFFSET VALUE
AE30:          JSR     LF4BD				; 2D LK UP W/OFFSET
AE33:          CMPA    L01D9				; %TPS
AE36:          BCS     LAE4C				;
											;
AE38:          LDAA    L0063				; RPM/12.5
AE3A:          CMPA    0,Y
AE3D:          BCS     LAE4C
AE3F:          LDAA    L0853
AE42:          BEQ     LAE47
AE44:          DECA    
AE45:          BRA     LAE4F


AE47:  LAE47   BSET    L0089,#$20			; SET b5
											;
AE4A:          BRA     LAE55				;
											;
											;
											;
AE4C:  LAE4C   LDAA    L515E				; .. SEC DLY LOCK DELAY AFER QUALS
AE4F:  LAE4F   STAA    L0853				;
AE52:  LAE52   BCLR    L0089,#$20			;
											;
AE55:  LAE55   LDAA    L01D9				; %TPS
AE58:          STAA    L0854				;

AE5B:  LAE5B   RTS     
			;-----------------------------------------                         


    		;----------------------------------------------
    		; CK VATS PARAMS
    		; (SEE TIC 2)
    		; CAL = HZ * 2 * 65.536
    		;----------------------------------------------
AE5C:  LAE5C   LDAA    L400D				; AFR MD BYTE 3, 1000 0010
AE5F:          BITA    #$40					; b6, (VATS)
AE61:          BEQ     LAE81				; BR IF NOT b6

											;
           		;   
		   		; AFR MD WORD 0,	
           		; 	b1 1 = VATS PASS/FAIL 
            	;
AE63:          BRSET   L003D,#$02,LAE84		; BR IF b1, VATS PASS/FAIL
											;
AE67:          LDX     L3012				; TIC 2
AE6A:          PSHX    						;
AE6B:          PULA    						;
AE6C:          PULB    						;
AE6D:          SUBD    L0851				;
AE70:          BEQ     LAE84				; BR IF Z
											;
AE72:          STX     L0851
AE75:          CPD     L518B				; VATS, ... HZ UPPER LIMIT
AE79:          BHI     LAE84
											;
AE7B:          CPD     L518D				; VATS, ... Hz LOWER LIMIT
AE7F:          BCS     LAE84
											;
AE81:  LAE81   BSET    L003D,#$02			; SET b1, VATS PASS/FAIL


AE84:  LAE84   RTS     
 			;-----------------------------------------



AE85:  LAE85   JSR     LAEA4
AE88:          JSR     LB018
AE8B:          JSR     LB089
AE8E:          JSR     LC483
AE91:          JSR     LB1F0
AE94:          JSR     LB23C
AE97:          JSR     LB2C9
AE9A:          JSR     LB2ED
AE9D:          JSR     LF781
AEA0:          JSR     LF64E

AEA3:          RTS     
 			;-----------------------------------------


AEA4:  LAEA4   BCLR    L0076,#$80
AEA7:          LDAA    L3000
AEAA:          BITA    #$0040
       LAEAB
AEAC:          BEQ     LAEB1
AEAE:          BSET    L0076,#$80
AEB1:  LAEB1   LDAB    L3002
AEB4:          COMB    
AEB5:          ANDB    #$000F
AEB7:          LDAA    L3060
AEBA:          EORA    L3062
AEBD:          ANDA    #$0003
AEBF:          ASLA    
AEC0:          ASLA    
AEC1:          ASLA    
AEC2:          ASLA    
AEC3:          ABA     
AEC4:          STAA    L009E

AEC6:          LDAA    L009C
AEC8:          STAA    L009D

AECA:          BCLR    L009C,#$04

AECD:          BRCLR   L003D,#$20,LAED4		; BR IF NOT b5, PWR ENR IS ACTIVE
											;
AED1:          BSET    L009C,#$04
AED4:  LAED4   BCLR    L009C,#$80

AED7:          BRCLR   L0050,#$10,LAEE2		; BR IF NOT b4,
											;
AEDB:          BRSET   L0086,#$80,LAEE2		; BR IF NOT b7,
											;
AEDF:          BSET    L009C,#$80

                    ;---------------------------------
				    ; 0000 0001, SPD SENSOR SOURCE
                    ;
                    ; b7    not used
                    ; b6    not used
                    ; b5 1 = force 2nd Gr if in D2 and not manual
                    ; b4 0 = Output spd fm Dig Ratio Adaptor
                    ;   
                    ; b3    not used
                    ; b2 1 = BARO & MAP SENSOR USED, 0 = MAP ONLY
                    ; b1    not used
                    ; b0 1 = allow tps hist buffer every 25 Msec 
					;
                    ;------------------------------------
AEE2:  LAEE2   LDY     #$5D02				; 0000 0001, SPD SENSOR SOURCE

AEE6:          LDAB    L004D				; I/O PORT C
AEE8:          TBA     
AEE9:          EORA    L009B
AEEB:          STAB    L009B
AEED:          BITA    #$01					; BK SW ON
AEEF:          BEQ     LAEF6

AEF1:          BRSET   1,Y,#$04,LAF00
AEF6:  LAEF6   BCLR    L009C,#$02
AEF9:          BITB    #$0001
AEFB:          BEQ     LAF00
AEFD:          BSET    L009C,#$02
AF00:  LAF00   BITA    #$0080
AF02:          BEQ     LAF11
AF04:          XGDX    
AF05:          LDAA    L5D2F
AF08:          STAA    L01AB
AF0B:          XGDX    
AF0C:          BRSET   $0001,Y,#$10,LAF1B
AF11:  LAF11   BSET    L009C,#$20
AF14:          BITB    #$0080
AF16:          BEQ     LAF1B
AF18:          BCLR    L009C,#$20
AF1B:  LAF1B   TST     L01AB
AF1E:          BEQ     LAF23
AF20:          DEC     L01AB
AF23:  LAF23   BITA    #$001C
AF25:          BEQ     LAF2C
AF27:          BRSET   $0001,Y,#$02,LAF49
											;
AF2C:  LAF2C   ANDB    #$1C
AF2E:          LSRB    
AF2F:          LSRB    

			;-------------------------------
			;
			;
			;-------------------------------
AF30:          LDX     #$B010				; ... TBL 
AF33:          ABX     
AF34:          LDAB    0,X
AF36:          LDAA    L00A1
AF38:          INCA    
AF39:          BEQ     LAF3D
											;
AF3B:          STAA    L00A1
AF3D:  LAF3D   LDAA    L00A2
AF3F:          STAA    L00A3
AF41:          CBA     
AF42:          BEQ     LAF49
											;
AF44:          CLR     L00A1
AF47:          STAB    L00A2
AF49:  LAF49   LDAB    L0076
AF4B:          TBA     
AF4C:          EORA    L0077
AF4E:          STAB    L0077
AF50:          BITA    #$80					; b7
AF52:          BEQ     LAF59
											;
AF54:          BRSET   $01,Y,#$08,LAF63		; BR IF B3, 
											;
AF59:  LAF59   BSET    L009C,#$40
AF5C:          BITB    #$80					; b7
AF5E:          BEQ     LAF63

AF60:          BCLR    L009C,#$40

AF63:  LAF63   LDD     #$0078
AF66:          LDX     L005F
AF68:          FDIV    
AF69:          XGDX    
AF6A:          CPD     #$0078
AF6E:          BHI     LAF72
											;
AF70:          CLRA    
AF71:          CLRB    
AF72:  LAF72   STD     L00B7
AF74:          SEI     


AF75:          LDX     #$3000				; INDEX CPU REG'S

AF78:          LDAB    L3027				; PACNT
AF7B:          LDY     $10,X
AF7E:          CMPB    L3027				; PACNT
AF81:          BEQ     LAF87
											;
AF83:          LDY     $10,X
AF86:          INCB    

AF87:  LAF87   LDX     #$00B9
AF8A:          STAB    $08,X
AF8C:          STY     $06,X
AF8F:          CLI     

AF90:          LDY     #$00B9
AF94:          LDAB    L5D11
AF97:          LDX     L5D12
AF9A:          JSR     LE58C

AF9D:          STD     L00BD

AF9F:          LDX     L00BD

AFA1:          LDAA    L00D9  				; CURRENT GEAR
AFA3:          CMPA    #$03					; 4th GR
AFA5:          BCS     LAFAD				; BR IF < 4th GR
											;
AFA7:          XGDX    
AFA8:          LSRD    
AFA9:          LDX     L5D15
AFAC:          FDIV    
AFAD:  LAFAD   STX     L00C4
AFAF:          LDX     #$3FE0
AFB2:          LDY     #$3FC2

                    ;---------------------------------
				    ; 0000 0001, SPD SENSOR SOURCE
                    ; b4 0 = Output spd fm Dig Ratio Adaptor
                    ;------------------------------------
AFB6:          LDAA    #$10					; b4
AFB8:          BITA    L5D02				; SPEED SENSOR SOURCE
AFBB:          BEQ     LAFC4				; BR IF NOT b4

AFBD:          LDX     #$3FC6
AFC0:          LDY     #$3FF8
AFC4:  LAFC4   SEI     
AFC5:          LDD     0,X
AFC7:          JSR     LF3ED				; Very short delay (RTS)
AFCA:          PSHY    
AFCC:          LDY     0,Y
AFCF:          JSR     LF3ED				; Very short delay (RTS)
AFD2:          CPD     0,X
AFD5:          BEQ     LAFE2
AFD7:          JSR     LF3ED				; Very short delay (RTS)
AFDA:          PULY    
AFDC:          LDY     0,Y
AFDF:          INCB    
AFE0:          BRA     LAFE4

AFE2:  LAFE2   INS     
AFE3:          INS     

AFE4:  LAFE4   LDX     #$00C8
AFE7:          STAB    $08,X
AFE9:          STY     $06,X
AFEC:          CLI     
AFED:          LDY     #$00C8
AFF1:          LDX     L5D19
AFF4:          LDAB    L5D18
AFF7:          JSR     LE58C
AFFA:          BRCLR   L009C,#$20,LB00D
											;
AFFE:          LDX     L5D1C
B001:          JSR     LF5A2
B004:          ASLD    
B005:          BCS     LB00A
											;
B007:          ASLD    
B008:          BCC     LB00D
											;
B00A:  LB00A   LDD     #$FFFF
B00D:  LB00D   STD     L00CC
B00F:          RTS     
 			;------------------------------------------


 			;------------------------------------------
 			; 8 BIT VAL'S
			;
 			;------------------------------------------
B010: 	LB010  EORA    #$08
B012:          EORA    #$04
B014:          BRA     LB056


B016:          NOP     
B017:          IDIV    
 			;------------------------------------------


B018:  LB018   LDAA    L009F			; MNP PATTERN
B01A:          STAA    L00A0

			;--------------------------------------
			; 0000 0001, SPD SENSOR SOURCE
            ; 	b5 1 = force 2nd Gr if in D2 and not manual
			;-----------------------------------------
B01C:          LDX     #$5D02
B01F:          BRCLR   0,X,#$20,LB033		; BR IF NOT b5
											;
B023:          BRSET   L0098,#$04,LB033		; SET b2, 
											;
B027:          BRCLR   L00A2,#$02,LB033		; CLR b1,
											;
B02B:          CLR     L009F				; MNP PATTERN
B02E:          BSET    L009F,#$04			; SET b2,'MANUAL' PATTERN REQUESTED 
B031:          BRA     LB083
 

			;
			; FILTER ...
			;
B033:  LB033   LDX     L01A2				; 
B036:          LDAA    L01A1				; A/D VALUE
B039:          LDAB    L5D2A				; FILT COEF
B03C:          JSR     LF459				; LAG FILTER
B03F:          STD     L01A2				; SAVE FILTERED

		;--------------------------------------------------
		;
		;
		;--------------------------------------------------
B042:          LDX     #$5D2B				; ... TBL

B045:          CLRB    
B046:          CMPA    1,X
B048:          BCS     LB054

B04A:          CMPA    2,X
B04C:          BCS     LB05C

B04E:          CMPA    3,X
B050:          BCS     LB05B

B052:          BRA     LB05A


B054:  LB054   CMPA    0,X
B056:  LB056   BCS     LB05E

B058:          BRA     LB05D
		;----------------------------------------------

B05A:  LB05A   INCB    
B05B:  LB05B   INCB 
B05C:  LB05C   INCB
B05D:  LB05D   INCB    


B05E:  LB05E   LDX     #$B084				; ... tble
B061:          ABX     
B062:          LDAA    0,X
B064:          CMPA    L01A4
B067:          BEQ     LB06E

B069:          CLR     L01A5				;

B06C:          BRA     LB080
 

B06E:  LB06E   LDAB    L01A5				;
B071:          CMPB    L5D29				; CONST 
B074:          BCC     LB07E				;

B076:          INCB    
B077:          BEQ     LB07E				; BR I = Z
											;
B079:          STAB    L01A5				;

B07C:          BRA     LB080


B07E:  LB07E   STAA    L009F				; MNP PATTERN
B080:  LB080   STAA    L01A4

B083:  LB083   RTS     
 		;------------------------------------------


 		;------------------------------------------
		;
		;
		;
 		;------------------------------------------
B084:   FCB	09  
B085:   FCB 01  
B086:   FCB 02  
B087:   FCB 04  
B088:   FCB	09
 		;------------------------------------------
		   


 		;------------------------------------------
		;
		;
		;
 		;------------------------------------------
B089:  LB089   JSR     LE8C8
B08C:          JSR     LECCC
B08F:          JSR     LE6F5



B092:          BRCLR   L0098,#$04,LB09A		; BR IF NOT b2
											;
B096:          LDAA    #$88
B098:          STAA    L00A2  

		;------------------------------
		; $5B32, 1000 1111,  ERR WD 8
		;
		; b5 1 = ERR 77, MNP SWITCH
		;------------------------------
B09A:  LB09A   LDX     #$5B00				; INDEX ERR MASKS
											;
B09D:          LDAA    L009F				; MNP PATTERN
											;
B09F:          BRCLR   $32,X,#$20,LB0AD		; ($5B32), BR IF NOT b5
											;
B0A3:          BRCLR   L001D,#$20,LB0AD		; BR IF NOT b5
											;
											;
B0A7:          ANDA    #$F0					; 1111 0000
B0A9:          ORAA    #$09					; 0000 1001
											;
B0AB:          BRA     LB0BC


B0AD:  LB0AD   BITA    #$04					; b2
B0AF:  LB0AF   BEQ     LB0BE				; BR IF NOT b2
											;
B0B1:          BRSET   L0098,#$04,LB0BA		; BR IF b2
											;
B0B5:          LDAB    L5D0F				;
B0B8:          BEQ     LB0BC				;
											;
B0BA:  LB0BA   EORA    #$05					; TOGGLE b0 & b2
B0BC:  LB0BC   STAA    L009F				; MNP PATTERN
											;
B0BE:  LB0BE   JSR     LE7C7				; HIGH TPS ERR 21 HANDLER
B0C1:          JSR     LE808	   			; LOW TPS, ERR 22 HANDLER
B0C4:          JSR     LE5CF				;
B0C7:          JSR     LEBC0				;

			;----------------------------------------------
			; AFR MD BYTE 5,	 0001 0000, (DIG I/O)
			;
			; b7 1 = MAN, (0 = TCC)
			;----------------------------------------------
B0CA:          LDX     #$400F			; INDEX AFR MD BYTE 5 
B0CD:          BRSET   0,X,#$80,LB0D4	; BR IF b7,
										; 
B0D1:          JSR     LE847

B0D4:  LB0D4   JSR     LEF2B
B0D7:          JSR     LEB81
B0DA:          JSR     LE60B
B0DD:          JSR     LE6E4
B0E0:          JSR     LE5F1

B0E3:          RTS     
 			;----------------------------------------------


											
			;----------------------------------------------		
			; HI %TPS ERR
			;
			; 
			;----------------------------------------------
B0E4:  LB0E4   LDX     #$5B00				; INDEX ERR MASKS
 											;
B0E7:          BRSET   L0098,#$01,LB114		; BR IF b0, 
											;
			;------------------------------		
			; $5B2B, 1111 0001, MASK XMISSH ERR WD 1
			;
			; b0 1 = ERR 21,	HIGH TPS
			;------------------------------		
											;
B0EB:          BRCLR   $2B,X,#$01,LB0F8		; ($5B2B), BR IF b0, HIGH TPS  
											;


			;------------------------------
			; (5B34) 0000 0000, XMISH ERR WD 1 ALT
			;
			; b0 1 = ERR 21,	HIGH TPS
			;------------------------------						
B0EF:          BRSET   $34,X,#$01,LB0F8		; ($5B34), BR IF b0, HIGH TPS
											;
B0F3:          LDAA    L0162				; ERR 21 TIMER
B0F6:          BNE     LB105				; BR IF NZ
											;
B0F8:  LB0F8   BRCLR   $2C,X,#$80,LB116		;
											;
B0FC:          BRSET   $35,X,#$80,LB116		;
											;
B100:          LDAA    L0163				; CLR ERR 22 TIMER
B103:          BEQ     LB116  				; BR IF TIME = 0
											;

			;--------------------------------------
			; 0000 0001, SPD SENSOR SOURCE
        	; b0 1 = allow tps hist buffer every 25 Msec 
			;-----------------------------------------
B105:  LB105   LDX     #$5D02
B108:          BRCLR   0,X,#$01,LB111		; BR IF NOT b0, 
											;
B10C:          LDAA    L01AA				;
B10F:          BRA     LB178				;
 											
B111:  LB111   JMP     LB182
 
B114:  LB114   BRA     LB172
 

B116:  LB116   LDAA    L00A6			   	; TPS A/D
B118:          CMPA    L02F6				; OLD FILT TPS (XMISH)
B11B:          BHI     LB12C				; BR IF NEW TPS GT OLD TPS
											;
B11D:          LDAB    #$80
		;
		; P/O TPS AUTO ZERO
		;
B11F:          LDX     L02F6				; FILT TPS (XMISH)
B122:          LDY     #$5B25				; 0.024, TPS OFF SET TIME CONSTANT
B126:          JSR     LF436				; LAG FILTER SUB ROUTINE, XMSIH
B129:          STD     L02F6				; SAVE FILT tps A/D VALUE
											

B12C:  LB12C   LDAA    L00F7				;
B12E:          SUBA    L00D7				;
B130:          BCC     LB137				;
											;
B132:          BCLR    L009A,#$04			;

B135:          BRA     LB160


;
B137:  LB137   BRSET   L009A,#$04,LB160		;
											;
B13B:          BRSET   L0018,#$02,LB160		;
											;
B13F:          BRSET   L0018,#$01,LB160		;
											;
B143:          BRCLR   L009C,#$01,LB160		;
											;
B147:          CMPA    L5B2A				; 5 MPH VSS TO QULIFY DECEL for TPS	INCREASE
B14A:          BLS     LB164				;
											;
B14C:          LDAA    L02F6				; FILT TPS (XMISH)
B14F:          ADDA    L5B29				; TPS OFFSET INCR for EACH DECEL
B152:          CMPA    L5B24				; TPS MIN BIN VAL, (IDLE)
B155:          BLS     LB15A				;
											;
B157:          LDAA    L5B24				; TPS MIN BIN VAL, (IDLE)
B15A:  LB15A   STAA    L02F6				; FILT TPS (XMISH)

B15D:          BSET    L009A,#$04

B160:  LB160   LDAA    L00D7
B162:          STAA    L00F7

B164:  LB164   LDD     L01A8
B167:          STD     L01A9

B16A:          LDD     L01A6				; TPS FOR ENGINE
B16D:          STD     L01A7

B170:          BRA     LB178
 		;----------------------------------------------


 		;----------------------------------------------
		; APPLY DEFAULT TPS
		;
 		;----------------------------------------------
B172:  LB172   LDAA    L5B22				; 35% DEFAULT TPS, (ERR E22/23)
B175:          CLRB    

B176:          BRA     LB180
 		;----------------------------------------------


 		;----------------------------------------------
		;
		;
 		;----------------------------------------------
B178:  LB178   LDX     L00B0				; GET OLD TPS
B17A:          LDAB    L5B28				; 4.5 msec TPS FILTER TIME CONST
B17D:          JSR     LF459				; LAG FILT
B180:  LB180   STD     L00B0				; SAVE FILTERED TPS

B182:  LB182   LDAA    L00B0
B184:          SUBA    #128
B186:          ADDA    L0101
B189:          BVC     LB18F
											;
B18B:          LDAA    #$007F
B18D:          ADCA    #$0000
B18F:  LB18F   ADDA    #128
B191:          STAA    L00B2


		;
		; CK XMISH KICK DOWN TPS THRESH
		;
B193:          LDAB    L5D22				; 85.9% TPS kick down thresh
											;
B196:          BRSET   L009C,#$10,LB19D	   	; BR IF b4, IN XMISH KICK DN
											;
B19A:          LDAB    L5D21				; 87.0% TPS kick down thres
											;
B19D:  LB19D   BCLR    L009C,#$10			; CLR b4, XMISH KSIK DN

B1A0:          CMPB    L00B0				;
B1A2:          BCC     LB1AB				;
											;
B1A4:          BRSET   L009F,#$04,LB1AB		; BR IF b2, 'MANUAL' PATTERN REQUESTED 
											;
B1A8:          BSET    L009C,#$10			; 

B1AB:  LB1AB   RTS     
 		;--------------------------------------------------


 		;--------------------------------------------------
		;
		;
 		;--------------------------------------------------
B1AC:  LB1AC   LDAA    L00A6			   	; TPS A/D
B1AE:          CMPA    L02F6				; FILT TPS (XMISH)	
B1B1:          BLS     LB1CE				;
											;
B1B3:          LDAB    #$80					;
											;
		;
		; FILTER TPS
		;
B1B5:          LDX     L02F6				; FILT TPS (XMISH)
B1B8:          LDY     #$5B27			   	; TPS OFFSET FILTER TIME CONST
B1BC:          JSR     LF436				; LAG FILTER SUB ROUTINE, XMSIH
B1BF:          STD     L02F6				; FILT TPS (XMISH)

B1C2:          CMPA    L5B24				; TPS MIN BIN VAL, (IDLE)
B1C5:          BCS     LB1CE				;
											;
B1C7:          LDAA    L5B24				; TPS MIN BIN VAL, (IDLE)
B1CA:          CLRB    						;
B1CB:          STD     L02F6				; FILT TPS (XMISH)

B1CE:  LB1CE   RTS     
 		;------------------------------------------


B1CF:  LB1CF   LDD     L02F6				; FILT TPS (XMISH)
B1D2:          ADDD    #128
B1D5:          TAB     
B1D6:          LDAA    L00A6			   	; TPS A/D
B1D8:          SBA     
B1D9:          BCC     LB1DC
											;
B1DB:          CLRA    						;
B1DC:  LB1DC   LDAB    L5B26				; 0.55%/CNT TPS GAIN
B1DF:          MUL     
B1E0:          ADDD    #$0020
B1E3:          ASLD    
B1E4:          BCS     LB1E9
											;
B1E6:          ASLD    
B1E7:          BCC     LB1EC
											;
B1E9:  LB1E9   LDD     #$FFFF
B1EC:  LB1EC   STAA    L01A6				; TPS FOR ENGINE

B1EF:          RTS     
 		;------------------------------------------




B1F0:  LB1F0   LDD     L00B7
B1F2:          LDX     L01AC
B1F5:          LDY     #$5D10
B1F9:          JSR     LF436				; LAG FILTER SUB ROUTINE, XMSIH
B1FC:          STD     L01AC

B1FF:          LDD     L00BD
B201:          LDX     L00C2
B203:          LDY     #$5D14
B207:          JSR     LF436				; LAG FILTER SUB ROUTINE, XMSIH
B20A:          STD     L00C2

B20C:          LDD     L00C4
B20E:          LDX     L00C6
B210:          LDY     #$5D17
B214:          JSR     LF436				; LAG FILTER SUB ROUTINE, XMSIH
B217:          STD     L00C6
B219:          LDD     L00B7
B21B:          SUBD    L00C4
B21D:          RORA    
B21E:          ROLA    
B21F:          BVC     LB228

B221:          LDD     #$7FFF
B224:          ADCB    #$0000
B226:          ADCA    #$0000
B228:  LB228   LDX     L00EB
B22A:          LDY     #$5D0D
B22E:          JSR     LF420
B231:          STD     L00EB
B233:          BPL     LB239
B235:          NEGA    
B236:          NEGB    
B237:          SBCA    #$0000
B239:  LB239   STD     L00ED
B23B:          RTS     
 ; ------------------------------------------
B23C:  LB23C   BRCLR   L0098,#$02,LB25E
B240:          JSR     LB2B2
B243:          LDD     L00BD
B245:          LSRD    
B246:          LSRD    
B247:          FDIV    
B248:          XGDX    
B249:          BRCLR   L009C,#$20,LB277
B24D:          LDX     L5D1C
B250:          JSR     LF5A2
B253:          ASLD    
B254:          BCS     LB259
B256:          ASLD    
B257:          BCC     LB277
B259:  LB259   LDD     #$FFFF
B25C:          BRA     LB277
 

B25E:  LB25E   LDAA    L0164				; ERR 24 TIMER
B261:          ORAA    L0175				;
B264:          BNE     LB275				;
											;
B266:          LDD     L00CC
B268:          LDX     L00D3
B26A:          BRSET   L0086,#$08,LB271

B26E:          LDX     #$0000
B271:  LB271   STX     L00D5
B273:          BRA     LB277
 ;
B275:  LB275   LDD     L00D5
B277:  LB277   STD     L00D1
B279:          LDX     L00D3
B27B:          LDY     #$5D1B
B27F:          JSR     LF436				; LAG FILTER SUB ROUTINE, XMSIH
B282:          STD     L00D3

B284:          LDD     L00D3
B286:          LDX     L5D1E
B289:          FDIV    
B28A:          XGDX    
B28B:          SUBA    #$0080
B28D:          ADDA    L0102
B290:          BVC     LB299
B292:          LDD     #$7FFF
B295:          ADCB    #$0000
B297:          ADCA    #$0000
B299:  LB299   ADDA    #$0080
B29B:          ADDD    #$0080
B29E:          BCC     LB2A3
B2A0:          LDD     #$FFFF
B2A3:  LB2A3   STD     L0814

		;
		; FILTER Vss 
		;
B2A6:          LDX     L00D7
B2A8:          LDY     #$5D20			    ; 0.984, Vss FILTER TIME CONST
B2AC:          JSR     LF436				; LAG FILTER SUB ROUTINE, XMSIH

B2AF:          STD     L00D7

B2B1:  LB2B1   RTS     
 	;------------------------------------------


B2B2:  LB2B2   LDX     L5B43

B2B5:          BRSET   L00A2,#$20,LB2C8
											;
B2B9:          LDX     #$5B49
B2BC:          LDAB    L00D9  				; CURRENT GEAR
B2BE:          BRCLR   L0098,#$04,LB2C4
B2C2:          LDAB    #$0001
B2C4:  LB2C4   ASLB    
B2C5:          ABX     
B2C6:          LDX     0,X
B2C8:  LB2C8   RTS     
 ; ------------------------------------------
B2C9:  LB2C9   BCLR    L009A,#$02
B2CC:          LDAA    L00D9  				; CURRENT GEAR
B2CE:          CMPA    #$03					; 4th GR
B2D0:          BCS     LB2E0

B2D2:          BRCLR   L0089,#$20,LB2DD
B2D6:          LDD     L01AC
B2D9:          LDX     L00C2
B2DB:          BRA     LB2E4
 ;
B2DD:  LB2DD   BSET    L009A,#$02
B2E0:  LB2E0   LDD     L00C2
B2E2:  LB2E2   LDX     L00D3
B2E4:  LB2E4   LSRD    
B2E5:          LSRD    
B2E6:          BNE     LB2E9
B2E8:          XGDX    
B2E9:  LB2E9   FDIV    
B2EA:          STX     L00F9
B2EC:          RTS     
 ; ------------------------------------------
B2ED:  LB2ED   LDAA    L00B5
B2EF:          LDAB    #$0008
B2F1:          MUL     
B2F2:          SUBD    #$0001
B2F5:          BLT     LB2FC
B2F7:          CMPA    L0152
B2FA:          BGE     LB304
B2FC:  LB2FC   ADDD    #$0011
B2FF:          CMPA    L0152
B302:          BGE     LB307
B304:  LB304   STAA    L0152
B307:  LB307   LDAB    L0152
B30A:          LDX     #$B31D
B30D:          ABX     
B30E:          LDAA    0,X
B310:          STAA    L0153
B313:          LDAA    $0008,X
B315:          STAA    L0154
B318:          RTS     
 ; ------------------------------------------
B319:          NOP     
B31A:          TEST    
B31B:          IDIV    
B31C:          FDIV    
B31D:          RORA    
B31E:          NEGA    
B31F:          PSHX    
B320:          ABX     
B321:          PSHA    
B322:          DES     
B323:          DES     
B324:          DES     
B325:          BVS     LB34A
											;
B327:          BRCLR   $001C,X,#$18,LB340
											;
B32B:          BRCLR   L0011,#$BD,LB2E2
											;
B32F:          DES     
B330:          JSR     LB367

B333:          RTS     
	 	; ------------------------------------------

		;-------------------------------------------
		;
		;
		;-------------------------------------------
B334:          LDD     L01AC
B337:          CPD     L5D23
B33B:          BCC     LB360
											;
B33D:          LDD     L00D3
B33F:          CPD     L5D25
B343:          BCC     LB360
											;
B345:          LDD     L00C6
B347:          CPD     L5D27
B34B:          BCC     LB360
											;
B34D:          BRCLR   L0086,#$80,LB366
											;
B351:          INC     L00FF
B354:          LDAA    L5D0E
B357:          CMPA    L00FF
B359:          BCC     LB366
											;
B35B:          BCLR    L0086,#$80

B35E:          BRA     LB366


B360:  LB360   CLR     L00FF
B363:          BSET    L0086,#$80

B366:  LB366   RTS     
 		;----------------------------------------------

		;----------------------------------------------
B367:  LB367   LDAB    L00DB
B369:          INCB    
B36A:          BEQ     LB36E
B36C:          STAB    L00DB
B36E:  LB36E   BRSET   L0083,#$11,LB378
B372:          BRSET   L0083,#$0A,LB378
B376:          BRA     LB37E
 ;
B378:  LB378   BCLR    L0083,#$12
B37B:          BCLR    L0085,#$02
B37E:  LB37E   BRSET   L0085,#$02,LB3D5
B382:          BRCLR   L0083,#$09,LB3E0
B386:          BSET    L0085,#$02
B389:          BCLR    L0085,#$10
B38C:          BCLR    L0085,#$80
B38F:          BCLR    L0083,#$12
B392:          BRCLR   L0083,#$01,LB399
B396:          BSET    L0083,#$02
B399:  LB399   BRCLR   L0083,#$08,LB3A0
B39D:          BSET    L0083,#$10
B3A0:  LB3A0   BCLR    L008E,#$08
B3A3:          LDAA    L00A1
B3A5:          BNE     LB3AA
B3A7:          BSET    L008E,#$08
B3AA:  LB3AA   LDAA    L00DB
B3AC:          STAA    L0188
B3AF:          CLRA    
B3B0:          CLRB    
B3B1:          STAA    L00DA
B3B3:          STAA    L00DB
B3B5:          STD     L019A
B3B8:          LDAA    #$007F
B3BA:          STAA    L00DF
B3BC:          STAA    L00E0
B3BE:          CLRA    

B3BF:          LDAB    L00A0
B3C1:          EORB    L009F				; MNP PATTERN
B3C3:          ANDB    #$07					; 0000 0111
B3C5:          BEQ     LB3C9				; 
											;
B3C7:          LDAA    #$01
B3C9:  LB3C9   STAA    L0090

B3CB:          CLRA    
B3CC:          STAA    L0091
B3CE:          STAA    L0092
B3D0:          LDAA    L00B2
B3D2:          STAA    L0195

B3D5:  LB3D5   BRSET   L0083,#$01,LB3E0
B3D9:          BRSET   L0083,#$08,LB3E0
B3DD:          BCLR    L0085,#$02

B3E0:  LB3E0   LDAB    L00D9  				; CURRENT GEAR

B3E2:          BRSET   L0083,#$10,LB3E7
B3E6:          DECB    
B3E7:  LB3E7   BRCLR   L0085,#$80,LB3EE
B3EB:          JMP     LB4B1
 ;
B3EE:  LB3EE   LDAA    L00DB
B3F0:          SUBA    L00DA
B3F2:          STAA    L00DC
B3F4:          LDX     #$68A9
B3F7:          ABX     
B3F8:          ABX     
B3F9:          LDD     L00F9
B3FB:          TST     L00D9  				; CURRENT GEAR
B3FE:          BEQ     LB404
B400:          BRCLR   L0083,#$10,LB407
B404:  LB404   JMP     LB49C
 ;
B407:  LB407   BRCLR   L009A,#$02,LB417
B40B:          BSET    L0091,#$10
B40E:          BSET    L009A,#$10
B411:          JSR     LB4B2
B414:          JMP     LB454
 ;
B417:  LB417   CPD     0,X
B41A:          BCS     LB433
B41C:          CLRA    
B41D:          CLRB    
B41E:          STD     L019A
B421:          BCLR    L0085,#$10
B424:          LDAA    L00DB
B426:          STAA    L00DA

B428:          LDX     #$0189
B42B:          LDAB    L00D9  				; CURRENT GEAR
B42D:          DECB    
B42E:          ABX     
B42F:          STAA    0,X
B431:          BRA     LB44C
 ;
B433:  LB433   SUBD    6,X
B435:          BCS     LB454
B437:          LDD     L00F9
B439:          LSRD    
B43A:          LSRD    
B43B:          LSRD    
B43C:          LSRD    
B43D:          LSRD    
B43E:          ADDD    L019A
B441:          BCC     LB446
B443:          LDD     #$FFFF
B446:  LB446   STD     L019A
B449:          BSET    L0085,#$10
B44C:  LB44C   JSR     LB4B2
B44F:          LDAA    L00DB
B451:          INCA    
B452:          BNE     LB4B1
B454:  LB454   LDAB    L00DC
B456:          CLRA    
B457:          XGDX    
B458:          LDD     L019A
B45B:          CPD     #$FFFF
B45F:          BEQ     LB478
B461:          IDIV    
B462:          XGDX    
B463:          ASLD    
B464:          BCS     LB472
B466:          ASLD    
B467:          BCS     LB472
B469:          ASLD    
B46A:          BCS     LB472
B46C:          ASLD    
B46D:          BCS     LB472
B46F:          ASLD    
B470:          BCC     LB475
B472:  LB472   LDD     #$FFFF
B475:  LB475   STD     L019A

B478:  LB478   LDX     #$019C
B47B:          LDAB    L00D9  				; CURRENT GEAR
B47D:          DECB    
B47E:          ABX     
B47F:          STAA    0,X
B481:          LDX     #$68CB
B484:          LDAB    L00D9  				; CURRENT GEAR
B486:          DECB    
B487:          ABX     
B488:          LDAB    L00DC
B48A:          CMPB    0,X
B48C:          BCC     LB494
B48E:          LDAA    L0091
B490:          ORAA    #$0040
B492:          STAA    L0091
B494:  LB494   JSR     LBA65
B497:          JSR     LF131
B49A:          BRA     LB4A8
 ;
B49C:  LB49C   LDAA    L00DB
B49E:          LDX     #$68B5
B4A1:          LDAB    L00D9  				; CURRENT GEAR
B4A3:          ABX     
B4A4:          CMPA    0,X
B4A6:          BCS     LB4B1
B4A8:  LB4A8   BSET    L0085,#$80
B4AB:          BCLR    L0085,#$02
B4AE:          BCLR    L0083,#$12

B4B1:  LB4B1   RTS     
 
 			;-----------------------------------------
B4B2:  LB4B2   LDAA    L0090
B4B4:          LDX     #$68B8
B4B7:          LDAB    L00D9  				; CURRENT GEAR
B4B9:          DECB    
B4BA:          ABX     
B4BB:          BRCLR   L008E,#$04,LB4C1
B4BF:          ORAA    #$08
B4C1:  LB4C1   LDY     #$68A8
B4C5:          BRCLR   0,Y,#$01,LB4D3
B4CA:          LDAB    L00DA
B4CC:          CMPB    $EF,X
B4CE:          BLS     LB4D3
B4D0:          BSET    L0091,#$80
B4D3:  LB4D3   LDAB    L00DC
B4D5:          CMPB    $16,X
B4D7:          BLS     LB4DB
B4D9:          ORAA    #$0020
B4DB:  LB4DB   LDAB    L00B2
B4DD:          CMPB    $03,X
B4DF:          BLS     LB4E5
B4E1:          CMPB    $06,X
B4E3:          BLS     LB4E7
B4E5:  LB4E5   ORAA    #$04

B4E7:  LB4E7   LDX     #$68B8
B4EA:          SUBB    L0195
B4ED:          BCC     LB4F0
B4EF:          NEGB    
B4F0:  LB4F0   CMPB    $09,X
B4F2:          BCS     LB4F6

B4F4:          ORAA    #$80


B4F6:  LB4F6   BRSET   L009F,#$04,LB507		; BR IF b2,'MANUAL' PATTERN REQUESTED 
											;
B4FA:          LDY     #$68A8
B4FE:          BRCLR   0,Y,#$04,LB509		; BR IF NOT b2
											;
B503:          BRCLR   L009F,#$02,LB509		; BR IF NOT b1, 'PERFORMANCE' PATTERN REQUESTED
											; 
B507:  LB507   ORAA    #$01

B509:  LB509   LDAB    L00B5
B50B:          CMPB    $01,X
B50D:          BLS     LB513

B50F:          CMPB    $02,X
B511:          BCS     LB515

B513:  LB513   ORAA    #$0002
B515:  LB515   BRCLR   L00A2,#$03,LB51B

B519:          ORAA    #$0010
B51B:  LB51B   LDAB    0,X
B51D:          CMPB    L00DB
B51F:          BNE     LB527
B521:          CMPB    L00DA
B523:          BLS     LB527
B525:          ORAA    #$0040
B527:  LB527   STAA    L0090
B529:          PSHX    
B52A:          JSR     LE654
B52D:          PULX    
B52E:          LDAA    L0091
B530:          BRCLR   L0098,#$10,LB536
B534:          ORAA    #$0008

B536:  LB536   LDAB    L00D9  				; CURRENT GEAR
B538:          DECB    
B539:          ABX     
B53A:          LDAB    L0188
B53D:          CMPB    $000A,X
B53F:          BCC     LB543
B541:          ORAA    #$0001
B543:  LB543   LDAB    L00A1
B545:          CMPB    $000D,X
B547:          BCC     LB54B
B549:          ORAA    #$0002
B54B:  LB54B   LDAB    L00D7
B54D:          SUBB    L0187
B550:          BPL     LB553
B552:          NEGB    
B553:  LB553   CMPB    $0010,X
B555:          BLS     LB559
B557:          ORAA    #$0004
B559:  LB559   STAA    L0091
B55B:          CLRA    
B55C:          BRCLR   L009C,#$20,LB562
B560:          ORAA    #$0001
B562:  LB562   BRCLR   L0087,#$02,LB568
B566:          ORAA    #$0002
B568:  LB568   STAA    L0092
B56A:          RTS     
 ; ------------------------------------------

			;----------------------------------------------
			; AFR MD BYTE 5,	 0001 0000, (DIG I/O)
			;
			; b7 1 = MAN, (0 = TCC)
			; b6 1 = TCC (Non Elect xmish)
			; b5 1 = Not Used 
			; b4 1 = CONV OVER HEAT PROTECTION
			;
			; b3 1 = BURST KNOCK RETARD
			; b2 1 = A/C CLUTCH CNT'L, 0 = CPI TUNE
			; b1 1 = Not Used
			; b0 1 = 1 DO RPM/MPH LMT, (GOV'R OPT)
			;
			;----------------------------------------------
B56B:  LB56B   LDX     #$400F
B56E:          BRCLR   0,X,#$C0,LB574
B572:          BRA     LB586
 ;
B574:  LB574   JSR     LB587
B577:          JSR     LBE5C
B57A:          JSR     LBA38
B57D:          JSR     LBF62
B580:          JSR     LBEBC
B583:          JSR     LC00B
B586:  LB586   RTS     
 ; ------------------------------------------
B587:  LB587   LDAA    L0111
B58A:          BEQ     LB58F
B58C:          JMP     LB88A


B58F:  LB58F   LDAB    L009F				; MNP PATTERN
B591:          ANDB    #$06					; b1 & b2,

B593:          LDX     #$B961
B596:          CLRA    
B597:          BRSET   L00A2,#$20,LB59D		; BR IF b5, 
											;
B59B:          LDAA    L00D7
B59D:  LB59D   ASLA    
B59E:          BCC     LB5A3
											;
B5A0:          LDX     #$B967
B5A3:  LB5A3   ABX     
B5A4:          LDX     0,X
B5A6:          TAB     
B5A7:          LDAA    L00B2
B5A9:          JSR     LF4DE				; 3d LK UP

B5AC:          LDAB    L00D9  				; CURRENT GEAR
B5AE:          DECB    
B5AF:          BRCLR   L0083,#$10,LB5B4		; BR IF NOT b4
											;
B5B3:          INCB    
B5B4:  LB5B4   BMI     LB5E3
											;
B5B6:          PSHA    
B5B7:          LDX     #$0115
B5BA:          ABX     
B5BB:          LDAA    0,X
B5BD:          BNE     LB5DB
											;


 		  	;  MNP PATTERN
			;
            ; b3 1 = ILLEGAL PATTERN REQUESTED 
            ; b2 1 = 'MANUAL' PATTERN REQUESTED
            ; b1 1 = 'PERFORMANCE' PATTERN REQUESTED
            ; b0 1 = 'NORMAL' PATTERN REQUESTED
            ;-----------------------------
B5BF:          BRCLR   L009F,#$06,LB5CB		; BR IF NOT b2 & b2
											;
B5C3:          ADDB    #$0003
B5C5:          BRSET   L009F,#$02,LB5CB	 	; NR IF b1, 'PERFORMANCE' PATTERN REQUESTED
											;
B5C9:          ADDB    #$03
B5CB:  LB5CB   LDX     #$B96D
B5CE:          ASLB    
B5CF:          ABX     
B5D0:          LDX     0,X
B5D2:          BEQ     LB5DB
B5D4:          LDAA    L00B2
B5D6:          JSR     LF4C1				; 2d LK UP
B5D9:          SUBA    #$80
B5DB:  LB5DB   PULB    
B5DC:          ABA     
B5DD:          BVC     LB5E3
B5DF:          LDAA    #$7F
B5E1:          ADCA    #$00
B5E3:  LB5E3   PSHA    
B5E4:          JSR     LB91D
B5E7:          PULB    
B5E8:          ASRA    
B5E9:          ASRA    
B5EA:          ASRA    
B5EB:          ABA     
B5EC:          BVC     LB5F2
B5EE:          LDAA    #$007F
B5F0:          ADCA    #$0000

B5F2:  LB5F2   LDX     #$B991
B5F5:          LDAB    L00D9  				; CURRENT GEAR
B5F7:          ASLB    
B5F8:          ABX     
B5F9:          LDX     0,X
B5FB:          BNE     LB600
B5FD:          JMP     LB680
 ;
B600:  LB600   PSHA    
B601:          PSHX    
B602:          LDAA    L00B5
B604:          LDAB    #$00A0
B606:          MUL     
B607:          PSHA    
B608:          PSHX    
B609:          PSHX    
B60A:          PSHX    
B60B:          LDAA    #$0000
B60D:          LDAB    L00B2
B60F:          CMPB    L5F28
B612:          BLS     LB66E
B614:          LDAA    #$0030
B616:          CMPB    L5F2B
B619:          BCC     LB66E
B61B:          LDAA    #$0010
B61D:          LDX     #$5F29
B620:  LB620   CMPB    0,X
B622:          BCS     LB629
B624:          INX     
B625:          ADDA    #$0010
B627:          BRA     LB620
 ;
B629:  LB629   TSY     
B62B:          STAB    $0005,Y
B62E:          STAA    $0004,Y
B631:          LDAA    0,X
B633:          DEX     
B634:          LDAB    0,X
B636:          SBA     
B637:          STAA    $0003,Y
B63A:          LDAB    $0004,Y
B63D:          MUL     
B63E:          STD     $0001,Y
B641:          LDAB    $0005,Y
B644:          LDAA    #$0010
B646:          MUL     
B647:          STD     $0004,Y
B64A:          LDAA    $0001,X
B64C:          LDAB    #$0010
B64E:          MUL     
B64F:          COMA    
B650:          COMB    
B651:          ADDD    #$0001
B654:          ADDD    $0001,Y
B657:          ADDD    $0004,Y
B65A:          STAA    $0004,Y
B65D:          CLRA    
B65E:          STAA    $0002,Y
B661:          LDX     $0002,Y
B664:          LDAA    $0004,Y
B667:          IDIV    
B668:          STX     0,Y
B66B:          LDAA    $0001,Y
B66E:  LB66E   PULX    
B66F:          PULX    
B670:          PULX    
B671:          PULB    
B672:          PULX    
B673:          JSR     LF4DE				; 3d LK UP
B676:          SUBA    #$0080
B678:          PULB    
B679:          ABA     
B67A:          BVC     LB680
B67C:          LDAA    #$007F
B67E:          ADCA    #$0000
B680:  LB680   PSHA    
B681:          JSR     LBCC6
B684:          PULB    
B685:          ABA     
B686:          BVC     LB68C
B688:          LDAA    #$007F
B68A:          ADCA    #$0000
B68C:  LB68C   JSR     LBC77
B68F:          BRCLR   L0083,#$10,LB6B9

B693:          LDAB    L00D9  				; CURRENT GEAR


 		  	;  MNP PATTERN
			;
            ; b3 1 = ILLEGAL PATTERN REQUESTED 
            ; b2 1 = 'MANUAL' PATTERN REQUESTED
            ; b1 1 = 'PERFORMANCE' PATTERN REQUESTED
            ; b0 1 = 'NORMAL' PATTERN REQUESTED
            ;-----------------------------
B695:          BRCLR   L009F,#$06,LB6A1		; BR IF NOT b2 & b3

B699:          ADDB    #$03					; 
B69B:          BRSET   L009F,#$02,LB6A1		; BR IF b1, 'PERFORMANCE' PATTERN REQUESTED
											;
B69F:          ADDB    #$03

B6A1:  LB6A1   LDX     #$B97F
B6A4:          ASLB    
B6A5:          ABX     
B6A6:          LDX     0,X
B6A8:          BEQ     LB6B9
B6AA:          TAB     
B6AB:          LDAA    L00D7
B6AD:          JSR     LF4A4
B6B0:          SUBA    #$0080
B6B2:          ABA     
B6B3:          BVC     LB6B9
B6B5:          LDAA    #$7F
       LB6B6
B6B7:          ADCA    #$00
B6B9:  LB6B9   JSR     LB88D
B6BC:          PSHA    

B6BD:          LDAB    L00D9  				; CURRENT GEAR
B6BF:          BRCLR   L0083,#$10,LB6C4
B6C3:          INCB    
B6C4:  LB6C4   CLRA    
B6C5:          DECB    
B6C6:          BMI     LB6D6
B6C8:          ASLB    
B6C9:          LDX     #$B999
B6CC:          ABX     
B6CD:          LDX     0,X
B6CF:          BEQ     LB6D6
B6D1:          LDAA    L00B2
B6D3:          JSR     LF4C1				; 2d LK UP
B6D6:  LB6D6   PSHA    
B6D7:          TSX     
B6D8:          JSR     LD969
B6DB:          INS     
B6DC:          ADDD    #$0080
B6DF:          PULB    
B6E0:          MUL     
B6E1:          ASLD    
B6E2:          BVS     LB6E6
B6E4:          BPL     LB6E8
B6E6:  LB6E6   LDAA    #$007F
B6E8:  LB6E8   STAA    L0142
B6EB:          BCLR    L008E,#$04
B6EE:          BRCLR   L0083,#$09,LB701
B6F2:          CLR     L00E8
B6F5:          LDX     L00EF
B6F7:          CPX     L5F26
B6FA:          BLT     LB70A
B6FC:          LDAB    L5F25
B6FF:          STAB    L00E8
B701:  LB701   LDAB    L00E8
B703:          BEQ     LB70A
B705:          DECB    
B706:          STAB    L00E8
B708:          BRA     LB747
 ;
B70A:  LB70A   BRCLR   L0098,#$04,LB713
B70E:          LDX     #$5F96
B711:          BRA     LB735
 ;
B713:  LB713   LDAB    L00D9  				; CURRENT GEAR
B715:          CMPB    #$03					; 4th GR
B717:          BEQ     LB747				; 
											;
B719:          BRCLR   L00A2,#$07,LB747
B71D:          LDX     #$5FA7
B720:          CMPB    #$0002
B722:          BEQ     LB735
B724:          BRCLR   L00A2,#$03,LB747
B728:          LDX     #$5F96
B72B:          TSTB    
B72C:          BNE     LB735
B72E:          BRCLR   L00A2,#$01,LB747
B732:          LDX     #$5F85
B735:  LB735   TAB     
B736:          LDAA    L00D7
B738:          JSR     LF4C1				; 2d LK UP
B73B:          STAA    L0143
B73E:          CBA     
B73F:          BCS     LB746
B741:          BSET    L008E,#$04
B744:          BRA     LB747
 ;
B746:  LB746   TBA     
B747:  LB747   LDX     L00EB
B749:          STX     L00EF
B74B:          STAA    L0145
B74E:          LDAB    L00D7
B750:          BRCLR   L00A2,#$50,LB76A
B754:          BCLR    L008E,#$30
B757:          CMPB    L5F11
B75A:          BCS     LB75F
B75C:  LB75C   JMP     LB835
 ;
B75F:  LB75F   BCLR    L008E,#$02
B762:          LDX     #$5FB8
B765:          LDAB    L5F13
B768:          BRA     LB7B6
 ;
B76A:  LB76A   CMPB    L5F12
B76D:          BCC     LB779
B76F:          BRCLR   L00A2,#$0F,LB77E
B773:          BRCLR   L00A3,#$0F,LB789
B777:          BRA     LB782
 ;
B779:  LB779   BCLR    L008E,#$30
B77C:          BRA     LB75C
 ;
B77E:  LB77E   BRCLR   L00A3,#$20,LB789
B782:  LB782   BRSET   L008E,#$02,LB7E0
B786:          JMP     LB83B
 ;
B789:  LB789   BSET    L008E,#$02
B78C:          BRSET   L00A2,#$20,LB7A4
B790:          BCLR    L008E,#$10
B793:          BSET    L008E,#$20
B796:          LDAA    L5F0D
B799:          STAA    L0141
B79C:          LDX     #$5FB8
B79F:          LDAB    L5F14
B7A2:          BRA     LB7B6
 ;
B7A4:  LB7A4   BSET    L008E,#$10
B7A7:          BCLR    L008E,#$20
B7AA:          LDAA    L5F0F
B7AD:          STAA    L0141
B7B0:          LDX     #$6043
B7B3:          LDAB    L5F15
B7B6:  LB7B6   STAB    L0140
B7B9:          LDD     L00C2
B7BC:          ASLD    
B7BD:          BCS     LB7C2
B7BF:          ASLD    
B7C0:          BCC     LB7C4
B7C2:  LB7C2   LDAA    #$00FF
B7C4:  LB7C4   ADDD    #$0080
B7C7:          SBCA    #$0000
B7C9:          PSHA    
B7CA:          LDAA    L00B5
B7CC:          LDAB    #$009A
B7CE:          MUL     
B7CF:          ADCA    #$0000
B7D1:          CMPA    #$0070
B7D3:          BLS     LB7D7
B7D5:          LDAA    #$0070
B7D7:  LB7D7   PULB    
B7D8:          JSR     LF4DE				; 3d LK UP
B7DB:          SUBA    #$80
B7DD:          STAA    L0146


B7E0:  LB7E0   LDX     #$60CE
B7E3:          LDAA    L00B2
B7E5:          LDAB    L00D7
B7E7:          CMPB    #$0020
B7E9:          BLS     LB7ED
B7EB:          LDAB    #$20
B7ED:  LB7ED   ASLB    
B7EE:          JSR     LF4DE				; 3d LK UP


B7F1:          SUBA    #$80
B7F3:          ADDA    L0146
B7F6:          BVC     LB7FC
B7F8:          LDAA    #$007F
B7FA:          ADCA    #$0000
B7FC:  LB7FC   ADDA    #$0080
B7FE:          LDAB    L0141
B801:          BEQ     LB81C
B803:          BRCLR   L008E,#$20,LB80C
B807:          ADDA    L5F0E
B80A:          BRA     LB813
 ;
B80C:  LB80C   BRCLR   L008E,#$10,LB813
B810:          ADDA    L5F10
B813:  LB813   DECB    
B814:          STAB    L0141
B817:          STAA    L0144
B81A:          BRA     LB822
 ;
B81C:  LB81C   STAA    L0144
B81F:          BCLR    L008E,#$30
B822:  LB822   LDAB    L0144
B825:          LDAA    L0145
B828:          ADDB    L0140
B82B:          BCS     LB830
B82D:          CBA     
B82E:          BGE     LB835
B830:  LB830   LDAA    L0144
B833:          BRA     LB83B
 ;
B835:  LB835   BCLR    L008E,#$02
B838:          CLR     L0141
B83B:  LB83B   BRCLR   L009C,#$02,LB850

B83F:          LDAB    L00D9  				; CURRENT GEAR
B841:          LDX     #$5F21
B844:          ABX     
B845:          SUBA    0,X
B847:          BVC     LB84D
B849:          LDAA    #$007F
B84B:          ADCA    #$0000
B84D:  LB84D   BPL     LB850
B84F:          CLRA    
B850:  LB850   TAB     
B851:          LDAA    L5F2C
B854:          PSHA    
B855:          SBA     
B856:          RORA    
B857:          ROLA    
B858:          BVC     LB85E
B85A:          LDAA    #$007F
B85C:          ADCA    #$0000
B85E:  LB85E   CMPA    L00E0
B860:          BGE     LB864
B862:          STAA    L00E0
B864:  LB864   PULA    
B865:          CMPB    L00DF
B867:          BGE     LB86B
B869:          STAB    L00DF
B86B:  LB86B   BRSET   L0098,#$08,LB87E
B86F:          PSHB    
B870:          PSHA    
B871:          JSR     LE664
B874:          PULA    
B875:          PULB    
B876:          BRSET   L0098,#$20,LB87E
B87A:          CBA     
B87B:          BLS     LB87E
B87D:          TBA     
B87E:  LB87E   ADDA    L0112
B881:          BVC     LB887
B883:          LDAA    #$007F
B885:          ADCA    #$0000
B887:  LB887   BPL     LB88A
B889:          CLRA    
B88A:  LB88A   STAA    L00E2 				; CURRENT TQ SIG PRESSURE


B88C:          RTS     
 		;------------------------------------------


B88D:  LB88D   BRCLR   L0083,#$02,LB89A
B891:          BRCLR   L0084,#$02,LB89A
B895:          BSET    L0085,#$40
B898:          BRA     LB8A1
 ;
B89A:  LB89A   BRSET   L0083,#$02,LB8A1
B89E:          BCLR    L0085,#$40
B8A1:  LB8A1   BRCLR   L0083,#$02,LB8BF
B8A5:          BRCLR   L0085,#$40,LB8BF
B8A9:          BRCLR   L0087,#$04,LB8BF

B8AD:          LDAB    L00D9   				; CURRENT GEAR
B8AF:          DECB    
B8B0:          BMI     LB8BF
B8B2:          LDX     #$5F16
B8B5:          ABX     
B8B6:          LDAB    0,X
B8B8:          ABA     
B8B9:          BVC     LB8BF
B8BB:          LDAA    #$007F
B8BD:          ADCA    #$0000
B8BF:  LB8BF   BRCLR   L009C,#$04,LB8D6
B8C3:          TAB     
B8C4:          LDAA    L01AC
B8C7:          LDX     #$5F30
B8CA:          JSR     LF4C1				; 2d LK UP
B8CD:          SUBA    #$0080
B8CF:          ABA     
B8D0:          BVC     LB8D6
B8D2:          LDAA    #$007F
B8D4:          ADCA    #$0000
B8D6:  LB8D6   TSTA    
B8D7:          BPL     LB8DA
B8D9:          CLRA    

B8DA:  LB8DA   LDAB    L00D9
B8DC:          CMPB    #$0003
B8DE:          BEQ     LB8F8
B8E0:          PSHA    
B8E1:          CLRA    
B8E2:          LDAB    L0844				; MAX KNOCK RETARD NOT IN WOT vs VAC
B8E5:          XGDX    
B8E6:          CLRA    
B8E7:          LDAB    L5F0C
B8EA:          FDIV    
B8EB:          XGDX    
B8EC:          LDAB    L020C				; DEG, KNOCK RETARD
B8EF:          MUL     
B8F0:          ADCA    #$0000
B8F2:          TAB     
B8F3:          PULA    
B8F4:          SBA     
B8F5:          BCC     LB8F8
B8F7:          CLRA    

B8F8:  LB8F8   TAB     
B8F9:          LDAA    L022F				; LINEAR IAT VALUE
B8FC:          SUBA    #$30
B8FE:          BCS     LB907
B900:          ASLA    
B901:          BCC     LB908
											;
B903:          LDAA    #$FF
B905:          BRA     LB908
 
B907:  LB907   CLRA   

		***************************************************
		* MAT TEMP OFFSET
		* FORCE MOTOR vs MAT TEMP
		* ECM TYPE 0E, BJKZ
		***************************************************
B908:  LB908   LDX     #$5F41				; FORCE MOTOR vs MAT TEMP
B90B:          JSR     LF4C1				; 2d LK UP
B90E:          SUBA    #$0080
B910:          ABA     
B911:          BVS     LB917
B913:          BMI     LB91B
B915:          BRA     LB91C
 ;
B917:  LB917   LDAA    #$007F
B919:          BRA     LB91C

 
B91B:  LB91B   CLRA    

B91C:  LB91C   RTS     
 			;-----------------------------------------


B91D:  LB91D   LDAB    L00D9  				; CURRENT GEAR
B91F:          BRSET   L0083,#$02,LB92A
B923:          BRCLR   L0083,#$10,LB936
B927:          INCB    
B928:          BRA     LB936
 ;
B92A:  LB92A   BRSET   L0083,#$01,LB936
B92E:          LDAA    L0090
B930:          ORAA    L0091
B932:          ORAA    L0092
B934:          BEQ     LB95D
B936:  LB936   CLRA    
B937:          DECB    
B938:          BMI     LB943
B93A:          LDX     #$BC65
B93D:          ASLB    
B93E:          ABX     
B93F:          LDX     0,X
B941:          BNE     LB948
											;
B943:  LB943   STAA    L0149			 	; CURRENT ADPTIVE MOD'ER INDEX W/IN TBL

B946:          BRA     LB95A



B948:  LB948   LDAA    L00B2
B94A:          LSRA    
B94B:          LSRA    
B94C:          LSRA    
B94D:          LSRA    
B94E:          ADCA    #$0000
B950:          STAA    L0149			 	; CURRENT ADPTIVE MOD'ER INDEX W/IN TBL
B953:          LDAA    L00B2
B955:          JSR     LF4C1				; 2d LK UP
B958:          SUBA    #$80
B95A:  LB95A   STAA    L0148
B95D:  LB95D   LDAA    L0148

B960:          RTS     
 			;------------------------------------------


			;------------------------------------------
			;
			;
			;
			;------------------------------------------
B961:            *****
B962:          SUBD    L61B3
B965:          COM     $00FB,X
B967:            *****
B968:          STAB    L0062				; ENGINE RPM/25
B96A:          STAB    L0065
B96C:          BRCLR   $66,X,#$43,LB9D6
B970:          LSRB    
B971:          ROR     $0065,X
B973:          ROR     $0076,X
B975:          ROR     $0087,X
B977:          ROR     $0098,X
B979:          ROR     $00A9,X
B97B:          ROR     $00BA,X
B97D:          ROR     $CB,X
B97F:          ROR     $DC,X
B981:          ROR     $F0,X
B983:          ASR     $04,X
B985:          ASR     $18,X
B987:          ASR     $2C,X
B989:          ASR     $40,X
B98B:          ROR     $DC,X
B98D:          ROR     $F0,X
B98F:          ASR     $04,X
B991:          TEST    
B992:          TEST    
B993:            *****
B994:          BNE     LB9F7
B996:            *****
B997:            *****
B998:          ANDA    #$005F
B99A:            *****
B99B:          CLRB    
B99C:          COM     $005F,X
B99E:          LSR     LF601
       LB99F
B9A1:            *****
B9A2:          BITB    #$0080
B9A4:          BEQ     LB9ED
B9A6:          ANDB    #$007F
B9A8:          STAB    L011A
B9AB:          CLRB    
B9AC:          STAB    L014A
B9AF:  LB9AF   LDAB    L014A
B9B2:          CMPB    #$0003
B9B4:          BEQ     LB9ED
       LB9B5
B9B6:          LDX     #$BC65
       LB9B8
B9B9:          LDY     #$BA32
B9BD:          ASLB    
B9BE:          ABX     
B9BF:          ABY     
B9C1:          LDX     0,X
B9C3:          LDY     0,Y
B9C6:          CLR     L014B
B9C9:  LB9C9   LDAB    L014B
B9CC:          CMPB    #$0011
B9CE:          BCC     LB9E8
B9D0:          LDAA    L032B
B9D3:          ADDA    0,X
B9D5:          LDAB    0,Y
       LB9D6
B9D8:          SEI     
B9D9:          STAB    0,X
B9DB:          SBA     
B9DC:          STAA    L032B
B9DF:          CLI     
B9E0:          INC     L014B
B9E3:          INX     
B9E4:          INY     
B9E6:          BRA     LB9C9
 ;
B9E8:  LB9E8   INC     L014A
B9EB:          BRA     LB9AF
 ;
B9ED:  LB9ED   RTS     
 ; ------------------------------------------
B9EE:  LB9EE   LDAB    L011A
B9F1:          BITB    #$0040
B9F3:          BEQ     LBA31
B9F5:          ANDB    #$00BF
B9F7:  LB9F7   STAB    L011A
B9FA:          CLRB    
B9FB:          STAB    L014A
B9FE:  LB9FE   LDAB    L014A
BA01:          CMPB    #$0003
BA03:          BEQ     LBA31
BA05:          LDX     #$BC65
BA08:          ASLB    
BA09:          ABX     
BA0A:          LDX     0,X
BA0C:          CLR     L014B
BA0F:          LDAA    #$0080
BA11:  LBA11   LDAB    L014B
BA14:          CMPB    #$0011
BA16:          BCC     LBA2C
BA18:          LDAB    L032B
BA1B:          ADDB    0,X
BA1D:          SUBB    #$0080
BA1F:          SEI     
BA20:          STAA    0,X
BA22:          STAB    L032B
BA25:          CLI     
BA26:          INC     L014B
BA29:          INX     
BA2A:          BRA     LBA11
 ;
BA2C:  LBA2C   INC     L014A
BA2F:          BRA     LB9FE
 ;
BA31:  LBA31   RTS     
 ; ------------------------------------------
BA32:          DEC     $81,X
BA34:          DEC     $92,X
BA36:          DEC     $A3,X
BA38:  LBA38   LDAA    L0093
BA3A:          ANDA    #$0060
BA3C:          CMPA    #$0020
BA3E:          BNE     LBA52

BA40:          LDX     #$BA5F
BA43:          LDAB    L00D9  				; CURRENT GEAR
BA45:          DECB    
BA46:          ASLB    
BA47:          ABX     
BA48:          LDX     0,X
BA4A:          BEQ     LBA52
BA4C:          LDAB    L0149			 	; CURRENT ADPTIVE MOD'ER INDEX W/IN TBL
BA4F:          ABX     
BA50:          INC     0,X
BA52:  LBA52   BITA    #$0020
BA54:          BEQ     LBA5B
BA56:          BSET    L0093,#$40
BA59:          BRA     LBA5E
 ;
BA5B:  LBA5B   BCLR    L0093,#$40
BA5E:  LBA5E   RTS     
 ; ------------------------------------------
BA5F:          FDIV    
BA60:          BGE     LBA65
BA62:          MUL     
BA63:          TEST    
BA64:          TEST    
BA65:  LBA65   BCLR    L0093,#$7D
BA68:          LDAA    L00AC 				; BAROMETRIC PRESS
BA6A:          CMPA    L68D1
BA6D:          BCC     LBA74
BA6F:          BSET    L0093,#$02
BA72:          BRA     LBA7C
 ;
BA74:  LBA74   CMPA    L68D2
BA77:          BLS     LBA7C
BA79:          BCLR    L0093,#$02
BA7C:  LBA7C   BRSET   L0093,#$02,LBA8C

BA80:          LDX     #$BC41

BA83:          BRCLR   L009F,#$02,LBA96		; BR IF NOT b1, 'PERF' PATTERN REQ'D
		 									;
BA87:          LDX     #$BC4D
BA8A:          BRA     LBA96
 ;
BA8C:  LBA8C   LDX     #$BC47
BA8F:          BRCLR   L009F,#$02,LBA96		; BR IF NOT b1, 'PERF' PATTERN REQ'D
		 									;
BA93:          LDX     #$BC53
BA96:  LBA96   LDAA    L0114
BA99:          BNE     LBAA7

BA9B:          LDAB    L00D9   				; CURRENT GEAR
BA9D:          DECB    
BA9E:          ASLB    
BA9F:          ABX     
BAA0:          LDX     0,X
BAA2:          LDAA    L00B2
BAA4:          JSR     LF4C1				; 2d LK UP
BAA7:  LBAA7   LDX     #$0136  				; TIME OF LATEST 1->2 SHIFT
BAAA:          LDAB    L00D9   				; CURRENT GEAR
BAAC:          DECB    
BAAD:          ABX     
BAAE:          LDAB    L00DB
BAB0:          SUBB    L00DA
BAB2:          STAB    L00DC
BAB4:          STAB    0,X
BAB6:          SBA     
BAB7:          RORA    
BAB8:          ROLA    
BAB9:          BVC     LBABF
BABB:          LDAA    #$007F
BABD:          ADCA    #$0000
BABF:  LBABF   STAA    L00DD
BAC1:          STAA    $0003,X
BAC3:          LDY     #$68A8
BAC7:          BRCLR   0,Y,#$02,LBAF9
BACC:          LDX     #$BC59
BACF:          LDAB    L00D9  				; CURRENT GEAR
BAD1:          DECB    
BAD2:          ASLB    
BAD3:          ABX     
BAD4:          LDX     0,X
BAD6:          LDAA    L00B2
BAD8:          JSR     LF4C1				; 2d LK UP
BADB:          LDX     #$019C
BADE:          LDAB    L00D9  				; CURRENT GEAR
BAE0:          DECB    
BAE1:          ABX     
BAE2:          LDAB    0,X
BAE4:          CMPB    #$00FF
BAE6:          BEQ     LBAF9
BAE8:          CBA     
BAE9:          BCC     LBAF9
BAEB:          BSET    L0093,#$10
BAEE:          LDX     #$699F
BAF1:          LDAB    L00D9  				; CURRENT GEAR
BAF3:          DECB    
BAF4:          ABX     
BAF5:          LDAA    $000E,X
BAF7:          BRA     LBB4D
 ;
BAF9:  LBAF9   LDX     #$699F
BAFC:          LDAB    L00D9  				; CURRENT GEAR
BAFE:          DECB    
BAFF:          ABX     
BB00:          LDAA    L68A8
BB03:          BITA    #$0001
BB05:          BNE     LBB22
BB07:          LDAA    L00DA
BB09:          CMPA    $0008,X
BB0B:          BCS     LBB22
BB0D:          LDAA    L00B5
BB0F:          CMPA    L69A5
BB12:          BLS     LBB22
BB14:          LDAA    L00B2
BB16:          CMPA    L69A6
BB19:          BLS     LBB22
BB1B:          BSET    L0093,#$04
BB1E:          LDAA    $0B,X
BB20:          BRA     LBB4D
 ;
BB22:  LBB22   LDAA    L00DD
BB24:          CMPA    0,X
BB26:          BGE     LBB2F
BB28:          BSET    L0093,#$08
BB2B:          LDAA    $0003,X
BB2D:          BRA     LBB4D
 ;
BB2F:  LBB2F   BSET    L0093,#$20
BB32:          LDX     #$BC3B
BB35:          LDAB    L00D9   				; CURRENT GEAR
BB37:          DECB    
BB38:          ASLB    
BB39:          ABX     
BB3A:          LDX     0,X
BB3C:          LDAA    L00DD
BB3E:          ADDA    #$0008
BB40:          BGE     LBB43
BB42:          CLRA    
BB43:  LBB43   CMPA    #$0010
BB45:          BLS     LBB49
BB47:          LDAA    #$0010
BB49:  LBB49   TAB     
BB4A:          ABX     
BB4B:          LDAA    0,X
BB4D:  LBB4D   STAA    L00E1
BB4F:          BRSET   L0093,#$04,LBB62
BB53:          BRCLR   L0093,#$38,LBB5F
BB57:          LDAA    L0091
BB59:          ORAA    L0090
BB5B:          ORAA    L0092
BB5D:          BEQ     LBB62
BB5F:  LBB5F   JMP     LBC3A
 ;
BB62:  LBB62   BSET    L0093,#$01
BB65:          LDY     #$BC65
BB69:          LDAB    L00D9  				; CURRENT GEAR
BB6B:          DECB    
BB6C:          ASLB    
BB6D:          ABY     
BB6F:          LDX     0,Y
BB72:          CLRB    
BB73:          STAB    L014B
BB76:  LBB76   LDAB    L014B
BB79:          CMPB    #$0004
BB7B:          BHI     LBB8D
BB7D:          ADDB    L0149			 	; CURRENT ADPTIVE MOD'ER INDEX W/IN TBL
BB80:          CMPB    #$0002
BB82:          BCC     LBB89
BB84:          INC     L014B
BB87:          BRA     LBB76
 ;
BB89:  LBB89   CMPB    #$12
BB8B:          BLS     LBB90
BB8D:  LBB8D   JMP     LBC3A
 ;
BB90:  LBB90   SUBB    #$0002
BB92:          ABX     
BB93:          LDAA    0,X
BB95:          SUBA    #$0080
BB97:          EORA    #$0009
BB99:          ANDA    #$07
BB9B:          STAA    L00DE
BB9D:          PSHX    
BB9E:          LDAB    L014B
BBA1:          LDX     #$6A16
BBA4:          ABX     
BBA5:          LDAB    0,X
BBA7:          PULX    
BBA8:          LDAA    L00E1
BBAA:          SUBA    #$0080
BBAC:          BPL     LBBB7
BBAE:          NEGA    
BBAF:          MUL     
BBB0:          ADCA    #$0000
BBB2:          NEGA    
BBB3:          BEQ     LBBEB
BBB5:          BRA     LBBBC
 ;
BBB7:  LBBB7   MUL     
BBB8:          ADCA    #$0000
BBBA:  LBBBA   BRA     LBBD7
 ;
BBBC:  LBBBC   LDAB    L00DF
BBBE:          BNE     LBBC3
BBC0:          CLRA    
BBC1:          BRA     LBBEB
 ;
BBC3:  LBBC3   CMPB    #$0010
BBC5:          BCC     LBBEB
BBC7:          NEGB    
BBC8:          ASLB    
BBC9:          ASLB    
BBCA:          ASLB    
BBCB:          ADDB    L00DE
BBCD:          SUBB    #$0005
BBCF:          BCS     LBBEB
BBD1:          CBA     
BBD2:          BCC     LBBEB
BBD4:          TBA     
BBD5:          BRA     LBBEB
 ;
BBD7:  LBBD7   LDAB    L00E0
BBD9:          BNE     LBBDE
BBDB:          CLRA    
BBDC:          BRA     LBBEB
 ;
BBDE:  LBBDE   CMPB    #$0010
BBE0:          BCC     LBBEB
BBE2:          ASLB    
BBE3:          ASLB    
BBE4:          ASLB    
BBE5:          ADDB    L00DE
BBE7:          CBA     
BBE8:          BLS     LBBEB
BBEA:          TBA     
BBEB:  LBBEB   LDAB    0,X
BBED:          SUBB    #$0080
BBEF:          ABA     
BBF0:          BVC     LBBF6
BBF2:          LDAA    #$007F
BBF4:          ADCA    #$0000
BBF6:  LBBF6   PSHX    
BBF7:          PSHA    
BBF8:          LDX     $000C,Y
BBFB:          LDAA    L00B2
BBFD:          JSR     LF4C1				; 2d LK UP
BC00:          SUBA    #$0080
BC02:          PULB    
BC03:          CBA     
BC04:          BLT     LBC07
BC06:          TAB     
BC07:  LBC07   LDX     6,Y
BC0A:          LDAA    L00B2
BC0C:          JSR     LF4C1				; 2d LK UP
BC0F:          SUBA    #$0080
BC11:          CBA     
BC12:          BGT     LBC15
BC14:          TAB     
BC15:  LBC15   PULX    
BC16:          TST     L0113
BC19:          BNE     LBC3A
BC1B:          BRCLR   L0086,#$08,LBC3A
BC1F:          TBA     
BC20:          NEGB    
BC21:          ADDB    0,X
BC23:          ADDB    L032B
BC26:          ADDA    #128
BC28:          ADDB    #128
BC2A:          SEI     
BC2B:          STAA    0,X
BC2D:          STAB    L032B
BC30:          CLI     
BC31:          INC     L014B
BC34:          LDX     0,Y
BC37:          JMP     LBB76
 ;
BC3A:  LBC3A   RTS     
 ; ------------------------------------------
BC3B:          ROL     $E3,X
BC3D:          ROL     $F4,X
BC3F:          DEC     $05,X
BC41:          ASL     $D3,X
BC43:          ASL     $E4,X
BC45:          ASL     $F5,X
BC47:          ROL     6,X
BC49:          ROL     $17,X
BC4B:          ROL     $28,X
BC4D:          ROL     $39,X
BC4F:          ROL     $4A,X
BC51:          ROL     $5B,X
BC53:          ROL     $6C,X
BC55:          ROL     $7D,X
BC57:          ROL     $8E,X
BC59:          ROL     $B0,X
BC5B:          ROL     $C1,X
BC5D:          ROL     $D2,X
BC5F:          ROL     $E3,X
BC61:          ROL     $F4,X
BC63:          DEC     $05,X
BC65:          IDIV    
BC66:          EORB    L0309
BC69:          FDIV    
BC6A:            *****
BC6B:          DEC     $004E,X
BC6D:          DEC     $005F,X
BC6F:          DEC     $0070,X
BC71:          DEC     $001B,X
BC73:          DEC     $2C,X
BC75:          DEC     $3D,X
BC77:  LBC77   PSHA    
BC78:          LDAA    L0198
BC7B:          BEQ     LBC7E
BC7D:          DECA    

BC7E:  LBC7E   LDX     L00F9

BC80:          BRCLR   L0083,#$03,LBCB6

BC84:          LDAB    L00D9  				; CURRENT GEAR
BC86:          CMPB    #$02					; 3rd GR
BC88:          BNE     LBC97

BC8A:          CPX     L68AF
BC8D:          BLS     LBCB6
BC8F:          LDAA    L5F06
BC92:          LDAB    L5F07
BC95:          BRA     LBCB3
 ;
BC97:  LBC97   CMPB    #$0003
BC99:          BNE     LBCB6
BC9B:          CPX     L68AF
BC9E:          BLS     LBCA8
BCA0:          LDAA    L5F08
BCA3:          LDAB    L5F09
BCA6:          BRA     LBCB3
 ;
BCA8:  LBCA8   CPX     L68B1
BCAB:          BLS     LBCB6
BCAD:          LDAA    L5F0A
BCB0:          LDAB    L5F0B
BCB3:  LBCB3   STAB    L0199
BCB6:  LBCB6   STAA    L0198
BCB9:          PULA    
BCBA:          BEQ     LBCC5
BCBC:          SUBA    L0199
BCBF:          BVC     LBCC5
BCC1:          LDAA    #$007F
BCC3:          ADCA    #$0000
BCC5:  LBCC5   RTS     
 ; ------------------------------------------
BCC6:  LBCC6   BRSET   L0098,#$04,LBCCE
BCCA:          BRCLR   L00A2,#$70,LBCD6
BCCE:  LBCCE   BCLR    L008E,#$01
BCD1:          CLRA    
BCD2:          CLRB    
BCD3:          JMP     LBE33
 ;
BCD6:  LBCD6   BRSET   L0083,#$01,LBCE1
BCDA:          BRCLR   L0083,#$08,LBCF3
BCDE:          JMP     LBE19
 ;
BCE1:  LBCE1   BSET    L008E,#$01
BCE4:          BCLR    L008F,#$01
BCE7:          LDD     #$0000
BCEA:          STAA    L013D
BCED:          STAA    L013C
BCF0:          JMP     LBE33
 ;
BCF3:  LBCF3   BRSET   L008E,#$01,LBCFA
BCF7:          JMP     LBE19
 ;
BCFA:  LBCFA   LDAB    L00D9  				; CURRENT GEAR
BCFC:          DECB    
BCFD:          BMI     LBD71
BCFF:          LDX     #$5F2D
BD02:          ABX     
BD03:          LDAA    L00DB
BD05:          CMPA    0,X
BD07:          BCC     LBD71
BD09:          CMPB    #$0002
BD0B:          BCC     LBD7A
BD0D:          LDX     #$5F19
BD10:          ABX     
BD11:          ABX     
BD12:          LDX     0,X
BD14:          CPX     L00F9
BD16:          BHI     LBD1E
BD18:          LDD     #$0000
BD1B:          JMP     LBE33
 ;
BD1E:  LBD1E   BRSET   L0091,#$10,LBD71
BD22:          BRSET   L008F,#$01,LBD3B
BD26:          LDX     #$BE55
BD29:          ABX     
BD2A:          ABX     
BD2B:          LDX     0,X
BD2D:          LDAA    L00B2
BD2F:          JSR     LF4C1				; 2d LK UP
BD32:          SUBA    #$0080
BD34:          CLRB    
BD35:          STD     L013E
BD38:          BSET    L008F,#$01
BD3B:  LBD3B   LDX     #$BE37
BD3E:          LDAB    L00D9  				; CURRENT GEAR
BD40:          DECB    
BD41:          ASLB    
BD42:          ABX     
BD43:          LDX     0,X
BD45:          LDAA    L00B2
BD47:          JSR     LF4C1				; 2d LK UP
BD4A:          CMPA    L00F9
BD4C:          BCC     LBD54
BD4E:          LDX     #$BE3D
BD51:          JMP     LBDFA
 ;
BD54:  LBD54   LDX     #$5F1D
BD57:          ABX     
BD58:          LDX     0,X
BD5A:          CPX     L00F9
BD5C:          BCS     LBD74
BD5E:          INC     L013D
BD61:          LDX     #$BE49
BD64:          ABX     
BD65:          LDX     0,X
BD67:          LDAA    L00B2
BD69:          JSR     LF4C1				; 2d LK UP
BD6C:          CMPA    L013D
BD6F:          BCC     LBD74
BD71:  LBD71   JMP     LBE19
 ;
BD74:  LBD74   LDX     #$BE43
BD77:          JMP     LBDFA
 ;
BD7A:  LBD7A   LDX     #$6864
BD7D:          LDAA    L00B2
BD7F:          JSR     LF4C1				; 2d LK UP
BD82:          CMPA    L013C
BD85:          BCS     LBD91
BD87:          LDAA    L00DB
BD89:          STAA    L013C
BD8C:          CLRA    
BD8D:          CLRB    
BD8E:          JMP     LBE33
 ;
BD91:  LBD91   LDX     #$6787
BD94:          LDAA    L00B2
BD96:          JSR     LF4C1				; 2d LK UP
BD99:          ADDA    L013C
BD9C:          BCC     LBDA0
BD9E:          LDAA    #$00FF
BDA0:  LBDA0   CMPA    L00DB
BDA2:          BCS     LBDE2
BDA4:          BRSET   L008F,#$01,LBDBE
BDA8:          LDX     #$BE55
BDAB:          LDAB    #$0004
BDAD:          ABX     
BDAE:          LDX     0,X
BDB0:          LDAA    L00B2
BDB2:          JSR     LF4C1				; 2d LK UP
BDB5:          SUBA    #$0080
BDB7:          CLRB    
BDB8:          STD     L013E
BDBB:          BSET    L008F,#$01
       LBDBD
BDBE:  LBDBE   LDX     #$BE3D
BDC1:          LDAB    #$0004
BDC3:          ABX     
BDC4:          LDX     0,X
BDC6:          LDAA    L00B2
BDC8:          JSR     LF4C1				; 2d LK UP
BDCB:          TAB     
BDCC:          CLRA    
BDCD:          SUBB    #$0080
BDCF:          SBCA    #$0000
BDD1:          ASLD    
BDD2:          ASLD    
BDD3:          ASLD    
BDD4:          ADDD    L013E
BDD7:          BVC     LBDE0
BDD9:          LDD     #$7FFF
BDDC:          ADCB    #$0000
BDDE:          ADCA    #$0000
BDE0:  LBDE0   BRA     LBE33
 ;
BDE2:  LBDE2   LDX     #$BE49
BDE5:          LDAB    #$0004
BDE7:          ABX     
BDE8:          LDX     0,X
BDEA:          LDAA    L00B2
BDEC:          JSR     LF4C1				; 2d LK UP
BDEF:          CMPA    L013D
BDF2:          BCS     LBE19
BDF4:          INC     L013D
BDF7:          LDX     #$BE43
BDFA:  LBDFA   ABX     
BDFB:          LDX     0,X
BDFD:          LDAA    L00B2
BDFF:          JSR     LF4C1				; 2d LK UP
BE02:          TAB     
BE03:          CLRA    
BE04:          SUBB    #$0080
BE06:          SBCA    #$0000
BE08:          ASLD    
BE09:          ASLD    
BE0A:          ASLD    
BE0B:          ADDD    L013E
BE0E:          BVC     LBE17
BE10:          LDD     #$7FFF
BE13:          ADCB    #$0000
BE15:          ADCA    #$0000
BE17:  LBE17   BRA     LBE33
 ;
BE19:  LBE19   BCLR    L008E,#$01
BE1C:          LDAB    L00D9  				; CURRENT GEAR
BE1E:          BNE     LBE23
BE20:          CLRA    
BE21:          BRA     LBE33
 ;
BE23:  LBE23   DECB    
BE24:          LDAA    #$0011
BE26:          MUL     
BE27:          LDX     #$6754
BE2A:          ABX     
BE2B:          LDAA    L00B2
BE2D:          JSR     LF4C1				; 2d LK UP
BE30:          SUBA    #$0080
BE32:          CLRB    
BE33:  LBE33   STD     L013E

BE36:          RTS     
 		;------------------------------------------



BE37:          ASR     $0098,X
BE39:          ASR     $00A9,X
BE3B:          ASR     $00BA,X
BE3D:          ASR     $00CB,X
BE3F:          ASR     $00DC,X
BE41:          ASR     $00ED,X
BE43:          ASR     $00FE,X
BE45:          ASL     $000F,X
BE47:          ASL     $0020,X
BE49:          ASL     $0031,X
BE4B:          ASL     $0042,X
BE4D:          ASL     $0053,X
BE4F:          ASR     $0054,X
BE51:          ASR     $0065,X
BE53:          ASR     $0076,X
BE55:          ASL     $0075,X
BE57:          ASL     $0086,X
BE59:          ASL     $0097,X
BE5B:          RTS     
 ; ------------------------------------------
BE5C:  LBE5C   BRCLR   L0099,#$08,LBE64
BE60:          CLRA    
BE61:          JMP     LBEB3
 ;
BE64:  LBE64   LDAA    L00B5
BE66:          ASLA    
BE67:          BCS     LBE6D
BE69:          ADDA    L00B5
BE6B:          BCC     LBE6F
BE6D:  LBE6D   LDAA    #$00FF
BE6F:  LBE6F   LDX     #$70A1
BE72:          JSR     LF4C1				; 2d LK UP
BE75:          TAB     
BE76:          LDAA    L0147
BE79:          SBA     
BE7A:          BCS     LBE80
BE7C:          CMPA    L00E2  				; CURRENT TQ SIG PRESSURE
BE7E:          BHI     LBE98
BE80:  LBE80   LDAA    L0147
BE83:          ABA     
BE84:          BCS     LBE8A
BE86:          CMPA    L00E2  				; CURRENT TQ SIG PRESSURE
BE88:          BCS     LBE90
BE8A:  LBE8A   BRSET   L008E,#$40,LBE90
BE8E:          BRA     LBE98
 ;
BE90:  LBE90   BSET    L008E,#$40
BE93:          LDX     #$6E59
BE96:          BRA     LBE9E
 ;
BE98:  LBE98   BCLR    L008E,#$40
BE9B:          LDX     #$6F7D
BE9E:  LBE9E   LDAA    L00E2  				; CURRENT TQ SIG PRESSURE
BEA0:          PSHA    
BEA1:          LDAB    #170
BEA3:          MUL     
BEA4:          PULB    
BEA5:          ASLB    
BEA6:          BCS     LBEAB
BEA8:          ABA     
BEA9:          BCC     LBEAD
BEAB:  LBEAB   LDAA    #$00FF
BEAD:  LBEAD   TAB     
BEAE:          LDAA    L00B5
BEB0:          JSR     LF4DE				; 3d LK UP

BEB3:  LBEB3   STAA    L014D				; REF CURRENT FORCE MTR CKT
        ;----------------------------------------------

        ;----------------------------------------------


BEB6:          LDAA    L00E2  				; CURRENT TQ SIG PRESSURE
BEB8:          STAA    L0147
BEBB:          RTS     
 ; ------------------------------------------
BEBC:  LBEBC   LDX     #$6AB4
BEBF:          LDAB    L018E
BEC2:          BEQ     LBEC8
BEC4:          DECB    
BEC5:          STAB    L018E
BEC8:  LBEC8   LDD     L00B2
BECA:          STAA    L00B3
BECC:          SBA     
BECD:          BCC     LBED7
BECF:          CMPA    $001A,X
BED1:          BHI     LBEE0
BED3:          LDAA    $001D,X
BED5:          BRA     LBEE6
 ;
BED7:  LBED7   CMPA    $001B,X
BED9:          BCS     LBEE0
BEDB:          LDAB    $001C,X
BEDD:          STAB    L018E
BEE0:  LBEE0   LDAA    L018D
BEE3:          BEQ     LBEE9
BEE5:          DECA    
BEE6:  LBEE6   STAA    L018D
BEE9:  LBEE9   LDD     L00EB
BEEB:          CPD     $0010,X
BEEE:          BGE     LBEF5
BEF0:          BSET    L0089,#$80
BEF3:          BRA     LBEFC
 ;
BEF5:  LBEF5   SUBD    $0012,X
BEF7:          BLE     LBEFC
BEF9:          BCLR    L0089,#$80
BEFC:  LBEFC   LDAB    $16,X
BEFE:          BRSET   L0089,#$40,LBF08
BF02:          BRSET   L0089,#$10,LBF08
BF06:          LDAB    $0017,X
BF08:  LBF08   LDAA    $0014,X
BF0A:          BRCLR   L0089,#$08,LBF10
BF0E:          LDAA    $0015,X
BF10:  LBF10   BCLR    L0089,#$08
BF13:          CMPA    L00D7
BF15:          BHI     LBF26
BF17:          LDAB    $0018,X
BF19:          BRSET   L0089,#$40,LBF23
BF1D:          BRSET   L0089,#$10,LBF23
BF21:          LDAB    $0019,X
BF23:  LBF23   BSET    L0089,#$08
BF26:  LBF26   BRCLR   0,X,#$04,LBF61
BF2A:          CMPB    L00B2
BF2C:          BLS     LBF61
BF2E:          BSET    L008B,#$08
BF31:          BRSET   L0089,#$40,LBF3B
BF35:          BRSET   L008B,#$20,LBF3B
BF39:          BRA     LBF61
 ;
BF3B:  LBF3B   BRCLR   L008B,#$10,LBF61
BF3F:          BSET    L008B,#$80
BF42:          BCLR    L008B,#$10
BF45:          LDD     L011B
BF48:          CPD     L6AE3
BF4C:          BHI     LBF5C
BF4E:          LDD     L0121
BF51:          ADDD    L6AE7
BF54:          BCC     LBF59
BF56:          LDD     #$FFFF
BF59:  LBF59   STD     L0121
BF5C:  LBF5C   CLRA    
BF5D:          CLRB    
BF5E:          STD     L011B
BF61:  LBF61   RTS     
 ; ------------------------------------------
BF62:  LBF62   LDX     L011B
BF65:          INX     
BF66:          BEQ     LBF6B
BF68:          STX     L011B
BF6B:  LBF6B   LDX     L011D
BF6E:          INX     
BF6F:          BNE     LBF72
BF71:          DEX     
BF72:  LBF72   STX     L011D
BF75:          CPX     L6AE5
BF78:          BCS     LBF8C
BF7A:          CLRA    
BF7B:          CLRB    
BF7C:          STD     L011D
BF7F:          LDD     L0121
BF82:          SUBD    L6AE9
BF85:          BCC     LBF89
BF87:          CLRA    
BF88:          CLRB    
BF89:  LBF89   STD     L0121
BF8C:  LBF8C   LDD     L0121
BF8F:          CPD     L6AE1
BF93:          BCC     LBF9B
BF95:          LDD     L6AE1
BF98:          STD     L0121
BF9B:  LBF9B   LDX     #$6AB4
BF9E:          BRCLR   L008B,#$20,LBFB5
BFA2:          LDAA    L0123
BFA5:          CMPA    L6AEB
BFA8:          BCC     LBFB2
BFAA:          INCA    
BFAB:          BEQ     LBFB8
BFAD:          STAA    L0123
BFB0:          BRA     LBFB8
 ;
BFB2:  LBFB2   BCLR    L008B,#$20
BFB5:  LBFB5   CLR     L0123
BFB8:  LBFB8   LDAB    L012D
BFBB:          INCB    
BFBC:          BEQ     LBFC1
BFBE:          STAB    L012D
BFC1:  LBFC1   LDAB    L012E
BFC4:          INCB    
BFC5:          BEQ     LBFCA
BFC7:          STAB    L012E
BFCA:  LBFCA   BRSET   L0089,#$40,LBFDB
BFCE:          BRSET   L0089,#$10,LBFDB
BFD2:          LDAB    L0125
BFD5:          INCB    
BFD6:          BEQ     LBFDB
BFD8:          STAB    L0125
BFDB:  LBFDB   LDAA    L018C
BFDE:          BEQ     LBFE3
BFE0:          DECA    
BFE1:          BRA     LBFEF
 ;
BFE3:  LBFE3   BRCLR   L0083,#$08,LBFF2
BFE7:          LDX     #$6AD2
BFEA:          LDAB    L00D9  				; CURRENT GEAR
BFEC:          ABX     
BFED:          LDAA    0,X
BFEF:  LBFEF   STAA    L018C
BFF2:  LBFF2   LDAA    L0124
BFF5:          BEQ     LBFFA
BFF7:          DECA    
BFF8:          BRA     LC007
 ;
BFFA:  LBFFA   BRCLR   L0083,#$01,LC00A
BFFE:          LDX     #$6AD5
C001:          LDAB    L00D9  				; CURRENT GEAR
C003:          DECB    
C004:          ABX     
C005:          LDAA    0,X
C007:  LC007   STAA    L0124
C00A:  LC00A   RTS     
 ; ------------------------------------------
C00B:  LC00B   BRSET   L008A,#$10,LC01A
C00F:          BRSET   L008B,#$04,LC020
C013:          BRSET   L008B,#$02,LC01D
C017:          JMP     LC260
 ;
C01A:  LC01A   JMP     LC2D5
 ;
C01D:  LC01D   JMP     LC180
 ;
C020:  LC020   BRSET   L0087,#$02,LC045
C024:          BRCLR   L008B,#$80,LC045
C028:          LDD     L011F
C02B:          CPD     L0121
C02F:          BCC     LC042
C031:          BSET    L008B,#$40
C034:          ADDD    #$0001
C037:          BCC     LC03C
C039:          LDD     #$FFFF
C03C:  LC03C   STD     L011F
C03F:          JMP     LC265
 ;
C042:  LC042   BCLR    L008B,#$80
C045:  LC045   CLRA    
C046:          CLRB    
C047:          STD     L011F
C04A:          BCLR    L008B,#$40
C04D:          BRSET   L0089,#$40,LC069
C051:          BSET    L008B,#$10
C054:          BSET    L0089,#$40
C057:          BCLR    L0089,#$10
C05A:          CLRA    
C05B:          STAA    L0125
C05E:          STAA    L012D
C061:          STAA    L012E
C064:          LDAA    L6ADD
C067:          STAA    L00E7
C069:  LC069   BRSET   L0089,#$20,LC0DE
C06D:          LDX     #$C35E
C070:          LDAA    L007F
C072:          LDAB    L00D9   				; CURRENT GEAR
C074:          JSR     LD8FE
C077:          BCC     LC07C
C079:          LDX     #$6DB3
C07C:  LC07C   LDY     #$010B
C080:          JSR     LC271
C083:          LDAA    L0110
C086:          BNE     LC09C
C088:          LDX     #$C3A2
C08B:          LDAB    L00D9  				; CURRENT GEAR
C08D:          LDAA    L007F
C08F:          JSR     LD8FE
C092:          BCC     LC097
C094:          LDX     #$6E08
C097:  LC097   LDAA    L00B2
C099:          JSR     LF4C1				; 2d LK UP
C09C:  LC09C   LDAB    #$0008
C09E:          MUL     
C09F:          STAA    L018F
C0A2:          ADDB    L018F
C0A5:          ADDB    L0127
C0A8:          BCC     LC0AB
C0AA:          INCB    
C0AB:  LC0AB   ADCA    L0126
C0AE:          BCC     LC0B3
C0B0:          LDD     #$FFFF
C0B3:  LC0B3   CPD     L00F1
C0B6:          BCC     LC0BA
C0B8:          LDD     L00F1
C0BA:  LC0BA   STD     L00F3
C0BC:          LDX     L00ED
C0BE:          CPX     L6AD9
C0C1:          BLS     LC0C9
C0C3:          LDAA    #$0001
C0C5:          STAA    L00E7
C0C7:          BRA     LC0D3
 ;
C0C9:  LC0C9   CPX     L6ADB
C0CC:          BCC     LC0D3
C0CE:          DEC     L00E7
C0D1:          BEQ     LC0E0
C0D3:  LC0D3   LDD     L00F3
C0D5:          CPD     L0129
C0D9:          BCC     LC0E0
C0DB:          JMP     LC23F
 ;
C0DE:  LC0DE   BRA     LC103
 ;
C0E0:  LC0E0   LDAA    L012D
C0E3:          STAA    L00E6
C0E5:          BSET    L0089,#$20
C0E8:          LDX     #$6E3B
C0EB:          LDY     #$010F
C0EF:          JSR     LC271
C0F2:          CLRA    
C0F3:          STAA    L00F6
C0F5:          STAA    L012D
C0F8:          LDAA    $0011,X
C0FA:          STAA    L00EA
C0FC:          LDAA    $16,X
C0FE:          STAA    L00F5
C100:          JMP     LC23F
 ;
C103:  LC103   BRCLR   L0083,#$03,LC117
C107:          BRCLR   L00A2,#$04,LC111
C10B:          LDAB    L00D9  				; CURRENT GEAR
C10D:          CMPB    #$0003
C10F:          BEQ     LC117
C111:  LC111   LDD     L0129
C114:          JMP     LC26D
 ;
C117:  LC117   LDX     #$6E3B
C11A:          LDY     #$010F
C11E:          JSR     LC271
C121:          LDAB    L00EA
C123:          BEQ     LC128
C125:          DECB    
C126:          BRA     LC138
 ;
C128:  LC128   LDAB    $0011,X
C12A:          BEQ     LC138
C12C:          LDAA    L00E9
C12E:          ADDA    $0012,X
C130:          BVC     LC136
C132:          LDAA    #$007F
C134:          ADCA    #$0000
C136:  LC136   STAA    L00E9
C138:  LC138   STAB    L00EA
C13A:          LDY     L00ED
C13D:          LDAB    L00F5
C13F:          BEQ     LC144
C141:          DECB    
C142:          BRA     LC157
 ;
C144:  LC144   CPY     $13,X
C147:          BLS     LC159
C149:          LDAA    L00E9
C14B:          ADDA    $0015,X
C14D:          BVC     LC153
C14F:          LDAA    #$007F
C151:          ADCA    #$0000
C153:  LC153   STAA    L00E9
C155:          LDAB    $16,X
C157:  LC157   STAB    L00F5
C159:  LC159   LDAB    L00F6
C15B:          INCB    
C15C:          CPY     $0017,X
C15F:          BCC     LC162
C161:          CLRB    
C162:  LC162   STAB    L00F6
C164:          LDAA    L00F1
C166:          LSRD    
C167:          SUBA    #$0080
C169:          ADDA    L00E9
C16B:          BVC     LC171
C16D:          LDAA    #$007F
C16F:          ADCA    #$0000
C171:  LC171   ADDA    #$0080
C173:          ASLD    
C174:          LDAB    L00F2
C176:          BCC     LC17B
C178:          LDD     #$FFFF
C17B:  LC17B   STD     L00F3
C17D:          JMP     LC23F
 ;
C180:  LC180   BRSET   L0089,#$40,LC18B
C184:          BRSET   L0089,#$10,LC19F
C188:          JMP     LC260
 ;
C18B:  LC18B   BSET    L0089,#$10
C18E:          BCLR    L0089,#$60
C191:          BCLR    L008A,#$40
C194:          CLRA    
C195:          CLRB    
C196:          STD     L011F
C199:          STAA    L012D
C19C:          STAA    L012E
C19F:  LC19F   LDX     #$C380
C1A2:          LDAB    L00D9   				; CURRENT GEAR
C1A4:          LDAA    L007F
C1A6:          JSR     LD8FE
C1A9:          BCC     LC1AE
C1AB:          LDX     #$6CC5
C1AE:  LC1AE   LDY     #$010C
C1B2:          JSR     LC271
C1B5:          LDAA    L0110
C1B8:          BNE     LC1D8
C1BA:          LDAA    L018E
C1BD:          BEQ     LC1C4
C1BF:          LDAA    L6ADE
C1C2:          BRA     LC1D8
 ;
C1C4:  LC1C4   LDX     #$C3C4
C1C7:          LDAB    L00D9  				; CURRENT GEAR
C1C9:          LDAA    L007F
C1CB:          JSR     LD8FE
C1CE:          BCC     LC1D3
C1D0:          LDX     #$6D1A
C1D3:  LC1D3   LDAA    L00B2
C1D5:          JSR     LF4C1				; 2d LK UP
C1D8:  LC1D8   LDAB    #$0008
C1DA:          MUL     
C1DB:          STAA    L018F
C1DE:          ADDB    L018F
C1E1:          SUBB    L0127
C1E4:          BCC     LC1E7
C1E6:          DECB    
C1E7:  LC1E7   SBCA    L0126
C1EA:          BCC     LC23C
C1EC:          NEGA    
C1ED:          NEGB    
C1EE:          SBCA    #$0000
C1F0:          CPD     L00F1
C1F3:          BLS     LC1F7
C1F5:          LDD     L00F1
C1F7:  LC1F7   STD     L00F3
C1F9:          LDD     L012B
C1FC:          CPD     L00F3
C1FF:          BHI     LC23C
C201:          BRSET   L008A,#$40,LC228
C205:          LDD     L00ED
C207:          SUBD    L6ADF
C20A:          BHI     LC220
C20C:          LDAA    L010D
C20F:          BNE     LC219
C211:          LDX     #$6D3C
C214:          LDAA    L00B2
C216:          JSR     LF4C1				; 2d LK UP
C219:  LC219   CMPA    L012D
C21C:          BCC     LC23A
C21E:          BRA     LC23C
 ;
C220:  LC220   LDAA    L012D
C223:          STAA    L00E5
C225:          BSET    L008A,#$40
C228:  LC228   LDAA    L010E
C22B:          BNE     LC235
C22D:          LDX     #$6D4D
C230:          LDAA    L00B2
C232:          JSR     LF4C1				; 2d LK UP
C235:  LC235   CMPA    L012D
C238:          BCS     LC23C
C23A:  LC23A   BRA     LC23F
 ;
C23C:  LC23C   JMP     LC260
 ;
C23F:  LC23F   LDD     L012B
C242:          CPD     L00F3
C245:          BCC     LC251
C247:          LDD     L0129
C24A:          CPD     L00F3
C24D:          BLS     LC251
C24F:          LDD     L00F3
C251:  LC251   STD     L0126
C254:          SUBD    L00F1
C256:          RORA    
C257:          ADCA    #$0000
C259:          BVC     LC25C
C25B:          DECA    
C25C:  LC25C   STAA    L00E9
C25E:          BRA     LC270
 ;
C260:  LC260   CLRA    
C261:          CLRB    
C262:          STD     L011F
C265:  LC265   BCLR    L0089,#$70
C268:          BCLR    L008A,#$40
C26B:          CLRA    
C26C:          CLRB    
C26D:  LC26D   STD     L0126
C270:  LC270   RTS     
 ; ------------------------------------------
C271:  LC271   LDAA    0,Y
C274:          TAB     
C275:          BNE     LC2C3
C277:          PSHX    
C278:          CLR     L0192
C27B:          LDX     #$6E2A
C27E:          LDAA    L00E2  				; CURRENT TQ SIG PRESSURE
C280:          ASLA    
C281:          BCC     LC285
C283:          LDAA    #$00FF
C285:  LC285   JSR     LF4C1				; 2d LK UP
C288:          PULX    
C289:          PSHA    
C28A:          LDAB    0,X
C28C:          MUL     
C28D:          STD     L0190
C290:          PULB    
C291:          LDAA    L00B2
C293:          JSR     LF4C1				; 2d LK UP
C296:          MUL     
C297:          SUBD    L0190
C29A:          ROL     L0192
C29D:          NEG     L0192
C2A0:          ASLD    
C2A1:          ROL     L0192
C2A4:          ADDA    0,X
C2A6:          PSHB    
C2A7:          LDAB    L0192
C2AA:          ADCB    #$0000
C2AC:          PULB    
C2AD:          BGE     LC2B1
C2AF:          CLRA    
C2B0:          CLRB    
C2B1:  LC2B1   BNE     LC2C0
C2B3:          STAA    L018F
C2B6:          ADDB    L018F
C2B9:          BCC     LC2C3
C2BB:          ADDD    #$0101
C2BE:          BCC     LC2C3
C2C0:  LC2C0   LDD     #$FFFF
C2C3:  LC2C3   SUBA    #$0080
C2C5:          ADDA    $0001,Y
C2C8:          BVC     LC2D1
C2CA:          LDD     #$7FFF
C2CD:          ADCB    #$0000
C2CF:          ADCA    #$0000
C2D1:  LC2D1   ADDA    #$0080
C2D3:          STD     L00F1
C2D5:  LC2D5   RTS     
 ; ------------------------------------------
C2D6:          INX     
C2D7:          INX     
C2D8:          TEST    
C2D9:          TEST    
C2DA:          INC     $003D,X
C2DC:          INC     $004E,X
C2DE:          INC     $005F,X
C2E0:          TEST    
C2E1:          TEST    
C2E2:          TEST    
C2E3:          TEST    
C2E4:          INC     $001B,X
C2E6:          INC     $002C,X
C2E8:          TEST    
C2E9:          TEST    
C2EA:          TEST    
C2EB:          TEST    
C2EC:            *****
C2ED:          ADCB    L6C0A
C2F0:          TEST    
C2F1:          TEST    
C2F2:            *****
C2F3:          LDAB    #$006B
C2F5:          STAB    L006B
C2F7:          EORB    $0008,X
C2F9:          INX     
C2FA:          TEST    
C2FB:          TEST    
C2FC:          DEC     $00F4,X
C2FE:          DEC     $00F5,X
C300:          DEC     $00F6,X
C302:          TEST    
C303:          TEST    
C304:          TEST    
C305:          TEST    
C306:          TEST    
C307:          TEST    
C308:          TEST    
C309:          TEST    
C30A:          TEST    
C30B:          TEST    
C30C:          TEST    
C30D:          TEST    
C30E:          TEST    
C30F:          TEST    
C310:          TEST    
C311:          TEST    
C312:          TEST    
C313:          TEST    
C314:          DEC     $00EE,X
C316:          DEC     $00EF,X
C318:          DEC     $00F0,X
C31A:          INX     
C31B:          INX     
C31C:          TEST    
C31D:          TEST    
C31E:            *****
C31F:            *****
C320:            *****
C321:          SBCA    #$006B
C323:          SUBD    L0000
C325:          TEST    
C326:          TEST    
C327:          TEST    
C328:            *****
C329:          ANDA    $006B,X
C32B:          BITA    L0000
C32E:          TEST    
C32F:          TEST    
C330:            *****
C331:          BLT     LC39E
C333:          WAI     
C334:          TEST    
C335:          TEST    
C336:          DEC     $00FA,X
C338:            *****
C339:          SEV     
C33A:            *****
C33B:          BSET    $0008,X,#$08
C33E:          TEST    
C33F:          TEST    
C340:          DEC     $00F7,X
C342:          DEC     $00F8,X
C344:          DEC     $00F9,X
C346:          TEST    
C347:          TEST    
C348:          TEST    
C349:          TEST    
C34A:          TEST    
C34B:          TEST    
C34C:          TEST    
C34D:          TEST    
C34E:          TEST    
C34F:          TEST    
C350:          TEST    
C351:          TEST    
C352:          TEST    
C353:          TEST    
C354:          TEST    
C355:          TEST    
C356:          TEST    
C357:          TEST    
C358:          DEC     $00F1,X
C35A:          DEC     $00F2,X
C35C:          DEC     $00F3,X
C35E:          INX     
C35F:          INX     
C360:          TEST    
C361:          TEST    
C362:          TEST    
C363:          TEST    
C364:          TST     $00B3,X
C366:          TST     $00C4,X
C368:          TEST    
C369:          TEST    
C36A:          TEST    
C36B:          TEST    
C36C:          TST     $00B3,X
C36E:          TST     $00C4,X
C370:          TEST    
C371:          TEST    
C372:          TEST    
C373:          TEST    
C374:          TST     $00B3,X
C376:          TST     $00C4,X
C378:          TEST    
C379:          TEST    
C37A:          TEST    
C37B:          TEST    
C37C:          TST     $00B3,X
C37E:          TST     $00C4,X
C380:          INX     
C381:          INX     
C382:          TEST    
C383:          TEST    
C384:          TEST    
C385:          TEST    
C386:          INC     $00C5,X
C388:          INC     $00D6,X
C38A:          TEST    
C38B:          TEST    
C38C:          TEST    
C38D:          TEST    
C38E:          INC     $00C5,X
C390:          INC     $00D6,X
C392:          TEST    
C393:          TEST    
C394:          TEST    
C395:          TEST    
C396:          INC     $00C5,X
C398:          INC     $00D6,X
C39A:          TEST    
C39B:          TEST    
C39C:          TEST    
C39D:          TEST    
C39E:  LC39E   INC     $00C5,X
C3A0:          INC     $00D6,X
C3A2:          INX     
C3A3:          INX     
C3A4:          TEST    
C3A5:          TEST    
C3A6:          TEST    
C3A7:          TEST    
C3A8:          JMP     $0008,X
 ;
C3AA:          JMP     $0019,X
 ;
C3AC:          TEST    
C3AD:          TEST    
C3AE:          TEST    
C3AF:          TEST    
C3B0:          JMP     $0008,X
 ;
C3B2:          JMP     $0019,X
 ;
C3B4:          TEST    
C3B5:          TEST    
C3B6:          TEST    
C3B7:          TEST    
C3B8:          JMP     $0008,X
 ;
C3BA:          JMP     $0019,X
 ;
C3BC:          TEST    
C3BD:          TEST    
C3BE:          TEST    
C3BF:          TEST    
C3C0:          JMP     $0008,X
 ;
C3C2:          JMP     $0019,X
 ;
C3C4:          INX     
C3C5:          INX     
C3C6:          TEST    
C3C7:          TEST    
C3C8:          TEST    
C3C9:          TEST    
C3CA:          TST     $001A,X
C3CC:          TST     $002B,X
C3CE:          TEST    
C3CF:          TEST    
C3D0:          TEST    
C3D1:          TEST    
C3D2:          TST     $001A,X
C3D4:          TST     $002B,X
C3D6:          TEST    
C3D7:          TEST    
C3D8:          TEST    
C3D9:          TEST    
C3DA:          TST     $001A,X
C3DC:          TST     $002B,X
C3DE:          TEST    
C3DF:          TEST    
C3E0:          TEST    
C3E1:          TEST    
C3E2:          TST     $001A,X
C3E4:          TST     $002B,X


C3E6:          IDIV    
C3E7:          INX     
C3E8:          TEST    
C3E9:          TEST    
C3EA:          TEST    
C3EB:          TEST    
C3EC:          TEST    
C3ED:          TEST    
C3EE:          TEST    
C3EF:          TEST    
C3F0:          TSTB    
C3F1:          PULX    
C3F2:          TSTB    
C3F3:          PULX    
C3F4:          TSTB    
C3F5:          PULX    
C3F6:          TSTB    
C3F7:          PULX    
C3F8:          IDIV    
C3F9:          INX     
C3FA:          TEST    
C3FB:          TEST    
C3FC:          TEST    
C3FD:          TEST    
C3FE:          TEST    
C3FF:          TEST    
C400:          TEST    
C401:          TEST    
C402:          TSTB    
C403:          PULX    
C404:          TSTB    
C405:          PULX    
C406:          TSTB    
C407:          PULX    
C408:          TSTB    
C409:          PULX    
C40A:  LC40A   LDAA    L0119
C40D:          BNE     LC47F
C40F:          BRCLR   L00A4,#$08,LC447
C413:          LDAB    L00A9
C416:          CMPB    L70B2
C419:          BCC     LC425
C41B:          LDAA    L70B7
C41E:          PSHA    
C41F:          PSHB    
C420:          LDAB    L70B2
C423:          BRA     LC434
 ;
C425:  LC425   CMPB    L70B3
C428:          BLS     LC447
C42A:          LDAA    L70B7
C42D:          PSHA    
C42E:          COMB    
C42F:          PSHB    
C430:          LDAB    L70B3
C433:          COMB    
C434:  LC434   CLRA    
C435:          XGDX    
C436:          CLRA    
C437:          PULB    
C438:          FDIV    
C439:          XGDX    
C43A:          PULB    

C43B:          MUL     
C43C:          ADCA    #$00
C43E:          LDAB    L015A
C441:          MUL     
C442:          ADCA    #$00
C444:          STAA    L015A

C447:  LC447   BRCLR   L00A4,#$17,LC482
C44B:          LDAB    L00A9
C44E:          CMPB    L70B4
C451:          BCC     LC45D
C453:          LDAA    L70B6
C456:          PSHA    
C457:          PSHB    
C458:          LDAB    L70B4
C45B:          BRA     LC46F
 ;
C45D:  LC45D   LDAB    L00A9
C460:          CMPB    L70B5
C463:          BLS     LC482
C465:          LDAA    L70B6
C468:          PSHA    
C469:          COMB    
C46A:          PSHB    
C46B:          LDAB    L70B5
C46E:          COMB    
C46F:  LC46F   CLRA    
C470:          XGDX    
C471:          CLRA    
C472:          PULB    
C473:          FDIV    
C474:          XGDX    
C475:          PULB    
C476:          MUL     
C477:          ADCA    #$00
C479:          LDAB    L015A
C47C:          MUL     
C47D:          ADCA    #$00
C47F:  LC47F   STAA    L015A

C482:  LC482   RTS     
 ; ------------------------------------------
C483:  LC483   CLRA  

 		  	;  MNP PATTERN
			;
            ; b3 1 = ILLEGAL PATTERN REQUESTED 
            ; b2 1 = 'MANUAL' PATTERN REQUESTED
            ; b1 1 = 'PERFORMANCE' PATTERN REQUESTED
            ; b0 1 = 'NORMAL' PATTERN REQUESTED
            ;-----------------------------
C484:          BRCLR   L009F,#$04,LC48C		; BR IF NOT b2, "MANUAL" PATTERN REQ
											;
C488:          ORAA    #$01
C48A:          BRA     LC496
 

C48C:  LC48C   BRCLR   L009F,#$02,LC494		; BR IF NOT b1,	"PERF PATTERN REQ'D"
											;
C490:          ORAA    #$0002
C492:          BRA     LC496
 

C494:  LC494   ORAA    #$04					; SET b2
C496:  LC496   STAA    L0080

C498:          LDAA    #$01

C49A:          BRSET   L009F,#$04,LC4A0		; BR IF b2, "MANUAL" PATTERN REQ
											;
C49E:          LDAA    #$02
C4A0:  LC4A0   STAA    L0082

C4A2:          CLRA    
C4A3:          BRCLR   L0087,#$02,LC4AB
											;
C4A7:          ORAA    #$01
C4A9:          BRA     LC4BD
 

C4AB:  LC4AB   BRCLR   L009F,#$04,LC4B3		; BR IF NOT b2, "MANUAL" PATTERN REQ
											; ... els
C4AF:          ORAA    #$02
C4B1:          BRA     LC4BD


C4B3:  LC4B3   BRCLR   L009F,#$02,LC4BB		; BR IF NOT b1,	"PERF PATTERN REQ'D"
											;
C4B7:          ORAA    #$04
C4B9:          BRA     LC4BD


C4BB:  LC4BB   ORAA    #$08
C4BD:  LC4BD   STAA    L007F
C4BF:          CLRA    
C4C0:          BRCLR   L0087,#$04,LC4C8
C4C4:          ORAA    #$0001
C4C6:          BRA     LC4E2

C4C8:  LC4C8   BRCLR   L0087,#$02,LC4D0
C4CC:          ORAA    #$02

C4CE:          BRA     LC4E2
 
C4D0:  LC4D0   BRCLR   L009F,#$04,LC4D8		; BR IF NOT b2, "MANUAL PATTERN REQ'ED
											;
C4D4:          ORAA    #$04					; SET b2
C4D6:          BRA     LC4E2


C4D8:  LC4D8   BRCLR   L009F,#$02,LC4E0		; BR IF NOT b1, "PERF PATTERN REQ'ED
											;
C4DC:          ORAA    #$08					; SET b3
C4DE:          BRA     LC4E2


C4E0:  LC4E0   ORAA    #$10					; SET b4
C4E2:  LC4E2   STAA    L0081

C4E4:          RTS     
 		;------------------------------------------


C4E5:  LC4E5   JSR     LB0E4
C4E8:          JSR     LD9B7
C4EB:          JSR     LDA6F
C4EE:          JSR     LDAE2
C4F1:          JSR     LC40A
C4F4:          RTS     
		;------------------------------------------
C4F5:  LC4F5   JSR     LE905
C4F8:          JSR     LE99E
C4FB:          JSR     LEE02
C4FE:          JSR     LEE61
C501:          JSR     LEEBC
C504:          JSR     LEC2D
C507:          JSR     LECFF
C50A:          JSR     LEF88
C50D:          JSR     LF02F
C510:          JSR     LF0AD
C513:          RTS     
 ; ------------------------------------------
C514:  LC514   LDAB    L00D9   				; CURRENT GEAR
C516:          LDX     #$B319
C519:          ABX     
C51A:          LDAA    0,X
C51C:          LDAB    L004C
C51F:          ANDB    #$00FC
C521:          ABA     
C522:          STAA    L004C
C525:          LDX     #$0399
C528:          BRCLR   $0001,X,#$40,LC532
C52C:          BRSET   $0002,X,#$40,LC546
C530:          BRA     LC54B
 ;
C532:  LC532   BRSET   L0099,#$08,LC54B
C536:          BRSET   L001C,#$02,LC54B
C53A:          BRSET   L001D,#$80,LC54B
C53E:          BRSET   L0086,#$01,LC54B
C542:          BRSET   L008E,#$80,LC54B
C546:  LC546   BSET    L004C,#$20
C549:          BRA     LC54E
 ;
C54B:  LC54B   BCLR    L004C,#$20

			;----------------------------------------------
			; AFR MD BYTE 5,	 0001 0000, (DIG I/O)
			;
			; b7 1 = MAN, (0 = TCC)
			; b6 1 = TCC (Non Elect xmish)
			; b5 1 = Not Used 
			; b4 1 = CONV OVER HEAT PROTECTION
			;
			; b3 1 = BURST KNOCK RETARD
			; b2 1 = A/C CLUTCH CNT'L, 0 = CPI TUNE
			; b1 1 = Not Used
			; b0 1 = 1 DO RPM/MPH LMT, (GOV'R OPT)
			;
			;----------------------------------------------
C54E:  LC54E   LDX     #$400F
C551:          BRSET   0,X,#$40,LC56E		;
C555:          BCLR    L008B,#$01			; CLR b0
C558:          LDD     L0126
C55B:          CPD     L012B
C55F:          BLS     LC568
C561:          BRCLR   L008A,#$04,LC568
C565:          BSET    L008B,#$01
C568:  LC568   TAB     
C569:          LDAA    #127
C56B:          STD     L306A

C56E:  LC56E   RTS     
 			;------------------------------------------
 			
 			;------------------------------------------
			; READ BATTERY VOLTAGE
			;
 			;------------------------------------------
C56F:  LC56F   LDX     #$3000				; INDEX CPU REG'S
											;
C572:          LDAA    #$02					;
C574:          JSR     LF275				;
											;
C577:          LDAA    #$01					;
C579:          SEI     						; SECURE INTERUPTS 
C57A:          JSR     LF25F				; A/D CNT'L MODE

C57D:          LDAB    $34,X				; READ A/D CH 
C57F:          CLI     						; RESUME & CLR INTERUPTS
C580:          STAB    L0055				; BATTERY VOLTS * 10

C582:          RTS     
 			;------------------------------------------



                    ;---------------------------------
				    ; 0000 0001, SPD SENSOR SOURCE
                    ;
                    ; b2 1 = BARO & MAP SENSOR USED, 0 = MAP ONLY
                    ;------------------------------------
C583:  LC583   LDX     #$5D02				; INDEX 
C586:          BRCLR   0,X,#$04,LC5A6		; BR OF NOT b2
											;

			;
			; READ A/D BARO VAL With A/D
			;
C58A:          LDX     #$3000				; INDEX CPU REG'S
											;
C58D:          SEI     						; SECURE INTERUPTS

			;
			; SET UP A/D M,ODE & CH
			;
C58E:          LDAA    #$05					;
C590:          JSR     LF275				;

C593:          LDAA    #$01					;
C595:          JSR     LF25F				; A/D CNT'L MODE
C598:          CLI     						; CLR & RESTORE INTERUPTS 

C599:          LDAA    $34,X				; GET A/D VAL FM ADR4
C59B:          STAA    L02F3 				; BARO A/D
C59E:          ADDA    #11					;
C5A0:          BCC     LC609				; BR IF NO OVERFLOW
											;
C5A2:          LDAA    #255					; MAX VALUE
C5A4:          BRA     LC609
 			;----------------------------------------------


			;---------------------------------------------
			;
			;
			;---------------------------------------------
C5A6:  LC5A6   CLRA    
C5A7:          BRSET   L0044,#$10,LC5FF		; BR IF b4, 
											;
C5AB:          LDAB    L01C6
C5AE:          CMPB    L02F4				; BARO
C5B1:          BHI     LC5FF

C5B3:          BRSET   L006F,#$40,LC619		; BR IF b6, 

C5B7:          LDAA    L006F
C5B9:          ANDA    #$0C					; 0000 1100
C5BB:          BEQ     LC5C2

C5BD:          CMPB    L4E68				; 90.8 Kpa DEFAULT MAP IF NOT RUNNING
C5C0:          BCS     LC619

C5C2:  LC5C2   LDAA    L0061				; RPM/25
C5C4:          CMPA    L4154				; 5600 RPM MAX FOR BARO UP-DATE
C5C7:          BHI     LC614

C5C9:          CMPA    L4155
C5CC:          BCS     LC614

C5CE:          LDAA    L0006				; COOL VALUE
C5D0:          CMPA    L4159
C5D3:          BCS     LC614
C5D5:          LDAA    L01D9				; %TPS
C5D8:          CMPA    L4156
C5DB:          BLS     LC614

C5DD:          SUBA    L01DE
C5E0:          BCC     LC5E3
C5E2:          NEGA    
C5E3:  LC5E3   CMPA    L4157				; 3.1% DIFF TPS MIN FOR BARO UP-DATE
C5E6:          BHI     LC614

C5E8:          LDAA    L0062				; ENGINE RPM/25
C5EA:          LDAB    #171
C5EC:          MUL     
C5ED:          ADCA    #$00
C5EF:          CMPA    #128
C5F1:          BLS     LC5F5

C5F3:          LDAA    #128
C5F5:  LC5F5   LDAB    L01D9				; %TPS
C5F8:          LSRB 


    	;----------------------------------------------
    	; BARO CORR FACTOR vs RPM & TPS
    	;
    	; TERM ADDED TO A/D MAP TO MAKE PSEUDO BARO
    	;
    	; TBL = Kpa * 2.71
    	;----------------------------------------------
C5F9:          LDX     #$4558				; BARO CORR FACTOR
C5FC:          JSR     LF4DE				; 3d LK UP

C5FF:  LC5FF   ADDA    L01C6
C602:          BCC     LC606
											;
C604:          LDAA    #255					; MAX VALUE
C606:  LC606   STAA    L02F3 				; ADBARO, BARO A/D

			;
			; FILTER BARO
			;
C609:  LC609   LDAB    L4158				; 50% BARO A/D FILT COEF
C60C:          LDX     L02F4				; BARO
C60F:          JSR     LF459				; LAG FILT

C612:          BRA     LC620



C614:  LC614   LDAA    L02F4				; BARO
C617:          BNE     LC623
											;
C619:  LC619   LDAA    L4E68				; 90.8 Kpa DEFAULT MAP IF NOT RUNNING
C61C:          CLRB    
C61D:          STAA    L02F3 				; A/D BARO, BARO A/D
C620:  LC620   STD     L02F4				; BARO

C623:  LC623   TAB     
C624:          LDAA    #$8F
C626:          SUBB    #$0D
C628:          BCS     LC62F
											;
C62A:          LDAA    #$0097
C62C:          MUL     
C62D:          ADCA    #$00
C62F:  LC62F   STAA    L01CC				; BARO VALUE (Kpa)
C632:          LDAB    #$60

    		;--------------------------------------------------
    		; DIFF TPS ACEL ENRICH MULT FACTOR vs BARO
    		;
    		; TBL = FACTOR * 128 
    		;--------------------------------------------------
C634:          LDX     #$4B60				; DIFF TPS ACEL ENRICH MULT 
C637:          JSR     LF4BD
C63A:          STAA    L01E4



    	;---------------------------------------------
    	; WOT DIFF TPS vs BARO
    	;
    	; TBL = %TPS * 2.56
    	;---------------------------------------------
C63D:          LDAA    L01CC				; BARO VALUE (Kpa)
C640:          LDAB    #96
C642:          LDX     #$4C89				; WOT DIFF TPS TBL
C645:          JSR     LF4BD
C648:          STAA    L01E3

        ;---------------------------------
        ; PWR ENRICH QUALIFICATION VS BARO
        ;
        ; TBL = RPM/25
        ;---------------------------------
C64B:          LDAA    L01CC				; BARO VALUE (Kpa)
C64E:          LDAB    #96
C650:          LDX     #$4975				; PWR ENRICH QUALIFICATION
C653:          JSR     LF4BD
C656:          STAA    L01CD

C659:          LDAA    L01CC				; BARO VALUE (Kpa)
C65C:          LDAB    #96
C65E:          LDX     #$49D1
C661:          JSR     LF4BD
C664:          STAA    L01CE

C667:          RTS     
 			;------------------------------------------


C668:  LC668   LDX     #$5B00				; INDEX ERR MASKS

                    ;---------------------------------
				    ; 0000 0001, SPD SENSOR SOURCE
                    ;
                    ; b7    not used
                    ; b6    not used
                    ; b5 1 = force 2nd Gr if in D2 and not manual
                    ; b4 0 = Output spd fm Dig Ratio Adaptor
                    ;   
                    ; b3    not used
                    ; b2 1 = BARO & MAP SENSOR USED, 0 = MAP ONLY
                    ; b1    not used
                    ; b0 1 = allow tps hist buffer every 25 Msec 
					;
                    ;------------------------------------
C66B:          LDY     #$5D02				; SPEED SOURCE

C66F:          BRCLR   $30,X,#$04,LC679
C673:          BRCLR   L001B,#$04,LC679
C677:          BRA     LC686
 ;
C679:  LC679   BRCLR   $2D,X,#$20,LC68A				  
C67D:          BRCLR   L0018,#$20,LC68A
C681:          BRSET   0,Y,#$04,LC68A
C686:  LC686   LDD     $6F,X
C688:          BRA     LC6B8
 ;
C68A:  LC68A   BRCLR   $30,X,#$02,LC694
C68E:          BRCLR   L001B,#$02,LC694
C692:          BRA     LC6A1
 ;
C694:  LC694   BRCLR   $2D,X,#$10,LC6A5				  
C698:          BRCLR   L0018,#$10,LC6A5
C69C:          BRSET   0,Y,#$04,LC6A5
C6A1:  LC6A1   LDD     $73,X

C6A3:          BRA     LC6B8


C6A5:  LC6A5   LDAA    L02F3 				; ADBARO, BARO A/D
C6A8:          LDAB    L5D07
C6AB:          MUL     
C6AC:          ADDD    L5D08

C6AF:          LDX     L00AC
C6B1:          LDY     #$5D0A
C6B5:          JSR     LF436				; LAG FILTER SUB ROUTINE, XMSIH

C6B8:  LC6B8   STD     L00AC

C6BA:          RTS     


 ; ------------------------------------------
C6BB:  LC6BB   LDX     #$6AB4
C6BE:          LDD     #$0000
C6C1:          STD     L008C
C6C3:          BRCLR   0,X,#$08,LC6D2
C6C7:          BRCLR   L00A2,#$03,LC6D2
C6CB:          BRSET   L0087,#$02,LC6D2
C6CF:          BSET    L008C,#$01
C6D2:  LC6D2   BRCLR   $0001,X,#$20,LC6DD
C6D6:          BRCLR   L00A2,#$04,LC6DD
C6DA:          BSET    L008D,#$10
C6DD:  LC6DD   BRCLR   $0001,X,#$40,LC6E8
C6E1:          BRCLR   L00A2,#$08,LC6E8
C6E5:          BSET    L008D,#$20
C6E8:  LC6E8   BRCLR   0,X,#$20,LC6FB
C6EC:          LDAA    $0004,X
C6EE:          BRCLR   L008B,#$01,LC6F4
C6F2:          LDAA    $0005,X
C6F4:  LC6F4   CMPA    L00B5
C6F6:          BLS     LC6FB
C6F8:          BSET    L008C,#$02
C6FB:  LC6FB   BRCLR   0,X,#$40,LC70E
C6FF:          LDAA    $0002,X
C701:          BRCLR   L008B,#$01,LC707
C705:          LDAA    $0003,X
C707:  LC707   CMPA    L00A9
C709:          BLS     LC70E
C70B:          BSET    L008C,#$04
C70E:  LC70E   BRCLR   L009C,#$01,LC715
C712:          BSET    L008C,#$08
C715:  LC715   BRCLR   0,X,#$02,LC728
C719:          LDAA    L018D
C71C:          BEQ     LC728
C71E:          BRCLR   L0089,#$40,LC725
C722:          BSET    L008B,#$20
C725:  LC725   BSET    L008C,#$10
C728:  LC728   BRCLR   0,X,#$01,LC734
C72C:          LDAA    L018C
C72F:          BEQ     LC734
C731:          BSET    L008C,#$20
C734:  LC734   BRCLR   $0001,X,#$10,LC740
C738:          LDAA    L0124
C73B:          BEQ     LC740
C73D:          BSET    L008D,#$01
C740:  LC740   BRCLR   $0001,X,#$02,LC760
C744:          BRSET   L0087,#$02,LC760
C748:          BRCLR   L009C,#$02,LC760
C74C:          LDAB    L00D9  				; CURRENT GEAR
C74E:          BEQ     LC760
C750:          ABX     
C751:          LDAA    $07,X
C753:          BRSET   L008B,#$01,LC759
C757:          LDAA    $000A,X
C759:  LC759   CMPA    L00D7
C75B:          BLS     LC760
C75D:          BSET    L008C,#$40
C760:  LC760   LDX     #$6AB4
C763:          BRCLR   $0001,X,#$01,LC76E
C767:          BRCLR   L0089,#$80,LC76E
C76B:          BSET    L008C,#$80
C76E:  LC76E   BRCLR   $0001,X,#$04,LC77C
C772:          BRCLR   L008B,#$08,LC77C
C776:          BCLR    L008B,#$08
C779:          BSET    L008D,#$02
       LC77B
C77C:  LC77C   BRCLR   $0001,X,#$04,LC7AD
C780:          JSR     LE674
C783:          BRCLR   L0098,#$40,LC7A0
C787:          LDX     #$6AC2
C78A:          BRSET   L0089,#$04,LC78F
C78E:          INX     
C78F:  LC78F   LDAA    L00B5
C791:          CMPA    0,X
C793:          BHI     LC79D
C795:          BCLR    L0089,#$04
C798:          BSET    L008D,#$04
C79B:          BRA     LC7A0
 ;
C79D:  LC79D   BSET    L0089,#$04
C7A0:  LC7A0   BRCLR   L0099,#$04,LC7AD
C7A4:          LDAA    L00D9
C7A6:          CMPA    #$0003
C7A8:          BEQ     LC7AD
C7AA:          BSET    L008D,#$08
C7AD:  LC7AD   LDX     #$6D5E
C7B0:          LDAA    L00E2   				; CURRENT TQ SIG PRESSURE
C7B2:          ASLA    
C7B3:          BCC     LC7B7
C7B5:          LDAA    #$FF
C7B7:  LC7B7   JSR     LF4C1				; 2d LK UP
C7BA:          CLRB    
C7BB:          STD     L0129
C7BE:          LDX     #$6D6F
C7C1:          LDAA    L00E2  				; CURRENT TQ SIG PRESSURE
C7C3:          ASLA    
C7C4:          BCC     LC7C8
C7C6:          LDAA    #$FF
C7C8:  LC7C8   JSR     LF4C1				; 2d LK UP
C7CB:          CLRB    
C7CC:          STD     L012B
C7CF:          LDAA    L010A
C7D2:          BEQ     LC7FE
C7D4:          CMPA    #$00C8
C7D6:          BLS     LC7E2
C7D8:          BRCLR   L008A,#$10,LC7DF
C7DC:          BCLR    L008A,#$14
C7DF:  LC7DF   JMP     LC8AA
 ;
C7E2:  LC7E2   CMPA    #$0064
C7E4:          BLS     LC7F0
C7E6:          BRCLR   L008A,#$10,LC7ED
C7EA:          BCLR    L008A,#$14
C7ED:  LC7ED   JMP     LC8A2
 ;
C7F0:  LC7F0   LDAB    #$00A3
C7F2:          MUL     
C7F3:          ASLD    
C7F4:          ASLD    
C7F5:          STD     L0126
C7F8:          BSET    L008A,#$14
C7FB:          JMP     LC8B0
 ;
C7FE:  LC7FE   BRCLR   L0099,#$08,LC80A
C802:          CLRA    
C803:          CLRB    
C804:          STD     L0126
C807:          JMP     LC89D
 ;
C80A:  LC80A   BRCLR   L008A,#$10,LC811
C80E:          BCLR    L008A,#$14
C811:  LC811   BRSET   L008C,#$08,LC826
C815:          BRSET   L008C,#$20,LC826
C819:          BRCLR   L0099,#$04,LC826
C81D:          LDAA    L00D9  				; CURRENT GEAR
C81F:          CMPA    #$0003
C821:          BNE     LC826
C823:          JMP     LC8A2
 ;
C826:  LC826   LDD     L008C
C828:          BNE     LC89D
C82A:          LDAA    L018E
C82D:          BNE     LC8AA


			;------------------------------		
			; 5B2B  1111 0001, MASK XMISSH ERR WD 1
			;
			; b7 1 = ERR 13, o2 FAIL
			; b6 1 = ERR 14, HIGH COOLANT TEMP
			; b5 1 = ERR 15, LOW COOLANT TEMP
			; b4 1 = ERR 16, 2002 PPM Vss FAIL
			;
			; b3 1 = ERR 17
			; b2 1 = ERR 18
			; b1 1 = ERR 19
			; b0 1 = ERR 21,	HIGH TPS
			;------------------------------		
C82F:          LDX     #$5B2B
C832:          BRCLR   L0018,#$30,LC83A
C836:          BRSET   $0002,X,#$30,LC849
C83A:  LC83A   LDAB    L6AEC
C83D:          BRSET   L0089,#$40,LC844

C841:          LDAB    L6AED
C844:  LC844   CMPB    L01C0				; GET CURRENT MAP VALUE
C847:          BHI     LC8AA

C849:  LC849   LDX     #$C2D6
C84C:          BRCLR   L0089,#$40,LC853
C850:          LDAB    #$0044
C852:          ABX     
C853:  LC853   PSHX    
C854:          BRCLR   L009C,#$10,LC86D
C858:          LDAB    #$0022
C85A:          ABX     
C85B:          LDAB    L00D9   				; CURRENT GEAR
C85D:          LDAA    L007F
C85F:          JSR     LD8FE
C862:          BCS     LC86D
C864:          PULY    
C866:          LDAA    0,X
C868:          STAA    L0128
C86B:          BRA     LC881
 ;
C86D:  LC86D   PULX    
C86E:          LDAA    L007F
C870:          LDAB    L00D9   				; CURRENT GEAR
C872:          JSR     LD8FE
C875:          BCS     LC89D
C877:          LDAA    0,X
C879:          STAA    L0128


C87C:          LDAA    L00B2
C87E:          JSR     LF4C1				; 2d LK UP
C881:  LC881   LDX     #$C3E6
C884:          BRCLR   L009C,#$10,LC88B
C888:          LDAB    #$0012
C88A:          ABX     
C88B:  LC88B   CLRB    
C88C:          JSR     LD92E
C88F:          CMPA    L0128
C892:          BCC     LC897
C894:          LDAA    L0128
C897:  LC897   CMPA    L00D7
C899:          BHI     LC8AA
C89B:          BRA     LC8A2
 ;
C89D:  LC89D   BCLR    L008B,#$06
C8A0:          BRA     LC8B0
 ;
C8A2:  LC8A2   BCLR    L008B,#$02
C8A5:          BSET    L008B,#$04
C8A8:          BRA     LC8B0
 ;
C8AA:  LC8AA   BSET    L008B,#$02
C8AD:          BCLR    L008B,#$04
C8B0:  LC8B0   RTS     
 ; ------------------------------------------
C8B1:  LC8B1   JSR     LEE5F
C8B4:          JSR     LEE60
C8B7:          JSR     LED3F
C8BA:          JSR     LED80
C8BD:          JSR     LEDC1
C8C0:          JSR     LEA40
C8C3:          JSR     LEA7C
C8C6:          JSR     LEC79
C8C9:          JSR     LEB17
C8CC:          JSR     LEB18
C8CF:          JSR     LEB19
C8D2:          JSR     LEB4D

C8D5:          RTS     
 	;------------------------------------------


 	;------------------------------------------
	; LOOK UP A/D vs COOLANT TEMPERATURE
	;
	; TYPE $31 PCM
	;------------------------------------------
C8D6:  LC8D6   LDAA    L00A5				; A/D COOL VALUE
C8D8:          LDX     #$FC45				; INDEX A/D vs COOL TBL
C8DB:          BRSET   L0043,#$80,LC8E6		; BR IF b7, 
											;
C8DF:          BRSET   L004E,#$02,LC8E6		; BR IF b1, 
											;
C8E3:          LDX     #$FD45				; INDEX A/D vs COOL TBL
C8E6:  LC8E6   TAB     						; A/D VAL TO B Reg
C8E7:          ABX     						;
C8E8:          LDAA    0,X					; GET COOL VALUE FM TBL
C8EA:          CMPA    #120					; 50c ?
C8EC:          BHI     LC8F7				;
											;
C8EE:          CMPA    #106					; 39.5c ?
C8F0:          BHI     LC8FA				;
											;
C8F2:          BSET    L004E,#$02			; SET b1

C8F5:          BRA     LC8FA



C8F7:  LC8F7   BCLR    L004E,#$02			; CLR b1
C8FA:  LC8FA   STAA    L00B4

C8FC:          RTS     
 	;------------------------------------------


 	;------------------------------------------
C8FD:  LC8FD   LDX     #$5B00				; INDEX ERR MASKS


C900:          LDAA    L00B4
C902:          BRCLR   $30,X,#$40,LC90A		;
											;
C906:          BRSET   L001B,#$40,LC912		;
											;
C90A:  LC90A   BRCLR   $30,X,#$20,LC914		;
											;
C90E:          BRCLR   L001B,#$20,LC914		;
											;
C912:  LC912   LDAA    $6A,X
C914:  LC914   LDAB    #$80
C916:          LDX     L00B5
C918:          LDY     #$5D0B
C91C:          JSR     LF436				; LAG FILTER SUB ROUTINE, XMSIH
C91F:          STD     L00B5

C921:          LDAB    L6ABB
C924:          BRSET   L0087,#$02,LC92B
C928:          LDAB    L6ABA
C92B:  LC92B   BCLR    L0087,#$02
C92E:          CBA     
C92F:          BCS     LC934
C931:          BSET    L0087,#$02
C934:  LC934   LDAB    L00A9
C937:          CMPB    L5D34
C93A:          BCC     LC93F
C93C:          BSET    L0087,#$01
C93F:  LC93F   CMPB    L5D35
C942:          BLS     LC947
											;
C944:          BCLR    L0087,#$01
C947:  LC947   CLRA    
C948:          CMPB    L5D36  				; IF COOLANT L.T. 10c SET COLD SHIFT
C94B:          BHI     LC950
C94D:          COMA    
C94E:          BRA     LC967
 ;
C950:  LC950   CMPB    L5D37
C953:          BCC     LC967
C955:          LDAA    L5D37
C958:          SUBA    L5D36				; IF COOLANT L.T. 10c SET COLD SHIFT
C95B:          CLRB    
C95C:          XGDX    
C95D:          LDAA    L00A9
C960:          SUBA    L5D36				; IF COOLANT L.T. 10c SET COLD SHIFT
C963:          CLRB    
C964:          FDIV    
C965:          XGDX    
C966:          COMA    
C967:  LC967   STAA    L00AB

C969:          RTS     
		;------------------------------------------
		
		 
 
 		;------------------------------------------
		; DO COOL SUBROUTINE
		;
		;
		;------------------------------------------
C96A:  LC96A   LDAA    L082D
											;
C96D:          LDX     #$FC45				; INDEX A/D vs COOL TBL
C970:          BRSET   L0043,#$80,LC97B
C974:          BRSET   L004E,#$01,LC97B
C978:          LDX     #$FD45
C97B:  LC97B   TAB     
C97C:          ABX     
C97D:          LDAA    0,X
C97F:          STAA    L00A8
C981:          CMPA    #$0078
C983:          BHI     LC98E
C985:          CMPA    #$006A
C987:          BHI     LC991
C989:          BSET    L004E,#$01
C98C:          BRA     LC991
 ;
C98E:  LC98E   BCLR    L004E,#$01
C991:  LC991   BRCLR   L0016,#$60,LC9A6		; BR IF NOT b6 & b5, ERR  ..
											;
C995:          LDAA    L5B1A

C998:          LDX     L00FD				; RUN TIMER
C99A:          CPX     L5B18
C99D:          BHI     LC9A2

C99F:          LDAA    L5B1B
C9A2:  LC9A2   STAA    L0006				; COOL VALUE
C9A4:          BRA     LC9AA
 ;
C9A6:  LC9A6   LDAA    L00A8
C9A8:          STAA    L0006				; COOL VALUE

C9AA:  LC9AA   BCLR    L0043,#$80

			;
			; MAKE UP RANGE LIMITTED COOL
			;
C9AD:          LDAA    L0006				; COOL VALUE
C9AF:          SUBA    #16					; -28c
C9B1:          BCC     LC9B6				; BR IF COOL GT -28c
											;
C9B3:          CLRA    
C9B4:          BRA     LC9BC
 

C9B6:  LC9B6   CMPA    #192					; 104c
C9B8:          BLS     LC9BC				; BR IF COOL LT 104c
C9BA:          LDAA    #192					; 104c
C9BC:  LC9BC   STAA    L0283				; SAVE RANGE LMT'ED COOL (-28 - 104c)

C9BF:          RTS     
			;------------------------------------------

 			;------------------------------------------
			;  CK COOL FOR ERR'S
			; 
			;  ERR MASK MASK:
			;  5B2B, b6 1 = ERR 14, HIGH COOLANT TEMP
			;		 b5 1 = ERR 15, LOW  COOLANT TEMP
			;
			;------------------------------------------
C9C0:  LC9C0   LDX     #$5B00				; INDEX ERR MASKS
											;
C9C3:          LDAA    L00A8				; 
C9C5:          BRCLR   $2B,X,#$40,LC9CD		; (5B2B),  BR IF NOT b6, (HIGH COOL)

											;
C9C9:          BRSET   L0016,#$40,LC9D5		; BR IF b6, ERR  ..

C9CD:  LC9CD   BRCLR   $2B,X,#$20,LC9D7		; (5B2B), BR IF NOT b5, 
											;
C9D1:          BRCLR   L0016,#$20,LC9D7		; BR IF NOT b5
											;
C9D5:  LC9D5   LDAA    $17,X				; (5B17),  90 DEG C DEFAULT COOLANT TEMP 

			;
			; FILTER ROUTINE
			;
C9D7:  LC9D7   LDAB    #128
C9D9:          LDX     L00A9
C9DB:          LDY     #$5D0C				; 200 Msec, COOL FILT COEF
C9DF:          JSR     LF436				; LAG FILTER SUB ROUTINE, XMSIH
C9E2:          STD     L00A9 				;

C9E4:          CMPA    L5D04				; 128c COOL
C9E7:          BLS     LC9EE				;
											;
C9E9:          BSET    L0087,#$04

C9EC:          BRA     LC9F6


C9EE:  LC9EE   CMPA    L5D05				; 255d
C9F1:          BCC     LC9F6				;
											;
C9F3:          BCLR    L0087,#$04

C9F6:  LC9F6   RTS     
 			;------------------------------------------


    		;--------------------------------------------------
    		; ACCEL ENRICH DIFF TPS COEF vs COOL
    		;
    		; TABLE = %COEF * 2.56
    		;--------------------------------------------------
C9F7:  LC9F7   LDAA    L0283				; RANGE LMT'ED COOL (-28 - 104c 
C9FA:          LDX     #$4B64				; ACCEL ENRICH DIFF TPS COEF TBL
C9FD:          JSR     LF4C1				; 2d LK UP
											;
CA00:          STAA    L01E5				; ACCEL ENRICH DIFF TPS COEF 


CA03:          LDAA    L0283				; RANGE LMT'ED COOL (-28 - 104c
CA06:          LSRA    						; n/2

    		;--------------------------------------------------
    		; DECEL FUEL CUT OFF RPM THRESH vs COOL/2
    		;
    		;   RPM MUST BE  G.T. THESE VAL'S TO STAY IN COUT OFF
    		;
    		; TBL = RPM/25
    		;--------------------------------------------------
CA07:          LDX     #$4C8D				; DECEL FUEL CUT OFF RPM THRESH TBL
CA0A:          JSR     LF4C1				; 2d LK UP
											;
CA0D:          STAA    L0243				; DECEL FUEL CUT OFF RPM THRESH 

    		;--------------------------------------------------
    		; OPN LOOP IDLE AFR NUMERICAL LIMIT (MIN LEAN)
    		;
    		;
    		; TABLE = AFR * 10
    		;--------------------------------------------------
CA10:          LDX     #$4BAD				; OPN LOOP IDLE AFR NUMERICAL LIMIT	TBL.
											;
CA13:          LDAA    L0006				; COOL VALUE
CA15:          CMPA    #192					; LIMIT TEMP FOR LK UP (104c)
CA17:          BLS     LCA1B				;
											;
CA19:          LDAA    #192					; USE 104c COOL
CA1B:  LCA1B   JSR     LF4C1				; 2d LK UP
											;
CA1E:          BRSET   L003F,#$40,LCA30		; BR IF b6, 
											;
CA22:          LDAB    L0006				; COOL VALUE
CA24:          CMPB    L48E3  				; -10c COOL, OPEN LP RICH IDLE THRESH
CA27:          BHI     LCA30				; BR IF COOL GT THRESH 
											;
CA29:          SUBA    L48E8				; 0:1 AFR RATIO BIAS FOR OPN LP IDLE
CA2C:          BCC     LCA30				; BR IF NO UNDER FLOW 
											;
CA2E:          LDAA    #$00					; FORCE A ZERO
CA30:  LCA30   STAA    L0272				; AFR

    		;-----------------------------------------
    		; MAP FILTER COEF vs COOLANT
    		;
    		; TBL = COEF * 256
    		;-----------------------------------------
CA33:          LDX     #$4B3C				;  MAP FILTER COEF vs COOLANT
CA36:          LDAA    L0283				; RANGE LMT'ED COOL (-28 - 104c
CA39:          JSR     LF4C1				; 2d LK UP

CA3C:          STAA    L01CB				;

    		;-----------------------------------------
    		; DESIRED EGR GAIN FACTOR vs COOL
    		;
    		;   FOR BP EGR WITH 0   TO DISABLE  EGR
    		;           OR WITH 128 TO ENABLE   EGR
    		;-----------------------------------------
CA3F:          LDX     #$475F				; DESIRED EGR GAIN FACTOR
CA42:          LDAA    L0006				; COOL VALUE
CA44:          LDAB    #80					;
CA46:          JSR     LF49A				;
CA49:          STAA    L01BB				;

CA4C:          LDAA    L0006				; COOL VALUE
CA4E:          SUBA    #153					; 
CA50:          BCC     LCA54				; BR IF NO UNDERFLOW 
											;
CA52:          LDAA    #$00
CA54:  LCA54   ASLA    
CA55:          ASLA    
CA56:          BCC     LCA5A				; BR IF NO OVERFLOW 
											;
CA58:          LDAA    #$FF
CA5A:  LCA5A   LDAB    #$99
CA5C:          MUL     
CA5D:          ADCA    #$00

            ;---------------------------------------------
        	; DEGREES BURST KNK RETARD vs COOLANT
        	;
        	; TBL = SPK RETARD * (256/90)
            ;---------------------------------------------- 
CA5F:          LDX     #$46E3
CA62:          JSR     LF499
CA65:          STAA    L0842
CA68:          JMP     LCB14




CA6B:  LCA6B   CLRA    

		;--------------------------------------------
		; AFR MD BYTE 1 0000 0100 
		;
		; b7 1 = DE-LATCH
		; b6 1 = MAT SENSOR
		; b5 1 = 180 DEG OFFSET 
		; b4 1 = ASDF CRANK
		;
		; b3 1 = ACCEL ENRICH LMT OPTION  
		; b2 1 = SYNC FUEL AT IDLE (TBI)
		; b1 1 = AIR MANAGE 
		; b0 1 = CPI/PFI MODE
		;--------------------------------------------
CA6C:          LDX     #$400B				; AFR MD BYTE 1,  0000 0100
CA6F:          BRCLR   0,X,#$40,LCAB1		; BR IF NOT b6, (1 = MAT SENSOR)
											;
CA73:          LDAA    L022F				; LINEAR IAT VALUE
CA76:          CMPA    #192					; 104c
CA78:          BCS     LCA7E				; BR IF IAT < 192
											;
CA7A:          LDAA    #192					; 104c
CA7C:          BRA     LCA85
 


CA7E:  LCA7E   CMPA    #80					;
CA80:          BCC     LCA85				;
											;
CA82:          CLRA    						;
CA83:          BRA     LCAB1				 
    		;-----------------------------------------
 
 

    		;-----------------------------------------
    		; BASE MAT SPK ADV CORR vs VAC & MAT
			;
    		; TBL = SPK DEG + BAIS * 2.844
    		;-----------------------------------------
CA85:  LCA85   LDX     #$4439				; BASE MAT SPK ADV CORR
CA88:          LDAB    0,X					;
CA8A:          BEQ     LCA96				;
											;
CA8C:          LDAB    L0062				; ENGINE RPM/25
CA8E:          CMPB    #176
CA90:          BLS     LCA9F
											;
CA92:          LDAB    #176
CA94:          BRA     LCA9F
 


CA96:  LCA96   LDAB    L01C9				; Kpa VACUUM
CA99:          SUBB    #80
CA9B:          BCC     LCA9F
											;
CA9D:          LDAB    #$0000
CA9F:  LCA9F   INX     
CAA0:          JSR     LF4DE				; 3d LK UP
CAA3:          SUBA    L413F				; 0  DEG  BIAS FOR MAP  CORR SA
CAA6:          BMI     LCAAD
											;
CAA8:          BCLR    L0041,#$02
CAAB:          BRA     LCAB1



CAAD:  LCAAD   BSET    L0041,#$02			; SET b1, 
CAB0:          NEGA    
CAB1:  LCAB1   STAA    L01FA

CAB4:          CLRA    						;
											;
CAB5:          LDAB    L0006				; COOL VALUE
CAB7:          CMPB    L45DA				; 35 c MIN COOL FOR SPK RETARD
CABA:          BLS     LCAD2				; BR IF COOL LT THRESH  
											;

			;
			; CURRENT ERR WD #4
			;
CABC:          BRSET   L0019,#$10,LCAD2		; BR IF b4, KNOCK SENSOR ERR 
											;
            ;    
			; AFR MD WORD 0,	
            ; 	b5 1 = PWR ENR IS ACTIVE   
            ;
CAC0:          BRCLR   L003D,#$20,LCAD2		; BR IF NOT b5, PWR ENR IS ACTIVE 
											;

        ;----------------------------------------------
    	; LK UP WOT SPK ADV CORR VS RPM
    	;
    	; TBL = (256/90) * SPK ADV DEG
        ;---------------------------------------------
CAC4:          LDX     #$44BF				;
CAC7:          LDAA    L0062				; ENGINE RPM/25
CAC9:          JSR     LF4C1				; 2d LK UP

CACC:          LDAB    L0278				; PWR ENR AFR SLEW MULT
CACF:          MUL     
CAD0:          ADCA    #$00
CAD2:  LCAD2   STAA    L01FC				; SPARK ADDER

    	;----------------------------------------------
    	; LOW OCTAINE SPK RETARD MULT Vs. RPM 
    	;
    	; APPLIED TO BASE SPARK RETARD
    	; 
		; 2d LK UP vs RPM/25
		;
		: TBL = MULT * 256
		;----------------------------------------------
CAD5:          LDAA    L0062				; ENGINE RPM/25
CAD7:          LSRA    						; RPM/2
CAD8:          LDX     #$45BE				; LOW OCTAINE SPK RETARD MULT
CADB:          JSR     LF4C1				; 2d LK UP
											;
CADE:          STAA    L0841				; LOW OCTAINE SPK RETARD MULT

        ;---------------------------------------------
    	; KNOCK RECOVERY RATE vs RPM
    	;
    	;  TBL =  44.4444  * (Deg/Msec)
        ;---------------------------------------------
CAE1:          LDX     #$4594
CAE4:          LDAA    L0062				; ENGINE RPM/25
CAE6:          JSR     LF4C1				; 2d LK UP
CAE9:          STAA    L0843				; KNOCK RECOVERY RATE vs RPM

CAEC:          BRCLR   L003D,#$20,LCAFD		; BR IF NOT b5, PWR ENR IS ACTIVE 

            ;---------------------------------------------
        	; MAX KNOCK RETARD IN WOT vs RPM
        	; 8 LINE TABLE
        	;
        	; TBL = SPK ADV * (256/45)
            ;---------------------------------------------
CAF0:          LDX     #$4585
CAF3:          LDAA    L0062				; ENGINE RPM/25
CAF5:          LSRA    
CAF6:          LDAB    #$10
CAF8:          JSR     LF4BD

CAFB:          BRA     LCB11


CAFD:  LCAFD   LDAA    #255

CAFF:          LDAB    L006F
CB01:          BITB    #$48					: b6 & b3
CB03:          BNE     LCB08
											;
CB05:          LDAA    L01C9				; Kpa VACUUM
CB08:  LCB08   LSRA    
CB09:          LDAB    #$20

            ;---------------------------------------------
        	; MAX KNOCK RETARD NOT IN WOT vs VAC
        	; 7 LINE TABLE
        	;
        	; TBL = SPK ADV 8 (256/45)
            ;---------------------------------------------
CB0B:          LDX     #$458D				; INDEX KNOCK RETARD NOT IN WOT TBL
CB0E:          JSR     LF4BD

CB11:  LCB11   STAA    L0844				; MAX KNOCK RETARD NOT IN WOT vs VAC

CB14:  LCB14   RTS     
 		;---------------------------------------------



CB15:  LCB15   SEI     
CB16:          BCLR    L0050,#$18
CB19:          LDAA    L082F
CB1C:          CMPA    #$28
CB1E:          BCS     LCB2D
												;
CB20:          CMPA    #$64
CB22:          BCC     LCB30
												;
CB24:          BRCLR   L0044,#$01,LCB30			; SET b0, FACTORY TEST ENTERED
												;
CB28:          BSET    L0050,#$08

CB2B:          BRA     LCB30
 

CB2D:  LCB2D   BSET    L0050,#$10
CB30:  LCB30   CLI     

			;----------------------------------------------
			; AFR MD BYTE 5,	 0001 0000, (DIG I/O)
			;
			; b7 1 = MAN, (0 = TCC)
			; b6 1 = TCC (Non Elect xmish)
			; b5 1 = Not Used 
			; b4 1 = CONV OVER HEAT PROTECTION
			;
			; b3 1 = BURST KNOCK RETARD
			; b2 1 = A/C CLUTCH CNT'L, 0 = CPI TUNE
			; b1 1 = Not Used
			; b0 1 = 1 DO RPM/MPH LMT, (GOV'R OPT)
			;
			;----------------------------------------------
CB31:          LDX     #$400F
CB34:          BRSET   0,X,#$04,LCB3B
CB38:          JMP     LCC34
 ;
CB3B:  LCB3B   LDD     L00FD				; RUN TIMER
CB3D:          CPD     L4022
CB41:          BCS     LCB47
											;
			;
			; I/O PORT C
			;
CB43:          BRSET   L004D,#$01,LCB55		; BR IF b0, A/C REQUEST ON  
											;
CB47:  LCB47   LDAA    L4012
CB4A:          STAA    L0830
CB4D:  LCB4D   LDAA    L4013
CB50:          STAA    L0831
CB53:          BRA     LCB86
 ;
CB55:  LCB55   LDAA    L0830
CB58:          BEQ     LCB5F
CB5A:          DEC     L0830
CB5D:          BRA     LCB86
 ;
CB5F:  LCB5F   LDAA    L4011

CB62:          BRSET   L0041,#$10,LCB69		; BR IF b4, A/C PRESSURE SW, (A/C ON)
											;
CB66:          LDAA    L4010
CB69:  LCB69   CMPA    L01D9				; %TPS
CB6C:          BCS     LCB7A
CB6E:          LDX     #$0000
       LCB70
CB71:          STX     L0834
CB74:  LCB74   BRCLR   L0036,#$10,LCBBA
CB78:          BRA     LCBB5
 ;
CB7A:  LCB7A   LDX     L0834
CB7D:          CPX     L4020
CB80:          BHI     LCB74
CB82:          INX     
CB83:          STX     L0834

CB86:  LCB86   BRCLR   L004F,#$80,LCBB2		; BR IF NOT b7, ENGINE RUNNING
											;
CB8A:          LDAA    L0062				; ENGINE RPM/25
CB8C:          CMPA    L4019
CB8F:          BLS     LCB9F
CB91:          BSET    L0052,#$10
CB94:          CLR     L0833
CB97:          LDAA    L4013
CB9A:          STAA    L0831
CB9D:          BRA     LCBB2
 ;
CB9F:  LCB9F   LDAA    L0833
CBA2:          CMPA    L4016
CBA5:          BCS     LCBAC
CBA7:          BCLR    L0052,#$10
CBAA:          BRA     LCBB2
 ;
CBAC:  LCBAC   INCA    
CBAD:          BEQ     LCBB2
CBAF:          STAA    L0833

CBB2:  LCBB2   BCLR    L0052,#$20
CBB5:  LCBB5   BCLR    L0041,#$10
CBB8:          BRA     LCC34
 ;
CBBA:  LCBBA   LDAA    L401B
CBBD:          BRSET   L0041,#$10,LCBC4
CBC1:          LDAA    L401A
CBC4:  LCBC4   CMPA    L0006				; COOL VALUE
CBC6:          BCS     LCB4D
CBC8:          LDAA    L401C
CBCB:          BRSET   L0041,#$10,LCBD2
CBCF:          LDAA    L401D
CBD2:  LCBD2   BRSET   L0016,#$10,LCBFC		; BR IF b4, ERR  ..

CBD6:          CMPA    L0284				; MPH/1
CBD9:          BLS     LCBFC
CBDB:          LDAA    L401E

CBDE:          BRCLR   L0041,#$10,LCBEB
CBE2:          LDAA    L401F
CBE5:          LDAB    L4014
CBE8:          STAB    L0836
CBEB:  LCBEB   CMPA    L01D9				; %TPS
CBEE:          BCC     LCBFC
CBF0:          LDAA    L0836
CBF3:          BEQ     LCBFC
CBF5:          DECA    
CBF6:          STAA    L0836
CBF9:          JMP     LCB4D
 ;
CBFC:  LCBFC   LDAA    L4017
CBFF:          BRSET   L0041,#$10,LCC06
CC03:          LDAA    L4018
CC06:  LCC06   CMPA    L0062				; ENGINE RPM/25
CC08:          BCS     LCC0F
CC0A:          CLR     L0832
CC0D:          BRA     LCC1D
 ;
CC0F:  LCC0F   LDAA    L0832
CC12:          CMPA    L4015
CC15:          BCC     LCC21
CC17:          INCA    
CC18:          BEQ     LCC1D
CC1A:          STAA    L0832
CC1D:  LCC1D   BRCLR   L0052,#$10,LCC24
CC21:  LCC21   JMP     LCB86
 ;
CC24:  LCC24   BSET    L0052,#$20
CC27:          LDAA    L0831
CC2A:          BEQ     LCC31
CC2C:          DEC     L0831
CC2F:          BRA     LCC34
 ;
CC31:  LCC31   BSET    L0041,#$10

CC34:  LCC34   RTS     



 		;------------------------------------------
CC35:  LCC35   BRSET   L004F,#$80,LCC48		; BR IF b7, ENGINE RUNNING
											;
CC39:          LDAA    L0006				; COOL VALUE
CC3B:          STAA    L0282				; START UP COOL
CC3E:          CLRB    

CC3F:          LDAA    L48BE				; 450 Mv, INIT VALUE
CC42:          STD     L01D0				; o2 VOLTAGE, 1
CC45:          STAA    L01D5				; o2 VOLTS * 226 (A/D RESULT)

CC48:  LCC48   JMP     LCC4B
 ;
CC4B:  LCC4B   LDAA    L03B0
CC4E:          BEQ     LCC53
CC50:          BSET    L003A,#$10

CC53:  LCC53   LDX     #$3000				; INDEX CPU REG'S

CC56:          BSET    $22,X,#$A0			; TMSK1

CC59:          SEI     

CC5A:          LDD     L3FFC          		; I/O D PORT ..
CC5D:          ANDB    #$00FE


		;--------------------------------------------
		; AFR MD BYTE 1 0000 0100 
		;
		; b7 1 = DE-LATCH
		; b6 1 = MAT SENSOR
		; b5 1 = 180 DEG OFFSET 
		; b4 1 = ASDF CRANK
		;
		; b3 1 = ACCEL ENRICH LMT OPTION  
		; b2 1 = SYNC FUEL AT IDLE (TBI)
		; b1 1 = AIR MANAGE 
		; b0 1 = CPI/PFI MODE
		;--------------------------------------------
CC5F:          LDY     #$400B				; AFR MD BYTE 1, 0000 0100
CC63:          BRSET   0,Y,#$01,LCC6E		; BR IF b0, (1 = CPI/PFI MODE) 

CC68:          ORAB    #$0032
CC6A:          ORAA    #$00F9
CC6C:          BRA     LCC72
 ;
CC6E:  LCC6E   ORAB    #$12
CC70:          ORAA    #$79
CC72:  LCC72   JSR     LF3ED				; Very short delay
 (RTS)
CC75:          STD     L3FFC          		; I/O D PORT ..

CC78:          CLI     
CC79:          BCLR    L004C,#$80			; CLR b7
CC7C:  LCC7C   CLRA    
CC7D:          STAA    $0C,X
CC7F:          STAA    $0D,X
CC81:          STAA    $2C,X
CC83:          STAA    $0B,X
CC85:          STAA    $28,X
CC87:          STAA    $3E,X
CC89:          STAA    $5C,X
CC8B:          STAA    $03,X

CC8D:          LDAA    #$26
CC8F:          STAA    $0021,X
CC91:          LDAA    #$0040
CC93:          STAA    $0026,X
CC95:          LDAA    #$0038
CC97:          STAA    $0001,X
CC99:          LDAA    #$0038
CC9B:          STAA    $0009,X
CC9D:          LDAA    #$0004
CC9F:          STAA    $002B,X
CCA1:          LDAA    #$0015
CCA3:          STAA    $003C,X
CCA5:          LDAA    #$00AC
CCA7:          STAA    $005D,X
CCA9:          LDAA    #$00CB
CCAB:          STAA    $005F,X
CCAD:          LDAA    #$0000
CCAF:          STAA    $005E,X
CCB1:          LDAA    #$0090
CCB3:          STAA    L3061
CCB6:          LDAA    #$00FF
CCB8:          STAA    L3063
CCBB:          LDAA    #$0000
CCBD:          STAA    L3065
CCC0:          RTS     
 			;-----------------------------------------


			;-----------------------------------------
			; CALLED FM MAJOR LOOP D
			;   	1. FILTER ... o2 VOLTAGES
			;   	2. DO A.I.R MANAGE
			;   	3.
			;-----------------------------------------
CCC1:  LCCC1   LDX     L01D0				; o2 VOLTAGE, 1
CCC4:          LDAB    L4E89				; MJR LP o2 SENSOR FILTER COEF
CCC7:          LDAA    L01D5				; o2 VOLTS * 226 (A/D RESULT)
CCCA:          JSR     LF459				; LAG FILTER
CCCD:          STD     L01D0				; o2 VOLTAGE, 1

CCD0:          LDX     #$400B				; AFR MD BYTE 1, 0000 0100
CCD3:          BRSET   0,X,#$02,LCCDA		; BR IF b1, (1 = AIR MANAGE)
CCD7:          JMP     LCD2C				; EXIT IF NOT A.I.R
 

CCDA:  LCCDA   CLRB    
CCDB:          BRCLR   L003B,#$10,LCCF0
CCDF:          LDX     #$038F
CCE2:          BRCLR   0,X,#$02,LCCF0
CCE6:          LDX     #$0390
CCE9:          BRSET   0,X,#$02,LCD21

CCED:          JMP     LCD26


CCF0:  LCCF0   LDAA    L0006				; COOL VALUE
CCF2:          CMPA    L4E8C				; DISABLE AIR INJ IF L.T. 151 Deg c
CCF5:          BCS     LCD26			    ;
CCF7:          BRSET   L0071,#$01,LCD26		; BR IF b0
											;
CCFB:          BRCLR   L003D,#$20,LCD0A		; BR IF NOT b5, PWR ENR IS ACTIVE 
											;
CCFF:          LDAB    L0279				; PWR ENR TIMER
CD02:          CMPB    L4E8D				; DISABLE AIR INJ IF PWR ENR G.T. 0 SEC'S
CD05:          BHI     LCD26				; 
											;
CD07:          INCB    						; INCR PWR ENR TMR

CD08:          BRA     LCD21
 

CD0A:  LCD0A   LDAA    L0061				; RPM/25
CD0C:          CMPA    L4E8A				; DISABLE AIR INJ IF G.T. 6375 RPM
CD0F:          BHI     LCD26				;
											;
CD11:          LDAA    L01C6				;
CD14:          CMPA    L4E8B				; DISABLE AIR INJ IF L.T. 20 Kpa
CD17:          BCS     LCD26				; BR IF MAP LT THRESH, (Turn air 0ff)
											;
CD19:          BRSET   L0050,#$02,LCD21		; BR IF b1,
											;
CD1D:          BRSET   L003E,#$80,LCD26		; BR IF b7,	CLOSED LOOP
											;
CD21:  LCD21   BSET    L0046,#$04			; SET b2, AIR MANAGMENT OFF, 1=ON 

CD24:          BRA     LCD29

CD26:  LCD26   BCLR    L0046,#$04			; CLR b2, AIR MANAGMENT OFF, 1=ON

CD29:  LCD29   STAB    L0279

CD2C:  LCD2C   BRA     LCD2E

CD2E:  LCD2E   LDAA    L00A7   				; BAT VOLTS, VDC/10
CD30:          CMPA    #171 				; 17.1
CD32:          BCS     LCD3D				; BR IF BAT VOLTS LT 17.1
CD34:          BRSET   L0051,#$10,LCD58		; BR IF b4,
CD38:          BSET    L0051,#$10			; SET b4,

CD3B:          BRA     LCD40


CD3D:  LCD3D   BCLR    L0051,#$10			; CLR b4,

CD40:  LCD40   BRSET   L004F,#$80,LCD67		; BR IF b7, ENGINE RUNNING
											;
CD44:          BRCLR   L0071,#$80,LCD58		; BR IF NOT b7,

CD48:          LDAA    #255					; FORCE MAX VALUE
CD4A:          STAA    L01D6 				; PURGE D.C

CD4D:          BSET    L0046,#$04			; SET b2, AIR MANAGMENT OFF, 1=ON
CD50:          BSET    L0041,#$10			; SET b4,
CD53:          BSET    L0052,#$08			; SET b3, 

CD56:          BRA     LCD67

 
CD58:  LCD58   CLR     L01D6 				; PURGE D.C
CD5B:          BCLR    L0046,#$04			; CLR b2, AIR MANAGMENT OFF, 1=ON
CD5E:          BCLR    L0053,#$04			; CLR b2
CD61:          BCLR    L0041,#$10			; CLR b4
CD64:          BCLR    L0052,#$08			; CLR b2
CD67:  LCD67   LDD     #$DFFF

CD6A:          BRSET   L0046,#$04,LCD71		; BR IF NOT b2,  AIR MANAGMENT OFF, 1=ON

CD6E:          LDD     #$D000
CD71:  LCD71   STD     L3FDA				; HARDWARE

CD74:          BRCLR   L003B,#$10,LCD84

CD78:          LDX     #$0393
CD7B:          BRCLR   0,X,#$04,LCD84		; BR IF NOT b2
											;
CD7F:          LDAB    L0394

CD82:          BRA     LCD87
 

CD84:  LCD84   LDAB    L01D6 				; PURGE D.C
CD87:  LCD87   CLRA    
CD88:          ASLD    
CD89:          ASLD    
CD8A:          ASLD    
CD8B:          ORAA    #176
CD8D:          STD     L3FD6
CD90:          LDX     #$0393
CD93:          BRCLR   0,X,#$38,LCDA4
CD97:          CLRA    
CD98:          LDAB    L0394
CD9B:          ASLD    
CD9C:          ASLD    
CD9D:          ASLD    
CD9E:          ASLD    
CD9F:          ORAA    #112
CDA1:          XGDX    
CDA2:          BRA     LCDCB
 ;
CDA4:  LCDA4   LDX     #$7FFF

			;----------------------------------------------
			; AFR MD BYTE 5,	 0001 0000, (DIG I/O)
			;
			; b7 1 = MAN, (0 = TCC)
			; b6 1 = TCC (Non Elect xmish)
			; b5 1 = Not Used 
			; b4 1 = CONV OVER HEAT PROTECTION
			;
			; b3 1 = BURST KNOCK RETARD
			; b2 1 = A/C CLUTCH CNT'L, 0 = CPI TUNE
			; b1 1 = Not Used
			; b0 1 = 1 DO RPM/MPH LMT, (GOV'R OPT)
			;
			;----------------------------------------------
CDA7:          LDY     #$400F				; AFR MD BYTE 5, 0001 0000, (DIG I/O)
CDAB:          BRCLR   0,Y,#$01,LCDB9		; BR IF NOT b0, 1 DO RPM/MPH LMT, (GOV'R OPT)
CDB0:          LDAA    L0062				; ENGINE RPM/25
CDB2:          CMPA    L50DC				; O RPM
CDB5:          BCC     LCDCB				; BR IF RPM GT THRESH
CDB7:          BRA     LCDC8
 ;
CDB9:  LCDB9   BRSET   L0052,#$08,LCDCB

			;----------------------------------------------
			; AFR MD BYTE 5,	 0001 0000, (DIG I/O)
			;
			; b7 1 = MAN, (0 = TCC)
			; b6 1 = TCC (Non Elect xmish)
			; b5 1 = Not Used 
			; b4 1 = CONV OVER HEAT PROTECTION
			;
			; b3 1 = BURST KNOCK RETARD
			; b2 1 = A/C CLUTCH CNT'L, 0 = CPI TUNE
			; b1 1 = Not Used
			; b0 1 = 1 DO RPM/MPH LMT, (GOV'R OPT)
			;
			;----------------------------------------------
CDBD:          LDAA    L400F				; AFR MD BYTE 5, 0001 0000,(DIG I/O)
CDC0:          BITA    #$0004				; b2
CDC2:          BEQ     LCDC8				; BR IF NOT b2
CDC4:          BRCLR   L0041,#$10,LCDCB		; BR IF NOT b4,
CDC8:  LCDC8   LDX     #$7000
CDCB:  LCDCB   STX     L3FD4

			;------------------------------
			; AFR MD BYTE 4,	 0000 0011 
			;
			; b7 1 = Not Used
			; b6 1 = Not Used
			; b5 1 = LATCH ERR 45
			; b4 1 = USE L4968 WITH ASYNC FUEL DELIVERY
			;
			; b3 1 = CPI MANAFOLD TUNE CNT'L
			; b2 1 = SHIFT LIGHT ENABLE 
			; b1 1 = USE ALT CMAP vs
			;    MAP LD FOR FUEL CUR HYST PAIR
			; b0 1 = USE ALT CMAP vs
			;    MAP LD & AD MAP FOR BLM ENABLE 
			;------------------------------
CDCE:  LCDCE   LDX     #$400E				;  AFR MD BYTE 4, 0000 0011 
CDD1:          BRCLR   0,X,#$04,LCDE2		; BR IF	NOT b2, 1 = SHIFT LIGHT ENABLE 

CDD5:          LDD     #$1FFF
CDD8:          BRSET   L0053,#$04,LCDDF		; BR IF b2
CDDC:          LDD     #$1F00
CDDF:  LCDDF   STD     L306C

			;----------------------------------------------
			; AFR MD BYTE 5,	 0001 0000, (DIG I/O)
			;
			; b7 1 = MAN, (0 = TCC)
			; b6 1 = TCC (Non Elect xmish)
			; b5 1 = Not Used 
			; b4 1 = CONV OVER HEAT PROTECTION
			;
			; b3 1 = BURST KNOCK RETARD
			; b2 1 = A/C CLUTCH CNT'L, 0 = CPI TUNE
			; b1 1 = Not Used
			; b0 1 = 1 DO RPM/MPH LMT, (GOV'R OPT)
			;
			;----------------------------------------------
CDE2:  LCDE2   LDX     #$400F				; AFR MD BYTE 5, 0001 0000,(DIG I/O)
CDE5:          BRCLR   0,X,#$40,LCDF6		; BR IF NOT b6, 1 = TCC (Non Elect xmish) 
CDE9:          LDD     #$7FFF
CDEC:          BRSET   L0089,#$20,LCDF3 	; BR IF b5,
											;
CDF0:          LDD     #32512	
CDF3:  LCDF3   STD     L306A

CDF6:  LCDF6   RTS     
 		;----------------------------------------------


CDF7:  LCDF7   CLRB    
CDF8:          BRSET   L0051,#$10,LCE0A		; BR IF b4, 
											;
CDFC:          BRSET   L004F,#$80,LCE07		; BR IF b7, ENGINE RUNNING

CE00:  LCE00   BRCLR   L0071,#$80,LCE0A		; BR IF NOT b7
											;
CE04:          DECB    

CE05:          BRA     LCE0A

 
CE07:  LCE07   LDAB    L01AF				; Pct EGR D.C.
CE0A:  LCE0A   LDAA    #240
CE0C:          STD     L3FD8

CE0F:          RTS     
			;----------------------------------------------



			;----------------------------------------------
			; MJR LOOP SEG
			;
			;----------------------------------------------	
CE10:  LCE10   LDAA    L0002				; MJR LOOP SEGMENT COUNT
CE12:          CMPA    #$06					; SEGMENT 6 
CE14:          BNE     LCE7B				; BR IF 
											;
CE16:          LDAB    L0209				;

		;
		;  CURRENT ERR WD #4
		;
CE19:          BRSET   L0019,#$10,LCE64		; BR IF b4, ERR 43, KNOCK SENSOR CKT
											;
CE1D:          LDAA    L0006				; COOL VALUE
CE1F:          CMPA    L45B6				; .. c, MIN FOR LOW OCTANE
CE22:          BLS     LCE78

CE24:          LDAA    L01C0				; GET CURRENT MAP VALUE
CE27:          CMPA    L45B7				; 52 Kpa MAP, MIN FOR LOW OCTANE
CE2A:          BCS     LCE78				; BR IF MAP 
											;
CE2C:          SUBA    L01C2
CE2F:          BCS     LCE36

CE31:          CMPA    L45B8				;  L.T. or E.Q  Kpa DIFF MAP INCREASE, (LO OCTAINE)
CE34:          BHI     LCE78

CE36:  LCE36   LDAA    L020C				; DEG, KNOCK RETARD
CE39:          CMPA    L45BA				; 1.8 deg LO OCTANE KNOCK
CE3C:          BLS     LCE58				;
											;
CE3E:          CMPA    L45B9				; 2 deg HI KNOCK ACTIVITY
CE41:          BLS     LCE78				;
											;
CE43:          BRSET   L0052,#$01,LCE4F		; BR IF NOT b0, 1 = HIGH KNOCK ACTIVITY 
											;
CE47:          BSET    L0052,#$01			; SET b0,  1 = HIGH KNOCK ACTIVITY
CE4A:          BCLR    L0052,#$02			; CLR b1,  ZERO ACTIVITY FLAG (LO OCTANE)

CE4D:          BRA     LCE6A



CE4F:  LCE4F   ADDB    L45BB				; 25 CNT'S LO OCT CNTR, INCR CNTS IF
											; HI KNOCK > KNK RETARD  G.T. L45AA 
CE52:          BCC     LCE6A				; BR IF NO OVERFLOW 
											;
CE54:          LDAB    #255					; USE MAX VALUE

CE56:          BRA     LCE6A



CE58:  LCE58   BRSET   L0052,#$02,LCE64		; BR IF b1, ZERO ACTIVITY FLAG (LO OCTANE)
											;
CE5C:          BSET    L0052,#$02			; SET b1, ZERO ACTIVITY FLAG (LO OCTANE)
CE5F:          BCLR    L0052,#$01			; CLR b0,  1 = HIGH KNOCK ACTIVITY

CE62:          BRA     LCE6A


CE64:  LCE64   SUBB    L45BC				; 26 CNT'S LO OCT CNTR, INCR CNTS IF
											; HI KNOCK (= KNK RETARD  G.T. L45AB
CE67:          BCC     LCE6A
CE69:          CLRB    
CE6A:  LCE6A   STAB    L0209
CE6D:          LDAA    L45BD				; 8 Deg LO OCT BASE SPK RETARD MAX
CE70:          MUL     
CE71:          ADCA    #$00
CE73:          STAA    L020A				; LO OCT BASE SPK RETARD SPK

CE76:          BRA     LCE7B

                    
		;--------------------------------------
        ; b1 1 = ZERO ACTIVITY FLAG (LO OCTANE)
        ; b0 1 = HIGH KNOCK ACTIVITY     
		;--------------------------------------
CE78:  LCE78   BCLR    L0052,#$03			; CLR b0 & b1

CE7B:  LCE7B   RTS     
		;---------------------------------------------
	
		 	
 		;---------------------------------------------
		; TOC 1INTERUPT VECTOR HANDLER
		;
		;
		;---------------------------------------------
CE7C:          LDAA    #$80					; b7, TOC 1
CE7E:          STAA    L3023				; TMR FLG 1 REG

CE81:          LDD     L3FC8

CE84:          PSHB    
CE85:          PSHA    
CE86:          SUBD    L0203
CE89:          TSTA    
CE8A:          BEQ     LCE8E				; BR IF NO UNDERFLOW
											;
CE8C:          LDAB    #255
CE8E:  LCE8E   PULX    
CE8F:          STX     L0203
		
    	;---------------------------------------------
		; DIFF PA2 IGNORE TIME, (msec) vs RPM
		; (knock function)
    	;
    	;  TBL =  16.384  * Msec
    	;---------------------------------------------
CE92:          TBA     
CE93:          LDX     #$45DB				; INDEX DIFF PA2 IGNORE TIME TBL 
CE96:          LDAB    L0062				; ENGINE RPM/25 
CE98:          LSRB    						;
CE99:          LSRB    						;
CE9A:          ABX     						;
CE9B:          SUBA    0,X					;
CE9D:          BLS     LCEBA				; BR IF 
											;
    		;------------------------------------
    		; DIFF PA3 ADD ON TIME (msec) vs RPM
    		; (knock function)
			;
    		;  TBL =  16.384  * Msec
    		;------------------------------------
CE9F:          LDX     #$461C				; INDEX DIFF PA3 ADD ON TIME TBL
CEA2:          LDAB    L0062				; ENGINE RPM/25
CEA4:          LSRB    						;
CEA5:          LSRB    						;
CEA6:          ABX     						;
CEA7:          ADDA    0,X					;
CEA9:          BCC     LCEAF				; BR IF NOT OVERFLOW
											;
CEAB:          LDAB    #255					; FORCE MAX VALUE
CEAD:          BRA     LCEB7				;
											;
											;
CEAF:  LCEAF   TAB     						;
CEB0:          ADDB    L020D				;
CEB3:          BCC     LCEB7				;
											;
CEB5:          LDAB    #255				; FORCE MAX VALUE
CEB7:  LCEB7   STAB    L020D				;

CEBA:  LCEBA   RTI     
 		;----------------------------------------------



    	;---------------------------------------------
    	; KNOCK RECOVERY RATE vs RPM
		;
    	;  TBL = %/Msec * (256/500)
    	;  TBL =  .512  * %/Msec
    	;---------------------------------------------
CEBB:  LCEBB   BRSET   L0002,#$10,LCEDB		; BR IF b4, MAJOR LOOP COUNTER
											;
CEBF:          LDX     #$45A5				; INDEX KNOCK RECOVERY RATE
CEC2:          LDAA    L0062				; ENGINE RPM/25
CEC4:          JSR     LF4C1				; 2d LK UP
											;
CEC7:          LDAB    L020C				; DEG, KNOCK RETARD
CECA:          MUL     						;
CECB:          ADCA    #$00					; PREVENT ROLL OVER
CECD:          NEGA    						; INVERT
CECE:          BNE     LCED2				;
											;
CED0:          LDAA    #255					; FORCE MAX VALUE
CED2:  LCED2   ADDA    L020C				; DEG, KNOCK RETARD
CED5:          BCS     LCED8				;
											;
CED7:          CLRA    

CED8:  LCED8   STAA    L020C				; DEG, KNOCK RETARD


CEDB:  LCEDB   LDAA    L5B03				; 1011 1100, ERR WD 4  
CEDE:          ANDA    #$10					; CLR ALL EXCEPT, ERR 43, KNOCK SYS FAIL
CEE0:          BEQ     LCF15				;
											;
CEE2:          LDX     #$3000				; INDEX CPU REG'S

CEE5:          LDAA    #$00
CEE7:          JSR     LF275			   	; DELAY ROUTINE

CEEA:          SEI     
CEEB:          LDAA    #$01
CEED:          JSR     LF25F				; A/D CNT'L MODE

		;---------------------------------------------
		; ERR 43
		; KNOCK SENSOR FAIL
		;---------------------------------------------
CEF0:          CLI     
CEF1:          LDAA    $34,X				; A/D RESULT 4
CEF3:          CMPA    L4E75				; 4.5 VDC A/D UPPER VOLTS LMT
CEF6:          BHI     LCEFD				; BR IF A/D VALUE GT THRESH
											;
CEF8:          CMPA    L4E76				; 0.390 VDC A/D LOWER VOLT LMT
CEFB:          BCC     LCF0F				; BR IF A/D VALUE GT THRESH, (MIN VDC)
											;
CEFD:  LCEFD   LDAA    L0207				; ERR 43 TIMER
CF00:          CMPA    L4E74			    ; 16 SEC'S. HI VOLTS CK PERIOD
CF03:          BHI     LCF0A				; BR IF ERR 43 TIMER 
											;
CF05:          INC     L0207				; INCR ERR 43 TIMER 

CF08:          BRA     LCF15



CF0A:  LCF0A   BSET    L0019,#$10			; SET b4, ERR WD #4, ERR 43

CF0D:          BRA     LCF15				; Exit WITH ERROR SET
 

CF0F:  LCF0F   BCLR    L0019,#$10			; CLR b4, ERR 43
CF12:          CLR     L0207				; CLR ERR 43 TIMER

CF15:  LCF15   RTS     
 	   	;----------------------------------------------


		;---------------------------------------------
		;
		;
		;---------------------------------------------
CF16:  LCF16   LDX     #$46F9	  			; INDEX EGR QUALS
											;
CF19:          LDAA    L400B				; AFR MD BYTE 1, 0000 0100
CF1C:          BITA    #$40					; b6 1 = MAT SENSOR 
CF1E:          BEQ     LCF2E				; BR IF NOT b1

CF20:          LDAA    L0230				; GET A/D INV MAT VAL

CF23:          LDAB    4,X					; -50c MAT THRESH to DISABLE EGR
											;
CF25:          BRSET   L006E,#$80,LCF2B		; BR IF b7, EGR ON
											;
CF29:          LDAB    3,X					; -50c MAT THRESH to ENABLE EGR
CF2B:  LCF2B   CBA     						;
CF2C:          BLS     LCF89				; BR IF MAT ....
											;
CF2E:  LCF2E   LDAA    L0282				; START UP COOL
CF31:          CMPA    0,X					; 20c START UP COOL THRESH TO ENABLE EGR 
CF33:          BLS     LCF3D				; BR IF ....
											;
CF35:          LDAA    2,X					; 39c COOL THRESH to ENABLE EGR
CF37:          CMPA    L0006				; COOL VALUE
CF39:          BHI     LCF89				; BR IF COOL ...
											;
CF3B:          BRA     LCF43				; Exit W/
 

CF3D:  LCF3D   LDAA    1,X					; 39c COOL THRESH to ENABLE EGR
CF3F:          CMPA    L0006				; COOL VALUE
CF41:          BHI     LCF89				; BR IF COOL LT Thresh
											;
CF43:  LCF43   BRCLR   L0018,#$30,LCF49		; BR IF NOT b4, b5	 b5 1 = ERR 33, MAP SENSOR HI
											;					 b4 1 = ERR 34, MAP SENSOR LOW

CF47:          BRA     LCF89
 
			;
			; CK LOWER EGR MAP THRESH 
			;	(Hist pair)
			;
CF49:  LCF49   LDAA    $0A,X				; 31 Kpa MAP Thresh for EGR OFF TO ON
									   		;
CF4B:          BRCLR   L006E,#$10,LCF51		; BR IF b4, EGR MAP HYST
											;
CF4F:          LDAA    $0B,X				; 29 Kpa MAP Thresh for EGR STAY ON
CF51:  LCF51   CMPA    L01C0				; GET CURRENT MAP VALUE
CF54:          BCS     LCF5B				; BR IF MAP LT THRESH 
											; ... els
CF56:          BCLR    L006E,#$10			; CLR b4, EGR MAP HYST

CF59:          BRA     LCF89
 

CF5B:  LCF5B   BSET    L006E,#$10			; SET b4,  EGR MAP HYST

CF5E:          LDAA    L006F
CF60:          BITA    #$24					; b5, b2
CF62:          BNE     LCF79				; BR IF 
											;
CF64:          LDAA    8,X					; 3% TPS Thresh for EGR OFF TO ON
CF66:          BRCLR   L006E,#$20,LCF6C		; BR IF NOT b5,EGR TPS HYST 
											;
CF6A:          LDAA    9,X					; 2% TPS Thresh for EGR TO STAY ON 
CF6C:  LCF6C   CMPA    L01D9				; CURRENT %TPS
CF6F:          BCS     LCF76				; BR IF 
											;
CF71:          BCLR    L006E,#$20			; CLR b5  EGR TPS HYST

CF74:          BRA     LCF89


CF76:  LCF76   BSET    L006E,#$20			; SET b5,  EGR TPS HYST
	
		;
		; CK RPM QUAL'S
		;									
CF79:  LCF79   LDAB    L0062				; ENGINE RPM/25
CF7B:          LDAA    6,X				   	; 1100 RPM Thrsh for EGR OFF TO ON 
											;
CF7D:          BRCLR   L006E,#$40,LCF83		; BR IF NOT b5,	 EGR MPH HYST
											;
CF81:          LDAA    7,X					; 1000 RPM Thrsh for EGR TO STAY ON
CF83:  LCF83   CBA     						;
CF84:          BLS     LCF8D				; BR IF 
											;
CF86:          BCLR    L006E,#$40			; CLR b6   EGR MPH HYST
CF89:  LCF89   CLRA    

CF8A:          JMP     LD010


 
CF8D:  LCF8D   BSET    L006E,#$40			; SET b6,  EGR MPH HYST
											;
CF90:          BRSET   L0016,#$10,LCF9C		; BR IF b4, ERR  ..

CF94:          LDAA    L0284				; MPH/1
CF97:          CMPA    L46FE				; 0 MPH Vss THRESH TO ENABLE EGR
CF9A:          BCS     LCF89				; BR IF  LT THRESH
											;

		;
		; CHECK VAC QUALS
		;
CF9C:  LCF9C   LDAA    $0C,X				; 3.75 Kpa VAC Thresh to TURN EGR OFF
											;
CF9E:          BRSET   L006E,#$04,LCFA4		; BR IF B2, EGR HI VAC HYST
											;
CFA2:          LDAA    $0D,X				; 7.50 Kpa VAC Thresh to KEEP EGR OFF
CFA4:  LCFA4   CMPA    L01C9				; Kpa VACUUM
CFA7:          BCC     LCFAE				; BR IF VAC gt THRESH
											;
CFA9:          BCLR    L006E,#$04			; EGR HI VAC HYST

CFAC:          BRA     LCF89

											;

		;
		; CHECK MAX %TPS QUAL'S
		;
CFAE:  LCFAE   BSET    L006E,#$04			; SET b2, EGR HI VAC HYST
											;
CFB1:          LDAA    $0E,X				; 98.8% MAX TPS for EGR ON
CFB3:          CMPA    L01D9				; %TPS
CFB6:          BCS     LCF89				; BR IF %TPS  
											;

		;
		; CHECK AFR QUAL'S
		;
CFB8:          LDAA    $0F,X				; EGR OFF WHEN l.t. 13:1 AFR
CFBA:          CMPA    L024A				; AFR
CFBD:          BHI     LCF89				; BR IF AFR ....
											;
CFBF:          BRSET   L0046,#$08,LCF89		; BR IF b3, DECEL FUEL C/O  
											;
CFC3:          LDAA    L400D				; AFR MD BYTE 3, 1000 0010
CFC6:          BITA    #$08					; b3,1 = OPN LP FUEL DISABLE EGR
CFC8:          BEQ     LCFCE				; BR IF b3
											;
CFCA:          BRCLR   L003E,#$80,LCF8		; BR IF NOT b7,	CLOSED LOOP
											;
    	;----------------------------------------------
    	; DESIRED EGR vs RPM & LOAD, (VAC or MAP)
    	;
    	;
    	; 	1. DIGITAL VALVE ALL VALS = 255
    	; 	2. LINEAR EGR DESIDED PINTEL POSIT
    	; 	3. EVRV D.C.
    	;----------------------------------------------
CFCE:  LCFCE   LDX     #$470A

CFD1:          LDAB    L01CF
CFD4:          LDAA    0,X					; SEL LOAD MODE
CFD6:          CMPA    #2					; 2 = ALT MAP
CFD8:          BEQ     LCFE4
											;
CFDA:          LDAB    L01C9				; Kpa VACUUM
CFDD:          LDAA    0,X					; SEL LOAD MODE
CFDF:          BEQ     LCFE4				; BR IF MOD = 0 = VAC
											; 
CFE1:          LDAB    L01C0				; GET CURRENT MAP VALUE

CFE4:  LCFE4   INX     						; INCR TO INDEX TOP OF 3d TABLE 
CFE5:          LSRB    
CFE6:          LDAA    L0062				; ENGINE RPM/25
CFE8:          CMPA    #160					; 4000 RPM
CFEA:          BLS     LCFEE
											;
CFEC:          LDAA    #160					; FORCE 4000 RPM AS MAX RPM 
CFEE:  LCFEE   JSR     LF4DE				; 3d LK UP

CFF1:          TAB     						; RESULT TO B REG
CFF2:          LDAA    L01BB
CFF5:          MUL     						; APPLY MULT
CFF6:          ASLD    						; N x 2
CFF7:          BCC     LCFFB				; BR IF NOT OVERFLOW
											;
CFF9:          LDAA    #255					; FORCE MAX VALUE

    	;----------------------------------------------
    	; EGR GAIN FACTOR vs BARO & MAP
    	;
    	;   FOR BP EGR WITH 0   TO DISABLE  EGR
    	;           OR WITH 128 TO ENABLE   EGR
    	;
    	; TBL = FACTOR * 1.28
    	;----------------------------------------------
CFFB:  LCFFB   PSHA    						;
CFFC:          LDX     #$4767				; EGR GAIN FACTOR vs BARO & MAP	
											;
CFFF:          LDAB    L01CC				; BARO VALUE (Kpa)
											;
D002:          LDAA    L01C0				; CURRENT MAP VALUE (Kpa)
D005:          LSRA    						; MAP/2
D006:          JSR     LF4DE				; 3d LK UP
											;
D009:          PULB    						;
D00A:          MUL     						; APPLY MULT. 
D00B:          ASLD    						; n x 2
D00C:          BCC     LD010				; BR IF NO OVERFLOW
											;
D00E:          LDAA    #255					;
											;
D010:  LD010   CMPA    L4709				; 4.6% MIN DESIRED EGR
											;	 0 EGR IF REQUESST L.T. 4.6%  
D013:          BCC     LD017				; BR IF ... 
											;
D015:          BRA     LD021				; ZERO DESIRED %EGR


D017:  LD017   BRSET   L0051,#$10,LD021	   	; BR IF b4, ZERO DESIRED %EGR
											;
D01B:          BRSET   L0072,#$20,LD021	   	; BR IF b5, ZERO DESIRED %EGR
											;
D01F:          BRA     LD022				; SAVE DESIRED %EGR, (Non-BP)
 

D021:  LD021   CLRA    						; ZERO DESIRED %EGR
D022:  LD022   STAA    L01AE   				; DESIRED %EGR
											;
D025:          BRCLR   L0086,#$40,LD02C		; BR IF NOT b6, HEADS UP
											;
D029:          JSR     L1815				; TO HEADS UP
											;
D02C:  LD02C   BRCLR   L003B,#$10,LD03D		; BR IF NOT b4,
											;
D030:          LDAA    L0393				;
D033:          BITA    #$02					; b1
D035:          BEQ     LD03D				; BR IF NOT b1, 
											;
D037:          LDAA    L0394				;
D03A:          STAA    L01AE   				; DESIRED %EGR

D03D:  LD03D   RTS     
		;---------------------------------------------


		;---------------------------------------------
		;
		;
		;---------------------------------------------
D03E:  LD03E   LDX     #$400D				; AFR MD BYTE 3, 1000 0010
D041:          BRSET   0,X,#$20,LD049		; BR IF b6,	USE L4479 TBL FOR %EGR
											;
D045:          BRCLR   0,X,#$04,LD088		; BR IF b2,	BACK PRESS EGR
											;
D049:  LD049   BCLR    L006E,#$80			; CLR b7, EGR ON
D04C:          BRSET   L0070,#$01,LD059		; BR IF b0
											;
D050:          BRSET   L0070,#$04,LD05F		; BR IF b2
											;
D054:          LDAA    L01AF				; EGR D.C
D057:          BNE     LD05C				; BR IF EGR D.C IS NZ
											;
D059:  LD059   CLRA    						; ZERO EGR D.C.
D05A:          BRA     LD084


D05C:  LD05C   BSET    L006E,#$80			; SET b7  EGR ON
    	;---------------------------------------------
    	; EGR PCT EGR vs RPM & VAC
    	; (BP EGR)
    	;
    	; TBL = 00 = NO FUEL REDUCTION
    	;     = FF = 25% FUEL REDUCTION
    	;
    	; FUEL REMOVED PCT
    	;
    	; TBL = EGR% * 10.24
    	;---------------------------------------------
D05F:  LD05F   LDX     #$478A

D062:          LDAB    L01C9				; Kpa VACUUM
D065:          NEGB    
D066:          CMPB    #64
D068:          BHI     LD06D
											;
D06A:          ASLB    						; N x 2

D06B:          BRA     LD078

 
D06D:  LD06D   SUBB    #64
D06F:          LSRB    
D070:          ADDB    #128
D072:          CMPB    #192
D074:          BLS     LD078				; BR IF ....

D076:          LDAB    #192

D078:  LD078   LDAA    L0062				; ENGINE RPM/25
D07A:          CMPA    #160					; 4000 RPM
D07C:          BLS     LD080				; BR IF RPM LT 4000 RPM
											;
D07E:          LDAA    #160					; FORCE 4000 RPM
D080:  LD080   LSRA    						; RPM/2
D081:          JSR     LF4DE				; 3d LK UP

D084:  LD084   PSHA    

D085:          JMP     LD121



D088:  LD088   BCLR    L006E,#$80			; CLR b7, EGR ON
D08B:          BRSET   L0070,#$01,LD103		; BR IF b0
											;
D08F:          BRSET   L0072,#$20,LD103		; BR IF b5
											;
D093:          BRSET   L0070,#$04,LD0CC		; BR IF b2
											;

			;-----------------------------------------                         
			; AFR MD BYTE 3, 1000 0010
			;
			; b7 1 = SINGLE PASS EGR TEST
			; b6 1 = VATS
			; b5 1 = USE L4479 TBL FOR %EGR
			; b4 1 = EGR = 0 AT IDLE
			;
			; b3 1 = OPN LP FUEL DISABLE EGR
			; b2 1 = BACK PRESS EGR
			; b1 1 = LINEAR EGR/ 0 = EVRV EGR
			; b0 1 = USE TBL L4BA9 FOR CLS LP AFR
			;        IF COOL L.T. L48C0
			;-----------------------------------------
D097:          LDX     #$400D
D09A:          BRCLR   0,X,#$02,LD0B7		; LINEAR EGR/ 0 = EVRV EGR

D09E:          BRCLR   0,X,#$10,LD0A6		; USE TBL L4BBA FOR CLS LP AFR IF COOL L.T. L48D1
D0A2:          BRSET   L0050,#$80,LD103		; BR IF b7, IDLE
											;
D0A6:  LD0A6   LDAB    L01B9				; LINEAR EGR POS 
D0A9:          CMPB    L485A
D0AC:          BCS     LD103

D0AE:          LDX     L00FD				; RUN TIMER
D0B0:          CPX     L485B				; 3 Sec's MIN ENG RUN TIME FOR EGR
D0B3:          BCS     LD103				; BR IF TIMER LT THRESH
											;
D0B5:          BRA     LD0BF
 

D0B7:  LD0B7   LDAB    L01AF				; EGR D.C
D0BA:          CMPB    L485D				; 0, MIN EVRC D.C. THRESH FOR FLOW
D0BD:          BCS     LD103				; BR IF EGR, THRESH
											;

			;-----------------------------------------                         
			; AFR MD BYTE 3, 1000 0010
			;
			; b7 1 = SINGLE PASS EGR TEST
			; b6 1 = VATS
			; b5 1 = USE L4479 TBL FOR %EGR
			; b4 1 = EGR = 0 AT IDLE
			;
			; b3 1 = OPN LP FUEL DISABLE EGR
			; b2 1 = BACK PRESS EGR
			; b1 1 = LINEAR EGR/ 0 = EVRV EGR
			; b0 1 = USE TBL L4BA9 FOR CLS LP AFR
			;        IF COOL L.T. L48C0
			;-----------------------------------------
D0BF:  LD0BF   BSET    L006E,#$80			; SET b7, EGR ON
											; 
D0C2:          LDAA    L01B9				; LINEAR EGR POS

D0C5:          LDX     #$400D
D0C8:          BRSET   0,X,#$02,LD0CF		; LINEAR EGR/ 0 = EVRV EGR
											;
D0CC:  LD0CC   LDAA    L01AE    			; DESIRED %EGR, (Non-BP)
D0CF:  LD0CF   LDAB    #$A0
D0D1:          MUL     
D0D2:          ADCA    #$0000
D0D4:          PSHA    


       	;----------------------------------------------
	   	;  EGR EXHAUST BACK PRESS Vs EGR AIR FLOW
	   	;
	   	;  MY 95 L19
       	;  Dissassemby of BMHM
	   	;
	   	; TBL = KPA * 3.2
       	;----------------------------------------------
D0D5:          LDAA    L0232				; AIR FLOW
D0D8:          LDX     #$47D3				; EGR EXHAUST BACK PRESS TABLE
D0DB:          JSR     LF4C1				; 2d LK UP

D0DE:          LDAB    L01C9				; Kpa VACUUM
D0E1:          NEGB    
D0E2:          ABA     
D0E3:          BCC     LD0E7
											;
D0E5:          LDAA    #255

D0E7:  LD0E7   STAA    L01B0
D0EA:          CMPA    #64
D0EC:          BCS     LD0F9
											;
D0EE:          SUBA    #64
D0F0:          LSRA    
D0F1:          ADDA    #64
D0F3:          CMPA    #144
D0F5:          BCS     LD0F9

D0F7:          LDAA    #144
D0F9:  LD0F9   TAB     
D0FA:          PULA    

        ;----------------------------------------------
    	; %EGR FLOW vs EGR VALVE PRESS DROP and 
    	; LINEAR EGR POSIT, (or EVRV D.C.)
    	;
    	;
    	; TABLE = %PRES DROP * 2.56
        ;----------------------------------------------
D0FB:          LDX     #$47E5
D0FE:          JSR     LF4DE				; 3d LK UP
D101:          BRA     LD104
 ;
D103:  LD103   CLRA    						;
D104:  LD104   STAA    L01B1				;

D107:          LDAB    L47E4				;
D10A:          MUL     						;
D10B:          LSRD    						;
D10C:          BCC     LD111				;
											;
D10E:          ADDD    #$01					;

D111:  LD111   LDX     L0232				; AIR FLOW
D114:          FDIV    						;
D115:          PSHX    						;
D116:          PULA    						;
D117:          PULB    						;
D118:          CMPA    #255					;
D11A:          BEQ     LD120				;
											;
D11C:          TSTB    						;
D11D:          BPL     LD120				;
											;
D11F:          INCA    						;
D120:  LD120   PSHA    						;

        ;----------------------------------------------
    	; ALTITUDE CORR MULT OF ENGINE % EGR vs BARO
		;
		;	BARO 75- 105 Kpa
		;
    	; TABLE = FACTOR
        ;----------------------------------------------
D121:  LD121   LDX     #$4856				; ALT CORR MULT OF ENGINE
D124:          LDAA    L01CC				; BARO VALUE (Kpa)
											;
D127:          LDAB    #96					;
D129:          JSR     LF4BD				;

D12C:          PULB    						;
D12D:          MUL     						;
D12E:          TSTB    						;
D12F:          BPL     LD132				;
											;
D131:          INCA    						;
D132:  LD132   PSHA    						;
D133:          LDAA    L0232				; AIR FLOW
D136:          CMPA    #64					;
D138:          BLS     LD13C				;
											;
D13A:          LDAA    #64					;
        ;---------------------------------------------
        ; FILTER CONTANTS FOR EGR PCT vs AIR
        ;
        ;---------------------------------------------
D13C:  LD13C   LDX     #$47CE				; FILTER CONTANTS FOR EGR PCT TBL
D13F:          JSR     LF4C1				; 2d LK UP
											;
D142:          TAB     						;
											;
D143:          PULA    						;
D144:          LDX     L01B2				;
D147:          JSR     LF459				;
											;
D14A:          STD     L01B2				;

D14D:          RTS     
		;--------------------------------------------------


		;--------------------------------------------------
		; CHECK IF BACK PRESS EGR
		;
		;  b1 1 = LINEAR EGR/0 = EVRV EGR
		;--------------------------------------------------
D14E:  LD14E   LDAA    L400D				; AFR MD BYTE 3, 1000 0010
D151:          BITA    #$02					; 1 = BACK PRESS EGR
D153:          BNE     LD15C				; BR IF b1
											;
D155:          CLRA    						; CLR LINEAR EGR POS ACCUM. 
D156:          STAA    L01B9				; LINEAR EGR POS

D159:          JMP     LD1F5


		;--------------------------------------------------
		;
		;
		;
		;-------------------------------------------------
D15C:  LD15C   LDX     #$3000				; INDEX CPU REG'S

D15F:          SEI  
  
D160:          LDAA    #$03

D162:          BCLR    8,X,#$38				; CLR PRT D b3, b4 & b5

D165:          ASLA    
D166:          ASLA    
D167:          ASLA    
D168:          ORAA    8,X					;
D16A:          STAA    8,X					; PORT D
											;
			;
			; DO A/D PROCESS, EGR POSITION
			;
D16C:          LDAA    #$01					; SELECT CHANEL 
											;
D16E:          BCLR    L001A,#$02			; CLR b1,
											; 
D171:          STAA    L3030				; A/D CNTL 
											;
D174:          LDAB    #12					; SET A/D DELAY TIMER
											;
D176:  LD176   BRSET   $30,X,#$80,LD183		; BR IF b7, 
											;
D17A:          DECB    						; DECR A/D DELAY TIMER
D17B:          BNE     LD176				; LOOP TILL DONE
											;
D17D:          BSET    L003A,#$01			; SET b0, 
D180:          BSET    L001A,#$02			; SET b2, 
											;
D183:  LD183   CLI     						;
D184:          LDAA    $34,X				; A/D RESULTS CH 4
D186:          STAA    L01B4				; EGR POSITION A/D COUNTS
											;
D189:          CMPA    L01B5				;
D18C:          BCC     LD1A3				;
											;
D18E:          LDX     L01B5				;
D191:          LDAB    L48A7				; 4 COEF, CLS VALVE POSIT AUTO ZERO
D194:          JSR     LF459				; LAG FILT
											;
D197:          CMPA    L48A6				; 8 A/D BIN MIN FOR CLOSED VALVE
D19A:          BCC     LD1A0				;
											;
D19C:          LDAA    L48A6				; 8 A/D BIN MIN FOR CLOSED VALVE
D19F:          CLRB    						;
D1A0:  LD1A0   STD     L01B5				;
											;
D1A3:  LD1A3   LDAA    L01B4				; EGR POSITION A/D COUNTS
											;
D1A6:          LDAB    #128					;
D1A8:          SUBD    L01B5				;
D1AB:          BCC     LD1AE				;
											;
D1AD:          CLRA    						;
											;
D1AE:  LD1AE   LDAB    L48A4				; 95 A/D BIN FOR EGR VALVE POSIT SCALAR
D1B1:          MUL     						; APPLY MULTIPLIER
D1B2:          CPD     #$3FC0				; HARDWARE
D1B6:          BLS     LD1BB				;
											;
D1B8:          LDD     #$3FC0				; HARDWARE
D1BB:  LD1BB   ASLD    						;
D1BC:          ASLD    						;
D1BD:          LDX     L01B7				;
D1C0:          LDY     #$48A8				; 0.688 COEF FILTER EGR POSIT
D1C4:          JSR     LF436 				; LAG FILTER SUB ROUTINE, XMSIH
											;
D1C7:          STD     L01B7				;
											;
											;
D1CA:          ADDD    #128					;
D1CD:          STAA    L01B9				; LINEAR EGR POS
D1D0:          CMPA    #128					;
D1D2:          BLS     LD1D9				;
											;
D1D4:          BSET    L0041,#$01			;
D1D7:          BRA     LD1F5				
											
D1D9:  LD1D9   TST     L01AE    			; DESIRED %EGR, (Non-BP)
D1DC:          BNE     LD1F5				;
											;
D1DE:          BRCLR   L0041,#$01,LD1F5		;
											;
D1E2:          BCLR    L0041,#$01

D1E5:          LDAA    #$02					;
D1E7:          ADDA    L01B5				;
D1EA:          CMPA    L48A5				; 77 A/D BIN MAX FOR CLOSED VALVE 
D1ED:          BLS     LD1F2				;
											;
D1EF:          LDAA    L48A5				; 77 A/D BIN MAX FOR CLOSED VALVE
D1F2:  LD1F2   STAA    L01B5				;

D1F5:  LD1F5   RTS     
 		;---------------------------------------------



 		;---------------------------------------------
		;
		;
 		;---------------------------------------------
D1F6:  LD1F6   BRSET   L0070,#$04,LD233		; BR IF b2, 
											;
D1FA:          LDX     #$400D				; AFR MD BYTE 3, 1000 0010
D1FD:          BRSET   0,X,#$02,LD207		; BR IF b2,	1 = BACK PRESS EGR
											; ... els
D201:          LDAA    L01AE    			; DESIRED %EGR
D204:          JMP     LD2AE


D207:  LD207   BRCLR   L003B,#$10,LD212		; BR IF NOT b4,
											;
D20B:          LDAA    L0393				;
D20E:          BITA    #$02					; b1
D210:          BNE     LD21A				; BR IF b1
											;
D212:  LD212   BRSET   L0070,#$01,LD233		; BR IF b0,
											;
D216:          BRSET   L0072,#$20,LD233		; BR IF b5,
											;
D21A:  LD21A   LDAA    L01AE    			; DESIRED %EGR, (Non-BP)
											;
D21D:          BCLR    L006D,#$08			; CLR b3, 
											;
D220:          SUBA    L01B9				; LINEAR EGR POS
D223:          BCC     LD229				; BR IF POSITIVE RESULT

D225:          NEGA    						; INVERT RESULT
											;
D226:          BSET    L006D,#$08			; SET b3,


D229:  LD229   STAA    L01BA				; EGR POSIT ERROR
											;
D22C:          TST     L01AE    			; DESIRED %EGR, (Non-BP)
D22F:          BNE     LD239				; BR IF NZ
											;
D231:          BRA     LD2A6
			;----------------------------------------------



			;----------------------------------------------
			;
			;
			;
			;----------------------------------------------
D233:  LD233   CLRA    
D234:          STAA    L01BA				; EGR POSIT ERROR

D237:          BRA     LD2A7


D239:  LD239   LDD     L01BC
D23C:          BNE     LD24B

        ;-------------------------------------------------
        ; EGR D.C. INTEGRAL INIT vs DESIRED EGR POSIT
        ;
        ; TBL = %D.C. * 2.56
        ;-------------------------------------------------
D23E:          LDAA    L01AE    			; DESIRED EGR POSIT
D241:          LDX     #$48A9
D244:          JSR     LF4B6
D247:          CLRB    
D248:          STD     L01BC


        ;-------------------------------------------------
        ; EGR D.C. INTEGRAL GAIN MULT vs EGR POSIT ERR
        ;
        ; TBL = FACTOR * 128
        ;-------------------------------------------------
D24B:  LD24B   LDAA    L01BA				; EGR POSIT ERROR
D24E:          LDX     #$48AF				; EGR D.C. INTEGRAL GAIN MULT TBL
D251:          JSR     LF4B6				; 2D LK UP

D254:          LDAB    L01BA				; EGR POSIT ERROR
D257:          MUL     						; APPLY MULT 
D258:          STD     L084F

D25B:          LDD     L01BC
D25E:          BRSET   L006D,#$08,LD26C
D262:          ADDD    L084F
D265:          BCC     LD26A
D267:          LDD     #$FFFF
D26A:  LD26A   BRA     LD273
 ;
D26C:  LD26C   SUBD    L084F
D26F:          BCC     LD273
D271:          CLRA    
D272:          CLRB    
D273:  LD273   STD     L01BC



        ;-------------------------------------------------
        ; EGR D.C. PROPORTIONAL GAIN MULT vs 
        ; EGR POSIT ERROR
        ;
        ; TBL = FACTOR * 128
        ;-------------------------------------------------
D276:          LDAA    L01BA				; EGR POSIT ERROR
D279:          LDX     #$48B5
D27C:          JSR     LF4B6				; 2D LK UP

D27F:          LDAB    L01BA				; EGR POSIT ERROR
D282:          MUL     						; APPLY GAIN MULT 
D283:          ASLD    
D284:          BCC     LD289				; BR IF NOT OVERFLOW
											;
D286:          LDAA    #255					; USE MAX VALUE
D288:          CLRB    
D289:  LD289   STD     L01BE


D28C:          LDD     L01BC
D28F:          BRSET   L006D,#$08,LD29D
D293:          ADDD    L01BE
D296:          BCC     LD29B
D298:          LDD     #$FFFF
D29B:  LD29B   BRA     LD2AE
 ;
D29D:  LD29D   SUBD    L01BE
D2A0:          BCC     LD2AE
D2A2:          CLRA    
D2A3:          CLRB    

D2A4:          BRA     LD2AE


D2A6:  LD2A6   CLRA    
D2A7:  LD2A7   CLRB    
D2A8:          STD     L01BC
D2AB:          STD     L01BE
D2AE:  LD2AE   STAA    L01AF				; ZERO EGR EGR D.C

D2B1:          RTS     
 			;------------------------------------------


			;-----------------------------------------
			;
			;
			;
			;-----------------------------------------
D2B2:  LD2B2   BRCLR   L0002,#$10,LD2B9				; MAJOR LOOP COUNTER
D2B6:          JMP     LD3AF
 ;

			;-----------------------------------------
			; AFR MD BYTE 2	 1011 0111 
			;
			; b7 1 = CAN PURGE
			; b6 1 = CONDITIONAL INT R/S ON BLM CELL CHNAGE
			; b5 1 = INT R/S IF ACELL ENRICH
			; b4 1 = INT RESET IN BLM CELL CHANGE
			;
			; b3 1 = ASDF 
			; b2 1 = CRANK FUEL ALL INJ'S EACH DRP
			; b1 1 = ERR 44/45 BLM LMT
			; b0 1 = SYNC MAP SENSOR READS  
			;-----------------------------------------                         
D2B9:  LD2B9   LDAA    L400C
D2BC:          BITA    #$80
D2BE:          BEQ     LD2F3
											;
D2C0:          LDAA    L0006				; COOL VALUE
D2C2:          CMPA    L402C
D2C5:          BLS     LD2D7

D2C7:          LDD     L00FD				; RUN TIMER
D2C9:          CPD     L402D
D2CD:          BHI     LD2D7
D2CF:          LDAA    #$00FF
D2D1:          STAA    L01D6 				; PURGE D.C

D2D4:          JMP     LD3A4
 

D2D7:  LD2D7   BRSET   L0046,#$08,LD2F3		; BR IF b3, DECEL FUEL C/O
											;
D2DB:          LDAA    L0006				; COOL VALUE
D2DD:          CMPA    L402B				; ENABLE CCP IF COOL G.T. 50c
D2E0:          BLS     LD2F3				;
											;

            ;----------------------
            ; CCP OFF TO ON PARAMS
            ;----------------------
D2E2:          LDX     #$4030				; INDEX CCP OFF TO ON PARAMS

D2E5:          BRCLR   L0041,#$80,LD2EC		; BR IF NOT b3, CCP SOLENOID ON
											;
            ;----------------------
            ; CCP ON TO OFF PARAMS
            ;----------------------
D2E9:          LDX     #$4033				; INDEX CCP ON TO OFF PARAMS

D2EC:  LD2EC   LDAB    L0284				; MPH/1
D2EF:          CMPB    0,X
D2F1:          BCC     LD307
											;
D2F3:  LD2F3   CLR     L01D6  				; PURGE D.C
D2F6:          CLR     L01D8				; PURGE DELAY TIMER

D2F9:          LDAA    L0284				; MPH/1
D2FC:          CMPA    L402F				; 0 MPH
D2FF:          BCC     LD304				; BR IF Vss GT THRESH
											;
D301:          CLR     L01D7
D304:  LD304   JMP     LD3A4
 

D307:  LD307   LDAB    L01D9				; %TPS
D30A:          CMPB    2,X
D30C:          BCS     LD2F3
											;
D32A:          BHI     LD361				; BR IF 

D30E:          LDAB    L0257
D311:          CMPB    1,X
D313:          BCS     LD2F3
											;
D32A:          BHI     LD361				; BR IF 


        ;--------------------------------------------------
        ; PURGE ALLOWED vs BLM CELL 0 - 20
        ;
        ; DETERMINE IF PURGE ALLOWED IN EACH CELL
        ;
        ; 0 = FALSE
        ; 1 = TRUE
        ;--------------------------------------------------
D315:          LDX     #$4058				; PURGE ALLOWED vs BLM CELL
D318:          LDAB    L0247			 	; BLM CELL
D31B:          ABX     						; ADJ INDEX FOR BLM CELL NUMBER
D31C:          LDAA    0,X					; GET 1/0 FLAG
D31E:          BEQ     LD2F3				; BR IF Z
											;
D320:          BRCLR   L003E,#$80,LD366		; BR IF NOT b7, CLOSED LOOP
											;
D32A:          BHI     LD361				; BR IF 

D324:          LDAB    L01C9				; Kpa VACUUM
D327:          CMPB    L4024				; IF VAC L.T. __ Kpa NO UPDATE OF PURGE MULT
D32A:          BHI     LD361				; BR IF 

D32C:          LDAA    L0005
D32E:          BITA    #$C0
D330:          BNE     LD361
											;
D332:          LDAB    L01D8				; PURGE DELAY TIMER
D335:          CMPB    L4025				; 0,4 SEC'S DELAY BETWEEN UPDATEDS OF PURGE MULT
D338:          BCC     LD33F				; BR IF
											;
D33A:          INC     L01D8				; PURGE DELAY TIMER

D33D:          BRA     LD381



D33F:  LD33F   LDAA    L01D7

D342:          LDAB    L020F				; INTEGRATOR COUNTS
D345:          CMPB    L4026
D348:          BCC     LD357				; BR IF
											;
D34A:          CMPB    L4027
D34D:          BCC     LD361
D34F:          SUBA    L402A
D352:          BCC     LD35E				; BR IF
											;
D354:          CLRA    

D355:          BRA     LD35E


D357:  LD357   ADDA    L4029				; 0.05 FACTOR INCREMENT TO PURGE MULT
D35A:          BCC     LD35E				; BR IF 
											;
D35C:          LDAA    #255
D35E:  LD35E   STAA    L01D7
D361:  LD361   CLR     L01D8				; PURGE DELAY TIMER

D364:          BRA     LD381

    		;--------------------------------------------------
    		; CCP DUTY CYCLE MINIMUM vs AIR FLOW (CLSD LOOP)
    		;
    		; TBL = 2.56 * %D.C.
    		;--------------------------------------------------
D366:  LD366   LDX     #$4047				; CCP DUTY CYCLE MINIMUM
D369:          LDAA    L0232				; AIR FLOW
D36C:          JSR     LF4C1				; 2d LK UP

D36F:          LDAB    L4028
D372:          MUL     
D373:          ADDD    #64
D376:          ASLD    
D377:          BCC     LD37C				; BR IF 
											;
D379:          LDD     #$FFFF
D37C:  LD37C   STAA    L01D6 				; PURGE D.C

D37F:          BRA     LD3A4
 

    		;----------------------------------------------
    		; CCP DUTY CYCLE vs AIR FLOW (CLSD LOOP)
    		;
    		; TBL = 2.56 * %D.C.
    		;----------------------------------------------
D381:  LD381   LDX     #$4036				; CCP DUTY CYCLE vs AIR FLOW (CLSD LOOP)
D384:          LDAA    L0232				; AIR FLOW
D387:          JSR     LF4C1				; 2d LK UP

D38A:          LDAB    L01D7
D38D:          MUL     
D38E:          ADCA    #$00
D390:          STAA    L01D6 				; PURGE D.C

    		;----------------------------------------------
    		; CCP DUTY CYCLE MINIMUM vs AIR FLOW (CLSD LOOP)
    		;
    		; TBL = 2.56 * %D.C.
    		;----------------------------------------------
D393:          LDX     #$4047				; CCP DUTY CYCLE MINIMUM
D396:          LDAA    L0232				; AIR FLOW
D399:          JSR     LF4C1				; 2d LK UP
			   
D39C:          CMPA    L01D6 				; PURGE D.C
D39F:          BLS     LD3A4				; BR IF 
											;
D3A1:          STAA    L01D6 				; PURGE D.C

D3A4:  LD3A4   BCLR    L0041,#$80			; CLR b7

D3A7:          LDAA    L01D6  				; PURGE D.C
D3AA:          BEQ     LD3AF				; BR IF 
											;
D3AC:          BSET    L0041,#$80			; SET b7

D3AF:  LD3AF   RTS     
 		;------------------------------------------

			;----------------------------------------------
			; AFR MD BYTE 5,	 0001 0000, (DIG I/O)
			;
			; b7 1 = MAN, (0 = TCC)
			; b6 1 = TCC (Non Elect xmish)
			; b5 1 = Not Used 
			; b4 1 = CONV OVER HEAT PROTECTION
			;
			; b3 1 = BURST KNOCK RETARD
			; b2 1 = A/C CLUTCH CNT'L, 0 = CPI TUNE
			; b1 1 = Not Used
			; b0 1 = 1 DO RPM/MPH LMT, (GOV'R OPT)
			;
			;----------------------------------------------
D3B0:  LD3B0   LDX     #$400F
D3B3:          BRSET   0,X,#$10,LD3BA
D3B7:          JMP     LD471
 ;
D3BA:  LD3BA   LDAA    L0002				; MAJOR LOOP COUNTER
D3BC:          CMPA    #$05
D3BE:          BNE     LD3C4

D3C0:          BRSET   L004F,#$80,LD3C7		; BR IF b7, ENGINE RUNNING
											;
D3C4:  LD3C4   JMP     LD471
 ;
D3C7:  LD3C7   LDAA    L01D9				; %TPS
D3CA:          CMPA    L4074
D3CD:          BHI     LD3D4
D3CF:          CLR     L007E
D3D2:          BRA     LD3EC
 ;
D3D4:  LD3D4   LDAA    L0062				; ENGINE RPM/25
D3D6:          CMPA    L4075
D3D9:          BCC     LD3E2
D3DB:          LDAA    L007E
D3DD:          INCA    
D3DE:          BEQ     LD3E2
D3E0:          STAA    L007E
D3E2:  LD3E2   LDAA    L007E
D3E4:          CMPA    L4076
D3E7:          BCS     LD3EC
D3E9:          JMP     LD471
 
    	;---------------------------------------------
    	; CAT CONVERTER TEMPERATURE FILT COEF vs AIR FLOW
    	;
    	;  Dissassemby of BMHM
    	;
    	; USED W/LAG FILTER & TBL'S L4084, L408B
    	; 
    	; TABLE = 
    	;---------------------------------------------
D3EC:  LD3EC   LDAA    L0232				; AIR FLOW
D3EF:          TAB     

D3F0:          LDX     #$4077				; CAT CONVERTER TEMPERATURE FILT COEF 

D3F3:          JSR     LF4C1				; 2d LK UP

D3F6:          STAA    L007C				; SAVE CAT FILT COEF


    	;---------------------------------------------
    	; RPM REACTION TEMP COMPONENT vs RPM & AIR FLOW
    	;
    	;  Dissassemby of BMHM
    	;
    	; TBL = ( DEG C - 300)/3
    	;---------------------------------------------
D3F8:          LDAA    L0062				; ENGINE RPM/25
D3FA:          LSRA    
D3FB:          LDX     #$408F
D3FE:          JSR     LF4DE				; 3d LK UP

D401:          STAA    L007B

D403:          LDAA    L024A				; AFR
D406:          CMPA    #155					;
D408:          BLS     LD40C				; BR IF LT 15.5 AFR
											;
D40A:          LDAA    #155
D40C:  LD40C   SUBA    #107
D40E:          BCC     LD411
											;
D410:          CLRA    
    	;---------------------------------------------
		; ENDO/EXOTHERMIC REACTION TEMPERATURE 
		; COMPONENT vs AFR
		;
		; TBL = (DEG C/3) + 128
    	;---------------------------------------------
D411:  LD411   ASLA    						; AFR x 2
D412:          LDX     #$4088				; ENDO/EXOTHERMIC REACTION TEMP
D415:          JSR     LF4C1				; 2d LK UP

D418:          STAA    L007D
D41A:          SUBA    #128
D41C:          BMI     LD426
											;
D41E:          ADDA    L007B
D420:          BCC     LD42B
											;
D422:          LDAA    #255

D424:          BRA     LD42B



D426:  LD426   ADDA    L007B
D428:          BCS     LD42B				; BR IF OVERFLOW

D42A:          CLRA    
D42B:  LD42B   STAA    L007A

D42D:          LDAA    L007A
D42F:          LDAB    L007C				; CAT FILT COEF
D431:          LDX     L0078				; CAT TEMP
D433:          JSR     LF459				; LAG FILT
D436:          STD     L0078				; FILTERED CAT TEMP

D438:          BRCLR   L003E,#$80,LD459		; BR IF NOT b7,	CLOSED LOOP
											;
D43C:          LDAB    L0078				; CAT TEMP
D43E:          CMPB    L406D				; 786 Deg c CAT OVER TEMP UPPER 1ST HYST PR
D441:          BLS     LD454				; BR IF CAT TEMP LT THRESH
D443:          LDAA    L084C				; CAT CONV TMR
D446:          INCA    						; INCR CAT TIMER
D447:          BNE     LD44A
D449:          DECA    						; DECR CAT TIMER
D44A:  LD44A   STAA    L084C				; CAT CONV TMR
D44D:          CMPA    L4073				; 60 Sec, IF CONV TMR G.T. or E.Q. thresh USE AFR FM TBL 
D450:          BCC     LD46E				; BR 
D452:          BRA     LD45F
 ;
D454:  LD454   CMPB    L406E				; 726 Deg c CAT OVER TEMP LOWER 1ST HYST PR
D457:          BHI     LD45F
D459:  LD459   CLRA    
D45A:          STAA    L084C				; CAT CONV TMR
D45D:          BRA     LD469
 ;
D45F:  LD45F   CMPB    L406F				; 819 Deg c CAT OVER TEMP UPPER 2ND HYST PR 
D462:          BHI     LD46E
D464:          CMPB    L4070				; 726 Deg c CAT OVER TEMP LOWER 2ND HYST PR
D467:          BHI     LD471
D469:  LD469   BCLR    L0052,#$40			; CLR b6, 
D46C:          BRA     LD471
 ;
D46E:  LD46E   BSET    L0052,#$40			; SET b6
D471:  LD471   RTS     

			;------------------------------
			; AFR MD BYTE 4,	 0000 0011 
			;
			; b7 1 = Not Used
			; b6 1 = Not Used
			; b5 1 = LATCH ERR 45
			; b4 1 = USE L4979 WITH ASYNC FUEL DELIVERY
			;
			; b3 1 = CPI MANAFOLD TUNE CNT'L
			; b2 1 = SHIFT LIGHT ENABLE 
			; b1 1 = USE ALT CMAP vs
			;    MAP LD FOR FUEL CUR HYST PAIR
			; b0 1 = USE ALT CMAP vs
			;    MAP LD & AD MAP FOR BLM ENABLE 
			;------------------------------
D472:  LD472   LDX     #$400E				; AFR MD BYTE 4, 0000 0011 
D475:          BRSET   0,X,#$08,LD47B		; BR IF b3, 1 = CPI MANAFOLD TUNE CNT'L 

D479:          BRA     LD49F
 ;
D47B:  LD47B   LDX     #$412B
D47E:          BRSET   L0052,#$08,LD489		; BR IF b3,
D482:          LDAA    L00A8
D484:          CMPA    6,X
D486:          BCS     LD49F
D488:          INX     
D489:  LD489   LDAA    L0062				; ENGINE RPM/25
D48B:          CMPA    0,X
D48D:          BLS     LD49F
D48F:          CMPA    2,X
D491:          BHI     LD49F
D493:          LDAA    L01D9				; %TPS
D496:          CMPA    4,X
D498:          BLS     LD49F
D49A:          BSET    L0052,#$08
D49D:          BRA     LD4A2
 ;
D49F:  LD49F   BCLR    L0052,#$08
D4A2:  LD4A2   RTS     
 ; ------------------------------------------
D4A3:  LD4A3   LDAB    L080C
D4A6:          BNE     LD4B6
D4A8:          CLRA    
D4A9:          LDAB    L0811
D4AC:          BEQ     LD4B1
D4AE:          DECB    
D4AF:          BNE     LD4D6
D4B1:  LD4B1   STD     L0812				; Vss/1
D4B4:          BRA     LD4D6
 ;
D4B6:  LD4B6   LDAA    L0811
D4B9:          BEQ     LD4CB
D4BB:          LDAA    #$00E6
D4BD:          MUL     
D4BE:          ASLD    
D4BF:          XGDX    
D4C0:          LDD     L080D
D4C3:          SUBD    L080F
D4C6:          XGDX    
D4C7:          FDIV    
D4C8:          STX     L0812				; Vss/1
D4CB:  LD4CB   CLR     L080C
D4CE:          LDX     L080D
D4D1:          STX     L080F
D4D4:          LDAB    #$0027
D4D6:  LD4D6   STAB    L0811

D4D9:          RTS     
 		;---------------------------------------------

		;
		; FILTER Vss
		;
D4DA:  LD4DA   LDD     L0812				; NEW MPH/1
D4DD:          LDX     L0284				; OLD MPH/1
D4E0:          LDY     #$4E8E				; LAG FILTER COEF FOR Vss (02A5)FILT MPH
D4E4:          JSR     LF436 				; LAG FILTER SUB ROUTINE, XMSIH

D4E7:          STD     L0284				; SAVE FILT MPH/1

D4EA:          RTS     
 		;---------------------------------------------


D4EB:  LD4EB   JSR     LE684
D4EE:          JSR     LE6AC
D4F1:          JSR     LE69C
D4F4:          CLRA    
D4F5:          STAA    L0084
D4F7:          LDAB    L00D9  				; CURRENT GEAR
D4F9:          CMPB    #$03
D4FB:          BCC     LD557
 		;---------------------------------------------


		;---------------------------------------------
		;
		;
		;---------------------------------------------
D4FD:          LDX     #$D787				; TABLE <------
D500:          JSR     LD8F0				;
D503:          BEQ     LD50A				;
											;
D505:          BSET    L0084,#$08			; SET b3
											;			
D508:          BRA     LD53E
 		;---------------------------------------------


		;---------------------------------------------
		;
		;
		;---------------------------------------------
D50A:  LD50A   LDX     #$D763				; TABLE <------
D50D:          JSR     LD8CE				;
D510:          BCS     LD517				;
											;
D512:          BSET    L0084,#$04			; SET b2

D515:          BRA     LD53E
 		;---------------------------------------------


		;---------------------------------------------
		;
		;
		;---------------------------------------------
D517:  LD517   BRCLR   L009C,#$10,LD532		; BR IF NOT b4, 
D51B:          LDY     #$D69F				; TABLE 
D51F:          JSR     LD840
D522:          BCS     LD532
											;
D524:          PSHA
 		;---------------------------------------------


		;---------------------------------------------
		;
		;
		;---------------------------------------------
D525:          LDY     #$D6B7				; TABLE	 <------
D529:          JSR     LD8A7
D52C:          PULA    						
D52D:          BSET    L0084,#$02

D530:          BRA     LD541
 		;---------------------------------------------


		;---------------------------------------------
		;
		;
		;---------------------------------------------
D532:  LD532   LDY     #$D69F				; TABLE <--------
D536:          JSR     LD7E5
D539:          BCS     LD557
											;
D53B:          BSET    L0084,#$01
D53E:  LD53E   LDX     #$0000

D541:  LD541   LDAB    #$0001
D543:          CMPA    #$00FF
D545:          BEQ     LD557
											;
D547:          CMPA    L00D7
D549:          BHI     LD557
											;
D54B:          BRCLR   L0099,#$20,LD552
											;
D54F:          LDX     #$0000
D552:  LD552   CPX     L01AC
D555:          BLS     LD5A0
											;
D557:  LD557   CLRA    						
D558:          LDAB    L00D9   				; CURRENT GEAR
D55A:          DECB    						
D55B:          BMI     LD59F
											;
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D55D:          LDX     #$D79B
D560:          JSR     LD8F0

D563:          BEQ     LD56A				;

D565:          BSET    L0084,#$80
D568:          BRA     LD595
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D56A:  LD56A   LDX     #$D775
D56D:          JSR     LD8CE

D570:          BCS     LD577				;

D572:          BSET    L0084,#$40
D575:          BRA     LD595
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D577:  LD577   BRCLR   L009C,#$10,LD589		; BR IF NOT b4
D57B:          LDY     #$D6AB
D57F:          JSR     LD840

D582:          BCS     LD589
											;
D584:          BSET    L0084,#$20
D587:          BRA     LD595
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D589:  LD589   LDY     #$D6AB
D58D:          JSR     LD7E5
D590:          BCS     LD59F
											;
D592:          BSET    L0084,#$10
D595:  LD595   LDAB    #255

D597:          CMPA    #0
D599:          BEQ     LD59F
											;
D59B:          CMPA    L00D7
D59D:          BHI     LD5A0
											;
D59F:  LD59F   CLRB    
D5A0:  LD5A0   ADDB    L00D9  				; CURRENT GEAR
D5A2:          CMPB    L00D9  				; CURRENT GEAR
D5A4:          BEQ     LD5A9
											;
D5A6:          STAA    L0187

D5A9:  LD5A9   BRSET   L0087,#$01,LD5B1
											;
D5AD:          BRCLR   L0098,#$80,LD5B7
											;
D5B1:  LD5B1   CMPB    #$02
D5B3:          BLS     LD5B7
											;
D5B5:          LDAB    #$02
D5B7:  LD5B7   BRCLR   L0099,#$08,LD5BD
											;
D5BB:          LDAB    #$01
D5BD:  LD5BD   BRCLR   L0099,#$01,LD5D5
											;
D5C1:          CMPB    L00D9  				; CURRENT GEAR
D5C3:          BLS     LD5CB
											;
D5C5:          CMPB    #$01
D5C7:          BLS     LD5D5
											;
D5C9:          BRA     LD5D3
 ;
D5CB:  LD5CB   CMPB    L00D9  				; CURRENT GEAR
D5CD:          BCC     LD5D5
											;
D5CF:          CMPB    #$01
D5D1:          BCC     LD5D5
											;
D5D3:  LD5D3   LDAB    L00D9  				; CURRENT GEAR
D5D5:  LD5D5   BRCLR   L0099,#$01,LD5E6
											;
D5D9:          CMPB    #$01
D5DB:          BNE     LD5E6
											;
D5DD:          LDAA    L00D7
D5DF:          CMPA    L5D39
D5E2:          BCS     LD5E6
											;
D5E4:          LDAB    #$03
D5E6:  LD5E6   BRSET   L0098,#$08,LD5EE
											;
D5EA:          BRCLR   L0099,#$02,LD5F0
											;
D5EE:  LD5EE   LDAB    #$01
D5F0:  LD5F0   BCLR    L0083,#$24
D5F3:          CMPB    L00D9  				; CURRENT GEAR
D5F5:          BEQ     LD601
											;
D5F7:          BCS     LD5FE
											;
D5F9:          BSET    L0083,#$04

D5FC:          BRA     LD601

D5FE:  LD5FE   BSET    L0083,#$20
D601:  LD601   BRCLR   L0083,#$20,LD617
D605:          LDAA    L00D9   				; CURRENT GEAR
D607:          CMPA    #$02
D609:          BNE     LD617
											;
D60B:          BRSET   L0083,#$40,LD623
											;
D60F:          BSET    L0083,#$40
D612:          BCLR    L0083,#$80

D615:          BRA     LD623


D617:  LD617   BCLR    L0083,#$40

D61A:          LDAA    L0135
D61D:          INCA    
D61E:          BEQ     LD623
											;
D620:          STAA    L0135

D623:  LD623   BRSET   L0083,#$04,LD65C
											;
D627:          BRCLR   L0083,#$20,LD65C
											;
D62B:          LDAA    L00D9  				; CURRENT GEAR
D62D:          CMPA    #$03
D62F:          BNE     LD634
											;
D631:          CLR     L0135

D634:  LD634   BRCLR   L0083,#$40,LD652
											;
D638:          LDAA    L0135
D63B:          CMPA    L5D32
D63E:          BLS     LD652
											;
D640:          CMPA    L5D33
D643:          BCC     LD652
											;
D645:          LDAA    L0118
D648:          BNE     LD652
											;
D64A:          LDAA    L0134
D64D:          CMPA    L5D31				; 0 SEC'S, 3 -> 2 shift delay
D650:          BCS     LD65A
											;
D652:  LD652   LDAA    L0125
D655:          CMPA    L5D30				; 0 SEC'S, TCC off time prior to dn shift
D658:          BCC     LD65C
											;
D65A:  LD65A   LDAB    L00D9  				; CURRENT GEAR
D65C:  LD65C   TBA     
D65D:          BCLR    L0085,#$20
D660:          BRCLR   L00A2,#$04,LD670
											;
D664:          CMPB    #$03
D666:          BNE     LD670
											;
D668:          TST     L0197
D66B:          BEQ     LD670
											;
D66D:          BSET    L0085,#$20
D670:  LD670   JSR     LE562
D673:          BCLR    L0083,#$09

D676:          LDAB    L0103
D679:          BEQ     LD68E
											;
D67B:          DECB    
D67C:          CMPB    #$03
D67E:          BLS     LD686
											;
D680:          LDAB    #$04
D682:          STAB    L0103
D685:          DECB    
D686:  LD686   LDAA    #255
D688:          STAA    L0187

D68B:          TBA     
D68C:          BRA     LD69C


D68E:  LD68E   CMPA    L00D9   				; CURRENT GEAR
D690:          BEQ     LD69E
											;
D692:          BCS     LD699
											;
D694:          BSET    L0083,#$01
D697:          BRA     LD69C
 ;
D699:  LD699   BSET    L0083,#$08
D69C:  LD69C   STAA    L00D9  				; CURRENT GEAR
D69E:  LD69E   RTS     
	 	;----------------------------------------------

		;----------------------------------------------
		; TABLE 
		;
		;----------------------------------------------
LD69F   FDB $D6F7   ;
LD6A1   FDB $D717   ;
LD6A3   FDB $D7C1   ;
LD6A5   FDB $D6BD   ;
LD6A7   FDB $D6D1   ;
LD6A9   FDB $D7AF   ;
LD6AB   FDB $D71D   ;
LD6AD   FDB $D73D   ;
LD6AF   FDB $D7C1   ;
LD6B1   FDB $D6D7   ;
LD6B3   FDB $D6EB   ;
LD6B5   FDB $D7AF   ;
		;----------------------------------------------
		;----------------------------------------------
LD6B7   FDB $D743   ;
LD6B9   FDB $D6F1   ;
LD6BB   FDB $D7D3   ;


LD6BD   FDB $0406   ;
LD6BF   FDB $5D6E   ;
LD6C1   FDB $5D7F   ;
LD6C3   FDB $5D90   ;
LD6C5   FDB $5DD4   ;
LD6C7   FDB $5DE5   ;
LD6C9   FDB $5DF6   ;
LD6CB   FDB $5E3A   ;
LD6CD   FDB $5E4B   ;
LD6CF   FDB $5E5C   ;

LD6D1   FDB $5EA0   ;
LD6D3   FDB $5EB1   ;
LD6D5   FDB $5EC2   ;

LD6D7   FDB $0406   ;
LD6D9   FDB $5DA1   ;
LD6DB   FDB $5DB2   ;
LD6DD   FDB $5DC3   ;
LD6DF   FDB $5E07   ;
LD6E1   FDB $5E18   ;
LD6E3   FDB $5E29   ;
LD6E5   FDB $5E6D   ;
LD6E7   FDB $5E7E   ;
LD6E9   FDB $5E8F   ;

LD6EB   FDB $5ED3   ;
LD6ED   FDB $5EE4   ;
LD6EF   FDB $5EF5   ;
LD6F1   FDB $5D5C   ;
LD6F3   FDB $5D5E   ;
LD6F5   FDB $5D60   ;

LD6F7   FDB $1006   ;
LD6F9   FDB $5D44   ;
LD6FB   FDB $5D45   ;
LD6FD   FDB $5D46   ;
LD6FF   FDB $5D4A   ;
LD701   FDB $5D4B   ;
LD703   FDB $5D4C   ;
LD705   FDB $5D3E   ;
LD707   FDB $5D3F   ;
LD709   FDB $5D40   ;
LD70B   FDB $5D3E   ;
LD70D   FDB $5D3F   ;
LD70F   FDB $5D40   ;
LD711   FDB $5D3E   ;
LD713   FDB $5D3F   ;
LD715   FDB $5D40   ;

LD717   FDB $5D50   ;
LD719   FDB $5D51   ;
LD71B   FDB $5D52   ;
LD71D   FDB $1006   ;
LD71F   FDB $5D47   ;
LD721   FDB $5D48   ;
LD723   FDB $5D49   ;
LD725   FDB $5D4D   ;
LD727   FDB $5D4E   ;
LD729   FDB $5D4F   ;
LD72B   FDB $5D41   ;
LD72D   FDB $5D42   ;
LD72F   FDB $5D43   ;
LD731   FDB $5D41   ;
LD733   FDB $5D42   ;
LD735   FDB $5D43   ;
LD737   FDB $5D41   ;
LD739   FDB $5D42   ;
LD73B   FDB $5D43   ;
LD73D   FDB $5D53   ;
LD73F   FDB $5D54   ;
LD741   FDB $5D55   ;
LD743   FDB $1006   ;
LD745   FDB $5D68   ;
LD747   FDB $5D6A   ;
LD749   FDB $5D6C   ;
LD74B   FDB $5D62   ;
LD74D   FDB $5D64   ;
LD74F   FDB $5D66   ;
LD751   FDB $5D56   ;
LD753   FDB $5D58   ;
LD755   FDB $5D5A   ;
LD757   FDB $5D56   ;
LD759   FDB $5D58   ;
LD75B   FDB $5D5A   ;
LD75D   FDB $5D56   ;
LD75F   FDB $5D58   ;
LD761   FDB $5D5A   ;
LD763   FDB $5D3C   ;
LD765   FDB $5D3B   ;
LD767   FDB $5D3B   ;
LD769   FDB $0000   ;
LD76B   FDB $5D3B   ;
LD76D   FDB $5D3B   ;
LD76F   FDB $0000   ;
LD771   FDB $0000   ;
LD773   FDB $0000   ;
LD775   FDB $5D3D   ;
LD777   FDB $5D3A   ;
LD779   FDB $5D3A   ;
LD77B   FDB $0000   ;
LD77D   FDB $5D3A   ;
LD77F   FDB $5D3A   ;
LD781   FDB $0000   ;
LD783   FDB $0000   ;
LD785   FDB $0000   ;
LD787   FDB $0406   ;
LD789   FDB $0104   ;
LD78B   FDB $0105   ;
LD78D   FDB $0106   ;
LD78F   FDB $0104   ;
LD791   FDB $0105   ;
LD793   FDB $0106   ;
LD795   FDB $0104   ;
LD797   FDB $0105   ;
LD799   FDB $0106   ;
LD79B   FDB $0406   ;
LD79D   FDB $0107   ;
LD79F   FDB $0108   ;
LD7A1   FDB $0109   ;
LD7A3   FDB $0107   ;
LD7A5   FDB $0108   ;
LD7A7   FDB $0109   ;
LD7A9   FDB $0107   ;
LD7AB   FDB $0108   ;
LD7AD   FDB $0109   ;

LD7AF   FDB $0208   ;
LD7B1   FDB $0000   ;
LD7B3   FDB $0000   ;
LD7B5   FDB $0000   ;
LD7B7   FDB $0000   ;
LD7B9   FDB $5D38   ;
LD7BB   FDB $5D38   ;
LD7BD   FDB $5D38   ;
LD7BF   FDB $5D38   ;
					;
LD7C1   FDB $0208   ;
LD7C3   FDB $0000   ;
LD7C5   FDB $0000   ;
LD7C7   FDB $0000   ;
LD7C9   FDB $0000   ;
LD7CB   FDB $5D38   ;
LD7CD   FDB $5D38   ;
LD7CF   FDB $5D38   ;
LD7D1   FDB $5D38   ;
LD7D3   FDB $0208   ;
LD7D5   FDB $0000   ;
LD7D7   FDB $0000   ;
LD7D9   FDB $0000   ;
LD7DB   FDB $0000   ;
LD7DD   FDB $5D38   ;
LD7DF   FDB $5D38   ;
LD7E1   FDB $5D38   ;
LD7E3   FDB $5D38   ;
		;--------------------------------------------------

														   	
		;--------------------------------------------------
		; USE LD69F TABLE 
		;
		;--------------------------------------------------
D7E5:  LD7E5   PSHB    
D7E6:          CLRA    
D7E7:          PSHA    
D7E8:          PSHA    
D7E9:          PSHA    
D7EA:          LDX     8,Y
D7ED:          ABX     
D7EE:          ABX     
D7EF:          LDX     0,X
D7F1:          BEQ     LD805
D7F3:          LDAA    L00B2
D7F5:          JSR     LF4C1				; 2d LK UP

D7F8:          SUBA    #128

D7FA:          LDAB    0,X
D7FC:          SUBB    #128
D7FE:          TSX     
D7FF:          STAB    2,X
D801:          STAA    0,X
D803:          LDAB    3,X
D805:  LD805   LDX     6,Y
D808:          LDAA    L0080
D80A:          JSR     LD8FE

D80D:          LDAA    #$0000
D80F:          BCC     LD816

D811:          PULB    
D812:          PULB    
D813:          PULB    
D814:          BRA     LD83E
 ;
D816:  LD816   LDAA    L00B2
D818:          JSR     LF4C1				; 2d LK UP
D81B:          LDAB    0,X
D81D:          TSX     
D81E:          STAB    $0001,X
D820:          CLRB    
D821:          XGDX    
D822:          PULA    
D823:          CLRB    
D824:          JSR     LD980
D827:          LDX     $000A,Y
D82A:          JSR     LD92E
D82D:          XGDX    
D82E:          PULA    
D82F:          CLRB    
D830:          XGDX    
D831:          TAB     
D832:          PULA    
D833:          PSHB    
D834:          CLRB    
D835:          JSR     LD980
D838:          PULB    
D839:          CBA     
D83A:          BCC     LD83E
D83C:          TBA     
D83D:          CLC     
D83E:  LD83E   PULB    
D83F:          RTS     
 		;---------------------------------------------


		;---------------------------------------------
		;
		;
		;---------------------------------------------
D840:  LD840   PSHB    
D841:          CLRA    
D842:          PSHA    
D843:          PSHA    
D844:          PSHA    
D845:          LDX     $0002,Y
D848:          ABX     
D849:          ABX     
D84A:          LDX     0,X
D84C:          BEQ     LD855
D84E:          LDAA    0,X
D850:          SUBA    #$0080
D852:          TSX     
D853:          STAA    0,X
D855:  LD855   LDX     $0008,Y
D858:          ABX     
D859:          ABX     
D85A:          LDX     0,X
D85C:          BEQ     LD865
D85E:          LDAA    0,X
D860:          SUBA    #$0080
D862:          TSX     
D863:          STAA    $0002,X
D865:  LD865   LDX     $0006,Y
D868:          LDAA    L0080
D86A:          JSR     LD8FE
D86D:          BCS     LD874
D86F:          LDAA    0,X
D871:          TSX     
D872:          STAA    $0001,X
D874:  LD874   LDX     0,Y
D877:          LDAA    L0081
D879:          JSR     LD8FE
D87C:          LDAA    #$0000
D87E:          BCC     LD885
D880:          PULB    
D881:          PULB    
D882:          PULB    
D883:          BRA     LD8A5
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D885:  LD885   LDAA    0,X
D887:          CLRB    
D888:          XGDX    
D889:          PULA    
D88A:          CLRB    
D88B:          JSR     LD980
D88E:          LDX     4,Y
D891:          JSR     LD92E
D894:          XGDX    
D895:          PULA    
D896:          CLRB    
D897:          XGDX    
D898:          TAB     
D899:          PULA    
D89A:          PSHB    
D89B:          CLRB    
D89C:          JSR     LD980
D89F:          PULB    
D8A0:          CBA     
D8A1:          BCC     LD8A5
D8A3:          TBA     
D8A4:          CLC     
D8A5:  LD8A5   PULB
    
D8A6:          RTS     
 		;---------------------------------------------

		;---------------------------------------------
		;  INDEX TO LD6B7 TABLE 
		;
		;---------------------------------------------
D8A7:  LD8A7   PSHB    
D8A8:          LDX     $0002,Y
D8AB:          ABX     
D8AC:          ABX     
D8AD:          LDX     0,X
D8AF:          BEQ     LD8B3
D8B1:          LDX     0,X
D8B3:  LD8B3   PSHX    
D8B4:          LDX     0,Y
D8B7:          LDAA    L0081
D8B9:          JSR     LD8FE
D8BC:          BCS     LD8C0
D8BE:          LDX     0,X
D8C0:  LD8C0   PULA    
D8C1:          PULB    
D8C2:          JSR     LD980
D8C5:          LDX     $0004,Y
D8C8:          JSR     LD92E
D8CB:          XGDX    
D8CC:          PULB    
D8CD:          RTS     
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D8CE:  LD8CE   PSHB    
D8CF:          BRSET   L0098,#$04,LD8EC
D8D3:          LDAA    L00A2
D8D5:          ANDA    #$07
D8D7:          BEQ     LD8EC
D8D9:          LSRA    
D8DA:          PSHB    
D8DB:          LDAB    #$0003
D8DD:          MUL     
D8DE:          PULA    
D8DF:          ABA     
D8E0:          ASLA    
D8E1:          TAB     
D8E2:          ABX     
D8E3:          LDX     0,X
D8E5:          BEQ     LD8EC
D8E7:          LDAA    0,X
D8E9:          CLC     
D8EA:          BRA     LD8EE
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D8EC:  LD8EC   CLRA    
D8ED:          SEC     
D8EE:  LD8EE   PULB    
D8EF:          RTS     
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D8F0:  LD8F0   PSHB    
D8F1:          LDAA    L0080
D8F3:          BSR     LD8FE
D8F5:          BCC     LD8FA

D8F7:          CLRA    
D8F8:          BRA     LD8FC
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D8FA:  LD8FA   LDAA    0,X
D8FC:  LD8FC   PULB    
D8FD:          RTS     
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D8FE:  LD8FE   PSHB    
D8FF:          PSHA
    
D900:          LDAA    0,X
D902:          PSHA    

D903:          LDAA    $0001,X
D905:          PSHA    

D906:          ASLB    
D907:          ABX     
D908:          LDAA    #$0001

D90A:          INX     
D90B:          INX     
D90C:          PULB    

D90D:  LD90D   PSHX    

D90E:          TSX     
D90F:          BITA    $0003,X
D911:          BNE     LD91E

D913:          BITA    $0002,X
D915:          BNE     LD925

D917:          ASLA    
D918:          BCS     LD925

D91A:          PULX    
D91B:          ABX     
D91C:          BRA     LD90D
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D91E:  LD91E   PULX    
D91F:          LDX     0,X
D921:          BEQ     LD926
D923:          BRA     LD929
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D925:  LD925   PULX    
D926:  LD926   SEC     
D927:          BRA     LD92A
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D929:  LD929   CLC     
D92A:  LD92A   INS     
D92B:          PULA    
D92C:          PULB    
D92D:          RTS     
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D92E:  LD92E   PSHB    
D92F:          PSHA    
D930:          LDAB    L00D9  				; CURRENT GEAR
D932:          LDAA    L0082
D934:          JSR     LD8FE

D937:          BCS     LD948

D939:          JSR     LD94B

D93C:          TSX     
D93D:          JSR     LF550				; MUL 8X16 Subroutine

D940:          ASLD    
D941:          BCC     LD946
D943:          LDD     #$FFFF
D946:  LD946   PULX    
D947:          RTS     
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D948:  LD948   PULA    
D949:          PULB    
D94A:          RTS     
 		;---------------------------------------------

		;---------------------------------------------
		;
		;
		;---------------------------------------------
D94B:  LD94B   CLRA    
D94C:          LDAB    0,X
D94E:          SUBB    #$80
D950:          PSHB    
D951:          BPL     LD955
D953:          NEGB    
D954:          DECA    
D955:  LD955   PSHA    
D956:          LDAA    L00AC
D958:          MUL     
D959:          ASLD    
D95A:          TSX     
D95B:          TST     0,X
D95D:          BEQ     LD963
D95F:          NEGA    
D960:          NEGB    
D961:          SBCA    #$00
D963:  LD963   SUBA    1,X
D965:          ADDA    #$80
D967:          PULX    
D968:          RTS     
 ; ------------------------------------------
D969:  LD969   LDAA    L00AC
D96B:          SUBA    #$80
D96D:          LDAB    0,X
D96F:          MUL     
D970:          TST     L00AC
D973:          BMI     LD977
D975:          SUBA    0,X
D977:  LD977   ADDA    #$40
D979:  LD979   BGT     LD97E
D97B:          LDD     #$0000
D97E:  LD97E   ASLD    
D97F:          RTS     
 ; ------------------------------------------
D980:  LD980   PSHX    
D981:          PSHA    
D982:          TSTA    
D983:          BPL     LD989
D985:          NEGA    
D986:          NEGB    
D987:          SBCA    #$00
D989:  LD989   PSHB    
D98A:          PSHA    
D98B:          TSX     
D98C:          LDAA    L00AB
D98E:          JSR     LF550				; MUL 8X16 Subroutine
D991:          PULX    
D992:          TSX     
D993:          TST     0,X
D995:          BPL     LD99B
D997:          NEGA    
D998:          NEGB    
D999:          SBCA    #$0000
D99B:  LD99B   INS     
D99C:          PSHA    
D99D:          ADDD    $0001,X
D99F:          BCS     LD9AB
D9A1:          PSHA    
D9A2:          ANDA    0,X
D9A4:          PULA    
D9A5:          BPL     LD9B4
D9A7:          CLRA    
D9A8:          CLRB    
D9A9:          BRA     LD9B4
 ;
D9AB:  LD9AB   PSHA    
D9AC:          ORAA    0,X
D9AE:          PULA    
D9AF:          BMI     LD9B4
D9B1:          LDD     #$FFFF
D9B4:  LD9B4   INS     
D9B5:          PULX    
D9B6:          RTS     
 ; ------------------------------------------
D9B7:  LD9B7   BRCLR   L00A2,#$0F,LD9BF
D9BB:          BRCLR   L00A3,#$0F,LD9C7
D9BF:  LD9BF   BRCLR   L00A2,#$20,LD9EF
D9C3:          BRSET   L00A3,#$20,LD9EF
D9C7:  LD9C7   BSET    L00A4,#$01
D9CA:          BCLR    L00A4,#$12
D9CD:          CLR     L015D
D9D0:          BRSET   L00A2,#$20,LD9DB
D9D4:          LDX     #$70D4
D9D7:          BRCLR   0,X,#$01,LD9EC
D9DB:  LD9DB   LDAA    L00D9   				; CURRENT GEAR
D9DD:          CMPA    #$0003
D9DF:          BEQ     LD9EC
D9E1:          CMPA    #$0002
D9E3:          BEQ     LD9EC
D9E5:          LDAA    L00D7
D9E7:          CMPA    L70D3
D9EA:          BLS     LD9EF
D9EC:  LD9EC   BCLR    L00A4,#$01
D9EF:  LD9EF   BRCLR   L00A4,#$03,LDA34
D9F3:          LDAA    L015D
D9F6:          INCA    
D9F7:          BEQ     LD9FC
D9F9:          STAA    L015D
D9FC:  LD9FC   LDD     L01AC
D9FF:          CPD     L70B8
DA03:          BHI     LDA0C
DA05:          LDAA    L00B2
DA07:          CMPA    L70BA
DA0A:          BLS     LDA12
DA0C:  LDA0C   BSET    L00A4,#$02
DA0F:          BCLR    L00A4,#$01
DA12:  LDA12   LDD     L00C2
DA14:          CPD     L70BB
DA18:          BCS     LDA22
DA1A:          LDAA    L015D
DA1D:          CMPA    L70BD
DA20:          BLS     LDA67
DA22:  LDA22   BRCLR   L00A4,#$02,LDA2F
DA26:          BSET    L00A4,#$10
DA29:          LDAA    L70D2
DA2C:          STAA    L015E
DA2F:  LDA2F   BCLR    L00A4,#$03
DA32:          BRA     LDA67
 ;
DA34:  LDA34   LDAA    L00D7
DA36:          CMPA    L70C2			; 
DA39:          BCC     LDA50
DA3B:          LDD     L01AC
DA3E:          CPD     L70BF
DA42:          BLS     LDA50
DA44:          LDAA    L00B2
DA46:          CMPA    L70C1			; 
DA49:          BLS     LDA50
DA4B:          BSET    L00A4,#$04
DA4E:          BRA     LDA67
 ;
DA50:  LDA50   LDAA    L00D7
DA52:          CMPA    L70BE
DA55:          BHI     LDA6B
DA57:          LDD     L01AC
DA5A:          CPD     L70C3			; 
DA5E:          BCS     LDA6B
DA60:          LDAA    L00B2
DA62:          CMPA    L70C5			; 
DA65:          BCS     LDA6B
DA67:  LDA67   BRCLR   L00A2,#$50,LDA6E
DA6B:  LDA6B   BCLR    L00A4,#$04
DA6E:  LDA6E   RTS     
 		; ------------------------------------------
DA6F:  LDA6F   BRSET   L0099,#$10,LDA87		; BR IF b4
											;
DA73:          BRSET   L00A4,#$08,LDAE1		; BR IF b3
											;
DA77:          BRSET   L00A4,#$01,LDA8A		; BR IF b0
											;
DA7B:          BRSET   L00A4,#$02,LDAA3		; BR IF b1
											;
DA7F:          BRSET   L00A4,#$10,LDAA8		; BR IF b4
											;
DA83:          BRSET   L00A4,#$04,LDADB		; BR IF b2
											;
DA87:  LDA87   CLRA    

DA88:          BRA     LDADE

		;--------------------------------------------------
		; 3d TBL .... Vs. MAP  Vs. RPM
		;
		;
		;--------------------------------------------------
DA8A:  LDA8A   LDX     #$55F5
DA8D:          LDAB    L01C0				; GET CURRENT MAP VALUE
DA90:          LDAA    L0061				; RPM/25
DA92:          CMPA    #64					; 1600 RPM
DA94:          BLS     LDA9E
											;
DA96:          LDAA    L0062				; ENGINE RPM/25
DA98:          ADDA    #16					; 400 RPM
DA9A:          BCC     LDA9E

DA9C:          LDAA    #255
DA9E:  LDA9E   JSR     LF4DE				; 3d LK UP

DAA1:          BRA     LDADE


DAA3:  LDAA3   LDAA    L55F3
DAA6:          BRA     LDADE

DAA8:  LDAA8   CLRB    
DAA9:          LDAA    L70D2
DAAC:          XGDX    
DAAD:          CLRB    
DAAE:          LDAA    L015E
DAB1:          FDIV    
DAB2:          XGDX    

DAB3:          LDAB    L55F3				;
DAB6:          MUL     
DAB7:          STAA    L015A
DABA:          DEC     L015E

DABD:          BRCLR   L00A4,#$04,LDAD1
											;
DAC1:          LDAA    L015A				;
DAC4:          CMPA    L55F4				;
DAC7:          BHI     LDAD1
											;
DAC9:          LDAA    L55F4
DACC:          STAA    L015A
DACF:          BRA     LDAD6
 ;
DAD1:  LDAD1   LDAA    L015E
DAD4:          BNE     LDAE1
DAD6:  LDAD6   BCLR    L00A4,#$10
DAD9:          BRA     LDAE1
 ;
DADB:  LDADB   LDAA    L55F4				;
DADE:  LDADE   STAA    L015A				;

DAE1:  LDAE1   RTS     
 		;----------------------------------------------

DAE2:  LDAE2   BRCLR   L00A4,#$17,LDAE9
DAE6:          JMP     LDBE2
 ;
DAE9:  LDAE9   CLRA    
DAEA:          BRCLR   L00A2,#$70,LDAF0	    ;
											;
DAEE:          BRA     LDB65
 ;
DAF0:  LDAF0   BRSET   L0099,#$10,LDB65	    ;
											;
DAF4:          BCLR    L00A4,#$80			;
											;
DAF7:          BRCLR   L0083,#$01,LDB04	    ;
											;
DAFB:          BSET    L00A4,#$08			;
											;
DAFE:          CLR     L015B				;
DB01:          CLR     L015C				;
DB04:  LDB04   BRCLR   L00A4,#$08,LDB65		; BR IF NOT b3
											;
DB08:          BRSET   L0083,#$08,LDB65		; BR IF b3
											;


DB0C:          LDAB    L00D9   				; CURRENT GEAR
DB0E:          ASLB    						;
DB0F:          LDX     #$DBE3				; INDEX MULTI ADDR TBL
DB12:          ABX     						; SELECT 1 of 4 ADDRESS (TABLES)
DB13:          LDX     0,X					; GET ADDRESS
DB15:          LDAB    L01C0				; GET CURRENT MAP VALUE

DB18:          LDAA    L0061				; RPM/25
DB1A:          CMPA    #64					; 1600 RPM
DB1C:          BLS     LDB26				;
											;
DB1E:          LDAA    L0062				; ENGINE RPM/25
DB20:          ADDA    #16					; 400 RPM
DB22:          BCC     LDB26				;
											;
DB24:          LDAA    #255					;
DB26:  LDB26   JSR     LF4DE 				; 3d LK UP
DB29:          CMPA    L015B				;
DB2C:          BCS     LDB31				;
											;
DB2E:          STAA    L015B				;
DB31:  LDB31   LDAB    L00D9   				; CURRENT GEAR
DB33:          CMPB    #$01					;
DB35:          BEQ     LDB3B				;
											;
DB37:          CMPB    #$02					;
DB39:          BNE     LDB84				;
											;

			;---------------------------------
			;
			;
			;---------------------------------
DB3B:  LDB3B   DECB    						;
DB3C:          ASLB    						;
DB3D:          LDY     #$DBEB				; INDEX TABLE
DB41:          ABY     						;
DB43:          LDX     4,Y					;
DB46:          LDAA    L00F9				;
DB48:          CMPA    0,X					;
DB4A:          BLS     LDB69				;
											;
DB4C:          BSET    L00A4,#$80			;
DB4F:          LDX     0,Y
DB52:          LDAB    0,X
DB54:          PSHB    
DB55:          LDX     4,Y
DB58:          SUBB    0,X
DB5A:          CLRA    
DB5B:          XGDX    
DB5C:          PULA    
DB5D:          SUBA    L00F9
DB5F:          BCC     LDB67
DB61:          CLRA    
DB62:          JMP     LDBDF
 
DB65:  LDB65   BRA     LDBDB
 
DB67:  LDB67   BRA     LDBC2
 
DB69:  LDB69   LDX     $0C,Y
DB6C:          CMPA    0,X
DB6E:          BLS     LDBDB
DB70:          LDX     $0008,Y
DB73:          LDAB    0,X
DB75:          LDX     $000C,Y
DB78:          SUBB    0,X
DB7A:          CLRA    
DB7B:          PSHB    
DB7C:          PSHA    
DB7D:          LDAA    L00F9
DB7F:          SUBA    0,X
DB81:          PULX    
DB82:          BRA     LDBC2
 ;
DB84:  LDB84   LDAA    L015C
DB87:          INCA    
DB88:          BEQ     LDBDB
DB8A:          STAA    L015C
DB8D:          CMPA    L70CF
DB90:          BCC     LDBAA
DB92:          BSET    L00A4,#$80
DB95:          LDAB    L70CF
DB98:          SUBB    L70CE
DB9B:          CLRA    
DB9C:          XGDX    
DB9D:          LDAA    L015C
DBA0:          SUBA    L70CE
DBA3:          BCC     LDBA8
DBA5:          CLRA    
DBA6:          BRA     LDBDF
 ;
DBA8:  LDBA8   BRA     LDBC2
 ;
DBAA:  LDBAA   CMPA    L70D1
DBAD:          BCC     LDBDB
DBAF:          LDAB    L70D1
DBB2:          SUBB    L70D0
DBB5:          CLRA    
DBB6:          XGDX    
DBB7:          LDAA    L70D1
DBBA:          SUBA    L015C
DBBD:          BCC     LDBC2
DBBF:          CLRA    
DBC0:          BRA     LDBDF
 ;
DBC2:  LDBC2   CLRB    
DBC3:          IDIV    
DBC4:          XGDX    
DBC5:          TSTA    
DBC6:          BEQ     LDBD2
DBC8:          CLRA    
DBC9:          BRSET   L00A4,#$80,LDBDF
DBCD:          LDAA    L015B
DBD0:          BRA     LDBDF
 ;
DBD2:  LDBD2   LDAA    L015B
DBD5:          MUL     
DBD6:          ADDD    #$0080
DBD9:          BRA     LDBDF
 ;
DBDB:  LDBDB   BCLR    L00A4,#$08
DBDE:          CLRA    
DBDF:  LDBDF   STAA    L015A


DBE2:  LDBE2   RTS     
 			;------------------------------------------


 			;------------------------------------------
			; ADDRESS TABLE
			;
			;------------------------------------------
DBE3:		FDB $0000
			FDB	$5719 
	   		FDB $583D 
	   		FDB	$5961 
 			;------------------------------------------


 			;------------------------------------------
			;  TABLE OF VALES
			;
			;------------------------------------------
DBEB:	   	FDB $70C6 
	   		FDB	$70CA 
	   		FDB	$70C7
			FDB $70CB
			FDB	$70C8 
			FDB $70CC 
			FDB	$70C9 
			FDB $70CD
 			;------------------------------------------





 			;------------------------------------------
			;  READS A/D
			;  & CK FOR ERR 23, LO IAT
 			;------------------------------------------
               ORG     $DBFB				
          
DBFB:          LDX     #$3000				; INDEX CPU REG'S
DBFE:          SEI     						; SECURE INTERUPTS
											;
DBFF:          LDAA    #$04					; SET A/D MODE
DC01:          JSR     LF275				; 

DC04:          LDAA    #$01
DC06:          JSR     LF25F				; A/D CNT'L MODE
DC09:          CLI     
DC0A:          LDAA    $34,X				; READ A/D RESULT
DC0C:          COMA    						; INVERT MAT VALUE
DC0D:          STAA    L0230				; SAVE INV MAT CAL

DC10:          LDX     L00FD				; RUN TIMER
DC12:          CPX     L4E45				; 0d ERR THRESH
DC15:          BLS     LDC72				;
											;
DC17:          LDAB    L0284				; MPH/1
											;
DC1A:          LDAA    L0230				;


			;
			; CK MAT FOR ERR 23
			; LOW MAT
			; 
DC1D:          LDX     #$5B01				; 1010 0010, ERR WD 2
DC20:          BRCLR   0,X,#$40,LDC3E		; BR IF NOT b6,  1 = ERR 23, MAT LOW
											;
DC24:          BCLR    L0017,#$40			; CLR ERR WD,  1 = ERR 23, MAT LOW
DC27:          CMPA    L4E41				; MAT ERR 23 TIMER
DC2A:          BCC     LDC3E				;
											;
DC2C:          LDAA    L021D				; ERR 23, TIMER
DC2F:          CMPA    L4E42				; 120d
DC32:          BHI     LDC43				; BR IF IAT TO HIGH 
											;
DC34:          CMPB    L4E47				; 1d ERR THRESH VAL ???
DC37:          BHI     LDC3E				;
											;
DC39:          INC     L021D				; ERR 23 TIMER
DC3C:          BRA     LDC46
 
DC3E:  LDC3E   CLR     L021D				; ERR 23 TIMER
DC41:          BRA     LDC46
 

DC43:  LDC43   BSET    L0017,#$40			; SET ERR 23, MAT LOW

			;------------------------------
			; CK FOR ERR 25
			; HIGH IAT
			;------------------------------
DC46:  LDC46   LDX     #$5B01				; 1010 0010, ERR WD 2
DC49:          BRCLR   0,X,#$10,LDC6A		; BR IF NOT b4
											;
DC4D:          BCLR    L0017,#$10			; CLR ERR 25

DC50:          LDAA    L0230				; GET A/D INV MAT VAL
DC53:          CMPA    L4E49				; 243d, TEMP THRESH 
DC56:          BCS     LDC6A				; BR IF A/D < 243d 
											;
DC58:          LDAA    L021E				; HI IAT TIMER
DC5B:          CMPA    L4E4A				; 120d
DC5E:          BHI     LDC6F				; 
											;
DC60:          CMPB    L4E47				; 1d ERR THRESH VAL ???
DC63:          BLS     LDC6A				; 
											;
DC65:          INC     L021E				; INCR ERR 25 TIMER

DC68:          BRA     LDC72

 
DC6A:  LDC6A   CLR     L021E				; HI IAT TIMER

DC6D:          BRA     LDC72

 
DC6F:  LDC6F   BSET    L0017,#$10			; SET b4, ERR 25, HI IAT

		;------------------------------------
		; LOOK UP LINEAR IAT VALUE
		;
		; CONVERT A/D MAT TO: 
		;	 N = (DEG C - 40) * 256/192
		;
		;------------------------------------
DC72:  LDC72   LDAA    L0230				; GET A/D MAT VAL (INVERTED)
DC75:          LDX     #$FE45				; LINEAR MAT TABLE
DC78:          JSR     LF4C1 				; 2d LK UP 
DC7B:          STAA    L0855				; SAVE LINEAR TBL IAT VALUE (Disp only)
			
			;
			; CK FOR MAT ERR & USE DEFAULT IF ERR'S
			;
			;	  b4 = 1 = HI  IAT ERR 	25
			;     b6 = 1 = LOW IAT ERR	23
			;
DC7E:          BRCLR   L0017,#$50,LDC85		; BR IF NOT b4 & b6,
											; 
DC82:          LDAA    L4E48				; -18c, DEFAULT MAT VAL
DC85:  LDC85   STAA    L022F				; SAVE LINEAR IAT VALUE

DC88:          RTS     
 			;------------------------------------------


			;-----------------------------------------
			;
			;
			;
			;-----------------------------------------
DC89:  LDC89   BSET    L006F,#$80
DC8C:          BRCLR   L0002,#$F0,LDC93				; MAJOR LOOP COUNTER
DC90:          BCLR    L006F,#$80
DC93:  LDC93   BRSET   L0050,#$10,LDCA0
DC97:          BCLR    L0071,#$80
DC9A:          BCLR    L0043,#$1C
DC9D:          JMP     LDCF5
 ;
DCA0:  LDCA0   BSET    L0071,#$80
DCA3:          CLR     L022B

DCA6:          BRSET   L004F,#$80,LDCB0		; BR IF b7, ENGINE RUNNING
											;
DCAA:          BCLR    L0043,#$1C
DCAD:          JMP     LDD06
 ;
DCB0:  LDCB0   BRSET   L003E,#$80,LDCC2		; BR IF B7, CLOSED LOOP
											;
DCB4:  LDCB4   LDAA    L0043
DCB6:          ANDA    #$F7
DCB8:          EORA    #$40
DCBA:          STAA    L0043
DCBC:          BITA    #$40
DCBE:          BNE     LDCEA
DCC0:          BRA     LDCDE
 ;
DCC2:  LDCC2   BRSET   L0043,#$08,LDCD3
DCC6:          BRCLR   L006F,#$80,LDCB4
DCCA:          BSET    L0043,#$08

DCCD:  LDCCD   BRSET   L003E,#$40,LDCE2		; BR IF b6, RICH/ LEAN, 1 = RICH

DCD1:          BRA     LDCE7
 ;
DCD3:  LDCD3   BRCLR   L006F,#$80,LDCEA
DCD7:          BRCLR   L0043,#$10,LDCCD
DCDB:          BCLR    L0043,#$10
DCDE:  LDCDE   BRSET   L0072,#$80,LDCE7
DCE2:  LDCE2   BSET    L0072,#$80
DCE5:          BRA     LDCEA
 ;
DCE7:  LDCE7   BCLR    L0072,#$80
DCEA:  LDCEA   CLRA    
DCEB:          STAA    L003C
DCED:          STAA    L0216
DCF0:          BSET    L0043,#$04
DCF3:          BRA     LDD14
 ;
DCF5:  LDCF5   CLRA    
DCF6:          STAA    L003C
DCF8:          STAA    L0216
DCFB:          BRCLR   L001A,#$20,LDD02

DCFF:          JMP     LE1E8


DD02:  LDD02   BRSET   L004F,#$80,LDD14		; BR IF b7, ENGINE RUNNING
											;
DD06:  LDD06   CLRA    
DD07:          CLRB    
DD08:          STAA    L0228
DD0B:          STAA    L0219
DD0E:          STD     L021A				; ERR 45 TIMER

DD11:          JMP     LE11A
 

DD14:  LDD14   BRSET   L0043,#$02,LDD40
DD18:          LDAB    L00FE
DD1A:          CMPB    #$000A
DD1C:          BCS     LDD40
DD1E:          BSET    L0043,#$02
DD21:          INC     L0014
DD24:          DEC     L0015
DD27:          LDAA    L0014
DD29:          CMPA    L5B12
DD2C:          BLS     LDD40
DD2E:          CLRA    
DD2F:          LDX     #$0009
DD32:  LDD32   STAA    $000A,X
DD34:          DEX     
DD35:          BNE     LDD32
DD37:          STAA    L0014
DD39:          STAA    L003C
DD3B:          JSR     LF326
DD3E:          STAA    L0015

DD40:  LDD40   BCLR    L0016,#$80			; CLR b7, ERR ...

DD43:          LDAB    L006F
DD45:          BITB    #$24
DD47:          BNE     LDDB2
DD49:          BRSET   L0071,#$40,LDD58
DD4D:          LDD     L00FD				; RUN TIMER
DD4F:          LSRD    
DD50:          CMPB    L4E32
DD53:          BCS     LDDB2
DD55:          BSET    L0071,#$40
DD58:  LDD58   LDAA    L015F

DD5B:          BRCLR   L0046,#$08,LDD69		; BR IF NOT b3, DECEL FUEL C/O
											; 
DD5F:          CMPA    L4E33				; ERR 13,  5 Sec MAX DECEL CUT OFF TIME ACCUM
DD62:          BCC     LDDB2				; BR IF TIME GT THRESH
DD64:          INC     L015F

DD67:          BRA     LDDB2


DD69:  LDD69   TSTA    
DD6A:          BEQ     LDD6D
DD6C:          DECA    
DD6D:  LDD6D   STAA    L015F
DD70:          CMPA    L4E34
DD73:          BCC     LDDB2
DD75:          LDAB    L01D5				; o2 VOLTS * 226 (A/D RESULT)
DD78:          CMPB    L4E36
DD7B:          BHI     LDDB2
DD7D:          CMPB    L4E35
DD80:          BLS     LDDB2
DD82:          LDAB    L021C
DD85:          CMPB    L4E38
DD88:          BHI     LDDB7
DD8A:          LDAA    L0002				; MAJOR LOOP COUNTER
DD8C:          ANDA    #$F0
DD8E:          BNE     LDDBA
DD90:          BRSET   L00FE,#$01,LDDBA
DD94:          LDAB    L0006				; COOL VALUE
DD96:          CMPB    L4E39
DD99:          BLS     LDDBA
DD9B:          LDAA    L01D9				; %TPS
DD9E:          CMPA    L4E37
DDA1:          BHI     LDDAD
DDA3:          TST     L021C
DDA6:          BEQ     LDDBA
DDA8:          DEC     L021C
DDAB:          BRA     LDDBA
 ;
DDAD:  LDDAD   INC     L021C
DDB0:          BRA     LDDBA
 ;
DDB2:  LDDB2   CLR     L021C
DDB5:          BRA     LDDBA
 ;
DDB7:  LDDB7   BSET    L0016,#$80			; SET b7, ERR
DDBA:  LDDBA   BCLR    L0016,#$10			; CLR b4, ERR...

DDBD:          LDAA    L006F
DDBF:          BITA    #$0048
DDC1:          BNE     LDDEE

DDC3:          LDAA    L0284				; MPH/1
DDC6:          CMPA    L4E3A
DDC9:          BHI     LDDEE

DDCB:          LDAA    L0817
DDCE:          CMPA    L4E3F
DDD1:          BHI     LDE04
DDD3:          LDAA    L01C6
DDD6:          CMPA    L4E3D
DDD9:          BCC     LDDEE

DDDB:          LDAA    L0006				; COOL VALUE
DDDD:          CMPA    L4E3E
DDE0:          BLS     LDDEE
DDE2:          LDAA    L0062				; ENGINE RPM/25
DDE4:          CMPA    L4E3B
DDE7:          BLS     LDDEE
DDE9:          CMPA    L4E3C
DDEC:          BLS     LDDF3
DDEE:  LDDEE   CLR     L0817
DDF1:          BRA     LDE07
 ;
DDF3:  LDDF3   LDAA    L01D9				; %TPS
DDF6:          CMPA    L4E40
DDF9:          BCC     LDDEE
DDFB:          LDAA    L006F
DDFD:          BPL     LDE07
DDFF:          INC     L0817
DE02:          BRA     LDE07
 ;
DE04:  LDE04   BSET    L0016,#$10			; SET b4, ERR ...

			;----------------------------------------------
			; AFR MD BYTE 5,	 0001 0000, (DIG I/O)
			;
			; b7 1 = MAN, (0 = TCC)
			; b6 1 = TCC (Non Elect xmish)
			; b5 1 = Not Used 
			; b4 1 = CONV OVER HEAT PROTECTION
			;
			; b3 1 = BURST KNOCK RETARD
			; b2 1 = A/C CLUTCH CNT'L, 0 = CPI TUNE
			; b1 1 = Not Used
			; b0 1 = 1 DO RPM/MPH LMT, (GOV'R OPT)
			;
			;----------------------------------------------
DE07:  LDE07   LDAA    L400F
DE0A:          BITA    #$0080
DE0C:          BEQ     LDE3A

			;------------------------------
			; 1010 0010, ERR WD 2
			;
			; b7 1 = ERR 22, TPS LOW 
			; b6 1 = ERR 23, MAT LOW
			; b5 1 = ERR 24, OUTPUT XMISH SPD LOW
			; b4 1 = ERR 25, MAT HIGH
			;
			; b3 1 = ERR 26,  
			; b2 1 = ERR 27, XMISH PRESS MANIFOLD
			; b1 1 = ERR 28, PRESS SWITCH MANIFOLD
			; b0 1 = ERR 29,
			;------------------------------
DE0E:          LDAA    L5B01
DE11:          BITA    #$0020
DE13:          BEQ     LDE3A
DE15:          LDD     L0849
DE18:          BEQ     LDE22
DE1A:          BCLR    L0017,#$20
DE1D:          CLR     L081C
DE20:          BRA     LDE3A
 ;
DE22:  LDE22   LDAA    L081C
DE25:          CMPA    L4E43
DE28:          BLS     LDE2F
DE2A:          BSET    L0017,#$20
DE2D:          BRA     LDE3A
 ;
DE2F:  LDE2F   LDAA    L0284				; MPH/1
DE32:          CMPA    L4E44
DE35:          BLS     LDE3A
											;
DE37:          INC     L081C
DE3A:  LDE3A   BCLR    L0018,#$80			; CLR b7

			;-----------------------------------------
			; CL IF GOVENOR OPTION
			;
			;-----------------------------------------
DE3D:          LDX     #$400F				; AFR MD BYTE 5
DE40:          BRCLR   0,X,#$01,LDE56		; BR IF NOT b0, DO RPM/MPH LMT, (GOV'R OPT) 
											;
DE44:          BRSET   L006F,#$10,LDE50		; BR IF b4, 
											;
DE48:          LDAA    L0288
DE4B:          CMPA    L4E4B
DE4E:          BCS     LDE56
DE50:  LDE50   BSET    L0018,#$80			; SET b7
DE53:          BSET    L006F,#$10			; SET b4

DE56:  LDE56   LDX     #$5B02				; ERR WD 3 MASK
DE59:          BRCLR   0,X,#$40,LDE64		; BR IF NOT b6, ERR 32, EGR FAIL
											;
DE5D:          BCLR    L0018,#$40			; CLR b6
DE60:          BRCLR   L0070,#$08,LDE67		; BR IF NOT b3	ERR 32
											;
DE64:  LDE64   JMP     LDF54				; BR TO ERR 32B ROUTINE
 			;-----------------------------------------


			;-----------------------------------------
			;  ERR 32 EGR Diag SET UP
			;
			;-----------------------------------------
DE67:  LDE67   LDX     #$400D				; AFR MD BYTE 3
DE6A:          BRCLR   0,X,#$02,LDE75		; BR IF NOT b1, (LINEAR EGR/ 0 = EVRV EGR)
											;
DE6E:          BRCLR   L0070,#$01,LDE75		; BR IF NOT b0
											;
DE72:          JMP     LDF4D
 

DE75:  LDE75   BRSET   L003E,#$80,LDE7C		; BR IF b7, CLOSED LOOP 
											;
DE79:  LDE79   JMP     LDF3D				; EXIT TEST
 

DE7C:  LDE7C   BRSET   L0046,#$08,LDE79		; BR IF b3, DECEL FUEL C/O
											;
DE80:          LDAA    L021F				; DIAG CYCLE TIME, ERR 32
DE83:          BEQ     LDE92				; BR IF TIME UP
											;
DE85:          BRSET   L006F,#$80,LDE8B		; BR IF b7
											;
DE89:          BRA     LDE8F


DE8B:  LDE8B   DECA    						; INCR CYCLE TIME
DE8C:          STAA    L021F				; DIAG CYCLE TIME, ERR 32

DE8F:  LDE8F   JMP     LDF43
			;----------------------------------------------
			
			 
			;----------------------------------------------
			; ERR 32 EGR Diag & Err
			;
			;----------------------------------------------
DE92:  LDE92   LDAA    L01AE    			; DESIRED %EGR
DE95:          CMPA    L4E51				; 50% Desired required for Err test
DE98:          BCS     LDECE				; BR IF DESIRED %EGR LT THRESH
											;
DE9A:          LDAA    L01C9				; Kpa VACUUM
DE9D:          CMPA    L4E4D				; 50.0 Kpa Low Load disable
DEA0:          BLS     LDECE				;
											;
DEA2:          CMPA    L4E4E				; 92.5 Kpa Hi load disable
DEA5:          BHI     LDECE

		; 
		; ERR 32  TPS QUALS
		;	
DEA7:          LDAA    L01D9				; %TPS
DEAA:          CMPA    L4E4F  				; 10% Low TPS Disable
DEAD:          BLS     LDECE
											;
DEAF:          CMPA    L4E50				; 50%  Hi TPS Disable
DEB2:          BHI     LDECE
											;
DEB4:          SUBA    L01DE
DEB7:          BCC     LDEBA
											; ... els
DEB9:          NEGA    
DEBA:  LDEBA   CMPA    L4E54				; 2.7% diff TPS to escape tes
DEBD:          BHI     LDECE
											;
DEBF:          LDAA    L0284				; MPH/1
DEC2:          CMPA    L4E57
DEC5:          BCS     LDF43
											;
DEC7:          BRCLR   L006E,#$01,LDED0		; EGR DIAG INT RESET
											;
DECB:          BCLR    L006E,#$01			; EGR DIAG INT RESET

DECE:  LDECE   BRA     LDF43


		;
		; CHECK INTEGRATOR FOR EGR EFFECT
		;
DED0:  LDED0   LDAA    L020F				; INTEGRATOR COUNTS
DED3:          BRSET   L0070,#$04,LDEFB
											;
DED7:          SUBA    #$80					; STOCH VALUE
DED9:          BCC     LDEDC				; BR IF NO UNDERFLOW
											;
DEDB:          NEGA    						; INVERT INT OFFSET VALUE
DEDC:  LDEDC   CMPA    L48F7				; 2, CLSD LP INT WINDOW, ERR 32 
DEDF:          BHI     LDF43				; BR IF INT OFF SET ...
											;
DEE1:          LDAA    L0220				; Err delay timer
DEE4:          CMPA    L4E52				; 3 Sec's Err delay timer, ERR32
DEE7:          BHI     LDEEC				; BR IF TIME UP
											;
DEE9:          INCA    						; INCR Err delay timer
DEEA:          BRA     LDEF6
 ;
DEEC:  LDEEC   BSET    L0070,#$04			; SET b2,
DEEF:          LDAA    L020F				; INTEGRATOR COUNTS
DEF2:          STAA    L0222
DEF5:          CLRA    						; CLEAR TIMER
DEF6:  LDEF6   STAA    L0220				; Err delay timer

DEF9:          BRA     LDF4D


DEFB:  LDEFB   SUBA    L0222
DEFE:          BCS     LDF05
DF00:          CMPA    L4E56				; 4 integrator count max for err32
DF03:          BCC     LDF25
DF05:  LDF05   LDAA    L0221				; integrator test time, (ERR32)
DF08:          CMPA    L4E55				; 3.0 Sec's integrator test time, (ERR32)
DF0B:          BCC     LDF13
DF0D:          INCA    						; Increment integrator test timer
DF0E:          STAA    L0221				; integrator test time, (ERR32)

DF11:          BRA     LDF4D



DF13:  LDF13   LDAA    L0223    			; FAIL COUNTER, (ERR 32)
DF16:          INCA    						; INCR FAIL COUNTER
DF17:          CMPA    L4E53				; 3 FAIL COUNTER MIN, (ERR 32)
DF1A:          BCS     LDF20				; BR IF FAIL COUNTER LT THRESH

DF1C:          BSET    L0070,#$01			; SET b0

DF1F:          DECA    		    			; DECR FAIL COUNTER
DF20:  LDF20   STAA    L0223    			; FAIL COUNTER, (ERR 32)

DF23:          BRA     LDF3D
 
 
DF25:  LDF25   LDAA    L0223    			; FAIL COUNTER, (ERR 32)
DF28:          BEQ     LDF2B
DF2A:          DECA    
DF2B:  LDF2B   BNE     LDF20				; BR IF 
											;
DF2D:          BCLR    L0070,#$01			; CLR b0
											;
DF30:          STAA    L0223    			; FAIL COUNTER, (ERR 32)

DF33:          LDX     #$400D				; AFR MD BYTE 3, (SINGLE PASS EGR TEST)
DF36:          BRCLR   0,X,#$80,LDF3D		; BR IF NOT b7 SINGLE PASS EGR TEST
											;
DF3A:          BSET    L0070,#$08			; SET b3, ERR32

DF3D:  LDF3D   LDAA    L4E4C				; 30 SEC DIAG CYCLE TIME
DF40:          STAA    L021F				; DIAG CYCLE TIME, ERR 32

DF43:  LDF43   CLRA    						; CLEAR TIMERS
DF44:          STAA    L0220				; Err delay timer
DF47:          STAA    L0221				; integrator test time, (ERR32)	
											;
DF4A:          BCLR    L0070,#$04			; CLR b3
											;
DF4D:  LDF4D   BRCLR   L0070,#$01,LDF54		; BR IF NOT b0, ERR 32B ROUTINE
											;
DF51:          BSET    L0018,#$40			; SET b6,
			;-----------------------------------------                         
			; ERR 32B ROUTINE
			; AFR MD BYTE 3, 1000 0010
			;
			; b1 1 = LINEAR EGR/ 0 = EVRV EGR
			;-----------------------------------------
DF54:  LDF54   LDX     #$400D				; AFR MD BYTE 3
DF57:          BRCLR   0,X,#$02,LDFCA		; BR IF NOT b1, (IF EVRV EGR)
											;
DF5B:          LDX     #$5B02				; ERR WD 3 MASK
DF5E:          BRCLR   0,X,#$40,LDFCA		; BR IF NOT b6, (ERR 32, EGR FAIL) 
											;
DF62:          BRSET   L0070,#$01,LDFBE		; BR IF b0, 
											;
DF66:          LDAA    L01B4				; EGR POSITION A/D COUNTS
DF69:          CMPA    L4E59				; 0.12 VDC, A/D VAL FOR PINTEL,(Err 32)
DF6C:          BCC     LDF81				; BR IF A/D GT 0.12 VDC 
											;
DF6E:          LDAA    L0227				; ERR TIMER
DF71:          CMPA    L4E5F				; 5 SEC'S
DF74:          BCS     LDF7B				; BR IF 
											;
DF76:          BSET    L0072,#$20			; SET b5, 

DF79:          BRA     LDFBB

 
DF7B:  LDF7B   INCA    						; INCR ERR TIMER
DF7C:          STAA    L0227				; ERR TIMER

DF7F:          BRA     LDF84
			;----------------------------------------------


			;----------------------------------------------
			;  ERR 32B TESTS
			;
			;----------------------------------------------
DF81:  LDF81   CLR     L0227				; 
DF84:  LDF84   BRCLR   L0070,#$08,LDF99		; BR IF NOT b3, ERR32
											;
DF88:          LDX     L0225				; TIME BETWEEN ERR 32B TESTS
DF8B:          CPX     L4E5D				; 1	Sec's TIME BETWEEN ERR 32B TESTS
DF8E:          BCC     LDF96				; BR IF TIME GT THRESH
											;
DF90:          INX     						; INCR TIME BETWEEN ERR 32B TESTS
DF91:          STX     L0225 				; TIME BETWEEN ERR 32B TESTS

DF94:          BRA     LDFCA


DF96:  LDF96   BCLR    L0072,#$20			; CLR b5, 

DF99:  LDF99   LDAA    L01AE    			; DESIRED %EGR
DF9C:          CMPA    L4E5C				; 69.9% DESIRED EGR
DF9F:          BHI     LDFC6				; BR IF EGR GT 69.9%
											;
DFA1:          LDAA    L01BA				; PINTLE POSIT ERROR
DFA4:          CMPA    L4E5A				; 10%, PINTLE POSIT ERROR
DFA7:          BLS     LDFC6				; BR IF 
											;
DFA9:          LDAB    L0224				; ERR 32B TIME THRESH
DFAC:          CMPB    L4E5B				; 30 SEC'S TIME THRESH, ERR32B
DFAF:          BCC     LDFB4				; BR IF NOT TIME UP
											;
DFB1:          INCB    						; INCR ERR 32B TIME THRESH

DFB2:          BRA     LDFC7
 

DFB4:  LDFB4   BSET    L0072,#$20			; SET b5
											; 
DFB7:          BRCLR   L0070,#$08,LDFC3		; BR IF NOT b3, SET ERROR 32B 
											;
DFBB:  LDFBB   BSET    L0070,#$01			; SET b0
DFBE:  LDFBE   BSET    L0018,#$40			; SET b6
											
DFC1:          BRA     LDFCA				; EXIT TO ERR 33 TESTS


DFC3:  LDFC3   BSET    L0070,#$08			; SET b3 ERR 32B
DFC6:  LDFC6   CLRB    						; CLR TIME THRESH
DFC7:  LDFC7   STAB    L0224				; ERR 32B TIME THRESH
			;-----------------------------------------



			;-----------------------------------------
			; BR HERE FOR ERR 33 TESTS
			;-----------------------------------------
DFCA:  LDFCA   BCLR    L0018,#$20			; CLR b5

DFCD:          LDAB    L006F
DFCF:          ANDB    #$BF
DFD1:          BITB    #$24
DFD3:          BNE     LE001
											;
DFD5:          LDAA    L4E61				; 68 KPA MAP LMT, ERR 33
DFD8:          CMPA    L02F4				; BARO 
DFDB:          BLS     LDFE0				; BR IF
											;
DFDD:          LDAA    L02F4				; BARO
DFE0:  LDFE0   CMPA    L082E				; MAP A/D
DFE3:          BCC     LE001				;
											;
			;
			; CK TIMER FOR ERR 33
			; MAP SENSOR HI
			;									
DFE5:          LDAA    L0228				; ERR 33 TIMER
DFE8:          CMPA    L4E62				; 5 SEC'S TIME LMT
DFEB:          BHI     LE006				; BR IF TIME GT THRESH
											;
DFED:          LDAA    L01D9				; %TPS
DFF0:          SUBA    L4E60				; 4% TPS LIMIT
DFF3:          BCC     LE001				; BR IF TPS GT THRESH
											;
DFF5:          LDAA    L0061				; RPM/25
DFF7:          CMPA    L4E63				; 1200 RPM
DFFA:          BCS     LE001				; BR IF RPM LT 1200 RPM
											;
DFFC:          INC     L0228				; INCR ERR 33 TIMER

DFFF:          BRA     LE00B
 
E001:  LE001   CLR     L0228				; CLR ERR 33 TIMER

E004:          BRA     LE00B
 
 
E006:  LE006   BSET    L0018,#$20			; SET b5, ERR 33


E009:          ORAB    #$40					; SET b6
E00B:  LE00B   STAB    L006F

E00D:          BRSET   L0044,#$04,LE041		; BR IF b2, SKIP ERR 43 DUE TO ALDL
											;
E011:          BRSET   L0050,#$08,LE041		;
											;
E015:          BRSET   L0002,#$10,LE041		; MAJOR LOOP COUNTER
											;
E019:          BRCLR   L004F,#$40,LE041		; BR IF NOT b6, MAJOR LOOP EST MONITOR ENABLE
											;
E01D:          CLRB    

E01E:          LDX     L3FCA

			;
			; ERR 42 EST CHECKING
			;
E021:          LDAA    L0061				; RPM/25 
E023:          CMPA    L4E70				; RPM LIMIT, 450 RPM, ERR 42
E026:          BLS     LE03B				;
											;
E028:          CPX     L0205				;
E02B:          BNE     LE03B				;
											;
E02D:          LDAB    L022C				; ERR 42B 
E030:          CMPB    L4E73				; NUM EST FAULT FOR 42B
E033:          BHI     LE038				; BR IF 
											;
E035:          INCB    						; INCR ERR 42B CNT'R

E036:          BRA     LE03B
 


E038:  LE038   BSET    L0004,#$80
E03B:  LE03B   STAB    L022C
E03E:          STX     L0205
E041:  LE041   BCLR    L0019,#$08			;
											;
E044:          LDAA    L4E78				; --- Mv LOW o2 SENSOR LMT
E047:          CMPA    L01D0				; o2 VOLTAGE, 1  
E04A:          BLS     LE079				;
											;
E04C:          LDAA    L0219				;
E04F:          BRCLR   L0072,#$40,LE05E		;
E053:          CMPA    L4E7A				;
E056:          BHI     LE081				;
											;
E058:          BRSET   L00FE,#$01,LE084		; 
											;
E05C:          BRA     LE070
 ;
E05E:  LE05E   CMPA    L4E79
E061:          BLS     LE068
E063:          BSET    L0072,#$40
E066:          BRA     LE07C
 ;
E068:  LE068   BRCLR   L003E,#$80,LE079		; BR IF NOT b7, CLOSED LOOP
											;
E06C:          BRSET   L0071,#$04,LE079
E070:  LE070   BRCLR   L006F,#$80,LE084
E074:          INC     L0219
E077:          BRA     LE084
 ;
E079:  LE079   BCLR    L0072,#$40
E07C:  LE07C   CLR     L0219
E07F:          BRA     LE084
 

E081:  LE081   BSET    L0019,#$08

E084:  LE084   LDX     #$400E				; AFR MD BYTE 4, LATCH ERR 45
E087:          BRSET   0,X,#$20,LE08E		; BR IF	b5, 

E08B:          BCLR    L0019,#$04			; CLR b2
											;

			;
			; CK HI o2 LINE FOR ERR 45
			;  HIGH o2 SENSOR
			;
E08E:  LE08E   LDAA    L01D0				; o2 VOLTAGE, 1
E091:          CMPA    L4E7D				; 698 Mv, o2 HI LMT, ERR 45
E094:          BLS     LE0D6				; BR IF o2 VDC  LT THRESH
											;
E096:          LDX     L021A				; ERR 45 TIMER
											;
E099:          BRSET   L0044,#$20,LE0AF		; BR IF b5, HIGH MAT CONDITIONS OBSERVED 

E09D:          LDAA    L022F				; LINEAR IAT VALUE
E0A0:          CMPA    L4E7C				; 151c COOL, ERR 45
E0A3:          BHI     LE0AC				; BR IF IAT > 151

E0A5:          CPX     L4E7E				; 60 SEC'S ERR 45 TIME LMT
E0A8:          BHI     LE0DE				; BR IF 
											;
E0AA:          BRA     LE0B4
 
 
E0AC:  LE0AC   BSET    L0044,#$20			; SET b5, HIGH MAT CONDITIONS OBSERVED

E0AF:  LE0AF   CPX     L4E80				; 0 SEC'S ERR TIME LMT, (ERR 45)
E0B2:          BHI     LE0DE				; BR IF TIME 
											;
E0B4:  LE0B4   BRCLR   L003E,#$80,LE0D6		; BR IF NOT b7,	CLOSED LOOP
											;
E0B8:          BRSET   L0071,#$04,LE0D6		; BR IF b2,


			;
			; CK TPS WINDOW, (Err 45)
			;  HIGH o2 SENSOR
			;
E0BC:          LDAA    L01D9				; %TPS
E0BF:          CMPA    L4E82				; 5% TPS HI LMT, (ERR 45)
E0C2:          BHI     LE0C9				; BR IF TPS GT THRESH 

E0C4:          CMPA    L4E83				; 93.8% TPS HI LMT,	(ERR 45)
E0C7:          BCC     LE0D6				; BR IF TPS GT THRESH

E0C9:  LE0C9   BRCLR   L006F,#$80,LE0E1		; BR IF NOT b7 

E0CD:          LDX     L021A				; ERR 45 TIMER
E0D0:          INX     						; INCR ERR 45 TIMER
E0D1:          STX     L021A				; ERR 45 TIMER

E0D4:          BRA     LE0E1


E0D6:  LE0D6   LDX     #$0000				; ZERO TIMER
E0D9:          STX     L021A				; ERR 45 TIMER

E0DC:          BRA     LE0E1

 

E0DE:  LE0DE   BSET    L0019,#$04			; SET b2
E0E1:  LE0E1   BCLR    L0071,#$04			; CLR b2

E0E4:          LDAB    L400C				; AFR MD BYTE 2	 1011 0111 <---****
E0E7:          BITB    #$02					; b1, ERR 44/45 BLM LMT
E0E9:          BEQ     LE0F6				; BR IF NOT b1
											;
E0EB:          BRSET   L0019,#$04,LE0F3	    ; BR IF b2,
											;
E0EF:          BRCLR   L0072,#$40,LE0F6		; BR IF NOT b6
											;
E0F3:  LE0F3   JSR     LF28E

E0F6:  LE0F6   LDAA    L5B03				; 1011 1100, ERR WD 4 <---***
E0F9:          BITA    #$02					; b1,  1 = ERR 46, VATS FAIL 
E0FB:          BEQ     LE11A				;
											;
E0FD:          LDAA    L00A7    			; BAT VOLTS, VDC/10
E0FF:          CMPA    #90					; 9.0 VDC
E101:          BCS     LE11A				; BR IF BAT LT 9 VDC
											;
E103:          BRSET   L003D,#$02,LE11A		; BR IF b1, VATS PASSED 
											;
E107:          LDAA    L0856				; VATS, TIMER, (ERR 46)
E10A:          CMPA    L4E84				; 12.8 SEC'S VATS TMR FOR ERR 46
E10D:          BHI     LE117				; BR IF TIMER GT THRESH
											;
E10F:          INCA							; INCR VATS, TIMER, (ERR 46)
E110:          BEQ     LE11A				; BR IF TIME UP
											;
E112:          STAA    L0856				; VATS, TIMER, (ERR 46

E115:          BRA     LE11A


E117:  LE117   BSET    L0019,#$02			; SET b1 (VATS ERR, ERR 46)
											;
E11A:  LE11A   BRCLR   L0043,#$04,LE121		; BR IF NOT b2
											;
E11E:          JMP     LE1EB
 			;----------------------------------------------


			;----------------------------------------------
			;
			;
			;---------------------------------------------=
E121:  LE121   BRCLR   L0071,#$80,LE12B		; BR IF NOT b7
											;
E125:          JSR     LE1EC

E128:          JMP     LE1DF


E12B:  LE12B   BRCLR   L0044,#$10,LE132		; BR IF NOT b4, IGNITION OFF 
											;e

E12F:          JMP     LE1EB
 

E132:  LE132   LDY     #$5B08				; ERR MASK WD 9
E136:          CLRA    
E137:          LDX     #$0009
E13A:  LE13A   ORAA    $55,X
E13C:          DEX     
E13D:          BNE     LE13A
											;
E13F:          TSTA    
E140:          BNE     LE160
											;
E142:          LDX     #$09
E145:  LE145   LDAA    0,Y
E148:          ANDA    $15,X
E14A:          STAA    $55,X
E14C:          DEY     
E14E:          DEX     
E14F:          BNE     LE145
											;
E151:          LDAA    L022B
E154:          BEQ     LE15B
E156:          DEC     L022B
E159:          BRA     LE1C7

E15B:  LE15B   BCLR    L0071,#$01
E15E:          BRA     LE1C7


E160:  LE160   LDX     #$0009
E163:          CLRA    
E164:  LE164   LDAB    $15,X
E166:          ANDB    $55,X
E168:          ANDB    0,Y
E16B:          STAB    $55,X
E16D:          ORAA    $55,X
E16F:          DEY     
E171:          DEX     
E172:          BNE     LE164
E174:          INC     L022B

		;------------------------------
		; ERR LOGGING TIMERS CALIB'S
		;
		;------------------------------
E177:          LDX     #$4E2E				; INDEX ERR LOG CNS'T TBL
											;
E17A:          BRCLR   L0071,#$01,LE180		; BR IF NOT b0
											;
E17E:          INX     
E17F:          INX 
    
E180:  LE180   TSTA    
E181:          BEQ     LE184

E183:          INX     
E184:  LE184   LDAB    0,X
E186:          CMPB    L022B
E189:          BCC     LE1C7

E18B:          STAB    L022B
E18E:          TSTA    
E18F:          BEQ     LE1C7

E191:          LDAA    L4E30				; 10 SEC DELAY ERR LOG TIME #3
E194:          STAA    L022B

E197:          CLRB    
E198:          LDX     #$0009
E19B:  LE19B   LDAA    $0A,X
E19D:          ORAA    $55,X
E19F:          STAA    $0A,X
E1A1:          STAB    $55,X
E1A3:          DEY     
E1A5:          DEX     
E1A6:          BNE     LE19B

E1A8:          STAB    L0014
E1AA:          JSR     LF326

E1AD:          STAA    L0015

E1AF:          LDX     #$0009
E1B2:          LDY     #$5AFC
E1B6:  LE1B6   LDAB    $0015,X
E1B8:          BITB    $0015,Y
E1BB:          BNE     LE1C4

E1BD:          DEY     
E1BF:          DEX     
E1C0:          BNE     LE1B6

E1C2:          BRA     LE1C7


E1C4:  LE1C4   BSET    L0071,#$01

E1C7:  LE1C7   BRSET   L004F,#$80,LE1D8		; BR IF b7, ENGINE RUNNING
											;
E1CB:          BRSET   L004F,#$02,LE1E8		; BR IF b1, CHECK ENG LAMP DELAY


E1CF:          BRSET   L0004,#$08,LE1D8		; BR IF b3, BAD SHUT DOWN
											;
E1D3:          BSET    L004F,#$02			; SET b1, CHECK ENG LAMP DELAY
											
E1D6:          BRA     LE1DB


E1D8:  LE1D8   BCLR    L004F,#$02			; CLR b1, CHECK ENG LAMP DELAY

E1DB:  LE1DB   BRSET   L0050,#$08,LE1E8
E1DF:  LE1DF   BRSET   L0071,#$01,LE1E8
										
E1E3:          BCLR    L0072,#$80			; CLR b1, CHECK ENG LAMP DELAY
											
E1E6:          BRA     LE1EB
 ;
E1E8:  LE1E8   BSET    L0072,#$80

E1EB:  LE1EB   RTS     
 		;------------------------------------------

E1EC:  LE1EC   BRCLR   L003C,#$40,LE258
E1F0:          DEC     L0218
E1F3:          BNE     LE20F
E1F5:          LDAB    #$0004
E1F7:          BRSET   L0071,#$01,LE273
E1FB:          LDX     #$0214
E1FE:          BRCLR   L003C,#$20,LE203
E202:          INX     
E203:  LE203   DEC     0,X
E205:          BMI     LE211
E207:          BSET    L0071,#$01
E20A:          LDAB    #$0004
E20C:          STAB    L0218
E20F:  LE20F   BRA     LE279
 ;
E211:  LE211   BRSET   L003C,#$20,LE21C
E215:          BSET    L003C,#$20
E218:          LDAB    #$0008
E21A:          BRA     LE273
 ;
E21C:  LE21C   BCLR    L003C,#$20
E21F:          BRCLR   L003C,#$03,LE228
E223:          DEC     L003C
E226:          BRA     LE25B
 ;
E228:  LE228   LDAB    L0216
E22B:          CMPB    #71
E22D:          BLS     LE237
											;
E22F:          CLR     L0216
E232:          BCLR    L003C,#$40

E235:          BRA     LE276
 

E237:  LE237   BITB    #$07
E239:          BNE     LE250
											;
E23B:          LSRB    
E23C:          LSRB    
E23D:          LSRB    
E23E:          LDY     #$5B00				; INDEX ERR MASKS


E242:          LDX     #$000B
E245:          ABX     
E246:          ABY     
E248:          LDAB    0,X
E24A:          ANDB    0,Y
E24D:          STAB    L0217
E250:  LE250   INC     L0216
E253:          ASL     L0217
E256:          BCC     LE228
											;
E258:  LE258   BSET    L003C,#$02

    ;---------------------------------
    ; PLINK OUT CODES
    ;
    ;---------------------------------
E25B:  LE25B   LDAB    L0216

E25E:          LDX     #$FE56		INDEX BLINK OUT CODES
E261:          ABX     
E262:          LDAA    0,X
E264:          TAB     
E265:          ANDB    #$000F
E267:          LSRA    
E268:          LSRA    
E269:          LSRA    
E26A:          LSRA    
E26B:          STD     L0214

E26E:          LDAB    #$1C
E270:          BSET    L003C,#$40
E273:  LE273   STAB    L0218

E276:  LE276   BCLR    L0071,#$01
E279:  LE279   BRSET   L0071,#$01,LE282
E27D:          BCLR    L0072,#$80

E280:          BRA     LE285

E282:  LE282   BSET    L0072,#$80

E285:  LE285   RTS     
 	;--------------------------------


E286:  LE286   LDX     #$5B04
E289:          BRCLR   0,X,#$04,LE2C8
E28D:          BCLR    L001A,#$04
E290:          BRSET   L0072,#$01,LE2C5
E294:          LDAB    L00A7    				; BAT VOLTS, VDC/10
E296:          CMPB    L4E88
E299:          BCS     LE2C8
E29B:          LDAA    L0055
E29D:          BRCLR   L0072,#$02,LE2AC

E2A1:          BRCLR   L004F,#$10,LE2C8			; BR IF NOT b4, RUN FUEL
												;
E2A5:          CMPA    L4E87
E2A8:          BCC     LE2C8
E2AA:          BRA     LE2C5
 ;
E2AC:  LE2AC   LDAB    L022A
E2AF:          INCB    
E2B0:          STAB    L022A
E2B3:          CMPB    L4E85
E2B6:          BHI     LE2C2
E2B8:          CMPA    L4E86
E2BB:          BCS     LE2C8
E2BD:          BSET    L0072,#$02
E2C0:          BRA     LE2C8
 ;
E2C2:  LE2C2   BSET    L0072,#$01
E2C5:  LE2C5   BSET    L001A,#$04
E2C8:  LE2C8   LDAA    L0006				; COOL VALUE



			;--------------------------------------------
			; AFR MD BYTE 1 0000 0100 
			;
			; b6 1 = MAT SENSOR
			;--------------------------------------------
E2CA:          LDX     #$400B				; AFR MD BYTE 1, 0000 0100
E2CD:          BRCLR   0,X,#$40,LE2ED		; BR IF NOT b6, (1 = MAT SENSOR)
											;

    		;------------------------------------------
    		; MAT vs INTEMEDIATE MAT or vs COOLANT TEMP
    		;
    		; TBL = DEG C + 40
    		;------------------------------------------
E2D1:          LDAA    L0232				; MAT VALUE
E2D4:          LDX     #$4AE3				; INDEX MAT TBL
E2D7:          JSR     LF4C1				; 2d LK UP 

E2DA:          LDAB    L0006				; COOL VALUE
E2DC:          SUBB    L022F				; LINEAR IAT VALUE
E2DF:          BCC     LE2E2				; 
											;
E2E1:          CLRB    
E2E2:  LE2E2   MUL     
E2E3:          ASLD    
E2E4:          BCS     LE2EB				; 
											;
E2E6:          ADDA    L022F				; LINEAR IAT VALUE
E2E9:          BCC     LE2ED				; BR IF NO UNDER FLOW
											;
E2EB:  LE2EB   LDAA    #255					; FORCE MAX VALUE

    		;--------------------------------------------------
    		; INJECTOR OFF SET BIAS ADDED TO BPW
    		;
    		; TYPE $31 ECM
    		;
    		; TBL = MSEC * 65.536
    		;--------------------------------------------------
E2ED:  LE2ED   LDX     #$4AF4
E2F0:          JSR     LF4C1				; 2D LK UP

E2F3:          CLRB    
E2F4:          LSRD    
E2F5:          ADDD    #$7480				; 29,824
E2F8:          STD     L0236

E2FB:          LDAA    L00A7    			; BAT VOLTS, VDC/10
E2FD:          LDX     #$4B05				; INJ OFFSET BIAS TBL
E300:          JSR     LF4C1				; 2D LK UP
											;
E303:          STAA    L0256              	; SAVE BPW BIAS (Msec)
											;
E306:          BRCLR   L0002,#$10,LE30B		; MAJOR LOOP COUNTER

E30A:          RTS     
 			;-----------------------------------------


E30B:  LE30B   LDAA    L0006				; COOL VALUE
E30D:          LDX     #$4B16
E310:          JSR     LF4B6				; 2D LK UP

E313:          STAA    L0242


    		;-------------------------------------
    		; ACCEL ENRICH TEMP CORRECTION vs COOL
    		;
    		; TBL = FACTOR * 32
    		;-------------------------------------
E316:          LDAA    L0006				; COOL VALUE
											;
E318:          LDX     #$4B71				; INDEX ACCEL ENRICH TEMP TBL
E31B:          JSR     LF4C1				;
E31E:          TAB     						;

    		;--------------------------------------
    		; ACELL TPS TEST CORRECTION MULT vs MAT
    		;
    		; TBL = MULT * 128
    		;--------------------------------------
E31F:          LDAA    L022F				; LINEAR IAT VALUE
E322:          LDX     #$4B82				; INDEX ACELL TPS TEST CORR TBL 
											;
E325:          JSR     LF4C1				;
											;
E328:          MUL     						; APPLY MULT
E329:          ASLD    						;
E32A:          BCC     LE32E				;
											;
E32C:          LDAA    #255					;
E32E:  LE32E   STAA    L023C				;


    		;-----------------------------------------
    		; ACELL TEMP CORRECTION FACTOR vs COOL
    		;
    		; TLB = FACTOR * 32
    		;-----------------------------------------
E331:          LDAA    L0006				; COOL TEMP
E333:          LDX     #$4B93				; ACELL TEMP CORRECTION TBL
E336:          JSR     LF4C1				; 2D LK UP

E339:          STAA    L023D

E33C:          BRSET   L004F,#$10,LE38F		; BR IF b4, RUN FUEL
											;
E340:          BRSET   L0004,#$08,LE376		; BR IF b3, BAD SHUT DOWN  
											;


    	;------------------------------------------------------
    	; TIME OUT AFR vs COOLANT
    	; AFTER START UP AFR INCREASES WITH TIME, SIMULATING A 
    	; CHOKE. 
    	;
    	; TIME BETWEEN INCREMENTS IS FROM TBL L4C33 * TBL L4C44
    	; (vs COOL).
    	;
    	; TBL = AFR * 10
    	;--------------------------------------------------
E344:          LDAA    L0006				; COOL TEMP
E346:          LDX     #$4C33				; TIME OUT AFR vs COOL TBL
E349:          JSR     LF4C1				; 2d LK UP 
E34C:          STAA    L02C8

        ;---------------------------------------------
        ; SPK TIME OUT VS COOL
		;
        ; TBL = SPK * (256/90)
        ;---------------------------------------------
E34F:          LDX     #$452C				; SPK TIME OUT VS COOL
E352:          LDAA    L0006				; COOL TEMP
E354:          JSR     LF4B6				; 2d LK UP 
E357:          STAA    L02CB				; START UP SPK ADV

		;--------------------------------------------------
		; SPK TIME OUT DECAY DELAY vs COOL
		;
		; TBL = SEC'S
		;--------------------------------------------------
E35A:          LDX     #$4536				; SPK TIME OUT DECAY DELAY
E35D:          LDAA    L0006				; COOL TEMP
E35F:          JSR     LF4B6				; 2d LK UP				
E362:          STAA    L02CC				; SPK TIME OUT DELAY IN SEC'S


    	;--------------------------------------------------
    	; AFR CRANK XISITION vs COOLANT
    	;
    	; (THIS IS TRANSISITON AFR FOR CRANK TO RUN
    	; ADDED or SUBTRACTED FROM AFR)
    	; TBL = RATIO * 10
    	;--------------------------------------------------
E365:          LDX     #$4C9D				; AFR CRANK XISITION vs COOLANT
E368:          LDAA    L0006				; COOL TEMP
E36A:          JSR     LF4C1				; 2d LK UP
E36D:          STAA    L02C9				; CRANK XISITION AFR 

E370:          LDAB    L4929				; 2 SEC ENG RUN TIME PRIOR TO AFR DECAY
E373:          STAB    L02CA

    	;-----------------------------------------
    	; AFR CRANK XISITION DECAY vs COOL
    	;
    	; TBL = AFR * 10
    	;-----------------------------------------
E376:  LE376   LDX     #$4CAE				; AFR CRANK XISITION DECAY
E379:          LDAA    L0006				; COOL TEMP
E37B:          JSR     LF4C1				; 2d LK UP
E37E:          STAA    L0267				; CRANK XISITION DECAY AFR


        ;------------------------------------------
        ; SPK TIME OUT DECAY MULTIPLIER vs COOL 
        ;
        ; TBL = %MULT * 2.56
        ;------------------------------------------
E381:          LDX     #$4540				; SPK TIME OUT DECAY MULTIPLIER
E384:          LDAA    L0006				; COOL TEMP
E386:          JSR     LF4B6				; 2D LK UP
E389:          STAA    L01FF

E38C:          JMP     LE477
 		;-------------------------------------------
 

 		;-------------------------------------------
		;
		;
 		;-------------------------------------------
E38F:  LE38F   SEI     						; SECURE INTERUPTS
E390:          LDAB    L003F				; FLAG REG 
E392:          ANDB    #$F0					; 1111 0000

E394:          LDAA    L0066				; OLD RPM/25
E396:          SUBA    L0063				; RPM/12.5
E398:          BCC     LE39D				; BR IF OLD RPM GT CURRENT RPM
											;
E39A:          ORAB    #$01					; SET b0, RPM DECREASING

E39C:          NEGA    						; INVERT RPM
E39D:  LE39D   CMPA    L4954				; 12.5 RPM DIFF IDLE THRESH, (See L494F &  L4952)
E3A0:          BCS     LE3A4				; BR IF DIFF GT THRESH
											;
E3A2:          ORAB    #$02					; SET b1

		;
		; RESET OLD RPM VALUE
		;
E3A4:  LE3A4   LDAA    L0063				; RPM/12.5
E3A6:          STAA    L0066				; OLD RPM/25

E3A8:          LDAA    L0858				; RPM/12.5
E3AB:          CMPA    L4FBE 				; 25 RPM, DEADBAND FOR UPDATING IDLE CELLS
E3AE:          BLS     LE3B2
											;
E3B0:          ORAB    #$08

E3B2:  LE3B2   BRCLR   L0036,#$80,LE3B8		; BR IF NOT b7, IDLE RPM TOO HIGH
											;
E3B6:          ORAB    #$04					; SET b2

			;
			; SET RPM STATUS FLAG
			; 
E3B8:  LE3B8   STAB    L003F

E3BA:          CLI     						; RESTORE INTERUPTS

E3BB:          LDAA    L02CA
E3BE:          BNE     LE434				; BR IF NZ
											;
E3C0:          LDAA    L02C8
E3C3:          BNE     LE3C8				; BR IF NZ
											;
E3C5:          JMP     LE43C
 

E3C8:  LE3C8   LDAA    L027D				; AFR DECAY TIMER
E3CB:          BEQ     LE3E6				; BR IF TIMER = Z
											;
E3CD:          CMPA    L4959				; 10 sec's DELAY PRIOR TO DECAY OF AFR IN COLD PK -> DRIVE 
E3D0:          BNE     LE3DD
											;
E3D2:          LDAB    L0006				; COOL TEMP
E3D4:          CMPB    L4957				; -4c COOL, UPPER LMT FOR COLD PK -> DRIVE
E3D7:          BHI     LE3DD
											;
E3D9:          BRSET   L0041,#$20,LE43C		; BR IF b5, PARK/NEUTRAL
											;
E3DD:  LE3DD   DECA    
E3DE:          STAA    L027D				; AFR DECAY TIMER
E3E1:          BNE     LE43C				; BR IF TIMER = NZ

E3E3:          BSET    L003E,#$08			; BR IF NOT b7,	CLOSED LOOP
											;
E3E6:  LE3E6   LDAA    L0270
E3E9:          BNE     LE439
											;
    	;----------------------------------------------
    	; TIME OUT AFR vs COOLANT
    	;
    	; AFTER START UP AFR INCREASES WITH TIME, SIMULATING A 
    	;  CHOKE. 
    	;
    	; TIME BETWEEN INCREMENTS IS FROM TBL L4C33 * TBL L4C44
    	; (vs COOL).
    	;
    	; TBL = AFR * 10
    	;----------------------------------------------
E3EB:          LDX     #$4C44

E3EE:          LDAA    L0006				; COOL TEMP
E3F0:          JSR     LF4C1				; 2d LK UP

E3F3:          STAA    L0270

    	;---------------------------------------------
    	;  MULTIPLIER vs COUNTS AIR FLOW
    	;
    	;  Dissassemby of BMHM
    	;
    	; TBL = MULT * 128
    	;---------------------------------------------
E3F6:          LDX     #$4C55

E3F9:          LDAA    L0232				; AIR FLOW
E3FC:          CMPA    #64					; CK FOR MAX LIMIT
E3FE:          BLS     LE402				;

E400:          LDAA    #64					; FORCE 64 AS MAX VALUE
E402:  LE402   JSR     LF4C1				; 2d LK UP

E405:          TAB     

E406:          LDAA    L0270
E409:          MUL     
E40A:          ASLD    
E40B:          BCC     LE40F
											;
E40D:          LDAA    #255
E40F:  LE40F   STAA    L0270

E412:          LDAA    L02C8

E415:          LDAB    L4928				; 96% MULT, AFR TIME OUT (START UP)
E418:          MUL     

E419:          BRSET   L003E,#$08,LE42F		; BR IF NOT b7,	CLOSED LOOP
											;
E41D:          CMPA    L4958				;  2.5 AFR LIMIT FOR COLD PK -> DRIVE 
E420:          BHI     LE42F				; BR IF AFR ...
											;
E422:          LDAB    L0006				; COOL TEMP
E424:          CMPB    L4957				; -4c COOL, UPPER LMT FOR COLD PK -> DRIVE
E427:          BHI     LE42F
											;
E429:          LDAB    L4959 				; 10 sec's DELAY PRIOR TO DECAY OF AFR IN COLD PK -> DRIVE 
E42C:          STAB    L027D				; AFR DECAY TIMER

E42F:  LE42F   STAA    L02C8

E432:          BRA     LE43C

E434:  LE434   DEC     L02CA

E437:          BRA     LE43C


E439:  LE439   DEC     L0270



E43C:  LE43C   LDAA    L02CC				; SPK TIME OUT DELAY IN SEC'S
E43F:          BEQ     LE44C				; BR IF DELAY = 0
											;
E441:          LDAA    L0002				; MAJOR LOOP COUNTER
E443:          ANDA    #$F0					; 1111 0000
E445:          BNE     LE477				; BR IF 
											;
E447:          DEC     L02CC				; SPK TIME OUT DELAY IN SEC'S
E44A:          BRA     LE477


E44C:  LE44C   LDAA    L02CB				; START UP SPK ADV
E44F:          BEQ     LE477				; BR IF = 0
											;
E451:          LDAA    L0200				; SEC'S, SPK TIME OUT REDUCTION RATE
E454:          BEQ     LE45B				; BR IF = 0

E456:          DEC     L0200				; DECR, SEC'S, SPK TIME OUT REDUCTION RATE 

E459:          BRA     LE477
										   
    		;-----------------------------------------
    		; SPK TIME OUT REDUCTION RATE vs FLOW
    		;
    		; TBL = SEC 5 -1 
    		;-----------------------------------------
E45B:  LE45B   LDAA    L0232				; GET CYL AIR FLOW (BIN)
E45E:          CMPA    #64					; CK FOR MAX TBL VAL
E460:          BLS     LE464				; BR IF FLOW < 64
											;
E462:          LDAA    #64					; MAX TBL LMIT
E464:  LE464   LDX     #$44D0				; SPK TIME OUT REDUCTION RATE
E467:          JSR     LF4C1				; 2d LK UP
E46A:          STAA    L0200				; SEC'S, SPK TIME OUT REDUCTION RATE


E46D:          LDAA    L02CB				; START UP SPK ADV
E470:          LDAB    L01FF
E473:          MUL     						; MULT .... 
E474:          STAA    L02CB				; START UP SPK ADV

E477:  LE477   BRCLR   L004F,#$10,LE490		; BR IF NOT b4, RUN FUEL
											;
E47B:          BRCLR   L0019,#$0C,LE481		; BR IF NOT b3 & b2
											;
E47F:          BRA     LE48D


E481:  LE481   BRSET   L0072,#$40,LE48D		; BR IF b6
											;
E485:          BRCLR   L0018,#$30,LE493		; BR IF NOT b4 & b5
											;
E489:          BRCLR   L0050,#$80,LE493		; BR IF NOT b7, IDLE
											;
E48D:  LE48D   CLR     L0241
E490:  LE490   JMP     LE516



E493:  LE493   BRCLR   L003B,#$10,LE4A4		; BR IF NOT b4
											;
E497:          LDX     #$0391
E49A:          BRCLR   0,X,#$01,LE4A4		; BR IF NOT b0
											; ... els
E49E:          BRCLR   1,X,#$01,LE516		; BR IF NOT b0
											; ... els
E4A2:          BRA     LE4FC
 ;
E4A4:  LE4A4   LDAA    L0241				; 
E4A7:          CMPA    L48D2 				; 21 SEC MIN FOR INSIDE WINDOW FOR NOT-READ
E4AA:          BCC     LE4B2
											;
E4AC:          INCA    
E4AD:          STAA    L0241

E4B0:          BRA     LE4B5
 

E4B2:  LE4B2   BCLR    L0004,#$01			; CLR b0, o2 SENSOR READY
											;
E4B5:  LE4B5   BRCLR   L0004,#$01,LE516		; BR IF NOT b0, o2 SENSOR READY
											;
E4B9:          BRSET   L0050,#$10,LE4EA		; BR IF b4
											;
E4BD:          BRSET   L0004,#$02,LE4EA		; BR IF b1, CLS LP TMR OK
											;
E4C1:          LDD     L00FD				; RUN TIMER
E4C3:          LSRD    						; n/2
E4C4:          LDAA    L0282				; START UP COOL
E4C7:          CMPA    L48CC				; 100 DEC c HOT START THRESH
E4CA:          BLS     LE4D3				; BR IF  S/U COOL LT THRESH
											;
E4CC:          CMPB    L48CF				; 90 Sec CLS LP MIN IF START UP COOL G.T. L48CC
E4CF:          BCS     LE50B				;
											;
E4D1:          BRA     LE4E4
 


E4D3:  LE4D3   CMPA    L48CB				;  84c, CLS LOOP TIMER START THRESH
E4D6:          BHI     LE4DF				; BR IF 
											;
E4D8:          CMPB    L48CE				; 120 SEC CLSD LOOP MIN IF L.T. L48BA
E4DB:          BCC     LE4E4				;
											;
E4DD:          BRA     LE50B
 

E4DF:  LE4DF   CMPB    L48CD 				; 30  SEC MIN FOR CLSD LOOP IF TEMP UP 48BA
E4E2:          BCS     LE50B				;
											;
E4E4:  LE4E4   BSET    L0004,#$02			; SET b1,  CLS LP TMR OK
E4E7:          BCLR    L0052,#$80			; CLR b7
											;
E4EA:  LE4EA   LDAA    L0006				; COOL TEMP
E4EC:          CMPA    L48D0				; 30c COOL MIN FOR CLSD LP
E4EF:          BLS     LE519				; BR IF COOL 
											;
E4F1:          BRCLR   L0086,#$40,LE4FC		; BR IF NOT b6
											;
E4F5:          LDAA    L0801				;
E4F8:          ANDA    #$03					;
E4FA:          BNE     LE519				;
											;
E4FC:  LE4FC   BSET    L0046,#$80			; SET b7,  HAS BEEN IN CLS LP ONCE SINCE START UP


                    ;---------------------------------
					;  NWAF1, A/F MODE WD 1
					; 		b7 1 = CLSD LOOP
					; 		b5 1 = CLSD LP 
					;-------------------------------
E4FF:          BSET    L003E,#$A0			; SET b7 & b5
											;
E502:          BRCLR   L0050,#$02,LE51E		; BR IF NOT b1
											;

                    ;---------------------------------
   					; NWAF1, A/F MODE WD 1
					;
                    ; b7 1 = CLSD LOOP	
                    ; b1 1 = BLM ENABLE    
                    ;---------------------------------
E506:          BCLR    L003E,#$82			; CLR b7 & b1

E509:          BRA     LE561
 

E50B:  LE50B   BSET    L0052,#$80			; SET b7
											;
E50E:          LDAA    L024A				; AFR
E511:          CMPA    L48E9				; 25.5:1 AFR FOR QUSI CLSD LP
E514:          BCC     LE519				;
											;
E516:  LE516   BCLR    L0052,#$80			; CLR b7
E519:  LE519   BCLR    L003E,#$A2			; CLR $A2

E51C:          BRA     LE561			


E51E:  LE51E   LDAA    L006F				;
E520:          ANDA    #$48					;
E522:          BNE     LE55E				;
											;
E524:          LDAA    L0006				; COOL TEMP
E526:          CMPA    L48D6				; 35 DEG C, MIN COOL for BLM ENABLE
E529:          BLS     LE55E				; BR IF COOL 
											;
E52B:          LDAA    L024A				; AFR
E52E:          CMPA    L48E7				; 14.7, STOCH AFR
E531:          BNE     LE55E				; BR IF AFR NE STOCH
											;
E533:          LDAA    L01C9				; Kpa VACUUM
E536:          CMPA    L48D3				; 0 Kpa VAC MIN for BLM LEARN
E539:          BHI     LE55E				;
											;
E53B:          LDAA    L01CF

			;------------------------------
			; AFR MD BYTE 4,	 0000 0011 
			;
			; b7 1 = Not Used
			; b6 1 = Not Used
			; b5 1 = LATCH ERR 45
			; b4 1 = USE L4979 WITH ASYNC FUEL DELIVERY
			;
			; b3 1 = CPI MANAFOLD TUNE CNT'L
			; b2 1 = SHIFT LIGHT ENABLE 
			; b1 1 = USE ALT CMAP vs
			;    MAP LD FOR FUEL CUR HYST PAIR
			; b0 1 = USE ALT CMAP vs
			;    MAP LD & AD MAP FOR BLM ENABLE 
			;------------------------------
E53E:          LDAB    L400E				; 
E541:          BITB    #$01					; b0
E543:          BNE     LE548				; BR IF b0 
											;
E545:          LDAA    L01C6
E548:  LE548   CMPA    L48D5				; 99.6 Kpa MAX for BLM LEARN
E54B:          BHI     LE55E				; BR IF 
											;
E54D:          CMPA    L48D4				; 28 Kpa MIN for BLM LEARN
E550:          BCS     LE55E				; BR IF 
											;
E552:          LDAA    L0062				; ENGINE RPM/25 
E554:          CMPA    L48D7				; 3175 RPM, MAX for BLM ENABLE
E557:          BCC     LE55E				; BR IF 
											;
E559:          BSET    L003E,#$02
E55C:          BRA     LE561
 ;
E55E:  LE55E   BCLR    L003E,#$02

E561:  LE561   RTS     
 			;------------------------------------------


E562:  LE562   LDAB    L00A2
E564:          ANDB    #$07
E566:          BNE     LE56A
											;
E568:          LDAB    #$06
E56A:  LE56A   LSRB    
E56B:          PSHA    
E56C:          LDAA    #$04
E56E:          MUL     
E56F:          LDX     #$E57C
E572:          ABX     
E573:          PULB    
E574:          ABX     
E575:          LDAA    0,X
E577:          CBA     
E578:          BLS     LE57B
E57A:          TBA  
   
E57B:  LE57B   RTS     
 			;------------------------------------------


E57C:          TEST    
E57D:          NOP     
E57E:          NOP     
E57F:          NOP     
E580:          TEST    
E581:          NOP     
E582:          NOP     
E583:          NOP     
E584:          TEST    
E585:          NOP     
E586:          IDIV    
E587:          IDIV    
E588:          TEST    
E589:          NOP     
E58A:          IDIV    
E58B:          FDIV    
E58C:  LE58C   LDAA    $0008,Y
E58F:          SUBA    0,Y
E592:          BNE     LE5A4
E594:          LDAB    $0003,Y
E597:          BEQ     LE59F
E599:          DECB    
E59A:          STAB    $0003,Y
E59D:          BNE     LE5CE
E59F:  LE59F   STD     $0004,Y
E5A2:          BRA     LE5CE
 ;
E5A4:  LE5A4   PSHB    
E5A5:          LDAB    $0003,Y
E5A8:          BEQ     LE5BB
E5AA:          TAB     
E5AB:          CLRA    
E5AC:          ASLD    
E5AD:          ASLD    
E5AE:          ASLD    
E5AF:          FDIV    
E5B0:          LDD     6,Y
E5B3:          SUBD    1,Y
E5B6:          XGDX    
E5B7:          FDIV    
E5B8:          STX     4,Y
E5BB:  LE5BB   LDX     6,Y
E5BE:          STX     1,Y
E5C1:          LDAA    8,Y
E5C4:          STAA    0,Y
E5C7:          PULA    
E5C8:          STAA    3,Y
E5CB:          LDD     4,Y

E5CE:  LE5CE   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;  ERR 21,	HIGH TPS
		;--------------------------------------------------
E5CF:  LE5CF   LDAA    L5B34		; 0000 0000, XMISH ERR WD 1 ALT
E5D2:          COMA    				; INVERT TO 1111 1111

E5D3:          ANDA    L5B2B		; 1111 0001, MASK XMISH ERR WD 1
E5D6:          ANDA    L0016		; xxxx xxx1
E5D8:          ANDA    #$01			; 0000 0001 (Hi TPS err mask)
E5DA:          BNE     LE5E9		; BR IF b0 ...


			;
			; ERR 22 TPS LOW
			;
E5DC:          LDAA    L5B35			    ; 0000 0000 XMISH ERR WD 2 ALT
E5DF:          COMA    

E5E0:          ANDA    L5B2C				; 5B2C,  1010 0010, MASK XMISSH ERR WD 2
E5E3:          ANDA    L0017				; ERR WD, 1 = ERR 22, TPS LOW 
E5E5:          ANDA    #$80					; b7 1 = ERR 22, TPS LOW
E5E7:          BEQ     LE5ED				; BR IF 
											;
E5E9:  LE5E9   BSET    L0098,#$01			; SET b0

E5EC:          RTS 
    

E5ED:  LE5ED   BCLR    L0098,#$01

E5F0:          RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
E5F1:  LE5F1   LDAA    L5B2F
E5F4:          ANDA    L001A
E5F6:          ANDA    #$0018
E5F8:          BNE     LE603
E5FA:          BRSET   L0086,#$80,LE607
E5FE:          TST     L0100
E601:          BNE     LE607
E603:  LE603   BSET    L0099,#$08
E606:          RTS     
 ; ------------------------------------------
E607:  LE607   BCLR    L0099,#$08
E60A:          RTS     
 			;------------------------------------------
			; ERR 
			;
			;
			;------------------------------------------
E60B:  LE60B   LDAA    L5B35				; 0000 0000 XMISH ERR WD 2 ALT
E60E:          COMA    

E60F:          ANDA    L5B2C				; L5B2C 1010 0010, MASK XMISSH ERR WD 2
E612:          ANDA    L0017				;
E614:          ANDA    #$20					; b5,  1 = ERR 24, OUTPUT XMISH SPD LOW
E616:          BNE     LE625				; BR IF
											; 

E618:          LDAA    L5B3A				; 0000 0000 XMISH ERR WD 7 ALT
E61B:          COMA    
E61C:          ANDA    L5B31
E61F:          ANDA    L001C
E621:          ANDA    #$0004
E623:          BEQ     LE629
E625:  LE625   BSET    L0098,#$02
E628:          RTS     
 ; ------------------------------------------
E629:  LE629   BCLR    L0098,#$02
E62C:          RTS     
 ; ------------------------------------------
E62D:  LE62D   LDY     #$5B00				; INDEX ERR MASKS


E631:          LDAB    #$0009
E633:  LE633   LDAA    $003C,Y
E636:          ANDA    $0033,Y
E639:          LDX     #$0015
E63C:          ABX     
E63D:          ANDA    0,X
E63F:          LDX     #$E716
E642:          ABX     
E643:          ANDA    0,X
E645:          BNE     LE650
E647:          DEY     
E649:          DECB    
E64A:          BNE     LE633
E64C:          BCLR    L0098,#$08
E64F:          RTS     
 ; ------------------------------------------
E650:  LE650   BSET    L0098,#$08
E653:          RTS     
 ; ------------------------------------------
E654:  LE654   LDX     #$E71F
E657:          JSR     LE6BC
E65A:          BNE     LE660
E65C:          BCLR    L0098,#$10
E65F:          RTS     
 ; ------------------------------------------
E660:  LE660   BSET    L0098,#$10
E663:          RTS     
 ; ------------------------------------------
E664:  LE664   LDX     #$E728
E667:          JSR     LE6BC
E66A:          BNE     LE670
E66C:          BCLR    L0098,#$20
E66F:          RTS     
 ; ------------------------------------------
E670:  LE670   BSET    L0098,#$20
E673:          RTS     
 ; ------------------------------------------
E674:  LE674   LDX     #$E731
E677:          JSR     LE6BC
E67A:          BNE     LE680
E67C:          BCLR    L0098,#$40
E67F:          RTS     
 ; ------------------------------------------
E680:  LE680   BSET    L0098,#$40
E683:          RTS     
 ; ------------------------------------------
E684:  LE684   BRSET   L001D,#$80,LE698
E688:          BRCLR   L0087,#$02,LE694
E68C:          LDX     #$E74C
E68F:          JSR     LE6BC
E692:          BNE     LE698
E694:  LE694   BCLR    L0098,#$80
E697:          RTS     
 ; ------------------------------------------
E698:  LE698   BSET    L0098,#$80
E69B:          RTS     
 ; ------------------------------------------
E69C:  LE69C   LDX     #$E73A
E69F:          JSR     LE6BC
E6A2:          BNE     LE6A8
E6A4:          BCLR    L0099,#$01
E6A7:          RTS     
 ; ------------------------------------------
E6A8:  LE6A8   BSET    L0099,#$01
E6AB:          RTS     
 ; ------------------------------------------
E6AC:  LE6AC   LDX     #$E743
E6AF:          JSR     LE6BC
E6B2:          BNE     LE6B8
E6B4:          BCLR    L0099,#$02
E6B7:          RTS     
 ; ------------------------------------------
E6B8:  LE6B8   BSET    L0099,#$02
E6BB:          RTS     
 ; ------------------------------------------
E6BC:  LE6BC   PSHY    
E6BE:          PSHB    
E6BF:  LE6BF   LDY     #$5B00				; INDEX ERR MASKS


E6C3:          LDAB    #$0009
E6C5:          ABX     
E6C6:  LE6C6   LDAA    $003C,Y
E6C9:          COMA    
E6CA:          ANDA    $0033,Y
E6CD:          PSHX    
E6CE:          LDX     #$0015
E6D1:          ABX     
E6D2:          ANDA    0,X
E6D4:          PULX    
E6D5:          ANDA    0,X
E6D7:          BNE     LE6DF
E6D9:          DEX     
E6DA:          DEY     
E6DC:          DECB    
E6DD:          BNE     LE6C6
E6DF:  LE6DF   PULB    
E6E0:          PULY    
E6E2:          TSTA    
E6E3:          RTS     
 ; ------------------------------------------
E6E4:  LE6E4   RTS     
 ; ------------------------------------------
E6E5:  LE6E5   LDX     #$E755
E6E8:          JSR     LE6BC
E6EB:          BNE     LE6F1
E6ED:          BCLR    L0099,#$10
E6F0:          RTS     
 ; ------------------------------------------
E6F1:  LE6F1   BSET    L0099,#$10
E6F4:          RTS     
 ; ------------------------------------------
E6F5:  LE6F5   LDAA    L5B35				; 0000 0000 XMISH ERR WD 2 ALT
E6F8:          COMA    

E6F9:          ANDA    L5B2C				; 1010 0010, MASK XMISSH ERR WD 2
E6FC:          ANDA    L0017				; 
E6FE:          ANDA    #$02					; b1 1 = ERR 28, TRANS RANGE PRESS SW

E700:          BNE     LE70F
											;
E702:          LDAA    L5B3A				; 0000 0000 XMISH ERR WD 7 ALT
E705:          COMA    
E706:          ANDA    L5B31
E709:          ANDA    L001C
E70B:          ANDA    #$0020
E70D:          BEQ     LE713
E70F:  LE70F   BSET    L0098,#$04
E712:          RTS     
 ; ------------------------------------------
E713:  LE713   BCLR    L0098,#$04
E716:          RTS     
			;----------------------------------------------



			;----------------------------------------------
			; 
        ;---------------------------------------------
        ORG $E717   ;                      
                    ;---------------------------------
LE717   FDB $01A2   ;
LE719   FDB $0080   ;
LE71B   FDB $0000   ;
LE71D   FDB $3D87   ;
LE71F   FDB $4401   ;
LE721   FDB $F270   ;
LE723   FDB $3C18   ;
LE725   FDB $6637   ;
LE727   FDB $8E74   ;
LE729   FDB $01A0   ;
LE72B   FDB $0010   ;
LE72D   FDB $0000   ;
LE72F   FDB $0404   ;
LE731   FDB $7400   ;
LE733   FDB $0201   ;
LE735   FDB $0008   ;
LE737   FDB $0029   ;
LE739   FDB $8530   ;
LE73B   FDB $0020   ;
LE73D   FDB $0000   ;
LE73F   FDB $0000   ;
LE741   FDB $0480   ;
LE743   FDB $0000   ;
LE745   FDB $0000   ;
LE747   FDB $0008   ;
LE749   FDB $0000   ;
LE74B   FDB $0430   ;
LE74D   FDB $0182   ;
LE74F   FDB $0380   ;
LE751   FDB $0000   ;
LE753   FDB $0801   ;
LE755   FDB $0001   ;
LE757   FDB $E200   ;
LE759   FDB $0000   ;
LE75B   FDB $002D   ;
LE75D   FDB $0070   ;
LE75F   FDB $123B   ;
LE761   FDB $042F   ;
LE763   FDB $CE5B   ;

LE765          TEST

E766:          BRCLR   0,X,#$40,LE78E		;
											;

E76A:          LDAA    L0160

E76D:          LDAB    L082D
E770:          CMPB    $13,X
E772:          BCS     LE782
E774:          BRCLR   L0016,#$40,LE78E		;
											;

E778:          INCA    
E779:          CMPA    $14,X
E77B:          BCS     LE78F
E77D:          BCLR    L0016,#$40

E780:          BRA     LE78E

 
E782:  LE782   BRSET   L0016,#$40,LE78E		;
											;
E786:          INCA    						;
E787:          CMPA    $14,X				;
E789:          BCS     LE78F				;
											;
E78B:          BSET    L0016,#$40			;
E78E:  LE78E   CLRA    						;
E78F:  LE78F   STAA    L0160				;
										
E792:          RTS     					
 		;--------------------------------------------------


		;--------------------------------------------------
		;  ERR 15 PARAMS
		;  LOW COOLANT TEMP
		;
		;--------------------------------------------------
E793:  LE793   BRSET   L003B,#$04,LE7C6		; BR IF b2, (EXIT IF ANY ERROR)
											;
E797:          LDX     #$5B00				; INDEX ERR MASKS
 											;
E79A:          BRCLR   0,X,#$20,LE7C2		; BR IF NOT b5
											; 
E79E:          LDAA    L0161				; ERR 15 TIMER
											;
E7A1:          LDAB    L082D				;
E7A4:          CMPB    $15,X				; (5B15), 254, A/D BIN COOL MIN TO ENBLE ERR 15
E7A6:          BHI     LE7B6				; BR IF 
											;
E7A8:          BRCLR   L0016,#$20,LE7C2		; BR IF 
											;
E7AC:          INCA    						;
E7AD:          CMPA    $16,X				; (5B16), 1 SEC REQ FOR ERR 15 
E7AF:          BCS     LE7C3				; BR IF 
											;
E7B1:          BCLR    L0016,#$20			; CLR b5, (LO COOL TEMP)

E7B4:          BRA     LE7C2


E7B6:  LE7B6   BRSET   L0016,#$20,LE7C2		; BR IF b5, (LO COOL TEMP) 
											;
E7BA:          INCA    						; INCR TIMER
E7BB:          CMPA    $16,X				; (5B16), 1 SEC REQ FOR ERR 15
E7BD:          BCS     LE7C3				;
											;
E7BF:          BSET    L0016,#$20			; SET b5, (LO COOL TEMP) 
E7C2:  LE7C2   CLRA    						; CLR ERR 15 TIMER
E7C3:  LE7C3   STAA    L0161				; ERR 15 TIMER

E7C6:  LE7C6   RTS     
  		;--------------------------------------------------
 
 

		;--------------------------------------------------
 		; HIGH TPS, ERR 21 SUBROUTINE
		;
		;
  		;--------------------------------------------------
E7C7:  LE7C7   BRSET   L003B,#$04,LE807		; BR IF b2, (EXIT IF ANY ERROR) 
											;
E7CB:          LDX     #$5B00				; INDEX ERR MASKS

			;------------------------------
			; (5B00), 1111 0001, ERR WD 1
			;
			; b0 1 = ERR 21, HIGH TPS
			;------------------------------
E7CE:          BRCLR   0,X,#$01,LE803		; ($5B00) BR IF NOT b0, (EXIT)
											;
E7D2:          LDAA    L0162				; ERR 21 TIMER 
											;
E7D5:          LDAB    L00A6				; TPS A/D (BIN)
E7D7:          CMPB    $1C,X				; ($5B1C) 249, A/D TPS MIN FOR ERR 21
E7D9:          BHI     LE7F6				; BR IF ERR
											;
E7DB:          BRSET   L0094,#$01,LE803		; BR IF b0, (EXIT)
											;
E7DF:          BSET    L0094,#$01			; SET b0 
											;
E7E2:          BRCLR   L0016,#$01,LE803		; BR IF NOT b0, (EXIT, PRIOR ERR 21)
											;
E7E6:          LDAB    L001F				; ERR 21 CNT'R, HI TPS
E7E8:          CMPB    L5B1E 				; IF ERR 21 CNT'S L.T. 5 ENABLE RESET OF ERR  21				;
E7EB:          BCC     LE803				; BR IF CNT'R > 5
											;
E7ED:          INCB    					    ; INCR CNT'R
E7EE:          INCB     					; INCR CNT'R   
E7EF:          STAB    L001F				; ERR 21 CNT'R
											; 
E7F1:          BCLR    L0016,#$01			; CLR b0, (ERR 21)

E7F4:          BRA     LE803

E7F6:  LE7F6   BRSET   L0016,#$01,LE803		; BR IF NOT b0 <PRIOR ERR 21)
E7FA:          INCA    						;
E7FB:          CMPA    L5B1D				; 1 SEC QUAL TIME FOR ERR 21
E7FE:          BCS     LE804				; BR IF TIME < 1 SEC
											;
E800:          BSET    L0016,#$01			; SET b0, TPS ERR 21 (----***
											;
E803:  LE803   CLRA    						; CLR ERR 21 TIMER
E804:  LE804   STAA    L0162				; ERR 22 TIMER 
		
E807:  LE807   RTS     
  		;--------------------------------------------------
 
 
		;--------------------------------------------------
 		; LOW TPS, ERR 22
		;
		;
  		;--------------------------------------------------
E808:  LE808   BRSET   L003B,#$04,LE846		; BR IF b2, (EXIT IF ANY ERROR)
											;
E80C:          LDX     #$5B00				; INDEX ERR MASKS
											;

				;------------------------------
				; ($5B01) 1010 0010, ERR WD 2
				;
				; b7 1 = ERR 22, TPS LOW 
				;------------------------------
E80F:          BRCLR   1,X,#$80,LE842		; ($5B01) BR IF b7, 
											; 
E813:          LDAA    L0163				; ERR 22 TIMER
 											; 
E816:          LDAB    L00A6			   	; TPS A/D
E818:          CMPB    $1F,X				; ($5B1F), A/D TPS MAX FOR ERR 22
E81A:          BCS     LE836				;
											;
E81C:          BRSET   L0094,#$02,LE842		; BR IF 
											;
E820:          BSET    L0094,#$02			;
											;
E823:          BRCLR   L0017,#$80,LE842		; BR IF NOT b7
											;
E827:          LDAB    L0020				; ERR 22 CNT'R
E829:          CMPB    $21,X				; (5B21),IF ERR 22 CNT'S < 5 ENABLE RESET 
E82B:          BCC     LE842				; BR IF > THRESH 
											;
E82D:          INCB    						; INCR CNT'R
E82E:          INCB    						; INCR CNT'R
E82F:          STAB    L0020				; ERR 22 CNT'R
E831:          BCLR    L0017,#$80			; CLR b7 (ERR 22)

E834:          BRA     LE842


E836:  LE836   BRSET   L0017,#$80,LE842		; BR IF b7 
											;
E83A:          INCA    						; INCR TIME
E83B:          CMPA    $20,X				; ($5B20), 1 SEC QUAL TIME FOR ERR 22
E83D:          BCS     LE843				; BR IF 
											;
E83F:          BSET    L0017,#$80			; SET b7, ERR 22  <----***
E842:  LE842   CLRA    						;
E843:  LE843   STAA    L0163				; CLR ERR 22 TIMER

E846:  LE846   RTS     
 		;--------------------------------------------------


 		;--------------------------------------------------
		; ERR 24, LOW OUTPUT XMISH SPEED (TOS)
		;
		;
 		;--------------------------------------------------
E847:  LE847   BRSET   L003B,#$04,LE8C7		; BR IF b2, (EXIT IF ANY ERROR)
											;
E84B:          LDX     #$5B00				; INDEX ERR MASKS
											;

			;------------------------------
			; L5B01, 1010 0010, ERR WD 2  
			; ERR 24
			;
			; b5 1 = ERR 24, OUTPUT XMISH SPD LOW
			;------------------------------
E84E:          BRCLR   1,X,#$20,LE8C3		; (5B01) BR IF NOT b5, 
											;
E852:          LDAA    L0164				; ERR 24 TIMER
											; 
E855:          BRSET   L0094,#$04,LE86F		; BR IF b2
											;
E859:          BSET    L0094,#$04			; SET b2
E85C:          BRCLR   L0017,#$20,LE8C3		;
											;
E860:          LDAB    L0021				; ERR 24 CNT'R
E862:          CMPB    $42,X				; (5B42), 7 ERR CNTS MIN TO SET ERR 24 
E864:          BCC     LE8C3				;
											;
E866:          INCB    						;
E867:          INCB    						;
E868:          STAB    L0021				; ERR 24 CNT'R
											;
E86A:          BCLR    L0017,#$20			; CLR b5, (ERR 24)

E86D:          BRA     LE8C3				


E86F:  LE86F   BRSET   L0017,#$20,LE8C3		; BR IF b5, (ERR24)
											;
E873:          BRSET   L0018,#$20,LE8C3		;
											;
E877:          BRSET   L0018,#$10,LE8C3		;
											;
E87B:          BRSET   L0016,#$01,LE8C3		;
											;
E87F:          BRSET   L0017,#$80,LE8C3		;
											;
E883:          LDAB    L01C0				; GET CURRENT MAP VALUE
E886:          CMPB    L5B45				; IF LD  L.T. 60 Kpa,     
											; DISABLE ERR 24 TEST
E889:          BCS     LE8C3				;
											;
E88B:          CMPB    L5B46				; IF LD  G.T. 255 Kpa,    
											; DISABLE ERR 24 TEST
E88E:          BHI     LE8C3				;
											;
E890:          LDAB    L00B2				;
E892:          CMPB    L5B47				; IF TPS L.T. 9.8% TPS,   
											; DISABLE ERR 24 TEST
E895:          BCS     LE8C3				;
											;
E897:          CMPB    L5B48				; IF TPS G.T. 99.6% TPS, 
											;  DISABLE ERR 24 TEST
E89A:          BHI     LE8C3				;
											;
E89C:          LDY     L00D1				;
E89F:          CPY     $3D,X				;
E8A2:          BCC     LE8C3				;
											;
E8A4:          BRSET   L001C,#$01,LE8C3		; BR IF b0, 
											;
E8A8:          BRSET   L0017,#$02,LE8C3		; BR IF b1
											;
E8AC:          LDY     L00C2				; RPM/8
E8B0:          CPY     $3F,X				; (5B3F)  3000 RPM MIN TO SET ERR 24
E8B3:          BLS     LE8C3				; BR IF LT 3K RPM
											;
E8B5:          BRCLR   L00A2,#$50,LE8BB		; BR IF NOT b4 & b6
											;
E8B9:          BRA     LE8C3				 



E8BB:  LE8BB   INCA    						; INCT ERR 24 TIMER
E8BC:          CMPA    $41,X				; (5B41) 3 SEC TIME QUAL, ERR 24
E8BE:          BCS     LE8C4				;
											;
E8C0:          BSET    L0017,#$20			; SET b5,  ERR 24
											;
E8C3:  LE8C3   CLRA    						; CLR ERR 24 TIMER
E8C4:  LE8C4   STAA    L0164				; ERR 24 TIMER

E8C7:  LE8C7   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;  ERR 28, PRESS SWITCH MANIFOLD
		;
		;
		;--------------------------------------------------
E8C8:  LE8C8   BRSET   L003B,#$04,LE904		; BR IF b2, (EXIT IF ANY ERROR) 
											;
E8CC:          LDX     #$5B00				; INDEX ERR MASKS
											;
			;------------------------------
			; $5B01, 1010 0010, ERR WD 2
			; b1 1 = ERR 28,
			;------------------------------
E8CF:          BRCLR   1,X,#$02,LE900		; BR IF NOT b1, 	
											;
E8D3:          LDAA    L0165				; ERR 28 TIMER
											;
E8D6:          BRSET   L00A2,#$80,LE8F4		; BR IF	b7
											;
E8DA:          BRSET   L0094,#$08,LE900		; BR IF	b3
											;
E8DE:          BSET    L0094,#$08			; SET b3
											;
E8E1:          BRCLR   L0017,#$02,LE900		; BR IF NOT b1
											;
E8E5:          LDAB    L0022				;
E8E7:          CMPB    $52,X				; (5B52), 10 ERR CNTS MIN TO SET ERR 28 
E8E9:          BCC     LE900				; BR IF
											;
E8EB:          INCB    						;
E8EC:          INCB    						;
E8ED:          STAB    L0022				;
E8EF:          BCLR    L0017,#$02			;

E8F2:          BRA     LE900				


E8F4:  LE8F4   BRSET   L0017,#$02,LE900		; BR IF
											;
E8F8:          INCA    						;
E8F9:          CMPA    $51,X				;
E8FB:          BCS     LE90					; BR IF
											;1
E8FD:          BSET    L0017,#$02			; SET b1, ERR 28
E900:  LE900   CLRA    						; CLR ERR 28 TIMER
E901:  LE901   STAA    L0165				; ERR 28 TIMER

E904:  LE904   RTS     
 		;--------------------------------------------------



		;--------------------------------------------------
		;  ERR 37,  BRAKE ON
		;
		;
		;--------------------------------------------------
E905:  LE905   BRSET   L003B,#$04,LE936		; BR IF b2, (EXIT IF ANY ERROR)

E909:          LDX     #$5B00				; INDEX ERR MASKS
E90C:          BRCLR   2,X,#$02,LE930		; (5B02) BR IF NOT b1, (ERR 37, BRAKE ON)
											;
E910:          BRSET   L009C,#$01,LE939		; BR IF
											;
E914:          BCLR    L0094,#$30			;
											;
E917:          BRCLR   L0018,#$02,LE930		; BR IF
											;
E91B:          LDAA    L0166				;
E91E:          INCA    						;
E91F:          CMPA    $57,X				; (5B57), 7 ERR CNTS MIN TO ENABLE ERR 37
E921:          BCS     LE933
											;
E923:          LDAB    L0023				; ERR 37 CNT'R
E925:          CMPB    $58,X				; (5B58), 8 ERR CNTS MIN TO SET ERR 37
E927:          BCC     LE930				; BR IF ERR CNT'S < THRESH
											;
E929:          INCB    						; INCR ERR CNT'R
E92A:          INCB    						; INCR ERR CNT'R
E92B:          STAB    L0023				; ERR 37 CNT'R

E92D:          BCLR    L0018,#$02			; CLR b1, (ERR 37)

E930:  LE930   JMP     LE999
E933:  LE933   JMP     LE99A
E936:  LE936   JMP     LE99D
 
 

E939:  LE939   BRSET   L0018,#$02,LE999		; BR IF
											;
E93D:          LDAB    L00D7
E93F:          CMPB    $53,X
E941:          BHI     LE94F				; BR IF
											;
E943:          BSET    L0094,#$10
E946:          BCLR    L0094,#$20
E949:          CLRA    
E94A:          STAA    L0182
E94D:          BRA     LE99D


E94F:  LE94F   BRCLR   L0094,#$10,LE99D		; BR IF
											;
E953:          CMPB    $0054,X
E955:          BCC     LE96B
E957:          BRSET   L0094,#$20,LE97F		; BR IF
											;
E95B:          LDAA    L0182
E95E:          ADDA    #$0001
E960:          BEQ     LE966				; BR IF
											;
E962:          STAA    L0182
E965:          CLRA    
E966:  LE966   STAA    L0183
E969:          BRA     LE99D
 ;
E96B:  LE96B   BSET    L0094,#$20
E96E:          LDAA    L0183
E971:          ADDA    #$0001
E973:          BEQ     LE978
E975:          STAA    L0183
E978:  LE978   LDAA    L0182
E97B:          CMPA    $0055,X
E97D:          BHI     LE984
E97F:  LE97F   BCLR    L0094,#$30
E982:          BRA     LE99D
 ;
E984:  LE984   LDAA    L0183
E987:          CMPA    $0056,X
E989:          BLS     LE99D
E98B:          BCLR    L0094,#$30
E98E:          LDAA    L0166
E991:          INCA    
E992:          CMPA    $0057,X
E994:          BCS     LE99A
E996:          BSET    L0018,#$02
E999:  LE999   CLRA    
E99A:  LE99A   STAA    L0166
E99D:  LE99D   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
E99E:  LE99E   BRSET   L003B,#$04,LE9D2		; BR IF b2, (EXIT IF ANY ERROR)
											;
E9A2:          LDX     #$5B00				; INDEX ERR MASKS
											;
E9A5:          BRCLR   $2,X,#$01,LE9CC		; 
											;
E9A9:          BRCLR   L009C,#$01,LE9D5		;
											;
E9AD:          BCLR    L0094,#$80			; CLR b7
E9B0:          BSET    L0094,#$40			; SET b6
											;
E9B3:          BRCLR   L0018,#$01,LE9CC		; BR IF NOT b0
											;
E9B7:          LDAA    L0167				;
E9BA:          INCA    						;
E9BB:          CMPA    $5D,X				;
E9BD:          BCS     LE9CF				;
											;
E9BF:          LDAB    L0024				; ERR 38 CNT'R,  BRAKE ON
E9C1:          CMPB    $5E,X				;
E9C3:          BCC     LE9CC				;
											;
E9C5:          INCB    
E9C6:          INCB    
E9C7:          STAB    L0024				; ERR 38 CNT'R,  BRAKE ON
E9C9:          BCLR    L0018,#$01
E9CC:  LE9CC   JMP     LEA3B
 ;
E9CF:  LE9CF   JMP     LEA3C
 ;
E9D2:  LE9D2   JMP     LEA3F
 ;
E9D5:  LE9D5   BRSET   L0018,#$01,LEA3B
E9D9:          LDAB    L00D7
E9DB:          CMPB    $59,X
E9DD:          BLS     LE9FD
E9DF:          BRCLR   L0094,#$40,LE9E7
E9E3:          CLRA    
E9E4:          STAA    L0185
E9E7:  LE9E7   BCLR    L0094,#$40
E9EA:          BSET    L0094,#$80
E9ED:          LDAA    L0185
E9F0:          ADDA    #$01
E9F2:          BEQ     LE9F8
E9F4:          STAA    L0185
E9F7:          CLRA    
E9F8:  LE9F8   STAA    L0184
E9FB:          BRA     LEA3F
 ;
E9FD:  LE9FD   BRCLR   L0094,#$80,LEA3F
EA01:          CMPB    $5A,X
EA03:          BLS     LEA14
EA05:          BSET    L0094,#$40
EA08:          LDAA    L0184
EA0B:          ADDA    #$01
EA0D:          BEQ     LEA3F
EA0F:          STAA    L0184
EA12:          BRA     LEA3F
 ;
EA14:  LEA14   LDAA    L0184
EA17:          CMPA    $5B,X
EA19:          BLS     LEA22
EA1B:          LDAA    L0185
EA1E:          CMPA    $5C,X
EA20:          BHI     LEA2A
EA22:  LEA22   BCLR    L0094,#$80
EA25:          BSET    L0094,#$40
EA28:          BRA     LEA3F
 ;
EA2A:  LEA2A   BCLR    L0094,#$80
EA2D:          BSET    L0094,#$40
EA30:          LDAA    L0167
EA33:          INCA    
EA34:          CMPA    $5D,X
EA36:          BCS     LEA3C
EA38:          BSET    L0018,#$01
EA3B:  LEA3B   CLRA    
EA3C:  LEA3C   STAA    L0167
EA3F:  LEA3F   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
EA40:  LEA40   BRSET   L003B,#$04,LEA7B		; BR IF b2, (EXIT IF ANY ERROR)
EA44:          LDX     #$5B00				; INDEX ERR MASKS


EA47:          BRCLR   $04,X,#$10,LEA73

EA4B:          LDY     L0169
EA4F:          LDAB    L00A7    		   	; BAT VOLTS, VDC/10
EA51:          CMPB    $63,X
EA53:          BHI     LEA65

EA55:          BRSET   L0097,#$01,LEA73
EA59:          BSET    L0097,#$01
EA5C:          BRCLR   L001A,#$10,LEA73
EA60:          BCLR    L001A,#$10
EA63:          BRA     LEA73
 ;
EA65:  LEA65   BRSET   L001A,#$10,LEA73
EA69:          INY     
EA6B:          CPY     $0064,X
EA6E:          BCS     LEA77
EA70:          BSET    L001A,#$10
EA73:  LEA73   LDY     #$0000
EA77:  LEA77   STY     L0169
EA7B:  LEA7B   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
EA7C:  LEA7C   BRSET   L003B,#$04,LEAB0		; BR IF b2, (EXIT IF ANY ERROR)
EA80:          LDX     #$5B00
EA83:          BRCLR   $0004,X,#$08,LEAAC
EA87:          LDAA    L016B

EA8A:          LDAB    L00A7    		   	; BAT VOLTS, VDC/10
EA8C:          CMPB    $66,X
EA8E:          BHI     LEAA0

EA90:          BRSET   L0095,#$02,LEAAC
EA94:          BSET    L0095,#$02
EA97:          BRCLR   L001A,#$08,LEAAC
EA9B:          BCLR    L001A,#$08
EA9E:          BRA     LEAAC
 ;
EAA0:  LEAA0   BRSET   L001A,#$08,LEAAC
EAA4:          INCA    
EAA5:          CMPA    $0067,X
EAA7:          BCS     LEAAD
EAA9:          BSET    L001A,#$08
EAAC:  LEAAC   CLRA    
EAAD:  LEAAD   STAA    L016B
EAB0:  LEAB0   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
EAB1:  LEAB1   BRSET   L003B,#$04,LEAE3		; BR IF b2, (EXIT IF ANY ERROR)
EAB5:          LDX     #$5B00				; INDEX ERR MASKS


EAB8:          BRCLR   $0005,X,#$40,LEADF
EABC:          LDAA    L016C
EABF:          LDAB    L00A5
EAC1:          CMPB    $68,X
EAC3:          BCS     LEAD3
EAC5:          BRCLR   L001B,#$40,LEADF
EAC9:          INCA    
EACA:          CMPA    $69,X
EACC:          BCS     LEAE0
EACE:          BCLR    L001B,#$40
EAD1:          BRA     LEADF
 ;
EAD3:  LEAD3   BRSET   L001B,#$40,LEADF
EAD7:          INCA    
EAD8:          CMPA    $69,X
EADA:          BCS     LEAE0
EADC:          BSET    L001B,#$40
EADF:  LEADF   CLRA    
EAE0:  LEAE0   STAA    L016C
EAE3:  LEAE3   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
EAE4:  LEAE4   BRSET   L003B,#$04,LEB16
EAE8:          LDX     #$5B00
EAEB:          BRCLR   $0005,X,#$20,LEB12
EAEF:          LDAA    L016D
EAF2:          LDAB    L00A5
EAF4:          CMPB    $006B,X
EAF6:          BHI     LEB06
EAF8:          BRCLR   L001B,#$20,LEB12
EAFC:          INCA    
EAFD:          CMPA    $6C,X
EAFF:          BCS     LEB13
EB01:          BCLR    L001B,#$20
EB04:          BRA     LEB12
 ;
EB06:  LEB06   BRSET   L001B,#$20,LEB12
EB0A:          INCA    
EB0B:          CMPA    $6C,X
EB0D:          BCS     LEB13
EB0F:          BSET    L001B,#$20
EB12:  LEB12   CLRA    
EB13:  LEB13   STAA    L016D
EB16:  LEB16   RTS     
 ; ------------------------------------------
EB17:  LEB17   RTS     
 ; ------------------------------------------
EB18:  LEB18   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
EB19:  LEB19   BRSET   L003B,#$04,LEB4C		; BR IF b2, (EXIT IF ANY ERROR)
EB1D:          LDX     #$5B00				; INDEX ERR MASKS


EB20:          BRCLR   $0005,X,#$04,LEB48
EB24:          LDAA    L016E
EB27:          LDAB    L02F3 				; ADBARO, BARO A/D
EB2A:          CMPB    $006D,X
EB2C:          BHI     LEB3C
EB2E:          BRCLR   L001B,#$04,LEB48
EB32:          INCA    
EB33:          CMPA    $006E,X
EB35:          BCS     LEB49
EB37:          BCLR    L001B,#$04
EB3A:          BRA     LEB48
 ;
EB3C:  LEB3C   BRSET   L001B,#$04,LEB48
EB40:          INCA    
EB41:          CMPA    $006E,X
EB43:          BCS     LEB49
EB45:          BSET    L001B,#$04
EB48:  LEB48   CLRA    
EB49:  LEB49   STAA    L016E
EB4C:  LEB4C   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
EB4D:  LEB4D   BRSET   L003B,#$04,LEB80		; BR IF b2, (EXIT IF ANY ERROR)
EB51:          LDX     #$5B00
EB54:          BRCLR   $0005,X,#$02,LEB7C
EB58:          LDAA    L016F
EB5B:          LDAB    L02F3 				; ADBARO, BARO A/D
EB5E:          CMPB    $0071,X
EB60:          BCS     LEB70
EB62:          BRCLR   L001B,#$02,LEB7C
EB66:          INCA    
EB67:          CMPA    $0072,X
EB69:          BCS     LEB7D
EB6B:          BCLR    L001B,#$02
EB6E:          BRA     LEB7C
 ;
EB70:  LEB70   BRSET   L001B,#$02,LEB7C
EB74:          INCA    
EB75:          CMPA    $0072,X
EB77:          BCS     LEB7D
EB79:          BSET    L001B,#$02
EB7C:  LEB7C   CLRA    
EB7D:  LEB7D   STAA    L016F
EB80:  LEB80   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
EB81:  LEB81   BRSET   L003B,#$04,LEBBF		; BR IF b2, (EXIT IF ANY ERROR)
EB85:          LDX     #$5B00				; INDEX ERR MASKS


EB88:          BRCLR   6,X,#$08,LEBBB
EB8C:          LDAA    L0174
EB8F:          LDY     L00B7
EB92:          CPY     $0081,X
EB95:          BCS     LEBA5
EB97:          BRCLR   L001C,#$08,LEBBB
EB9B:          INCA    
EB9C:          CMPA    $0083,X
EB9E:          BCS     LEBBC
EBA0:          BCLR    L001C,#$08
EBA3:          BRA     LEBBB
 ;
EBA5:  LEBA5   BRSET   L001C,#$08,LEBBB
EBA9:          BRSET   L0017,#$02,LEBBB
EBAD:          LDAB    L00A2
EBAF:          ANDB    #$0052
EBB1:          BNE     LEBBB
EBB3:          INCA    
EBB4:          CMPA    $0083,X
EBB6:          BCS     LEBBC
EBB8:          BSET    L001C,#$08
EBBB:  LEBBB   CLRA    
EBBC:  LEBBC   STAA    L0174

EBBF:  LEBBF   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
EBC0:  LEBC0   BRSET   L003B,#$04,LEC2C		; BR IF b2, (EXIT IF ANY ERROR)
EBC4:          LDX     #$5B00				; INDEX ERR MASKS


EBC7:          BRCLR   6,X,#$04,LEC28
EBCB:          LDD     L00D5
EBCD:          SUBD    L00CC
EBCF:          BPL     LEBD5
EBD1:          NEGB    
EBD2:          NEGA    
EBD3:          SBCA    #$0000
EBD5:  LEBD5   BRCLR   L00A2,#$50,LEBDF
EBD9:          CPD     L5B88
EBDD:          BRA     LEBE3
 ;
EBDF:  LEBDF   CPD     L5B86
EBE3:  LEBE3   BHI     LEC00
EBE5:          BRSET   L0095,#$10,LEC28
											;
EBE9:          BSET    L0095,#$10
EBEC:          BRCLR   L001C,#$04,LEC28
											;
EBF0:          LDAB    L0029
EBF2:          CMPB    L5B8C
EBF5:          BCC     LEC28
											;
EBF7:          INCB    
EBF8:          INCB    
EBF9:          STAB    L0029
EBFB:          BCLR    L001C,#$04
EBFE:          BRA     LEC28
 ;
EC00:  LEC00   BRSET   L001C,#$04,LEC28
											;
EC04:          LDAA    L01AB
EC07:          BNE     LEC28
											;
EC09:          LDD     L01AC
EC0C:          CPD     L5B8A
EC10:          BCS     LEC28
											;
EC12:          LDAA    L00A1
EC14:          CMPA    #$00FF
EC16:          BNE     LEC28
											;
EC18:          BRSET   L0017,#$02,LEC28
											;
EC1C:          LDAA    L0175
EC1F:          INCA    
EC20:          CMPA    L5B8D
EC23:          BCS     LEC29
											;
EC25:          BSET    L001C,#$04

EC28:  LEC28   CLRA    
EC29:  LEC29   STAA    L0175

EC2C:  LEC2C   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
EC2D:  LEC2D   BRSET   L003B,#$04,LEC78		; BR IF b2, (EXIT IF ANY ERROR)
EC31:          LDX     #$5B00				; INDEX ERR MASKS


EC34:          BRCLR   6,X,#$02,LEC74		; BR IF NOT b1
											;
EC38:          LDAA    L0176
EC3B:          BRSET   L008E,#$80,LEC63		; BR IF b7
											;
EC3F:          LDAB    L014F
EC42:          BPL     LEC45
											;
EC44:          NEGB    
EC45:  LEC45   CMPB    $8E,X
EC47:          BHI     LEC63
											;
EC49:          BRSET   L0095,#$20,LEC74		; BR IF b6
											;
EC4D:          BSET    L0095,#$20
EC50:          BRCLR   L001C,#$02,LEC74		; BR IF NOT b1
											;
EC54:          LDAB    L002A
EC56:          CMPB    $90,X
EC58:          BCC     LEC74
											;
EC5A:          INCB    
EC5B:          INCB    
EC5C:          STAB    L002A
EC5E:          BCLR    L001C,#$02

EC61:          BRA     LEC74


EC63:  LEC63   BRSET   L001D,#$80,LEC74		; BR IF b7
											;
EC67:          TST     L0178
EC6A:          BNE     LEC74
EC6C:          INCA    
EC6D:          CMPA    $8F,X
EC6F:          BCS     LEC75
											;
EC71:          BSET    L001C,#$02
EC74:  LEC74   CLRA    
EC75:  LEC75   STAA    L0176

EC78:  LEC78   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
EC79:  LEC79   BRSET   L003B,#$04,LECCB		; BR IF b2, (EXIT IF ANY ERROR)
											;
EC7D:          LDX     #$5B00				; INDEX ERR MASKS


EC80:          BRCLR   $07,X,#$80,LECC7		; BR IF NOT b7
											;
EC84:          LDD     L01AC
EC87:          CPD     L5B9B
EC8B:          BCS     LECC7
EC8D:          BRSET   L1D,#$80,LEC9C		; BR IF b3, 
											;
EC91:          LDAB    $97,X
EC93:          SUBB    $96,X
EC95:          LDAA    L00B5
EC97:          MUL     
EC98:          ADCA    $96,X
EC9A:          BRA     LECA5



EC9C:  LEC9C   LDAB    $99,X
EC9E:          SUBB    $98,X
ECA0:          LDAA    L00B5
ECA2:          MUL     
ECA3:          ADCA    $98,X
ECA5:  LECA5   TAB     

ECA6:          LDAA    L0178
ECA9:          CMPB    L00A7    		   	; BAT VOLTS, VDC/10
ECAB:          BHI     LECBB
											;
ECAD:          BRCLR   L001D,#$80,LECC7		; BR IF NOT b7
											;
ECB1:          INCA    
ECB2:          CMPA    $9A,X
ECB4:          BCS     LECC8
ECB6:          BCLR    L001D,#$80
ECB9:          BRA     LECC7
 ;
ECBB:  LECBB   BRSET   L001D,#$80,LECC7		; BR IF b7
											;
ECBF:          INCA    
ECC0:          CMPA    $9A,X
ECC2:          BCS     LECC8

ECC4:          BSET    L001D,#$80
ECC7:  LECC7   CLRA    

ECC8:  LECC8   STAA    L0178

ECCB:  LECCB   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
ECCC:  LECCC   BRSET   L003B,#$04,LECFE		; BR IF b2, (EXIT IF ANY ERROR)
											;
ECD0:          LDX     #$5B00				; INDEX ERR MASKS


ECD3:          BRCLR   $07,X,#$20,LECFA		; (5B07)
											;
ECD7:          LDAA    L0179


ECDA:          BRSET   L009F,#$08,LECEE		; BR IF b3,  ILLEGAL PATTERN REQUESTED
											;
ECDE:          BRSET   L0095,#$40,LECFA		; BR IF  b6, 
											;
ECE2:          BSET    L0095,#$40
ECE5:          BRCLR   L001D,#$20,LECFA		; BR IF NOT b5, 
											;
ECE9:          BCLR    L001D,#$20

ECEC:          BRA     LECFA
 

ECEE:  LECEE   BRSET   L001D,#$20,LECFA		; BR IF b5, 
											;
ECF2:          INCA    
ECF3:          CMPA    $9D,X
ECF5:          BCS     LECFB
											;
ECF7:          BSET    L001D,#$20

ECFA:  LECFA   CLRA    
ECFB:  LECFB   STAA    L0179

ECFE:  LECFE   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
ECFF:  LECFF   BRSET   L003B,#$04,LED3E		; BR IF b2, (EXIT IF ANY ERROR)
											;
ED03:          LDX     #$5B00				; INDEX ERR MASKS


ED06:          BRCLR   $07,X,#$08,LED36		; (5B07)
											;
ED0A:          LDY     L017A
ED0E:          LDAA    L00B5
ED10:          BRCLR   L001D,#$08,LED24		; BR IF NOT b3, 
											;
ED14:          CMPA    $9E,X
ED16:          BCC     LED36
											;
ED18:          INY     
ED1A:          CPY     $A0,X
ED1D:          BCS     LED3A
											;
ED1F:          BCLR    L001D,#$08
ED22:          BRA     LED36
 ;
ED24:  LED24   CMPA    $9F,X
ED26:          BCS     LED36
											;
ED28:          BRSET   L001B,#$40,LED36
ED2C:          INY     
ED2E:          CPY     $A0,X
ED31:          BCS     LED3A
											;
ED33:          BSET    L001D,#$08

ED36:  LED36   LDY     #$0000
ED3A:  LED3A   STY     L017A

ED3E:  LED3E   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
ED3F:  LED3F   BRSET   L003B,#$04,LED7F		; BR IF b2, (EXIT IF ANY ERROR)
											;
ED43:          LDX     #$5B00				; INDEX ERR MASKS

ED46:          BRCLR   $07,X,#$04,LED7B		; (5B07) ERR 81, QUAD DVR 1 & SHFT B ERR
ED4A:          LDAA    L017C
ED4D:          BRCLR   L009E,#$01,LED55		; BR IF NOT b0
											;
ED51:          BRCLR   L009E,#$20,LED6F		; BR IF NOT b5
											;
ED55:  LED55   BRSET   L0096,#$01,LED7B		; BR IF NOT b0
											;
ED59:          BSET    L0096,#$01
ED5C:          BRCLR   L001D,#$04,LED7B		; BR IF NOT b2
											;

ED60:          LDAB    L002B
ED62:          CMPB    $A3,X
ED64:          BCC     LED7B
											;
ED66:          INCB    
ED67:          INCB    
ED68:          STAB    L002B
ED6A:          BCLR    L001D,#$04
ED6D:          BRA     LED7B
 ;
ED6F:  LED6F   BRSET   L001D,#$04,LED7B		; BR IF b2, 
											;
ED73:          INCA    
ED74:          CMPA    $00A2,X
ED76:          BCS     LED7C
											;
ED78:          BSET    L001D,#$04

ED7B:  LED7B   CLRA    
ED7C:  LED7C   STAA    L017C

ED7F:  LED7F   RTS     
 		;------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
ED80:  LED80   BRSET   L003B,#$04,LEDC0		; BR IF b2, (EXIT IF ANY ERROR)
	
ED84:          LDX     #$5B00				; INDEX ERR MASKS
											;
ED87:          BRCLR   7,X,#$02,LEDBC	   	;
											;
ED8B:          LDAA    L017D
ED8E:          BRCLR   L009E,#$01,LED96		;
											;
ED92:          BRCLR   L009E,#$10,LEDB0		;
											;


ED96:  LED96   BRSET   L0096,#$02,LEDBC		; BR IF b1
											;
ED9A:          BSET    L0096,#$02			; SET b1
ED9D:          BRCLR   L001D,#$02,LEDBC		; BR IF NOT b1
											;
				
			;
			; ERR 82
			;
EDA1:          LDAB    L002C				; ERR 82 CNT'R
EDA3:          CMPB    $A5,X
EDA5:          BCC     LEDBC

EDA7:          INCB    						; INCR CNT VALUE
EDA8:          INCB    
EDA9:          STAB    L002C				; ERR 82 CNT'R


EDAB:          BCLR    L001D,#$02			; CLR b1

EDAE:          BRA     LEDBC


 
EDB0:  LEDB0   BRSET   L001D,#$02,LEDBC		; BR IF b1
											;
EDB4:          INCA    
EDB5:          CMPA    $A4,X
EDB7:          BCS     LEDBD
EDB9:          BSET    L001D,#$02

EDBC:  LEDBC   CLRA    
EDBD:  LEDBD   STAA    L017D

EDC0:  LEDC0   RTS     
 		;------------------------------------------


		;------------------------------------------
		;
		;
		;------------------------------------------
EDC1:  LEDC1   BRSET   L003B,#$04,LEE01		; BR IF b2, (EXIT IF ANY ERROR)
EDC5:          LDX     #$5B00				; INDEX ERR MASKS


EDC8:          BRCLR   $0007,X,#$01,LEDFD
EDCC:          LDAA    L017E
EDCF:          BRCLR   L009E,#$01,LEDD7
EDD3:          BRSET   L009E,#$30,LEDF1
EDD7:  LEDD7   BRSET   L0096,#$04,LEDFD
EDDB:          BSET    L0096,#$04
EDDE:          BRCLR   L001D,#$01,LEDFD
       LEDE1
EDE2:          LDAB    L002D
EDE4:          CMPB    $A7,X
EDE6:          BCC     LEDFD
EDE8:          INCB    
EDE9:          INCB    
EDEA:          STAB    L002D
EDEC:          BCLR    L001D,#$01
EDEF:          BRA     LEDFD
 ;
EDF1:  LEDF1   BRSET   L001D,#$01,LEDFD
EDF5:          INCA    
EDF6:          CMPA    $A6,X
EDF8:          BCS     LEDFE
EDFA:          BSET    L001D,#$01
EDFD:  LEDFD   CLRA    
EDFE:  LEDFE   STAA    L017E
EE01:  LEE01   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
EE02:  LEE02   BRSET   L003B,#$04,LEE5E		; BR IF b2, (EXIT IF ANY ERROR)

EE06:          LDX     #$5B00				; INDEX ERR MASKS


EE09:          BRCLR   $0003,X,#$80,LEE5A

EE0D:          LDAA    L0168
EE10:          BRSET   L0095,#$01,LEE2A

EE14:          BSET    L0095,#$01
EE17:          BRCLR   L0019,#$80,LEE5A

EE1B:          LDAB    L0025
EE1D:          CMPB    $62,X
EE1F:          BCC     LEE5A
											;
EE21:          INCB    
EE22:          INCB    
EE23:          STAB    L0025
EE25:          BCLR    L0019,#$80
EE28:          BRA     LEE5A
 ;
EE2A:  LEE2A   BRSET   L0019,#$80,LEE5A
EE2E:          LDY     L00EB
EE31:          CPY     $5F,X
EE34:          BLT     LEE5A
											;
EE36:          BRCLR   L0089,#$20,LEE5A
EE3A:          LDAB    L00D9  				; CURRENT GEAR
EE3C:          BEQ     LEE5A
											;
EE3E:          CMPB    #$0003
EE40:          BEQ     LEE5A
											;
EE42:          BRSET   L001C,#$08,LEE5A
EE46:          BRSET   L001C,#$01,LEE5A
EE4A:          BRSET   L0017,#$02,LEE5A
EE4E:          BRCLR   L00A2,#$0C,LEE5A
EE52:          INCA    
EE53:          CMPA    $61,X
EE55:          BCS     LEE5B
EE57:          BSET    L0019,#$80
EE5A:  LEE5A   CLRA    
EE5B:  LEE5B   STAA    L0168

EE5E:  LEE5E   RTS     

EE5F:  LEE5F   RTS     

EE60:  LEE60   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
EE61:  LEE61   BRSET   L003B,#$04,LEEBB		; BR IF b2, (EXIT IF ANY ERROR)
EE65:          LDX     #$5B00				; INDEX ERR MASKS


EE68:          BRCLR   6,X,#$20,LEEB7		; BR IF NOT b5
											;
EE6C:          LDAA    L0172
EE6F:          LDY     L00ED
EE72:          CPY     $77,X
EE75:          BHI     LEE91

EE77:          BRSET   L0095,#$04,LEEB7		; BR IF NOT b2
											;
EE7B:          BSET    L0095,#$04
EE7E:          BRCLR   L001C,#$20,LEEB7		; BR IF NOT b5
											;
EE82:          LDAB    L0028
EE84:          CMPB    $7A,X
EE86:          BCC     LEEB7
EE88:          INCB    
EE89:          INCB    
EE8A:          STAB    L0028

EE8C:          BCLR    L001C,#$20

EE8F:          BRA     LEEB7
 

EE91:  LEE91   BRSET   L001C,#$20,LEEB7		; BR IF NOT b5
											;
EE95:          LDAB    L00D9   				; CURRENT GEAR
EE97:          CMPB    #$0003
EE99:          BNE     LEEB7
EE9B:          BRCLR   L0089,#$20,LEEB7		; BR IF NOT b5
											;
EE9F:          BRSET   L001C,#$08,LEEB7		; BR IF NOT b3
											;
EEA3:          BRSET   L001C,#$01,LEEB7		; BR IF NOT b0
											;
EEA7:          BRSET   L0017,#$02,LEEB7		; BR IF NOT b1
											;
EEAB:          BRCLR   L00A2,#$0F,LEEB7		; BR IF NOT 0000 1111
											;
EEAF:          INCA    
EEB0:          CMPA    $79,X
EEB2:          BCS     LEEB8

EEB4:          BSET    L001C,#$20

EEB7:  LEEB7   CLRA    
EEB8:  LEEB8   STAA    L0172

EEBB:  LEEBB   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
EEBC:  LEEBC   BRSET   L003B,#$04,LEF2A		; BR IF b2, (EXIT IF ANY ERROR)
EEC0:          LDX     #$5B00				; INDEX ERR MASKS


EEC3:          BRCLR   6,X,#$10,LEF26		; BR IF NOT b4
											;
EEC7:          LDAA    L0173
EECA:          BRSET   L0095,#$08,LEEDA		; BR IF b3
											;
EECE:          BSET    L0095,#$08
EED1:          BRCLR   L001C,#$10,LEF26		; BR IF NOT b4
											;
EED5:          BCLR    L001C,#$10

EED8:          BRA     LEF26



EEDA:  LEEDA   BRSET   L001C,#$10,LEF26
EEDE:          LDY     L00EB
EEE1:          CPY     $7D,X
EEE4:          BLE     LEF26
											;
EEE6:          CPY     $7B,X
EEE9:          BGE     LEF26
											;
EEEB:          LDAB    L00B2
EEED:          CMPB    $80,X
EEEF:          BLS     LEF26
											;
EEF1:          BRSET   L0016,#$01,LEF26		; BR IF b0
											;
EEF5:          BRSET   L0017,#$80,LEF26		; BR IF b7
											;
EEF9:          BRSET   L0089,#$20,LEF26		; BR IF b5
											;
EEFD:          LDAB    L00D9   				; CURRENT GEAR
EEFF:          BEQ     LEF26

EF01:          CMPB    #$03
EF03:          BEQ     LEF26

EF05:          BRSET   L001C,#$08,LEF26		; BR IF b3, 
											;
EF09:          LDY     L01AC
EF0D:          CPY     $84,X
EF10:          BLS     LEF26
											;
EF12:          BRSET   L001C,#$01,LEF26		; BR IF b0
											;
EF16:          BRSET   L0017,#$02,LEF26		; BR IF b1
											;
EF1A:          BRCLR   L00A2,#$0C,LEF26		; BR IF 
											;
EF1E:          INCA    
EF1F:          CMPA    $7F,X
EF21:          BCS     LEF27
											;
EF23:          BSET    L001C,#$10
EF26:  LEF26   CLRA    
EF27:  LEF27   STAA    L0173

EF2A:  LEF2A   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
EF2B:  LEF2B   BRSET   L003B,#$04,LEF87		; BR IF b2, (EXIT IF ANY ERROR)

EF2F:          LDX     #$5B00				; INDEX ERR MASKS

EF32:          BRCLR   6,X,#$01,LEF83		; (b5B06), ERR 74, TURBINE SPEED
											;
EF36:          LDAA    L0177
EF39:          LDY     L00BD
EF3D:          CPY     $91,X
EF40:          BCS     LEF50
											;
EF42:          BRCLR   L001C,#$01,LEF83
EF46:          INCA    
EF47:          CMPA    $95,X
EF49:          BCS     LEF84
											;
EF4B:          BCLR    L001C,#$01

EF4E:          BRA     LEF83



EF50:  LEF50   BRSET   L001C,#$01,LEF83		; BR IF b0
											;
EF54:          BRCLR   L00A2,#$50,LEF5A		; BR IF b4 & b6
											;
EF58:          BRA     LEF83
 ;
EF5A:  LEF5A   BRSET   L0017,#$20,LEF83		; BR IF b5
											;
EF5E:          BRSET   L001C,#$04,LEF83		; BR IF b2
											;
EF62:          LDY     L00D3
EF65:          CPY     $93,X
EF68:          BLS     LEF83
EF6A:          BRSET   L001C,#$08,LEF83		; BR IF b3
											;
EF6E:          LDY     L01AC
EF72:          CPY     $84,X
EF75:          BLS     LEF83
EF77:          BRSET   L0017,#$02,LEF83		; BR IF b1
											;
EF7B:          INCA    
EF7C:          CMPA    $95,X
EF7E:          BCS     LEF84				; BR IF
											;
EF80:          BSET    L001C,#$01
EF83:  LEF83   CLRA    
EF84:  LEF84   STAA    L0177
EF87:  LEF87   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
EF88:  LEF88   BRSET   L003B,#$04,LEFB1		; BR IF b2, (EXIT IF ANY ERROR)
											;
EF8C:          LDX     #$5B00				; INDEX ERR MASKS

EF8F:          BRCLR   $08,X,#$40,LEFAE		; (5B08), BR IF NOT b6, 
											; ERR 85, RATIO UN-DEFINED OP REGION 
											;
EF93:          LDAA    L017F
EF96:          BRSET   L0096,#$08,LEFB4

EF9A:          BSET    L0096,#$08
EF9D:          BRCLR   L001E,#$40,LEFAE

EFA1:          LDAB    L002E
EFA3:          CMPB    $A9,X				;(5BA9)	 ERR 86,  LO RATIO
EFA5:          BCC     LEFAE

EFA7:          INCB    
EFA8:          INCB    
EFA9:          STAB    L002E

EFAB:          BCLR    L001E,#$40

EFAE:  LEFAE   JMP     LF02A
EFB1:  LEFB1   JMP     LF02E



EFB4:  LEFB4   LDY     L00F9
EFB7:          CPY     $AF,X
EFBA:          BLS     LEFC1

EFBC:          CPY     $B1,X
EFBF:          BCS     LF02A

EFC1:  LEFC1   CPY     $B3,X
EFC4:          BLS     LEFCB

EFC6:          CPY     $B5,X
EFC9:          BCS     LF02A

EFCB:  LEFCB   CPY     $B7,X
EFCE:          BLS     LEFD5

EFD0:          CPY     $B9,X
EFD3:          BCS     LF02A

EFD5:  LEFD5   LDAB    L00D9  				; CURRENT GEAR
EFD7:          CMPB    #$03
EFD9:          BEQ     LF02A

EFDB:          CPY     $BB,X
EFDE:          BLS     LEFE5

EFE0:          CPY     $BD,X
EFE3:          BCS     LF02A

EFE5:  LEFE5   BRSET   L001E,#$40,LF02A
EFE9:          BRSET   L0016,#$01,LF02A
EFED:          BRSET   L0017,#$80,LF02A
EFF1:          BRSET   L001E,#$10,LF02A
EFF5:          BRSET   L0017,#$02,LF02A
EFF9:          LDAB    L00B2
EFFB:          CMPB    $AC,X
EFFD:          BLS     LF02A

EFFF:          BRSET   L001C,#$08,LF02A
F003:          LDY     L01AC
F007:          CPY     $0084,X
F00A:          BLS     LF02A
F00C:          BRSET   L0017,#$20,LF02A
F010:          BRSET   L001C,#$04,LF02A
F014:          BRSET   L001C,#$01,LF02A
F018:          LDAB    L00D7
F01A:          CMPB    $00AD,X
F01C:          BLS     LF02A
F01E:          BRCLR   L00A2,#$2F,LF02A
F022:          INCA    
F023:          CMPA    $00A8,X
F025:          BCS     LF02B
F027:          BSET    L001E,#$40
F02A:  LF02A   CLRA    
F02B:  LF02B   STAA    L017F
F02E:  LF02E   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
F02F:  LF02F   BRSET   L003B,#$04,LF057		; BR IF b2, (EXIT IF ANY ERROR)
F033:          LDX     #$5B00				; INDEX ERR MASKS


F036:          BRCLR   $0008,X,#$20,LF055
F03A:          LDAA    L0180
F03D:          BRSET   L0096,#$10,LF059
F041:          BSET    L0096,#$10
F044:          BRCLR   L001E,#$20,LF0A8
F048:          LDAB    L002F
F04A:          CMPB    $00AB,X
F04C:          BCC     LF0A8
F04E:          INCB    
F04F:          INCB    
F050:          STAB    L002F
F052:          BCLR    L001E,#$20
F055:  LF055   BRA     LF0A8
 ;
F057:  LF057   BRA     LF0AC
 ;
F059:  LF059   BRSET   L001E,#$20,LF0A8
F05D:          LDAB    L00D9   				; CURRENT GEAR
F05F:          CMPB    #$0002
F061:          BCC     LF0A8
F063:          LDY     L00F9
F066:          CPY     $00B9,X
F069:          BHI     LF0A8
F06B:          BRSET   L0016,#$01,LF0A8
F06F:          BRSET   L0017,#$80,LF0A8
F073:          LDAB    L00B2
F075:          CMPB    $00AC,X
F077:          BLS     LF0A8
F079:          BRSET   L001C,#$08,LF0A8
F07D:          LDY     L01AC
F081:          CPY     $0084,X
F084:          BLS     LF0A8
F086:          BRSET   L0017,#$20,LF0A8
F08A:          BRSET   L001C,#$04,LF0A8
F08E:          BRSET   L001C,#$01,LF0A8
F092:          LDAB    L00D7
F094:          CMPB    $00AD,X
F096:          BLS     LF0A8
F098:          BRSET   L0017,#$02,LF0A8
F09C:          BRCLR   L00A2,#$0F,LF0A8
F0A0:          INCA    
F0A1:          CMPA    $00AA,X
F0A3:          BCS     LF0A9
F0A5:          BSET    L001E,#$20
F0A8:  LF0A8   CLRA    
F0A9:  LF0A9   STAA    L0180
F0AC:  LF0AC   RTS     
 		;--------------------------------------------------


		;--------------------------------------------------
		;
		;
		;
		;--------------------------------------------------
F0AD:  LF0AD   BRSET   L003B,#$04,LF0D5		; BR IF b2, (EXIT IF ANY ERROR)
F0B1:          LDX     #$5B00				; INDEX ERR MASKS


F0B4:          BRCLR   $0008,X,#$10,LF0D3
F0B8:          LDAA    L0181
F0BB:          BRSET   L0096,#$20,LF0D7
F0BF:          BSET    L0096,#$20
F0C2:          BRCLR   L001E,#$10,LF0D3
F0C6:          LDAB    L0030
F0C8:          CMPB    $00C0,X
F0CA:          BCC     LF12C
F0CC:          INCB    
F0CD:          INCB    
F0CE:          STAB    L0030
F0D0:          BCLR    L001E,#$10
F0D3:  LF0D3   BRA     LF12C
 ;
F0D5:  LF0D5   BRA     LF130
 ;
F0D7:  LF0D7   BRSET   L001E,#$10,LF12C
F0DB:          LDAB    L00D9  				; CURRENT GEAR
F0DD:          CMPB    #$0002
F0DF:          BCS     LF12C
F0E1:          LDY     L00F9
F0E4:          CPY     $00B3,X
F0E7:          BCS     LF12C
F0E9:          BRSET   L0016,#$01,LF12C
F0ED:          BRSET   L0017,#$80,LF12C
F0F1:          LDAB    L00B2
F0F3:          CMPB    $00AC,X
F0F5:          BLS     LF12C
F0F7:          LDAB    L00B5
F0F9:          CMPB    $00AE,X
F0FB:          BLS     LF12C
F0FD:          BRSET   L001C,#$08,LF12C
F101:          LDY     L01AC
F105:          CPY     $0084,X
F108:          BLS     LF12C
F10A:          BRSET   L0017,#$20,LF12C
F10E:          BRSET   L001C,#$04,LF12C
F112:          BRSET   L001C,#$01,LF12C
F116:          LDAB    L00D7
F118:          CMPB    $00AD,X
F11A:          BLS     LF12C
F11C:          BRSET   L0017,#$02,LF12C
F120:          BRCLR   L00A2,#$0F,LF12C
F124:          INCA    
F125:          CMPA    $00BF,X
F127:          BCS     LF12D
F129:          BSET    L001E,#$10
F12C:  LF12C   CLRA    
F12D:  LF12D   STAA    L0181

F130:  LF130   RTS     
  		;------------------------------------------


		;------------------------------------------
		; 		
		; b2 1 = ERR 89,  MAX ADPT LONG SHFT
		;------------------------------------------
F131:  LF131   BRSET   L003B,#$04,LF1A1		; BR IF b2, (EXIT IF ANY ERROR)
											;
F135:          LDX     #$5B00				; INDEX ERR MASKS
											;
F138:          BRCLR   8,X,#$04,LF1A1		; BR IF NOT b2,
											;
F13C:          BRSET   L0096,#$40,LF156		; BR IF b6
											;
F140:          BSET    L0096,#$40			; SET b6
											;
F143:          BRCLR   L001E,#$04,LF1A1		; BR IF NOT b2
											;

F147:          LDAB    L0031
F149:          CMPB    $CA,X
F14B:          BCC     LF1A1
											;
F14D:          INCB    
F14E:          INCB    
F14F:          STAB    L0031
F151:          BCLR    L001E,#$04

F154:          BRA     LF1A1


F156:  LF156   BRSET   L001E,#$04,LF1A1
F15A:          LDAA    L0148
F15D:          ASLA    
F15E:          BCS     LF166
											;
F160:          ASLA    
F161:          BCS     LF166
F163:          ASLA    
F164:          BCC     LF168
											;
F166:  LF166   LDAA    #$FF
F168:  LF168   LDY     #$BC6B
F16C:          LDAB    L00D9   				; CURRENT GEAR
F16E:          DECB    
F16F:          BMI     LF1A1
											;
F171:          ASLB    
F172:          ABY     
F174:          PSHX    
F175:          LDX     0,Y
F178:          PSHA    
F179:          LDAA    L00B2
F17B:          JSR     LF4C1				; 2d LK UP
F17E:          SUBA    #$0080
F180:          PULB    
F181:          PULX    
F182:          CBA     
F183:          BGT     LF1A1
F185:          LDAB    L00D9   				; CURRENT GEAR
F187:          DECB    
F188:          BMI     LF1A1
F18A:          BNE     LF1A3
F18C:          LDAB    L0136  				; TIME OF LATEST 1->2 SHIFT
F18F:          CMPB    $00C4,X
F191:          BLS     LF1DC
F193:          JSR     LF1DD
F196:          BCS     LF1DC
F198:          LDAA    L0032
F19A:          INCA    
F19B:          CMPA    $00C7,X
F19D:          BCC     LF1D9
F19F:          STAA    L0032
F1A1:  LF1A1   BRA     LF1DC
 ;
F1A3:  LF1A3   CMPB    #$0001
F1A5:          BNE     LF1BE

F1A7:          LDAB    L0137 				; TIME OF LATEST 3->3 SHIFT
F1AA:          CMPB    $C5,X
F1AC:          BLS     LF1DC

F1AE:          JSR     LF1DD
F1B1:          BCS     LF1DC
F1B3:          LDAA    L0033
F1B5:          INCA    
F1B6:          CMPA    $C8,X
F1B8:          BCC     LF1D9
F1BA:          STAA    L0033
F1BC:          BRA     LF1DC
 ;
F1BE:  LF1BE   CMPB    #$02
F1C0:          BNE     LF1DC
F1C2:          LDAB    L0138
F1C5:          CMPB    $C6,X
F1C7:          BLS     LF1DC
F1C9:          JSR     LF1DD
F1CC:          BCS     LF1DC
F1CE:          LDAA    L0034
F1D0:          INCA    
F1D1:          CMPA    $C9,X
F1D3:          BCC     LF1D9
F1D5:          STAA    L0034
F1D7:          BRA     LF1DC


F1D9:  LF1D9   BSET    L001E,#$04

F1DC:  LF1DC   RTS     
 			;------------------------------------------



F1DD:  LF1DD   SEC     
F1DE:          BRSET   L001B,#$40,LF20C		; BR IF NOT b6
											;
F1E2:          BRSET   L001B,#$20,LF20C		; BR IF NOT b5
											;
F1E6:          LDAB    L00B5
F1E8:          CMPB    $C1,X
F1EA:          BCS     LF20C
											;
F1EC:          SEC     
F1ED:          BRSET   L0016,#$01,LF20C		; BR IF b0, 
       LF1EF								;
F1F1:          BRSET   L0017,#$80,LF20C		; BR IF b7, 
       LF1EF								;
F1F5:          LDAB    L00B2
F1F7:          CMPB    $C2,X
F1F9:          BCS     LF20C
											;
F1FB:          SEC     
F1FC:          BRSET   L0017,#$20,LF20C		;
											;
F200:          BRSET   L001C,#$04,LF20C		;
											;
F204:          BRSET   L001C,#$01,LF20C		;
											;
F208:          LDAB    L00D7
F20A:          CMPB    $C3,X

F20C:  LF20C   RTS     
		;-------------------------------------------------


		;-------------------------------------------------
		; A/D ROUTINE ??
		;  READ COOL SENSOR
		;
		;-------------------------------------------------		                                                            
F20D:  LF20D   LDX     #$3000				; INDEX CPU REG'S
F210:          LDAA    #$07
F212:          JSR     LF275

F215:          LDAA    #$01					; 
F217:          JSR     LF25F				; A/D CNT'L MODE

F21A:          LDAA    $34,X				; A/D CH 4
F21C:          STAA    L082D

		;-------------------------------------------------
		; A/D ROUTINE ??
		;
		;
		;-------------------------------------------------		                                                            
F21F:          LDAA    #$06
F221:          JSR     LF275

F224:          LDAA    #$01
F226:          JSR     LF25F				; A/D CNT'L MODE

F229:          LDAA    $34,X				; A/D CH 4
F22B:          STAA    L01A1				; A/D RESULT

		;-------------------------------------------------
		; A/D ROUTINE, (MULT CH)
		;
		;
		;-------------------------------------------------		                                                            
F22E:          LDAA    #$01
F230:          BSR     LF275				; DELAY ROUTIN

F232:          LDAA    #$11
F234:          BSR     LF25F				; A.D CNT'L MODE

F236:          LDAA    $32,X				; A/D CH 2
F238:          STAA    L082F

F23B:          LDAA    $33,X				; A/D CH 3
F23D:          STAA    L00A5

F23F:          LDAA    $34,X				; A/D CH 4
F241:          STAA    L00A7    		   	; BAT VOLTS, VDC/10

F243:          BRA     LF25E
	   ;---------------------------------------------- 
 


	   ;----------------------------------------------
	   ; READ A/D CH'S FOR:
	   ;		CH 1 TPS, L00A6
	   ;		CH 2 MAP, LO82E
	   ;		CH 3 o2,  L01D5
	   ;
 	   ;----------------------------------------------
F245:  LF245   LDX     #$3000				; INDEX CPU REG'S

				;
				;   A/D SET UP
				; b4 1 = MULT
				: b2 1 = SEL CH 1 
				;
F248:          LDAA    #$14					; 0001 0100
F24A:          BSR     LF25F				; A/D SUB
											;
F24C:          LDAA    $31,X			    ; A/D CH 1
F24E:          STAA    L00A6				; TPS A/D
											;
F250:          BRSET   L0050,#$01,LF259		; BR IF b0, 
											;
F254:          LDAA    $32,X				; A/D CH 2
F256:          STAA    L082E				; A/D MAP VAL
											;
F259:  LF259   LDAA    $33,X				; A/D CH 3
F25B:          STAA    L01D5				; o2 VOLTAGE (A/D)

F25E:  LF25E   RTS     
 		;------------------------------------------


		;------------------------------------------
		;  READ A/D SUBROUTINE 
		;   	CALL WITH SELECT VAL IN A REG
		;  		RETURN WI A/D VAL'S IN A/D REG'S
 		;------------------------------------------
F25F:  LF25F   BCLR    L001A,#$02			; CLR b1
											;
F262:          STAA    L3030				; A/D CNT'L REG 
											;
F265:          LDAB    #12					; TIMER
											;
F267:  LF267   BRSET   $30,X,#$80,LF274		; BR IF b7, (CONV DONE)
											;
F26B:          DECB    						; DECR TIMER
F26C:          BNE     LF267				;
											;
F26E:          BSET    L003A,#$01			; SET b0
F271:          BSET    L001A,#$02			; SET b1

F274:  LF274   RTS     
    	;-------------------------------------------------


    	                                                        
    	;-------------------------------------------------
		; DELAY ROUTINE
		;
		;
		;-------------------------------------------------
F275:  LF275   BCLR    8,X,#$38				; CLR b5, b4 & b3
F278:          ASLA    
F279:          ASLA    
F27A:          ASLA    
F27B:          ORAA    8,X					; SET b5, b4 & b3
F27D:          STAA    8,X

F27F:          RTS     
    	;-------------------------------------------------



    	;-------------------------------------------------
		;  RESET BLM VALUES TO MID VALUES (128d)
		;
		;  BLM CELLS $02D4 th $02E8, 20 CELLS
		;
		;-------------------------------------------------
F280:  LF280   LDX     #$02B3
F283:          LDAA    #$80
F285:  LF285   STAA    0,X

F287:          INX     
F288:          CPX     #$02C7
F28B:          BLS     LF285
											;
F28D:          RTS     
    	;-------------------------------------------------

    	                                                        
    	;-------------------------------------------------
		;  CK ALL 20 BLM CELLS FOR MAX AND MIN LIMITS
		;  126/135	L48EC & L48ED
		;
    	;-------------------------------------------------
F28E:  LF28E   LDAA    L48FD				; MAX BLM AT INIT
F291:          LDAB    L48FE				; MIN BLM AT INIT
											;
F294:          LDX     #$02B3				; INDEX 1st BLM CELL
F297:  LF297   CMPA    0,X					; CK FOR MAX BLM 
F299:          BCC     LF29D				; BR IF BLM LT MAX
											;
F29B:          STAA    0,X					; USE MAX BLM
F29D:  LF29D   CMPB    0,X					; CK FOR MIN BLM
F29F:          BLS     LF2A3				; BR IF BLM GT MIN
											;
F2A1:          STAB    0,X
F2A3:  LF2A3   INX     						; NEXT ADDR
F2A4:          CPX     #$02C7				; CK FOR LAST ADDRESS
F2A7:          BLS     LF297				; BR IF NOT DONE
											;
F2A9:          RTS     
    	;-------------------------------------------------
		                                                            
    	************************************************
    	* ERPOM CHECK SUM ROUTINE
    	* TYPE $E6 ECM
    	*
    	*   Enter with:
    	*               X Pointing to start of CK SUM AREA
    	*
    	*   Exit with:
    	*               16 Bit ck sum results in Y Reg
    	*
    	*
    	************************************************
F2AA:  LF2AA   LDY     #$0000
F2AE:          PSHX    
F2AF:          PULA    
F2B0:          PULA 
   
F2B1:          CLRB    
F2B2:          LSRD    
F2B3:          LSRD    
F2B4:          LSRD    
F2B5:          PSHA    
F2B6:          TBA     
F2B7:          BEQ     LF2C2
F2B9:  LF2B9   LDAB    0,X
F2BB:          ABY     
F2BD:          INX     
F2BE:          ADDA    #$20
F2C0:          BNE     LF2B9
											;
F2C2:  LF2C2   LDAB    #$08
F2C4:          PULA    
F2C5:  LF2C5   XGDY    
F2C7:          ADDB    0,X
F2C9:          ADCA    #$00

F2CB:          ADDB    $01,X
F2CD:          ADCA    #$00

F2CF:          ADDB    $02,X
F2D1:          ADCA    #$00

F2D3:          ADDB    $03,X
F2D5:          ADCA    #$00

F2D7:          ADDB    $04,X
F2D9:          ADCA    #$00

F2DB:          ADDB    $05,X
F2DD:          ADCA    #$00

F2DF:          ADDB    $06,X
F2E1:          ADCA    #$00

F2E3:          ADDB    $07,X
F2E5:          ADCA    #$00

F2E7:          XGDY    
F2E9:          ABX     
F2EA:          INCA    
F2EB:          BNE     LF2C5

			;
			; TOGGLE COP 
			;
F2ED:          LDAA    #$55
F2EF:          STAA    L303A
F2F2:          COMA    
F2F3:          STAA    L303A

F2F6:          CLRA    
F2F7:          CPX     #$0000
F2FA:          BNE     LF2C5

F2FC:          RTS     
 		;----------------------------------------------


        ***********************************************
        * CLEAR RAM ROUTINE 
        * TYPE $E6 ECM
        *
        *   ENTER WITH:
        *               X = ADDR POINTER
        *               D = NUMBER OF BYTES TO CLEAR
        *
        * EXIT WITH:
        *               NOTHING
        *
        ***********************************************         
F2FD:  LF2FD   BITB    #$07
F2FF:          BEQ     LF30B
											;
F301:          CLR     0,X
F303:          INX     
F304:          SUBD    #$01
F307:          BNE     LF2FD

F309:          BRA     LF325
 		;----------------------------------------------
 
 
F30B:  LF30B   LSRD    
F30C:          LSRD    
F30D:          LSRD    
F30E:          TBA     
F30F:          LDAB    #$08
F311:          LDY     #$0000
F315:  LF315   STY     0,X
F318:          STY     2,X
F31B:          STY     4,X
F31E:          STY     6,X
F321:          ABX     
F322:          DECA    
F323:          BNE     LF315


F325:  LF325   RTS     
		;----------------------------------------------

        ***********************************************
        * CK SUM KA RAM 
        * TYPE $E6 ECM
        *
        *   $000A -> $0014, 10 BBYTES
        *
        * ENTER WITH:
        *               NOTHING
        * EXIT WITH:
        *               A = CK SUM
        ***********************************************
F326:  LF326   LDX     #$0014		; POINT TO TOP OF KA RAM
F329:          LDAB    #$0A			; 10 BYTES
F32B:          CLRA 				; ZERO CK SUM VAS
   
F32C:  LF32C   SUBA    0,X			;
F32E:          DEX     				; DECR ADDR POINTER
F32F:          DECB    				; DEC BYTE CNT
F330:          BNE     LF32C		; LP TILL DONE

F332:          RTS     
		;----------------------------------------------



		;-----------------------------------------
		;
		;
		;
		;-----------------------------------------
F333:  LF333   LDX     #$0009
F336:          LDY     #$F37F

F33A:  LF33A   LDAA    $0A,X
F33C:          ANDA    0,Y
F33F:          STAA    $0A,X
F341:          LDAA    $15,X
F343:          ANDA    0,Y
F346:          STAA    15,X

F348:          LDAA    55,X
F34A:          ANDA    0,Y
F34D:          STAA    $55,X

F34F:          DEY     
F351:          DEX     
F352:          BNE     LF33A

		;----------------------------
		; MODE 1, WD #3, FLAGWORD,
		;		  b0 7 =  ERR 42, EST MON  
		;----------------------------
F354:          BCLR    L0004,#$80

F357:          BCLR    L0044,#$80			; CLR b3, LOCKED IN ERR 42A
											
F35A:          BCLR    L0072,#$01
F35D:          BCLR    L006F,#$10
F360:          BCLR    L0070,#$01

		;-----------------------------
		;  CLR ... 
		;
		;----------------------------- 
F363:          CLRA    
F364:          STAA    L001F				; ERR 21 CNT'R, HIGH TPS
F366:          STAA    L0020				; ERR 21 CNT'R, LOW  TPS
F368:          STAA    L0817
F36B:          STAA    L021C
F36E:          STAA    L081C
F371:          JSR     LF326
F374:          STAA    L0015

F376:          RTS     
 		;------------------------------------------

 		;------------------------------------------
		;
		;
 		;------------------------------------------
F377:          CLI     
F378:          SEI     
F379:          FDIV    
F37A:          CMPA    #$D9
F37C:          STX     LFFFF
F37F:          STX     LCE00

F382:          DEX     
F383:          LDY     #$F3E3

F387:  LF387   LDAA    $0A,X
F389:          ANDA    0,Y
F38C:          STAA    $0A,X
F38E:          LDAA    $15,X
F390:          ANDA    0,Y
F393:          STAA    $15,X
F395:          DEY     
F397:          DEX     
F398:          BNE     LF387
											;
F39A:          BCLR    L0094,#$F0
F39D:          BCLR    L008E,#$80

			;
			; DTC ERROR COUNTERS
			;
F3A0:          CLRA    
F3A1:          STAA    L001F				; ERR 21 CNT'R, HIGH TPS
F3A3:          STAA    L0020				; ERR 22 CNT'R, LOW  TPS
F3A5:          STAA    L0021
F3A7:          STAA    L0022
F3A9:          STAA    L0023
F3AB:          STAA    L0024				; ERR 38 CNT'R,BRAKE ON
F3AD:          STAA    L0026
F3AF:          STAA    L0027
F3B1:          STAA    L0028
F3B3:          STAA    L0029
F3B5:          STAA    L002A
F3B7:          STAA    L002B
F3B9:          STAA    L002C
F3BB:          STAA    L002D
F3BD:          STAA    L002F
F3BF:          STAA    L0030
F3C1:          STAA    L0031
F3C3:          STAA    L0182
F3C6:          STAA    L0183
F3C9:          STAA    L0184
F3CC:          STAA    L0185
F3CF:          STAA    L0032
F3D1:          STAA    L0033
F3D3:          STAA    L0034

F3D5:          JSR     LF326

F3D8:          STAA    L0015

F3DA:          RTS     
 		;------------------------------------------

F3DB:          LDS     L005D
F3DD:          LDD     L7FE7
F3E0:          ADCA    L0000
F3E2:          NEGB    
F3E3:          ADDA    #$B6
       LF3E4
F3E5:          TSX     
F3E6:          ROR     $08,X
F3E8:          SUBA    #$B7
F3EA:          TSX     
F3EB:          ROR     $39,X

F3ED:  LF3ED   RTS							; also used as a Very short delay (RTS)     


		;-----------------------------------------
F3EE:  LF3EE   SEI     
F3EF:          LDD     L3FFC           		; I/O D PORT ..
F3F2:          JSR     LF3ED				; Very short delay (RTS)

F3F5:          ORAB    #$0008
F3F7:          BRCLR   L0072,#$80,LF3FD

F3FB:          ANDB    #$F7
F3FD:  LF3FD   STD     L3FFC           		; I/O D PORT ..

F400:          LDAA    L3060
F403:          ANDA    #$6F

F405:          LDAB    L004B
F407:          ANDB    #$90
F409:          STAB    L3060
F40C:          ABA     
F40D:          STAA    L004B

F40F:          LDAA    L004C
F411:          STAA    L3062

F414:          LDAA    L3064				; I/O PORT C
F417:          STAA    L004D				; I/O PORT C

F419:          LDAA    L004E
F41B:          STAA    L3067
F41E:          CLI 
    
F41F:          RTS     
 			;------------------------------------------


F420:  LF420   PSHX    
F421:          TSX     
F422:          SUBD    0,X
F424:          PSHB    
F425:          BLT     LF42D
											;
F427:          LDAB    0,Y
F42A:          MUL     
F42B:          BRA     LF447


F42D:  LF42D   LDAB    0,Y
F430:          MUL     
F431:          SUBA    0,Y

F434:          BRA     LF447
      	;----------------------------------------------                                                 

 		;------------------------------------------
        ; TRANSMISSION LAG FILTER ROUTINE
        ;
        ;   ENTER WITH:
        ;           D = NEW VALUE
        ;           X = OLD VALUE
        ;           Y = FILT COEF
        ;
        ;   RETURN WITH:
        ;           D = FILTERED RESULT
        ;
 		;------------------------------------------
F436:  LF436   PSHX    
F437:          TSX     
F438:          SUBD    0,X
F43A:          PSHB    
F43B:          LDAB    0,Y
F43E:          BCS     LF443
											;
F440:          MUL     
F441:          BRA     LF447


F443:  LF443   MUL     
F444:          SUBA    0,Y
F447:  LF447   ADDD    0,X
F449:          STD     0,X

F44B:          PULA    
F44C:          LDAB    0,Y
F44F:          MUL     
F450:          ADCA    $01,X
F452:          TAB     
F453:          LDAA    0,X
F455:          ADCA    #$00
F457:          PULX    

F458:          RTS     
 		;------------------------------------------


 		;------------------------------------------
        ; LAG FILT
        ;
        ; Smooth 8 bit data (old VS new) using
        ; an 8 bit fuilt coef, (coef/256)
        ;
        ;   ENTER WITH:
        ;           X = OLD VAL
        ;           A = NEW	VAL
        ;           B = FILT COEF, (Q)
        ;
        ;   RETURN WITH:
        ;           X =	SAME AS ENTRY
        ;           A =	FILTERED RESULT
        ;           B =
        ;
 		;------------------------------------------
	   LF459:  PSHB    
F45A:          PSHX    
F45B:          TSX  
   
F45C:          SUBA    0,X
F45E:          BCS     LF463
									;
F460:          MUL     
F461:          BRA     LF466
 

F463:  LF463   MUL     
F464:          SUBA    2,X

F466:  LF466   PSHA    
F467:          PSHB    
F468:          LDD     1,X
F46A:          NEGB    
F46B:          BEQ     LF470
									;
F46D:          MUL     
F46E:          ADCA    #$00			; round off

F470:  LF470   PULB    
F471:          ABA     
F472:          TAB     
F473:          PULA    
F474:          ADCA    0,X
F476:          PULX    
F477:          INS     	

F478:          RTS     
 		;----------------------------------------------


 		;----------------------------------------------
		; FILTER ROUTINE
		;
		;
 		;----------------------------------------------
	   LF479:  SUBD    0,X			 ;
F47B:          PSHB    				 ;
F47C:          LDAB    0,Y			 ;
F47F:          BCS     LF484		 ;
F481:          MUL     				 ;
F482:          BRA     LF488		 ;
 ;									 ;
F484:  LF484   MUL     				 ;
F485:          SUBA    0,Y			 ;
									 ;
F488:  LF488   ADDD    0,X			 ;
F48A:          STD     0,X			 ;
F48C:          PULA    				 ;
F48D:          LDAB    0,Y			 ;
F490:          MUL     				 ;
F491:          ADCA    1,X			 ;
F493:          TAB     				 ;
F494:          LDAA    0,X			 ;
F496:          ADCA    #$00			 ;
									 ;
F498:          RTS     
 		;----------------------------------------------


 		;----------------------------------------------
		; LOOK UP SUB ROUTINE (2d)
		;
		;
 		;----------------------------------------------
F499:  LF499   CLRB    
F49A:  LF49A   CMPA    0,X
F49C:          BLS     LF4A0
											;
F49E:          LDAA    0,X
F4A0:  LF4A0   INX     
F4A1:          BSR     LF4BD

F4A3:          RTS     
 		;----------------------------------------------


 		;----------------------------------------------
		;
		;
		;
 		;----------------------------------------------
F4A4:  LF4A4   PSHX    
F4A5:          PSHB    
F4A6:          SUBA    0,X
F4A8:          BCC     LF4AB
											;
F4AA:          CLRA    
F4AB:  LF4AB   CMPA    1,X
F4AD:          BLS     LF4B1
											;
F4AF:          LDAA    1,X
F4B1:  LF4B1   LDAB    #$02
F4B3:          ABX     
F4B4:          BRA     LF4B8
		;---------------------------------------------- 

    	********************************************************
    	; LKUP_2DA.SRC
    	;
    	; LF4BD:    2D table lookup w/offset
    	;           spaced from table
    	;
    	; LF4B6:    2D table look up w/no offset
    	;           spacing from table (4 = 5 Line table)
    	;
    	; LF4C1:    2D table lookup 
    	;           spaced 16
    	;
    	;  Returns a value from a table based on the value of an
    	;    independent varable. Only certin values of indepenednt 
    	;    varable are represnted in the table.
    	;
    	; Call Arg:
    	;   A Reg = independent var
    	;   X Reg = Address of table
    	;
    	; LF4BD: 
    	;   B Reg = Value of independednt var
		;
    	; LF4B6: 
    	;   B Reg = Ignored & 1st tabulated val is 0
    	;
    	; LF4B6
    	;   1st byt of table = 256/H (subsequent bytes are the tabulated values)
    	;
    	;   EXAMPLE:
    	;        2 for H = 128, (3 table entries max)
    	;       16 for H = 16, (17 table entries max)
    	;       25 for H = 10.4, (26 table entries max)
    	;
    	; LF4B6 & LKU_PQ
    	;   This byte omitedm H = 16
    	;
    	; RETURNS WITH: A Reg = table value
    	;
    	; EXEC TIME:    LE3C5 	= 81 - 82 cyc
    	;       		LKUP_2D = 78 - 81
    	;       		LKUP_Q  = 73 - 74
    	;
    	; STACK REQ:        *
    	;
    	*******************************************************

		;----------------------------------------------
        ;  2D LK UP W/LINE CNT        ;
        ;  ENTER W/VAR IN A reg
		;----------------------------------------------
F4B6:  LF4B6   PSHX    
F4B7:          PSHB    
F4B8:  LF4B8   LDAB    0,X				; GET LINE CNT
F4BA:          INX     					; INCR TO 1st DATA LINE
F4BB:          BRA     LF4C5			;
 

        ;-----------------------
        ; ENTRY, LF4BD
        ;-----------------------
F4BD:  LF4BD   SBA     
F4BE:          BCC     LF4C1				; 2d LK UP
F4C0:          CLRA    


        ;-----------------------
        ; ENTRY, LF4C1
        ; 2D LOOK UP, NO OFF SET
        ; (spaced 16)
        ;-----------------------
F4C1:  LF4C1   PSHX    
F4C2:          PSHB    
F4C3:          LDAB    #16

        ;---------------------------------
        ; Seperate  val into table offset
        ; & interp fraction
        ;--------------------------------
F4C5:  LF4C5   MUL     
F4C6:          PSHB    
F4C7:          TAB     
F4C8:          ABX 
    
        ;---------------------
        ;
        ;---------------------
F4C9:          LDD     0,X
F4CB:          SBA     
F4CC:          PULB    
F4CD:          BCC     LF4D5
											;
F4CF:          NEGA    

        ;-------------------------------
        ; Interp & round down if req'ed
        ;-------------------------------
F4D0:          MUL     
F4D1:          ADCA    0,X
F4D3:          BRA     LF4DB
 

F4D5:  LF4D5   MUL     
F4D6:          ADCA    #$00
F4D8:          NEGA    
F4D9:          ADDA    0,X
F4DB:  LF4DB   PULB    
F4DC:          PULX    

F4DD:          RTS     
 		;------------------------------------------


		;-------------------------------------------
        ; LKUP_3D.SRC       $E6 PROCESSOR
        ;
        ; 3D Look up routine. Returns with the table value, 
        ; (interpolated),  based on 2 independent inputs.
        ;
        ; INPUTS:
        ;   1. R min value, (Rows)
        ;   2. Q min value, (Col's)
        ;   3. RNUM, number of Q Vals, (col's) 
        ;      in each R table
        ;   4. Thr 1st R table, R num entries in length
        ;
        ;       4 + RNUM secont R table
        ;       4 + (N-1) Nth R table
        ;
        ; CALL WITH:
        ;   A Reg = R input, (Row arg)
        ;   B Reg = Q input, (Coll arg)
        ;   X Reg = Table start address
        ;
        ; RETURNS WITH:
        ;   A Reg = F(Q,R)
        ;
        ; EXEC TIME:    257 - 264 Cycles
        ; SRACK REG:    9 Bytes
        ; CODE LENGTH:  114 BYTES
        ;
        ;
		;-------------------------------------------
F4DE:  LF4DE   PSHY    
F4E0:          PSHB    
F4E1:          PSHX    
F4E2:          SUBA    0,X	 	; Calc row arg offset, (limited to 0)
F4E4:          BCC     LF4E7

F4E6:          CLRA    
F4E7:  LF4E7   SUBB    $01,X 	;  Calc Col Arg offset, (Limited to 0)
F4E9:          BCC     LF4EC

F4EB:          CLRB    
F4EC:  LF4EC   PSHX    
F4ED:          PULY    		 	; Xfer Table addr to Y reg    
F4EF:          PSHA    
							 	; Save Row address 
F4F0:          LDAA    #16		; Split Col arg into table offset
								; & interp portion     
								; save interp portion to stack    

F4F2:          MUL     		 	
F4F3:          PSHB    		 	
F4F4:          TAB     		 	
F4F5:          ABX     
F4F6:          PULA    
F4F7:          PULB    
F4F8:          PSHA    
F4F9:          LDAA    #$10
F4FB:          MUL     
F4FC:          PSHB    
F4FD:          LDAB    $02,Y
F500:          MUL     
F501:          ABX     
F502:          PSHX    
F503:          LDAB    $02,Y
F506:          ABX     
F507:          TSY     
F509:          LDD     $03,X
F50B:          SBA     
F50C:          LDAB    $03,Y
F50F:          BCC     LF517

F511:          NEGA    
F512:          MUL     
F513:          ADCA    $03,X

F515:          BRA     LF51D
 
F517:  LF517   MUL     
F518:          ADCA    #$0000
F51A:          NEGA    
F51B:          ADDA    $03,X
F51D:  LF51D   PULX    
F51E:          PSHA    
F51F:          LDD     $03,X
F521:          SBA     
F522:          LDAB    $03,Y
F525:          BCC     LF52D
F527:          NEGA    
F528:          MUL     
F529:          ADCA    $03,X

F52B:          BRA     LF533
                                                             
        ;--------------------
        ; INTERP Y2, RND DOWN
        ;--------------------
F52D:  LF52D   MUL     
F52E:          ADCA    #$00
F530:          NEGA    
F531:          ADDA    $03,X
F533:  LF533   PULB    
F534:          PSHA    
F535:          SBA     
F536:          LDAB    $02,Y
F539:          BCC     LF542

F53B:          NEGA    
F53C:          MUL     
F53D:          ADCA    $01,Y

F540:          BRA     LF549
        
		;-------------------
        ; Interp Y & round
        ; down if nesessary
        :-------------------
F542:  LF542   MUL     
F543:          ADCA    #$00
F545:          NEGA    
F546:          ADDA    $01,Y
F549:  LF549   INS     
F54A:          PULX    
F54B:          PULX    
F54C:          PULB    
F54D:          PULY    

F54F:          RTS     
		;----------------------------------------------


    	*******************************************************
    	* MUL8X16.SRC       $E6 PROCESSOR
    	*
    	* 8 x 16 Multiply with 16 bit result result rounded 
    	*  to the upper 16 bits.
    	*
    	*   CALL WITH:  
    	*       A Reg = 8 BIT Multiplier
    	*       X Reg = Adderss og 16 bit Multiplicand
    	*       
    	*   RETURN WITH:
    	*       A Reg = MSB of 16 bit result
    	*       B Reg = LSB of 16 bit result
    	*
    	*   Exec time:  66 Cycles
    	*   Code length:    20 Bytes
    	*   Stack req:  3 Bytes
    	*
    	*   ORG $F161
    	********************************************************
F550:  LF550   PSHA    		   	; Save Multiplier   
F551:          LDAB    1,X	   	; Get LSB of multiplicand
F553:          MUL     		   	; MSB Partial product     
F554:          ADCA    #$00	   	; Round 

F556:          PULB    
F557:          PSHA    		   	; Save partial product    

F558:          LDAA    0,X	   	; Get MSB of multiplicand
F55A:          MUL     		   	; MSB Partial product     
F55B:          PSHX    		   	; Save    
F55C:          TSX     
F55D:          ADDB    2,X		; Add in LSB Partial prod
F55F:          ADCA    #$00		; Round
F561:          PULX    
F562:          INS     

F563:          RTS     
		;----------------------------------------------


    	*******************************************************
    	* 16x16 FIXED POINT MULTIPLY
    	*
    	* ROUNDING IS FORM LOW ORDER BYTE OF RESULT
    	* THE MIDDLE 2 BYTES RETURNED IN A & B REG'S
    	* 
    	* Calling:
    	*   X = multipicand
    	*   A = MSB of Multiplier
    	*   B = LSB of Multiplier
    	*
    	* Returring:
    	*   X+5 = Partial prod
    	*    +4 = Partial prod
    	*     3 = LSB of Multipicand
    	*     2 = MSB of Multipicand
    	*     1 = LSB of Multiplier
    	*     0 = MSB of Multiplier
    	*
    	*  ExCPUtion time: 155 Cycles
    	*
    	*******************************************************
F564:          PSHA					; Mk space on stack for MS byte
    								; of result    
F565:          PSHX    				; Space for partaial result    
F566:          PSHX    				; Multiplicand to stack    
F567:          PSHB    				; LSB of Multiplier    
F568:          PSHA    				; MSB of Multiplier    
F569:          TSX     
F56A:          LDAA    3,X
F56C:          MUL     
F56D:          ADCA    #0
F56F:          STAA    5,X

F571:          LDD     1,X

F573:          MUL     
F574:          ADDB    5,X
F576:          ADCA    #0
F578:          STD     4,X

F57A:          LDAA    0,X		; Get MSB of Mult'er
F57C:          LDAB    3,X		; Get LSB of mult'cnd
F57E:          CLR     6,X		; Clr MSB of product
F580:          MUL     			; MSB Multp'er * LSB Mult'cnd
F581:          ADDD    4,X		; Add result to tepm LSB of
								; final result

F583:          ROL     6,X		; Rotate CY in to overflow counter
F585:          STD     $04,X	; Get MSB of Mult'er

F587:          LDAA    0,X		; Get MSB of Mult'er
F589:          LDAB    2,X		; Get MSB of Mult'cnd
F58B:          MUL     			; MSB Mult'er * MS Mult'cnd     
F58C:          ADDB    4,X		; Add LSB of result to MSB of

F58E:          ADCA    6,X		; final result
F590:          STAB    4,X		; Add MSB of final to overflow counter
F592:          STD     2,X      ; Save final result


F594:          TSTA    
F595:          BEQ     LF59C	; IF NO OVERFLOW
								;
F597:          LDD     #$FFFF	; IF OVERFLOW
F59A:          STD     $04,X

F59C:  LF59C   PULX    
F59D:          PULX    
F59E:          PULA    
F59F:          PULB    
F5A0:          INS     

F5A1:          RTS     
 		;------------------------------------------


        *******************************************************
        *
        * MULT ROUTINE ????
		* USED FOR XMISH
        *******************************************************
F5A2:  LF5A2   PSHX    
F5A3:          PSHA    
F5A4:          PSHX    
F5A5:          PSHB    
F5A6:          PSHA    
F5A7:          TSX     
F5A8:          LDAA    $03,X
F5AA:          MUL     
F5AB:          STD     $05,X
F5AD:          LDD     $01,X
F5AF:          MUL     
F5B0:          ADDB    $05,X
F5B2:          ADCA    #$00
F5B4:          STD     $04,X

F5B6:          LDAA    0,X
F5B8:          LDAB    $03,X
F5BA:          CLR     $03,X
F5BC:          MUL     
F5BD:          ADDD    $04,X
F5BF:          ROL     $03,X
F5C1:          STD     $04,X

F5C3:          LDAA    0,X
F5C5:          LDAB    $02,X
F5C7:          MUL     
F5C8:          ADDD    $03,X
F5CA:          INS     
F5CB:          PULX    
F5CC:          PULX    
F5CD:          PULX    

F5CE:          RTS     
		;----------------------------------------------


		;----------------------------------------------
		; HEADS UP
		;
		;----------------------------------------------
F5CF:  LF5CF   BRCLR   L0086,#$40,LF5D6		; BR IF NOT HEADS UP ON LINE

F5D3:          JSR     L1806				; TO HEADS UP ROUTINE

F5D6:  LF5D6   LDAA    #247
F5D8:          STAA    L0F00

F5DB:          RTS     
 		;----------------------------------------------

                                           
    	;-------------------------------------------------
		; CK IF HEADS UP IS CONNECTED
		; (LOOK FOR ID PATTERN)
    	;-------------------------------------------------
F5DC:  LF5DC   LDX     L1800			; START OF HEADS UP EPROM
F5DF:          CPX     #$7E18			; 1st 2 BYTES OF HU EPROM
F5E2:          BNE     LF5E7			; BR IF NOT CONNECTED
										;
F5E4:          JSR     L180C			; TP HEADS UP TO CONNECT SOFTWARE
										                   
F5E7:  LF5E7   RTS     					; RET TO CALLER
 		;------------------------------------------


		;=============================================
		; REMOTE BROADCAST ROUTINE
		;  (PCM POLLING MESSAGES)
		;
		;  JSR HER FROM L7B3D  
		;
		; TYPE $E6 CPU      
		;=============================================
			;
    		; CK L0042, ALDL MODE WD  
    		;	 	b0 = F4
			;		b1 = F5
			;
F5E8:  LF5E8   LDAA    L0042				; ALDL MD WD				
F5EA:          ANDA    #$03					; b0 & b1, ($F4 and $F5)
F5EC:          BNE     LF64D				; BR IF b0 & b1, (EXIT Via RTS) 
											;
F5EE:          LDX     #$518F				; INDEX MESSAGE SCHEDULE TABLE 
											; (REMOTE BROADCAST MODE ADDR TBL)
											;
		;
		; SET UP POLL MESSAGE ADDRESS USING LP COUNTER
		; EXIT IF ADDRESS = 0
		;
F5F1:          LDAB    L0002				; MJR LOOP SEGMENT COUNT
F5F3:          ANDB    #$1F					; MASK
F5F5:          ABX     						; ADD LP CNT TO ADDRESS
F5F6:          LDX     0,X					; GET SELECTED ADDRESS THIS LOOP
F5F8:          BEQ     LF64D				; BR IF Z. (EXIT via RTI)
											;
F5FA:          LDAA    2,X					;  
F5FC:          BEQ     LF64D				; BR IF Z. (EXIT via RTI)
											;

		;
		; SERIAL DATA MODE WD
		; 8192 TX IN WORK 
		;
F5FE:          BRSET   L003B,#$40,LF64A		; BR IF b6, 1st PASS CK ??
                                            ;        
F602:          BSET    L003B,#$40			; SET b6
											;
F605:          STX     L0362				;

F608:          LDAB    L302E				; GET SCI STATUS
F60B:          STAA    L302F				; TX 8192 DATA
F60E:          STAA    L0361 				; 8192 CKSUM
											;
F611:          LDAB    $04,X				; BYT CNT ??
F613:          STAB    L0365				; 8192 MSG LEN
F616:          SEI     						; TURN OFF INTERUPTS
F617:          BEQ     LF632				; BR IF MSG LEN = Z 
											;
F619:          LDAA    $03,X				;
F61B:          BITA    #$C0					; 1100 0000
F61D:          BNE     LF632				; BR IF 
											;  
F61F:          LDY     $05,X

		;
		; LOOP TILL B = 0
		;
F622:  LF622   PSHX    						;
F623:          LDX     $09,X				;
F625:          LDAA    0,X					;
F627:          STAA    0,Y					;
F62A:          INY     						;
F62C:          PULX    						;
F62D:          INX     						;
F62E:          INX     						;
F62F:          DECB    						;
F630:          BNE     LF622				; BR IF NZ
											;
F632:  LF632   LDAB    #$01					; SET BYTE CNT
F634:          STAB    L0360				; 8192 MSG LEN CNT'R

F637:          LDD     L3FFC           		; I/O D PORT ..
F63A:          JSR     LF3ED				; Very short delay (RTS)

			;
			; sET 
F63D:          ORAB    #$04					; SET b2
F63F:          STD     L3FFC          		; I/O D PORT ..
											;
F642:          CLI     						;
F643:          LDAA    #$88					; TX INT & IDLE LINE INT ENABLE
F645:          STAA    L302D				; SCI CNT'L REG #2
											;
F648:          BRA     LF64D				; EXIT Via RTS


F64A:  LF64A   BSET    L003B,#$20			; SET b5

F64D:  LF64D   RTS    						; EXIT     
 		;----------------------------------------------



		;----------------------------------------------
F64E:  LF64E   LDAA    L008C
F650:          ANDA    #$D9

F652:          LDAB    L008D
F654:          ANDB    #$02
F656:          ABA     

F657:          LDAB    L0089
F659:          ANDB    #$0020
F65B:          ABA     
F65C:          STAA    L0130

F65F:          LDAA    L0093
F661:          ANDA    #$0049

F663:          LDAB    L0090
F665:          ANDB    #$84
F667:          ABA     

F668:          LDAB    L0091
F66A:          ANDB    #$04
F66C:          ASLB    
F66D:          ASLB    
F66E:          ABA     

F66F:          LDAB    L0092
F671:          ANDB    #$0002
F673:          ABA     

F674:          STAA    L0131
F677:          BRCLR   L0042,#$02,LF6CD	; BR IF NOT b1
										;
F67B:          LDX     #$0399
F67E:          LDAA    L0399
F681:          CMPA    #$0004
F683:          BNE     LF6F5
F685:          LDD     L036A
F688:          BNE     LF6F5
F68A:          BSET    L003B,#$08
F68D:          BRCLR   $0001,X,#$18,LF6C1
F691:          CLRA    
F692:          BRCLR   $01,X,#$08,LF69C	; BR IF NOT b3

F696:          BRCLR   $02,X,#$08,LF69C	; BR IF NOT b3

F69A:          ORAA    #$01				; SET b0
										;
F69C:  LF69C   BRCLR   $01,X,#$10,LF6A6	; BR IF NOT b4

F6A0:          BRCLR   $02,X,#$10,LF6A6	; BR IF NOT b4

F6A4:          ORAA    #$02
F6A6:  LF6A6   LDY     #$B319
F6AA:          CLRB    
F6AB:          CMPA    0,Y
F6AE:          BEQ     LF6BD
										;
F6B0:          INCB    
F6B1:          CMPA    $01,Y
F6B4:          BEQ     LF6BD
										;
F6B6:          INCB    
F6B7:          CMPA    $02,Y
F6BA:          BEQ     LF6BD
										;
F6BC:          INCB    
F6BD:  LF6BD   INCB    
F6BE:          STAB    L0103
F6C1:  LF6C1   BRCLR   $05,X,#$80,LF6CF
										;
F6C5:          LDAA    L039F
F6C8:          STAA    L010A

F6CB:          BRA     LF6CF


F6CD:  LF6CD   BRA     LF6F5
 
 
F6CF:  LF6CF   BRCLR   L003B,#$08,LF6EC
											;
F6D3:          LDAA    L011A
F6D6:          ANDA    #$BF
F6D8:          BRCLR   $07,X,#$40,LF6DE		; BR IF NOT b6

F6DC:          ORAA    #$40					; SET b6
F6DE:  LF6DE   STAA    L011A

F6E1:          LDAA    L011A
F6E4:          ANDA    #$7F
F6E6:          BRCLR   $07,X,#$80,LF6EC		; BR IF NOT b7

F6EA:          ORAA    #$0080
F6EC:  LF6EC   STAA    L011A

F6EF:          LDAA    L03A1
F6F2:          STAA    L0111

F6F5:  LF6F5   BRCLR   L003B,#$08,LF715		; BR IF NOT b3

F6F9:          BRCLR   L0042,#$02,LF702		; BR IF NOT b1	
 
F6FD:          LDD     L036A
F700:          BEQ     LF715
											;
F702:  LF702   CLRA    
F703:          STAA    L0399
F706:          STAA    L010A
F709:          STAA    L0103
F70C:          STAA    L0111
F70F:          STAA    L0118

F712:          BCLR    L003B,#$08			; CLR b3

F715:  LF715   BRCLR   L0042,#$01,LF739		; BR IF NOT b0

F719:          LDAA    L038E 				; Output Cnt'l Blk ADDR
F71C:          CMPA    #$04
F71E:          BNE     LF739
											;
F720:          BSET    L003B,#$10
F723:          LDAA    L0391
F726:          BITA    #$10
F728:          BEQ     LF736
F72A:          BRSET   L0045,#$10,LF739
F72E:          JSR     LF280
F731:          BSET    L0045,#$10
F734:          BRA     LF739
 ;
F736:  LF736   BCLR    L0045,#$10
F739:  LF739   BRSET   L003B,#$02,LF748
F73D:          BRCLR   L003B,#$10,LF754
F741:          LDAA    L0391
F744:          BITA    #$0040
F746:          BEQ     LF754
F748:  LF748   BRSET   L0045,#$80,LF757
F74C:          JSR     LF333
F74F:          BSET    L0045,#$80
F752:          BRA     LF757
 ;
F754:  LF754   BCLR    L0045,#$80
F757:  LF757   BRCLR   L003B,#$01,LF767
F75B:          BRSET   L0045,#$40,LF76A
F75F:          JSR     LF380
F762:          BSET    L0045,#$40
F765:          BRA     LF76A
 ;
F767:  LF767   BCLR    L0045,#$40
F76A:  LF76A   BRCLR   L003B,#$10,LF780
F76E:          BRCLR   L0042,#$01,LF777
F772:          LDD     L036A
F775:          BEQ     LF780
											;
F777:  LF777   BCLR    L003B,#$10
F77A:          CLR     L038E 				; Output Cnt'l Blk ADDR

F77D:          BCLR    L0044,#$04			; CLR b2, SKIP ERR 43 DUE TO ALDL
											;

F780:  LF780   RTS     

 			;-----------------------------------------
F781:  LF781   SEI     
F782:          BRCLR   L0042,#$03,LF7BA		; 
											;
F786:          LDAA    L0367
F789:          INCA    
F78A:          BEQ     LF793				; 
											;
F78C:          STAA    L0367
F78F:          CMPA    #$00C8
F791:          BCS     LF7BA				; 
											;
F793:  LF793   CLR     L0399
F796:          CLR     L038E 				; Output Cnt'l Blk ADDR
F799:          BCLR    L0042,#$03
F79C:          BCLR    L0045,#$D0
F79F:          BCLR    L003B,#$43

			;
			; CLR b2
			;
F7A2:          LDD     L3FFC          		; I/O D PORT ..
F7A5:          JSR     LF3ED				; Very short delay (RTS)
F7A8:          ANDB    #$FB					; 1111 1011
F7AA:          STD     L3FFC          		; I/O D PORT ..

F7AD:          LDAA    #$26					; RX INT, RX RC WAK UP ENABLE
F7AF:          STAA    L302D				; SCI CNT'L REG #2

			;
			; CLR ... & MSG LEN CNT'R
F7B2:          CLRA    
F7B3:          CLRB    
F7B4:          STD     L0362				;
F7B7:          STD     L0360				; 8192 MSG LEN CNT'R

F7BA:  LF7BA   CLI     
F7BB:          BRCLR   L003B,#$18,LF7D3	  	; BR IF NOT b3 & b4 
										  	;
F7BF:          LDX     L0368
F7C2:          INX     
F7C3:          STX     L0368
F7C6:          CPX     L51BB
F7C9:          BCS     LF7E9				; 
											;
F7CB:          LDX     #$0001
F7CE:          STX     L036A
F7D1:          BRA     LF7E9
 ;
F7D3:  LF7D3   LDX     L036A
F7D6:          BEQ     LF7E9
F7D8:          INX     
F7D9:          STX     L036A
F7DC:          CPX     L51BD
F7DF:          BCS     LF7E9				; 
											;
F7E1:          CLRA    
F7E2:          CLRB    
F7E3:          STD     L036A
F7E6:          STD     L0368

F7E9:  LF7E9   RTS     


 			;------------------------------------
			; SCI INTERUPT VECTOR HANDLER
			;
			;
			;------------------------------------
F7EA:          LDX     #$3000				; INDEX CPU REG'S
											;
F7ED:          BRCLR   $2D,X,#$20,LF7FA		; BR IF NOT b5, (RX INT ENABLED) 
											;
F7F1:          BRCLR   $2E,X,#$20,LF821		; BR IF NOT b5,	(RX REG FULL)
											;
F7F5:  LF7F5   JSR     LF90B				;
F7F8:          BRA     LF821				; EXIT via RTI  


 											;
F7FA:  LF7FA   BRCLR   $2D,X,#$80,LF807		; BR IF NOT b7, (TX INT ENABLED)
											;
F7FE:          BRCLR   $2E,X,#$80,LF821		; BR IF NOT b7,	(TX REG EMPTY)
											;
F802:          JSR     LF822				;
F805:          BRA     LF821				; EXIT via RTI

 											

F807:  LF807   BRCLR   $2D,X,#$40,LF821		; BR IF NOT b6, (TC DONE INT ENABLED)
											;
F80B:          BRCLR   $2E,X,#$40,LF821		; BR IF NOT b6,	(TC DONE)
											;
F80F:          LDAA    #$26					; IDLE LINE INT, RX, RX WAKE UP ENABLE
F811:          STAA    $2D,X				; SCI CNT'L REG #2 
											;
F813:          LDD     L3FFC          		; I/O D PORT ..
F816:          JSR     LF3ED				; Very short delay (RTS)							;
											;
F819:          ANDB    #$FB					;
F81B:          STD     L3FFC          		; I/O D PORT ..

F81E:          BCLR    L003B,#$40			; CLR b6
											
F821:  LF821   RTI     
 		;----------------------------------------


		;----------------------------------------
		;
		;
		;----------------------------------------
F822:  LF822   LDX     L0362				; INDEX 8192 DATA BUFFER
F825:          LDAB    L0360				; 8192 MSG LEN CNT'R
F828:          DECB    						; DECR MSG CNT'R
F829:          BNE     LF852				; BR IF NOT DONE
											;
F82B:          LDAA    4,X					;
											; 
F82D:          BRCLR   L0042,#$03,LF84A		; BR IF NOT b0 & b1
											;
F831:          PSHA    						;
F832:          LDAB    L038E 				; Output Cnt'l Blk ADDR
											;
F835:          LDAA    L0364				; GET DEVICE ID
F838:          CMPA    #$F5					; DEVICE CODE $F5 ?
F83A:          BNE     LF83F				; BR IF F5
											;
F83C:          LDAB    L0399				;
F83F:  LF83F   PULA    						;
F840:          CMPB    #$03					;
F842:          BNE     LF84A				; BR IF 
											;
F844:          LDAA    L0365				; 8192 MSG LEN
F847:          DECA    						; DECR 8192 MSG LEN
F848:          ASRA    
F849:          INCA    
F84A:  LF84A   STAA    L0365				; 8192 MSG LEN
F84D:          ADDA    #$55					; ADD IN 8192 MSG LEN BIAS

F84F:          JMP     LF8E6
 

F852:  LF852   DECB    
F853:          BNE     LF869
F855:          BRCLR   L0042,#$03,LF869		; BR IF NOT B0 & B1
											;
F859:          LDAA    L038E 				; Output Cnt'l Blk ADDR
F85C:          LDAB    L0364				; GET DEVICE ID
F85F:          CMPB    #$F5					; DEVICE CODE $F5 ?
F861:          BNE     LF866				; BR IF NOTF5
											;
F863:          LDAA    L0399
F866:  LF866   JMP     LF8E6
 

F869:  LF869   CMPB    L0365				; 8192 MSG LEN
F86C:          BCC     LF8E0				; BR IF MSG LEN NZ
											;
F86E:          BRSET   L003B,#$80,LF8D4		; BR IF b7
											;
F872:          BRSET   $03,X,#$80,LF881		; BR IF b7
											;
F876:          BRSET   $03,X,#$40,LF88C		; BR IF b6
											;
F87A:          LDX     $05,X
F87C:          ABX     
F87D:          LDAA    0,X
F87F:          BRA     LF8E6
 ;
F881:  LF881   BRCLR   L0042,#$03,LF886		; BR IF NOT b0 & b1
											;
F885:          DECB    
F886:  LF886   ASLB    
F887:          ABX     
F888:          LDX     $0009,X
F88A:          BRA     LF8B8
 ;
F88C:  LF88C   DECB    
F88D:          LDX     $05,X
F88F:          PSHB    

F890:          LDAA    L038E 				; Output Cnt'l Blk ADDR
F893:          LDAB    L0364				; GET 8192 DEVICE ID
F896:          CMPB    #$00F4				; F4 (ENGINE) ?
F898:          BEQ     LF8A2				; BR IF 
											;
F89A:          LDAA    L0399				;
											;
F89D:          CMPB    #$F5					; F5 (XMISH) ?
F89F:          BEQ     LF8A2				; BR IF 
											;
F8A1:          CLRA    						;
F8A2:  LF8A2   PULB    						;
F8A3:          CMPA    #$02					;
F8A5:          BEQ     LF8B4				; BR IF 
											;
F8A7:          ASLB    						;
F8A8:          INCB    						;
F8A9:          CMPA    #$04					;
F8AB:          BNE     LF8AF				; BR IF 
											;
F8AD:          ADDB    #$000A				;
F8AF:  LF8AF   ABX     						;
F8B0:          LDX     0,X					;

F8B2:          BRA     LF8B8



F8B4:  LF8B4   INX     
F8B5:          LDX     0,X
F8B7:          ABX     
F8B8:  LF8B8   CPX     #$1000
F8BB:          BCS     LF8DC				; BR IF 
											;
F8BD:          CPX     #$3FFF
F8C0:          BHI     LF8DC
F8C2:          XGDX    
F8C3:          BRSET   L0050,#$08,LF8C9
F8C7:          ANDA    #$00CF
F8C9:  LF8C9   XGDX    
F8CA:          LDD     0,X
F8CC:          STAB    L0366
F8CF:          BSET    L003B,#$80
F8D2:          BRA     LF8E6
 ;
F8D4:  LF8D4   BCLR    L003B,#$80
F8D7:          LDAA    L0366
F8DA:          BRA     LF8E6
 ;
F8DC:  LF8DC   LDAA    0,X
F8DE:          BRA     LF8E6
 
F8E0:  LF8E0   BNE     LF8F4

F8E2:          LDAA    L0361 				; 8192 CKSUM
F8E5:          NEGA    						; DO 2'S COMP FOR TX
F8E6:  LF8E6   STAA    L302F				; TX A BYTE VIA 8192

F8E9:          ADDA    L0361				; ADD TX'ED BYTE TO CK SUM
F8EC:          STAA    L0361 				; 8192 CKSUM
F8EF:          INC     L0360				; INCR MSG LEN CNT'R
F8F2:          BRA     LF90A
 

F8F4:  LF8F4   CLRA    
F8F5:          CLRB    

F8F6:          BCLR    L003B,#$80			; CLR b7

F8F9:          STD     L0360				; 8192 MSG LEN CNT'R
F8FC:          STD     L0362

F8FF:          LDAA    L302E			   	; GET SCI STATUS
F902:          LDAA    L302F				; GET 8192 RX'ED DATA

F905:          LDAA    #$40					; TX DONE INT ENABLE
F907:          STAA    L302D				; SCI CNT'L REG #2

F90A:  LF90A   RTS     
			;-----------------------------------------


 			;-----------------------------------------
			; SCI RX SUBROUTINE
			;
			;
			;-----------------------------------------
F90B:  LF90B   LDAB    L302E				; SCI STATUS REG
F90E:          LDAA    L302F				; SCI DATA REG
F911:          LDX     L0362				; INDEX SCI RX DATA BUFFER
F914:          CLR     L0367				;
F917:          BITB    #$0E					; CK FOR SCI ERRORS
F919:          BNE     LF939				; BR IF
											;
F91B:          TAB     
F91C:          ADDB    L0361				; ADD NEW RX'ED BYTE TO CK SUM
F91F:          STAB    L0361				; 8192 CKSUM

F922:          LDAB    L0360				; 8192 MSG LEN CNT'R 
F925:          BNE     LF955				; BR IF NZ, (NOT DONE)
 											;
F927:          LDX     #$51BF
F92A:          BRCLR   L0050,#$08,LF931		;
											;
F92E:          LDX     #$FBD7
F931:  LF931   CMPA    $02,X
F933:          BEQ     LF93B				;
											;
F935:          LDX     0,X
F937:          BNE     LF931

F939:  LF939   BRA     LF9B6



F93B:  LF93B   CMPA    #$F4					; DEVICE F4, (ENGINE) ?
F93D:          BNE     LF944				;
											;
F93F:          BSET    L0042,#$01
F942:          BRA     LF94B
 ;
F944:  LF944   CMPA    #$F5					; DEVICE F5, (XMISSION)	?
F946:          BNE     LF94B				;
											;
F948:          BSET    L0042,#$02			; SET b1
F94B:  LF94B   STX     L0362				;
											;
F94E:          LDAA    #$24					; RX INT, RX Enable
F950:          STAA    L302D				; SCI CNT'L REG #2

F953:          BRA     LF9B0


;
F955:  LF955   DECB    
F956:          BNE     LF965
											;
F958:          SUBA    #$55					; SUB OFF MESSAGE LEN BIAS
F95A:          BCS     LF9B6
											;
F95C:          CMPA    #$22
F95E:          BHI     LF9B6
F960:          STAA    L0365				; 8192 MSG LEN

F963:          BRA     LF9B0
 

F965:  LF965   DECB    
F966:          CMPB    L0365				; 8192 MSG LEN
F969:          BCC     LF9B9
											;
F96B:          TSTB    						;
F96C:          BNE     LF984				;
											;
F96E:          BRCLR   L0042,#$03,LF9AB		; BR IF NOT b0 & b1
											;
F972:          CMPA    #10					;
F974:          BHI     LF9B6
F976:          PSHB    
F977:          TAB     
F978:          ASLB    
F979:          ABX     
F97A:          PULB  
  
F97B:          LDX     9,X
F97D:          BEQ     LF9B6
F97F:          STX     L0362
F982:          BRA     LF9AB
 ;
F984:  LF984   BRCLR   L0042,#$03,LF9AB
F988:          XGDY    
F98A:          LDAA    L036C
F98D:          CMPA    #$0001
F98F:          XGDY    
F991:          BNE     LF9AB
F993:          CMPB    #$01
F995:          BNE     LF9AB
F997:          CMPA    #$03
F999:          BCS     LF99C

F99B:          CLRA    
F99C:  LF99C   PSHB    
F99D:          XGDX    
F99E:          SUBD    #$06
F9A1:          XGDX    
F9A2:          TAB     
F9A3:          ASLB    
F9A4:          ABX     
F9A5:          LDX     0,X
F9A7:          PULB    
F9A8:          STX     L0362
F9AB:  LF9AB   LDX     7,X
F9AD:          ABX     
F9AE:          STAA    0,X
F9B0:  LF9B0   INC     L0360				; INCR 8192 MSG LEN CNT'R
F9B3:          JMP     LFA5A


F9B6:  LF9B6   JMP     LFA4D



F9B9:  LF9B9   LDAB    L0361 				; 8192 BAUD SCI MSG CK SUM
F9BC:          BNE     LF9B6				; BR IF NZ

F9BE:          LDAB    $02,X
F9C0:          STAB    L0364				; SAVE DEVICE ID, (ENG/XMISH MODE BYTE)

F9C3:          LDY     #$038E 				; Output Cnt'l Blk ADDR
F9C7:          LDAA    L0365				; 8192 MSG LEN

F9CA:          BRSET   L0050,#$08,LFA10		; BR IF b3
											;
F9CE:          CMPB    #$F5					; F5, (XMISH) ?
F9D0:          BNE     LF9D6				; BR IF NOT F5
											;
F9D2:          LDY     #$0399
F9D6:  LF9D6   BCLR    L003B,#$03			; CLR b0 & b1

F9D9:          LDAB    L036C
F9DC:          STAB    0,Y
F9DF:          BNE     LF9F1

F9E1:          LDAB    #$FE
F9E3:          CPY     #$0399
F9E7:          BNE     LF9EB				; BR IF 
											;
F9E9:          LDAB    #$FD
F9EB:  LF9EB   ANDB    L0042
F9ED:          STAB    L0042
F9EF:          BRA     LFA21
 ;
F9F1:  LF9F1   CMPB    #10
F9F3:          BNE     LFA06

F9F5:          LDAB    L0364				; GET DEVICE ID
F9F8:          CMPB    #$F5					; F5, (XMISH) ?
F9FA:          BEQ     LFA01				; BR IF F5
											;
F9FC:          BSET    L003B,#$02			; SET b1
F9FF:          BRA     LFA21
 
FA01:  LFA01   BSET    L003B,#$01			; SET b0
FA04:          BRA     LFA21
 
FA06:  LFA06   CMPB    #$04
FA08:          BNE     LFA21
FA0A:          CMPA    #11

FA0C:          BLS     LFA10
FA0E:          LDAA    #11
FA10:  LFA10   TSTA    
FA11:          BEQ     LFA21
FA13:          LDX     #$036C
FA16:  LFA16   LDAB    0,X
FA18:          STAB    0,Y
FA1B:          INX     
FA1C:          INY     
FA1E:          DECA    
FA1F:          BNE     LFA16

		;
		; CK RAM/ROM MODE
		;
FA21:  LFA21   LDX     L0362
FA24:          BRSET   $0004,X,#$80,LFA4D	; BR IF NOT b7
											;

FA28:  LFA28   STX     L0362
FA2B:          LDAB    L302E				; SCI STATUS REG

FA2E:          LDAA    $02,X
FA30:          STAA    L302F				; SCI DATA REG

FA33:          STAA    L0361 				; 8192 CKSUM
FA36:          LDAB    #$01
FA38:          STAB    L0360				; 8192 MSG LEN CNT'R

FA3B:          LDD     L3FFC          		; I/O D PORT ..
FA3E:          JSR     LF3ED				; Very short delay (RTS)
FA41:          ORAB    #$04					; SET b2
FA43:          STD     L3FFC          		; I/O D PORT ..

		;
		; ENABLE 8192 BAUD TX & TX INTERUPT
		;  
FA46:          LDAA    #$88					; TX INT & IDLE LINE INT ENABLE 
FA48:          STAA    L302D				; SCI CNT'L REG #2

FA4B:          BRA     LFA5A



FA4D:  LFA4D   CLRA    
FA4E:          CLRB    
FA4F:          STD     L0362
FA52:          STD     L0360				; 8192 MSG LEN CNT'R & CK SUM

		;
		;  RX WK UP, RX ENABLE & RX INT ENABLE
		;
FA55:          LDAA    #$26					; RX INT, RX RC WAK UP ENABLE
FA57:          STAA    L302D				; SCI CNT'L REG #2

FA5A:  LFA5A   RTS     
		;----------------------------------------

 
		;----------------------------------------
		;
		;
		;
		;----------------------------------------
FA5B:  LFA5B   LDS     #$03FF				; SET USR STX
											;
FA5E:          LDAA    #$01					; SET UP TO READ DIAG INPUT
											;
FA60:          LDX     #$3000				; INDEX CPU REG'S


FA63:          JSR     LF275			   	; DELAY ROUTINE

FA66:          LDAA    #$01
FA68:          JSR     LF25F

FA6B:          LDAA    L3031          		; GET A/D RESULT #1,
FA6E:          CMPA    #100					; 2VDC
FA70:          BCC     LFA82				; BR IF VDC GT 100 bin, (2 VDC)
											;
FA72:          CMPA    #$40					; 800 mvdc 
FA74:          BCS     LFA82				: BR IF A/D VAL LT 800 mvdc
											;
FA76:          LDAA    #$03
FA78:          JSR     LF25F

FA7B:          LDAA    L3031          		; GET A/D RESULT #1
FA7E:          CMPA    #$1A					;
FA80:          BHI     LFA83

FA82:  LFA82   SWI     
FA83:  LFA83   CLI     
            ;----------------------------------
			
			;
			; RESET COP
			;
FA84:          LDD     #$AA55
FA87:          STAA    L303A				; COP 1
FA8A:          STAB    L303A


FA8D:          LDAB    L0364				; GET DEVICE ID, (ENG/XMISH MODE BYTE)
FA90:          CMPB    #$02
FA92:          BEQ     LFA9F				; BR IF DEVICE ID = 2
											;
FA94:          JSR     LF3E4
FA97:          CMPB    #$03
FA99:          BNE     LFAA9				; BR IF 
											;
FA9B:          BRCLR   L0001,#$01,LFAA9		; BR IF NOT b1, 
											;
FA9F:  LFA9F   BSET    L0001,#$01			; SET b0

FAA2:          LDX     L038E 				; Output Cnt'l Blk ADDR
FAA5:          JSR     0,X

FAA7:          BRA     LFAC7				; EXIT TO WAIT FOR INTIRUP
 

FAA9:  LFAA9   CMPB    #$01
FAAB:          BNE     LFACA				; BR IF NOT RAM UP LD MSG
											;
                                                          
        ;---------------------
        ; UPLOAD RX'ED DATA
        ;
        ; XFER TO RAM STARTING
        ; AT  $02AE, (32 BYTES)
        ;---------------------
FAAD:          BCLR    L0001,#$01			; BR IF b0

FAB0:          LDX     L038E 				; Output Cnt'l Blk ADDR

FAB3:          LDY     #$0390             	; POINT TO MSG DATA ADDR
FAB7:          LDAB    #32	              	; 32 BY FIXED LEN MSG'S

FAB9:  LFAB9   LDAA    0,Y				  	; GET DATA BYTE 
FABC:          STAA    0,X				  	; XFER DATA TO DEST RAM LOC
FABE:          INY     					  	; BUMP ADDR POINTERS
FAC0:          INX     
FAC1:          DECB    					  	; DEC 32 BYTE CNT'R
FAC2:          BNE     LFAB9			  	; LOOP TILL CNT'R = 0
											;
FAC4:          COM     L0364				;  DEVICE ID  ENG/XMISH MODE BYTE

FAC7:  LFAC7   JMP     LFBD4				; DO NOTHING LP, (WAIT FOR INIT ?)
		;--------------------------------------------

	
		;--------------------------------------------
		; CK FOR OUTPUT	CYCLING DISABLE	 CONDITIONS
		;
		;
		;--------------------------------------------
FACA:  LFACA   LDX     #$FC01				;
FACD:          TSTB    						; NZ, A VALID SERAIL DATA MSG
											; HASE BEEN RX'ED, DONT CYCLE
											; OUTUTS
    
FACE:          BNE     LFB39				; BR IF 
											;
FAD0:          LDY     #$3064				; I/O DEV PORT
FAD4:          BRCLR   0,Y,#$80,LFB39		; BR IF 
											;
FAD9:          LDX     #$DFFF               ; 57,343d
FADC:          STX     L3FCC
FADF:          JSR     LFBD6                ; SHORT DELAY
											;
FAE2:          LDX     #$DFFF               ; 57,343d
FAE5:          STX     L3FEA				;
FAE8:          JSR     LFBD6                ; SHORT DELAY



             	;---------------------------
            	; OUTPUT CYCLING 
            	; 
            	;---------------------------
FAEB:          LDD     #197					; SET UP FOR 3msec PULSES
FAEE:          STD     L3FCE				; SAVE TO EFI PW
FAF1:          JSR     LFBD6				; SHORT CPU DELAY

FAF4:          LDX     #66					; SET DWELL TO 1 Msec
FAF7:          STX     L3FDC				; SPK WP, (DWELL)
FAFA:          JSR     LFBD6				; EXIT via RTS

FAFD:          LDD     #$FFF1				; 65,521d
FB00:          SUBD    #$05
FB03:          STD     L3FF6				; EST FALL CNT'R
											; (TIME FM DRP TO FIRE IGN)
FB06:          LDAB    L0002				; MJR LOOP SEGMENT COUNT; MAJOR LOOP COUNTER
FB08:          CMPB    #$4F					; 0010 1111
FB0A:          BLS     LFB0D				; BR IF 
											; 
FB0C:          CLRB    

FB0D:  LFB0D   STAB    L0002				; MAJOR LOOP COUNTER
FB0F:          BITB    #$0F
FB11:          BNE     LFAC7				; BR IF 
											;
FB13:          PSHB    
FB14:          LDAA    L3062				; I/O PORT D
FB17:          TAB     						; TO B reg
FB18:          ANDA    #$0C					; MASK 0000 1100
FB1A:          BEQ     LFB24				; BR IF NOT b2 & b3
											;
FB1C:          CMPA    #$0C					; b2 & b3
FB1E:          BEQ     LFB24				; BR IF NOT b2 & b3
											;
FB20:          EORB    #$08					; b3
FB22:          BRA     LFB26
 ;
FB24:  LFB24   EORB    #$04
FB26:  LFB26   ORAB    #$30
FB28:          STAB    L3062

FB2B:          PULB    
FB2C:          LSRB    
FB2D:          LSRB    
FB2E:          LSRB    
FB2F:          LSRB    
FB30:          LDAA    #$03
FB32:          MUL     
  
			;-----------------------------------------
			; MYSTERY TABLE
			;
			;----------------------------------------
FB33:          LDX     #$FBF2
FB36:          ABX     
FB37:          BRA     LFB4A

				;-----------------
				; I/O D PORT
				;
				;-----------------
FB39:  LFB39   LDAA    L3062				; I/O PORT D
FB3C:          ANDA    #$00E3				; 0111 0011
FB3E:          STAA    L3062				; I/O PORT D

FB41:          LDD     #$0000
FB44:          STD     L3FCE
FB47:          JSR     LFBD6				; EXIT via RTS

FB4A:  LFB4A   LDAA    L3060				; I/O PORT
FB4D:          ANDA    #$6F					; 0110 111
FB4F:          ORAA    0,X
FB51:          STAA    L3060				; I/O PORT


				;---------------
				; I/O D PORT
				;---------------
FB54:          LDAA    L3062				; I/O PORT D
FB57:          ANDA    #$FC					; 1111 1100
FB59:          ORAA    $01,X
FB5B:          STAA    L3062				; I/O PORT D

FB5E:          SEI     

FB5F:          LDD     L3FFC          		; I/O D PORT ..
FB62:          JSR     LFBD6				; very short delay (RTS)
FB65:          ANDB    #$F7					; 1111 0111
FB67:          ORAB    2,X					; SET ...
FB69:          STD     L3FFC          		; I/O D PORT ..

FB6C:          JSR     LFBD6				; EXIT via RTS

FB6F:          CLI     
FB70:          CPX     #$FC01
FB73:          BNE     LFB98

FB75:          LDX     #$D000
FB78:          STX     L3FD4
FB7B:          BSR     LFBD6				; very short delay (RTS)

FB7D:          STX     L3FD6
FB80:          BSR     LFBD6
FB82:          STX     L3FD8

FB85:          BSR     LFBD6

FB87:          STX     L3FDA
FB8A:          STX     L306A
FB8D:          STX     L306C
FB90:          STX     L306E
FB93:          STX     L3068

FB96:          BRA     LFBD4


FB98:  LFB98   LDX     #$D399				; 54,169d
FB9B:          STX     L3FD4
FB9E:          BSR     LFBD6				; EXIT via RTS

FBA0:          LDX     #$D366				; 54,118
FBA3:          STX     L3FD6
FBA6:          BSR     LFBD6				; EXIT via RTS

FBA8:          LDX     #$D332
FBAB:          STX     L3FD8
FBAE:          BSR     LFBD6				; EXIT via RTS

FBB0:          LDX     #$D2FF
FBB3:          STX     L3FDA

FBB6:          LDX     #$7FB3				; 32,691
FBB9:          STX     L306A

FBBC:          LDX     #$7FA6				; 32,678
FBBF:          STX     L306C

FBC2:          LDX     #$7F66
FBC5:          STX     L306E				; 32,614

FBC8:          LDX     #$0D73				; 3,443
FBCB:          STX     L3068

FBCE:          LDX     #$FBE0				; INDEX MSG HANDLER
FBD1:          JSR     LFA28

FBD4:  LFBD4   BRA     LFBD4


FBD6:  LFBD6   RTS     
 			;-----------------------------------------



    ;--------------------------------------------------
    ; FACTORY TEST MSG LIST 
	;
	; (SERIAL DAT MSG TBL)
	; $31          
    ;--------------------------------------------------
    ;--------------------------------------------------
    ; FACTORY TEST MSG LIST
    ;
    ;
    ;--------------------------------------------------
        ORG  $FBD7  ;                    
                    ;----------------------------------
LFBD7   FDB $FBE0   ; LINK TO NEXT MSG
LFBD9   FCB $01     ; MESSAGE ID
LFBDA   FCB $00     ; USE RAM BUFFER
LFBDB   FCB   0     ; NUM OUTPUT BYTES
					;
LFBDC   FDB $038E   ; OCB ADDR 
LFBDE   FDB $036C   ; ICB ADDR
    	;----------------------------------------


    	;----------------------------------------
    	;
    	;                                
    	;----------------------------------------
LFBE0   FCB $FBE9   ; LINK TO NEXT MSG
LFBE2   FCB $02     ; MESSAGE ID
LFBE3   FCB $00     ; USE RAM BUFFER
LFBE4   FCB  00     ; NUM OUTPUT BYTES
					;
LFBE5   FCB $038E   ; OCB ADDR
LFBE7   FCB $036C   ; ICB ADDR
    	;----------------------------------------


    	;----------------------------------------
    	;
    	;                                
    	;----------------------------------------
LFBE9   FCB $0000   ; END OF LINKED MSG LIST
LFBEB   FCB $03     ; MESSAGE ID
LFBEC   FCB $00     ; USE RAM BUFFER
LFBED   FCB $18     ; NUM OUTPUT BYTES
					;
LFBEE   FCB $036C   ; OCB ADDR
LFBF0   FCB $036C   ; ICB ADDR
		;----------------------------------------

    	;----------------------------------------
    	; MYSTERY TABLE
		;========================================   
		; OUTPUT CYCLING TABLE
		;========================================
    	;                                
    	;----------------------------------------

LFBF2   FCB $10     ;
LFBF3   FCB $20     ;
LFBF4   FCB $00     ;
LFBF5   FCB $10     ;
LFBF6   FCB $21     ;

LFBF7   FCB $08     ;
LFBF8   FCB $10     ;
LFBF9   FCB $22     ;

LFBFA   FCB $08     ;
LFBFB   FCB $00     ;
LFBFC   FCB $20     ;

LFBFD   FCB $08     ;
LFBFE   FCB $90     ;
LFBFF   FCB $20     ;

LFC00   FCB $08     ;
LFC01   FCB $10     ;
LFC02   FCB $00     ;
LFC03   FCB $08     ;





	;--------------------------------------------
	; SWI VECTOR HANDLER
	;
	;
	;--------------------------------------------
FC04:          BSET    L0000,#$08

FC07:  LFC07   BRA     LFC07				; LP HER IF SWI
	;--------------------------------------------


	;--------------------------------------------
	; XIRQ  VECTOR HANDLER
	;
	;
	;--------------------------------------------
FC09:          BSET    L0000,#$04			; SET b2

FC0C:          PULA    
FC0D:          ORAA    #$40					; SET b6
FC0F:          PSHA    

FC10:          RTI     
 	;------------------------------------------


	;--------------------------------------------
	; 
	;
	;
	;------------------------------------------
FC11:  LFC11   BSET    L0000,#$02
FC14:          LDAA    #$01
FC16:          STAA    L3023

FC19:          RTI     
 	;------------------------------------------


 	;------------------------------------------
	; ILLEAGL OP CODE VECTOR HANDLER
	;
	;
 	;------------------------------------------
FC1A:          BSET    L0000,#$10
FC1D:  LFC1D   BRA     LFC1D
 	;------------------------------------------


 	;------------------------------------------
	;  COP TIME OUT VECTOR HANDLER
	;
	;------------------------------------------
FC1F:          BSET    L0000,#$20
FC22:          BRA     LFC2C
 	;------------------------------------------

 
 	;----------------------------------------
 	; CLOCK FAIL VECTOR HANDLER
	;
	;----------------------------------------
FC24:          BSET    L0000,#$40
FC27:  LFC27   BRA     LFC27				; LOOP HER IF CLK FAIL
 	;----------------------------------------


	;----------------------------------------
 	; EXT RESET	VECTOR HANDLER
	;
	;
	;----------------------------------------
FC29:          BSET    L0000,#$80			; SET b7
FC2C:  LFC2C   JMP     L7100				; TO TOP OF ALGO

	;----------------------------------------
	; TIC 3	INTERUPT VECTOR HANDLER
	; TIC 2	INTERUPT VECTOR HANDLER
	; TIC 1	INTERUPT VECTOR HANDLER
	; REAL TIME INTERUPT VECTOR HANDLER
	:
	;----------------------------------------
FC2F:  LFC2F   LDAA    #$A0					; TOC1, TOC 3 INT ENABLE
FC31:          STAA    L3022				; TMSK1

FC34:          LDAA    #$5F					; CLR TOC3,4 TIC 1 - TIC 4
FC36:          STAA    L3023				; TFLG1

FC39:          RTI     
 	;------------------------------------------


 	;------------------------------------------
	; PA INPUT EDGE VECTOR
	; PA OVER FLOW
	; TMR OVERFLOW
	;
	;------------------------------------------
FC3A:          LDAA    #$03					; TMR PRE SCALE = E/16
FC3C:          STAA    L3024				; TMSK2

FC3F:          LDAA    #$FF					; CLR ALL FLAGS
FC41:          STAA    L3025				; TFLG2


 	;-------------------------------------------
	; SPI INTERUPT VECTOR HANDLER
	;
	;-------------------------------------------
FC44:          RTI     
 	;-------------------------------------------

***********************************************************
***********************************************************
***********************************************************

    ;--------------------------------------------------
    ;  1st 256 BYTE COOL TABLE ??
    ; TYPE $31 ECM                               
    ;
    ;
    ;
    ; TBL =  1.3333  * (dEG C cool + 40 )
    ;--------------------------------------------------
        ORG  $FC45  ;    Deg c COOL      A/D
                    ;----------------------------------
LFC45   FCB  255    ;       151            0
LFC46   FCB  255    ;       151            1
LFC47   FCB  255    ;       151            2
LFC48   FCB  254    ;       151            3
LFC49   FCB  237    ;       138            4
LFC4A   FCB  225    ;       129            5
LFC4B   FCB  215    ;       121            6
LFC4C   FCB  207    ;       115            7
LFC4D   FCB  201    ;       111            8
LFC4E   FCB  195    ;       106            9
LFC4F   FCB  190    ;       103           10
LFC50   FCB  185    ;        99           11
LFC51   FCB  181    ;        96           12
LFC52   FCB  178    ;        94           13
LFC53   FCB  174    ;        91           14
LFC54   FCB  171    ;        88           15
LFC55   FCB  168    ;        86           16
LFC56   FCB  166    ;        85           17
LFC57   FCB  163    ;        82           18
LFC58   FCB  161    ;        81           19
LFC59   FCB  159    ;        79           20
LFC5A   FCB  157    ;        78           21
LFC5B   FCB  155    ;        76           22
LFC5C   FCB  153    ;        75           23
LFC5D   FCB  151    ;        73           24
LFC5E   FCB  149    ;        72           25
LFC5F   FCB  147    ;        70           26
LFC60   FCB  146    ;        70           27
LFC61   FCB  144    ;        68           28
LFC62   FCB  143    ;        67           29
LFC63   FCB  141    ;        66           30
LFC64   FCB  140    ;        65           31
LFC65   FCB  139    ;        64           32
LFC66   FCB  137    ;        63           33
LFC67   FCB  136    ;        62           34
LFC68   FCB  135    ;        61           35
LFC69   FCB  134    ;        61           36
LFC6A   FCB  133    ;        60           37
LFC6B   FCB  131    ;        58           38
LFC6C   FCB  130    ;        58           39
LFC6D   FCB  129    ;        57           40
LFC6E   FCB  128    ;        56           41
LFC6F   FCB  127    ;        55           42
LFC70   FCB  126    ;        55           43
LFC71   FCB  125    ;        54           44
LFC72   FCB  124    ;        53           45
LFC73   FCB  124    ;        53           46
LFC74   FCB  123    ;        52           47
LFC75   FCB  122    ;        52           48
LFC76   FCB  121    ;        51           49
LFC77   FCB  120    ;        50           50
LFC78   FCB  119    ;        49           51
LFC79   FCB  118    ;        49           52
LFC7A   FCB  118    ;        49           53
LFC7B   FCB  117    ;        48           54
LFC7C   FCB  116    ;        47           55
LFC7D   FCB  115    ;        46           56
LFC7E   FCB  114    ;        46           57
LFC7F   FCB  114    ;        46           58
LFC80   FCB  113    ;        45           59
LFC81   FCB  112    ;        44           60
LFC82   FCB  112    ;        44           61
LFC83   FCB  111    ;        43           62
LFC84   FCB  110    ;        43           63
LFC85   FCB  110    ;        43           64
LFC86   FCB  109    ;        42           65
LFC87   FCB  108    ;        41           66
LFC88   FCB  108    ;        41           67
LFC89   FCB  107    ;        40           68
LFC8A   FCB  106    ;        40           69
LFC8B   FCB  106    ;        40           70
LFC8C   FCB  105    ;        39           71
LFC8D   FCB  104    ;        38           72
LFC8E   FCB  104    ;        38           73
LFC8F   FCB  103    ;        37           74
LFC90   FCB  103    ;        37           75
LFC91   FCB  102    ;        37           76
LFC92   FCB  101    ;        36           77
LFC93   FCB  101    ;        36           78
LFC94   FCB  100    ;        35           79
LFC95   FCB  100    ;        35           80
LFC96   FCB  99     ;        34           81
LFC97   FCB  99     ;        34           82
LFC98   FCB  98     ;        34           83
LFC99   FCB  98     ;        34           84
LFC9A   FCB  97     ;        33           85
LFC9B   FCB  96     ;        32           86
LFC9C   FCB  96     ;        32           87
LFC9D   FCB  95     ;        31           88
LFC9E   FCB  95     ;        31           89
LFC9F   FCB  94     ;        31           90
LFCA0   FCB  94     ;        31           91
LFCA1   FCB  93     ;        30           92
LFCA2   FCB  93     ;        30           93
LFCA3   FCB  92     ;        29           94
LFCA4   FCB  92     ;        29           95
LFCA5   FCB  91     ;        28           96
LFCA6   FCB  91     ;        28           97
LFCA7   FCB  90     ;        28           98
LFCA8   FCB  90     ;        28           99
LFCA9   FCB  89     ;        27          100
LFCAA   FCB  89     ;        27          101
LFCAB   FCB  88     ;        26          102
LFCAC   FCB  88     ;        26          103
LFCAD   FCB  87     ;        25          104
LFCAE   FCB  87     ;        25          105
LFCAF   FCB  86     ;        25          106
LFCB0   FCB  86     ;        25          107
LFCB1   FCB  86     ;        25          108
LFCB2   FCB  85     ;        24          109
LFCB3   FCB  85     ;        24          110
LFCB4   FCB  84     ;        23          111
LFCB5   FCB  84     ;        23          112
LFCB6   FCB  83     ;        22          113
LFCB7   FCB  83     ;        22          114
LFCB8   FCB  82     ;        22          115
LFCB9   FCB  82     ;        22          116
LFCBA   FCB  81     ;        21          117
LFCBB   FCB  81     ;        21          118
LFCBC   FCB  80     ;        20          119
LFCBD   FCB  80     ;        20          120
LFCBE   FCB  80     ;        20          121
LFCBF   FCB  79     ;        19          122
LFCC0   FCB  79     ;        19          123
LFCC1   FCB  78     ;        19          124
LFCC2   FCB  78     ;        19          125
LFCC3   FCB  77     ;        18          126
LFCC4   FCB  77     ;        18          127
LFCC5   FCB  77     ;        18          128
LFCC6   FCB  76     ;        17          129
LFCC7   FCB  76     ;        17          130
LFCC8   FCB  75     ;        16          131
LFCC9   FCB  75     ;        16          132
LFCCA   FCB  74     ;        16          133
LFCCB   FCB  74     ;        16          134
LFCCC   FCB  73     ;        15          135
LFCCD   FCB  73     ;        15          136
LFCCE   FCB  73     ;        15          137
LFCCF   FCB  72     ;        14          138
LFCD0   FCB  72     ;        14          139
LFCD1   FCB  71     ;        13          140
LFCD2   FCB  71     ;        13          141
LFCD3   FCB  70     ;        13          142
LFCD4   FCB  70     ;        13          143
LFCD5   FCB  70     ;        13          144
LFCD6   FCB  69     ;        12          145
LFCD7   FCB  69     ;        12          146
LFCD8   FCB  68     ;        11          147
LFCD9   FCB  68     ;        11          148
LFCDA   FCB  67     ;        10          149
LFCDB   FCB  67     ;        10          150
LFCDC   FCB  67     ;        10          151
LFCDD   FCB  66     ;        10          152
LFCDE   FCB  66     ;        10          153
LFCDF   FCB  65     ;         9          154
LFCE0   FCB  65     ;         9          155
LFCE1   FCB  64     ;         8          156
LFCE2   FCB  64     ;         8          157
LFCE3   FCB  63     ;         7          158
LFCE4   FCB  63     ;         7          159
LFCE5   FCB  63     ;         7          160
LFCE6   FCB  62     ;         7          161
LFCE7   FCB  62     ;         7          162
LFCE8   FCB  61     ;         6          163
LFCE9   FCB  61     ;         6          164
LFCEA   FCB  60     ;         5          165
LFCEB   FCB  60     ;         5          166
LFCEC   FCB  59     ;         4          167
LFCED   FCB  59     ;         4          168
LFCEE   FCB  59     ;         4          169
LFCEF   FCB  58     ;         4          170
LFCF0   FCB  58     ;         4          171
LFCF1   FCB  57     ;         3          172
LFCF2   FCB  57     ;         3          173
LFCF3   FCB  56     ;         2          174
LFCF4   FCB  56     ;         2          175
LFCF5   FCB  55     ;         1          176
LFCF6   FCB  55     ;         1          177
LFCF7   FCB  54     ;         1          178
LFCF8   FCB  54     ;         1          179
LFCF9   FCB  54     ;         1          180
LFCFA   FCB  53     ;        -0          181
LFCFB   FCB  53     ;        -0          182
LFCFC   FCB  52     ;        -1          183
LFCFD   FCB  52     ;        -1          184
LFCFE   FCB  51     ;        -2          185
LFCFF   FCB  51     ;        -2          186
LFD00   FCB  50     ;        -2          187
LFD01   FCB  50     ;        -2          188
LFD02   FCB  49     ;        -3          189
LFD03   FCB  49     ;        -3          190
LFD04   FCB  48     ;        -4          191
LFD05   FCB  48     ;        -4          192
LFD06   FCB  47     ;        -5          193
LFD07   FCB  47     ;        -5          194
LFD08   FCB  46     ;        -5          195
LFD09   FCB  45     ;        -6          196
LFD0A   FCB  45     ;        -6          197
LFD0B   FCB  44     ;        -7          198
LFD0C   FCB  44     ;        -7          199
LFD0D   FCB  43     ;        -8          200
LFD0E   FCB  43     ;        -8          201
LFD0F   FCB  42     ;        -8          202
LFD10   FCB  42     ;        -8          203
LFD11   FCB  41     ;        -9          204
LFD12   FCB  40     ;       -10          205
LFD13   FCB  40     ;       -10          206
LFD14   FCB  39     ;       -11          207
LFD15   FCB  39     ;       -11          208
LFD16   FCB  38     ;       -11          209
LFD17   FCB  37     ;       -12          210
LFD18   FCB  37     ;       -12          211
LFD19   FCB  36     ;       -13          212
LFD1A   FCB  35     ;       -14          213
LFD1B   FCB  35     ;       -14          214
LFD1C   FCB  34     ;       -14          215
LFD1D   FCB  33     ;       -15          216
LFD1E   FCB  33     ;       -15          217
LFD1F   FCB  32     ;       -16          218
LFD20   FCB  31     ;       -17          219
LFD21   FCB  31     ;       -17          220
LFD22   FCB  30     ;       -17          221
LFD23   FCB  29     ;       -18          222
LFD24   FCB  28     ;       -19          223
LFD25   FCB  28     ;       -19          224
LFD26   FCB  27     ;       -20          225
LFD27   FCB  26     ;       -20          226
LFD28   FCB  25     ;       -21          227
LFD29   FCB  24     ;       -22          228
LFD2A   FCB  23     ;       -23          229
LFD2B   FCB  22     ;       -23          230
LFD2C   FCB  21     ;       -24          231
LFD2D   FCB  20     ;       -25          232
LFD2E   FCB  19     ;       -26          233
LFD2F   FCB  18     ;       -26          234
LFD30   FCB  17     ;       -27          235
LFD31   FCB  16     ;       -28          236
LFD32   FCB  15     ;       -29          237
LFD33   FCB  13     ;       -30          238
LFD34   FCB  12     ;       -31          239
LFD35   FCB  11     ;       -32          240
LFD36   FCB  9      ;       -33          241
LFD37   FCB  8      ;       -34          242
LFD38   FCB  6      ;       -35          243
LFD39   FCB  4      ;       -37          244
LFD3A   FCB  3      ;       -38          245
LFD3B   FCB  1      ;       -39          246
LFD3C   FCB  0      ;       -40          247
LFD3D   FCB  0      ;       -40          248
LFD3E   FCB  0      ;       -40          249
LFD3F   FCB  0      ;       -40          250
LFD40   FCB  0      ;       -40          251
LFD41   FCB  0      ;       -40          252
LFD42   FCB  0      ;       -40          253
LFD43   FCB  0      ;       -40          254
LFD44   FCB  0      ;       -40          255
    ;--------------------------------------------------



    ;--------------------------------------------------
    ;  2nd 256 BYTE COOL TABLE ??
    ; TYPE $31 ECM                               
    ;
    ;
    ;
    ; TBL =  1.3333  * (dEG C cool + 40 )
    ;--------------------------------------------------
        ORG  $FD45  ;    Deg c COOL      A/D
                    ;----------------------------------
LFD45   FCB  255    ;
LFD46   FCB  255    ;
LFD47   FCB  255    ;
LFD48   FCB  255    ;
LFD49   FCB  255    ;
LFD4A   FCB  255    ;
LFD4B   FCB  255    ;
LFD4C   FCB  255    ;
LFD4D   FCB  255    ;
LFD4E   FCB  255    ;
LFD4F   FCB  255    ;
LFD50   FCB  255    ;
LFD51   FCB  255    ;
LFD52   FCB  255    ;
LFD53   FCB  255    ;
LFD54   FCB  255    ;
LFD55   FCB  255    ;
LFD56   FCB  255    ;
LFD57   FCB  255    ;
LFD58   FCB  255    ;
LFD59   FCB  255    ;
LFD5A   FCB  255    ;
LFD5B   FCB  255    ;
LFD5C   FCB  255    ;
LFD5D   FCB  255    ;
LFD5E   FCB  255    ;
LFD5F   FCB  255    ;
LFD60   FCB  255    ;
LFD61   FCB  255    ;
LFD62   FCB  255    ;
LFD63   FCB  255    ;
LFD64   FCB  253    ;
LFD65   FCB  251    ;
LFD66   FCB  249    ;
LFD67   FCB  247    ;
LFD68   FCB  245    ;
LFD69   FCB  243    ;
LFD6A   FCB  241    ;
LFD6B   FCB  239    ;
LFD6C   FCB  237    ;
LFD6D   FCB  236    ;
LFD6E   FCB  234    ;
LFD6F   FCB  232    ;
LFD70   FCB  231    ;
LFD71   FCB  229    ;
LFD72   FCB  228    ;
LFD73   FCB  227    ;
LFD74   FCB  225    ;
LFD75   FCB  224    ;
LFD76   FCB  222    ;
LFD77   FCB  221    ;
LFD78   FCB  220    ;
LFD79   FCB  219    ;
LFD7A   FCB  217    ;
LFD7B   FCB  216    ;
LFD7C   FCB  215    ;
LFD7D   FCB  214    ;
LFD7E   FCB  213    ;
LFD7F   FCB  211    ;
LFD80   FCB  210    ;
LFD81   FCB  209    ;
LFD82   FCB  208    ;
LFD83   FCB  207    ;
LFD84   FCB  206    ;
LFD85   FCB  205    ;
LFD86   FCB  204    ;
LFD87   FCB  203    ;
LFD88   FCB  202    ;
LFD89   FCB  201    ;
LFD8A   FCB  200    ;
LFD8B   FCB  199    ;
LFD8C   FCB  198    ;
LFD8D   FCB  197    ;
LFD8E   FCB  196    ;
LFD8F   FCB  195    ;
LFD90   FCB  195    ;
LFD91   FCB  194    ;
LFD92   FCB  193    ;
LFD93   FCB  192    ;
LFD94   FCB  191    ;
LFD95   FCB  190    ;
LFD96   FCB  189    ;
LFD97   FCB  189    ;
LFD98   FCB  188    ;
LFD99   FCB  187    ;
LFD9A   FCB  186    ;
LFD9B   FCB  185    ;
LFD9C   FCB  185    ;
LFD9D   FCB  184    ;
LFD9E   FCB  183    ;
LFD9F   FCB  182    ;
LFDA0   FCB  182    ;
LFDA1   FCB  181    ;
LFDA2   FCB  180    ;
LFDA3   FCB  179    ;
LFDA4   FCB  179    ;
LFDA5   FCB  178    ;
LFDA6   FCB  177    ;
LFDA7   FCB  176    ;
LFDA8   FCB  176    ;
LFDA9   FCB  175    ;
LFDAA   FCB  174    ;
LFDAB   FCB  174    ;
LFDAC   FCB  173    ;
LFDAD   FCB  172    ;
LFDAE   FCB  171    ;
LFDAF   FCB  171    ;
LFDB0   FCB  170    ;
LFDB1   FCB  169    ;
LFDB2   FCB  169    ;
LFDB3   FCB  168    ;
LFDB4   FCB  167    ;
LFDB5   FCB  167    ;
LFDB6   FCB  166    ;
LFDB7   FCB  165    ;
LFDB8   FCB  165    ;
LFDB9   FCB  164    ;
LFDBA   FCB  163    ;
LFDBB   FCB  163    ;
LFDBC   FCB  162    ;
LFDBD   FCB  161    ;
LFDBE   FCB  161    ;
LFDBF   FCB  160    ;
LFDC0   FCB  160    ;
LFDC1   FCB  159    ;
LFDC2   FCB  158    ;
LFDC3   FCB  158    ;
LFDC4   FCB  157    ;
LFDC5   FCB  156    ;
LFDC6   FCB  156    ;
LFDC7   FCB  155    ;
LFDC8   FCB  155    ;
LFDC9   FCB  154    ;
LFDCA   FCB  153    ;
LFDCB   FCB  153    ;
LFDCC   FCB  152    ;
LFDCD   FCB  151    ;
LFDCE   FCB  151    ;
LFDCF   FCB  150    ;
LFDD0   FCB  150    ;
LFDD1   FCB  149    ;
LFDD2   FCB  148    ;
LFDD3   FCB  148    ;
LFDD4   FCB  147    ;
LFDD5   FCB  147    ;
LFDD6   FCB  146    ;
LFDD7   FCB  145    ;
LFDD8   FCB  145    ;
LFDD9   FCB  144    ;
LFDDA   FCB  143    ;
LFDDB   FCB  143    ;
LFDDC   FCB  142    ;
LFDDD   FCB  142    ;
LFDDE   FCB  141    ;
LFDDF   FCB  140    ;
LFDE0   FCB  140    ;
LFDE1   FCB  139    ;
LFDE2   FCB  139    ;
LFDE3   FCB  138    ;
LFDE4   FCB  137    ;
LFDE5   FCB  137    ;
LFDE6   FCB  136    ;
LFDE7   FCB  135    ;
LFDE8   FCB  135    ;
LFDE9   FCB  134    ;
LFDEA   FCB  134    ;
LFDEB   FCB  133    ;
LFDEC   FCB  132    ;
LFDED   FCB  132    ;
LFDEE   FCB  131    ;
LFDEF   FCB  130    ;
LFDF0   FCB  130    ;
LFDF1   FCB  129    ;
LFDF2   FCB  128    ;
LFDF3   FCB  128    ;
LFDF4   FCB  127    ;
LFDF5   FCB  126    ;
LFDF6   FCB  126    ;
LFDF7   FCB  125    ;
LFDF8   FCB  125    ;
LFDF9   FCB  124    ;
LFDFA   FCB  123    ;
LFDFB   FCB  122    ;
LFDFC   FCB  122    ;
LFDFD   FCB  121    ;
LFDFE   FCB  120    ;
LFDFF   FCB  120    ;
LFE00   FCB  119    ;
LFE01   FCB  118    ;
LFE02   FCB  118    ;
LFE03   FCB  117    ;
LFE04   FCB  116    ;
LFE05   FCB  116    ;
LFE06   FCB  115    ;
LFE07   FCB  114    ;
LFE08   FCB  113    ;
LFE09   FCB  113    ;
LFE0A   FCB  112    ;
LFE0B   FCB  111    ;
LFE0C   FCB  110    ;
LFE0D   FCB  109    ;
LFE0E   FCB  109    ;
LFE0F   FCB  108    ;
LFE10   FCB  107    ;
LFE11   FCB  106    ;
LFE12   FCB  105    ;
LFE13   FCB  105    ;
LFE14   FCB  104    ;
LFE15   FCB  103    ;
LFE16   FCB  102    ;
LFE17   FCB  101    ;
LFE18   FCB  100    ;
LFE19   FCB  99     ;
LFE1A   FCB  98     ;
LFE1B   FCB  97     ;
LFE1C   FCB  97     ;
LFE1D   FCB  96     ;
LFE1E   FCB  95     ;
LFE1F   FCB  94     ;
LFE20   FCB  92     ;
LFE21   FCB  91     ;
LFE22   FCB  90     ;
LFE23   FCB  89     ;
LFE24   FCB  88     ;
LFE25   FCB  87     ;
LFE26   FCB  86     ;
LFE27   FCB  85     ;
LFE28   FCB  83     ;
LFE29   FCB  82     ;
LFE2A   FCB  81     ;
LFE2B   FCB  79     ;
LFE2C   FCB  78     ;
LFE2D   FCB  76     ;
LFE2E   FCB  75     ;
LFE2F   FCB  73     ;
LFE30   FCB  71     ;
LFE31   FCB  70     ;
LFE32   FCB  68     ;
LFE33   FCB  66     ;
LFE34   FCB  64     ;
LFE35   FCB  62     ;
LFE36   FCB  59     ;
LFE37   FCB  57     ;
LFE38   FCB  54     ;
LFE39   FCB  51     ;
LFE3A   FCB  47     ;
LFE3B   FCB  43     ;
LFE3C   FCB  39     ;
LFE3D   FCB  34     ;
LFE3E   FCB  27     ;
LFE3F   FCB  18     ;
LFE40   FCB  3      ;
LFE41   FCB  0      ;
LFE42   FCB  0      ;
LFE43   FCB  0      ;
LFE44   FCB  0      ;
    ;--------------------------------------------------



        ;---------------------------------------------
    	; MAT LINEARATY TBL
    	;
    	; 08-21-1996  Dissassemby of BMHM  Lines= 17 
    	;
    	;      
        ;---------------------------------------------
        ORG  $FE45  ; A/D		 Deg C                   
                    ;-----------------
LFE45   FCB  0      ; 0   		  -40
LFE46   FCB  26     ; 26  		  -28 
LFE47   FCB  44     ; 44  		  -16 
LFE48   FCB  56     ; 56  		  -4  
LFE49   FCB  65     ; 65  		   8  
LFE4A   FCB  74     ; 74  		   20 
LFE4B   FCB  82     ; 82  		   32 
LFE4C   FCB  89     ; 89  		   44
LFE4D   FCB  97     ; 97  		   56
LFE4E   FCB  105    ; 105 		   68 
LFE4F   FCB  113    ; 113 		   80 
LFE50   FCB  122    ; 122 		   92 
LFE51   FCB  133    ; 133 		  104 
LFE52   FCB  147    ; 147 		  116 
LFE53   FCB  166    ; 166 		  128 
LFE54   FCB  199    ; 199 		  140 
LFE55   FCB  255    ; 255 		  152 
        ;---------------------------------------------


		***************************************************

        ;---------------------------------------------
    	; PCM TYPE $31 ERR BLINK OUT CODES
    	;
        ;---------------------------------------------
		ORG	$FE56

LFE56   FCB $12     ; ERR 12,
LFE57   FCB $13     ; ERR 13,	o2 SENSOR
LFE58   FCB $14     ; ERR 14,	COOL SENSOR, HIGH
LFE59   FCB $15     ; ERR 15,	COOL SENSOR, LOW
LFE5A   FCB $16     ; ERR 16,	Vss BUFFER
LFE5B   FCB $17     ; ERR 17,	RPM SIGNAL PROBLEM
LFE5C   FCB $18     ; ERR 18,	CAM CRANK ERROR
LFE5D   FCB $19     ; ERR 19
LFE5E   FCB $21     ; ERR 21,	TPS SENSOR HIGH
LFE5F   FCB $22     ; ERR 22,	LOW TPS
LFE60   FCB $23     ; ERR 23,	LOW MAT
LFE61   FCB $24     ; ERR 24,	LOW Vss
LFE62   FCB $25     ; ERR 25,	MAT LOW 
LFE63   FCB $26     ; ERR 26
LFE64   FCB $27     ; ERR 27
LFE65   FCB $28     ; ERR 28
LFE66   FCB $29     ; ERR 29
LFE67   FCB $31     ; ERR 31,	ERR 31 GOVERNER FAIL
LFE68   FCB $32     ; ERR 32,	EGR ERROR
LFE69   FCB $33     ; ERR 33,	MAP SENSOR HI
LFE6A   FCB $34     ; ERR 34,	MAP SNENSOR LOW
LFE6B   FCB $35     ; ERR 35,	IAC ERROR
LFE6C   FCB $36     ; ERR 36,
LFE6D   FCB $37     ; ERR 37,	TCC BRAKE SW STUCK ON
LFE6E   FCB $38     ; ERR 38,	TCC BRAKE SW STUCK OFF
LFE6F   FCB $39     ; ERR 39,	TCC STUCK OFF 
LFE70   FCB $41     ; ERR 41,	1x CAM SENSOR 
LFE71   FCB $42     ; ERR 42,	IGN ERROR
LFE72   FCB $43     ; ERR 43,	KNOCK SENSOR CKT
LFE73   FCB $44     ; ERR 44,	LEAN
LFE74   FCB $45     ; ERR 45,	RICH
LFE75   FCB $46     ; ERR 46,	VATS FAIL
LFE76   FCB $47     ; ERR 47,
LFE77   FCB $48     ; ERR 48
LFE78   FCB $49     ; ERR 49
LFE79   FCB $51     ; ERR 51,	EPROM ERROR
LFE7A   FCB $52     ; ERR 52,	MISSING FUEL CALPACK
LFE7B   FCB $53     ; ERR 53,	HI SYS VOLTAGE
LFE7C   FCB $54     ; ERR 54,	LOW FUEL PUMP VDC
LFE7D   FCB $55     ; ERR 55,	FAULTY COMPUTER
LFE7E   FCB $56     ; ERR 56,	QUAD DRIVER B FAULT
LFE7F   FCB $57     ; ERR 57
LFE80   FCB $58     ; ERR 58,	HI XMIXH TEMP
LFE81   FCB $59     ; ERR 59,	LO XMISH TEMP
LFE82   FCB $61     ; ERR 61
LFE83   FCB $62     ; ERR 62
LFE84   FCB $63     ; ERR 63,	HIGH BARO PRESS
LFE85   FCB $64     ; ERR 64,	LOW BARO PRESS
LFE86   FCB $65     ; ERR 65,
LFE87   FCB $66     ; ERR 66,	3 -> 2 SHFT QUAD DVR FAIL
LFE88   FCB $67     ; ERR 67,	TCC ENAB QUAD DVR FAIL
LFE89   FCB $68     ; ERR 68,	XMISH SLIPPING
LFE8A   FCB $69     ; ERR 69,	TCC ON
LFE8B   FCB $71     ; ERR 71,	LOW ENGINE SPD 
LFE8C   FCB $72     ; ERR 72,	OUTPUT SPD LOSS
LFE8D   FCB $73     ; ERR 73,	FORCE MOTOR CURRENT
LFE8E   FCB $74     ; ERR 74,	TURBINE SPEED
LFE8F   FCB $75     ; ERR 75,	LOW SYS VOLTAGE  
LFE90   FCB $76     ; ERR 76,
LFE91   FCB $77     ; ERR 77,	MNP SWITCH
LFE92   FCB $78     ; ERR 78,
LFE93   FCB $79     ; ERR 79,	HOT XMISH
LFE94   FCB $81     ; ERR 81,	QUAD DVR 1 & SHFT B ERR
LFE95   FCB $82     ; ERR 82,	QUAD DVR 1 & SHFT A ERR
LFE96   FCB $83     ; ERR 83,	QUAD DVR 1 ERR
LFE97   FCB $84     ; ERR 84,
LFE98   FCB $85     ; ERR 85,
LFE99   FCB $86     ; ERR 86,
LFE9A   FCB $87     ; ERR 87,
LFE9B   FCB $88     ; ERR 88,
LFE9C   FCB $89     ; ERR 89,
LFE9D   FCB $91     ; ERR 91,
LFE9E   FCB $92     ; ERR 92,
***********************************************************

LFE9F	FCB	0

***********************************************************
*
* ALL 0'S FE9F th FF8F
* OBJECT FILE: BMHM
***********************************************************
LFF9F   FCB $0      ;
		;
		;
		;
		;
LFF8F   FCB $	      ;
***********************************************************


		;--------------------------------------------------
		;
		;
		;--------------------------------------------------
FF90:	  FDB     $7E98
FF92:     FDB     $997E
FF94:     FDB     $A3FA
FF96:     FDB     $7EF3

FF98:     FDB     $2600
FF9A:     FDB     $0000
FF9C:     FDB     $0000
FF9E:     FDB     $0000

FFA0:     FDB     $F2AA
FFA2:     FDB     $F25F
FFA4:     FDB     $F275
FFA6:     FDB     $F3E4

FFA8:     FDB     $0035
FFAA:     FDB     $036C	  		; DATA BUFFER, 34 BYTES
FFAC:     FDB     $0000
FFAE:     FDB     $0000

FFB0:     FDB     $53E1
FFB2:     FDB     $0000
FFB4:     FDB     $0000
FFB6:     FDB     $0000

FFB8:     FDB     $0000
FFBA:     FDB     $0000
FFBC:     FDB     $0000
FFBE:     FDB     $0000

			;------------------
			; RESERVED VECTORS
			;
			;------------------
FFC0:     FDB     $FC44
FFC2:     FDB     $FC44
FFC4:     FDB     $FC44
FFC6:     FDB     $FC44

FFC8:     FDB     $FC44
FFCA:     FDB     $FC44
FFCC:     FDB     $FC44

FFCE:     FDB     $FC44
FFD0:     FDB     $FC44
FFD2:     FDB     $FC44
FFD4:     FDB     $FC44
		;--------------------------------------------------



		;--------------------------------------------------
FFD6:     FDB     $F7EA    	; SCI INTERUPT 

FFD8:     FDB     $FC44    	; SPI VECTOR TO RTI

FFDA:     FDB     $FC3A    	; PA INPUT EDGE VECTOR
FFDC:     FDB     $FC3A    	; PA OVER FLOW
FFDE:     FDB     $FC3A 	; TMR OVERFLOW

FFE0:     FDB     $7875    	; TOC 5
FFE2:     FDB     $78D9    	; TOC 4
FFE4:     FDB     $793D    	; TOC 3
FFE6:     FDB     $FC2F    	; TOC 2
FFE8:     FDB     $CE7C    	; TOC 1

FFEA:     FDB     $FC2F    	; TIC 3
FFEC:     FDB     $FC2F    	; TIC 2
FFEE:     FDB     $FC2F    	; TIC 1

FFF0:     FDB     $FC2F    	; REAL TIME INTERUPT

FFF2:     FDB     $74EA    	; IRQ
FFF4:     FDB     $FC09    	; XIRQ
FFF6:     FDB     $FC04    	; SWI
FFF8:     FDB     $FC1A    	; ILLEAGL OP CODE

FFFA:     FDB     $FC1F    	; COP TIME OUT
FFFC:     FDB     $FC24    	; CLOCK FAIL
FFFE:     FDB     $FC29	 	; EXT RESET
	***********************************************************
	***********************************************************


