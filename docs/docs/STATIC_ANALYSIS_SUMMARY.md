# 7427 Hardware Access Static Pass v0.2
Source: `$31` BMHM/HAC disassembly from ORG `$7100` through end. This is a static source-listing pass, not a dynamic proof.
## Counts
- Total access rows: `7507`
- Hardware-facing rows: `693`
- Minimal-OS required rows: `904`
- Explicit test-item rows: `23`

## Rows by subsystem

| subsystem             |   count |
|:----------------------|--------:|
| OTHER                 |    6391 |
| SENSOR_ADC            |     528 |
| FUEL_MATH_HANDOFF     |     156 |
| SPARK_EST             |     143 |
| IDLE_IAC              |      71 |
| FUEL_SCHED_TIMER      |      37 |
| ALDL_SCI              |      35 |
| HC11_CORE             |      33 |
| IO_LATCH_OUTPUT       |      31 |
| BOOT_WATCHDOG_CPU     |      22 |
| UNKNOWN_306X_BOARD_IO |      20 |
| ASIC_STATUS_REF       |      19 |
| ASIC_COMMAND_OUTPUT   |      18 |
| ASIC_UNKNOWN          |       3 |

## Hardware rows by address class

| address_class   |   count |
|:----------------|--------:|
| UNKNOWN_HW      |     462 |
| HC11_REG        |     129 |
| ASIC_3FXX       |      76 |
| ALDL            |      26 |

## Immediate takeaways

- `$301C/$301E`, `$3020`, `$3022`, and `$3023` form the confirmed HC11 output-compare/timer side of the injector scheduler.
- `$3FCA`, `$3FFA`, and nearby `$3FCx/$3FEx` registers are the main ASIC/ref/status region needing dynamic logging.
- `$3FFC` is repeatedly used as an I/O/output latch during startup and fault paths; it must not be treated as passive RAM.
- `$306x` writes remain board/ASIC-adjacent unknowns. They are not removable until bench trace proves their physical output role.
- Fuel math can be redesigned later, but the timer compare/flag clear/enable order must be preserved until proven otherwise.
