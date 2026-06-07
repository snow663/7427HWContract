# Maps

Generated maps live here when they are small enough to commit directly.

Current generated local files from static pass v0.2:

```text
7427_Hardware_Access_Map_v0.2.csv              full static access map, large
7427_Hardware_Access_Map_HW_Only_v0.2.csv      hardware-facing subset
7427_Hardware_Test_Matrix_v0.2.csv             dynamic test target matrix
```

Working rule:

- Commit stable current maps when practical.
- Prefer generated `current` names over many near-duplicate exports.
- If a map is too large for connector-safe commit, commit the generator and summary first, then split the map by subsystem/address range.

Planned split layout:

```text
maps/current/hw_access_map_hw_only.csv
maps/current/hardware_test_matrix.csv
maps/by_subsystem/fuel_sched_timer.csv
maps/by_subsystem/spark_est.csv
maps/by_subsystem/asic_status_ref.csv
maps/by_subsystem/io_latch_output.csv
maps/by_subsystem/unknown_306x_board_io.csv
```
