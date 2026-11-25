#!/usr/bin/env python3
"""Manual-derived HC11 conformance tests, independent of either decoder.

Run: python tests/audit/test_hc11_isa.py [--repo CHECKOUT] [--matrix OUT.json]
AUDIT_REPO is an equivalent checkout selector. No BIN or third-party packages
are needed. The test oracle never imports production flag/address helpers.
"""
import importlib
import json
import os
from pathlib import Path
import sys
import unittest

from hc11_isa_spec import ISA, CCR, SOURCE, UNIMPLEMENTED_LEGACY

HERE = Path(__file__).resolve()
REPO = Path(os.environ.get("AUDIT_REPO", HERE.parents[2])).resolve()
if "--repo" in sys.argv:
    i = sys.argv.index("--repo")
    REPO = Path(sys.argv[i + 1]).resolve()
    del sys.argv[i:i + 2]
MATRIX = None
if "--matrix" in sys.argv:
    i = sys.argv.index("--matrix")
    MATRIX = Path(sys.argv[i + 1])
    del sys.argv[i:i + 2]
sys.path.insert(0, str(REPO / "hac31_romsim"))
sys.path.insert(0, str(REPO / "7427_simulator"))
legacy = importlib.import_module("romsim.hc11_core")
modern = importlib.import_module("sim7427.cpu")

REGS = ("a", "b", "x", "y", "sp", "pc", "ccr")
BOUND8 = (0, 1, 0x0F, 0x10, 0x7F, 0x80, 0xFE, 0xFF)
BOUND16 = (0, 1, 0xFF, 0x100, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF)
OPERANDS = tuple(sorted(set(BOUND8) | set(BOUND16)))


class FlatMemory:
    """Deliberately no PCM overlays, timers, or production bus implementation."""
    def __init__(self):
        self.mem = bytearray(65536)
        self.cycle_counter = 0
        self.writes = []

    def read8(self, address):
        return self.mem[address & 0xFFFF]

    def read16(self, address):
        return self.read8(address) * 256 + self.read8(address + 1)

    def write8(self, address, value):
        self.mem[address & 0xFFFF] = value & 255
        self.writes.append((address & 0xFFFF, value & 255))

    def write16(self, address, value):
        self.write8(address, value // 256)
        self.write8(address + 1, value)

    def tick(self, cycles):
        self.cycle_counter += cycles

    def reset(self):
        self.cycle_counter = 0


def cpu_for(which, code=b"", pc=0x6000):
    mem = FlatMemory()
    for i, byte in enumerate(code):
        mem.mem[(pc + i) & 65535] = byte
    cpu = legacy.HC11CPU(mem) if which == "legacy" else modern.CPU(mem)
    r = cpu.s if which == "legacy" else cpu.r
    r.pc, r.sp, r.x, r.y = pc, 0x4000, 0x2100, 0x3100
    return cpu, r, mem


def signed(value, bits):
    return value if value < (1 << (bits - 1)) else value - (1 << bits)


def arithmetic(a, b, bits, carry=0, subtract=False):
    """Range-based mathematical oracle; no production bitwise overflow formula."""
    modulus = 1 << bits
    full = a - b - carry if subtract else a + b + carry
    signed_full = signed(a,bits) - signed(b,bits) - carry if subtract else signed(a,bits) + signed(b,bits) + carry
    value = full % modulus
    flags = {"N": value >= modulus//2, "Z": value == 0,
             "V": not (-modulus//2 <= signed_full < modulus//2),
             "C": full < 0 if subtract else full >= modulus}
    if not subtract and bits == 8:
        flags["H"] = (a % 16 + b % 16 + carry) >= 16
    return value, flags


def nz(value, bits=8):
    return {"N": value >= 1 << (bits-1), "Z": value == 0, "V": False}


def setflags(r, flags):
    for flag, value in flags.items():
        r["ccr"] = (r["ccr"] | CCR[flag]) if value else (r["ccr"] & ~CCR[flag])


def putreg(r, name, value):
    if name == "d":
        r["a"], r["b"] = divmod(value,256)
    else:
        r[name] = value


def getreg(r, name):
    return r["a"] * 256 + r["b"] if name == "d" else r[name]


def fixture(spec, value, operand, ccr, which):
    cpu, r, mem = cpu_for(which)
    r.a, r.b, r.ccr = value & 255, value & 255, ccr
    if spec.mnemonic in {"IDIV", "FDIV", "LSRD", "ASLD", "CPD", "SUBD", "ADDD", "STD", "XGDX", "XGDY"}:
        r.d = value
    if spec.mnemonic in {"INX", "DEX", "CPX", "ABX", "TXS", "PSHX", "STX"}:
        r.x = value
    if spec.mnemonic in {"INY", "DEY", "CPY", "ABY", "TYS", "PSHY", "STY"}:
        r.y = value
    if spec.mnemonic in {"TSX", "TSY", "INS", "DES", "STS"}:
        r.sp = value
    if spec.mnemonic in {"IDIV", "FDIV"}:
        r.x = operand
    # A distinct B operand makes ABA/SBA/CBA and MUL meaningful.
    if spec.mnemonic in {"ABA", "SBA", "CBA", "MUL", "TAB", "TBA"}:
        r.b = operand & 255
    mode, encoded = spec.mode, bytearray(spec.encoding)
    addr = None
    if mode == "imm8":
        encoded += bytes([operand & 255])
    elif mode == "imm16":
        encoded += bytes([operand >> 8, operand & 255])
    elif mode == "rel":
        encoded += bytes([operand & 255])
    elif mode.endswith("dir") or mode == "dir":
        addr = 0x80
        encoded += b"\x80"
    elif mode == "ext":
        addr = 0x5080
        encoded += b"\x50\x80"
    elif mode.endswith("x") or mode.endswith("y"):
        reg = "x" if mode.endswith("x") else "y"
        # Nonzero, unsigned offset. X/Y may themselves be comparison operands.
        addr = (getattr(r,reg) + 0xE1) & 65535
        encoded += b"\xE1"
    if mode.startswith("bit"):
        encoded += bytes([operand & 255])
        if mode.startswith("bitrel"):
            encoded += b"\x80"
    if addr is not None:
        isword = spec.mnemonic in {"CPD","CPX","CPY","LDD","LDS","LDX","LDY","SUBD","ADDD"}
        if isword:
            mem.write16(addr, operand)
        else:
            mem.write8(addr,value if mode.startswith("bit") else operand)
    # Defined stack bytes permit single-step checking of pulls and RTI.
    for i, byte in enumerate((ccr ^ 0x7F,0x34,0x12,0xA5,0x5A,0xB6,0x6B,0x72,0x73),1):
        mem.mem[(r.sp+i)&65535] = byte
    mem.mem[0xFFF6:0xFFF8] = b"\x71\x23"
    for i,byte in enumerate(encoded):
        mem.mem[(r.pc+i)&65535] = byte
    mem.writes.clear()
    return cpu, r, mem, addr, operand


def reference(spec, old, data, addr, operand):
    """Architectural state only, not a bus-cycle or interrupt-interleaving model."""
    r, memory, writes = dict(old), bytearray(data), []
    name, mode = spec.mnemonic, spec.mode
    r["pc"] = (old["pc"] + spec.size) % 65536

    def write(address,value):
        memory[address % 65536] = value % 256
        writes.append((address % 65536,value % 256))

    def push(value):
        write(r["sp"], value)
        r["sp"] = (r["sp"]-1) % 65536

    def pushword(value):
        push(value % 256)
        push(value // 256)

    def pull():
        r["sp"] = (r["sp"]+1) % 65536
        return memory[r["sp"]]

    def pullword():
        return pull()*256 + pull()

    def software_ccr(value):
        r["ccr"] = (value & ~CCR["X"]) | (value & old["ccr"] & CCR["X"])

    # Values are read from actual fixture bytes, so wrap/address overlap cases
    # are checked without assuming that setup writes cannot overlap.
    val8 = operand & 255 if mode == "imm8" else memory[addr] if addr is not None else None
    val16 = operand if mode == "imm16" else (memory[addr]*256+memory[(addr+1)%65536]) if addr is not None else None
    c = bool(old["ccr"] & 1)
    if name in {"NOP","STOP"}:
        pass
    elif name in {"IDIV","FDIV"}:
        numerator,denominator = getreg(old,"d"),old["x"]
        overflow = name == "FDIV" and numerator >= denominator
        if not denominator or overflow:
            r["x"] = 65535
            # The manual specifies an indeterminate remainder. Do not bless
            # the emulator's chosen D as a hardware requirement.
            r["a"] = r["b"] = None
        else:
            r["x"], remainder = divmod(numerator * (65536 if name=="FDIV" else 1),denominator)
            putreg(r,"d",remainder)
        setflags(r,{"Z":r["x"]==0,"V":overflow,"C":denominator==0})
    elif name in {"TAP","TPA"}:
        if name == "TAP": software_ccr(old["a"])
        else: r["a"] = old["ccr"]
    elif name in {"INX","INY","DEX","DEY","INS","DES"}:
        reg = "sp" if name.endswith("S") else name[-1].lower()
        r[reg] = (old[reg] + (1 if name.startswith("IN") else -1)) % 65536
        if reg != "sp": setflags(r,{"Z":r[reg]==0})
    elif name in {"CLC","SEC","CLI","SEI","CLV","SEV"}:
        setflags(r,{name[-1]:name.startswith("SE")})
    elif name in {"ABA","SBA","CBA"}:
        result,flags=arithmetic(old["a"],old["b"],8,subtract=name!="ABA")
        if name != "CBA": r["a"] = result
        setflags(r,flags)
    elif name in {"TAB","TBA"}:
        dst,src=("b","a") if name=="TAB" else ("a","b")
        r[dst]=old[src]
        setflags(r,nz(r[dst]))
    elif name in {"TSX","TSY","TXS","TYS"}:
        if name.startswith("TS"): r[name[-1].lower()]=(old["sp"]+1)%65536
        else: r["sp"]=(old[name[1].lower()]-1)%65536
    elif name.startswith("PSH"):
        value=old[name[-1].lower()]
        (pushword if name[-1] in "XY" else push)(value)
    elif name.startswith("PUL"):
        r[name[-1].lower()] = pullword() if name[-1] in "XY" else pull()
    elif name in {"ABX","ABY"}:
        reg=name[-1].lower(); r[reg]=(old[reg]+old["b"])%65536
    elif name in {"XGDX","XGDY"}:
        reg=name[-1].lower(); putreg(r,"d",old[reg]); r[reg]=getreg(old,"d")
    elif name=="MUL":
        result=old["a"]*old["b"]; putreg(r,"d",result); setflags(r,{"C":bool(result & 128)})
    elif name in {"WAI","SWI"}:
        for key in ("pc","y","x"): pushword(r[key])
        for key in ("a","b","ccr"): push(r[key])
        if name=="SWI":
            setflags(r,{"I":True}); r["pc"]=memory[0xFFF6]*256+memory[0xFFF7]
    elif name=="RTS": r["pc"]=pullword()
    elif name=="RTI":
        software_ccr(pull())
        r["b"],r["a"]=pull(),pull()
        r["x"],r["y"],r["pc"]=pullword(),pullword(),pullword()
    elif name in {"JSR","BSR","JMP"}:
        target=(r["pc"]+signed(operand&255,8))%65536 if name=="BSR" else addr
        if name != "JMP": pushword(r["pc"])
        r["pc"]=target
    elif name in {"BRSET","BRCLR","BSET","BCLR"}:
        mask=operand & 255; value=memory[addr]
        if name in {"BSET","BCLR"}:
            result=value | mask if name=="BSET" else value & (255-mask)
            write(addr,result); setflags(r,nz(result))
        elif (value & mask == mask) if name=="BRSET" else (value & mask == 0):
            r["pc"]=(r["pc"]-128)%65536
    elif mode=="rel":
        n,z,v,c=(bool(old["ccr"]&CCR[x]) for x in "NZVC")
        cond={"BRA":True,"BRN":False,"BHI":not(c or z),"BLS":c or z,
              "BCC":not c,"BCS":c,"BNE":not z,"BEQ":z,"BVC":not v,
              "BVS":v,"BPL":not n,"BMI":n,"BGE":n==v,"BLT":n!=v,
              "BGT":not z and n==v,"BLE":z or n!=v}[name]
        if cond: r["pc"]=(r["pc"]+signed(operand&255,8))%65536
    elif name in {"LDAA","LDAB","LDD","LDS","LDX","LDY"}:
        reg={"LDAA":"a","LDAB":"b","LDD":"d","LDS":"sp","LDX":"x","LDY":"y"}[name]
        bits=8 if reg in {"a","b"} else 16; value=val8 if bits==8 else val16
        putreg(r,reg,value); setflags(r,nz(value,bits))
    elif name in {"STAA","STAB","STD","STS","STX","STY"}:
        reg={"STAA":"a","STAB":"b","STD":"d","STS":"sp","STX":"x","STY":"y"}[name]
        bits=8 if reg in {"a","b"} else 16; value=getreg(old,reg)
        if bits==16: write(addr,value//256); write(addr+1,value)
        else: write(addr,value)
        setflags(r,nz(value,bits))
    elif name in {"SUBD","ADDD","CPD","CPX","CPY"}:
        reg=name[-1].lower()
        result,flags=arithmetic(getreg(old,reg),val16,16,subtract=name!="ADDD")
        if name in {"ADDD","SUBD"}: putreg(r,"d",result)
        setflags(r,flags)
    elif name[:-1] in {"SUB","CMP","SBC","AND","BIT","EOR","ADC","ORA","ADD"}:
        reg=name[-1].lower(); operation=name[:-1]; a=old[reg]
        if operation in {"SUB","CMP","SBC","ADC","ADD"}:
            result,flags=arithmetic(a,val8,8,int(c) if operation in {"SBC","ADC"} else 0,operation in {"SUB","CMP","SBC"})
        else:
            result= a&val8 if operation in {"AND","BIT"} else a^val8 if operation=="EOR" else a|val8
            flags=nz(result)
        if operation not in {"CMP","BIT"}: r[reg]=result
        setflags(r,flags)
    else:
        # Unary operations have shared architectural rules in Appendix A.
        reg=name[-1].lower() if mode=="inh" else None
        operation=name[:-1] if reg is not None else name
        bits=16 if reg=="d" else 8; modulus=1<<bits
        value=getreg(old,reg) if reg is not None else memory[addr]
        result=value; flags={}
        if operation=="NEG": result=(-value)%modulus; flags={"C":value!=0,"V":value==modulus//2}
        elif operation=="COM": result=modulus-1-value; flags={"C":True,"V":False}
        elif operation=="CLR": result=0; flags={"C":False,"V":False}
        elif operation=="TST": flags={"C":False,"V":False}
        elif operation in {"INC","DEC"}:
            result=(value+(1 if operation=="INC" else -1))%modulus
            flags={"V":value==(modulus//2-1 if operation=="INC" else modulus//2)}
        elif operation in {"ASL","ROL"}:
            result=(value*2+(int(c) if operation=="ROL" else 0))%modulus
            flags={"C":value>=modulus//2}
            flags["V"]=(result>=modulus//2)!=flags["C"]
        elif operation in {"LSR","ASR","ROR"}:
            result=value//2
            if operation=="ASR" and value>=modulus//2: result+=modulus//2
            if operation=="ROR" and c: result+=modulus//2
            flags={"C":bool(value%2)}; flags["V"]=(result>=modulus//2)!=flags["C"]
        else: raise AssertionError(f"No independent oracle for {spec}")
        flags.update({"N":result>=modulus//2,"Z":result==0})
        setflags(r,flags)
        if operation != "TST":
            if reg is not None: putreg(r,reg,result)
            else: write(addr,result)
    return r,writes


def supported(which,spec):
    cpu,_,_,_,_=fixture(spec,0x7F,0x81,0,which)
    try: cpu.step(); return True
    except (legacy.UnknownOpcode,modern.UnknownInstruction): return False


SUPPORTED = {which:{key for key,spec in ISA.items() if supported(which,spec)} for which in ("legacy","modern")}


class ISAConformance(unittest.TestCase):
    def check_instruction(self,spec,which):
        for value in OPERANDS:
            for operand in OPERANDS:
                for ccr in (0,0xFF,0xE8,0x17):
                    cpu,r,mem,addr,operand=fixture(spec,value,operand,ccr,which)
                    before={key:getattr(r,key) for key in REGS}
                    expected,writes=reference(spec,before,mem.mem,addr,operand)
                    actual_cycles=cpu.step()
                    label=f"{which} {spec.key} {spec.mnemonic}/{spec.mode}: value={value:04X} operand={operand:04X} CCR={ccr:02X}"
                    for key,want in expected.items():
                        if want is not None:
                            self.assertEqual(getattr(r,key),want,f"{label} {key}")
                    self.assertEqual(mem.writes,writes,f"{label} write sequence")
                    if which=="legacy":
                        self.assertEqual(actual_cycles,spec.cycles,f"{label} returned cycles")
                        self.assertEqual(mem.cycle_counter,spec.cycles,f"{label} elapsed cycles")

    def test_known_unsupported_are_explicit(self):
        self.assertEqual({ISA[key].mnemonic for key in ISA if key not in SUPPORTED["legacy"]},UNIMPLEMENTED_LEGACY)

    def test_modern_implemented_opcode_inventory_is_pinned(self):
        expected="01 08 09 0E 0F 14 15 1D 20 22 25 26 27 30 39 3B 43 6F 7E 7F 81 86 8C 8E A7 AD B6 B7 BD C6 CC CE F7 FD FF"
        self.assertEqual(SUPPORTED["modern"],{(None,int(op,16)) for op in expected.split()})

    def test_reset_sets_s_x_i_and_fetches_big_endian_vector(self):
        for which in ("legacy","modern"):
            cpu,r,mem=cpu_for(which)
            mem.write16(0xFFFE,0xA123)
            r.ccr=0
            cpu.reset()
            after=cpu.s if which=="legacy" else cpu.r
            self.assertEqual((after.pc,after.ccr&0xD0),(0xA123,0xD0),which)

    def test_clr_reads_operand_before_write_for_peripheral_side_effects(self):
        class ReadSensitiveMemory(FlatMemory):
            def __init__(self):
                super().__init__();self.pending=True;self.events=[]
            def read8(self,address):
                if address&65535==0x302F:
                    self.pending=False;self.events.append("read")
                return super().read8(address)
            def write8(self,address,value):
                if address&65535==0x302F:self.events.append("write")
                super().write8(address,value)
        for which in ("legacy","modern"):
            for code in (bytes.fromhex("7F302F"),bytes.fromhex("6F2F")):
                with self.subTest(core=which,encoding=code.hex()):
                    mem=ReadSensitiveMemory()
                    mem.mem[0x6000:0x6000+len(code)]=code
                    cpu=legacy.HC11CPU(mem) if which=="legacy" else modern.CPU(mem)
                    r=cpu.s if which=="legacy" else cpu.r
                    r.pc,r.x,r.ccr=0x6000,0x3000,0xFF
                    cpu.step()
                    self.assertEqual(mem.events,["read","write"])
                    self.assertFalse(mem.pending)
                    self.assertEqual(r.ccr,0xF4)

    def test_all_normal_mode_illegal_encodings_are_rejected(self):
        for prefix in (None,0x18,0x1A,0xCD):
            for opcode in range(256):
                if (prefix,opcode) in ISA or (prefix is None and opcode in (0x18,0x1A,0xCD)):
                    continue
                code=bytes(([prefix] if prefix is not None else [])+[opcode,0x20,0x20,0x20])
                with self.subTest(encoding=code[:1 if prefix is None else 2].hex()):
                    cpu,_,mem=cpu_for("legacy",code)
                    with self.assertRaises(legacy.UnknownOpcode): cpu.step()
                    self.assertEqual(mem.writes,[],"invalid opcode must not write before fail-closed")

    def test_all_ccr_values_index_and_stack_transfers(self):
        for key in [(None,8),(None,9),(0x18,8),(0x18,9),(None,0x30),(0x18,0x30),(None,0x35),(0x18,0x35)]:
            spec=ISA[key]
            for ccr in range(256):
                for value in (0,0x7FFF,0x8000,0xFFFF):
                    cpu,r,mem,addr,operand=fixture(spec,value,0,ccr,"legacy")
                    expect,_=reference(spec,{k:getattr(r,k) for k in REGS},mem.mem,addr,operand)
                    cpu.step()
                    self.assertEqual(r.ccr,expect["ccr"],f"{spec.key} CCR={ccr:02X} value={value:04X}")

    def test_add_sub_all_8bit_inputs(self):
        cpu,_,_=cpu_for("legacy")
        for subtract in (False,True):
            fn=cpu._sub8 if subtract else cpu._add8
            for carry in (0,1):
                for a in range(256):
                    for b in range(256):
                        expected,flags=arithmetic(a,b,8,carry,subtract)
                        # The arithmetic helpers are additionally checked exhaustively;
                        # all opcode/address forms have end-to-end tests above.
                        for original in (0,0xF0 | (0x20 if subtract else 0)):
                            cpu.s.ccr=original
                            want={"ccr":original};setflags(want,flags)
                            got=fn(a,b,carry)
                            self.assertEqual((got,cpu.s.ccr),(expected,want["ccr"]),(a,b,carry,subtract,original))

    def test_branch_offset_and_pc_wrap(self):
        for spec in ISA.values():
            if spec.mode!="rel" or spec.mnemonic=="BRN": continue
            for pc in (0,0xFFFE,0xFFFF):
                for offset in (0,0x7F,0x80,0xFF):
                    for ccr in range(16):
                        cpu,r,mem=cpu_for("legacy",spec.encoding+bytes([offset]),pc)
                        r.ccr=ccr
                        before={key:getattr(r,key) for key in REGS}
                        expected,writes=reference(spec,before,mem.mem,None,offset)
                        cpu.step()
                        self.assertEqual((r.pc,r.ccr,mem.writes),(expected["pc"],expected["ccr"],writes),(spec.key,pc,offset,ccr))

    def test_index_offset_unsigned_and_16bit_address_wrap(self):
        for code,reg in [(b"\xA6","x"),(b"\x18\xA6","y")]:
            for base,offset in [(0,0xFF),(0xFF80,0x80),(0xFFFF,1)]:
                cpu,r,mem=cpu_for("legacy",code+bytes([offset]))
                setattr(r,reg,base)
                mem.mem[(base+offset)&65535]=0xA5
                r.ccr=0xF3
                cpu.step()
                self.assertEqual((r.a,r.ccr),(0xA5,0xF9))
        cpu,r,mem=cpu_for("legacy",b"\xFC\xFF\xFF")
        mem.mem[0xFFFF],mem.mem[0]=0x12,0x34
        cpu.step();self.assertEqual(r.d,0x1234)

    def test_jsr_rts_wraps_fetch_and_stack_in_hardware_byte_order(self):
        cpu,r,mem=cpu_for("legacy",bytes.fromhex("BD7000"),pc=0xFFFE)
        r.sp,r.ccr=0,0xAA
        mem.mem[0x7000]=0x39
        cpu.step()
        self.assertEqual((r.pc,r.sp,r.ccr),(0x7000,0xFFFE,0xAA))
        self.assertEqual(mem.writes,[(0,1),(0xFFFF,0)])
        cpu.step()
        self.assertEqual((r.pc,r.sp,r.ccr),(1,0,0xAA))

    def test_interrupt_frame_rti_and_xirq_masks(self):
        for which in ("legacy","modern"):
            for vector in (0xFFF2,0xFFF4):
                for ccr in (0,0x10,0x40,0x50):
                    cpu,r,mem=cpu_for(which)
                    r.a,r.b,r.x,r.y,r.sp,r.ccr=0x12,0x34,0x5678,0x9ABC,0,ccr
                    mem.write16(vector,0x7000);mem.mem[0x7000]=0x3B;mem.writes.clear()
                    before={k:getattr(r,k) for k in REGS}
                    accepted=cpu.interrupt(vector,maskable=vector!=0xFFF4)
                    expected=not(ccr & (0x40 if vector==0xFFF4 else 0x10))
                    self.assertEqual(accepted,expected,(which,vector,ccr))
                    if not accepted:
                        self.assertEqual({k:getattr(r,k) for k in REGS},before)
                        continue
                    expected_frame=[0,0x60,0xBC,0x9A,0x78,0x56,0x12,0x34,ccr]
                    self.assertEqual(mem.writes,[(i%65536,v) for i,v in zip(range(0,-9,-1),expected_frame)])
                    self.assertEqual(r.ccr,ccr|0x10|(0x40 if vector==0xFFF4 else 0))
                    cpu.step()
                    self.assertEqual({k:getattr(r,k) for k in REGS},before)

    def test_cli_defers_irq_through_one_following_instruction(self):
        for which in ("legacy","modern"):
            for initial_ccr in (0,0x10):
                cpu,r,mem=cpu_for(which,b"\x0E\x01\x01")
                r.ccr=initial_ccr
                mem.write16(0xFFF2,0x7000)
                cpu.step()
                self.assertEqual(r.ccr&0x10,0)
                if initial_ccr==0:
                    # RM p528 qualifies the extra instruction by a prior
                    # disabled state; writing an already-clear I adds no delay.
                    self.assertTrue(cpu.interrupt(0xFFF2),which)
                    continue
                self.assertFalse(cpu.interrupt(0xFFF2),(which,initial_ccr))
                self.assertEqual((r.pc,r.sp),(0x6001,0x4000))
                cpu.step()
                self.assertTrue(cpu.interrupt(0xFFF2),(which,initial_ccr))
                self.assertEqual((r.pc,r.sp),(0x7000,0x3FF7))

    def test_cli_sei_loop_never_admits_maskable_irq(self):
        for which in ("legacy","modern"):
            cpu,r,mem=cpu_for(which,b"\x0E\x0F\x20\xFC")
            r.ccr=0x10
            mem.write16(0xFFF2,0x7000)
            for _ in range(9):
                cpu.step()
                self.assertFalse(cpu.interrupt(0xFFF2),which)
            self.assertEqual((r.pc,r.sp),(0x6000,0x4000))

    def test_tap_clear_i_defers_irq_but_rti_does_not(self):
        cpu,r,mem=cpu_for("legacy",b"\x06\x01")
        r.a,r.ccr=0,0x10
        mem.write16(0xFFF2,0x7000);mem.mem[0x7000]=0x3B
        cpu.step()
        self.assertFalse(cpu.interrupt(0xFFF2))
        cpu.step()
        self.assertTrue(cpu.interrupt(0xFFF2))
        cpu.step()  # RTI restores I=0; no instruction from return site yet.
        self.assertEqual(r.pc,0x6002)
        self.assertTrue(cpu.interrupt(0xFFF2))
        cpu,r,mem=cpu_for("legacy",b"\x06\x01")
        r.a,r.ccr=0,0  # I was already clear before TAP.
        mem.write16(0xFFF2,0x7000)
        cpu.step()
        self.assertTrue(cpu.interrupt(0xFFF2))

    def test_cli_wai_completes_prestack_before_pending_irq(self):
        cpu,r,mem=cpu_for("legacy",b"\x0E\x3E")
        r.ccr=0x10
        mem.write16(0xFFF2,0x7000);mem.mem[0x7000]=0x3B;mem.writes.clear()
        cpu.step()
        self.assertFalse(cpu.interrupt(0xFFF2))
        cpu.step()
        self.assertTrue(cpu.waiting)
        self.assertEqual(len(mem.writes),9)
        self.assertTrue(cpu.interrupt(0xFFF2))
        self.assertEqual(len(mem.writes),9)
        cpu.step()
        self.assertEqual((r.pc,r.sp),(0x6002,0x4000))

    def test_cli_deferral_does_not_block_xirq(self):
        for which in ("legacy","modern"):
            cpu,r,mem=cpu_for(which,b"\x0E\x01")
            r.ccr=0x10  # X is clear.
            mem.write16(0xFFF4,0x7000)
            cpu.step()
            self.assertTrue(cpu.interrupt(0xFFF4),which)
            self.assertEqual(r.pc,0x7000)

    def test_wai_prestacks_once_and_preserves_ccr(self):
        cpu,r,mem=cpu_for("legacy",b"\x3E")
        r.ccr=0
        mem.write16(0xFFF2,0x7000);mem.mem[0x7000]=0x3B;mem.writes.clear()
        cpu.step()
        self.assertTrue(cpu.waiting);self.assertEqual((r.sp,r.ccr,len(mem.writes)),(0x3FF7,0,9))
        self.assertEqual(mem.cycle_counter,12)
        self.assertEqual(cpu.step(),0)
        mem.tick(7)  # Seven explicit idle E clocks, no additional stacking.
        self.assertTrue(cpu.interrupt(0xFFF2))
        self.assertFalse(cpu.waiting);self.assertEqual(len(mem.writes),9)
        self.assertEqual(mem.cycle_counter,12+7+2)
        cpu.step();self.assertEqual((r.sp,r.pc,r.ccr),(0x4000,0x6001,0))

    def test_literal_minimal_flag_reproductions(self):
        cases=[(b"\x08",{"x":0x7FFF,"ccr":0},"ccr",0),
               (b"\x09",{"x":0x8000,"ccr":8},"ccr",8),
               (b"\x30",{"sp":0x7FFF,"ccr":0},"ccr",0),
               (b"\x4D",{"a":1,"ccr":1},"ccr",0),
               (b"\x4F",{"a":1,"ccr":1},"ccr",4),
               (b"\x06",{"a":0x40,"ccr":0},"ccr",0)]
        for code,values,key,want in cases:
            with self.subTest(opcode=code.hex()):
                cpu,r,_=cpu_for("legacy",code)
                for k,v in values.items():setattr(r,k,v)
                cpu.step();self.assertEqual(getattr(r,key),want)


for which,keys in SUPPORTED.items():
    for key in sorted(keys,key=lambda k:(k[0] or 0,k[1])):
        spec=ISA[key]
        def test(self,spec=spec,which=which): self.check_instruction(spec,which)
        setattr(ISAConformance,f"test_{which}_{spec.key.replace(' ','_')}_{spec.mnemonic}_{spec.mode}",test)


def matrix():
    rows=[]
    for prefix in (None,0x18,0x1A,0xCD):
        for opcode in range(256):
            spec=ISA.get((prefix,opcode))
            encoding=bytes(([prefix] if prefix is not None else [])+[opcode]).hex(" ").upper()
            row={"encoding":encoding,"normal_mode_legal":spec is not None,
                 "prefix_selector":prefix is None and opcode in (0x18,0x1A,0xCD)}
            if not row["prefix_selector"]:
                for which in ("legacy","modern"):
                    code=bytes(([prefix] if prefix is not None else [])+[opcode,0x20,0x20,0x20])
                    cpu,_,mem=cpu_for(which,code)
                    try:
                        returned=cpu.step()
                        row[which+"_accepts_encoding"]=True
                        if which=="legacy":
                            row["legacy_probe_returned_cycles"]=returned
                            row["legacy_probe_elapsed_cycles"]=mem.cycle_counter
                    except (legacy.UnknownOpcode,modern.UnknownInstruction):
                        row[which+"_accepts_encoding"]=False
            if spec:
                row.update(mnemonic=spec.mnemonic,addressing_mode=spec.mode,bytes=spec.size,
                           documented_cycles=spec.cycles,modified_ccr=spec.modified_ccr,
                           unchanged_ccr="".join(flag for flag in "SXHINZVC" if flag not in spec.modified_ccr),
                           manual_page=spec.page,legacy_implemented=(prefix,opcode) in SUPPORTED["legacy"],
                           modern_implemented=(prefix,opcode) in SUPPORTED["modern"],
                           architectural_vectors_per_core=len(OPERANDS)**2*4,
                           coverage="manual-derived boundary state/CCR/write-sequence/cycle tests" if (prefix,opcode) in SUPPORTED["legacy"] else "explicit unsupported; no semantic implementation",
                           limitations="No cycle-by-cycle bus effects, asynchronous interleavings, or hardware validation; undefined division remainder excluded")
                if spec.mnemonic=="WAI":
                    row["cycle_scope"]="12 before wait; n explicit idle E clocks; 2 on interrupt vector fetch; 14+n complete"
            rows.append(row)
    return {"authority":SOURCE,"authority_revision":"6.1","repo":str(REPO),
            "normal_mode_encoding_count":len(ISA),"test_oracle":"independent mathematical oracle and manually transcribed encoding tables; neither production decoder imported by oracle",
            "rows":rows}


if __name__ == "__main__":
    if MATRIX:
        MATRIX.parent.mkdir(parents=True,exist_ok=True)
        MATRIX.write_text(json.dumps(matrix(),indent=2)+"\n")
    unittest.main()
