# 7427 ASIC / Hardware Register Contract v0.2
Static contract draft generated from `7427_Hardware_Access_Map_v0.2.csv`. Any inferred name is provisional until bench/runtime trace proves it.

## $0001,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R, W`
- Access count: `4`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xD81E, 0xD872, 0xD903, 0xD99D`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved

## $0002,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R, W`
- Access count: `3`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xA239, 0xD863, 0xD913`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved

## $0003,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R, W`
- Access count: `4`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xA23D, 0xBAC1, 0xBB2B, 0xD90F`
- Constant/init candidates: `0xBAC1 STAA $0003,X value_source=A=0x7F`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved

## $0004,X,#$80,LFA4D — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xFA24`
- Constant/init candidates: `0xFA24 BRSET $0004,X,#$80,LFA4D value_source=bit test 0x80`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: BR IF NOT b7 | indexed_unresolved

## $0005,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x9B25`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0008,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `EXEC, R`
- Access count: `7`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB313, 0xBB09, 0xC2F7, 0xC3A8, 0xC3B0, 0xC3B8, 0xC3C0`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved

## $0008,X,#$08 — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC33B`
- Constant/init candidates: `0xC33B BSET $0008,X,#$08 value_source=set 0x08`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0009,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF888`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $000A,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB53D, 0xC757`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $000D,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB545`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $000E,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBAF5`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $000F,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBE45`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0010,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB553`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0019,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `EXEC`
- Access count: `4`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC3AA, 0xC3B2, 0xC3BA, 0xC3C2`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved

## $001A,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `4`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC3CA, 0xC3D2, 0xC3DA, 0xC3E2`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved

## $001B,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC71, 0xC2E4`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $001C,X,#$18,LB340 — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB327`
- Constant/init candidates: `0xB327 BRCLR $001C,X,#$18,LB340 value_source=bit test 0x18`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0020,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBE47`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $002B,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `4`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC3CC, 0xC3D4, 0xC3DC, 0xC3E4`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved

## $002C,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC2E6`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0031,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBE49`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $003D,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC2DA`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0042,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBE4B`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $004E,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC6B, 0xC2DC`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $0053,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBE4D`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0054,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBE4F`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $005F,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `3`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB99C, 0xBC6D, 0xC2DE`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved

## $0065,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB971, 0xBE51`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $006B,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC329`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0070,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC6F`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0075,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBE55`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0076,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB973, 0xBE53`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $0086,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBE57`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0087,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB975`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0097,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBE59`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0098,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB977, 0xBE37`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $00A9,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB979, 0xBE39`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $00B3,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `4`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC364, 0xC36C, 0xC374, 0xC37C`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved

## $00BA,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB97B, 0xBE3B`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $00C4,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `5`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC366, 0xC36E, 0xC376, 0xC37E, 0xF18F`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved

## $00C5,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `4`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC386, 0xC38E, 0xC396, 0xC39E`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved

## $00C7,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF19B`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00CB,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBE3D`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00D6,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `4`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC388, 0xC390, 0xC398, 0xC3A0`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved

## $00DC,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBE3F`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00ED,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBE41`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00EE,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC314`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00EF,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC316`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00F0,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC318`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00F1,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC358`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00F2,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC35A`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00F3,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC35C`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00F4,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC2FC`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00F5,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC2FE`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00F6,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC300`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00F7,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC340`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00F8,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC342`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00F9,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC344`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00FA,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC336`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00FB,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB965`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $00FE,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBE43`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $01,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `3`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF4E7, 0xF5AD, 0xFB59`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: Calc Col Arg offset, (Limited to 0) | indexed_unresolved; indexed_unresolved; indexed_unresolved

## $01,Y — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF546`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $02,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `3`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF5C5, 0xF9BE, 0xFA2E`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved

## $02,Y — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `3`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF4FD, 0xF503, 0xF536`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved

## $03,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R, RMW`
- Access count: `11`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB4DD, 0xF509, 0xF51B, 0xF51F, 0xF531, 0xF5A8, 0xF5B8, 0xF5BA, 0xF5BF, 0xF5C8, 0xF619`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved

## $03,X,#$40,LF88C — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF876`
- Constant/init candidates: `0xF876 BRSET $03,X,#$40,LF88C value_source=bit test 0x40`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: BR IF b6 | indexed_unresolved

## $03,X,#$80,LF881 — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF872`
- Constant/init candidates: `0xF872 BRSET $03,X,#$80,LF881 value_source=bit test 0x80`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: BR IF b7 | indexed_unresolved

## $03,Y — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF50C, 0xF522`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $04,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R, RMW, W`
- Access count: `9`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xAD54, 0xB983, 0xB98F, 0xF585, 0xF59A, 0xF5B4, 0xF5BD, 0xF5C1, 0xF611`
- Constant/init candidates: `0xF59A STD $04,X value_source=D=0xFFFF`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; Get MSB of Mult'er | indexed_unresolved; indexed_unresolved

## $05,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R, RMW, W`
- Access count: `7`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC3F, 0xBC63, 0xF5AB, 0xF5B0, 0xF61F, 0xF87A, 0xF88D`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved

## $06,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB4E1`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $07,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xC751`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $08,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF3E6`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $09,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF623`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0B,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBB1E`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $0B,X,#$08 — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x75CE`
- Constant/init candidates: `0x75CE BSET $0B,X,#$08 value_source=set 0x08`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: SET b3, COMP FORCE 5 | indexed_unresolved

## $0B,X,#$10 — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x7601`
- Constant/init candidates: `0x7601 BSET $0B,X,#$10 value_source=set 0x10`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: SET b4 | indexed_unresolved

## $0E,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `4`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x75DD, 0x75E5, 0x7610, 0x7618`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: 16 BIT FREE RUN CNT'R | indexed_unresolved; 16 BIT FREE RUN CNT'R | indexed_unresolved; SET UP CPU TIMER | indexed_unresolved; GET CPU FREE RUN 16 BIT TIMER | indexed_unresolved

## $16,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB4D5`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $17,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC49`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $18,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB985`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $1C,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x7626`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $1E,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x75F3`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: TIC4/TOC5 | indexed_unresolved

## $20,X,#$01 — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x75E2`
- Constant/init candidates: `0x75E2 BCLR $20,X,#$01 value_source=clear 0x01`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: CLR b0, | indexed_unresolved

## $20,X,#$03 — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x75CB`
- Constant/init candidates: `0x75CB BSET $20,X,#$03 value_source=set 0x03`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: SET b0 & b1, TCTL1, | indexed_unresolved

## $20,X,#$04 — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x7615`
- Constant/init candidates: `0x7615 BCLR $20,X,#$04 value_source=clear 0x04`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $20,X,#$0C — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x75FE`
- Constant/init candidates: `0x75FE BSET $20,X,#$0C value_source=set 0x0C`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: SET b2, b3 | indexed_unresolved

## $23,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x75F9`
- Constant/init candidates: `0x75F9 STAA $23,X value_source=A=0x01`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: CLR TFLG 1 | indexed_unresolved

## $28,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC4B`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $2C,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB987, 0xBC73`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $39,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC4D, 0xF3EB`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $3D,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC75`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $40,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB989`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $4A,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC4F`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $5B,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC51`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $66,X,#$43,LB9D6 — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB96C`
- Constant/init candidates: `0xB96C BRCLR $66,X,#$43,LB9D6 value_source=bit test 0x43`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $6C,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC53`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $7D,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC55`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $81,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBA32`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $8E,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC57`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $92,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBA34`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $A3,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBA36`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $B0,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC59`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $C1,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R, RMW`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC5B, 0xF1E8`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $C2,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF1F7`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $C3,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF20A`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $C5,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF1AA`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $C6,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF1C5`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $C8,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF1B6`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $C9,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF1D1`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $CB,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB97D`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $D2,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC5D`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $D3,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC41`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $DC,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB97F, 0xB98B`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $E3,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC3B, 0xBC5F`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $E4,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC43`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $EF,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB4CC`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## $F0,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xB981, 0xB98D`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $F4,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `2`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC3D, 0xBC61`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved

## $F5,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xBC45`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## 0,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `spark/EST command or timing handoff`
- Access type(s): `EXEC, R, RMW, W`
- Access count: `166`
- Subsystem: `OTHER, SENSOR_ADC, SPARK_EST`
- Minimal OS required: `yes`
- Access PCs: `0x7501, 0x784C, 0x7A4D, 0x7A4F, 0x7A72, 0x7A77, 0x7C63, 0x86A1, 0x8CDC, 0x8D05, 0x8D7D, 0x8E78, 0x8E9A, 0x97C8, 0x9878, 0x9891, 0x99BA, 0x99BE, 0x9A80, 0x9C04, 0x9C47, 0x9DC6, 0x9DCB, 0xA245, 0xAAD4, 0xAB9A, 0xAB9E, 0xABA0, 0xABA2, 0xAD29 ...`
- Constant/init candidates: `0x9DCB STD 0,X value_source=D=0xFFFF`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ADD TBL VAL TO D | indexed_unresolved; GET TBL VAL | indexed_unresolved; GET MAJOR LOOP ADDRESS FM TBL | indexed_unresolved; CALL MAJOR LOOP SUB'S | indexed_unresolved; indexed_unresolved

## 0,Y — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R, W`
- Access count: `3`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xAFDC, 0xB9D5, 0xF627`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved

## 0x103D — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x7108`
- Constant/init candidates: `0x7108 STAA $3D,X value_source=A=0x03`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: CPU INIT REG | indexed_resolved

## 0x3000 — PORTA/TIMER_PIN_STATUS

- Address class: `HC11_REG`
- Proposed category: `reset/init/watchdog configuration`
- Access type(s): `R, W`
- Access count: `6`
- Subsystem: `BOOT_WATCHDOG_CPU`
- Minimal OS required: `yes`
- Access PCs: `0x7120, 0x77E2, 0x7812, 0x787C, 0x78E0, 0xAEA7`
- Constant/init candidates: `0x7120 STAA 0,X value_source=A=0x00 | 0x77E2 BRCLR 0,X,#$08,L77EE value_source=bit test 0x08 | 0x7812 BRCLR 0,X,#$10,L781E value_source=bit test 0x10 | 0x787C BRCLR 0,X,#$08,L78C5 value_source=bit test 0x08 | 0x78E0 BRCLR 0,X,#$10,L7929 value_source=bit test 0x10`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: PORTA / timer pin status | indexed_resolved; PORTA / timer pin status | indexed_resolved; PORTA / timer pin status | BR IF NOT b4 | indexed_resolved; PORTA / timer pin status | BR IF NOT b3, (NO INTERUPT) | indexed_resolved; PORTA / timer pin status | BR IF NOT b4, TOC3 | indexed_resolved

## 0x3001 — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0xCC97`
- Constant/init candidates: `0xCC97 STAA $0001,X value_source=A=0x38`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: PIOC | indexed_resolved

## 0x3002 — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0xAEB1`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: PORTC

## 0x3003 — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0xCC8B`
- Constant/init candidates: `0xCC8B STAA $03,X value_source=A=0x00`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: PORTB | indexed_resolved

## 0x3008 — PORTE_ADC_INPUT

- Address class: `HC11_REG`
- Proposed category: `sensor acquisition`
- Access type(s): `R, RMW, W`
- Access count: `8`
- Subsystem: `SENSOR_ADC`
- Minimal OS required: `yes`
- Access PCs: `0x7122, 0x9251, 0xD162, 0xD168, 0xD16A, 0xF275, 0xF27B, 0xF27D`
- Constant/init candidates: `0x7122 STAA $08,X value_source=A=0x00 | 0xD162 BCLR 8,X,#$38 value_source=clear 0x38 | 0xF275 BCLR 8,X,#$38 value_source=clear 0x38`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: PORTE / ADC input port | indexed_resolved; PORTE / ADC input port | CPU PORT D; PORTE / ADC input port | CLR PRT D b3, b4 & b5 | indexed_resolved; PORTE / ADC input port | indexed_resolved; PORTE / ADC input port | PORT D | indexed_resolved

## 0x3009 — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0xCC9B`
- Constant/init candidates: `0xCC9B STAA $0009,X value_source=A=0x38`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: CFORC/Timer force compare candidate | indexed_resolved

## 0x300B — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0xCC83`
- Constant/init candidates: `0xCC83 STAA $0B,X value_source=A=0x00`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: CFORC / compare force | indexed_resolved

## 0x300C — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0xCC7D`
- Constant/init candidates: `0xCC7D STAA $0C,X value_source=A=0x00`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: OC1D candidate | indexed_resolved

## 0x300D — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0xCC7F`
- Constant/init candidates: `0xCC7F STAA $0D,X value_source=A=0x00`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: TCNT high? candidate | indexed_resolved

## 0x300E — TCNT_FREE_RUNNING_COUNTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `9`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0x745E, 0x74F1, 0x77D6, 0x7806, 0x78B5, 0x78C8, 0x7919, 0x792C, 0x7A62`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: TCNT 16-bit free-running counter | 16 BIT FREE RUN CNT'R; TCNT 16-bit free-running counter | 16 BIT FREE RUN CNT'R; TCNT 16-bit free-running counter | 16 BIT FREE RUN CNT'R | indexed_resolved; TCNT 16-bit free-running counter | 16 BIT FREE RUN CNT'R | indexed_resolved; TCNT 16-bit free-running counter | 16 BIT FREE RUN CNT'R | indexed_resolved

## 0x3010 — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `2`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0xAF7B, 0xAF83`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: TIC1 | indexed_resolved; TIC1 | indexed_resolved

## 0x3012 — TIC2_CAPTURE

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `2`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0x7425, 0xAE67`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: TIC2 | GET TIC 2 VALUE; TIC2 | TIC 2

## 0x3016 — TOC1_COMPARE_KNOCK_WINDOW

- Address class: `HC11_REG`
- Proposed category: `spark/EST command or timing handoff`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `SPARK_EST`
- Minimal OS required: `yes`
- Access PCs: `0x7503`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: TOC1 | TOC 1

## 0x301A — TOC3_HEARTBEAT_COMPARE

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `R, W`
- Access count: `4`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0x7464, 0x793D, 0x7943, 0x7A65`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: TOC3 | TOC3; TOC3 | TOC3; TOC3 | TOC3; TOC3 | TOC3

## 0x301C — TOC4_COMPARE_INJECTOR_A

- Address class: `HC11_REG`
- Proposed category: `timer compare / flag / output action`
- Access type(s): `R, W`
- Access count: `5`
- Subsystem: `FUEL_SCHED_TIMER`
- Minimal OS required: `yes`
- Access PCs: `0x7819, 0x7824, 0x78FC, 0x7914, 0x793A`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: TOC4 compare | TOC 4 | indexed_resolved; TOC4 compare | TOC 4 VALUE | indexed_resolved; TOC4 compare | TOC4 | indexed_resolved; TOC4 compare | TOC4 | indexed_resolved; TOC4 compare | TOC4 | indexed_resolved

## 0x301E — TOC5_COMPARE_INJECTOR_B

- Address class: `HC11_REG`
- Proposed category: `timer compare / flag / output action`
- Access type(s): `R, W`
- Access count: `5`
- Subsystem: `FUEL_SCHED_TIMER`
- Minimal OS required: `yes`
- Access PCs: `0x77E9, 0x77F4, 0x7898, 0x78B0, 0x78D6`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: TOC5/TIC4 compare | TIC4/TOC5 | indexed_resolved; TOC5/TIC4 compare | TIC4/TOC5	VALUE | indexed_resolved; TOC5/TIC4 compare | TIC4/TOC5 | indexed_resolved; TOC5/TIC4 compare | TIC4/TOC5 | indexed_resolved; TOC5/TIC4 compare | TIC4/TOC5	VALUE | indexed_resolved

## 0x3020 — TCTL1_OUTPUT_COMPARE_ACTION

- Address class: `HC11_REG`
- Proposed category: `timer compare / flag / output action`
- Access type(s): `RMW`
- Access count: `6`
- Subsystem: `FUEL_SCHED_TIMER`
- Minimal OS required: `yes`
- Access PCs: `0x77EE, 0x781E, 0x7883, 0x78C5, 0x78E7, 0x7929`
- Constant/init candidates: `0x77EE BSET $20,X,#$03 value_source=set 0x03 | 0x781E BSET $20,X,#$0C value_source=set 0x0C | 0x7883 BCLR $20,X,#$01 value_source=clear 0x01 | 0x78C5 BSET $20,X,#$01 value_source=set 0x01 | 0x78E7 BCLR $20,X,#$04 value_source=clear 0x04`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: TCTL1 output compare action | indexed_resolved; TCTL1 output compare action | SET b2 & b3, TCTL1 OL4 & OM4 | indexed_resolved; TCTL1 output compare action | CLR b0, TCTL1, OL5 DISCON FM PIN | indexed_resolved; TCTL1 output compare action | SET b0 | indexed_resolved; TCTL1 output compare action | SET b2, TCTL1, OL4 TGGLE OC LINE | indexed_resolved

## 0x3021 — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0xCC8F`
- Constant/init candidates: `0xCC8F STAA $0021,X value_source=A=0x26`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: TCTL2 input capture edge | indexed_resolved

## 0x3022 — TMSK1_TIMER_INT_MASK

- Address class: `HC11_REG`
- Proposed category: `timer compare / flag / output action`
- Access type(s): `RMW, W`
- Access count: `7`
- Subsystem: `FUEL_SCHED_TIMER`
- Minimal OS required: `yes`
- Access PCs: `0x7469, 0x77DF, 0x780F, 0x7880, 0x78E4, 0xCC56, 0xFC31`
- Constant/init candidates: `0x7469 STAA L3022 value_source=A=0xA0 | 0x77DF BSET $22,X,#$08 value_source=set 0x08 | 0x780F BSET $22,X,#$10 value_source=set 0x10 | 0x7880 BCLR $22,X,#$08 value_source=clear 0x08 | 0x78E4 BCLR $22,X,#$10 value_source=clear 0x10`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: TMSK1 timer interrupt mask | TMSK1; TMSK1 timer interrupt mask | SET b3, TMSK1 TIC4/TOC5 INT ENABLE | indexed_resolved; TMSK1 timer interrupt mask | SET b4, TMSK1 TOC 4 INT ENABLE | indexed_resolved; TMSK1 timer interrupt mask | CLR b3, TMASK1, TIC4/TOC5 INHIB | indexed_resolved; TMSK1 timer interrupt mask | SET b4, TOC4 INT ENABLE | indexed_resolved

## 0x3023 — TFLG1_TIMER_FLAGS_W1C

- Address class: `HC11_REG`
- Proposed category: `timer compare / flag / output action`
- Access type(s): `R, W`
- Access count: `14`
- Subsystem: `FUEL_SCHED_TIMER`
- Minimal OS required: `yes`
- Access PCs: `0x745B, 0x754D, 0x7597, 0x76E1, 0x772B, 0x7731, 0x77DD, 0x780D, 0x787A, 0x78DE, 0x7948, 0xCE7E, 0xFC16, 0xFC36`
- Constant/init candidates: `0x745B STAA L3023 value_source=A=0xFF | 0x754D STAA $23,X value_source=A=0x01 | 0x7597 BRSET $23,X,#$01,L75F7 value_source=bit test 0x01 | 0x76E1 STAA $23,X value_source=A=0x01 | 0x772B BRCLR $23,X,#$01,L774C value_source=bit test 0x01`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: TFLG1 timer interrupt flags / write-one-clear | TFLG 1; TFLG1 timer interrupt flags / write-one-clear | TFLG1 | indexed_resolved; TFLG1 timer interrupt flags / write-one-clear | TFLG1, INPUT CAPT, | indexed_resolved; TFLG1 timer interrupt flags / write-one-clear | indexed_resolved; TFLG1 timer interrupt flags / write-one-clear | indexed_resolved

## 0x3024 — TMSK2_TIMER_PRESCALE_RTI

- Address class: `HC11_REG`
- Proposed category: `reset/init/watchdog configuration`
- Access type(s): `W`
- Access count: `2`
- Subsystem: `BOOT_WATCHDOG_CPU`
- Minimal OS required: `yes`
- Access PCs: `0x7113, 0xFC3C`
- Constant/init candidates: `0x7113 STAA $24,X value_source=A=0x03 | 0xFC3C STAA L3024 value_source=A=0x03`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: TMSK2 timer prescale/RTI mask | TMSK2 | indexed_resolved; TMSK2 timer prescale/RTI mask | TMSK2

## 0x3025 — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0xFC41`
- Constant/init candidates: `0xFC41 STAA L3025 value_source=A=0xFF`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: TFLG2 timer flags | TFLG2

## 0x3026 — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0xCC93`
- Constant/init candidates: `0xCC93 STAA $0026,X value_source=A=0x40`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: PACTL pulse accumulator control | indexed_resolved

## 0x3027 — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `2`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0xAF78, 0xAF7E`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: PACNT pulse accumulator count | PACNT; PACNT pulse accumulator count | PACNT

## 0x3028 — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0xCC85`
- Constant/init candidates: `0xCC85 STAA $28,X value_source=A=0x00`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: SPCR SPI control | indexed_resolved

## 0x302B — UNNAMED_HW_REGISTER

- Address class: `ALDL`
- Proposed category: `ALDL/SCI serial control`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `ALDL_SCI`
- Minimal OS required: `yes`
- Access PCs: `0xCC9F`
- Constant/init candidates: `0xCC9F STAA $002B,X value_source=A=0x04`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: BAUD SCI baud | indexed_resolved

## 0x302C — UNNAMED_HW_REGISTER

- Address class: `ALDL`
- Proposed category: `ALDL/SCI serial control`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `ALDL_SCI`
- Minimal OS required: `yes`
- Access PCs: `0xCC81`
- Constant/init candidates: `0xCC81 STAA $2C,X value_source=A=0x00`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: SCCR1 SCI control 1 | indexed_resolved

## 0x302D — SCCR2_SCI_CONTROL2

- Address class: `ALDL`
- Proposed category: `ALDL/SCI serial control`
- Access type(s): `R, W`
- Access count: `11`
- Subsystem: `ALDL_SCI`
- Minimal OS required: `yes`
- Access PCs: `0x7154, 0xF645, 0xF7AF, 0xF7ED, 0xF7FA, 0xF807, 0xF811, 0xF907, 0xF950, 0xFA48, 0xFA57`
- Constant/init candidates: `0x7154 STAB $2D,X value_source=B=0x26 | 0xF645 STAA L302D value_source=A=0x88 | 0xF7AF STAA L302D value_source=A=0x26 | 0xF7ED BRCLR $2D,X,#$20,LF7FA value_source=bit test 0x20 | 0xF7FA BRCLR $2D,X,#$80,LF807 value_source=bit test 0x80`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: SCCR2 SCI control 2 | SCI CNT'L REG #2 | indexed_resolved; SCCR2 SCI control 2 | SCI CNT'L REG #2; SCCR2 SCI control 2 | SCI CNT'L REG #2; SCCR2 SCI control 2 | BR IF NOT b5, (RX INT ENABLED) | indexed_resolved; SCCR2 SCI control 2 | BR IF NOT b7, (TX INT ENABLED) | indexed_resolved

## 0x302E — SCSR_SCI_STATUS

- Address class: `ALDL`
- Proposed category: `ALDL/SCI serial control`
- Access type(s): `R`
- Access count: `8`
- Subsystem: `ALDL_SCI`
- Minimal OS required: `yes`
- Access PCs: `0x7150, 0xF608, 0xF7F1, 0xF7FE, 0xF80B, 0xF8FF, 0xF90B, 0xFA2B`
- Constant/init candidates: `0xF7F1 BRCLR $2E,X,#$20,LF821 value_source=bit test 0x20 | 0xF7FE BRCLR $2E,X,#$80,LF821 value_source=bit test 0x80 | 0xF80B BRCLR $2E,X,#$40,LF821 value_source=bit test 0x40`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: SCSR SCI status | SCSR, GET SCI STATUS & RX BYTE | indexed_resolved; SCSR SCI status | GET SCI STATUS; SCSR SCI status | BR IF NOT b5,	(RX REG FULL) | indexed_resolved; SCSR SCI status | BR IF NOT b7,	(TX REG EMPTY) | indexed_resolved; SCSR SCI status | BR IF NOT b6,	(TC DONE) | indexed_resolved

## 0x302F — SCDR_SCI_DATA

- Address class: `ALDL`
- Proposed category: `ALDL/SCI serial control`
- Access type(s): `R, W`
- Access count: `5`
- Subsystem: `ALDL_SCI`
- Minimal OS required: `yes`
- Access PCs: `0xF60B, 0xF8E6, 0xF902, 0xF90E, 0xFA30`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: SCDR SCI data | TX 8192 DATA; SCDR SCI data | TX A BYTE VIA 8192; SCDR SCI data | GET 8192 RX'ED DATA; SCDR SCI data | SCI DATA REG; SCDR SCI data | SCI DATA REG

## 0x3030 — ADCTL_ADC_CONTROL_STATUS

- Address class: `HC11_REG`
- Proposed category: `sensor acquisition`
- Access type(s): `R, W`
- Access count: `7`
- Subsystem: `SENSOR_ADC`
- Minimal OS required: `yes`
- Access PCs: `0x7521, 0x7B73, 0x7B79, 0xD171, 0xD176, 0xF262, 0xF267`
- Constant/init candidates: `0x7B73 STAA L3030 value_source=A=0x07 | 0x7B79 BRCLR $0030,X,#$80,L7B79 value_source=bit test 0x80 | 0xD171 STAA L3030 value_source=A=0x01 | 0xD176 BRSET $30,X,#$80,LD183 value_source=bit test 0x80 | 0xF267 BRSET $30,X,#$80,LF274 value_source=bit test 0x80`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ADCTL A/D control | A/D CNT'L REG; ADCTL A/D control; ADCTL A/D control | indexed_resolved; ADCTL A/D control | A/D CNTL; ADCTL A/D control | BR IF b7, | indexed_resolved

## 0x3031 — ADR1_ADC_RESULT

- Address class: `HC11_REG`
- Proposed category: `sensor acquisition`
- Access type(s): `R`
- Access count: `5`
- Subsystem: `SENSOR_ADC`
- Minimal OS required: `yes`
- Access PCs: `0x7528, 0x7B7E, 0xF24C, 0xFA6B, 0xFA7B`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ADR1 A/D result 1 | GET A/D RESULT, CH 1; ADR1 A/D result 1; ADR1 A/D result 1 | A/D CH 1 | indexed_resolved; ADR1 A/D result 1 | GET A/D RESULT #1,; ADR1 A/D result 1 | GET A/D RESULT #1

## 0x3032 — ADR2_ADC_RESULT

- Address class: `HC11_REG`
- Proposed category: `sensor acquisition`
- Access type(s): `R`
- Access count: `3`
- Subsystem: `SENSOR_ADC`
- Minimal OS required: `yes`
- Access PCs: `0x7B81, 0xF236, 0xF254`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ADR2 A/D result 2; ADR2 A/D result 2 | A/D CH 2 | indexed_resolved; ADR2 A/D result 2 | A/D CH 2 | indexed_resolved

## 0x3033 — ADR3_ADC_RESULT

- Address class: `HC11_REG`
- Proposed category: `sensor acquisition`
- Access type(s): `R`
- Access count: `3`
- Subsystem: `SENSOR_ADC`
- Minimal OS required: `yes`
- Access PCs: `0x7B86, 0xF23B, 0xF259`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ADR3 A/D result 3; ADR3 A/D result 3 | A/D CH 3 | indexed_resolved; ADR3 A/D result 3 | A/D CH 3 | indexed_resolved

## 0x3034 — ADR4_ADC_RESULT

- Address class: `HC11_REG`
- Proposed category: `sensor acquisition`
- Access type(s): `R`
- Access count: `9`
- Subsystem: `SENSOR_ADC`
- Minimal OS required: `yes`
- Access PCs: `0x7B8B, 0xC57D, 0xC599, 0xCEF1, 0xD184, 0xDC0A, 0xF21A, 0xF229, 0xF23F`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ADR4 A/D result 4; ADR4 A/D result 4 | READ A/D CH | indexed_resolved; ADR4 A/D result 4 | GET A/D VAL FM ADR4 | indexed_resolved; ADR4 A/D result 4 | A/D RESULT 4 | indexed_resolved; ADR4 A/D result 4 | A/D RESULTS CH 4 | indexed_resolved

## 0x3035 — BPROT_EEPROM_PROTECT

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0x711A`
- Constant/init candidates: `0x711A STAA $35,X value_source=A=0x1B`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: BPROT EEPROM block protect | BPROT | indexed_resolved

## 0x3038 — OPT2_OPTION2

- Address class: `HC11_REG`
- Proposed category: `reset/init/watchdog configuration`
- Access type(s): `RMW`
- Access count: `1`
- Subsystem: `BOOT_WATCHDOG_CPU`
- Minimal OS required: `yes`
- Access PCs: `0x7115`
- Constant/init candidates: `0x7115 BCLR $38,X,#$20 value_source=clear 0x20`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: OPT2 | CLR b5, OPT2, 4X CLK OUT | indexed_resolved

## 0x3039 — OPTION_REG

- Address class: `HC11_REG`
- Proposed category: `reset/init/watchdog configuration`
- Access type(s): `W`
- Access count: `2`
- Subsystem: `BOOT_WATCHDOG_CPU`
- Minimal OS required: `yes`
- Access PCs: `0x710F, 0x7D89`
- Constant/init candidates: `0x710F STAA $39,X value_source=A=0xB8 | 0x7D89 STAB L3039 value_source=B=0x08`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: OPTION | OPTION REG | indexed_resolved; OPTION

## 0x303A — COPRST_WATCHDOG_CLEAR

- Address class: `HC11_REG`
- Proposed category: `reset/init/watchdog configuration`
- Access type(s): `W`
- Access count: `10`
- Subsystem: `BOOT_WATCHDOG_CPU`
- Minimal OS required: `yes`
- Access PCs: `0x7443, 0x7448, 0x79EA, 0x79ED, 0x7DB3, 0x9169, 0xF2EF, 0xF2F3, 0xFA87, 0xFA8A`
- Constant/init candidates: `0x7443 STAA L303A value_source=A=0x55 | 0x7448 STAA L303A value_source=A=0xAA | 0x79EA STAA L303A value_source=A=0xAA | 0x79ED STAB L303A value_source=B=0x55 | 0x7DB3 STAA L303A value_source=A=0x55`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: COPRST watchdog clear | ARM COP TIMER CLEARING MECHANISM; COPRST watchdog clear | CLEAR COP; COPRST watchdog clear; COPRST watchdog clear; COPRST watchdog clear | COP1

## 0x303C — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0xCCA3`
- Constant/init candidates: `0xCCA3 STAA $003C,X value_source=A=0x15`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_resolved

## 0x303E — UNNAMED_HW_REGISTER

- Address class: `HC11_REG`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `HC11_CORE`
- Minimal OS required: `yes`
- Access PCs: `0xCC87`
- Constant/init candidates: `0xCC87 STAA $3E,X value_source=A=0x00`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_resolved

## 0x303F — CONFIG_REG

- Address class: `HC11_REG`
- Proposed category: `reset/init/watchdog configuration`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `BOOT_WATCHDOG_CPU`
- Minimal OS required: `yes`
- Access PCs: `0x71C6`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: CONFIG/EPROM config candidate

## 0x305C — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xCC89`
- Constant/init candidates: `0xCC89 STAA $5C,X value_source=A=0x00`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_resolved

## 0x305D — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xCCA7`
- Constant/init candidates: `0xCCA7 STAA $005D,X value_source=A=0xAC`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_resolved

## 0x305E — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xCCAF`
- Constant/init candidates: `0xCCAF STAA $005E,X value_source=A=0x00`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_resolved

## 0x305F — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xCCAB`
- Constant/init candidates: `0xCCAB STAA $005F,X value_source=A=0xCB`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_resolved

## 0x3060 — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown hardware; test item`
- Access type(s): `R, RMW, W`
- Access count: `6`
- Subsystem: `UNKNOWN_306X_BOARD_IO`
- Minimal OS required: `test-item`
- Access PCs: `0xA5D4, 0xAEB7, 0xF400, 0xF409, 0xFB4A, 0xFB51`
- Constant/init candidates: `0xA5D4 BCLR 0,X,#$10 value_source=clear 0x10`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: CLR b4, | indexed_resolved; I/O PORT

## 0x3061 — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown hardware; test item`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `UNKNOWN_306X_BOARD_IO`
- Minimal OS required: `test-item`
- Access PCs: `0xCCB3`
- Constant/init candidates: `0xCCB3 STAA L3061 value_source=A=0x90`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: 

## 0x3062 — EXT_3062_SPARK_KNOCK_WINDOW_TOGGLE

- Address class: `UNKNOWN_HW`
- Proposed category: `spark/EST command or timing handoff`
- Access type(s): `R, RMW, W`
- Access count: `10`
- Subsystem: `SPARK_EST`
- Minimal OS required: `yes`
- Access PCs: `0x7509, 0x750C, 0xAEBA, 0xF411, 0xFB14, 0xFB28, 0xFB39, 0xFB3E, 0xFB54, 0xFB5B`
- Constant/init candidates: `0x7509 BCLR 0,X,#$40 value_source=clear 0x40 | 0x750C BSET 0,X,#$40 value_source=set 0x40`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: External 306x hardware latch/status candidate | CLR b6 | indexed_resolved; External 306x hardware latch/status candidate | SET b6 | indexed_resolved; External 306x hardware latch/status candidate; External 306x hardware latch/status candidate; External 306x hardware latch/status candidate | I/O PORT D

## 0x3063 — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown hardware; test item`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `UNKNOWN_306X_BOARD_IO`
- Minimal OS required: `test-item`
- Access PCs: `0xCCB8`
- Constant/init candidates: `0xCCB8 STAA L3063 value_source=A=0xFF`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: 

## 0x3064 — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown hardware; test item`
- Access type(s): `R`
- Access count: `2`
- Subsystem: `UNKNOWN_306X_BOARD_IO`
- Minimal OS required: `test-item`
- Access PCs: `0xF414, 0xFAD4`
- Constant/init candidates: `0xFAD4 BRCLR 0,Y,#$80,LFB39 value_source=bit test 0x80`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: I/O PORT C; BR IF | indexed_resolved

## 0x3065 — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown hardware; test item`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `UNKNOWN_306X_BOARD_IO`
- Minimal OS required: `test-item`
- Access PCs: `0xCCBD`
- Constant/init candidates: `0xCCBD STAA L3065 value_source=A=0x00`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: 

## 0x3067 — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown hardware; test item`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `UNKNOWN_306X_BOARD_IO`
- Minimal OS required: `test-item`
- Access PCs: `0xF41B`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: 

## 0x3068 — EXT_3068_FORCE_MOTOR_PWM_OR_DRIVER

- Address class: `UNKNOWN_HW`
- Proposed category: `external output latch/driver control`
- Access type(s): `W`
- Access count: `3`
- Subsystem: `IO_LATCH_OUTPUT`
- Minimal OS required: `yes`
- Access PCs: `0x7BA3, 0xFB93, 0xFBCB`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: External 306x output command candidate; External 306x output command candidate; External 306x output command candidate

## 0x306A — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown hardware; test item`
- Access type(s): `W`
- Access count: `4`
- Subsystem: `UNKNOWN_306X_BOARD_IO`
- Minimal OS required: `test-item`
- Access PCs: `0xC56B, 0xCDF3, 0xFB8A, 0xFBB9`
- Constant/init candidates: `0xCDF3 STD L306A value_source=D=0x7F00`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: 

## 0x306C — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown hardware; test item`
- Access type(s): `W`
- Access count: `4`
- Subsystem: `UNKNOWN_306X_BOARD_IO`
- Minimal OS required: `test-item`
- Access PCs: `0x9163, 0xCDDF, 0xFB8D, 0xFBBF`
- Constant/init candidates: `0xCDDF STD L306C value_source=D=0x1F00`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: 

## 0x306E — EXT_306E_IO_INIT_LATCH

- Address class: `UNKNOWN_HW`
- Proposed category: `external output latch/driver control`
- Access type(s): `W`
- Access count: `3`
- Subsystem: `IO_LATCH_OUTPUT`
- Minimal OS required: `yes`
- Access PCs: `0x7128, 0xFB90, 0xFBC5`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: External 306x I/O latch candidate; External 306x I/O latch candidate; External 306x I/O latch candidate | 32,614

## 0x306F — EXT_306F_REF_EVENT_LATCH_OR_RESET

- Address class: `UNKNOWN_HW`
- Proposed category: `external output latch/driver control`
- Access type(s): `W`
- Access count: `2`
- Subsystem: `IO_LATCH_OUTPUT`
- Minimal OS required: `yes`
- Access PCs: `0x7518, 0xA5AA`
- Constant/init candidates: `0x7518 STAB L306F value_source=B=0xFF | 0xA5AA STAA L306F value_source=A=0x00`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: External 306x I/O latch/status candidate; External 306x I/O latch/status candidate

## 0x3FC0 — ASIC_REF_PERIOD_OR_LAST_DRP

- Address class: `ASIC_3FXX`
- Proposed category: `input/status/event latch`
- Access type(s): `R`
- Access count: `8`
- Subsystem: `ASIC_STATUS_REF`
- Minimal OS required: `yes`
- Access PCs: `0x842C, 0x858B, 0xA551, 0xA581, 0xA5E5, 0xA6EF, 0xAB8E, 0xAC58`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC last DRP/ref period counter; ASIC last DRP/ref period counter | LAST REF PERIOD CNT'R; ASIC last DRP/ref period counter; ASIC last DRP/ref period counter | RPM = ((65536 * 120)/8)/CAL; ASIC last DRP/ref period counter | LAST DRP PERIOD CNTR

## 0x3FC0-0x3FF8 — UNNAMED_HW_REGISTER

- Address class: `ASIC_3FXX`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x715B`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: loop clears even ASIC words from $3FC0 through before $3FFA | ASIC last DRP/ref period counter | indexed_resolved

## 0x3FC4 — ASIC_EVENT_CAPTURE_3FC4

- Address class: `ASIC_3FXX`
- Proposed category: `input/status/event latch`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `ASIC_STATUS_REF`
- Minimal OS required: `yes`
- Access PCs: `0x7C00`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC period/status latch candidate

## 0x3FC6 — UNNAMED_HW_REGISTER

- Address class: `ASIC_3FXX`
- Proposed category: `input/status/event latch`
- Access type(s): `R`
- Access count: `2`
- Subsystem: `ASIC_STATUS_REF`
- Minimal OS required: `yes`
- Access PCs: `0xAFC5, 0xAFD2`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_resolved; indexed_resolved

## 0x3FC8 — UNNAMED_HW_REGISTER

- Address class: `ASIC_3FXX`
- Proposed category: `input/status/event latch`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `ASIC_STATUS_REF`
- Minimal OS required: `yes`
- Access PCs: `0xCE81`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC timing/status candidate

## 0x3FCA — ASIC_RPM_EVENT_COUNTER

- Address class: `ASIC_3FXX`
- Proposed category: `input/status/event latch`
- Access type(s): `R`
- Access count: `4`
- Subsystem: `ASIC_STATUS_REF`
- Minimal OS required: `yes`
- Access PCs: `0x741F, 0x8629, 0xABD3, 0xE01E`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC 16-bit RPM/event counter; ASIC 16-bit RPM/event counter | 16 BIT RPM COUNTER; ASIC 16-bit RPM/event counter; ASIC 16-bit RPM/event counter

## 0x3FCC — ASIC_COMMAND_3FCC

- Address class: `ASIC_3FXX`
- Proposed category: `ASIC command/output handoff`
- Access type(s): `W`
- Access count: `2`
- Subsystem: `ASIC_COMMAND_OUTPUT`
- Minimal OS required: `yes`
- Access PCs: `0x74D6, 0xFADC`
- Constant/init candidates: `0x74D6 STD L3FCC value_source=D=0xD000`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC fuel/scheduler command candidate A; ASIC fuel/scheduler command candidate A

## 0x3FCE — ASIC_EFI_PW_OR_OUTPUT_COMMAND

- Address class: `ASIC_3FXX`
- Proposed category: `ASIC command/output handoff`
- Access type(s): `W`
- Access count: `4`
- Subsystem: `ASIC_COMMAND_OUTPUT`
- Minimal OS required: `yes`
- Access PCs: `0x8426, 0x8512, 0xFAEE, 0xFB44`
- Constant/init candidates: `0x8512 STD L3FCE value_source=D=0x7FFF | 0xFAEE STD L3FCE value_source=D=0x00C5 | 0xFB44 STD L3FCE value_source=D=0x0000`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC EFI PW / fuel pulse-width handoff; ASIC EFI PW / fuel pulse-width handoff; ASIC EFI PW / fuel pulse-width handoff | SAVE TO EFI PW; ASIC EFI PW / fuel pulse-width handoff

## 0x3FD4 — UNNAMED_HW_REGISTER

- Address class: `ASIC_3FXX`
- Proposed category: `ASIC command/output handoff`
- Access type(s): `W`
- Access count: `3`
- Subsystem: `ASIC_COMMAND_OUTPUT`
- Minimal OS required: `yes`
- Access PCs: `0xCDCB, 0xFB78, 0xFB9B`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC output compare/scheduler slot D4; ASIC output compare/scheduler slot D4; ASIC output compare/scheduler slot D4

## 0x3FD6 — UNNAMED_HW_REGISTER

- Address class: `ASIC_3FXX`
- Proposed category: `ASIC command/output handoff`
- Access type(s): `W`
- Access count: `3`
- Subsystem: `ASIC_COMMAND_OUTPUT`
- Minimal OS required: `yes`
- Access PCs: `0xCD8D, 0xFB7D, 0xFBA3`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC output compare/scheduler slot D6; ASIC output compare/scheduler slot D6; ASIC output compare/scheduler slot D6

## 0x3FD8 — UNNAMED_HW_REGISTER

- Address class: `ASIC_3FXX`
- Proposed category: `ASIC command/output handoff`
- Access type(s): `W`
- Access count: `3`
- Subsystem: `ASIC_COMMAND_OUTPUT`
- Minimal OS required: `yes`
- Access PCs: `0xCE0C, 0xFB82, 0xFBAB`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC output compare/scheduler slot D8; ASIC output compare/scheduler slot D8; ASIC output compare/scheduler slot D8

## 0x3FDA — UNNAMED_HW_REGISTER

- Address class: `ASIC_3FXX`
- Proposed category: `ASIC command/output handoff`
- Access type(s): `W`
- Access count: `3`
- Subsystem: `ASIC_COMMAND_OUTPUT`
- Minimal OS required: `yes`
- Access PCs: `0xCD71, 0xFB87, 0xFBB3`
- Constant/init candidates: `0xCD71 STD L3FDA value_source=D=0xD000`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC output compare/scheduler slot DA | HARDWARE; ASIC output compare/scheduler slot DA; ASIC output compare/scheduler slot DA

## 0x3FDC — ASIC_SPARK_DWELL_WORK_PERIOD

- Address class: `ASIC_3FXX`
- Proposed category: `spark/EST command or timing handoff`
- Access type(s): `R, W`
- Access count: `3`
- Subsystem: `SPARK_EST`
- Minimal OS required: `yes`
- Access PCs: `0xABB0, 0xABC0, 0xFAF7`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC spark dwell / spark work period handoff; ASIC spark dwell / spark work period handoff; ASIC spark dwell / spark work period handoff | SPK WP, (DWELL)

## 0x3FE0 — UNNAMED_HW_REGISTER

- Address class: `ASIC_3FXX`
- Proposed category: `unknown hardware; test item`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `ASIC_UNKNOWN`
- Minimal OS required: `test-item`
- Access PCs: `0xACD3`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC timing/status candidate E0

## 0x3FE4 — ASIC_IGN_OUTPUT_COMPANION

- Address class: `ASIC_3FXX`
- Proposed category: `spark/EST command or timing handoff`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `SPARK_EST`
- Minimal OS required: `yes`
- Access PCs: `0xAC2E`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC ignition/output companion write

## 0x3FE6 — ASIC_SPARK_HANDOFF_A

- Address class: `ASIC_3FXX`
- Proposed category: `spark/EST command or timing handoff`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `SPARK_EST`
- Minimal OS required: `yes`
- Access PCs: `0xABBA`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC spark handoff path

## 0x3FE8 — ASIC_SPARK_HANDOFF_B

- Address class: `ASIC_3FXX`
- Proposed category: `spark/EST command or timing handoff`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `SPARK_EST`
- Minimal OS required: `yes`
- Access PCs: `0xABAA`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC EST/spark timing output engine

## 0x3FEA — ASIC_COMMAND_3FEA

- Address class: `ASIC_3FXX`
- Proposed category: `unknown/other`
- Access type(s): `W`
- Access count: `2`
- Subsystem: `FUEL_MATH_HANDOFF`
- Minimal OS required: `yes`
- Access PCs: `0x74DF, 0xFAE5`
- Constant/init candidates: `0x74DF STD L3FEA value_source=D=0xDFFF`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC fuel/scheduler command candidate B; ASIC fuel/scheduler command candidate B

## 0x3FEC — ASIC_STATUS_3FEC

- Address class: `ASIC_3FXX`
- Proposed category: `input/status/event latch`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `ASIC_STATUS_REF`
- Minimal OS required: `yes`
- Access PCs: `0xAC28`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC hardware status/source

## 0x3FF2 — ASIC_COMMAND_3FF2

- Address class: `ASIC_3FXX`
- Proposed category: `unknown hardware; test item`
- Access type(s): `W`
- Access count: `1`
- Subsystem: `ASIC_UNKNOWN`
- Minimal OS required: `test-item`
- Access PCs: `0x8571`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC output/scheduler candidate

## 0x3FF6 — ASIC_EST_FALL_COUNTER_OR_SCHED

- Address class: `ASIC_3FXX`
- Proposed category: `spark/EST command or timing handoff`
- Access type(s): `R, W`
- Access count: `4`
- Subsystem: `SPARK_EST`
- Minimal OS required: `yes`
- Access PCs: `0xAB97, 0xABA4, 0xABC8, 0xFB03`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC EST fall counter / output scheduler | EST FALL CNT'R; ASIC EST fall counter / output scheduler | EST FALL CNT'R; ASIC EST fall counter / output scheduler | EST FALL CNT'R; ASIC EST fall counter / output scheduler | EST FALL CNT'R

## 0x3FF8 — ASIC_COMMAND_3FF8

- Address class: `ASIC_3FXX`
- Proposed category: `unknown hardware; test item`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `ASIC_UNKNOWN`
- Minimal OS required: `test-item`
- Access PCs: `0xAFCC`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_resolved

## 0x3FFA — ASIC_PACKED_STATUS

- Address class: `ASIC_3FXX`
- Proposed category: `input/status/event latch`
- Access type(s): `R`
- Access count: `2`
- Subsystem: `ASIC_STATUS_REF`
- Minimal OS required: `yes`
- Access PCs: `0x7765, 0x7BF6`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC packed hardware status; ASIC packed hardware status

## 0x3FFC — ASIC_IO_D_PORT_OUTPUT_LATCH

- Address class: `ASIC_3FXX`
- Proposed category: `external output latch/driver control`
- Access type(s): `R, W`
- Access count: `23`
- Subsystem: `IO_LATCH_OUTPUT`
- Minimal OS required: `yes`
- Access PCs: `0x713A, 0x7140, 0x714A, 0x71BD, 0x71EF, 0x71F7, 0x8577, 0x857F, 0x8587, 0xCC5A, 0xCC75, 0xF3EF, 0xF3FD, 0xF637, 0xF63F, 0xF7A2, 0xF7AA, 0xF813, 0xF81B, 0xFA3B, 0xFA43, 0xFB5F, 0xFB69`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: ASIC I/O D port / external output latch | I/O D PORT ..; ASIC I/O D port / external output latch | I/O D PORT ..; ASIC I/O D port / external output latch | I/O D PORT ..; ASIC I/O D port / external output latch | I/O D PORT ..; ASIC I/O D port / external output latch | I/O D PORT ..

## 1,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `8`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x8CEB, 0x8D21, 0xD963, 0xF468, 0xF4AB, 0xF4AF, 0xF551, 0xF571`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved

## 2,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R, W`
- Access count: `10`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x9B1F, 0x9B9C, 0xD7FF, 0xF318, 0xF464, 0xF55D, 0xF589, 0xF592, 0xF5FA, 0xFB67`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved

## 3,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R, W`
- Access count: `4`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x9C00, 0xD803, 0xF56A, 0xF57C`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; Get LSB of mult'cnd | indexed_unresolved

## 4,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R, W`
- Access count: `6`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF31B, 0xF578, 0xF581, 0xF58C, 0xF590, 0xF82B`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; Add result to tepm LSB of | indexed_unresolved; Add LSB of result to MSB of | indexed_unresolved; Add MSB of final to overflow counter | indexed_unresolved

## 5,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R, W`
- Access count: `3`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x9B96, 0xF56F, 0xF574`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved

## 6,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R, RMW, W`
- Access count: `7`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x9B2C, 0x9C09, 0xB433, 0xBC47, 0xF31E, 0xF57E, 0xF583`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved; indexed_unresolved

## 7,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF9AB`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

## 8,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `3`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0x9B2E, 0x9C0E, 0xAD58`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved; indexed_unresolved; indexed_unresolved

## 9,X — UNNAMED_HW_REGISTER

- Address class: `UNKNOWN_HW`
- Proposed category: `unknown/other`
- Access type(s): `R`
- Access count: `1`
- Subsystem: `OTHER`
- Minimal OS required: `unknown`
- Access PCs: `0xF97B`
- Dependency source: `trace backward from CPU register/value_source into direct RAM/table producer; not fully proven in static pass`
- Write order requirements: `preserve stock order until dynamic trace proves safe simplification`
- Read/clear side effects: `unknown unless HC11-defined W1C flag or bench trace proves status latch`
- Timing requirements: `must be measured for timer/output/spark/fuel paths`
- Test needed: `capture PC, registers, address, value, cycle/timestamp across key-on, crank, idle, throttle snap, decel`
- Notes: indexed_unresolved

