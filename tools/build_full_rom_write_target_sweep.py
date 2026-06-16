#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,re
from collections import deque
from pathlib import Path
SOURCE=Path('source/31/BMHM_HAC_ORG_7100_to_end.asm')
OUT=Path('maps/generated/full_rom_write_target_sweep.csv')
WRITE_OPS={"STAA","STAB","STD","STS","STX","STY","BSET","BCLR","CLR","INC","DEC","COM","NEG","ASL","LSL","LSR","ROL","ROR"}
BRANCH_OPS={"BRA","BHI","BLS","BCC","BCS","BNE","BEQ","BVC","BVS","BPL","BMI","BGE","BLT","BGT","BLE","BRSET","BRCLR","JMP","JSR"}
LINE_RE=re.compile(r"^\s*([0-9A-Fa-f]{4}):\s*(?:(L[0-9A-Fa-f]{4})\s+)?([A-Z][A-Z0-9]*)\s*(.*?)\s*(?:;\s*(.*))?$")
IMM_RE=re.compile(r"^#\$([0-9A-Fa-f]{1,4})$")

def split_operands(s):
    if not s: return []
    out=[]; cur=''
    for part in s.split(','):
        p=part.strip()
        if p in {'X','Y'} and cur:
            cur += ','+p
        else:
            if cur: out.append(cur)
            cur=p
    if cur: out.append(cur)
    return out

def resolve_target(raw, xb, yb):
    raw=raw.strip(); status='direct'; address=''; sym=''; address_class='unknown'; xbase=''; ybase=''; ru=raw.upper()
    if ',' in ru:
        off,idx=ru.split(',',1); base = xb if idx=='X' else yb if idx=='Y' else None
        xbase=f'${xb:04X}' if xb is not None else ''; ybase=f'${yb:04X}' if yb is not None else ''
        if off.startswith('$') and base is not None:
            addr=(base+int(off[1:],16))&0xffff; address=f'${addr:04X}'; sym=f'L{addr:04X}'; status='resolved_indexed'
        elif off.startswith('$'):
            sym=ru; status='unresolved_indexed'
        else:
            sym=ru; status='unresolved_indexed'
    elif ru.startswith('$'):
        addr=int(ru[1:],16); address=f'${addr:04X}'; sym=f'L{addr:04X}'
    elif ru.startswith('L') and len(ru)==5:
        addr=int(ru[1:],16); address=f'${addr:04X}'; sym=ru
    else:
        sym=ru
    if address:
        a=int(address[1:],16)
        if 0x3000 <= a <= 0x30ff: address_class='hardware_register_region_30xx'
        elif 0x3f00 <= a <= 0x3fff: address_class='asic_hardware_region_3fxx'
        elif 0x0000 <= a <= 0x03ff: address_class='internal_ram'
        else: address_class='absolute_memory_or_table'
    return address,sym,address_class,status,xbase,ybase

def write_class(op):
    if op in {'STAA','STAB','STD','STS','STX','STY'}: return 'store'
    if op in {'BSET','BCLR'}: return 'bit_mutation'
    if op=='CLR': return 'clear'
    return 'read_modify_write'

def width(op):
    if op in {'STD','STS','STX','STY'}: return '16'
    if op in {'BSET','BCLR'}: return 'bit'
    return '8'

def value_source(op):
    return {'STAA':'A','STAB':'B','STD':'D','STS':'SP','STX':'X','STY':'Y','CLR':'zero','BSET':'bit_set_mask','BCLR':'bit_clear_mask','INC':'target_plus_1','DEC':'target_minus_1','COM':'ones_complement_target','NEG':'twos_complement_target','ASL':'target_shift_left','LSL':'target_shift_left','LSR':'target_shift_right','ROL':'target_rotate_left','ROR':'target_rotate_right'}.get(op,'unknown')

def candidate(sym,address_class,op):
    if sym=='L3FCE': return 'fuel_pw_hardware_sink','high','EFI pulsewidth command sink; active compact route bench-gated'
    if sym in {'L3FE8','L3FE6','L3FDC','L3FF6','L3FEC','L3FE4'}: return 'spark_stock_handoff_sink_or_state','medium','preserved stock spark handoff owns this target'
    if sym in {'L3062','L3060','L3FFC'}: return 'iac_output_sink_or_state','medium','IAC phase/output/enable candidate; direct writer bench-gated'
    if sym=='L303A': return 'watchdog_cop_sink','high','COP/watchdog register candidate'
    if address_class.startswith('hardware') or address_class.startswith('asic'): return 'hardware_or_asic_state','medium','mapped hardware/ASIC region'
    if op in {'BSET','BCLR'}: return 'mode_flag_or_safety_gate','medium','bit-level state mutation'
    return 'ram_state_or_intermediate','medium','requires downstream read/use analysis'

def dispatcher_context(pc,branches):
    p=int(pc,16)
    if 0x7a40 <= p <= 0x7aa5: return 'near_major_loop_dispatcher_7A4F'
    if 0xfa80 <= p <= 0xfad0: return 'near_output_control_dispatcher_FAA5'
    for b in branches:
        if b.startswith('7A4F:'): return 'major_loop_dispatch_context_recent'
        if b.startswith('FAA5:'): return 'output_control_dispatch_context_recent'
    return ''

def build(src):
    rows=[]; routine=''; xb=None; yb=None; branches=deque(maxlen=6)
    for line in src.read_text(encoding='utf-8',errors='ignore').splitlines():
        m=LINE_RE.match(line)
        if not m: continue
        pc,label,op,operands,comment=m.groups(); pc=pc.upper(); op=op.upper()
        if label: routine=label.upper()
        operands=(operands or '').split(';',1)[0].strip(); ops=split_operands(operands)
        if op in {'LDX','LDY'} and ops:
            mm=IMM_RE.match(ops[0].upper())
            if mm:
                if op=='LDX': xb=int(mm.group(1),16)
                else: yb=int(mm.group(1),16)
        if op in BRANCH_OPS: branches.append(f'{pc}:{op} {operands}'.strip())
        if op not in WRITE_OPS or not ops: continue
        tgt=ops[0]
        if not tgt or tgt.upper() in {'A','B','D','X','Y','SP'} or tgt.startswith('#'): continue
        bitmask=ops[1] if op in {'BSET','BCLR'} and len(ops)>1 else ''
        addr,sym,addr_class,status,xbase,ybase=resolve_target(tgt,xb,yb)
        role,conf,note=candidate(sym,addr_class,op)
        rows.append({'pc':pc,'routine_label':routine,'opcode':'','mnemonic':op,'operand_text':operands,'write_class':write_class(op),'target_raw':tgt,'target_resolved':addr,'target_symbol':sym,'address_class':addr_class,'width':width(op),'bitmask':bitmask,'x_base':xbase,'y_base':ybase,'index_resolution_status':status,'value_source':value_source(op),'nearby_branch_context':' | '.join(branches),'dispatcher_context':dispatcher_context(pc,branches),'candidate_role':role,'confidence':conf,'notes':note})
    return rows

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--source',default=str(SOURCE)); ap.add_argument('--out',default=str(OUT)); args=ap.parse_args()
    rows=build(Path(args.source)); out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f'wrote {len(rows)} rows to {out}')
