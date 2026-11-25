"""Independent instruction catalogue transcribed from Motorola M68HC11RM Rev 6.1.

This is test data, never imported by either CPU implementation. Appendix A's
individual encoding/cycle/CCR tables are the authority, not either decoder.
Page numbers below are the document's printed numbers (also PDF page numbers).
00 TEST is special-test-mode-only and is not a normal-mode instruction.
"""
from dataclasses import dataclass

SOURCE = "https://www.nxp.com/docs/en/reference-manual/M68HC11RM.pdf"


@dataclass(frozen=True)
class Instruction:
    prefix: int | None
    opcode: int
    mnemonic: str
    mode: str
    cycles: int
    modified_ccr: str
    page: int

    @property
    def encoding(self):
        return bytes(([self.prefix] if self.prefix is not None else []) + [self.opcode])

    @property
    def key(self):
        return self.encoding.hex(" ").upper()

    @property
    def size(self):
        return len(self.encoding) + {
            "inh": 0, "imm8": 1, "imm16": 2, "dir": 1, "ext": 2,
            "x": 1, "y": 1, "rel": 1, "bitdir": 2, "bitx": 2,
            "bity": 2, "bitreldir": 3, "bitrelx": 3, "bitrely": 3,
        }[self.mode]


def catalogue():
    result = {}

    def add(op, name, mode, cycles, flags="", page=491, prefix=None):
        spec = Instruction(prefix, op, name, mode, cycles, flags, page)
        assert (prefix, op) not in result
        result[prefix, op] = spec

    # Inherent instructions; X in the TAP/RTI mask means clear-only.
    rows = [
        (0x01,"NOP",2,"",562),(0x02,"IDIV",41,"ZVC",544),
        (0x03,"FDIV",41,"ZVC",543),(0x04,"LSRD",3,"NZVC",559),
        (0x05,"ASLD",3,"NZVC",500),(0x06,"TAP",2,"SXHINZVC",589),
        (0x07,"TPA",2,"",592),(0x08,"INX",3,"Z",547),
        (0x09,"DEX",3,"Z",540),(0x0A,"CLV",2,"V",530),
        (0x0B,"SEV",2,"V",578),(0x0C,"CLC",2,"C",527),
        (0x0D,"SEC",2,"C",576),(0x0E,"CLI",2,"I",528),
        (0x0F,"SEI",2,"I",577),(0x10,"SBA",2,"NZVC",574),
        (0x11,"CBA",2,"NZVC",526),(0x16,"TAB",2,"NZV",588),
        (0x17,"TBA",2,"NZV",590),(0x19,"DAA",2,"NZVC",536),
        (0x1B,"ABA",2,"HNZVC",492),(0x30,"TSX",3,"",594),
        (0x31,"INS",3,"",546),(0x32,"PULA",4,"",567),
        (0x33,"PULB",4,"",567),(0x34,"DES",3,"",539),
        (0x35,"TXS",3,"",596),(0x36,"PSHA",3,"",564),
        (0x37,"PSHB",3,"",564),(0x38,"PULX",5,"",568),
        (0x39,"RTS",5,"",573),(0x3A,"ABX",3,"",493),
        (0x3B,"RTI",12,"SXHINZVC",572),(0x3C,"PSHX",4,"",565),
        # WAI's step stops in the wait state: 12 before wait, then n idle
        # clocks and 2 vector-fetch clocks when an interrupt is accepted.
        (0x3D,"MUL",10,"C",560),(0x3E,"WAI",12,"",598),
        (0x3F,"SWI",14,"I",587),(0x8F,"XGDX",3,"",600),
        (0xCF,"STOP",2,"",581),
    ]
    for op,name,cycles,flags,page in rows:
        add(op,name,"inh",cycles,flags,page)
    for op,name,cycles,page in [
        (0x08,"INY",4,548),(0x09,"DEY",4,541),(0x30,"TSY",4,595),
        (0x35,"TYS",4,597),(0x38,"PULY",6,569),(0x3A,"ABY",4,494),
        (0x3C,"PSHY",5,566),(0x8F,"XGDY",4,601),
    ]:
        add(op,name,"inh",cycles,"Z" if name in {"INY","DEY"} else "",page,0x18)

    for op,name,page in [(0x12,"BRSET",521),(0x13,"BRCLR",519),(0x14,"BSET",522),(0x15,"BCLR",503)]:
        branch = name.startswith("BR")
        add(op,name,"bitreldir" if branch else "bitdir",6,"" if branch else "NZV",page)
        indexed_op = op + (12 if branch else 8)
        for prefix,mode,cycles in [(None,"x",7),(0x18,"y",8)]:
            add(indexed_op,name,("bitrel" if branch else "bit")+mode,cycles,"" if branch else "NZV",page,prefix)

    branches = ["BRA","BRN","BHI","BLS","BCC","BCS","BNE","BEQ","BVC","BVS","BPL","BMI","BGE","BLT","BGT","BLE"]
    branch_pages=(518,520,508,513,502,504,516,505,524,525,517,515,506,514,507,511)
    for op,(name,page) in enumerate(zip(branches,branch_pages),0x20):
        add(op,name,"rel",3,"",page)
    add(0x8D,"BSR","rel",6,"",523)
    for op,mode,cycles,prefix in [(0x9D,"dir",5,None),(0xAD,"x",6,None),(0xBD,"ext",6,None),(0xAD,"y",7,0x18)]:
        add(op,"JSR",mode,cycles,"",550,prefix)

    unary = [(0,"NEG","NZVC",561),(3,"COM","NZVC",532),(4,"LSR","NZVC",558),
             (6,"ROR","NZVC",571),(7,"ASR","NZVC",501),(8,"ASL","NZVC",499),
             (9,"ROL","NZVC",570),(10,"DEC","NZV",538),(12,"INC","NZV",545),
             (13,"TST","NZVC",593),(15,"CLR","NZVC",529)]
    for low,name,flags,page in unary:
        for base,mode,suffix,cycles,prefix in [(0x40,"inh","A",2,None),(0x50,"inh","B",2,None),(0x60,"x","",6,None),(0x70,"ext","",6,None),(0x60,"y","",7,0x18)]:
            add(base+low,name+suffix,mode,cycles,flags,page,prefix)
    for op,mode,cycles,prefix in [(0x6E,"x",3,None),(0x7E,"ext",3,None),(0x6E,"y",4,0x18)]:
        add(op,"JMP",mode,cycles,"",549,prefix)

    alu = [(0,"SUB","NZVC",585),(1,"CMP","NZVC",531),(2,"SBC","NZVC",575),
           (4,"AND","NZV",498),(5,"BIT","NZV",510),(6,"LD","NZV",551),
           (8,"EOR","NZV",542),(9,"ADC","HNZVC",495),(10,"ORA","NZV",563),
           (11,"ADD","HNZVC",496)]
    for reg,base in [("A",0x80),("B",0xC0)]:
        for low,name,flags,page in alu:
            mnemonic = ("LDA" if name == "LD" else name) + reg
            for delta,mode,cycles,prefix in [(0,"imm8",2,None),(0x10,"dir",3,None),(0x20,"x",4,None),(0x30,"ext",4,None),(0x20,"y",5,0x18)]:
                add(base+delta+low,mnemonic,mode,cycles,flags,page,prefix)
        for delta,mode,cycles,prefix in [(0x10,"dir",3,None),(0x20,"x",4,None),(0x30,"ext",4,None),(0x20,"y",5,0x18)]:
            add(base+delta+7,"STA"+reg,mode,cycles,"NZV",579,prefix)

    for name,base,first,flags,page in [("SUBD",0x83,4,"NZVC",586),("ADDD",0xC3,4,"NZVC",497),("LDD",0xCC,3,"NZV",552),("LDS",0x8E,3,"NZV",553)]:
        for delta,mode,extra,prefix in [(0,"imm16",0,None),(0x10,"dir",1,None),(0x20,"x",2,None),(0x30,"ext",2,None),(0x20,"y",3,0x18)]:
            add(base+delta,name,mode,first+extra,flags,page,prefix)
    for name,base,page in [("STD",0xCD,580),("STS",0x8F,582)]:
        for delta,mode,cycles,prefix in [(0x10,"dir",4,None),(0x20,"x",5,None),(0x30,"ext",5,None),(0x20,"y",6,0x18)]:
            add(base+delta,name,mode,cycles,"NZV",page,prefix)
    for name,base,first,page in [("CPX",0x8C,4,534),("LDX",0xCE,3,554)]:
        for delta,mode,extra,prefix in [(0,"imm16",0,None),(0x10,"dir",1,None),(0x20,"x",2,None),(0x30,"ext",2,None),(0x20,"y",3,0xCD)]:
            add(base+delta,name,mode,first+extra,"NZVC" if name=="CPX" else "NZV",page,prefix)
    for name,base,first,page in [("CPY",0x8C,5,535),("LDY",0xCE,4,555)]:
        for delta,mode,extra,prefix in [(0,"imm16",0,0x18),(0x10,"dir",1,0x18),(0x20,"x",2,0x1A),(0x30,"ext",2,0x18),(0x20,"y",2,0x18)]:
            add(base+delta,name,mode,first+extra,"NZVC" if name=="CPY" else "NZV",page,prefix)
    for name,page,rows in [
        ("STX",583,[(0xDF,"dir",4,None),(0xEF,"x",5,None),(0xFF,"ext",5,None),(0xEF,"y",6,0xCD)]),
        ("STY",584,[(0xDF,"dir",5,0x18),(0xEF,"x",6,0x1A),(0xFF,"ext",6,0x18),(0xEF,"y",6,0x18)]),
        ("CPD",533,[(0x83,"imm16",5,0x1A),(0x93,"dir",6,0x1A),(0xA3,"x",7,0x1A),(0xB3,"ext",7,0x1A),(0xA3,"y",7,0xCD)]),
    ]:
        for op,mode,cycles,prefix in rows:
            add(op,name,mode,cycles,"NZVC" if name=="CPD" else "NZV",page,prefix)
    return result


ISA = catalogue()
UNIMPLEMENTED_LEGACY = {"DAA", "BRN", "STOP"}
CCR = dict(zip("SXHINZVC", (128,64,32,16,8,4,2,1)))
