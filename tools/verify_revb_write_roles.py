"""Verify the 92 formerly unnamed Rev B writer roles without inventing globals.

Full-image checks use exact Rev B bytes/rooting. Recorded checks use selected
excerpts and controlled CPU witnesses, not a reconstructed full ROM or hardware.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

from explain_revb_bin import ROOT, SHA, read_workbook, sweep
from factory_rom_decode import decode
from revb_read_witnesses import CPU, fresh, put
from audit_revb_rw import TransactionMemory
from trace_revb_reads import csv_text

DATA = ROOT / "maps/maintenance/revb_write_roles"
SPANS = ((0x518f,0x51b0),(0x5b00,0x5b13),(0x4e2e,0x4e32),
         (0xe132,0xe1ac),(0xdd14,0xdd40),(0xf326,0xf3e4),
         (0x7a59,0x7a79),(0xab89,0xaba2),(0xf436,0xf459),
         (0xf5e8,0xf64e),(0xea80,0xeab1))


def run(image):
    cases = []

    def execute(memory, entry, stop, sp=0x3ff, x=0, y=0, d=0):
        m = TransactionMemory(memory)
        cpu = CPU(m)
        cpu.s.pc,cpu.s.sp,cpu.s.ccr,cpu.s.x,cpu.s.y,cpu.s.d = entry,sp,0xd0,x,y,d
        cpu._push16(0x7000)
        events = []
        for _ in range(4000):
            if cpu.s.pc == stop:
                return m,cpu,events
            pc = cpu.s.pc
            i = decode(lambda a,n:m.mem[a:a+n],pc)
            m.reads.clear();m.writes.clear()
            cpu.step()
            assert [a for a,v,fetch in m.reads if fetch] == list(range(pc,i.next_pc))
            events.append((pc,[(a,v) for a,v,fetch in m.reads if not fetch],list(m.writes)))
            assert not (cpu.halted or cpu.waiting)
        raise AssertionError("Role witness exceeded instruction budget")

    for name,entry,stop in (("Candidate seed",0xe142,0xe151),
                            ("Candidate intersection",0xe160,0xe174),
                            ("Retained log union and candidate clear",0xe197,0xe1a8),
                            ("Expired retained log clear",0xdd2e,0xdd37),
                            ("Masked log/live/candidate clear",0xf333,0xf354),
                            ("Masked log/live clear",0xf380,0xf39a)):
        b = fresh(image)
        b[0xb:0x14] = bytes([0x80]*9)
        b[0x16:0x1f] = bytes([0x33]*9)
        b[0x56:0x5f] = bytes([0x0f]*9)
        b[0x5b00:0x5b09] = bytes([0xff]*9)
        m,_,events = execute(b,entry,stop,y=0x5b08)
        h,p,live = list(m.mem[0xb:0x14]),list(m.mem[0x56:0x5f]),list(m.mem[0x16:0x1f])
        if entry == 0xe142:assert h == [0x80]*9 and p == [0x33]*9
        elif entry == 0xe160:assert p == [3]*9 and h == [0x80]*9
        elif entry == 0xe197:assert h == [0x8f]*9 and p == [0]*9
        elif entry == 0xdd2e:assert h == [0]*9 and p == [0x0f]*9 and live == [0x33]*9
        else:
            masks = b[0xf377:0xf380] if entry == 0xf333 else b[0xf3db:0xf3e4]
            assert h == [0x80 & v for v in masks]
            assert live == [0x33 & v for v in masks]
            assert p == ([0x0f & v for v in masks] if entry == 0xf333 else [0x0f]*9)
        cases.append(dict(name=name,retained=h,candidate=p,live=live))

    for slot in (0,15):
        for old in (0,0x400):
            b = fresh(image)
            b[2] = slot
            put(b,0x300e,0x1000);put(b,0x301a,0x1100)
            address = 0x2d3+2*slot
            put(b,address,old)
            m,_,events = execute(b,0x7a59,0x7a79)
            expected = max(old,0x233)
            assert int.from_bytes(m.mem[address:address+2],'big') == expected
            writes = [(a,v) for pc,r,w in events if pc == 0x7a77 for a,v in w]
            assert [a for a,v in writes] == ([address,address+1] if old < 0x233 else [])
            cases.append(dict(name="Per-slot elapsed maximum",slot=slot,old=old,result=expected,address=f"{address:04X}"))

    for sp in (0x3ff,0x3df):
        b = fresh(image)
        put(b,0x3fc0,0);put(b,0x3ff6,0x1000)
        m,cpu,events = execute(b,0xab89,0xaba2,sp=sp,d=0xf100)
        writes = [(a,v) for pc,r,w in events if pc == 0xaba0 for a,v in w]
        assert writes == [(sp-3,0),(sp-2,0)] and cpu.s.x == sp-3
        cases.append(dict(name="EST candidate is frame-relative",entry_SP=f"{sp:04X}",written=[f"{a:04X}" for a,v in writes]))
        b = fresh(image)
        b[0x5000] = 0x40
        m,cpu,events = execute(b,0xf436,0x7000,sp=sp,x=0x2000,y=0x5000,d=0x4000)
        writes = [(a,v) for pc,r,w in events if pc == 0xf449 for a,v in w]
        assert [a for a,v in writes] == [sp-3,sp-2]
        assert cpu.s.x == int.from_bytes(m.mem[sp-3:sp-1],'big')
        cases.append(dict(name="Lag state is frame-relative",entry_SP=f"{sp:04X}",written=[f"{a:04X}" for a,v in writes]))

    # AND1F chooses a byte offset, not a 32-entry word-table index.
    for offset in range(32):
        b = fresh(image)
        b[2] = offset
        assert int.from_bytes(image[0x518f+offset:0x5191+offset],'big') == 0
        _,cpu,events = execute(b,0xf5e8,0xf64d)
        assert all(pc != 0xf627 for pc,r,w in events)
        assert cpu.s.x == 0
        cases.append(dict(name="Released broadcast schedule is null",byte_offset=offset,descriptor="0000"))
    b = fresh(image)
    b[0x5203] = 0
    put(b,0x5205,0x0220);put(b,0x5209,0x0100);put(b,0x520b,0x0101)
    b[0x100],b[0x101] = 0x12,0x34
    m,_,events = execute(b,0xf619,0xf632,x=0x5200,d=2)
    writes = [(a,v) for pc,r,w in events if pc == 0xf627 for a,v in w]
    assert writes == [(0x220,0x12),(0x221,0x34)]
    cases.append(dict(name="Synthetic descriptor staging template",destination="0220..0221",data=[0x12,0x34],
        scope="Controlled descriptor only; not an admitted released-schedule transaction"))
    return dict(count=len(cases),cases=cases,scope=__doc__.strip())


def verify_catalog(image=None):
    sites = json.loads((DATA/"SITE_ROLES.json").read_text())
    addresses = json.loads((DATA/"ADDRESS_ROLES.json").read_text())
    with (DATA/"SEED_SITES.csv").open(newline="") as stream:
        seed = list(csv.DictReader(stream))
    assert len(sites) == len(seed) == len({r["pc"] for r in sites}) == 92
    assert {r["pc"] for r in sites} == {r["pc"] for r in seed}
    current = json.loads((ROOT/"maps/maintenance/write_registers_evidence.json").read_text())
    owners = {(r["address"],pc) for r in current["rows"] for pc in r["current_writer_pcs"]}
    for row in sites:
        pc,data = int(row["pc"],16),bytes.fromhex(row["bytes"])
        i = decode(lambda a,n:data[a-pc:a-pc+n],pc)
        assert i.access() and "W" in i.access()["access"]
        assert row["operation"] == (i.op+" "+i.operand).strip()
        if image is not None:
            assert image[pc:pc+len(data)] == data
        if row["kind"] in ("stack_local","descriptor_selected_copy"):
            assert not row["global_owners"]
        else:
            assert row["global_owners"]
            for a in row["global_owners"]:
                assert (a,"$"+row["pc"]) in owners,(row["pc"],a)
                if i.access()["address"] is not None:
                    assert int(a[1:].split('.')[0],16) == i.access()["address"]
    for filename,tab,use in (("7427_Address_Register_0.3.12.xlsx","RAM reads","read_use"),
                              ("7427_Write_Register_0.3.12.xlsx","RAM writes","write_use")):
        rows = {a:(b,c) for a,b,c in read_workbook(ROOT/filename)[tab]}
        for r in addresses:
            assert rows[r["address"]] == (r["oem_role"],r[use])
    return sites,addresses


def main():
    p = argparse.ArgumentParser(description=__doc__)
    modes = p.add_mutually_exclusive_group(required=True)
    modes.add_argument('--rom',type=Path);modes.add_argument('--check-recorded',action='store_true')
    p.add_argument('--record',action='store_true');a=p.parse_args()
    if a.record and not a.rom:p.error('Recording requires --rom')
    if a.rom:
        image = a.rom.read_bytes()
        assert len(image) == 65536 and hashlib.sha256(image).hexdigest() == SHA
        sites,addresses = verify_catalog(image)
        instructions,_,_ = sweep(image)
        assert all(int(r['pc'],16) in instructions for r in sites)
        evidence = dict(image_sha256=SHA,spans=[dict(start=f'{lo:04X}',bytes=image[lo:hi].hex(' ')) for lo,hi in SPANS])
    else:
        sites,addresses = verify_catalog()
        evidence = json.loads((DATA/'EVIDENCE.json').read_text())
        assert evidence['image_sha256'] == SHA
        image = bytearray(65536)
        for span in evidence['spans']:
            data=bytes.fromhex(span['bytes']);lo=int(span['start'],16);image[lo:lo+len(data)]=data
    result = run(image)
    summary = dict(image_sha256=SHA,writer_sites_named=len(sites),address_roles=len(addresses),
        kinds=dict(Counter(r['kind'] for r in sites)),witness_cases=result['count'],
        remaining_global_address_qualification='Two stack-local sites and one descriptor-selected copy have no invented absolute owner. Legacy recovery slots A/B have no proved monitor number.')
    files={'EXECUTION_WITNESSES.json':json.dumps(result,indent=2)+'\n','SUMMARY.json':json.dumps(summary,indent=2)+'\n',
           'SITE_ROLES.csv':csv_text([{**r,'global_owners':';'.join(r['global_owners'])} for r in sites])}
    if a.rom:files['EVIDENCE.json']=json.dumps(evidence,indent=2)+'\n'
    for name,text in files.items():
        if a.record:(DATA/name).write_text(text)
        else:assert (DATA/name).read_text()==text,'Stale role evidence: '+name
    if a.rom:assert a.rom.read_bytes()==image
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
