# 7427 ASIC / Hardware Register Contract v0.1

Generated from static source walk. This is not a dynamic proof; unknown or inferred meanings are marked as test items.

## HC11 relocated registers

| Address | Name / hypothesis | Accesses | First PCs | Constant writes / source hints | Contract status |
|---|---|---:|---|---|---|
| `0x103D` | CPU INIT REG | indexed_resolved | W:1 | 0x7108 | 0x7108 STAA $3D,X ← A=0x03 | KEEP / required until bench proven otherwise |
| `0x3000` | PORTA / timer pin status | W:1, R:5 | 0x7120, 0x77E2, 0x7812, 0x787C, 0x78E0, 0xAEA7 | 0x7120 STAA 0,X ← A=0x00 | KEEP / required until bench proven otherwise |
| `0x3001` | PIOC | W:1 | 0xCC97 | 0xCC97 STAA $0001,X ← A=0x38 | KEEP / required until bench proven otherwise |
| `0x3002` | PORTC | R:1 | 0xAEB1 |  | KEEP / required until bench proven otherwise |
| `0x3003` | PORTB | W:1 | 0xCC8B | 0xCC8B STAA $03,X ← A=0x00 | KEEP / required until bench proven otherwise |
| `0x3008` | PORTE / ADC input port | W:3, R:3, RMW:2 | 0x7122, 0x9251, 0xD162, 0xD168, 0xD16A, 0xF275, 0xF27B, 0xF27D | 0x7122 STAA $08,X ← A=0x00 | KEEP / required until bench proven otherwise |
| `0x3009` | CFORC/Timer force compare candidate | W:1 | 0xCC9B | 0xCC9B STAA $0009,X ← A=0x38 | KEEP / required until bench proven otherwise |
| `0x300B` | CFORC / compare force | W:1 | 0xCC83 | 0xCC83 STAA $0B,X ← A=0x00 | KEEP / required until bench proven otherwise |
| `0x300C` | OC1D candidate | W:1 | 0xCC7D | 0xCC7D STAA $0C,X ← A=0x00 | KEEP / required until bench proven otherwise |
| `0x300D` | TCNT high? candidate | W:1 | 0xCC7F | 0xCC7F STAA $0D,X ← A=0x00 | KEEP / required until bench proven otherwise |
| `0x300E` | TCNT 16-bit free-running counter | R:9 | 0x745E, 0x74F1, 0x77D6, 0x7806, 0x78B5, 0x78C8, 0x7919, 0x792C, 0x7A62 |  | KEEP / required until bench proven otherwise |
| `0x3010` | TIC1 | R:2 | 0xAF7B, 0xAF83 |  | KEEP / required until bench proven otherwise |
| `0x3012` | TIC2 | R:2 | 0x7425, 0xAE67 |  | KEEP / required until bench proven otherwise |
| `0x3016` | TOC1 | W:1 | 0x7503 |  | KEEP / required until bench proven otherwise |
| `0x301A` | TOC3 | W:2, R:2 | 0x7464, 0x793D, 0x7943, 0x7A65 |  | KEEP / required until bench proven otherwise |
| `0x301C` | TOC4 compare | R:3, W:2 | 0x7819, 0x7824, 0x78FC, 0x7914, 0x793A |  | KEEP / required until bench proven otherwise |
| `0x301E` | TOC5/TIC4 compare | R:3, W:2 | 0x77E9, 0x77F4, 0x7898, 0x78B0, 0x78D6 |  | KEEP / required until bench proven otherwise |
| `0x3020` | TCTL1 output compare action | RMW:6 | 0x77EE, 0x781E, 0x7883, 0x78C5, 0x78E7, 0x7929 |  | KEEP / required until bench proven otherwise |
| `0x3021` | TCTL2 input capture edge | W:1 | 0xCC8F | 0xCC8F STAA $0021,X ← A=0x26 | KEEP / required until bench proven otherwise |
| `0x3022` | TMSK1 timer interrupt mask | W:2, RMW:5 | 0x7469, 0x77DF, 0x780F, 0x7880, 0x78E4, 0xCC56, 0xFC31 | 0x7469 STAA L3022 ← A=0xA0; 0xFC31 STAA L3022 ← A=0xA0 | KEEP / required until bench proven otherwise |
| `0x3023` | TFLG1 timer interrupt flags / write-one-clear | W:12, R:2 | 0x745B, 0x754D, 0x7597, 0x76E1, 0x772B, 0x7731, 0x77DD, 0x780D, 0x787A, 0x78DE, ... | 0x745B STAA L3023 ← A=0xFF; 0x754D STAA $23,X ← A=0x01; 0x76E1 STAA $23,X ← A=0x01; 0x7731 STAA $23,X ← A=0x01; 0x77DD STAA $23,X ← A=0x08; 0x780D STAA $23,X ← A=0x10; 0x787A STAA $23,X ← A=0x08; 0x78DE STAA $23,X ← A=0x10 | KEEP / required until bench proven otherwise |
| `0x3024` | TMSK2 timer prescale/RTI mask | W:2 | 0x7113, 0xFC3C | 0x7113 STAA $24,X ← A=0x03; 0xFC3C STAA L3024 ← A=0x03 | KEEP / required until bench proven otherwise |
| `0x3025` | TFLG2 timer flags | W:1 | 0xFC41 | 0xFC41 STAA L3025 ← A=0xFF | KEEP / required until bench proven otherwise |
| `0x3026` | PACTL pulse accumulator control | W:1 | 0xCC93 | 0xCC93 STAA $0026,X ← A=0x40 | KEEP / required until bench proven otherwise |
| `0x3027` | PACNT pulse accumulator count | R:2 | 0xAF78, 0xAF7E |  | KEEP / required until bench proven otherwise |
| `0x3028` | SPCR SPI control | W:1 | 0xCC85 | 0xCC85 STAA $28,X ← A=0x00 | KEEP / required until bench proven otherwise |
| `0x3030` | ADCTL A/D control | W:4, R:3 | 0x7521, 0x7B73, 0x7B79, 0xD171, 0xD176, 0xF262, 0xF267 | 0x7B73 STAA L3030 ← A=0x07; 0xD171 STAA L3030 ← A=0x01 | KEEP / required until bench proven otherwise |
| `0x3031` | ADR1 A/D result 1 | R:5 | 0x7528, 0x7B7E, 0xF24C, 0xFA6B, 0xFA7B |  | KEEP / required until bench proven otherwise |
| `0x3032` | ADR2 A/D result 2 | R:3 | 0x7B81, 0xF236, 0xF254 |  | KEEP / required until bench proven otherwise |
| `0x3033` | ADR3 A/D result 3 | R:3 | 0x7B86, 0xF23B, 0xF259 |  | KEEP / required until bench proven otherwise |
| `0x3034` | ADR4 A/D result 4 | R:9 | 0x7B8B, 0xC57D, 0xC599, 0xCEF1, 0xD184, 0xDC0A, 0xF21A, 0xF229, 0xF23F |  | KEEP / required until bench proven otherwise |
| `0x3035` | BPROT EEPROM block protect | W:1 | 0x711A | 0x711A STAA $35,X ← A=0x1B | KEEP / required until bench proven otherwise |
| `0x3038` | OPT2 | RMW:1 | 0x7115 |  | KEEP / required until bench proven otherwise |
| `0x3039` | OPTION | W:2 | 0x710F, 0x7D89 | 0x710F STAA $39,X ← A=0xB8; 0x7D89 STAB L3039 ← B=0x08 | KEEP / required until bench proven otherwise |
| `0x303A` | COPRST watchdog clear | W:10 | 0x7443, 0x7448, 0x79EA, 0x79ED, 0x7DB3, 0x9169, 0xF2EF, 0xF2F3, 0xFA87, 0xFA8A | 0x7443 STAA L303A ← A=0x55; 0x7448 STAA L303A ← A=0xAA; 0x79EA STAA L303A ← A=0xAA; 0x79ED STAB L303A ← B=0x55; 0x7DB3 STAA L303A ← A=0x55; 0x9169 STAB L303A ← B=0xAA; 0xF2EF STAA L303A ← A=0x55; 0xF2F3 STAA L303A ← A=0x55 | KEEP / required until bench proven otherwise |
| `0x303C` | indexed_resolved | W:1 | 0xCCA3 | 0xCCA3 STAA $003C,X ← A=0x15 | KEEP / required until bench proven otherwise |
| `0x303E` | indexed_resolved | W:1 | 0xCC87 | 0xCC87 STAA $3E,X ← A=0x00 | KEEP / required until bench proven otherwise |
| `0x303F` | CONFIG/EPROM config candidate | R:1 | 0x71C6 |  | KEEP / required until bench proven otherwise |

## SCI/ALDL registers

| Address | Name / hypothesis | Accesses | First PCs | Constant writes / source hints | Contract status |
|---|---|---:|---|---|---|
| `0x302B` | BAUD SCI baud | W:1 | 0xCC9F | 0xCC9F STAA $002B,X ← A=0x04 | KEEP / required until bench proven otherwise |
| `0x302C` | SCCR1 SCI control 1 | W:1 | 0xCC81 | 0xCC81 STAA $2C,X ← A=0x00 | KEEP / required until bench proven otherwise |
| `0x302D` | SCCR2 SCI control 2 | W:8, R:3 | 0x7154, 0xF645, 0xF7AF, 0xF7ED, 0xF7FA, 0xF807, 0xF811, 0xF907, 0xF950, 0xFA48, ... | 0x7154 STAB $2D,X ← B=0x26; 0xF645 STAA L302D ← A=0x88; 0xF7AF STAA L302D ← A=0x26; 0xF811 STAA $2D,X ← A=0x26; 0xF907 STAA L302D ← A=0x40; 0xF950 STAA L302D ← A=0x24; 0xFA48 STAA L302D ← A=0x88; 0xFA57 STAA L302D ← A=0x26 | KEEP / required until bench proven otherwise |
| `0x302E` | SCSR SCI status | R:8 | 0x7150, 0xF608, 0xF7F1, 0xF7FE, 0xF80B, 0xF8FF, 0xF90B, 0xFA2B |  | KEEP / required until bench proven otherwise |
| `0x302F` | SCDR SCI data | W:3, R:2 | 0xF60B, 0xF8E6, 0xF902, 0xF90E, 0xFA30 |  | KEEP / required until bench proven otherwise |

## External ASIC / board registers

| Address | Name / hypothesis | Accesses | First PCs | Constant writes / source hints | Contract status |
|---|---|---:|---|---|---|
| `0x3FC0` | ASIC last DRP/ref period counter | R:8 | 0x842C, 0x858B, 0xA551, 0xA581, 0xA5E5, 0xA6EF, 0xAB8E, 0xAC58 |  | KEEP / required until bench proven otherwise |
| `0x3FC0-0x3FF8` | loop clears even ASIC words from $3FC0 through before $3FFA | ASIC last DRP/ref period cou | W:1 | 0x715B |  | Likely ASIC config/status; trace before minimal OS removal |
| `0x3FC4` | ASIC period/status latch candidate | R:1 | 0x7C00 |  | Likely ASIC config/status; trace before minimal OS removal |
| `0x3FC6` | indexed_resolved | R:2 | 0xAFC5, 0xAFD2 |  | Likely ASIC config/status; trace before minimal OS removal |
| `0x3FC8` | ASIC timing/status candidate | R:1 | 0xCE81 |  | Likely ASIC config/status; trace before minimal OS removal |
| `0x3FCA` | ASIC 16-bit RPM/event counter | R:4 | 0x741F, 0x8629, 0xABD3, 0xE01E |  | KEEP / required until bench proven otherwise |
| `0x3FCC` | ASIC fuel/scheduler command candidate A | W:2 | 0x74D6, 0xFADC | 0x74D6 STD L3FCC ← D=0xD000 | Likely ASIC config/status; trace before minimal OS removal |
| `0x3FCE` | ASIC EFI PW / fuel pulse-width handoff | W:4 | 0x8426, 0x8512, 0xFAEE, 0xFB44 | 0x8512 STD L3FCE ← D=0x7FFF; 0xFAEE STD L3FCE ← D=0x00C5; 0xFB44 STD L3FCE ← D=0x0000 | KEEP / required until bench proven otherwise |
| `0x3FD4` | ASIC output compare/scheduler slot D4 | W:3 | 0xCDCB, 0xFB78, 0xFB9B |  | Likely ASIC config/status; trace before minimal OS removal |
| `0x3FD6` | ASIC output compare/scheduler slot D6 | W:3 | 0xCD8D, 0xFB7D, 0xFBA3 |  | Likely ASIC config/status; trace before minimal OS removal |
| `0x3FD8` | ASIC output compare/scheduler slot D8 | W:3 | 0xCE0C, 0xFB82, 0xFBAB |  | Likely ASIC config/status; trace before minimal OS removal |
| `0x3FDA` | ASIC output compare/scheduler slot DA | W:3 | 0xCD71, 0xFB87, 0xFBB3 | 0xCD71 STD L3FDA ← D=0xD000 | Likely ASIC config/status; trace before minimal OS removal |
| `0x3FDC` | ASIC spark dwell / spark work period handoff | R:1, W:2 | 0xABB0, 0xABC0, 0xFAF7 |  | KEEP / required until bench proven otherwise |
| `0x3FE0` | ASIC timing/status candidate E0 | R:1 | 0xACD3 |  | Likely ASIC config/status; trace before minimal OS removal |
| `0x3FE4` | ASIC ignition/output companion write | W:1 | 0xAC2E |  | Likely ASIC config/status; trace before minimal OS removal |
| `0x3FE6` | ASIC spark handoff path | W:1 | 0xABBA |  | KEEP / required until bench proven otherwise |
| `0x3FE8` | ASIC EST/spark timing output engine | W:1 | 0xABAA |  | KEEP / required until bench proven otherwise |
| `0x3FEA` | ASIC fuel/scheduler command candidate B | W:2 | 0x74DF, 0xFAE5 | 0x74DF STD L3FEA ← D=0xDFFF | Likely ASIC config/status; trace before minimal OS removal |
| `0x3FEC` | ASIC hardware status/source | R:1 | 0xAC28 |  | KEEP / required until bench proven otherwise |
| `0x3FF2` | ASIC output/scheduler candidate | W:1 | 0x8571 |  | Likely ASIC config/status; trace before minimal OS removal |
| `0x3FF6` | ASIC EST fall counter / output scheduler | R:2, W:2 | 0xAB97, 0xABA4, 0xABC8, 0xFB03 |  | KEEP / required until bench proven otherwise |
| `0x3FF8` | indexed_resolved | R:1 | 0xAFCC |  | Likely ASIC config/status; trace before minimal OS removal |
| `0x3FFA` | ASIC packed hardware status | R:2 | 0x7765, 0x7BF6 |  | KEEP / required until bench proven otherwise |
| `0x3FFC` | ASIC I/O D port / external output latch | W:13, R:10 | 0x713A, 0x7140, 0x714A, 0x71BD, 0x71EF, 0x71F7, 0x8577, 0x857F, 0x8587, 0xCC5A, ... |  | KEEP / required until bench proven otherwise |

## Unknown external hardware / board register space

| Address | Name / hypothesis | Accesses | First PCs | Constant writes / source hints | Contract status |
|---|---|---:|---|---|---|
| `0x305C` | indexed_resolved | W:1 | 0xCC89 | 0xCC89 STAA $5C,X ← A=0x00 | TEST ITEM: classify before removal |
| `0x305D` | indexed_resolved | W:1 | 0xCCA7 | 0xCCA7 STAA $005D,X ← A=0xAC | TEST ITEM: classify before removal |
| `0x305E` | indexed_resolved | W:1 | 0xCCAF | 0xCCAF STAA $005E,X ← A=0x00 | TEST ITEM: classify before removal |
| `0x305F` | indexed_resolved | W:1 | 0xCCAB | 0xCCAB STAA $005F,X ← A=0xCB | TEST ITEM: classify before removal |
| `0x3060` | CLR b4, | indexed_resolved | RMW:1, R:3, W:2 | 0xA5D4, 0xAEB7, 0xF400, 0xF409, 0xFB4A, 0xFB51 |  | TEST ITEM: classify before removal |
| `0x3061` |  | W:1 | 0xCCB3 | 0xCCB3 STAA L3061 ← A=0x90 | TEST ITEM: classify before removal |
| `0x3062` | External 306x hardware latch/status candidate | RMW:2, R:4, W:4 | 0x7509, 0x750C, 0xAEBA, 0xF411, 0xFB14, 0xFB28, 0xFB39, 0xFB3E, 0xFB54, 0xFB5B |  | TEST ITEM: classify before removal |
| `0x3063` |  | W:1 | 0xCCB8 | 0xCCB8 STAA L3063 ← A=0xFF | TEST ITEM: classify before removal |
| `0x3064` | I/O PORT C | R:2 | 0xF414, 0xFAD4 |  | TEST ITEM: classify before removal |
| `0x3065` |  | W:1 | 0xCCBD | 0xCCBD STAA L3065 ← A=0x00 | TEST ITEM: classify before removal |
| `0x3067` |  | W:1 | 0xF41B |  | TEST ITEM: classify before removal |
| `0x3068` | External 306x output command candidate | W:3 | 0x7BA3, 0xFB93, 0xFBCB |  | TEST ITEM: classify before removal |
| `0x306A` |  | W:4 | 0xC56B, 0xCDF3, 0xFB8A, 0xFBB9 | 0xCDF3 STD L306A ← D=0x7F00 | TEST ITEM: classify before removal |
| `0x306C` |  | W:4 | 0x9163, 0xCDDF, 0xFB8D, 0xFBBF | 0xCDDF STD L306C ← D=0x1F00 | TEST ITEM: classify before removal |
| `0x306E` | External 306x I/O latch candidate | W:3 | 0x7128, 0xFB90, 0xFBC5 |  | TEST ITEM: classify before removal |
| `0x306F` | External 306x I/O latch/status candidate | W:2 | 0x7518, 0xA5AA | 0x7518 STAB L306F ← B=0xFF; 0xA5AA STAA L306F ← A=0x00 | TEST ITEM: classify before removal |
