"""Build the Rev B candidate from the exact user-supplied Rev A image.

Source, checksum and all changes are deterministic. No upload or flashing.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from factory_rom_decode import decode
from manual_idle_asm import assemble
from manual_idle_overlay import ROOT, EXPECTED_SHA, SOURCE, overlay
from trace_manual_idle import sweep

GATE_SOURCE = ROOT / 'source/manual_idle/decel_spark_gate.asm'
NAME = '0.3.12_engine_only_manual_idle_revB.bin'
RPM = [400, 600, 800, 1000, 1200] + list(range(1600, 6001, 400))
LOAD = list(range(20, 101, 5))


def build(original):
    candidate, idle, retired = overlay(original)  # exact hash/size guard
    image = bytearray(candidate)
    gate = assemble(GATE_SOURCE)
    assert not set(gate.memory) & set(idle.memory)
    assert all(0x9f40 <= a < 0x9fc0 for a in gate.memory)
    for a, v in gate.memory.items(): image[a] = v
    retired -= set(gate.memory)
    # The only incoming entry to the complete old decel/recovery body is A97A.
    image[0xa97a:0xa9e0] = b'\x7e\x9f\x40' + b'\xff' * (0xa9e0 - 0xa97d)
    retired |= set(range(0xa97d, 0xa9e0))
    cells = []
    # Extend the observed hot-idle shelf through the cold-idle operating range.
    # 55/60-kPa shoulders blend into each unchanged 65-kPa cell. Loaded Rev A
    # timing edits at 70..80 kPa and all other table cells remain unchanged.
    for r, wanted in ((4, 78), (5, 78), (6, 96)):
        endpoint = original[0x4169 + r * 17 + 9]
        for c in range(9):
            raw = wanted if c <= 6 else (wanted * (9-c) + endpoint * (c-6) + 1) // 3
            a = 0x4169 + r * 17 + c
            before = original[a]
            image[a] = raw
            if before != raw:
                cells.append(dict(address=f'{a:04X}', rpm=RPM[r], nominal_map_kpa=LOAD[c],
                    before_raw=before, after_raw=raw,
                    before_deg=before * 90/256, after_deg=raw * 90/256))
    image[0x4006:0x4008] = (sum(image[0x4008:]) & 65535).to_bytes(2, 'big')
    # Every byte outside this explicit union must match the user's running BIN.
    allowed = set(range(0x4006,0x4008)) | set(range(0x4169,0x428a)) | set(range(0xa97a,0xa9e0))
    from manual_idle_overlay import RETIRED
    allowed |= {a for lo,hi in RETIRED for a in range(lo,hi)}
    changed = {a for a in range(65536) if image[a] != original[a]}
    assert changed <= allowed
    assert {a for a in changed if 0x4169 <= a < 0x428a} == {int(c['address'],16) for c in cells}
    assert all(image[0x4169+r*17+c] == original[0x4169+r*17+c]
               for r in range(17) for c in range(9,17))
    # Sweep from all vectors and scheduler entries; erased code/data forbidden.
    decoded, frontiers, roots = sweep(image, retired)
    assert not [p for p,i in decoded.items() if i.op in ('BRSET','BRCLR') and i.value==0x36 and i.mask&2]
    assert not [p for p,i in decoded.items() if i.access() and i.access()['address'] is not None
                and 0x2a7 <= i.access()['address'] <= 0x2b0]
    assert not [p for p,i in decoded.items() if i.access() and i.access()['address'] in (0x414f,0x4150,0x4151)]
    # Store byte-exact reversible spans, including unchanged bytes only when
    # adjacent changes belong to one continuous span.
    patches=[]
    for a in sorted(changed):
        if patches and a==patches[-1][1]: patches[-1][1]+=1
        else: patches.append([a,a+1])
    patches=[dict(start=f'{lo:04X}',end_exclusive=f'{hi:04X}',before=original[lo:hi].hex(),after=image[lo:hi].hex()) for lo,hi in patches]
    restored=bytearray(image)
    for row in patches:
        lo,hi=int(row['start'],16),int(row['end_exclusive'],16)
        restored[lo:hi]=bytes.fromhex(row['before'])
    assert restored==original
    report=dict(baseline_sha256=EXPECTED_SHA,candidate_sha256=hashlib.sha256(image).hexdigest(),
        image_name=NAME,image_size=len(image),checksum=f'{sum(image[0x4008:])&65535:04X}',
        idle_source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        gate_source_sha256=hashlib.sha256(GATE_SOURCE.read_bytes()).hexdigest(),
        changed_bytes=len(changed),reversible_spans=patches,spark_cells=cells,
        static_instruction_starts=len(decoded),roots=[f'{a:04X}' for a in roots],
        execution_frontiers=frontiers,indexed_data_operations=sum(bool(i.access() and i.access()['address'] is None) for i in decoded.values()),
        checks=['Exact baseline SHA and 64 KiB size','Additive checksum repaired',
                'Changes bounded to reviewed strategy/spark/checksum allocations',
                'All 65..100 nominal kPa spark cells preserved',
                'Every change reverses to the exact baseline',
                'No direct gear selector or old Drive-bank readers',
                'No direct execution into retired code/calibration',
                'No remaining direct decel recovery-calibration readers'],
        limits='Development candidate. Static direct CFG has indexed/external frontiers. Software fixtures do not establish physical engine stability, airflow calibration or PCM timing deadlines.')
    return bytes(image), report, retired


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('baseline',type=Path)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    original=args.baseline.read_bytes(); image,report,_=build(original)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/NAME).write_bytes(image)
    (args.output/'patch_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    assert args.baseline.read_bytes()==original
    print(json.dumps({k:report[k] for k in ('image_name','candidate_sha256','checksum','changed_bytes','static_instruction_starts')},indent=2))
