#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
import re, zipfile, shutil, os, textwrap
base=Path('/mnt/data')
df=pd.read_csv(base/'7427_Hardware_Access_Map_v0.1.csv')

def hx(x):
    if pd.isna(x): return None
    s=str(x)
    if '-' in s: return None
    try: return int(s,16)
    except: return None

def subsystem(row):
    notes=str(row.get('notes','')).lower()
    ea=str(row.get('effective_address',''))
    pc=hx(row.get('pc'))
    addr=hx(ea)
    mnem=str(row.get('mnemonic','')).upper()
    # direct known addresses
    if addr in (0x301C,0x301D,0x301E,0x301F,0x3020,0x3022,0x3023): return 'FUEL_SCHED_TIMER'
    if addr in (0x3016,0x3017,0x3062,0x3FDC,0x3FE4,0x3FE6,0x3FE8,0x3FF6): return 'SPARK_EST'
    if addr in (0x3030,0x3031,0x3032,0x3033,0x3034,0x3008): return 'SENSOR_ADC'
    if addr in (0x302D,0x302E,0x302F): return 'ALDL_SCI'
    if addr in (0x303A,0x3039,0x3038,0x303F,0x3024,0x3000): return 'BOOT_WATCHDOG_CPU'
    if addr in (0x3FC0,0x3FC2,0x3FC4,0x3FC6,0x3FC8,0x3FCA,0x3FEC,0x3FFA): return 'ASIC_STATUS_REF'
    if addr in (0x3FCC,0x3FCE,0x3FD4,0x3FD6,0x3FD8,0x3FDA): return 'ASIC_COMMAND_OUTPUT'
    if addr in (0x3FFC,0x3068,0x306E,0x306F): return 'IO_LATCH_OUTPUT'
    if any(k in notes for k in ['iac','idle air']): return 'IDLE_IAC'
    if any(k in notes for k in ['bpw','fuel','inject']): return 'FUEL_MATH_HANDOFF'
    if any(k in notes for k in ['spark','est','ignition','knock']): return 'SPARK_EST'
    if any(k in notes for k in ['sci','aldl','serial']): return 'ALDL_SCI'
    if any(k in notes for k in ['a/d','adc','map','tps','cool','battery']): return 'SENSOR_ADC'
    if addr is not None and 0x3060<=addr<=0x307F: return 'UNKNOWN_306X_BOARD_IO'
    if addr is not None and 0x3F00<=addr<=0x3FFF: return 'ASIC_UNKNOWN'
    if addr is not None and 0x3000<=addr<=0x303F: return 'HC11_CORE'
    return 'OTHER'

def minimal_req(row):
    ss=row['subsystem']
    addr=hx(row.get('effective_address',''))
    if ss in ['FUEL_SCHED_TIMER','SPARK_EST','SENSOR_ADC','ALDL_SCI','BOOT_WATCHDOG_CPU','ASIC_STATUS_REF','ASIC_COMMAND_OUTPUT','IO_LATCH_OUTPUT','IDLE_IAC']:
        return 'YES'
    if ss in ['UNKNOWN_306X_BOARD_IO','ASIC_UNKNOWN']:
        return 'TEST_ITEM'
    return 'NO_UNLESS_DEPENDENCY_PROVES'

def risk(row):
    ss=row['subsystem']
    acc=str(row.get('access_type',''))
    if row['minimal_os_required']=='YES' and acc in ['W','RMW']: return 'HIGH'
    if row['minimal_os_required']=='YES': return 'MEDIUM'
    if row['minimal_os_required']=='TEST_ITEM': return 'HIGH_UNCLASSIFIED'
    return 'LOW'

df['subsystem']=df.apply(subsystem, axis=1)
df['minimal_os_required']=df.apply(minimal_req, axis=1)
df['risk']=df.apply(risk, axis=1)
# reorder columns
cols=['pc','bank/page','opcode','mnemonic','access_type','effective_address','address_class','subsystem','minimal_os_required','risk','width','bitmask','value_source','x_base/y_base','routine_label','interrupt_context','callers','engine_state_seen','notes','confidence']
df=df[[c for c in cols if c in df.columns]]
df.to_csv(base/'7427_Hardware_Access_Map_v0.2.csv', index=False)
# hardware only
hw=df[df['address_class'].isin(['HC11_REG','ASIC_3FXX','UNKNOWN_HW','ALDL'])].copy()
hw.to_csv(base/'7427_Hardware_Access_Map_HW_Only_v0.2.csv', index=False)
# test items group
test=hw[hw['minimal_os_required'].isin(['YES','TEST_ITEM'])].copy()
# group by addr/subsystem
rows=[]
for addr,g in test.groupby('effective_address', dropna=False):
    acc='/'.join(sorted(set(map(str,g['access_type']))))
    pcs=', '.join(g['pc'].astype(str).head(20)) + (' ...' if len(g)>20 else '')
    notes=' | '.join([n for n in g['notes'].astype(str).head(3) if n!='nan'])
    rows.append({
        'address':addr,
        'address_class': ','.join(sorted(set(map(str,g['address_class'])))),
        'subsystem': ','.join(sorted(set(map(str,g['subsystem'])))),
        'accesses':acc,
        'count':len(g),
        'risk': ','.join(sorted(set(map(str,g['risk'])))),
        'minimal_os_required': ','.join(sorted(set(map(str,g['minimal_os_required'])))),
        'first_pcs':pcs,
        'test_objective': '',
        'bench_method': '',
        'notes':notes,
    })
tm=pd.DataFrame(rows).sort_values(['risk','address'], ascending=[False,True])
# fill test objective
for i,r in tm.iterrows():
    ss=r['subsystem']
    if 'FUEL_SCHED_TIMER' in ss: obj='Verify compare-write order, flag clear, interrupt enable, minimum lead time, and injector pin action.'
    elif 'SPARK_EST' in ss: obj='Verify EST/spark handoff units, latch timing, bypass relationship, and stale-write behavior.'
    elif 'ASIC_STATUS_REF' in ss: obj='Determine read semantics, event latch behavior, read/clear side effects, and relation to REF/RPM.'
    elif 'SENSOR_ADC' in ss: obj='Verify ADC channel select, conversion complete bit, result scaling, and allowed sampling order.'
    elif 'ALDL_SCI' in ss: obj='Verify SCI baud/control setup, RX/TX flags, interrupt/polling mode, and debug frame safety.'
    elif 'BOOT_WATCHDOG_CPU' in ss: obj='Verify required reset/init/watchdog sequence and failure behavior.'
    elif 'IO_LATCH_OUTPUT' in ss: obj='Identify physical output bits, latch behavior, write-triggered actions, and safe startup value.'
    else: obj='Classify unknown hardware behavior; prove required/not-required before removal.'
    tm.at[i,'test_objective']=obj
    tm.at[i,'bench_method']='Static trace + bench bus logger: capture PC,A/B/D,X/Y, address, value, timestamp during key-on/crank/idle/snap/decel.'
tm.to_csv(base/'7427_Hardware_Test_Matrix_v0.2.csv', index=False)

# subsystem summary md
summary=[]
summary.append('# 7427 Hardware Access Static Pass v0.2\n')
summary.append('Source: `$31` BMHM/HAC disassembly from ORG `$7100` through end. This is a static source-listing pass, not a dynamic proof.\n')
summary.append('## Counts\n')
summary.append(f'- Total access rows: `{len(df)}`\n')
summary.append(f'- Hardware-facing rows: `{len(hw)}`\n')
summary.append(f'- Minimal-OS required rows: `{(df.minimal_os_required=="YES").sum()}`\n')
summary.append(f'- Explicit test-item rows: `{(df.minimal_os_required=="TEST_ITEM").sum()}`\n')
summary.append('\n## Rows by subsystem\n\n')
summary.append(df['subsystem'].value_counts().to_markdown())
summary.append('\n\n## Hardware rows by address class\n\n')
summary.append(hw['address_class'].value_counts().to_markdown())
summary.append('\n\n## Immediate takeaways\n\n')
summary.append('- `$301C/$301E`, `$3020`, `$3022`, and `$3023` form the confirmed HC11 output-compare/timer side of the injector scheduler.\n')
summary.append('- `$3FCA`, `$3FFA`, and nearby `$3FCx/$3FEx` registers are the main ASIC/ref/status region needing dynamic logging.\n')
summary.append('- `$3FFC` is repeatedly used as an I/O/output latch during startup and fault paths; it must not be treated as passive RAM.\n')
summary.append('- `$306x` writes remain board/ASIC-adjacent unknowns. They are not removable until bench trace proves their physical output role.\n')
summary.append('- Fuel math can be redesigned later, but the timer compare/flag clear/enable order must be preserved until proven otherwise.\n')
(base/'7427_Static_Analysis_Summary_v0.2.md').write_text(''.join(summary))

# Minimal OS skeleton markdown
mos='''# 7427 Minimal OS Skeleton v0.1

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
'''
(base/'7427_Minimal_OS_Skeleton_v0.1.md').write_text(mos)

cal='''# 7427 Clean Calibration Layout v0.1

No transmission, TCC, EGR, EVAP, or emissions-side modifiers are included. Each calibration item has one intended purpose.

```asm
CAL_HEADER:
  OS_ID
  CAL_ID
  CAL_VERSION
  CHECKSUM
  FEATURE_FLAGS

SENSORS:
  MAP_SCALE
  TPS_SCALE
  CTS_SCALE
  BATT_SCALE
  VSS_SCALE

FUEL:
  IFR
  STOICH_AFR
  VE_MAIN_TABLE
  VE_IDLE_TABLE
  AFR_TARGET_IDLE
  AFR_TARGET_RUN
  AFR_TARGET_POWER
  WARMUP_ENRICH_VS_CTS
  CRANK_FUEL_VS_CTS
  AFTERSTART_ENRICH_VS_CTS
  AFTERSTART_DECAY
  AE_TPS_GAIN
  AE_MAP_GAIN
  AE_DECAY
  PE_MAP_THRESHOLD
  PE_TPS_THRESHOLD
  PE_AFR
  DFCO_ENABLE_RPM
  DFCO_DISABLE_RPM
  DFCO_MAP_THRESHOLD
  DFCO_TPS_THRESHOLD
  INJ_DEADTIME_VS_BATT
  INJ_LOW_PW_TRANSFER_TABLE
  MIN_EFFECTIVE_PW

SPARK:
  SPARK_MAIN_TABLE
  CRANK_SPARK
  IDLE_SPARK_BASE
  IDLE_SPARK_RPM_ERROR_GAIN
  COOLANT_SPARK_CORRECTION
  MIN_SPARK
  MAX_SPARK
  KNOCK_ENABLE
  KNOCK_RETARD_LIMIT

IDLE:
  TARGET_RPM_VS_CTS
  HOT_TARGET_RPM
  BASE_IAC_VS_CTS
  CRANK_IAC_VS_CTS
  IAC_RPM_ERROR_GAIN
  IAC_STEP_RATE
  DASHPOT_ENABLE
  DASHPOT_STEPS
  DASHPOT_DECAY
  FOLLOWER_ENABLE
  TPS_IDLE_THRESHOLD
  VSS_IDLE_THRESHOLD

DEBUG:
  ALDL_FRAME_SELECTOR
  DEBUG_CH0
  DEBUG_CH1
  DEBUG_CH2
  DEBUG_CH3
  DEBUG_FLAGS
```
'''
(base/'7427_Calibration_Layout_v0.1.md').write_text(cal)

# create repo scaffold
repo=base/'7427HWContract_repo_scaffold_v0.2'
if repo.exists(): shutil.rmtree(repo)
(repo/'docs').mkdir(parents=True)
(repo/'maps').mkdir()
(repo/'tools').mkdir()
(repo/'source').mkdir()
(repo/'tests').mkdir()
for src,dst in [
    ('7427_ASIC_Register_Contract_v0.1.md','docs/7427_ASIC_Register_Contract_v0.1.md'),
    ('7427_Variable_Dependency_Graph_v0.1.md','docs/7427_Variable_Dependency_Graph_v0.1.md'),
    ('7427_Static_Analysis_Summary_v0.2.md','docs/7427_Static_Analysis_Summary_v0.2.md'),
    ('7427_Minimal_OS_Skeleton_v0.1.md','docs/7427_Minimal_OS_Skeleton_v0.1.md'),
    ('7427_Calibration_Layout_v0.1.md','docs/7427_Calibration_Layout_v0.1.md'),
    ('7427_Hardware_Access_Map_v0.2.csv','maps/7427_Hardware_Access_Map_v0.2.csv'),
    ('7427_Hardware_Access_Map_HW_Only_v0.2.csv','maps/7427_Hardware_Access_Map_HW_Only_v0.2.csv'),
    ('7427_Hardware_Test_Matrix_v0.2.csv','tests/7427_Hardware_Test_Matrix_v0.2.csv'),
    ('build_hw_map.py','tools/build_hw_map.py'),
    ('build_v02_outputs.py','tools/build_v02_outputs.py'),
    ('31_HAC_from_ORG_7100_to_end_NOWRAP.asm','source/31_HAC_from_ORG_7100_to_end_NOWRAP.asm'),
]:
    shutil.copy(base/src, repo/dst)
readme='''# 7427HWContract

Reverse-engineering workspace for the GM 16197427 / 7427 PCM hardware contract.

Goal: extract the CPU-to-HC11-register / ASIC / timer / direct-RAM handoff contract from the `$31` BMHM/HAC source and use that contract to build a clean minimal speed-density TBI control OS.

Current artifacts:

- `maps/7427_Hardware_Access_Map_v0.2.csv`
- `maps/7427_Hardware_Access_Map_HW_Only_v0.2.csv`
- `docs/7427_ASIC_Register_Contract_v0.1.md`
- `docs/7427_Variable_Dependency_Graph_v0.1.md`
- `tests/7427_Hardware_Test_Matrix_v0.2.csv`
- `docs/7427_Minimal_OS_Skeleton_v0.1.md`
- `docs/7427_Calibration_Layout_v0.1.md`

Static analysis is not proof. Any engine-affecting unknown register must become a bench/runtime trace item before removal or replacement.
'''
(repo/'README.md').write_text(readme)
# zip scaffold and also outputs zip
for zipname, root in [('7427HWContract_repo_scaffold_v0.2.zip', repo)]:
    zp=base/zipname
    if zp.exists(): zp.unlink()
    with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
        for p in root.rglob('*'):
            z.write(p, p.relative_to(root.parent))
# output bundle (no parent dir)
files=['7427_Hardware_Access_Map_v0.2.csv','7427_Hardware_Access_Map_HW_Only_v0.2.csv','7427_Hardware_Test_Matrix_v0.2.csv','7427_Static_Analysis_Summary_v0.2.md','7427_Minimal_OS_Skeleton_v0.1.md','7427_Calibration_Layout_v0.1.md','build_v02_outputs.py']
zp=base/'7427HWContract_static_pass_v0.2.zip'
if zp.exists(): zp.unlink()
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files:
        z.write(base/f, f)
print('created v0.2 outputs')
print(df['subsystem'].value_counts().to_string())
