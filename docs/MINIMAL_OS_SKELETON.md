# 7427 Minimal OS Skeleton v0.1

This is a design skeleton, not runnable firmware. It exists to keep the clean OS organized around the extracted hardware contract instead of inheriting GM strategy baggage.

## Execution model

```text
RESET
  set stack
  relocate HC11 register block to $3000
  initialize HC11 core registers
  initialize ASIC/output latch safe state
  clear direct-page RAM
  initialize sensors and SCI/ALDL
  initialize timer compare framework
  initialize IAC state
  enable required interrupts
  enter MAIN_LOOP

MAIN_LOOP
  service_watchdog()
  sample_sensors()
  read_ref_rpm_status()
  resolve_engine_state()
  calculate_fuel()
  calculate_spark()
  calculate_idle_air()
  publish_output_handoffs()
  service_aldl_debug()
  repeat
```

## Required states

```text
CRANK  rpm < run_threshold
IDLE   tps_closed && rpm near idle && rolling_idle_valid
RUN    normal operating state
POWER  map > pe_map_threshold || tps > pe_tps_threshold
DECEL  tps_closed && rpm > idle && map low && vss moving
```

## Direct-page memory map

```text
$0000-$003F   fast flags / critical state
$0040-$007F   raw and filtered sensors
$0080-$00BF   fuel state
$00C0-$00FF   spark state
$0100-$013F   idle/IAC state
$0140-$017F   diagnostics/debug
$0180-$01FF   ALDL frame / scratch
```

## Fuel handoff contract placeholder

Do not install new fuel math until the injector scheduler contract is proven:

```text
BPW_final
  -> timer-unit conversion
  -> minimum lead-time clamp
  -> compare value = TCNT + delay
  -> clear TFLG1 bit
  -> arm TMSK1 bit
  -> write TOC4/TOC5 compare
```

## Spark handoff contract placeholder

Do not install new spark control until EST/ASIC handoff registers are classified:

```text
spark_final_degrees
  -> spark delay / dwell units
  -> EST/bypass state logic
  -> ASIC spark handoff register(s)
  -> verify latch/update timing
```

## IAC handoff contract placeholder

Do not install new IAC control until output phase/latch path is mapped:

```text
iac_target
  -> iac_present error
  -> step direction
  -> phase state
  -> output latch bits
  -> verify physical coil phase sequence
```
