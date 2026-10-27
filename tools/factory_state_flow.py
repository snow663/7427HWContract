"""Conservative register/stack flow over ROM-decoded HC11 procedure graphs.

Values are bounded sets of constants or affine entry-register expressions.
RAM/device loads are unknown; only captured ROM and locally saved stack bytes
are folded. Calls substitute separately analyzed return/effect templates. Any
opaque call clobbers registers and may access arbitrary memory. This is a may
analysis of normal-return paths, not a whole-machine execution proof.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from itertools import product

from factory_rom_decode import BRANCHES, TERMINALS, successors

LIMIT = 64


@dataclass(frozen=True, order=True)
class Ref:
    name: str
    offset: int = 0
    part: str = "full"


@dataclass(frozen=True)
class Value:
    bits: int
    items: frozenset | None = None

    @classmethod
    def of(cls, bits, items):
        items = frozenset(x & ((1 << bits)-1) if isinstance(x, int) else x for x in items)
        return cls(bits, items if len(items) <= LIMIT else None)

    @classmethod
    def const(cls, bits, n):
        return cls.of(bits, [n])

    @classmethod
    def param(cls, bits, name):
        return cls.of(bits, [Ref(name)])

    def join(self, other):
        assert self.bits == other.bits
        return Value(self.bits) if self.items is None or other.items is None else Value.of(self.bits, self.items | other.items)

    def singleton(self):
        return next(iter(self.items)) if self.items is not None and len(self.items) == 1 else None

    def ints(self):
        return self.items if self.items is not None and all(isinstance(x, int) for x in self.items) else None

    def text(self):
        if self.items is None:
            return "unknown"
        def show(x):
            if isinstance(x, int):
                return f"${x:0{4 if self.bits==16 else 2}X}"
            offset = x.offset if x.offset < 0x8000 else x.offset - 0x10000
            base = "SP_at_" + x.name[6:] if x.name.startswith("FRAME_") else "entry_" + x.name
            name = base + (f"{offset:+d}" if offset else "")
            return name if x.part == "full" else f"{x.part}({name})"
        return ";".join(sorted(show(x) for x in self.items))


def add_constant(value, n):
    if value.items is None:
        return Value(value.bits)
    result = []
    for x in value.items:
        if isinstance(x, int):
            result.append(x+n)
        elif x.part == "full" and (value.bits == 16 or n == 0):
            result.append(Ref(x.name, (x.offset+n) & ((1 << value.bits)-1)))
        elif n == 0:
            result.append(x)
        else:
            return Value(value.bits)
    return Value.of(value.bits, result)


def byte_part(value, part):
    if value.items is None:
        return Value(8)
    return Value.of(8, [((x >> 8) if part == "hi" else x & 255) if isinstance(x, int)
                        else Ref(x.name, x.offset, part) for x in value.items])


def word(high, low):
    if high.items is None or low.items is None:
        return Value(16)
    result = []
    for a,b in product(high.items, low.items):
        if isinstance(a, int) and isinstance(b, int):
            result.append((a << 8) | b)
        elif isinstance(a, Ref) and isinstance(b, Ref) and a.name == b.name and a.offset == b.offset and a.part == "hi" and b.part == "lo":
            result.append(Ref(a.name, a.offset))
        else:
            return Value(16)
        if len(result) > LIMIT:
            return Value(16)
    return Value.of(16, result)


def binary(left, right, op):
    if op == "+":
        if isinstance(right.singleton(), int):
            return add_constant(left, right.singleton())
        if isinstance(left.singleton(), int):
            return add_constant(right, left.singleton())
    if op == "-" and isinstance(right.singleton(), int):
        return add_constant(left, -right.singleton())
    a, b = left.ints(), right.ints()
    # Unknown byte AND a mask still has a bounded, sound set of outcomes.
    if op == "&" and isinstance(right.singleton(), int):
        mask = right.singleton()
        if a is None:
            return Value.of(left.bits, (x & mask for x in range(256)))
    if op == "|" and isinstance(right.singleton(), int) and a is None and left.bits == 8:
        return Value.of(8, (x | right.singleton() for x in range(256)))
    if a is None or b is None:
        return Value(left.bits)
    functions = {"+": lambda x,y:x+y, "-": lambda x,y:x-y, "&": lambda x,y:x&y,
                 "|": lambda x,y:x|y, "^": lambda x,y:x^y}
    out = set()
    for x,y in product(a,b):
        out.add(functions[op](x,y) & ((1 << left.bits)-1))
        if len(out) > LIMIT:
            return Value(left.bits)
    return Value.of(left.bits, out)


def substitute(value, bindings):
    if value.items is None:
        return value
    out = Value.of(value.bits, [])
    for item in value.items:
        if isinstance(item, int):
            part = Value.const(value.bits, item)
        elif item.name.startswith("FRAME_"):
            # A reviewed local frame is relative to SP at its own save site,
            # even when an earlier opaque call made entry-SP unknowable.
            part = Value.of(value.bits, [item])
        else:
            # Zero-extension must precede 16-bit address arithmetic. Byte
            # wraparound expressions are widened at their producer instead.
            source = bindings[item.name]
            part = add_constant(Value(16 if item.part != "full" else value.bits, source.items), item.offset)
            if item.part != "full":
                part = byte_part(part, item.part)
        out = out.join(part)
    return out


@dataclass
class State:
    regs: dict
    stack: dict = field(default_factory=dict)
    carry: Value = field(default_factory=lambda: Value.param(1, "C"))
    predicate: tuple | None = None

    @classmethod
    def entry(cls):
        return cls({r: Value.param(8 if r in {"A","B"} else 16, r) for r in ["A","B","X","Y","SP"]})

    def copy(self):
        return State(dict(self.regs), dict(self.stack), self.carry, self.predicate)

    def get(self, register):
        return word(self.regs["A"], self.regs["B"]) if register == "D" else self.regs[register]

    def put(self, register, value):
        if register == "D":
            self.regs["A"], self.regs["B"] = byte_part(value,"hi"), byte_part(value,"lo")
        else:
            self.regs[register] = value
        # A flag predicate cannot refer to an older value of a changed register.
        if self.predicate and (self.predicate[0] == register or register == "D" and self.predicate[0] in {"A","B"} or self.predicate[0] == "D" and register in {"A","B"}):
            self.predicate = None

    def join(self, other):
        stack={}
        for address in self.stack.keys() & other.stack.keys():
            value=self.stack[address].join(other.stack[address])
            if value.items is not None:stack[address]=value
        return State({r:self.regs[r].join(other.regs[r]) for r in self.regs},
                     stack,
                     self.carry.join(other.carry), self.predicate if self.predicate == other.predicate else None)


@dataclass(frozen=True)
class Effect:
    pc: int
    access: str
    width: int
    address: Value
    via: tuple = ()


@dataclass
class Summary:
    entry: int
    outputs: dict
    carry: Value
    local: dict
    effects: dict
    calls: dict
    opaque: set
    states: dict
    normal_returns: int
    iterations: int


def stack_address(value):
    return value.items is not None and bool(value.items) and all(isinstance(x, Ref) and (x.name == "SP" or x.name.startswith("FRAME_")) and x.part == "full" for x in value.items)


def read_value(rom, state, address, bits):
    if address.items is None:
        return Value(bits)
    out = Value.of(bits, [])
    for key in address.items:
        if isinstance(key, int) and key >= 0x4000 and key + bits//8 <= 0x10000:
            part = Value.const(bits, int.from_bytes(rom.read(key, bits//8), "big"))
        elif bits == 8:
            part = state.stack.get(key, Value(8))
        else:
            part = word(state.stack.get(key, Value(8)), state.stack.get(add_constant(Value.of(16,[key]),1).singleton(), Value(8)))
        out = out.join(part)
    return out


def write_value(state, address, value):
    """Only saved stack bytes are tracked; arbitrary RAM writes invalidate aliases."""
    keys = address.items
    if keys is None:
        state.stack.clear()
        return
    if any(isinstance(k,Ref) and k.name!="SP" for k in keys):
        state.stack.clear();return
    cells={add_constant(Value.of(16,[key]),offset).singleton()
           for key in keys for offset in range(value.bits//8)}
    ram_ints={k for k in cells if isinstance(k,int) and k<0x1000}
    relative={k for k in cells if isinstance(k,Ref)}
    # Absolute RAM addresses and an unknown physical frame may alias. Work at
    # byte granularity so a word at $FFFF also accounts for its $0000 byte.
    if (ram_ints and any(isinstance(k,Ref) for k in state.stack)
            or relative and any(isinstance(k,int) for k in state.stack)):
        state.stack.clear();return
    if len(keys)!=1:
        for cell in cells:state.stack.pop(cell,None)
        return
    key=next(iter(keys))
    for offset in range(value.bits//8):
        cell=add_constant(Value.of(16,[key]),offset).singleton()
        part=value if value.bits==8 else byte_part(value,"hi" if offset==0 else "lo")
        if cell in state.stack or isinstance(cell,Ref):
            if part.items is None:state.stack.pop(cell,None)
            else:state.stack[cell]=part


def push(state, value):
    # HC11 stores the low word byte first while decrementing SP.
    for part in ([byte_part(value,"lo"), byte_part(value,"hi")] if value.bits == 16 else [value]):
        key = state.get("SP").singleton()
        if key is None:
            state.stack.clear()
        else:
            if part.items is None:state.stack.pop(key,None)
            else:state.stack[key]=part
        state.put("SP", add_constant(state.get("SP"), -1))


def pull(state, bits):
    parts = []
    for _ in range(bits//8):
        state.put("SP", add_constant(state.get("SP"), 1))
        key = state.get("SP").singleton()
        parts.append(state.stack.pop(key, Value(8)))
    return parts[0] if bits == 8 else word(*parts)


def effective(state, ins):
    if ins.mode in {"direct","extended"}:
        return Value.const(16, ins.value)
    if ins.mode.startswith("indexed_"):
        return add_constant(state.get(ins.mode[-1].upper()), ins.value)
    return Value(16)


def add_effect(mapping, effect):
    # Keep call witnesses distinct. Widen address unions rather than discarding
    # an unknown branch or substituting a known address from another context.
    key = (effect.pc, effect.access, effect.width, effect.via[:1])
    if key in mapping:
        old = mapping[key]
        witness = min((old.via,effect.via),key=lambda p:(len(p),p))
        effect = Effect(old.pc, old.access, old.width, old.address.join(effect.address), witness)
    mapping[key] = effect


def apply_call(state, summary, pc, effects, opaque):
    bindings = {**state.regs, "C":state.carry}
    bindings["SP"] = add_constant(state.get("SP"), -2)
    if summary is None:
        for r in state.regs:
            state.regs[r] = Value(8 if r in {"A","B"} else 16)
        state.stack.clear()
        state.carry, state.predicate = Value(1), None
        opaque.add(pc)
        return
    for effect in summary.effects.values():
        address = substitute(effect.address, bindings)
        # Explicit stack-relative reads belong to a frame, not a global state byte.
        if "W" in effect.access:
            write_value(state, address, Value(effect.width))
        add_effect(effects, Effect(effect.pc, effect.access, effect.width, address, (pc,)+effect.via))
    state.regs = {r:substitute(summary.outputs[r], bindings) for r in state.regs}
    if summary.outputs["SP"] != add_constant(Value.param(16,"SP"),2):
        state.stack.clear()
    state.carry = substitute(summary.carry, bindings)
    state.predicate = None
    opaque.update(summary.opaque)


def operand_value(rom, state, ins):
    bits = 16 if ins.op in {"ADDD","SUBD","LDD","LDX","LDY","LDS","CPD","CPX","CPY"} else 8
    return Value.const(bits,ins.value) if ins.mode == "immediate" else read_value(rom,state,effective(state,ins),bits)


def arithmetic(state, register, operand, subtract=False, carry=False):
    original = state.get(register)
    result = binary(original, operand, "-" if subtract else "+")
    if carry:
        result = binary(result, Value.of(result.bits,state.carry.ints()) if state.carry.ints() is not None else Value(result.bits), "-" if subtract else "+")
    state.put(register,result)
    state.predicate = (register,"zero",0)
    state.carry = Value(1)  # Carry/overflow is widened unless a branch has a compare predicate.


def transfer(rom, state, ins):
    op = ins.op
    if op in {"LDAA","LDAB","LDD","LDX","LDY","LDS"}:
        r = {"LDAA":"A","LDAB":"B","LDD":"D","LDX":"X","LDY":"Y","LDS":"SP"}[op]
        state.put(r,operand_value(rom,state,ins))
        if r == "SP":
            state.stack.clear()
        state.predicate = (r,"zero",0)
    elif op in {"STAA","STAB","STD","STX","STY"}:
        r = {"STAA":"A","STAB":"B","STD":"D","STX":"X","STY":"Y"}[op]
        write_value(state,effective(state,ins),state.get(r))
        state.predicate = (r,"zero",0)
    elif op.startswith("PSH"):
        push(state,state.get(op[-1]))
    elif op.startswith("PUL"):
        r = op[-1]
        state.put(r,pull(state,8 if r in {"A","B"} else 16))
    elif op in {"TSX","TSY"}:
        state.put(op[-1],add_constant(state.get("SP"),1))
    elif op == "TYS":
        state.put("SP",add_constant(state.get("Y"),-1))
        state.stack.clear()
    elif op == "INS":
        pull(state,8)
    elif op in {"TAB","TBA"}:
        r,src = ("B","A") if op == "TAB" else ("A","B")
        state.put(r,state.get(src)); state.predicate=(r,"zero",0)
    elif op in {"XGDX","XGDY"}:
        r=op[-1]; old=state.get(r); state.put(r,state.get("D")); state.put("D",old)
    elif op in {"INX","INY","DEX","DEY"}:
        r=op[-1]; state.put(r,add_constant(state.get(r),1 if op.startswith("IN") else -1))
        state.predicate=(r,"zero",0)
    elif op in {"ABX","ABY"}:
        r=op[-1]; state.put(r,binary(state.get(r),Value(16,state.get("B").items),"+"))
    elif op in {"CMPA","CMPB","CPD","CPX","CPY"}:
        state.predicate=(op[-1],"compare",operand_value(rom,state,ins))
        state.carry=Value(1)
    elif op == "CBA":
        state.predicate=("A","compare",state.get("B"));state.carry=Value(1)
    elif op in {"ANDA","ANDB","ORAA","ORAB","EORA","EORB"}:
        r=op[-1]; operator="&" if op.startswith("AND") else "|" if op.startswith("ORA") else "^"
        state.put(r,binary(state.get(r),operand_value(rom,state,ins),operator));state.predicate=(r,"zero",0)
    elif op in {"BITA","BITB"}:
        state.predicate=None
    elif op in {"ADDA","ADDB","ADCA","ADCB","SUBA","SUBB","SBCA","SBCB","ADDD","SUBD"}:
        arithmetic(state,op[-1],operand_value(rom,state,ins),op.startswith(("SUB","SBC")),op.startswith(("ADC","SBC")))
    elif op in {"ABA","SBA"}:
        arithmetic(state,"A",state.get("B"),op=="SBA")
    elif op == "MUL":
        a,b=state.get("A").ints(),state.get("B").ints()
        if a is None and b is None:
            state.put("D",Value(16))
        else:
            products=[x*y for x,y in product(a if a is not None else range(256), b if b is not None else range(256))]
            state.put("A",Value.of(8,(x >> 8 for x in products)))
            state.put("B",Value.of(8,(x & 255 for x in products)))
        state.carry=Value(1);state.predicate=None
    elif op in {"IDIV","FDIV"}:
        state.put("D",Value(16));state.put("X",Value(16));state.carry=Value(1);state.predicate=None
    elif op in {"CLC","SEC"}:
        state.carry=Value.const(1,int(op=="SEC"))
        state.predicate=None  # An earlier compare no longer describes carry.
    elif op in {"TPA"}:
        state.put("A",Value(8))
    elif op == "TAP":
        state.carry=Value(1);state.predicate=None
    elif op == "NOP" or op in {"SEI","CLI"} or op in BRANCHES or op in {"BRSET","BRCLR","JMP"}:
        pass
    elif op in {"BSET","BCLR"}:
        address=effective(state,ins); v=read_value(rom,state,address,8)
        write_value(state,address,binary(v,Value.const(8,ins.mask if op=="BSET" else (~ins.mask)&255),"|" if op=="BSET" else "&"))
        state.predicate=None
    else:
        # Unary memory/register operations. Widen rotates when carry is unknown.
        register=op[-1] if op[-1:] in {"A","B","D"} and ins.mode=="inherent" else None
        base=op[:-1] if register else op
        if base not in {"CLR","INC","DEC","NEG","COM","LSR","ASR","ASL","ROL","ROR","TST"}:
            raise ValueError(f"Unmodeled register effects: {ins.pc:04X} {op}")
        old=state.get(register) if register else read_value(rom,state,effective(state,ins),8)
        ints=old.ints()
        if base=="CLR":new=Value.const(old.bits,0)
        elif base in {"INC","DEC"}:new=add_constant(old,1 if base=="INC" else -1)
        elif base=="TST":new=old
        elif ints is None:new=Value(old.bits)
        else:
            mask=(1<<old.bits)-1
            f={"NEG":lambda x:-x,"COM":lambda x:~x,"LSR":lambda x:x>>1,
               "ASR":lambda x:(x>>1)|(x & (1<<(old.bits-1))),"ASL":lambda x:x<<1,
               "ROL":lambda x:(x<<1),"ROR":lambda x:(x>>1)}[base]
            results={f(x)&mask for x in ints}
            if base in {"ROL","ROR"}:
                carries=state.carry.ints() if state.carry.ints() is not None else {0,1}
                results={(f(x)| (c if base=="ROL" else c<<(old.bits-1)))&mask for x,c in product(ints,carries)}
            new=Value.of(old.bits,results)
        if base!="TST":
            if register:state.put(register,new)
            else:write_value(state,effective(state,ins),new)
        state.predicate=(register,"zero",0) if register else None
        if base not in {"INC","DEC"}:state.carry=Value(1)


def branch_state(state, op, taken):
    state=state.copy()
    if op in {"BCC","BCS"} and state.predicate is None:
        expected=int((op=="BCS")==taken)
        values=state.carry.ints()
        if values is not None and expected not in values:return None
        state.carry=Value.const(1,expected)
    pred=state.predicate
    if pred is None:return state
    register,kind,operand=pred
    lhs=state.get(register); values=lhs.ints()
    if values is None:return state
    if kind=="zero":
        if op not in {"BEQ","BNE"}:return state
        condition=lambda x:x==0 if op=="BEQ" else x!=0
    else:
        right=operand.singleton()
        if not isinstance(right,int):return state
        sign=1<<(lhs.bits-1)
        signed=lambda x:x if x<sign else x-(sign<<1)
        conditions={"BEQ":lambda x:x==right,"BNE":lambda x:x!=right,
                    "BCC":lambda x:x>=right,"BCS":lambda x:x<right,
                    "BHI":lambda x:x>right,"BLS":lambda x:x<=right,
                    "BGE":lambda x:signed(x)>=signed(right),"BLT":lambda x:signed(x)<signed(right),
                    "BGT":lambda x:signed(x)>signed(right),"BLE":lambda x:signed(x)<=signed(right)}
        if op not in conditions:return state
        condition=conditions[op]
    remaining={x for x in values if condition(x)==taken}
    if not remaining:return None
    state.put(register,Value.of(lhs.bits,remaining))
    state.predicate=pred
    return state


def analyze(rom, entry, instructions, summaries, dispatch_targets=(), call_override=None):
    states={entry:State.entry()}; queue=deque([entry]); queued={entry}
    local,effects,calls={}, {}, {};opaque=set(); returns={};iterations=0
    while queue:
        pc=queue.popleft();queued.remove(pc);iterations+=1
        if iterations>200000:
            raise ValueError(f"Dataflow did not converge at {entry:04X}")
        ins=instructions[pc];state=states[pc].copy()
        access=ins.access()
        if access:
            effect=Effect(pc,access["access"],access["width_bits"],effective(state,ins))
            add_effect(local,effect);add_effect(effects,effect)
        if ins.op in {"JSR","BSR"}:
            target=Value.const(16,ins.target) if ins.target is not None else effective(state,ins)
            bindings={**state.regs,"C":state.carry}
            old=calls.get(pc)
            if old:
                target=old[0].join(target)
                bindings={r:old[1][r].join(bindings[r]) for r in bindings}
            calls[pc]=(target,bindings)
            destinations=target.ints()
            # The independently verified main table supplies the dependency
            # order. Actual flow must still recover the same destination set.
            if pc==0x7A4F and destinations is not None and set(destinations)!=set(dispatch_targets):
                raise ValueError("Recovered main-dispatch targets differ from ROM table")
            outputs=[]
            for destination in sorted(destinations) if destinations else [None]:
                out=state.copy()
                handled=call_override and call_override(rom,out,destination,pc,effects)
                if not handled:apply_call(out,summaries.get(destination),pc,effects,opaque)
                outputs.append(out)
            state=outputs[0]
            for out in outputs[1:]:state=state.join(out)
        elif ins.op=="RTS":
            state.put("SP",add_constant(state.get("SP"),2));returns[pc]=state
            continue
        elif ins.op in TERMINALS:
            continue
        else:
            transfer(rom,state,ins)
        for target,kind in successors(ins):
            if target not in instructions:continue
            next_state=branch_state(state,ins.op,kind=="branch_taken") if kind.startswith("branch_") and ins.op not in {"BRSET","BRCLR"} else state
            if next_state is None:continue
            joined=next_state if target not in states else states[target].join(next_state)
            if target not in states or joined!=states[target]:
                states[target]=joined
                if target not in queued:queue.append(target);queued.add(target)
    if returns:
        returned=list(returns.values());result=returned[0]
        for other in returned[1:]:result=result.join(other)
        outputs,carry=result.regs,result.carry
    else:
        outputs={r:Value(8 if r in {"A","B"} else 16) for r in ["A","B","X","Y","SP"]};carry=Value(1)
    return Summary(entry,outputs,carry,local,effects,calls,opaque,states,len(returns),iterations)
