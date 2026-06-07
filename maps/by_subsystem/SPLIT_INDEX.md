# Hardware Access Map Split Index

The full v0.2 access map is large, so the working repo uses subsystem splits plus a hardware-only current map target.

## v0.2 subsystem counts

| Subsystem | Rows | Commit strategy |
|---|---:|---|
| `SENSOR_ADC` | 528 | split CSV, high priority |
| `FUEL_MATH_HANDOFF` | 156 | split CSV, high priority |
| `SPARK_EST` | 143 | split CSV, high priority |
| `IDLE_IAC` | 71 | split CSV, high priority |
| `FUEL_SCHED_TIMER` | 37 | split CSV, high priority |
| `ALDL_SCI` | 35 | split CSV |
| `HC11_CORE` | 33 | split CSV |
| `IO_LATCH_OUTPUT` | 31 | split CSV, high priority |
| `BOOT_WATCHDOG_CPU` | 22 | split CSV |
| `UNKNOWN_306X_BOARD_IO` | 20 | split CSV, high priority test item |
| `ASIC_STATUS_REF` | 19 | split CSV, high priority |
| `ASIC_COMMAND_OUTPUT` | 18 | split CSV, high priority |
| `ASIC_UNKNOWN` | 3 | split CSV, high priority test item |
| `OTHER` | 6391 | do not commit as working noise until needed; regenerate from source/analyzer |

## Local generated split files

These are prepared locally from `7427_Hardware_Access_Map_v0.2.csv` and should be committed in chunks when connector-safe:

```text
maps/by_subsystem/aldl_sci.csv
maps/by_subsystem/asic_command_output.csv
maps/by_subsystem/asic_status_ref.csv
maps/by_subsystem/asic_unknown.csv
maps/by_subsystem/boot_watchdog_cpu.csv
maps/by_subsystem/fuel_math_handoff.csv
maps/by_subsystem/fuel_sched_timer.csv
maps/by_subsystem/hc11_core.csv
maps/by_subsystem/idle_iac.csv
maps/by_subsystem/io_latch_output.csv
maps/by_subsystem/sensor_adc.csv
maps/by_subsystem/spark_est.csv
maps/by_subsystem/unknown_306x_board_io.csv
```

## Working rule

Use the split CSVs for normal review. Regenerate the full map only when changing analyzer logic or source input.
