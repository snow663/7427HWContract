# 7427 Variable Dependency Graph v0.1

Static dependency sketch. Dynamic bus trace still required for side effects and units.

## Fuel pulsewidth path

```text
L02CF BPW
← calculated run/crank base pulsewidth
← VE / MAP / RPM / CTS / AFR modifiers / transient fuel

L024C/L024E sync BPW
← L02CF and sync/async mode logic
← crank mode all-injectors-each-DRP branch

L0254 async BPW
← async fuel decision logic
← AE / transient fuel handling

L0250 working BPW
← selected sync/async BPW
← low-BPW correction
← BPW bias L0256
← min/max clamps

HC11 TOC4/TOC5 compare values $301C/$301E
← L0250 plus timer state
← output compare setup $3020/$3022/$3023
```

## Fuel ASIC handoff path

```text
$3FCE EFI PW / fuel handoff writes @ $8426/$8512/$FAEE/$FB44
← L024E/L0254/L0250 fuel pulse state
← async/sync mode decision
← low-BPW thresholds L492A/L492C/L4974
← final fuel math and AE/DFCO gating
```

## Spark / EST path

```text
$3FE8 spark/EST timing write @ $ABAA
← D = computed EST event time
← L3FF6 EST fall counter and L3FC0 ref period timing
← spark/dwell work variables around LAB8E-LABC8
← final spark advance L01FD
← base spark table $4166 or $428A
← idle spark correction tables around $4502/$451B
← coolant spark, altitude spark, low-octane retard, EGR spark correction, startup spark
← MAP/RPM/TPS/CTS/VSS/state flags
```

```text
$3FE6 spark handoff write @ $ABBA
← D = timing/dwell companion value
← L3FDC spark dwell/work period
← same final spark/timing basis as $3FE8
```

```text
$3FDC spark dwell/work period @ $ABC0/$FAF7
← X/D work value from EST scheduling math
← dwell/spark timing counters and startup/default paths
```

## RPM/ref timing input

```text
$3FC0 last DRP/ref period counter reads
← ASIC/ref hardware
→ RPM calculation L0062/L0063/L0068/L006A
→ spark timing, fuel scheduling, idle logic, derivative RPM correction
```

```text
$3FCA RPM/event counter reads
← ASIC/ref hardware
→ initialization/run counter L0205 and runtime RPM/event logic
```

## IAC / external output latch path

```text
$3FFC I/O D port writes
← constants/mode-selected port images, e.g. $B93A/$B91A during init
← ALDL/SCI and hardware output handshakes
← likely external output latch state; exact IAC phase ownership still needs isolation
```

## ALDL/debug

```text
$302D SCCR2, $302E SCSR, $302F SCDR
← ALDL message state L0360-L036C
← SCI interrupt handler LF7EA/LF90B/LF822
→ debug frame TX/RX and RAM/ROM read service
```

## Unknown hardware that cannot be discarded yet

```text
$3062/$3068/$306E/$306F
← external 306x board register writes/status
→ likely force-motor/output/ASIC-adjacent path from source comments
→ keep as test items until board trace proves unused for minimal TBI manual OS
```