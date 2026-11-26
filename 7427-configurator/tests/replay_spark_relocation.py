"""Compare stock and relocated spark tables on the 7427HWContract HC11 emulator."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configurator import SPARK_TABLES, build, defaults, load_stock


def machine(image, cpu_type, memory_type):
    memory = memory_type()
    memory.mem[0x4000:] = image[0x4000:]
    cpu = cpu_type(memory)
    cpu.max_trace = 0
    return cpu, memory


def run(cpu, stop):
    for _ in range(128):
        if cpu.s.pc == stop:
            assert cpu.s.sp == 0x03ff
            return
        cpu.step()
    raise AssertionError(f'budget exhausted at ${cpu.s.pc:04X}')


def spark_base(machine, idle, load, low, high):
    cpu, m = machine
    s = cpu.s
    s.pc, s.sp, s.ccr, s.a, s.b, s.x, s.y = 0xa700, 0x03ff, 0xd0, 0, 0, 0, 0
    for address, value in ((0x50, 0x40 if idle else 0), (0x61, low), (0x62, high),
                           (0x1c0, load), (0x1c1, 77), (0x1c2, 99)):
        m.write8(address, value)
    run(cpu, 0xa72d)
    return s.a, s.b, s.y, s.ccr, m.read8(0x1f8), m.read8(0x1c1), m.read8(0x1c2), s.x


def interpolate(machine, address, row, col):
    cpu, _ = machine
    s = cpu.s
    s.pc, s.sp, s.ccr = 0xf4de, 0x03ff, 0xd0
    s.a, s.b, s.x, s.y = row, col, address, 0x1357
    cpu._push16(0x7000)
    run(cpu, 0x7000)
    assert (s.b, s.x, s.y) == (col, address, 0x1357)
    return s.a, s.ccr


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stock', type=Path)
    parser.add_argument('repo', type=Path, help='Path to the 7427HWContract checkout')
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo.resolve() / 'hac31_romsim'))
    from romsim.hc11_core import HC11CPU, HC11Memory

    original = load_stock(args.stock.read_bytes())
    report, files = build(original, defaults() | {'spark_layout': 'swap'})
    candidate = files['bmhm-configured.bin']

    class ReplayMemory(HC11Memory):
        def _bus_log(self, addr, data, rw, note=""):
            pass

    a, b = machine(original, HC11CPU, ReplayMemory), machine(candidate, HC11CPU, ReplayMemory)
    for idle in (0, 1):
        src, dst = SPARK_TABLES[idle][2], SPARK_TABLES[1-idle][2]
        for load in (0, 1, 15, 16, 17, 63, 64, 65, 127, 128, 239, 240, 254, 255):
            for low, high in ((0, 0), (1, 240), (63, 254), (64, 255),
                              (65, 0), (65, 16), (65, 238), (255, 239), (65, 240), (255, 255)):
                left = spark_base(a, idle, load, low, high)
                right = spark_base(b, idle, load, low, high)
                assert left[:-1] == right[:-1] and (left[-1], right[-1]) == (src,dst), (idle, load, low, high, left, right)
        print(f'Base entry agrees for {idle=} across 140 cases with the real selection operands.', flush=True)
        for row in range(256):
            for col in range(256):
                assert interpolate(a, src, row, col) == interpolate(b, dst, row, col), (idle, row, col)
        print(f'All 65,536 stock lookup coordinates agree for {idle=}.', flush=True)
    print(report['image_sha256'], report['changed_bytes'], report['checksum'])


if __name__ == "__main__":
    main()
