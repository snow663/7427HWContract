"""Stock BMHM image and instruction replay utilities for complete scheduler slots."""
from hashlib import sha256
from itertools import islice
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from build_factory_scheduler import recorded_rom
from factory_rom_decode import decode, successors
from factory_scheduler_replay import FixtureMemory, HC11CPU
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256

ROM = recorded_rom(json.loads(EVIDENCE.read_text()))
MAPPED = ROM.read(0x4000, 0xc000)
assert sha256(bytes([0xff]) * 0x4000 + MAPPED).hexdigest() == EXPECTED_SHA256
IMAGE = bytes(0x4000) + MAPPED  # fixture RAM below the mapped ROM


def word(address, value):
    return {address: value >> 8, (address + 1) & 65535: value & 255}


class CPU(HC11CPU):
    # A table operand may address ROM. Distinguish instruction fetch from data.
    def _fetch8(self):
        value = self.mem.mem[self.s.pc]
        self.s.pc = (self.s.pc + 1) & 65535
        return value


def compare(executable, romfile, stock, cases, label):
    cases = iter(cases)
    count = 0
    while block := list(islice(cases, 48)):
        run = subprocess.run([executable, romfile], input='\n'.join(c.row() for c in block) + '\n',
                             text=True, capture_output=True, check=True)
        actual = run.stdout.splitlines()
        assert len(actual) == len(block), (label, len(actual), len(block), run.stderr)
        for case, line in zip(block, actual):
            expected, observed = stock(case), line.split()
            if expected != observed:
                for want, got in zip(expected, observed):
                    if len(want) == len(got) and len(want) >= 100:
                        mismatch = next((n for n, pair in enumerate(zip(want, got)) if pair[0] != pair[1]), None)
                        if mismatch is not None:
                            byte = mismatch // 2
                            raise AssertionError((label, case, 'RAM snapshot byte', hex(byte),
                                                  want[2*byte:2*byte+2], got[2*byte:2*byte+2]))
                first = next((i for i, pair in enumerate(zip(expected, observed)) if pair[0] != pair[1]),
                             min(len(expected), len(observed)))
                raise AssertionError((label, case, first, 'stock', expected[max(0, first-3):first+4],
                                      'C', observed[max(0, first-3):first+4]))
            count += 1
    print(f'{label}: {count:,} comparisons passed', flush=True)
    return count


def resident_instructions(entries, external=()):
    pending = list(entries)
    reached = set()
    while pending:
        pc = pending.pop()
        if pc in reached:
            continue
        reached.add(pc)
        ins = decode(ROM.read, pc)
        pending.extend(target for target, _ in successors(ins))
        if ins.op in ('JSR', 'BSR'):
            if ins.target in external:
                continue
            assert ins.target is not None and ins.target >= 0x4000, f'Unresolved call at ${pc:04X}'
            pending.append(ins.target)
    return reached
