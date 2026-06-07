#!/usr/bin/env python3
"""Build the 7427 hardware-access map from a repo checkout.

Default paths are repo-relative so this can run from a normal clone:

    python tools/build_hw_map.py

Override paths as needed, for example:

    python tools/build_hw_map.py \
      --source source/31/BMHM_HAC_ORG_7100_to_end.asm \
      --out-full maps/full/hardware_access_map_v0.3.csv \
      --out-contract docs/ASIC_HARDWARE_REGISTER_CONTRACT.md \
      --out-graph docs/VARIABLE_DEPENDENCY_GRAPH.md \
      --out-summary docs/STATIC_ANALYSIS_SUMMARY.md
"""

import argparse
import re, csv, json, html
from pathlib import Path
from collections import defaultdict, Counter


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repo_path(value: str | Path) -> Path:
    value = Path(value)
    if value.is_absolute():
        return value
    return repo_root() / value


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description='Build static 7427 hardware access maps from source listing.')
    ap.add_argument('--source', default='source/31/BMHM_HAC_ORG_7100_to_end.asm', help='source ASM/listing input')
    ap.add_argument('--out-full', default='maps/full/hardware_access_map_v0.3.csv', help='full CSV output')
    ap.add_argument('--out-hw', default='maps/current/hardware_access_map_hw_only.csv', help='hardware-only CSV output')
    ap.add_argument('--out-contract', default='docs/ASIC_HARDWARE_REGISTER_CONTRACT.md', help='hardware contract markdown output')
    ap.add_argument('--out-graph', default='docs/VARIABLE_DEPENDENCY_GRAPH.md', help='dependency graph markdown output')
    ap.add_argument('--out-summary', default='docs/STATIC_ANALYSIS_SUMMARY.md', help='summary markdown output')
    ap.add_argument('--version', default='v0.3', help='analysis version label for generated docs')
    return ap.parse_args()


args = parse_args()
SRC = repo_path(args.source)
OUTCSV = repo_path(args.out_full)
OUTHW = repo_path(args.out_hw)
OUTMD = repo_path(args.out_contract)
OUTGRAPH = repo_path(args.out_graph)
OUTSUMMARY = repo_path(args.out_summary)
VERSION = args.version

for output_path in (OUTCSV, OUTHW, OUTMD, OUTGRAPH, OUTSUMMARY):
    output_path.parent.mkdir(parents=True, exist_ok=True)

if not SRC.exists():
    raise SystemExit(f'source file not found: {SRC}')

text = SRC.read_text(errors='replace')
lines = text.splitlines()

line_re = re.compile(r'^\s*([0-9A-F]{4}):\s*(?:(L[0-9A-F]{4})\s+)?([A-Z][A-Z0-9/]*|\*{3,5})?\s*(.*)$')
org_re = re.compile(r'\bORG\s+\$([0-9A-F]{4})')

# HC11F1/GM relocated register quick names; exactness varies by mask/comment.
REG_NAMES = {
    0x3000:'PORTA / timer pin status', 0x3001:'PIOC', 0x3002:'PORTC', 0x3003:'PORTB',
    0x3004:'PORTCL', 0x3005:'DDRC', 0x3006:'PORTD', 0x3007:'DDRD', 0x3008:'PORTE / ADC input port',
    0x3009:'CFORC/Timer force compare candidate', 0x300A:'OC1M candidate', 0x300B:'CFORC / compare force',
    0x300C:'OC1D candidate', 0x300D:'TCNT high? candidate', 0x300E:'TCNT 16-bit free-running counter',
    0x3010:'TIC1', 0x3012:'TIC2', 0x3014:'TIC3', 0x3016:'TOC1', 0x3018:'TOC2',
    0x301A:'TOC3', 0x301C:'TOC4 compare', 0x301E:'TOC5/TIC4 compare',
    0x3020:'TCTL1 output compare action', 0x3021:'TCTL2 input capture edge', 0x3022:'TMSK1 timer interrupt mask',
    0x3023:'TFLG1 timer interrupt flags / write-one-clear', 0x3024:'TMSK2 timer prescale/RTI mask',
    0x3025:'TFLG2 timer flags', 0x3026:'PACTL pulse accumulator control', 0x3027:'PACNT pulse accumulator count',
    0x3028:'SPCR SPI control', 0x3029:'SPSR SPI status', 0x302A:'SPDR SPI data', 0x302B:'BAUD SCI baud',
    0x302C:'SCCR1 SCI control 1', 0x302D:'SCCR2 SCI control 2', 0x302E:'SCSR SCI status', 0x302F:'SCDR SCI data',
    0x3030:'ADCTL A/D control', 0x3031:'ADR1 A/D result 1', 0x3032:'ADR2 A/D result 2', 0x3033:'ADR3 A/D result 3',
    0x3034:'ADR4 A/D result 4', 0x3035:'BPROT EEPROM block protect', 0x3038:'OPT2', 0x3039:'OPTION',
    0x303A:'COPRST watchdog clear', 0x303B:'PPROG EEPROM program', 0x303D:'INIT register relocation', 0x303F:'CONFIG/EPROM config candidate',
    0x3062:'External 306x hardware latch/status candidate', 0x3068:'External 306x output command candidate',
    0x306E:'External 306x I/O latch candidate', 0x306F:'External 306x I/O latch/status candidate',
    0x3FC0:'ASIC last DRP/ref period counter', 0x3FC4:'ASIC period/status latch candidate',
    0x3FC8:'ASIC timing/status candidate', 0x3FCA:'ASIC 16-bit RPM/event counter',
    0x3FCC:'ASIC fuel/scheduler command candidate A', 0x3FCE:'ASIC EFI PW / fuel pulse-width handoff',
    0x3FD4:'ASIC output compare/scheduler slot D4', 0x3FD6:'ASIC output compare/scheduler slot D6',
    0x3FD8:'ASIC output compare/scheduler slot D8', 0x3FDA:'ASIC output compare/scheduler slot DA',
    0x3FDC:'ASIC spark dwell / spark work period handoff', 0x3FE0:'ASIC timing/status candidate E0',
    0x3FE4:'ASIC ignition/output companion write', 0x3FE6:'ASIC spark handoff path', 0x3FE8:'ASIC EST/spark timing output engine',
    0x3FEA:'ASIC fuel/scheduler command candidate B', 0x3FEC:'ASIC hardware status/source',
    0x3FF2:'ASIC output/scheduler candidate', 0x3FF6:'ASIC EST fall counter / output scheduler',
    0x3FFA:'ASIC packed hardware status', 0x3FFC:'ASIC I/O D port / external output latch',
}

STORE = {'STAA':'A','STAB':'B','STD':'D','STS':'SP','STX':'X','STY':'Y'}
LOAD = {'LDAA':'A','LDAB':'B','LDD':'D','LDS':'SP','LDX':'X','LDY':'Y'}
CMP = {'CMPA':1,'CMPB':1,'CPD':2,'CPX':2,'CPY':2,'BITA':1,'BITB':1,'TST':1,'TSTA':0,'TSTB':0,'CBA':0}
ALU = {'ADDA':1,'ADDB':1,'ADDD':2,'SUBA':1,'SUBB':1,'SUBD':2,'ANDA':1,'ANDB':1,'ORAA':1,'ORAB':1,'EORA':1,'EORB':1,'ABA':0}
RMW = {'INC','DEC','CLR','COM','NEG','ASL','LSL','LSR','ROL','ROR','ASR'}
BITRMW = {'BSET','BCLR'}
BITREAD = {'BRSET','BRCLR'}
EXEC = {'JSR','JMP'}
WIDTH2 = {'LDD','STD','LDX','LDY','LDS','STS','STX','STY','CPD','CPX','CPY','ADDD','SUBD'}

parsed=[]
labels={}
current_org=None
for i,line in enumerate(lines,1):
    morg=org_re.search(line)
    if morg:
        current_org=int(morg.group(1),16)
    m=line_re.match(line)
    if not m: continue
    pc_s,label,mn,rest=m.groups()
    if not mn: continue
    # Split comment preserving source comment.
    code_rest=rest
    comment=''
    if ';' in code_rest:
        code_rest, comment = code_rest.split(';',1)
        comment=comment.strip()
    operand=code_rest.strip()
    pc=int(pc_s,16)
    if label: labels[label]=pc
    parsed.append({'lineno':i,'pc':pc,'pc_s':pc_s,'label':label or '', 'mnemonic':mn.strip(), 'operand':operand, 'comment':comment, 'raw':line.rstrip(), 'org':current_org})

# collect direct callers through JSR/JMP to labels
callers=defaultdict(list)
exec_targets=set()
for p in parsed:
    mn=p['mnemonic']
    if mn in EXEC:
        op=p['operand'].split()[0].split(',')[0] if p['operand'] else ''
        mt=re.match(r'(L[0-9A-F]{4})\b',op)
        if mt:
            lab=mt.group(1); exec_targets.add(lab); callers[lab].append(f"0x{p['pc']:04X}")
# force known interrupt/vector entry labels/ranges to routine starts
for lab in ['L74EA','L7875','L78D9','L793D','LF7EA','LFC09','LFC11','LFC2F','LCE7C','LCE7C']:
    if lab in labels: exec_targets.add(lab)

# assign current routine as latest label that is a JSR/JMP target or first label after ORG
current_routine='L7100'
for p in parsed:
    if p['label'] and (p['label'] in exec_targets or p['label']=='L7100'):
        current_routine=p['label']
    p['routine']=current_routine

# interrupt context ranges based on comments and known vector handlers in source
INT_RANGES = [
    (0x74EA,0x77C6,'IRQ/DRP/ref interrupt'),
    (0x77C7,0x7826,'IRQ-called fuel timer setup helper'),
    (0x7875,0x78D8,'TOC5/TIC4 interrupt'),
    (0x78D9,0x793C,'TOC4 interrupt'),
    (0x793D,0x7A84,'TOC3/6.25ms major-loop interrupt'),
    (0xCE7C,0xCEE0,'TOC1 knock-window interrupt'),
    (0xF7EA,0xF821,'SCI/ALDL interrupt'),
    (0xFC09,0xFC2E,'XIRQ/vector handler'),
    (0xFC2F,0xFC60,'TIC/RTI vector handler'),
]
def interrupt_context(pc):
    for a,b,name in INT_RANGES:
        if a<=pc<=b: return name
    return 'mainline/unknown'

def parse_hexnum(tok):
    tok=tok.strip()
    tok=tok.replace('#','')
    if tok.startswith('$'):
        try: return int(tok[1:],16)
        except: return None
    if tok.startswith('L') and re.fullmatch(r'L[0-9A-F]{4}',tok):
        return int(tok[1:],16)
    if re.fullmatch(r'[0-9]+',tok):
        return int(tok,10)
    if re.fullmatch(r'[0-9A-F]{4}',tok):
        return int(tok,16)
    return None

def split_operands(op):
    # Simple split is safe enough for 68HC11 operands here.
    return [x.strip() for x in op.split(',') if x.strip()]

def address_class(addr, mnemonic=None):
    if addr is None: return ''
    if mnemonic in {'JSR','JMP'} and addr >= 0x1000:
        return 'ROM_TABLE'
    if 0x1000 <= addr <= 0x103F:
        return 'HC11_REG'
    if 0x1800 <= addr <= 0x1FFF:
        return 'ROM_TABLE'
    if 0x302B <= addr <= 0x302F:
        return 'ALDL'
    if 0x3000 <= addr <= 0x303F:
        return 'HC11_REG'
    if 0x3060 <= addr <= 0x30FF:
        return 'UNKNOWN_HW'
    if 0x3F00 <= addr <= 0x3FFF:
        return 'ASIC_3FXX'
    if 0x0000 <= addr <= 0x03FF:
        return 'DIRECT_RAM'
    if 0x0400 <= addr <= 0x0FFF:
        return 'EXT_RAM'
    if 0x4000 <= addr <= 0xFFFF:
        return 'ROM_TABLE'
    return 'UNKNOWN_HW'

def reg_name(addr):
    return REG_NAMES.get(addr,'')

def parse_addr_operand(op0, regs):
    op0=op0.strip()
    # indexed: $1E,X or 0,X or L0009,X
    mix=re.fullmatch(r'([^,]+)\s*,\s*([XY])',op0)
    if mix:
        off_s, r=mix.groups()
        off=parse_hexnum(off_s)
        base=regs.get(r)
        if base is not None and off is not None:
            return base+off, f"{r}=0x{base:04X}", 'indexed_resolved'
        return None, f"{r}={('unknown' if base is None else hex(base))}", 'indexed_unresolved'
    # reject immediates and pure CPU registers
    if not op0 or op0.startswith('#') or op0 in {'A','B','D','X','Y','SP','CCR'}:
        return None,'','none'
    # direct/extended Lxxxx or $xxxx or decimal constants as addresses when not branch immediates
    val=parse_hexnum(op0)
    if val is not None:
        return val,'','direct_or_extended'
    return None,'','unparsed'

def first_addr_operand(ops):
    if not ops:
        return ''
    if len(ops) >= 2 and ops[1] in {'X','Y'}:
        return ops[0] + ',' + ops[1]
    return ops[0]

def bitmask_from_operands(ops):
    idx = 2 if len(ops) >= 3 and ops[1] in {'X','Y'} else 1
    if len(ops)>idx and ops[idx].startswith('#'):
        val=parse_hexnum(ops[idx])
        if val is not None: return f"0x{val:02X}"
    return ''

def width_for(mn):
    if mn in WIDTH2: return 16
    if mn in BITRMW or mn in BITREAD: return 'bit'
    if mn in RMW or mn in STORE or mn in LOAD or mn in CMP or mn in ALU: return 8
    return ''

def update_const_after(p, regs, vals):
    mn=p['mnemonic']; ops=split_operands(p['operand'])
    # Loads of immediate constants.
    if mn in LOAD:
        target=LOAD[mn]
        if ops and ops[0].startswith('#'):
            val=parse_hexnum(ops[0])
            if target in {'X','Y'}:
                regs[target]=val
            elif target=='A': vals['A']=val; vals['D']=None
            elif target=='B': vals['B']=val; vals['D']=None
            elif target=='D': vals['D']=val; vals['A']=(val>>8)&0xFF if val is not None else None; vals['B']=val&0xFF if val is not None else None
        else:
            if target in {'X','Y'}: regs[target]=None
            elif target in {'A','B','D'}:
                vals[target]=None
                if target in {'A','B'}: vals['D']=None
    elif mn=='CLRA': vals['A']=0; vals['D']=None
    elif mn=='CLRB': vals['B']=0; vals['D']=None
    elif mn=='CLR': pass
    elif mn in {'TAB'}:
        vals['B']=vals.get('A'); vals['D']=None
    elif mn in {'TBA'}:
        vals['A']=vals.get('B'); vals['D']=None
    elif mn in {'XGDX'}:
        # Swap D and X if both known.
        d=vals.get('D'); x=regs.get('X')
        vals['D']=x; regs['X']=d
        if vals['D'] is not None: vals['A']=(vals['D']>>8)&0xFF; vals['B']=vals['D']&0xFF
    elif mn in ALU or mn in {'MUL','LSLD','ASLD','LSRD','ASRD','IDIV','FDIV'}:
        vals['A']=vals['B']=vals['D']=None
    elif mn in STORE or mn in CMP or mn in BITRMW or mn in BITREAD or mn in RMW or mn in EXEC:
        pass
    else:
        # Unknown arithmetic/control may clobber A/B/D, but don't clobber X/Y unless explicit.
        pass

def source_for_store(mn, vals):
    reg=STORE[mn]
    val=vals.get(reg)
    if val is None: return reg
    if reg in {'A','B'}: return f"{reg}=0x{val:02X}"
    if reg=='D': return f"D=0x{val:04X}"
    return reg

# crude semantic engine state tags from comments/routine regions
def engine_state(p):
    c=(p['comment']+' '+p['raw']).lower()
    tags=[]
    for key,tag in [('crank','CRANK'),('run fuel','RUN'),('idle','IDLE'),('dfco','DFCO'),('aldl','ALDL'),('sci','SCI'),('spark','SPARK'),('est','EST'),('fuel','FUEL_CALC')]:
        if key in c and tag not in tags: tags.append(tag)
    return '|'.join(tags)

regs={'X':None,'Y':None}
vals={'A':None,'B':None,'D':None}
rows=[]
for p in parsed:
    pc=p['pc']; mn=p['mnemonic']; ops=split_operands(p['operand'])
    access_type=''; addr=None; xb=''; confidence=''; bitmask=''; value_source=''; width=''; notes=[]
    addr_status=''
    include=False
    if mn in STORE:
        access_type='W'; width=width_for(mn); value_source=source_for_store(mn, vals); include=True
        if ops: addr,xb,addr_status=parse_addr_operand(first_addr_operand(ops),regs)
    elif mn in LOAD:
        # include memory reads only; immediate loads only if they set X/Y base? no row.
        if ops and not ops[0].startswith('#'):
            access_type='R'; width=width_for(mn); value_source='memory'; include=True
            addr,xb,addr_status=parse_addr_operand(first_addr_operand(ops),regs)
    elif mn in BITRMW:
        access_type='RMW'; width='bit'; bitmask=bitmask_from_operands(ops); value_source=('set '+bitmask if mn=='BSET' else 'clear '+bitmask); include=True
        if ops: addr,xb,addr_status=parse_addr_operand(first_addr_operand(ops),regs)
    elif mn in BITREAD:
        access_type='R'; width='bit'; bitmask=bitmask_from_operands(ops); value_source='bit test '+bitmask; include=True
        if ops: addr,xb,addr_status=parse_addr_operand(first_addr_operand(ops),regs)
    elif mn in RMW:
        access_type='RMW'; width=8; value_source=mn; include=True
        if ops: addr,xb,addr_status=parse_addr_operand(first_addr_operand(ops),regs)
        else: include=False
    elif mn in CMP or mn in ALU:
        if ops and not ops[0].startswith('#'):
            access_type='R'; width=width_for(mn); value_source=mn; include=True
            addr,xb,addr_status=parse_addr_operand(first_addr_operand(ops),regs)
    elif mn in EXEC:
        access_type='EXEC'; width=''; value_source='control transfer'; include=True
        if ops: addr,xb,addr_status=parse_addr_operand(first_addr_operand(ops),regs)
    # Special: PC 715B loop clears $3FC0-$3FF8 by STD 0,X with X initialized $3FC0 and increments twice until $3FFA.
    if include:
        effective = ''
        if p['pc']==0x715B and mn=='STD':
            effective='0x3FC0-0x3FF8'
            addr_class='ASIC_3FXX'
            notes.append('loop clears even ASIC words from $3FC0 through before $3FFA')
            confidence='medium_range_inferred'
        elif addr is not None:
            effective=f"0x{addr:04X}"
            addr_class=address_class(addr,mn)
            confidence='high' if addr_status in {'indexed_resolved','direct_or_extended'} else 'medium'
        else:
            effective=p['operand']
            addr_class='UNKNOWN_HW' if 'X' in p['operand'] or 'Y' in p['operand'] else ''
            confidence='low_unresolved'
        rn=reg_name(addr) if isinstance(addr,int) else ''
        if rn: notes.append(rn)
        if p['comment']: notes.append(p['comment'])
        if addr_status and 'indexed' in addr_status: notes.append(addr_status)
        call_list=';'.join(callers.get(p['routine'],[])[:12])
        if len(callers.get(p['routine'],[]))>12: call_list+=';...'
        rows.append({
            'pc':f"0x{pc:04X}",
            'bank/page':'BMHM_$31_main_window_ORG_'+(f"0x{p['org']:04X}" if p['org'] else ''),
            'opcode':'source_listing_no_bytes',
            'mnemonic': (mn + ((' '+p['operand']) if p['operand'] else '')).strip(),
            'access_type':access_type,
            'effective_address':effective,
            'address_class':addr_class,
            'width':width,
            'bitmask':bitmask,
            'value_source':value_source,
            'x_base/y_base':xb,
            'routine_label':p['routine'],
            'interrupt_context':interrupt_context(pc),
            'callers':call_list,
            'engine_state_seen':engine_state(p),
            'notes':' | '.join(notes),
            'confidence':confidence,
        })
    # Update tracker after row emission to reflect source line effects.
    update_const_after(p, regs, vals)


def hex_to_int(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text or '-' in text:
        return None
    if text.lower().startswith('0x'):
        text = text[2:]
    if text.startswith('$'):
        text = text[1:]
    try:
        return int(text, 16)
    except ValueError:
        return None


def subsystem_for(row):
    notes = str(row.get('notes', '')).lower()
    ea = str(row.get('effective_address', ''))
    addr = hex_to_int(ea)

    if addr in (0x301C,0x301D,0x301E,0x301F,0x3020,0x3022,0x3023): return 'FUEL_SCHED_TIMER'
    if addr in (0x3016,0x3017,0x3062,0x3FDC,0x3FE4,0x3FE6,0x3FE8,0x3FF6): return 'SPARK_EST'
    if addr in (0x3030,0x3031,0x3032,0x3033,0x3034,0x3008): return 'SENSOR_ADC'
    if addr in (0x302D,0x302E,0x302F): return 'ALDL_SCI'
    if addr in (0x303A,0x3039,0x3038,0x303F,0x3024,0x3000): return 'BOOT_WATCHDOG_CPU'
    if addr in (0x3FC0,0x3FC2,0x3FC4,0x3FC6,0x3FC8,0x3FCA,0x3FEC,0x3FFA): return 'ASIC_STATUS_REF'
    if addr in (0x3FCC,0x3FCE,0x3FD4,0x3FD6,0x3FD8,0x3FDA,0x3FEA): return 'ASIC_COMMAND_OUTPUT'
    if addr in (0x3FFC,0x3068,0x306E,0x306F): return 'IO_LATCH_OUTPUT'
    if any(k in notes for k in ['iac','idle air']): return 'IDLE_IAC'
    if any(k in notes for k in ['bpw','fuel','inject']): return 'FUEL_MATH_HANDOFF'
    if any(k in notes for k in ['spark','est','ignition','knock']): return 'SPARK_EST'
    if any(k in notes for k in ['sci','aldl','serial']): return 'ALDL_SCI'
    if any(k in notes for k in ['a/d','adc','map','tps','cool','battery']): return 'SENSOR_ADC'
    if addr is not None and 0x3060 <= addr <= 0x307F: return 'UNKNOWN_306X_BOARD_IO'
    if addr is not None and 0x3F00 <= addr <= 0x3FFF: return 'ASIC_UNKNOWN'
    if addr is not None and 0x3000 <= addr <= 0x303F: return 'HC11_CORE'
    return 'OTHER'


def minimal_required_for(subsystem):
    if subsystem in {'FUEL_SCHED_TIMER','SPARK_EST','SENSOR_ADC','ALDL_SCI','BOOT_WATCHDOG_CPU','ASIC_STATUS_REF','ASIC_COMMAND_OUTPUT','IO_LATCH_OUTPUT','IDLE_IAC'}:
        return 'YES'
    if subsystem in {'UNKNOWN_306X_BOARD_IO','ASIC_UNKNOWN'}:
        return 'TEST_ITEM'
    return 'NO_UNLESS_DEPENDENCY_PROVES'


def risk_for(row):
    required = row.get('minimal_os_required', '')
    access = row.get('access_type', '')
    if required == 'YES' and access in {'W','RMW'}:
        return 'HIGH'
    if required == 'YES':
        return 'MEDIUM'
    if required == 'TEST_ITEM':
        return 'HIGH_UNCLASSIFIED'
    return 'LOW'

# Add v0.2/v0.3 classification columns before writing outputs.
for row in rows:
    row['subsystem'] = subsystem_for(row)
    row['minimal_os_required'] = minimal_required_for(row['subsystem'])
    row['risk'] = risk_for(row)

# Filter down? User requested hardware access map including direct RAM / ROM table too. Keep all classes.
fieldnames=['pc','bank/page','opcode','mnemonic','access_type','effective_address','address_class','subsystem','minimal_os_required','risk','width','bitmask','value_source','x_base/y_base','routine_label','interrupt_context','callers','engine_state_seen','notes','confidence']
with OUTCSV.open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=fieldnames)
    w.writeheader(); w.writerows(rows)

hardware_classes = {'HC11_REG','ALDL','ASIC_3FXX','UNKNOWN_HW'}
hardware_rows = [r for r in rows if r['address_class'] in hardware_classes]
with OUTHW.open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=fieldnames)
    w.writeheader(); w.writerows(hardware_rows)

# Aggregations for contract
hardware_classes={'HC11_REG','ASIC_3FXX','UNKNOWN_HW','ALDL'}
by_addr=defaultdict(list)
for r in rows:
    if r['address_class'] in hardware_classes and r['effective_address'].startswith('0x'):
        by_addr[r['effective_address']].append(r)

def access_summary(rs):
    return ', '.join(f"{k}:{v}" for k,v in Counter(r['access_type'] for r in rs).items())

def pcs(rs, maxn=28):
    vals=[r['pc'] for r in rs]
    return ', '.join(vals[:maxn]) + (', ...' if len(vals)>maxn else '')

def const_writes(rs):
    vals=[]
    for r in rs:
        if r['access_type'] in {'W','RMW'} and '=' in r['value_source']:
            vals.append(f"{r['pc']} {r['mnemonic']} ← {r['value_source']}")
    return '; '.join(vals[:8])

# Contract markdown
md=[]
md.append('# 7427 ASIC / Hardware Register Contract v0.1')
md.append('')
md.append('Generated from static source walk. This is not a dynamic proof; unknown or inferred meanings are marked as test items.')
md.append('')
for cls,title in [('HC11_REG','HC11 relocated registers'),('ALDL','SCI/ALDL registers'),('ASIC_3FXX','External ASIC / board registers'),('UNKNOWN_HW','Unknown external hardware / board register space')]:
    md.append(f'## {title}')
    md.append('')
    md.append('| Address | Name / hypothesis | Accesses | First PCs | Constant writes / source hints | Contract status |')
    md.append('|---|---|---:|---|---|---|')
    for addr,rs in sorted(by_addr.items(), key=lambda kv: kv[0]):
        if not rs or rs[0]['address_class']!=cls: continue
        name=''
        # for ranges, use notes
        if '-' not in addr:
            try: name=REG_NAMES.get(int(addr,16),'')
            except: name=''
        if not name:
            n=[r['notes'] for r in rs if r['notes']]
            name=(n[0][:90] if n else '')
        status='KEEP / required until bench proven otherwise'
        if cls=='UNKNOWN_HW': status='TEST ITEM: classify before removal'
        if cls=='ASIC_3FXX' and addr not in ['0x3FCE','0x3FDC','0x3FE6','0x3FE8','0x3FF6','0x3FFC','0x3FCA','0x3FFA','0x3FC0','0x3FEC']:
            status='Likely ASIC config/status; trace before minimal OS removal'
        md.append(f'| `{addr}` | {name} | {access_summary(rs)} | {pcs(rs,10)} | {const_writes(rs)} | {status} |')
    md.append('')
OUTMD.write_text('\n'.join(md),encoding='utf-8')

# Variable/dependency graph markdown: manually distilled from rows.
g=[]
g.append('# 7427 Variable Dependency Graph v0.1')
g.append('')
g.append('Static dependency sketch. Dynamic bus trace still required for side effects and units.')
g.append('')
g.append('## Fuel pulsewidth path')
g.append('')
g.append('```text')
g.append('L02CF BPW')
g.append('← calculated run/crank base pulsewidth')
g.append('← VE / MAP / RPM / CTS / AFR modifiers / transient fuel')
g.append('')
g.append('L024C/L024E sync BPW')
g.append('← L02CF and sync/async mode logic')
g.append('← crank mode all-injectors-each-DRP branch')
g.append('')
g.append('L0254 async BPW')
g.append('← async fuel decision logic')
g.append('← AE / transient fuel handling')
g.append('')
g.append('L0250 working BPW')
g.append('← selected sync/async BPW')
g.append('← low-BPW correction')
g.append('← BPW bias L0256')
g.append('← min/max clamps')
g.append('')
g.append('HC11 TOC4/TOC5 compare values $301C/$301E')
g.append('← L0250 plus timer state')
g.append('← output compare setup $3020/$3022/$3023')
g.append('```')
g.append('')
g.append('## Fuel ASIC handoff path')
g.append('')
g.append('```text')
g.append('$3FCE EFI PW / fuel handoff writes @ $8426/$8512/$FAEE/$FB44')
g.append('← L024E/L0254/L0250 fuel pulse state')
g.append('← async/sync mode decision')
g.append('← low-BPW thresholds L492A/L492C/L4974')
g.append('← final fuel math and AE/DFCO gating')
g.append('```')
g.append('')
g.append('## Spark / EST path')
g.append('')
g.append('```text')
g.append('$3FE8 spark/EST timing write @ $ABAA')
g.append('← D = computed EST event time')
g.append('← L3FF6 EST fall counter and L3FC0 ref period timing')
g.append('← spark/dwell work variables around LAB8E-LABC8')
g.append('← final spark advance L01FD')
g.append('← base spark table $4166 or $428A')
g.append('← idle spark correction tables around $4502/$451B')
g.append('← coolant spark, altitude spark, low-octane retard, EGR spark correction, startup spark')
g.append('← MAP/RPM/TPS/CTS/VSS/state flags')
g.append('```')
g.append('')
g.append('```text')
g.append('$3FE6 spark handoff write @ $ABBA')
g.append('← D = timing/dwell companion value')
g.append('← L3FDC spark dwell/work period')
g.append('← same final spark/timing basis as $3FE8')
g.append('```')
g.append('')
g.append('```text')
g.append('$3FDC spark dwell/work period @ $ABC0/$FAF7')
g.append('← X/D work value from EST scheduling math')
g.append('← dwell/spark timing counters and startup/default paths')
g.append('```')
g.append('')
g.append('## RPM/ref timing input')
g.append('')
g.append('```text')
g.append('$3FC0 last DRP/ref period counter reads')
g.append('← ASIC/ref hardware')
g.append('→ RPM calculation L0062/L0063/L0068/L006A')
g.append('→ spark timing, fuel scheduling, idle logic, derivative RPM correction')
g.append('```')
g.append('')
g.append('```text')
g.append('$3FCA RPM/event counter reads')
g.append('← ASIC/ref hardware')
g.append('→ initialization/run counter L0205 and runtime RPM/event logic')
g.append('```')
g.append('')
g.append('## IAC / external output latch path')
g.append('')
g.append('```text')
g.append('$3FFC I/O D port writes')
g.append('← constants/mode-selected port images, e.g. $B93A/$B91A during init')
g.append('← ALDL/SCI and hardware output handshakes')
g.append('← likely external output latch state; exact IAC phase ownership still needs isolation')
g.append('```')
g.append('')
g.append('## ALDL/debug')
g.append('')
g.append('```text')
g.append('$302D SCCR2, $302E SCSR, $302F SCDR')
g.append('← ALDL message state L0360-L036C')
g.append('← SCI interrupt handler LF7EA/LF90B/LF822')
g.append('→ debug frame TX/RX and RAM/ROM read service')
g.append('```')
g.append('')
g.append('## Unknown hardware that cannot be discarded yet')
g.append('')
g.append('```text')
g.append('$3062/$3068/$306E/$306F')
g.append('← external 306x board register writes/status')
g.append('→ likely force-motor/output/ASIC-adjacent path from source comments')
g.append('→ keep as test items until board trace proves unused for minimal TBI manual OS')
g.append('```')
OUTGRAPH.write_text('\n'.join(g),encoding='utf-8')

# Summary
cnt=Counter(r['address_class'] for r in rows)
hwcnt=len(hardware_rows)
asic_addrs=sorted({r['effective_address'] for r in rows if r['address_class']=='ASIC_3FXX'})
hc11_addrs=sorted({r['effective_address'] for r in rows if r['address_class'] in {'HC11_REG','ALDL'}})
unknown_hw=sorted({r['effective_address'] for r in rows if r['address_class']=='UNKNOWN_HW' and r['effective_address'].startswith('0x')})
sm=[]
sm.append(f'# 7427 Static Analysis Summary {VERSION}')
sm.append('')
sm.append(f'- Parsed source lines: {len(lines)}')
sm.append(f'- Parsed instruction rows: {len(parsed)}')
sm.append(f'- Hardware/direct/ROM access rows emitted: {len(rows)}')
sm.append(f'- Hardware-facing rows emitted: {hwcnt}')
sm.append('')
sm.append('## Address class counts')
for k,v in cnt.most_common(): sm.append(f'- {k or "UNCLASSIFIED"}: {v}')
sm.append('')
sm.append(f'## ASIC addresses/ranges found ({len(asic_addrs)})')
sm.append(', '.join(asic_addrs))
sm.append('')
sm.append(f'## HC11/ALDL addresses found ({len(hc11_addrs)})')
sm.append(', '.join(hc11_addrs))
sm.append('')
sm.append(f'## UNKNOWN_HW addresses/ranges found ({len(unknown_hw)})')
sm.append(', '.join(unknown_hw))
sm.append('')
sm.append('## Highest-priority next traces')
sm.append('1. Prove `$3FCE` EFI pulsewidth handoff first; scope injector output while forcing known values.')
sm.append('2. Passive observer log of `$301C/$301E/$3020/$3022/$3023` only if `$3FCE` alone does not explain injector pulse behavior.')
sm.append('3. Passive observer log of `$3FDC/$3FE6/$3FE8/$3FF6` to prove spark handoff units and write order.')
sm.append('4. Passive observer log of `$3FFC` and `$306x` writes to separate IAC/port/force-motor/trans leftovers.')
sm.append('5. SCI/ALDL preservation check for `$302D/$302E/$302F` before adding debug export frames.')
OUTSUMMARY.write_text('\n'.join(sm),encoding='utf-8')

print(json.dumps({
    'csv': str(OUTCSV), 'hw_csv': str(OUTHW), 'contract': str(OUTMD), 'graph': str(OUTGRAPH), 'summary': str(OUTSUMMARY),
    'rows': len(rows), 'parsed': len(parsed), 'counts': cnt, 'hardware_rows': hwcnt,
    'asic_addresses': asic_addrs, 'hc11_addresses': hc11_addrs, 'unknown_hw': unknown_hw,
}, indent=2, default=lambda o: dict(o) if hasattr(o,'items') else str(o)))
