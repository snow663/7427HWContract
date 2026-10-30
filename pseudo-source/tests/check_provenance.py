"""Check routine/file ownership and the ROM anchors behind the initial outline."""
import csv
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parent
sys.path.insert(0,str(ROOT/'tools'))
from build_factory_scheduler import recorded_rom
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256

rom=recorded_rom(json.loads(EVIDENCE.read_text()))
assert sha256(bytes([255])*0x4000+rom.read(0x4000,0xc000)).hexdigest()==EXPECTED_SHA256
assert rom.read(0x793d,9)==bytes.fromhex('FC 30 1A C3 03 33 FD 30 1A')
assert rom.read(0x7431,4)==bytes.fromhex('86 0E 97 02')
assert rom.word(0x495d)==10
assert rom.read(0xf3e4,9)==bytes.fromhex('B6 30 66 88 80 B7 30 66 39')
assert (BASE/'reference/factory_slots.csv').read_text()==(ROOT/'maps/structure/factory_scheduler_slots.csv').read_text()
rows=list(csv.DictReader((BASE/'routine_index.csv').open()))
files=sorted(p.relative_to(BASE).as_posix() for p in (BASE/'src').rglob('*.c'))
assert sorted(r['file'] for r in rows)==files
functions=[]
for row in rows:
    content=(BASE/row['file']).read_text()
    names=re.findall(r'^(?:PcmStatus|PcmFuelBase)\s+(pcm_\w+)\s*\(',content,re.M)
    assert names==[row['routine']],(row,names)
    functions+=names
    assert row['status'] in {'implemented_outline','dependency_boundary','implemented_algorithm'}
assert len(functions)==len(set(functions))
for p in [BASE/'README.md',*sorted((BASE/'docs').glob('*.md')),*sorted((BASE/'memory').glob('*.md'))]:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if not target.startswith(('http://','https://','#')): assert (p.parent/target.split('#')[0]).exists(),(p,target)
print(f'{len(functions)} public routines each have their own file; source anchors and links pass.')
