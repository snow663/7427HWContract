# 7427 Static Analysis Summary v0.3

- Parsed source lines: 25885
- Parsed instruction rows: 15002
- Hardware/direct/ROM access rows emitted: 7507
- Hardware-facing rows emitted: 427

## Address class counts
- DIRECT_RAM: 4467
- ROM_TABLE: 2200
- EXT_RAM: 412
- UNKNOWN_HW: 192
- HC11_REG: 133
- ASIC_3FXX: 76
- ALDL: 26
- UNCLASSIFIED: 1

## ASIC addresses/ranges found (24)
0x3FC0, 0x3FC0-0x3FF8, 0x3FC4, 0x3FC6, 0x3FC8, 0x3FCA, 0x3FCC, 0x3FCE, 0x3FD4, 0x3FD6, 0x3FD8, 0x3FDA, 0x3FDC, 0x3FE0, 0x3FE4, 0x3FE6, 0x3FE8, 0x3FEA, 0x3FEC, 0x3FF2, 0x3FF6, 0x3FF8, 0x3FFA, 0x3FFC

## HC11/ALDL addresses found (47)
0x103D, 0x3000, 0x3001, 0x3002, 0x3003, 0x3008, 0x3009, 0x300B, 0x300C, 0x300D, 0x300E, 0x3010, 0x3012, 0x3016, 0x301A, 0x301C, 0x301E, 0x3020, 0x3021, 0x3022, 0x3023, 0x3024, 0x3025, 0x3026, 0x3027, 0x3028, 0x302B, 0x302C, 0x302D, 0x302E, 0x302F, 0x3030, 0x3031, 0x3032, 0x3033, 0x3034, 0x3035, 0x3038, 0x3039, 0x303A, 0x303C, 0x303E, 0x303F, 0x305C, 0x305D, 0x305E, 0x305F

## UNKNOWN_HW addresses/ranges found (12)
0x3060, 0x3061, 0x3062, 0x3063, 0x3064, 0x3065, 0x3067, 0x3068, 0x306A, 0x306C, 0x306E, 0x306F

## Scope and current follow-up
This is a coarse source-listing inventory, not whole-program or physical-hardware proof.
Use [ROM-backed hardware boundaries](analysis/FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md) and `maps/structure/factory_global_hardware_accesses.csv` for the stronger access contracts.
Current implementation work and physical-evidence gaps are linked from [WORKING_STATE.md](WORKING_STATE.md) and [pseudo-source/](../pseudo-source/README.md).
Stock BMHM leaves OC4/5 locally disabled; source paths available under other mode constants remain explicitly separate.
