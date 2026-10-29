"""Nominal HC11 E-cycle costs for reviewed factory timing subsets.

Source: NXP M68HC11ERG rev2.1, Table1, pp13..20, and M68HC11RM
AppendixA. No bus stretching, asynchronous work or peripheral wait is included.
This deliberately does not use the simulator core's cycle accounting.
"""
from factory_rom_decode import BRANCHES

INHERENT = dict.fromkeys('ABA ASLA ASLB ASRA CLI CLRA CLRB DECA DECB INCA INCB LSRB NEGA ROLA RORA RORB SBA SEI TAB TAP TBA TPA TSTA TSTB'.split(), 2)
INHERENT.update(ABX=3, ASLD=3, INS=3, INX=3, INY=4, LSRD=3, TSX=3, XGDX=3,
                 XGDY=4, PSHA=3, PSHB=3, PSHX=4, PSHY=5, PULA=4, PULB=4, PULX=5, PULY=6,
                 RTS=5, RTI=12, FDIV=41, MUL=10)
READ8 = set('ADCA ADCB ADDA ADDB ANDA ANDB BITA BITB CMPA CMPB EORA EORB LDAA LDAB ORAA ORAB SBCA SBCB SUBA'.split())
MODES = ('immediate', 'direct', 'extended', 'indexed_x', 'indexed_y')


def cycles(i):
    if i.mode == 'inherent' and i.op in INHERENT:
        return INHERENT[i.op]
    if i.op in BRANCHES:
        return 3
    if i.op == 'BSR':
        return 6
    if i.op in {'BRSET','BRCLR','BSET','BCLR'}:
        return {'direct':6, 'indexed_x':7, 'indexed_y':8}[i.mode]
    if i.op in READ8:
        return dict(zip(MODES, (2,3,4,4,5)))[i.mode]
    if i.op in {'LDD','LDX','LDS'}:
        return dict(zip(MODES, (3,4,5,5,6)))[i.mode]
    if i.op == 'LDY':
        return dict(zip(MODES, (4,5,6,6,6)))[i.mode]
    if i.op in {'ADDD','SUBD','CPX'}:
        return dict(zip(MODES, (4,5,6,6,7)))[i.mode]
    if i.op in {'CPD','CPY'}:
        return dict(zip(MODES, (5,6,7,7,7)))[i.mode]
    if i.op in {'STAA','STAB'}:
        return {'direct':3,'extended':4,'indexed_x':4,'indexed_y':5}[i.mode]
    if i.op in {'STD','STX'}:
        return {'direct':4,'extended':5,'indexed_x':5,'indexed_y':6}[i.mode]
    if i.op == 'STY':
        return {'direct':5,'extended':6,'indexed_x':6,'indexed_y':6}[i.mode]
    if i.op in {'CLR','TST','INC'}:
        return {'extended':6,'indexed_x':6,'indexed_y':7}[i.mode]
    if i.op == 'JMP':
        return {'extended':3,'indexed_x':3,'indexed_y':4}[i.mode]
    if i.op == 'JSR':
        return {'direct':5,'extended':6,'indexed_x':6,'indexed_y':7}[i.mode]
    raise ValueError(f'Unreviewed HC11 timing at {i.pc:04X}: {i.op} {i.mode}')
