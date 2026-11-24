"""Bounded read-transaction witnesses using actual retained HC11 instructions.

Memory is controlled byte storage. No peripheral completion, read side effect,
physical bus cycle, resource relocation or hardware alias is simulated here.
"""
from collections import Counter, defaultdict

from factory_rom_decode import decode
from verify_revb_xdf_labels import HC11CPU, HC11Memory


class Memory(HC11Memory):
    def __init__(self, contents):
        super().__init__()
        self.mem[:] = contents
        self.reads = []
        self.fetching = False

    def read8(self, address):
        address &= 65535
        value = self.mem[address]
        self.reads.append((address, value, self.fetching))
        return value

    def write8(self, address, value):
        self.mem[address & 65535] = value & 255

    def tick(self, cycles):
        self.cycle_counter += cycles


class CPU(HC11CPU):
    def _fetch8(self):
        old = self.mem.fetching
        self.mem.fetching = True
        try:
            return super()._fetch8()
        finally:
            self.mem.fetching = old

    def _fetch16(self):
        old = self.mem.fetching
        self.mem.fetching = True
        try:
            return super()._fetch16()
        finally:
            self.mem.fetching = old


def execute(contents, entry, stops, x=0, frame=None, long=False):
    memory = Memory(contents)
    cpu = CPU(memory)
    cpu.s.pc, cpu.s.sp, cpu.s.ccr, cpu.s.x = entry, 0x3ff, 0xd0, x
    if frame:
        frame(cpu)
    else:
        cpu._push16(0x7000)
    events, addresses, counts = [], defaultdict(set), Counter()
    for _ in range(500000 if long else 4000):
        if cpu.s.pc in stops:
            return memory, cpu, events, addresses, counts
        pc = cpu.s.pc
        instruction = decode(lambda a,n: memory.mem[a:a+n], pc)
        memory.reads.clear()
        cpu.step()
        # Distinguish instruction-byte fetches from subsequent operand/stack
        # reads in this interpreter; this is not a cycle-accurate bus analyzer.
        assert [a for a, _, fetch in memory.reads if fetch] == list(range(pc, instruction.next_pc))
        data_reads = [(a, v) for a, v, fetch in memory.reads if not fetch]
        for address, value in data_reads:
            addresses[pc].add(address)
            counts[pc] += 1
            if not long:
                events.append(dict(pc=f"{pc:04X}", address=f"{address:04X}", value=f"{value:02X}"))
        assert not (cpu.halted or cpu.waiting)
    raise AssertionError("Read witness exceeded its instruction budget")


def fresh(image):
    result = bytearray(image)
    result[:0x400] = bytes(0x400)
    result[0x800:0x900] = bytes(0x100)
    return result


def put(image, address, value):
    image[address:address+2] = value.to_bytes(2, "big")


def run(image):
    cases = []

    def record(name, entry, stops, memory, x=0, expected=None):
        m, cpu, events, _, _ = execute(memory, entry, stops, x=x)
        if expected:
            expected(m, cpu, events)
        cases.append(dict(name=name, entry=f"{entry:04X}", stop=f"{cpu.s.pc:04X}",
                          reads=events, A=f"{cpu.s.a:02X}", B=f"{cpu.s.b:02X}", X=f"{cpu.s.x:04X}"))
        return m, cpu, events

    for value in (0x0b, 0x0a):
        b = fresh(image)
        b[0x303f] = value
        m, cpu, events = record(f"CONFIG comparison {value:02X}", 0x71c6, {0x71d2, 0x71ec}, b)
        assert cpu.s.pc == (0x71d2 if value == 0x0b else 0x71ec)
        assert events[0]["address"] == "303F"
    for value in (0, 0x80):
        b = fresh(image)
        b[0x3030] = value
        _, cpu, events = record(f"ADC status gate {value:02X}", 0xf267, {0xf26b, 0xf274}, b, x=0x3000)
        assert cpu.s.pc == (0xf274 if value else 0xf26b)
        assert events == [dict(pc="F267", address="3030", value=f"{value:02X}")]
    sample_cases = [
        ("Fast TPS", 0xf24c, 0xf250, 0x3031, 0x00a6, False),
        ("Fast MAP", 0xf254, 0xf259, 0x3032, 0x082e, False),
        ("Fast O2", 0xf259, 0xf25e, 0x3033, 0x01d5, False),
        ("Raw coolant", 0xf21a, 0xf21f, 0x3034, 0x082d, False),
        ("Battery spark/idle sample", 0xf23f, 0xf243, 0x3034, 0x00a7, False),
        ("Battery REF sample", 0xc57d, 0xc582, 0x3034, 0x0055, False),
        ("Auxiliary raw sample", 0xf236, 0xf23b, 0x3032, 0x082f, False),
        ("Inverted raw MAT", 0xdc0a, 0xdc10, 0x3034, 0x0230, True),
    ]
    for name, entry, stop, source, dest, invert in sample_cases:
        b = fresh(image)
        b[source] = 0x53
        m, _, events = record(name, entry, {stop}, b, x=0x3000)
        assert m.mem[dest] == (0xac if invert else 0x53)
        assert events == [dict(pc=f"{entry:04X}", address=f"{source:04X}", value="53")]
    b = fresh(image)
    put(b, 0x3fc0, 0x1234)
    _, cpu, events = record("Reference-period word", 0xa5e5, {0xa5e8}, b)
    assert cpu.s.d == 0x1234 and [e["address"] for e in events] == ["3FC0", "3FC1"]
    b = fresh(image)
    b[0x302e], b[0x302f] = 0x20, 0x5a
    _, cpu, events = record("SCI status before received data", 0xf90b, {0xf911}, b)
    assert (cpu.s.b, cpu.s.a) == (0x20, 0x5a)
    assert [e["address"] for e in events] == ["302E", "302F"]
    b = fresh(image)
    put(b, 0x3ffc, 0xbeef)
    _, cpu, events = record("Shared hardware word readback", 0xf3ef, {0xf3f5}, b)
    assert cpu.s.d == 0xbeef
    assert [e["address"] for e in events if int(e["address"],16) >= 0x3000] == ["3FFC", "3FFD"]
    b = fresh(image)
    b[0x3060], b[0x3064], b[0x4b], b[0x4c], b[0x4e] = 0x65, 0x26, 0x90, 0x1c, 0xa5
    m, _, events = record("Board inputs versus saved output shadows", 0xf400, {0xf41f}, b)
    assert m.mem[0x4d] == 0x26
    assert [e["address"] for e in events] == ["3060", "004B", "004C", "3064", "004E"]
    for mode in (0, 8):
        b = fresh(image)
        b[0x50] = mode
        put(b, 0x024a, 0xa55a)
        put(b, 0x124a, 0x4567)
        m, cpu, events = record(f"Addressed ALDL actual source, flag={mode}", 0xf8b8, {0xf8cf}, b, x=0x124a)
        target, result = (0x124a, 0x4567) if mode else (0x024a, 0xa55a)
        assert cpu.s.d == result and m.mem[0x366] == result & 255
        assert [e["address"] for e in events if e["pc"] == "F8CA"] == [f"{target:04X}", f"{target+1:04X}"]
    b = fresh(image)
    _, cpu, events = record("Descriptor pointer read, not AFR-value write", 0xf888, {0xf88a}, b, x=0x520d)
    assert cpu.s.x == 0x024a and [e["address"] for e in events] == ["5216", "5217"]
    _, cpu, events = record("Lookup header byte", 0xf4b8, {0xf4ba}, fresh(image), x=0x50a2)
    assert cpu.s.b == image[0x50a2] and events[0]["address"] == "50A2"

    # Every byte read by the admitted boot checksum, with addresses observed
    # from the CPU. Recorded replay checks a partial/synthetic memory's sum;
    # it cannot recover the released checksum from missing full-ROM data.
    b = fresh(image)
    m, cpu, _, addresses, counts = execute(b, 0xf2aa, {0xf2fc}, x=0x4008, long=True)
    assert cpu.s.y == sum(b[0x4008:]) & 65535
    checksum = []
    for offset, pc in enumerate((0xf2c7,0xf2cb,0xf2cf,0xf2d3,0xf2d7,0xf2db,0xf2df,0xf2e3)):
        expected_addresses = set(range(0x4008 + offset, 65536, 8))
        assert addresses[pc] == expected_addresses and counts[pc] == len(expected_addresses) == 6143
        checksum.append(dict(pc=f"{pc:04X}", start=f"{min(expected_addresses):04X}",
            end=f"{max(expected_addresses):04X}", stride=8, reads=counts[pc]))
    assert 0xf2b9 not in addresses
    cases.append(dict(name="Boot checksum read footprint", entry="F2AA", X="4008",
        ranges=checksum, distinct_data_bytes=49144, sum_matches_supplied_fixture=True,
        qualification="Call71D5 supplies4008 when CONFIG gate passes; recorded replay uses partial/synthetic data, not recovered whole-ROM contents"))

    def interrupt_frame(cpu):
        cpu._push16(0x7000)
        cpu._push16(0x1122)
        cpu._push16(0x3344)
        cpu._push8(0x55)
        cpu._push8(0x66)
        cpu._push8(0xd0)

    _, cpu, events, _, _ = execute(fresh(image), 0xfc44, {0x7000}, frame=interrupt_frame)
    assert len(events) == 9 and (cpu.s.x, cpu.s.y, cpu.s.a, cpu.s.b) == (0x3344,0x1122,0x55,0x66)
    cases.append(dict(name="Implicit RTI frame reads", entry="FC44", reads=events,
                      qualification="Controlled valid frame; no fixed runtime stack-owner proof"))
    return dict(cases=cases, count=len(cases), scope=__doc__.strip())
