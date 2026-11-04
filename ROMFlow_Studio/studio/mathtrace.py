"""Conservative straight-line expression sketches, NOT a decompiler.

Expressions reset at basic-block boundaries and after calls.  Flags, signed
conditions, indexing and interrupts are not globally propagated.  All values
are HC11 fixed-width expressions; unhandled operations invalidate registers.
"""
from __future__ import annotations

WORDS = {"LDD","STD","LDX","STX","LDY","STY","LDS","STS"}

def math_traces(an, pcs, boundaries):
    regs = {"A":"A?", "B":"B?", "D":"D?", "X":"X?", "Y":"Y?", "SP":"SP?"}
    traces=[]
    def fresh():
        return {"A":"A?", "B":"B?", "D":"D?", "X":"X?", "Y":"Y?", "SP":"SP?"}
    for pc in sorted(pcs):
        if pc in boundaries: regs=fresh()
        ins=an.instructions[pc]; op=ins.op; mode=ins.mode; value=ins.value
        operand=ins.operand
        mem=ins.access()
        addr = None
        if mem:
            if mode in ("direct","extended"):addr=value
            elif mode in ("indexed_x","indexed_y"):
                b=regs[mode[-1].upper()]
                if b.startswith('0x'):
                    try:addr=(int(b,16)+value)&0xFFFF
                    except ValueError:pass
        width=16 if op in WORDS else 8
        m=f'mem{width}[${addr:04X}]' if addr is not None else f'mem{width}[{operand.split(",")[0]}]'
        effects=[];formula='';conf='local expression; not whole-path proof'
        if op in {"LDAA","LDAB","LDD","LDX","LDY","LDS"}:
            k={'LDAA':'A','LDAB':'B','LDD':'D','LDX':'X','LDY':'Y','LDS':'SP'}[op]
            expr=(f'0x{value:0{4 if k in ("D","X","Y","SP") else 2}X}' if mode=='immediate' else m)
            regs[k]=expr;formula=f'{k} ← {expr}'
            if k in ('A','B'):regs['D']='D?'
            if k=='D':regs['A']=regs['B']='?'
        elif op in {"STAA","STAB","STD","STX","STY","STS"}:
            k={'STAA':'A','STAB':'B','STD':'D','STX':'X','STY':'Y','STS':'SP'}[op]
            formula=f'{m} ← {regs[k]}'
            if addr is not None:effects.append(f'WRITE ${addr:04X}')
        elif op in {"ADDD","SUBD","ADDA","SUBA","ADDB","SUBB"}:
            k='D' if op.endswith('D') else op[-1]
            mod=65536 if k=='D' else 256
            rhs=f'{value}' if mode=='immediate' else m
            sign='+' if op.startswith('ADD') else '-'
            regs[k]=f'(({regs[k]} {sign} {rhs}) & ${mod-1:04X})'
            formula=f'{k} ← {regs[k]}'
            if k in ('A','B'):regs['D']='D?'
            if k=='D':regs['A']=regs['B']='?'
        elif op in {'ASLD','LSRD'}:
            regs['D']=f'(({regs["D"]} {"<<" if op=="ASLD" else ">>"} 1) & $FFFF)'
            regs['A']=regs['B']='?';formula=f'D ← {regs["D"]}'
        elif op=='MUL':
            regs['D']=f'(({regs["A"]} × {regs["B"]}) & $FFFF)'
            regs['A']=regs['B']='?';formula=f'D ← {regs["D"]}'
        elif op in {'INX','DEX','INY','DEY'}:
            k=op[-1];add=1 if op.startswith('IN') else -1
            if regs[k].startswith('0x'):
                regs[k]=f'0x{(int(regs[k],16)+add)&0xFFFF:04X}'
            else:regs[k]=f'({regs[k]} {"+" if add>0 else "-"} 1) & $FFFF'
            formula=f'{k} ← {regs[k]}'
        elif op in {'BSET','BCLR'}:
            sign='|' if op=='BSET' else '& ~'
            formula=f'{m} ← {m} {sign} ${ins.mask:02X}'
            if addr is not None:effects.append(f'RMW ${addr:04X}')
        elif op in {'BRSET','BRCLR'}:
            formula=f'branch if ({m} & ${ins.mask:02X}) {"≠" if op=="BRSET" else "="} 0 → ${ins.target:04X}'
        elif op in {'LDAA','LDAB'}: pass
        elif op.startswith(('CMP','BIT','CP')):
            formula=f'compare {operand}; sets condition flags'
        elif op in {'JSR','BSR'}: formula=f'CALL ${ins.target:04X}' if ins.target is not None else 'CALL [indirect]';regs=fresh()
        elif op in {'RTS','RTI'}:formula=f'{op} — return to saved execution context'
        elif op in {'PSHA','PSHB','PSHX','PSHY'}:
            effects.append('stack write (SP relative)');formula=f'SP decreases; push {op[-1]}'
        elif op in {'PULA','PULB','PULX','PULY'}:
            effects.append('stack read (SP relative)');formula=f'SP increases; pull {op[-1]}'
            regs[op[-1]]='?'
        elif op in {'TSX','TSY','TXS','TYS','INS','DES'}:
            effects.append('stack pointer change');formula=f'{op} modifies or exchanges SP-relative address'
            regs['SP']='SP?';regs['X']='X?';regs['Y']='Y?'
        elif op in {'SEI','CLI','WAI','SWI','STOP'}:
            formula=f'{op} — CPU/interrupt state change'
        elif op in {'BRA','JMP','BRN','BNE','BEQ','BPL','BMI','BCC','BCS','BHI','BLS','BGE','BLT','BGT','BLE','BVC','BVS'}:
            formula=f'{op} → ${ins.target:04X}' if ins.target is not None else f'{op} indirect'
        elif op in {'CLRA','CLRB'}:
            k=op[-1];regs[k]='0x00';regs['D']='D?';formula=f'{k} ← 0'
        elif op in {'CLRX','CLRY'}: pass
        elif op in {'TAB','TBA'}:
            dest='B' if op=='TAB' else 'A';source='A' if op=='TAB' else 'B'
            regs[dest]=regs[source];regs['D']='D?';formula=f'{dest} ← {source}'
        elif op in {'ABX','ABY','XGDX','XGDY','PULX','PULY'}:
            regs['X']=regs['Y']='?'
        elif op.startswith(('ASL','LSL','LSR','ROR','ROL','ASR','EOR','ORA','ORB','AND','ADC','SBC','INC','DEC','NEG','COM')):
            # Unsupported carry and signed flag semantics deliberately invalidate affected register.
            if op.endswith('A'):regs['A']='A?';regs['D']='D?'
            if op.endswith('B'):regs['B']='B?';regs['D']='D?'
            if op in {'ABX','ABY'}:regs[op[-1]]='?'
            formula=f'{op} {operand} (flag/carry semantics not modeled)'
        traces.append({'pc':f'{pc:04X}','formula':formula,'effects':effects,'confidence':conf,'registers':dict(regs)})
    return traces
