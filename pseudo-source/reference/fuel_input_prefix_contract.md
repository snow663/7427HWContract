# Scheduled fuel ignition/input prefix — BMHM $7D4B..$7E4E

This is an incremental, **callable but not yet fast-dispatch-admitted** stock
translation. The factory `pcm_fuel_control` task remains an explicit boundary
until $7E4F..$852B and the true $852C..$8547 tail can be joined without
skipped producers or output side effects.

## Source sequence

| ROM range | C routine | Source behavior |
|---|---|---|
| $7D4B..$7DB5 | `pcm_fuel_ignition_precheck` | Load $027E, branch on $0044.4 ignition, conditionally clear startup/run memories, update timer and watchdog |
| $7DB6..$7DF0 | existing `pcm_map_transient` | $0041.4/$0089.5 context, RPM delta/idle/O2 flags, held transient MAP application |
| $7DF1..$7E08 | existing `pcm_fuel_throttle` | Copy previous engine TPS, normalize raw TPS by the transmission zero, fault-default fallback |
| $7E09..$7E35 | existing `pcm_fuel_oxygen_filter` | Idle/airflow-select gain and low/high clamp before lag filter |
| $7E36..$7E3F | `pcm_fuel_governor_drive` | Only if calibration $400F.0; now executes $90D3..$9166 proportional/integral duty body |
| $7E40..$7E4E | existing `pcm_fuel_density` | Zero-extended $01C6 MAP, FDIV by 694 and add $0A59 to density $0257 |
| $7D4B..$7E4E | `pcm_fuel_input_prefix` | Calls the first two group functions in source order; propagates nonreturning trap and failed governor drive output |

## Ignition gates and exception boundary

When $0044.4 is set, $027E values below eight skip the startup/RAM reset;
the counter is incremented and **one** COP byte ($55) is written to $303A.
At eight or above the source performs independent byte bit-clears at
$0004, $0019 and $004F, clears $00FD/$024C, $0062/$02CD/$02CE/$0268,
sets $0051.3, clears $0086.3, and clears $0004.3. It then compares the
original $027E against ROM word $4009; count >= limit writes $08 to
$3039, executes TAP with A=$50 and enters a nonreturning trap at $7D8E.
The C interface expresses this as `PCM_HALT_BOUNDARY`, after the board
write and IRQ-mask call. It does **not** execute an HC11 TAP instruction
or claim an implemented halt/illegal instruction on physical hardware.

When $0044.4 is clear, only an existing $0051.3 causes the once-only
clear of $0051.3/$0046.7/$0044.3/$003E.3, $0223 and $027D. The source
always sets $0086.3, wraps the $027E counter to zero, then writes COP55.

The C port uses 8/16-bit logical read/write callbacks with actual source
transaction order. The future target provider must bind these addresses
to the existing canonical named-state owners, including shared bits.
No duplicate 64 KB production RAM is introduced.

## Tests and current limitations

The isolated host harness for the ignition precheck was compiled with
C11 strict warnings and passed five branch-mode scenarios with **82
individual failed-I/O prefix cases** on the local stubbed backend. A matching
repository fixture is registered in both CMake and the Python fast gate, as
is a separate joined prefix fixture covering optional governor admission,
success/failure, MAP/TPS/O2 ordering and early trap propagation. These
repository fixtures have **not yet** run against the full integrated project
or been compared with the executable BMHM ROM after this branch change.
That work belongs to focused development validation and the final PR gate.

The callable $852C phase-selected tail and a joined $7D4B..$8547
`pcm_fuel_cycle` are now committed separately. See
[fuel_scheduled_tail_contract.md](fuel_scheduled_tail_contract.md).
The $90D3..$9166 governor PWM/drive body is now resident, including the
$306C word publication, ordered dual scaled-curve ROM reads, saturation,
source integral reset and service overrides. The $8EB4 target stage also
executes its $8EC9..$8EDA signed RPM error prelude; $8EDB..$90D2 and
optional $1809 remain explicit boundaries. See
[governor drive contract](fuel_governor_drive_contract.md).

Next implementation order: close the remaining $8EDB..$90D2 governing
TPS calculation and $1809 interface; verify canonical provider aliases
and full source-order histories before replacing the broad fuel task.
Verify special crank, VATS/authorization, governor-option, failure-prefix,
phase-flag and output histories **before** admitting it to foreground
dispatch. Do not infer flashed BIN/actuator proof from host comparisons.
