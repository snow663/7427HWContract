# Hardware test candidate matrix

This source-listing view contains 244 grouped candidate rows from `maps/full/hardware_access_map_v0.3.csv`.
It is an investigation index, not a list of measured hardware behaviors.

Current ROM-backed access and physical-interface authority:
[hardware boundaries](../../docs/analysis/FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md) and
[qualified access map](../structure/factory_global_hardware_accesses.csv).

Stock BMHM leaves OC4/5 locally disabled; their source paths remain relevant to other configurations.
Do not interpret a source-group label as proof that a timer drives a particular physical output.

| Address | Class | Subsystem | Source rows | Investigation objective |
|---|---|---|---:|---|
| $0001,X | UNKNOWN_HW | OTHER | 4 | Classify hardware effect and minimal-OS requirement. |
| $0002,X | UNKNOWN_HW | OTHER | 2 | Classify hardware effect and minimal-OS requirement. |
| $0003,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $0004,X,#$80,LFA4D | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $0009,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $001B,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $004E,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $005F,X | UNKNOWN_HW | OTHER | 2 | Classify hardware effect and minimal-OS requirement. |
| $0065,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $0070,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $0076,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $0087,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $0098,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $00A9,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $00BA,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $00C4,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $00C7,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $00FB,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $02,X | UNKNOWN_HW | OTHER | 2 | Classify hardware effect and minimal-OS requirement. |
| $03,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $03,X,#$40,LF88C | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $03,X,#$80,LF881 | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $04,X | UNKNOWN_HW | OTHER | 4 | Classify hardware effect and minimal-OS requirement. |
| $05,X | UNKNOWN_HW | OTHER | 5 | Classify hardware effect and minimal-OS requirement. |
| $09,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $17,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $18,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $28,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $2C,X | UNKNOWN_HW | OTHER | 2 | Classify hardware effect and minimal-OS requirement. |
| $39,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $3D,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $40,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $4A,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $5B,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $66,X,#$43,LB9D6 | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $6C,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $7D,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $81,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $8E,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $92,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $A3,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $B0,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $C1,X | UNKNOWN_HW | OTHER | 2 | Classify hardware effect and minimal-OS requirement. |
| $C2,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $C3,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $C5,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $C6,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $C8,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $C9,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $CB,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $D2,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $D3,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $DC,X | UNKNOWN_HW | OTHER | 2 | Classify hardware effect and minimal-OS requirement. |
| $E3,X | UNKNOWN_HW | OTHER | 2 | Classify hardware effect and minimal-OS requirement. |
| $E4,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| $F0,X | UNKNOWN_HW | OTHER | 2 | Classify hardware effect and minimal-OS requirement. |
| $F4,X | UNKNOWN_HW | OTHER | 2 | Classify hardware effect and minimal-OS requirement. |
| $F5,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| 0,X | UNKNOWN_HW | OTHER | 59 | Classify hardware effect and minimal-OS requirement. |
| 0,X | UNKNOWN_HW | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0,Y | UNKNOWN_HW | OTHER | 3 | Classify hardware effect and minimal-OS requirement. |
| 0x0004 | DIRECT_RAM | SPARK_EST | 7 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x0009 | DIRECT_RAM | SPARK_EST | 5 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x0019 | DIRECT_RAM | SPARK_EST | 3 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x0037 | DIRECT_RAM | SPARK_EST | 4 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x003E | DIRECT_RAM | FUEL_MATH_HANDOFF | 4 | Classify hardware effect and minimal-OS requirement. |
| 0x003F | DIRECT_RAM | FUEL_MATH_HANDOFF | 2 | Classify hardware effect and minimal-OS requirement. |
| 0x0044 | DIRECT_RAM | SPARK_EST | 16 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x0046 | DIRECT_RAM | FUEL_MATH_HANDOFF | 19 | Classify hardware effect and minimal-OS requirement. |
| 0x004D | DIRECT_RAM | SPARK_EST | 3 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x004F | DIRECT_RAM | FUEL_MATH_HANDOFF | 12 | Classify hardware effect and minimal-OS requirement. |
| 0x004F | DIRECT_RAM | SPARK_EST | 4 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x0050 | DIRECT_RAM | SPARK_EST | 2 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x0052 | DIRECT_RAM | SPARK_EST | 3 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x0053 | DIRECT_RAM | FUEL_MATH_HANDOFF | 3 | Classify hardware effect and minimal-OS requirement. |
| 0x006E | DIRECT_RAM | SPARK_EST | 4 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x009F | DIRECT_RAM | SPARK_EST | 7 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x0136 | DIRECT_RAM | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x0137 | DIRECT_RAM | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x01EE | DIRECT_RAM | SPARK_EST | 12 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x01F2 | DIRECT_RAM | SPARK_EST | 7 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x01F4 | DIRECT_RAM | SPARK_EST | 2 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x01FC | DIRECT_RAM | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x020C | DIRECT_RAM | SPARK_EST | 7 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x0221 | DIRECT_RAM | SPARK_EST | 3 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x0225 | DIRECT_RAM | SPARK_EST | 2 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x022C | DIRECT_RAM | SPARK_EST | 2 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x023A | DIRECT_RAM | FUEL_MATH_HANDOFF | 2 | Classify hardware effect and minimal-OS requirement. |
| 0x0243 | DIRECT_RAM | FUEL_MATH_HANDOFF | 2 | Classify hardware effect and minimal-OS requirement. |
| 0x0244 | DIRECT_RAM | FUEL_MATH_HANDOFF | 3 | Classify hardware effect and minimal-OS requirement. |
| 0x024C | DIRECT_RAM | FUEL_MATH_HANDOFF | 6 | Classify hardware effect and minimal-OS requirement. |
| 0x024E | DIRECT_RAM | FUEL_MATH_HANDOFF | 22 | Classify hardware effect and minimal-OS requirement. |
| 0x0250 | DIRECT_RAM | FUEL_MATH_HANDOFF | 10 | Classify hardware effect and minimal-OS requirement. |
| 0x0254 | DIRECT_RAM | FUEL_MATH_HANDOFF | 7 | Classify hardware effect and minimal-OS requirement. |
| 0x0256 | DIRECT_RAM | FUEL_MATH_HANDOFF | 5 | Classify hardware effect and minimal-OS requirement. |
| 0x0260 | DIRECT_RAM | FUEL_MATH_HANDOFF | 3 | Classify hardware effect and minimal-OS requirement. |
| 0x026A | DIRECT_RAM | FUEL_MATH_HANDOFF | 3 | Classify hardware effect and minimal-OS requirement. |
| 0x027A | DIRECT_RAM | FUEL_MATH_HANDOFF | 4 | Classify hardware effect and minimal-OS requirement. |
| 0x02CF | DIRECT_RAM | FUEL_MATH_HANDOFF | 3 | Classify hardware effect and minimal-OS requirement. |
| 0x0827 | EXT_RAM | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x0843 | EXT_RAM | SPARK_EST | 2 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x0844 | EXT_RAM | SPARK_EST | 3 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x103D | HC11_REG | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x3000 | HC11_REG | BOOT_WATCHDOG_CPU | 6 | Classify hardware effect and minimal-OS requirement. |
| 0x3001 | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x3002 | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x3003 | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x3008 | HC11_REG | SENSOR_ADC | 8 | Classify hardware effect and minimal-OS requirement. |
| 0x3009 | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x300B | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x300C | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x300D | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x300E | HC11_REG | HC11_CORE | 9 | Classify hardware effect and minimal-OS requirement. |
| 0x3010 | HC11_REG | HC11_CORE | 2 | Classify hardware effect and minimal-OS requirement. |
| 0x3012 | HC11_REG | HC11_CORE | 2 | Classify hardware effect and minimal-OS requirement. |
| 0x3016 | HC11_REG | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x301A | HC11_REG | HC11_CORE | 4 | Classify hardware effect and minimal-OS requirement. |
| 0x301C | HC11_REG | FUEL_SCHED_TIMER | 5 | Classify whether HC11 timer compare path is still required when $3FCE is driven. |
| 0x301E | HC11_REG | FUEL_SCHED_TIMER | 5 | Classify whether HC11 timer compare path is still required when $3FCE is driven. |
| 0x3020 | HC11_REG | FUEL_SCHED_TIMER | 6 | Classify whether HC11 timer compare path is still required when $3FCE is driven. |
| 0x3021 | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x3022 | HC11_REG | FUEL_SCHED_TIMER | 7 | Classify whether HC11 timer compare path is still required when $3FCE is driven. |
| 0x3023 | HC11_REG | FUEL_SCHED_TIMER | 14 | Classify whether HC11 timer compare path is still required when $3FCE is driven. |
| 0x3024 | HC11_REG | BOOT_WATCHDOG_CPU | 2 | Classify hardware effect and minimal-OS requirement. |
| 0x3025 | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x3026 | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x3027 | HC11_REG | HC11_CORE | 2 | Classify hardware effect and minimal-OS requirement. |
| 0x3028 | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x302B | ALDL | ALDL_SCI | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x302C | ALDL | ALDL_SCI | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x302D | ALDL | ALDL_SCI | 11 | Classify hardware effect and minimal-OS requirement. |
| 0x302E | ALDL | ALDL_SCI | 8 | Classify hardware effect and minimal-OS requirement. |
| 0x302F | ALDL | ALDL_SCI | 5 | Classify hardware effect and minimal-OS requirement. |
| 0x3030 | HC11_REG | SENSOR_ADC | 7 | Classify hardware effect and minimal-OS requirement. |
| 0x3031 | HC11_REG | SENSOR_ADC | 5 | Classify hardware effect and minimal-OS requirement. |
| 0x3032 | HC11_REG | SENSOR_ADC | 3 | Classify hardware effect and minimal-OS requirement. |
| 0x3033 | HC11_REG | SENSOR_ADC | 3 | Classify hardware effect and minimal-OS requirement. |
| 0x3034 | HC11_REG | SENSOR_ADC | 9 | Classify hardware effect and minimal-OS requirement. |
| 0x3035 | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x3038 | HC11_REG | BOOT_WATCHDOG_CPU | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x3039 | HC11_REG | BOOT_WATCHDOG_CPU | 2 | Classify hardware effect and minimal-OS requirement. |
| 0x303A | HC11_REG | BOOT_WATCHDOG_CPU | 10 | Classify hardware effect and minimal-OS requirement. |
| 0x303C | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x303E | HC11_REG | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x303F | HC11_REG | BOOT_WATCHDOG_CPU | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x305C | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x305D | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x305E | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x305F | HC11_REG | HC11_CORE | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x3060 | UNKNOWN_HW | UNKNOWN_306X_BOARD_IO | 6 | Classify board/ASIC-adjacent unknown as required or removable. |
| 0x3061 | UNKNOWN_HW | UNKNOWN_306X_BOARD_IO | 1 | Classify board/ASIC-adjacent unknown as required or removable. |
| 0x3062 | UNKNOWN_HW | SPARK_EST | 10 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x3063 | UNKNOWN_HW | UNKNOWN_306X_BOARD_IO | 1 | Classify board/ASIC-adjacent unknown as required or removable. |
| 0x3064 | UNKNOWN_HW | UNKNOWN_306X_BOARD_IO | 2 | Classify board/ASIC-adjacent unknown as required or removable. |
| 0x3065 | UNKNOWN_HW | UNKNOWN_306X_BOARD_IO | 1 | Classify board/ASIC-adjacent unknown as required or removable. |
| 0x3067 | UNKNOWN_HW | UNKNOWN_306X_BOARD_IO | 1 | Classify board/ASIC-adjacent unknown as required or removable. |
| 0x3068 | UNKNOWN_HW | IO_LATCH_OUTPUT | 3 | Map output latch bits to physical outputs and safe states. |
| 0x306A | UNKNOWN_HW | UNKNOWN_306X_BOARD_IO | 4 | Classify board/ASIC-adjacent unknown as required or removable. |
| 0x306C | UNKNOWN_HW | UNKNOWN_306X_BOARD_IO | 4 | Classify board/ASIC-adjacent unknown as required or removable. |
| 0x306E | UNKNOWN_HW | IO_LATCH_OUTPUT | 3 | Map output latch bits to physical outputs and safe states. |
| 0x306F | UNKNOWN_HW | IO_LATCH_OUTPUT | 2 | Map output latch bits to physical outputs and safe states. |
| 0x3FC0 | ASIC_3FXX | ASIC_STATUS_REF | 8 | Decode status/ref/RPM timing bits and read side effects. |
| 0x3FC0-0x3FF8 | ASIC_3FXX | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x3FC4 | ASIC_3FXX | ASIC_STATUS_REF | 1 | Decode status/ref/RPM timing bits and read side effects. |
| 0x3FC6 | ASIC_3FXX | ASIC_STATUS_REF | 2 | Decode status/ref/RPM timing bits and read side effects. |
| 0x3FC8 | ASIC_3FXX | ASIC_STATUS_REF | 1 | Decode status/ref/RPM timing bits and read side effects. |
| 0x3FCA | ASIC_3FXX | ASIC_STATUS_REF | 4 | Decode status/ref/RPM timing bits and read side effects. |
| 0x3FCC | ASIC_3FXX | ASIC_COMMAND_OUTPUT | 2 | Classify hardware effect and minimal-OS requirement. |
| 0x3FCE | ASIC_3FXX | ASIC_COMMAND_OUTPUT | 4 | Prove EFI pulsewidth handoff units and zero/no-fuel behavior. |
| 0x3FD4 | ASIC_3FXX | ASIC_COMMAND_OUTPUT | 3 | Classify hardware effect and minimal-OS requirement. |
| 0x3FD6 | ASIC_3FXX | ASIC_COMMAND_OUTPUT | 3 | Classify hardware effect and minimal-OS requirement. |
| 0x3FD8 | ASIC_3FXX | ASIC_COMMAND_OUTPUT | 3 | Classify hardware effect and minimal-OS requirement. |
| 0x3FDA | ASIC_3FXX | ASIC_COMMAND_OUTPUT | 3 | Classify hardware effect and minimal-OS requirement. |
| 0x3FDC | ASIC_3FXX | SPARK_EST | 3 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x3FE0 | ASIC_3FXX | ASIC_UNKNOWN | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x3FE4 | ASIC_3FXX | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x3FE6 | ASIC_3FXX | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x3FE8 | ASIC_3FXX | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x3FEA | ASIC_3FXX | ASIC_COMMAND_OUTPUT | 2 | Classify hardware effect and minimal-OS requirement. |
| 0x3FEC | ASIC_3FXX | ASIC_STATUS_REF | 1 | Decode status/ref/RPM timing bits and read side effects. |
| 0x3FF2 | ASIC_3FXX | ASIC_UNKNOWN | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x3FF6 | ASIC_3FXX | SPARK_EST | 4 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x3FF8 | ASIC_3FXX | ASIC_UNKNOWN | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x3FFA | ASIC_3FXX | ASIC_STATUS_REF | 2 | Decode status/ref/RPM timing bits and read side effects. |
| 0x3FFC | ASIC_3FXX | IO_LATCH_OUTPUT | 23 | Map output latch bits to physical outputs and safe states. |
| 0x400B | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x400C | ROM_TABLE | FUEL_MATH_HANDOFF | 2 | Classify hardware effect and minimal-OS requirement. |
| 0x400D | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x4135 | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x4143 | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x4148 | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x414A | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x414C | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x4519 | ROM_TABLE | FUEL_MATH_HANDOFF | 2 | Classify hardware effect and minimal-OS requirement. |
| 0x45B9 | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x45BA | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x485E | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x48C6 | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x48D8 | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x48DA | ROM_TABLE | FUEL_MATH_HANDOFF | 6 | Classify hardware effect and minimal-OS requirement. |
| 0x492A | ROM_TABLE | FUEL_MATH_HANDOFF | 3 | Classify hardware effect and minimal-OS requirement. |
| 0x492C | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x4932 | ROM_TABLE | FUEL_MATH_HANDOFF | 3 | Classify hardware effect and minimal-OS requirement. |
| 0x493A | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x493C | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x493D | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x493E | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x4942 | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x4943 | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x4944 | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x4945 | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x4946 | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x4947 | ROM_TABLE | SPARK_EST | 2 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x495B | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x495D | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x4960 | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x4962 | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x4965 | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x4966 | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x496D | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x496F | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x4971 | ROM_TABLE | FUEL_MATH_HANDOFF | 2 | Classify hardware effect and minimal-OS requirement. |
| 0x4973 | ROM_TABLE | FUEL_MATH_HANDOFF | 1 | Classify hardware effect and minimal-OS requirement. |
| 0x4E51 | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x4E55 | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x4E5D | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x4E72 | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x4E73 | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x4F8E | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x4F8F | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x5156 | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x5158 | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x5159 | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0x5B03 | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 0xDF3D | ROM_TABLE | SPARK_EST | 1 | Prove spark/EST handoff units, latch timing, and bypass/run behavior. |
| 1,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| 2,X | UNKNOWN_HW | OTHER | 3 | Classify hardware effect and minimal-OS requirement. |
| 3,X | UNKNOWN_HW | OTHER | 2 | Classify hardware effect and minimal-OS requirement. |
| 4,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| 5,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| 6,X | UNKNOWN_HW | OTHER | 2 | Classify hardware effect and minimal-OS requirement. |
| 7,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
| 8,X | UNKNOWN_HW | OTHER | 2 | Classify hardware effect and minimal-OS requirement. |
| 9,X | UNKNOWN_HW | OTHER | 1 | Classify hardware effect and minimal-OS requirement. |
