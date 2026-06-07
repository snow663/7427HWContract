# Variable Dependency Graph

Current dependency view from static pass v0.2. This is not yet a complete backward slice; it is the working graph used to decide what must be traced next.

## Fuel scheduler path

```text
$301E / $301C compare writes
<- D = TCNT + delay
<- delay = BPW timer units
<- L0825 / L0827 compare result scratch
<- L0250 BPW
<- L024C / L024E sync BPW
<- L0254 async BPW
<- fuel modifiers: AE, PE, DFCO, warmup, crank, battery correction
<- VE / airflow math
<- MAP, RPM, TPS, CTS, BATT, VSS/state
```

Known timer-control companions:

```text
$3020 TCTL1 output action bits
$3022 TMSK1 interrupt enable bits
$3023 TFLG1 write-one-clear flags
```

## Spark / EST candidate path

```text
$3FE6 / $3FE8 / $3FF6 / $3FDC candidate handoff registers
<- spark delay / dwell / output scheduler units
<- final spark
<- base spark table
<- idle correction
<- coolant correction
<- knock retard if enabled
<- MAP, RPM, CTS, knock/status/state
```

Required next proof:

```text
trace write cadence
trace write order
trace value range vs RPM/MAP/spark
identify latch or read-clear behavior
```

## IAC / output latch candidate path

```text
$3FFC and/or board latch/output path
<- output phase bits or companion command value
<- IAC phase state
<- IAC present / target error
<- target idle RPM
<- CTS, TPS idle flag, VSS rolling-idle state, RPM error
```

Required next proof:

```text
bench IAC movement capture
output bit-to-coil phase mapping
startup park/reset behavior
fault shutdown behavior
```

## ASIC/ref/status path

```text
$3FCA / $3FFA / $3FCx reads
<- ASIC/ref/status hardware state
<- crank/ref events
<- RPM period/counter
<- status flags used by fuel/spark scheduling
```

Required next proof:

```text
log reads under key-on, crank, idle, throttle snap, DFCO, stall
correlate bits with known physical events
separate passive status from read-clear latches
```

## Unknown board I/O path

```text
$3060-$306F writes/reads
<- CPU direct hardware access
<- unknown board/ASIC-adjacent output or configuration
```

Rule: no `$306x` access is removable until trace or bench probing proves it is not required for fuel, spark, idle air, sensor acquisition, watchdog/reset, ALDL/debug, or engine protection.
