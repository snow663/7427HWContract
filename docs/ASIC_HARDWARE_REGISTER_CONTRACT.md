# ASIC / Hardware Register Contract

Current concise contract generated from `maps/current/hardware_access_map_hw_only.csv`. Static evidence only; dynamic trace must prove side effects and timing.

| Address | Proposed name | Subsystem | Access | Count | Risk | First PCs | Required for minimal OS | Test needed |
|---|---|---|---:|---:|---|---|---|---|
| `0x103D` | unclassified hardware access | OTHER | `W` | 1 | LOW | `0x7108` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3000` | unclassified hardware access | boot/watchdog/core CPU | `R/W` | 6 | HIGH | `0x7120, 0x77E2, 0x7812, 0x787C, 0x78E0` | yes/test | preserve init/watchdog sequence until boot proven |
| `0x3001` | unclassified hardware access | HC11 timer/core | `W` | 1 | LOW | `0xCC97` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3002` | unclassified hardware access | HC11 timer/core | `R` | 1 | LOW | `0xAEB1` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3003` | unclassified hardware access | HC11 timer/core | `W` | 1 | LOW | `0xCC8B` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3008` | unclassified hardware access | sensor acquisition | `R/RMW/W` | 8 | HIGH | `0x7122, 0x9251, 0xD162, 0xD168, 0xD16A` | yes/test | verify channel select/result order and scaling |
| `0x3009` | unclassified hardware access | HC11 timer/core | `W` | 1 | LOW | `0xCC9B` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x300B` | unclassified hardware access | HC11 timer/core | `W` | 1 | LOW | `0xCC83` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x300C` | unclassified hardware access | HC11 timer/core | `W` | 1 | LOW | `0xCC7D` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x300D` | unclassified hardware access | HC11 timer/core | `W` | 1 | LOW | `0xCC7F` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x300E` | unclassified hardware access | HC11 timer/core | `R` | 9 | LOW | `0x745E, 0x74F1, 0x77D6, 0x7806, 0x78B5` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3010` | unclassified hardware access | HC11 timer/core | `R` | 2 | LOW | `0xAF7B, 0xAF83` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3012` | unclassified hardware access | HC11 timer/core | `R` | 2 | LOW | `0x7425, 0xAE67` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3016` | unclassified hardware access | spark or EST handoff | `W` | 1 | HIGH | `0x7503` | yes/test | trace value units vs spark/RPM and EST/bypass latch timing |
| `0x301A` | unclassified hardware access | HC11 timer/core | `R/W` | 4 | LOW | `0x7464, 0x793D, 0x7943, 0x7A65` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x301C` | unclassified hardware access | timer compare / injector scheduler | `R/W` | 5 | HIGH | `0x7819, 0x7824, 0x78FC, 0x7914, 0x793A` | yes/test | capture compare write order, flag clear, enable timing, minimum lead time |
| `0x301E` | unclassified hardware access | timer compare / injector scheduler | `R/W` | 5 | HIGH | `0x77E9, 0x77F4, 0x7898, 0x78B0, 0x78D6` | yes/test | capture compare write order, flag clear, enable timing, minimum lead time |
| `0x3020` | unclassified hardware access | timer compare / injector scheduler | `RMW` | 6 | HIGH | `0x77EE, 0x781E, 0x7883, 0x78C5, 0x78E7` | yes/test | capture compare write order, flag clear, enable timing, minimum lead time |
| `0x3021` | unclassified hardware access | HC11 timer/core | `W` | 1 | LOW | `0xCC8F` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3022` | unclassified hardware access | timer compare / injector scheduler | `RMW/W` | 7 | HIGH | `0x7469, 0x77DF, 0x780F, 0x7880, 0x78E4` | yes/test | capture compare write order, flag clear, enable timing, minimum lead time |
| `0x3023` | unclassified hardware access | timer compare / injector scheduler | `R/W` | 14 | HIGH | `0x745B, 0x754D, 0x7597, 0x76E1, 0x772B` | yes/test | capture compare write order, flag clear, enable timing, minimum lead time |
| `0x3024` | unclassified hardware access | boot/watchdog/core CPU | `W` | 2 | HIGH | `0x7113, 0xFC3C` | yes/test | preserve init/watchdog sequence until boot proven |
| `0x3025` | unclassified hardware access | HC11 timer/core | `W` | 1 | LOW | `0xFC41` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3026` | unclassified hardware access | HC11 timer/core | `W` | 1 | LOW | `0xCC93` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3027` | unclassified hardware access | HC11 timer/core | `R` | 2 | LOW | `0xAF78, 0xAF7E` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3028` | unclassified hardware access | HC11 timer/core | `W` | 1 | LOW | `0xCC85` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x302B` | unclassified hardware access | ALDL/SCI | `W` | 1 | HIGH | `0xCC9F` | yes/test | verify SCI setup and debug frame safety |
| `0x302C` | unclassified hardware access | ALDL/SCI | `W` | 1 | HIGH | `0xCC81` | yes/test | verify SCI setup and debug frame safety |
| `0x302D` | unclassified hardware access | ALDL/SCI | `R/W` | 11 | HIGH | `0x7154, 0xF645, 0xF7AF, 0xF7ED, 0xF7FA` | yes/test | verify SCI setup and debug frame safety |
| `0x302E` | unclassified hardware access | ALDL/SCI | `R` | 8 | MEDIUM | `0x7150, 0xF608, 0xF7F1, 0xF7FE, 0xF80B` | yes/test | verify SCI setup and debug frame safety |
| `0x302F` | unclassified hardware access | ALDL/SCI | `R/W` | 5 | HIGH | `0xF60B, 0xF8E6, 0xF902, 0xF90E, 0xFA30` | yes/test | verify SCI setup and debug frame safety |
| `0x3030` | unclassified hardware access | sensor acquisition | `R/W` | 7 | HIGH | `0x7521, 0x7B73, 0x7B79, 0xD171, 0xD176` | yes/test | verify channel select/result order and scaling |
| `0x3031` | unclassified hardware access | sensor acquisition | `R` | 5 | MEDIUM | `0x7528, 0x7B7E, 0xF24C, 0xFA6B, 0xFA7B` | yes/test | verify channel select/result order and scaling |
| `0x3032` | unclassified hardware access | sensor acquisition | `R` | 3 | MEDIUM | `0x7B81, 0xF236, 0xF254` | yes/test | verify channel select/result order and scaling |
| `0x3033` | unclassified hardware access | sensor acquisition | `R` | 3 | MEDIUM | `0x7B86, 0xF23B, 0xF259` | yes/test | verify channel select/result order and scaling |
| `0x3034` | unclassified hardware access | sensor acquisition | `R` | 9 | MEDIUM | `0x7B8B, 0xC57D, 0xC599, 0xCEF1, 0xD184` | yes/test | verify channel select/result order and scaling |
| `0x3035` | unclassified hardware access | HC11 timer/core | `W` | 1 | LOW | `0x711A` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3038` | unclassified hardware access | boot/watchdog/core CPU | `RMW` | 1 | HIGH | `0x7115` | yes/test | preserve init/watchdog sequence until boot proven |
| `0x3039` | unclassified hardware access | boot/watchdog/core CPU | `W` | 2 | HIGH | `0x710F, 0x7D89` | yes/test | preserve init/watchdog sequence until boot proven |
| `0x303A` | unclassified hardware access | boot/watchdog/core CPU | `W` | 10 | HIGH | `0x7443, 0x7448, 0x79EA, 0x79ED, 0x7DB3` | yes/test | preserve init/watchdog sequence until boot proven |
| `0x303C` | unclassified hardware access | HC11 timer/core | `W` | 1 | LOW | `0xCCA3` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x303E` | unclassified hardware access | HC11 timer/core | `W` | 1 | LOW | `0xCC87` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x303F` | unclassified hardware access | boot/watchdog/core CPU | `R` | 1 | MEDIUM | `0x71C6` | yes/test | preserve init/watchdog sequence until boot proven |
| `0x305C` | unclassified hardware access | OTHER | `W` | 1 | LOW | `0xCC89` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x305D` | unclassified hardware access | OTHER | `W` | 1 | LOW | `0xCCA7` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x305E` | unclassified hardware access | OTHER | `W` | 1 | LOW | `0xCCAF` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x305F` | unclassified hardware access | OTHER | `W` | 1 | LOW | `0xCCAB` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3060` | unclassified hardware access | board/ASIC-adjacent unknown | `R/RMW/W` | 6 | HIGH_UNCLASSIFIED | `0xA5D4, 0xAEB7, 0xF400, 0xF409, 0xFB4A` | unknown | bench-probe pins/outputs; classify required/not-required |
| `0x3061` | unclassified hardware access | board/ASIC-adjacent unknown | `W` | 1 | HIGH_UNCLASSIFIED | `0xCCB3` | unknown | bench-probe pins/outputs; classify required/not-required |
| `0x3062` | unclassified hardware access | spark or EST handoff | `R/RMW/W` | 10 | HIGH | `0x7509, 0x750C, 0xAEBA, 0xF411, 0xFB14` | yes/test | trace value units vs spark/RPM and EST/bypass latch timing |
| `0x3063` | unclassified hardware access | board/ASIC-adjacent unknown | `W` | 1 | HIGH_UNCLASSIFIED | `0xCCB8` | unknown | bench-probe pins/outputs; classify required/not-required |
| `0x3064` | unclassified hardware access | board/ASIC-adjacent unknown | `R` | 2 | HIGH_UNCLASSIFIED | `0xF414, 0xFAD4` | unknown | bench-probe pins/outputs; classify required/not-required |
| `0x3065` | unclassified hardware access | board/ASIC-adjacent unknown | `W` | 1 | HIGH_UNCLASSIFIED | `0xCCBD` | unknown | bench-probe pins/outputs; classify required/not-required |
| `0x3067` | unclassified hardware access | board/ASIC-adjacent unknown | `W` | 1 | HIGH_UNCLASSIFIED | `0xF41B` | unknown | bench-probe pins/outputs; classify required/not-required |
| `0x3068` | unclassified hardware access | output latch | `W` | 3 | HIGH | `0x7BA3, 0xFB93, 0xFBCB` | yes/test | probe physical output effect and latch/update order |
| `0x306A` | unclassified hardware access | board/ASIC-adjacent unknown | `W` | 4 | HIGH_UNCLASSIFIED | `0xC56B, 0xCDF3, 0xFB8A, 0xFBB9` | unknown | bench-probe pins/outputs; classify required/not-required |
| `0x306C` | unclassified hardware access | board/ASIC-adjacent unknown | `W` | 4 | HIGH_UNCLASSIFIED | `0x9163, 0xCDDF, 0xFB8D, 0xFBBF` | unknown | bench-probe pins/outputs; classify required/not-required |
| `0x306E` | unclassified hardware access | output latch | `W` | 3 | HIGH | `0x7128, 0xFB90, 0xFBC5` | yes/test | probe physical output effect and latch/update order |
| `0x306F` | unclassified hardware access | output latch | `W` | 2 | HIGH | `0x7518, 0xA5AA` | yes/test | probe physical output effect and latch/update order |
| `0x3FC0` | unclassified hardware access | ASIC/ref/status read | `R` | 8 | MEDIUM | `0x842C, 0x858B, 0xA551, 0xA581, 0xA5E5` | yes/test | trace read cadence, bit meanings, read-clear side effects |
| `0x3FC4` | unclassified hardware access | ASIC/ref/status read | `R` | 1 | MEDIUM | `0x7C00` | yes/test | trace read cadence, bit meanings, read-clear side effects |
| `0x3FC6` | unclassified hardware access | ASIC/ref/status read | `R` | 2 | MEDIUM | `0xAFC5, 0xAFD2` | yes/test | trace read cadence, bit meanings, read-clear side effects |
| `0x3FC8` | unclassified hardware access | ASIC/ref/status read | `R` | 1 | MEDIUM | `0xCE81` | yes/test | trace read cadence, bit meanings, read-clear side effects |
| `0x3FCA` | unclassified hardware access | ASIC/ref/status read | `R` | 4 | MEDIUM | `0x741F, 0x8629, 0xABD3, 0xE01E` | yes/test | trace read cadence, bit meanings, read-clear side effects |
| `0x3FCC` | unclassified hardware access | ASIC command/output write | `W` | 2 | HIGH | `0x74D6, 0xFADC` | yes/test | probe physical output effect and latch/update order |
| `0x3FCE` | unclassified hardware access | ASIC command/output write | `W` | 4 | HIGH | `0x8426, 0x8512, 0xFAEE, 0xFB44` | yes/test | probe physical output effect and latch/update order |
| `0x3FD4` | unclassified hardware access | ASIC command/output write | `W` | 3 | HIGH | `0xCDCB, 0xFB78, 0xFB9B` | yes/test | probe physical output effect and latch/update order |
| `0x3FD6` | unclassified hardware access | ASIC command/output write | `W` | 3 | HIGH | `0xCD8D, 0xFB7D, 0xFBA3` | yes/test | probe physical output effect and latch/update order |
| `0x3FD8` | unclassified hardware access | ASIC command/output write | `W` | 3 | HIGH | `0xCE0C, 0xFB82, 0xFBAB` | yes/test | probe physical output effect and latch/update order |
| `0x3FDA` | unclassified hardware access | ASIC command/output write | `W` | 3 | HIGH | `0xCD71, 0xFB87, 0xFBB3` | yes/test | probe physical output effect and latch/update order |
| `0x3FDC` | unclassified hardware access | spark or EST handoff | `R/W` | 3 | HIGH | `0xABB0, 0xABC0, 0xFAF7` | yes/test | trace value units vs spark/RPM and EST/bypass latch timing |
| `0x3FE0` | unclassified hardware access | ASIC unknown | `R` | 1 | HIGH_UNCLASSIFIED | `0xACD3` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3FE4` | unclassified hardware access | spark or EST handoff | `W` | 1 | HIGH | `0xAC2E` | yes/test | trace value units vs spark/RPM and EST/bypass latch timing |
| `0x3FE6` | unclassified hardware access | spark or EST handoff | `W` | 1 | HIGH | `0xABBA` | yes/test | trace value units vs spark/RPM and EST/bypass latch timing |
| `0x3FE8` | unclassified hardware access | spark or EST handoff | `W` | 1 | HIGH | `0xABAA` | yes/test | trace value units vs spark/RPM and EST/bypass latch timing |
| `0x3FEA` | unclassified hardware access | fuel handoff | `W` | 2 | LOW | `0x74DF, 0xFAE5` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3FEC` | unclassified hardware access | ASIC/ref/status read | `R` | 1 | MEDIUM | `0xAC28` | yes/test | trace read cadence, bit meanings, read-clear side effects |
| `0x3FF2` | unclassified hardware access | ASIC unknown | `W` | 1 | HIGH_UNCLASSIFIED | `0x8571` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3FF6` | unclassified hardware access | spark or EST handoff | `R/W` | 4 | HIGH | `0xAB97, 0xABA4, 0xABC8, 0xFB03` | yes/test | trace value units vs spark/RPM and EST/bypass latch timing |
| `0x3FF8` | unclassified hardware access | ASIC unknown | `R` | 1 | HIGH_UNCLASSIFIED | `0xAFCC` | unknown | trace across key-on/crank/idle/snap/decel |
| `0x3FFA` | unclassified hardware access | ASIC/ref/status read | `R` | 2 | MEDIUM | `0x7765, 0x7BF6` | yes/test | trace read cadence, bit meanings, read-clear side effects |
| `0x3FFC` | unclassified hardware access | output latch | `R/W` | 23 | HIGH | `0x713A, 0x7140, 0x714A, 0x71BD, 0x71EF` | yes/test | probe physical output effect and latch/update order |
| `0x3FC0-0x3FF8` | unclassified hardware access | OTHER | `W` | 1 | LOW | `0x715B` | unknown | trace across key-on/crank/idle/snap/decel |
| `0,X` | unclassified hardware access | OTHER | `EXEC/R/RMW/W` | 166 | HIGH | `0x7501, 0x784C, 0x7A4D, 0x7A4F, 0x7A72` | yes/test | trace across key-on/crank/idle/snap/decel |
| `$20,X,#$03` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0x75CB` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0B,X,#$08` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0x75CE` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0E,X` | unclassified hardware access | OTHER | `R` | 4 | LOW | `0x75DD, 0x75E5, 0x7610, 0x7618` | unknown | trace across key-on/crank/idle/snap/decel |
| `$20,X,#$01` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0x75E2` | unknown | trace across key-on/crank/idle/snap/decel |
| `$1E,X` | unclassified hardware access | OTHER | `W` | 1 | LOW | `0x75F3` | unknown | trace across key-on/crank/idle/snap/decel |
| `$23,X` | unclassified hardware access | OTHER | `W` | 1 | LOW | `0x75F9` | unknown | trace across key-on/crank/idle/snap/decel |
| `$20,X,#$0C` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0x75FE` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0B,X,#$10` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0x7601` | unknown | trace across key-on/crank/idle/snap/decel |
| `$20,X,#$04` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0x7615` | unknown | trace across key-on/crank/idle/snap/decel |
| `$1C,X` | unclassified hardware access | OTHER | `W` | 1 | LOW | `0x7626` | unknown | trace across key-on/crank/idle/snap/decel |
| `1,X` | unclassified hardware access | OTHER | `R` | 8 | LOW | `0x8CEB, 0x8D21, 0xD963, 0xF468, 0xF4AB` | unknown | trace across key-on/crank/idle/snap/decel |
| `2,X` | unclassified hardware access | OTHER | `R/W` | 10 | LOW | `0x9B1F, 0x9B9C, 0xD7FF, 0xF318, 0xF464` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0005,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0x9B25` | unknown | trace across key-on/crank/idle/snap/decel |
| `6,X` | unclassified hardware access | OTHER | `R/RMW/W` | 7 | LOW | `0x9B2C, 0x9C09, 0xB433, 0xBC47, 0xF31E` | unknown | trace across key-on/crank/idle/snap/decel |
| `8,X` | unclassified hardware access | OTHER | `R` | 3 | LOW | `0x9B2E, 0x9C0E, 0xAD58` | unknown | trace across key-on/crank/idle/snap/decel |
| `5,X` | unclassified hardware access | OTHER | `R/W` | 3 | LOW | `0x9B96, 0xF56F, 0xF574` | unknown | trace across key-on/crank/idle/snap/decel |
| `3,X` | unclassified hardware access | OTHER | `R/W` | 4 | LOW | `0x9C00, 0xD803, 0xF56A, 0xF57C` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0002,X` | unclassified hardware access | OTHER | `R/W` | 3 | LOW | `0xA239, 0xD863, 0xD913` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0003,X` | unclassified hardware access | OTHER | `R/W` | 4 | LOW | `0xA23D, 0xBAC1, 0xBB2B, 0xD90F` | unknown | trace across key-on/crank/idle/snap/decel |
| `$04,X` | unclassified hardware access | OTHER | `R/RMW/W` | 9 | LOW | `0xAD54, 0xB983, 0xB98F, 0xF585, 0xF59A` | unknown | trace across key-on/crank/idle/snap/decel |
| `0,Y` | unclassified hardware access | OTHER | `R/W` | 3 | LOW | `0xAFDC, 0xB9D5, 0xF627` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0008,X` | unclassified hardware access | OTHER | `EXEC/R` | 7 | LOW | `0xB313, 0xBB09, 0xC2F7, 0xC3A8, 0xC3B0` | unknown | trace across key-on/crank/idle/snap/decel |
| `$001C,X,#$18,LB340` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xB327` | unknown | trace across key-on/crank/idle/snap/decel |
| `$EF,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xB4CC` | unknown | trace across key-on/crank/idle/snap/decel |
| `$16,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xB4D5` | unknown | trace across key-on/crank/idle/snap/decel |
| `$03,X` | unclassified hardware access | OTHER | `R/RMW` | 11 | LOW | `0xB4DD, 0xF509, 0xF51B, 0xF51F, 0xF531` | unknown | trace across key-on/crank/idle/snap/decel |
| `$06,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xB4E1` | unknown | trace across key-on/crank/idle/snap/decel |
| `$000A,X` | unclassified hardware access | OTHER | `R` | 2 | LOW | `0xB53D, 0xC757` | unknown | trace across key-on/crank/idle/snap/decel |
| `$000D,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xB545` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0010,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xB553` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00FB,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xB965` | unknown | trace across key-on/crank/idle/snap/decel |
| `$66,X,#$43,LB9D6` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xB96C` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0065,X` | unclassified hardware access | OTHER | `RMW` | 2 | LOW | `0xB971, 0xBE51` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0076,X` | unclassified hardware access | OTHER | `RMW` | 2 | LOW | `0xB973, 0xBE53` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0087,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xB975` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0098,X` | unclassified hardware access | OTHER | `RMW` | 2 | LOW | `0xB977, 0xBE37` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00A9,X` | unclassified hardware access | OTHER | `RMW` | 2 | LOW | `0xB979, 0xBE39` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00BA,X` | unclassified hardware access | OTHER | `RMW` | 2 | LOW | `0xB97B, 0xBE3B` | unknown | trace across key-on/crank/idle/snap/decel |
| `$CB,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xB97D` | unknown | trace across key-on/crank/idle/snap/decel |
| `$DC,X` | unclassified hardware access | OTHER | `RMW` | 2 | LOW | `0xB97F, 0xB98B` | unknown | trace across key-on/crank/idle/snap/decel |
| `$F0,X` | unclassified hardware access | OTHER | `RMW` | 2 | LOW | `0xB981, 0xB98D` | unknown | trace across key-on/crank/idle/snap/decel |
| `$18,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xB985` | unknown | trace across key-on/crank/idle/snap/decel |
| `$2C,X` | unclassified hardware access | OTHER | `RMW` | 2 | LOW | `0xB987, 0xBC73` | unknown | trace across key-on/crank/idle/snap/decel |
| `$40,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xB989` | unknown | trace across key-on/crank/idle/snap/decel |
| `$005F,X` | unclassified hardware access | OTHER | `RMW` | 3 | LOW | `0xB99C, 0xBC6D, 0xC2DE` | unknown | trace across key-on/crank/idle/snap/decel |
| `$81,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBA32` | unknown | trace across key-on/crank/idle/snap/decel |
| `$92,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBA34` | unknown | trace across key-on/crank/idle/snap/decel |
| `$A3,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBA36` | unknown | trace across key-on/crank/idle/snap/decel |
| `$000E,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xBAF5` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0B,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xBB1E` | unknown | trace across key-on/crank/idle/snap/decel |
| `$E3,X` | unclassified hardware access | OTHER | `RMW` | 2 | LOW | `0xBC3B, 0xBC5F` | unknown | trace across key-on/crank/idle/snap/decel |
| `$F4,X` | unclassified hardware access | OTHER | `RMW` | 2 | LOW | `0xBC3D, 0xBC61` | unknown | trace across key-on/crank/idle/snap/decel |
| `$05,X` | unclassified hardware access | OTHER | `R/RMW/W` | 7 | LOW | `0xBC3F, 0xBC63, 0xF5AB, 0xF5B0, 0xF61F` | unknown | trace across key-on/crank/idle/snap/decel |
| `$D3,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBC41` | unknown | trace across key-on/crank/idle/snap/decel |
| `$E4,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBC43` | unknown | trace across key-on/crank/idle/snap/decel |
| `$F5,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBC45` | unknown | trace across key-on/crank/idle/snap/decel |
| `$17,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBC49` | unknown | trace across key-on/crank/idle/snap/decel |
| `$28,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBC4B` | unknown | trace across key-on/crank/idle/snap/decel |
| `$39,X` | unclassified hardware access | OTHER | `RMW` | 2 | LOW | `0xBC4D, 0xF3EB` | unknown | trace across key-on/crank/idle/snap/decel |
| `$4A,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBC4F` | unknown | trace across key-on/crank/idle/snap/decel |
| `$5B,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBC51` | unknown | trace across key-on/crank/idle/snap/decel |
| `$6C,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBC53` | unknown | trace across key-on/crank/idle/snap/decel |
| `$7D,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBC55` | unknown | trace across key-on/crank/idle/snap/decel |
| `$8E,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBC57` | unknown | trace across key-on/crank/idle/snap/decel |
| `$B0,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBC59` | unknown | trace across key-on/crank/idle/snap/decel |
| `$C1,X` | unclassified hardware access | OTHER | `R/RMW` | 2 | LOW | `0xBC5B, 0xF1E8` | unknown | trace across key-on/crank/idle/snap/decel |
| `$D2,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBC5D` | unknown | trace across key-on/crank/idle/snap/decel |
| `$004E,X` | unclassified hardware access | OTHER | `RMW` | 2 | LOW | `0xBC6B, 0xC2DC` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0070,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBC6F` | unknown | trace across key-on/crank/idle/snap/decel |
| `$001B,X` | unclassified hardware access | OTHER | `RMW` | 2 | LOW | `0xBC71, 0xC2E4` | unknown | trace across key-on/crank/idle/snap/decel |
| `$3D,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBC75` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00CB,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBE3D` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00DC,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBE3F` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00ED,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBE41` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00FE,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBE43` | unknown | trace across key-on/crank/idle/snap/decel |
| `$000F,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBE45` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0020,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBE47` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0031,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBE49` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0042,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBE4B` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0053,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBE4D` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0054,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBE4F` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0075,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBE55` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0086,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBE57` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0097,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xBE59` | unknown | trace across key-on/crank/idle/snap/decel |
| `$003D,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC2DA` | unknown | trace across key-on/crank/idle/snap/decel |
| `$002C,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC2E6` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00F4,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC2FC` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00F5,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC2FE` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00F6,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC300` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00EE,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC314` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00EF,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC316` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00F0,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC318` | unknown | trace across key-on/crank/idle/snap/decel |
| `$006B,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xC329` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00FA,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC336` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0008,X,#$08` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC33B` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00F7,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC340` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00F8,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC342` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00F9,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC344` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00F1,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC358` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00F2,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC35A` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00F3,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xC35C` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00B3,X` | unclassified hardware access | OTHER | `R` | 4 | LOW | `0xC364, 0xC36C, 0xC374, 0xC37C` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00C4,X` | unclassified hardware access | OTHER | `R` | 5 | LOW | `0xC366, 0xC36E, 0xC376, 0xC37E, 0xF18F` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00C5,X` | unclassified hardware access | OTHER | `RMW` | 4 | LOW | `0xC386, 0xC38E, 0xC396, 0xC39E` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00D6,X` | unclassified hardware access | OTHER | `RMW` | 4 | LOW | `0xC388, 0xC390, 0xC398, 0xC3A0` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0019,X` | unclassified hardware access | OTHER | `EXEC` | 4 | LOW | `0xC3AA, 0xC3B2, 0xC3BA, 0xC3C2` | unknown | trace across key-on/crank/idle/snap/decel |
| `$001A,X` | unclassified hardware access | OTHER | `R` | 4 | LOW | `0xC3CA, 0xC3D2, 0xC3DA, 0xC3E2` | unknown | trace across key-on/crank/idle/snap/decel |
| `$002B,X` | unclassified hardware access | OTHER | `R` | 4 | LOW | `0xC3CC, 0xC3D4, 0xC3DC, 0xC3E4` | unknown | trace across key-on/crank/idle/snap/decel |
| `$07,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xC751` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0001,X` | unclassified hardware access | OTHER | `R/W` | 4 | LOW | `0xD81E, 0xD872, 0xD903, 0xD99D` | unknown | trace across key-on/crank/idle/snap/decel |
| `$00C7,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xF19B` | unknown | trace across key-on/crank/idle/snap/decel |
| `$C5,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xF1AA` | unknown | trace across key-on/crank/idle/snap/decel |
| `$C8,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xF1B6` | unknown | trace across key-on/crank/idle/snap/decel |
| `$C6,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xF1C5` | unknown | trace across key-on/crank/idle/snap/decel |
| `$C9,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xF1D1` | unknown | trace across key-on/crank/idle/snap/decel |
| `$C2,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xF1F7` | unknown | trace across key-on/crank/idle/snap/decel |
| `$C3,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xF20A` | unknown | trace across key-on/crank/idle/snap/decel |
| `4,X` | unclassified hardware access | OTHER | `R/W` | 6 | LOW | `0xF31B, 0xF578, 0xF581, 0xF58C, 0xF590` | unknown | trace across key-on/crank/idle/snap/decel |
| `$08,X` | unclassified hardware access | OTHER | `RMW` | 1 | LOW | `0xF3E6` | unknown | trace across key-on/crank/idle/snap/decel |
| `$01,X` | unclassified hardware access | OTHER | `R` | 3 | LOW | `0xF4E7, 0xF5AD, 0xFB59` | unknown | trace across key-on/crank/idle/snap/decel |
| `$02,Y` | unclassified hardware access | OTHER | `R` | 3 | LOW | `0xF4FD, 0xF503, 0xF536` | unknown | trace across key-on/crank/idle/snap/decel |
| `$03,Y` | unclassified hardware access | OTHER | `R` | 2 | LOW | `0xF50C, 0xF522` | unknown | trace across key-on/crank/idle/snap/decel |
| `$01,Y` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xF546` | unknown | trace across key-on/crank/idle/snap/decel |
| `$02,X` | unclassified hardware access | OTHER | `R` | 3 | LOW | `0xF5C5, 0xF9BE, 0xFA2E` | unknown | trace across key-on/crank/idle/snap/decel |
| `$09,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xF623` | unknown | trace across key-on/crank/idle/snap/decel |
| `$03,X,#$80,LF881` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xF872` | unknown | trace across key-on/crank/idle/snap/decel |
| `$03,X,#$40,LF88C` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xF876` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0009,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xF888` | unknown | trace across key-on/crank/idle/snap/decel |
| `9,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xF97B` | unknown | trace across key-on/crank/idle/snap/decel |
| `7,X` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xF9AB` | unknown | trace across key-on/crank/idle/snap/decel |
| `$0004,X,#$80,LFA4D` | unclassified hardware access | OTHER | `R` | 1 | LOW | `0xFA24` | unknown | trace across key-on/crank/idle/snap/decel |
