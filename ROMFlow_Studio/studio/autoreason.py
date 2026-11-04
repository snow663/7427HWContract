"""ROMFlow HC11F1-aware, ROM-first *conservative* abstract interpreter.

No executable emulator, no guessed runtime input values. A constant is recorded only
when it is provable on every analyzed incoming path. All reported interpretations
carry provenance and confidence. This engine never changes the decoded CFG.
"""
from collections import defaultdict, deque, Counter

UNKNOWN = None
REGS = ('A', 'B', 'X', 'Y', 'SP')
WIDTH = {'A': 8, 'B': 8, 'X': 16, 'Y': 16, 'SP': 16}
SCI_OFFSETS = {0x2B: 'BAUD', 0x2C: 'SCCR1', 0x2D: 'SCCR2', 0x2E: 'SCSR', 0x2F: 'SCDR'}
TIMER_OFFSETS = {0x0E: 'TCNT_H', 0x0F: 'TCNT_L', 0x22: 'TMSK1', 0x23: 'TFLG1'}
OPS_STORE = {'STAA': 'A', 'STAB': 'B', 'STD': 'D', 'STX': 'X', 'STY': 'Y', 'STS': 'SP'}
OPS_LOAD = {'LDAA': 'A', 'LDAB': 'B', 'LDD': 'D', 'LDX': 'X', 'LDY': 'Y', 'LDS': 'SP'}
OPS_BINARY = {'ADDA': ('A', '+'), 'ADDB': ('B', '+'), 'ADDD': ('D', '+'),
              'SUBA': ('A', '-'), 'SUBB': ('B', '-'), 'SUBD': ('D', '-'),
              'ANDA': ('A', '&'), 'ANDB': ('B', '&'), 'ORAA': ('A', '|'),
              'ORAB': ('B', '|'), 'EORA': ('A', '^'), 'EORB': ('B', '^')}
STACK = {'PSHA': -1, 'PSHB': -1, 'PSHX': -2, 'PSHY': -2,
         'PULA': 1, 'PULB': 1, 'PULX': 2, 'PULY': 2,
         'INS': 1, 'DES': -1}


def hx(n):
    return f'{n:04X}' if n is not None else '?'


def fresh():
    return (None, None, None, None, None)


def get(s, k):
    if k == 'D':
        return ((s[0] << 8) | s[1]) if s[0] is not None and s[1] is not None else None
    return s[REGS.index(k)]


def put(s, k, value):
    z = list(s)
    if k == 'D':
        z[0], z[1] = ((value >> 8) & 255, value & 255) if value is not None else (None, None)
    else:
        z[REGS.index(k)] = (value & ((1 << WIDTH[k]) - 1)) if value is not None else None
    return tuple(z)


def merge(old, new):
    return tuple(a if a == b else None for a, b in zip(old, new))


def operand_address(ins, s):
    if ins.mode in ('extended', 'direct'):
        return ins.value, 'instruction_absolute'
    if ins.mode in ('indexed_x', 'indexed_y'):
        base = get(s, ins.mode[-1].upper())
        if base is not None:
            return (base + ins.value) & 0xFFFF, 'register_constant_propagation'
    return None, 'unresolved_index'


def plausible_rom(an, address, size=1):
    # Full 64KiB dumps can include RAM/peripheral address space; treat that
    # region as runtime memory in the default HC11F1 map, not ROM constants.
    return an.img.contains(address,size) and not (an.img.start == 0 and address < 0x4000)


def read_operand(an, ins, s, width):
    if ins.mode == 'immediate':
        return ins.value, 'immediate_constant'
    addr, resolution = operand_address(ins, s)
    if addr is None or not plausible_rom(an, addr, width // 8):
        return None, 'runtime_memory_or_unknown'
    return int.from_bytes(an.img.read(addr, width // 8), 'big'), 'rom_constant_at_' + hx(addr)


def step(an, ins, incoming):
    """Transfer function; conservative for unknown arithmetic, flags and calls."""
    s = incoming
    op = ins.op
    if op in OPS_LOAD:
        k = OPS_LOAD[op]
        val, source = read_operand(an, ins, s, 16 if k in ('D', 'X', 'Y', 'SP') else 8)
        return put(s, k, val), source
    if op in OPS_BINARY:
        k, kind = OPS_BINARY[op]
        old = get(s, k)
        rhs, source = read_operand(an, ins, s, 16 if k == 'D' else 8)
        if old is None or rhs is None:
            return put(s, k, None), source
        if kind == '+': val = old + rhs
        elif kind == '-': val = old - rhs
        elif kind == '&': val = old & rhs
        elif kind == '|': val = old | rhs
        else: val = old ^ rhs
        return put(s, k, val), 'constant_fold_' + source
    if op in ('INX', 'DEX', 'INY', 'DEY'):
        k = op[-1]
        v = get(s, k)
        return put(s, k, (v + (1 if op.startswith('IN') else -1)) if v is not None else None), 'index_increment'
    if op in ('TAB', 'TBA'):
        return put(s, 'B' if op == 'TAB' else 'A', get(s, 'A' if op == 'TAB' else 'B')), 'register_transfer'
    if op == 'ABA':
        a, b = get(s, 'A'), get(s, 'B')
        return put(s, 'A', a + b if a is not None and b is not None else None), 'register_math'
    if op == 'CLRA': return put(s, 'A', 0), 'clear'
    if op == 'CLRB': return put(s, 'B', 0), 'clear'
    if op == 'XGDX' or op == 'XGDY':
        k = 'X' if op == 'XGDX' else 'Y'
        d, x = get(s, 'D'), get(s, k)
        return put(put(s, 'D', x), k, d), 'register_exchange'
    if op in ('ABX', 'ABY'):
        k = op[-1];x, b = get(s, k), get(s, 'B')
        return put(s, k, x + b if x is not None and b is not None else None), 'indexed_table_offset'
    if op == 'TSX' or op == 'TSY':
        sp = get(s, 'SP')
        return put(s, op[-1], (sp + 1) & 0xFFFF if sp is not None else None), 'stack_to_index'
    if op == 'TXS' or op == 'TYS':
        x = get(s, 'X' if op == 'TXS' else 'Y')
        return put(s, 'SP', (x - 1) & 0xFFFF if x is not None else None), 'index_to_stack'
    if op in STACK:
        sp = get(s, 'SP')
        s = put(s, 'SP', sp + STACK[op] if sp is not None else None)
        if op.startswith('PUL'):
            k = {'PULA': 'A', 'PULB': 'B', 'PULX': 'X', 'PULY': 'Y'}[op]
            s = put(s, k, None)
        return s, 'stack_update'
    if op == 'MUL':
        a,b = get(s,'A'),get(s,'B')
        return put(s,'D',a*b if a is not None and b is not None else None),'multiply'
    if op in ('IDIV','FDIV'):
        return put(put(s,'D',None),'X',None),'division_unknown_or_runtime'
    if op in ('JSR', 'BSR', 'SWI', 'RTI', 'WAI'):
        return fresh(), 'control_boundary_register_clobber'
    # Most ops that modify CCR or memory but not register values are harmless.
    # Inherent ALU operators absent from OPS_BINARY must not preserve stale values.
    if op in ('SBA','CBA','DAA','TAP','TPA','LSRD','ASLD'):
        if op == 'CBA' or op == 'TAP': return s, 'flags_only'
        if op == 'TPA': return put(s, 'A', None), 'ccr_unknown'
        return put(s,'D' if op in ('LSRD','ASLD') else 'A',None), 'conservative_alu'
    for k in ('A','B'):
        if op in ('NEG'+k,'COM'+k,'LSR'+k,'ROR'+k,'ASR'+k,'ASL'+k,'ROL'+k,'DEC'+k,'INC'+k,'CLR'+k):
            if op == 'CLR'+k:return put(s,k,0),'clear'
            return put(s,k,None),'conservative_alu'
    return s, 'unchanged'


def register_dataflow(an, max_steps=220000):
    """Forward fixed-point register propagation with conservative join semantics."""
    states = {}
    pending = deque()
    def admit(pc, state):
        if pc not in an.instructions: return
        if pc not in states:
            states[pc] = state
            pending.append(pc)
        else:
            combined = merge(states[pc], state)
            if combined != states[pc]:
                states[pc] = combined
                pending.append(pc)
    for pc in sorted(an.entries): admit(pc, fresh())
    steps = 0
    while pending and steps < max_steps:
        steps += 1
        pc = pending.popleft()
        ins = an.instructions[pc]
        outgoing, _ = step(an, ins, states[pc])
        for target, kind in an.graph_edges(ins):
            if target is not None: admit(target, outgoing)
    return states, {'steps': steps, 'converged': not pending, 'state_count': len(states)}


def analyze(an):
    """Return JSON-compatible per-instruction reasoning and auto-discovery findings."""
    states, convergence = register_dataflow(an)
    details = {}
    xrefs = []
    categories = Counter()
    sci_base_counts = Counter()
    for pc, ins in sorted(an.instructions.items()):
        before = states.get(pc, fresh())
        after, evidence = step(an, ins, before)
        mem = ins.access()
        item = {'pc': hx(pc), 'op': ins.op, 'before': {k: hx(v) if v is not None else '?' for k,v in zip(REGS,before)},
                'after': {k: hx(v) if v is not None else '?' for k,v in zip(REGS,after)},
                'reason': evidence, 'confidence': 'static_proven_if_reachable' if pc in states else 'unreachable_state_unknown',
                'stack_delta': STACK.get(ins.op), 'memory': []}
        if mem is not None:
            address, resolution = operand_address(ins, before)
            if address is not None:
                for lane in range(2 if mem['width_bits'] == 16 else 1):
                    a = (address + lane) & 0xFFFF
                    kind = ('rom_read' if ins.op not in OPS_STORE and plausible_rom(an,a) else
                            'rom_write_attempt_or_memory_overlay' if ins.op in OPS_STORE and plausible_rom(an,a) else
                            'memory_access')
                    d = {'address':hx(a), 'direction':mem['access'], 'category':kind,
                         'resolution':resolution,'lane':lane}
                    item['memory'].append(d)
                    xrefs.append({'pc':hx(pc),**d,'instruction':ins.op})
                    categories[kind] += 1
                    for off in SCI_OFFSETS:
                        if a >= off and (a-off) % 0x1000 == 0:
                            sci_base_counts[a-off] += 1
            else:
                item['memory'].append({'address':'?', 'direction':mem['access'], 'category':'unknown_address','resolution':resolution})
        if ins.op in ('JSR','BSR','JMP'):
            item['control']={'kind':ins.op,'target':hx(ins.target),'resolution':'direct' if ins.target is not None else 'register_indirect_or_runtime'}
        details[hx(pc)] = item
    sci = []
    # HC11 peripheral register base is writable at startup; do not assert one base.
    for base,count in sci_base_counts.most_common(8):
        if not 0 <= base <= 0xF000: continue
        references = [x for x in xrefs if x['address']!='?' and int(x['address'],16)-base in SCI_OFFSETS]
        distinct = len({int(x['address'],16)-base for x in references})
        if distinct < 2: continue
        sci.append({'base':hx(base),'confidence':'candidate_register_block_unverified','distinct_sci_offsets':distinct,
                    'references':len(references),'registers':[
                    {'address':x['address'],'name':SCI_OFFSETS[int(x['address'],16)-base], 'pc':x['pc'],
                     'direction':x['direction']} for x in references[:200]]})
    # Classify likely code/data based on control-flow evidence and actual ROM read sites.
    rom_refs = defaultdict(list)
    for x in xrefs:
        if x['category']=='rom_read':rom_refs[x['address']].append(x)
    suggestions=[]
    code_byte={pc+j for pc,ins in an.instructions.items() for j in range(len(ins.data))}
    for addr, refs in sorted(rom_refs.items()):
        a=int(addr,16)
        if a in code_byte: continue
        suggestions.append({'address':addr, 'kind':'rom_data_reference', 'confidence':'medium',
                            'reason':'Decoded instructions explicitly read mapped image bytes not classified as reachable code',
                            'reference_sites':sorted({x['pc'] for x in refs})[:25], 'read_count':len(refs)})
    for candidate in sci:
        suggestions.append({'address':candidate['base'], 'kind':'hc11_sci_register_base_candidate',
                            'confidence':'low_to_medium','reason':'Multiple accesses align with relocatable HC11 SCI register offsets'})
    roles = []
    sci_addresses={int(ref['address'],16) for c in sci for ref in c['registers']}
    for entry, routine in sorted(an.routines.items()):
        pcs = routine['pcs']
        ops = Counter(an.instructions[pc].op for pc in pcs)
        accesses = [x for x in xrefs if int(x['pc'],16) in pcs]
        kinds=[]
        if any(int(x['address'],16) in sci_addresses for x in accesses if x['address']!='?'):
            kinds.append('SCI / serial candidate')
        if ops['RTI']:
            kinds.append('interrupt handler candidate')
        if any(x['category']=='rom_read' for x in accesses):
            kinds.append('ROM lookup / calibration consumer')
        if any(x['direction'] in ('W','RW') for x in accesses):
            kinds.append('state update / I-O writer')
        if any(ops[o] for o in ('MUL','IDIV','FDIV','ADDD','SUBD')):
            kinds.append('arithmetic / scaling')
        if any(an.instructions[pc].op in ('JSR','JMP') and an.instructions[pc].target is None for pc in pcs):
            kinds.append('indirect dispatch / pointer control')
        if any(e[2] in ('taken','jump') and e[1] is not None and e[1]<=e[0] for e in routine.get('edges',[])):
            kinds.append('loop / state machine candidate')
        if not kinds:kinds=['general control / unclassified']
        roles.append({'entry':hx(entry),'suggested_roles':kinds,
                      'confidence':'behavioral_pattern_only', 'instruction_count':len(pcs),
                      'rom_read_sites':len([x for x in accesses if x['category']=='rom_read']),
                      'memory_write_sites':len([x for x in accesses if x['direction'] in ('W','RW')]),
                      'branch_count':sum(ops[k] for k in ('BRA','BEQ','BNE','BCC','BCS','BHI','BLS','BRSET','BRCLR'))})
    return {'engine':'HC11 conservative abstract interpretation v0.1',
            'limitations':['Static paths are not proof of real-time execution','Unknown runtime RAM and I/O stay unknown',
                           'Interrupt and call effects are conservatively clobbered','No bank switching inferred',
                           'Hardware register base candidates require confirmation'],
            'convergence':convergence,'instructions':details,'memory_references':xrefs,
            'likely_sci_blocks':sci,'routine_roles':roles,'suggestions':suggestions[:500], 'counts':dict(categories)}
