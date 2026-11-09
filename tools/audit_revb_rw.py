"""Audit Rev B read/write evidence and replay bounded cross-reference findings.

Full-image mode checks rooted writers and recorded readers against actual bytes.
Recorded mode replays selected code in controlled byte storage; it cannot prove
whole-image reachability, interrupt histories, electrical behavior or aliases.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path

from build_factory_state_flow import target_bytes
from explain_revb_bin import ROOT, SHA, read_workbook
from factory_rom_decode import decode
from revb_access_flow import analyze_image
from revb_read_witnesses import CPU, Memory, fresh, put
from trace_revb_reads import csv_text, span_text

DATA = ROOT / "maps/maintenance/revb_rw_audit"
WRITE_EVIDENCE = ROOT / "maps/maintenance/write_registers_evidence.json"
SPANS = ((0x746c,0x74b4),(0x8209,0x821b),(0xf245,0xf280),
         (0x9200,0x920d),(0xf40f,0xf414),(0x9880,0x989c),
         (0xeb19,0xeb81),(0x794b,0x794e),(0xfc04,0xfc2f),(0xf5cf,0xf5dc),
         (0xc5ff,0xc623))


class TransactionMemory(Memory):
    def __init__(self, contents):
        super().__init__(contents)
        self.writes = []

    def write8(self, address, value):
        self.writes.append((address & 65535, value & 255))
        super().write8(address, value)


def walk(contents, entry, stops, b=0, a=0):
    memory = TransactionMemory(contents)
    cpu = CPU(memory)
    cpu.s.pc, cpu.s.sp, cpu.s.ccr, cpu.s.x, cpu.s.b = entry, 0x3ff, 0xd0, 0x3000, b
    cpu.s.a = a
    cpu._push16(0x7000)
    events = []
    for _ in range(10000):
        if cpu.s.pc in stops:
            return memory, cpu, events
        pc = cpu.s.pc
        i = decode(lambda a,n: memory.mem[a:a+n], pc)
        memory.reads.clear()
        memory.writes.clear()
        cpu.step()
        assert [a for a, _, fetch in memory.reads if fetch] == list(range(pc,i.next_pc))
        events.append((pc, [(a,v) for a,v,fetch in memory.reads if not fetch], list(memory.writes)))
        assert not (cpu.halted or cpu.waiting)
    raise AssertionError("Audit witness instruction budget exceeded")


def witnesses(image):
    cases, refresh = [], []
    memory = fresh(image)
    for address in list(range(0x400)) + list(range(0x800,0x900)):
        memory[address] = (address*37+11) & 255
    put(memory,0x29b,0)
    memory[0x51] |= 4
    _, cpu, events = walk(memory,0x746c,{0x74b3})
    reads = (0x7484,0x7488,0x748c,0x7490,0x7494,0x7498,0x749c,0x74a0)
    covered = set()
    for offset, pc in enumerate(reads):
        observed = [r for p,r,w in events if p == pc]
        stores = [w for p,r,w in events if p == pc+2]
        assert len(observed) == 80 and observed == stores
        covered.update(a for row in observed for a,v in row)
        for first,last in ((0,0x3f0),(0x800,0x8f0)):
            expected = {a+2*offset+o for a in range(first,last+1,16) for o in range(2)}
            actual = {a for row in observed for a,v in row if first <= a <= last+15}
            assert actual == expected
            refresh.append(dict(read_pc=f"{pc:04X}",write_pc=f"{pc+2:04X}",
                first_word=f"{first+2*offset:04X}",last_word=f"{last+2*offset:04X}",
                stride=16,width_bits=16,word_transactions=len(expected)//2,
                qualification="Entry746C with0051.2 set and029B=0000; valid uninterrupted cursor walk"))
    assert covered == set(range(0x400)) | set(range(0x800,0x900))
    cases.append(dict(name="Qualified RAM refresh",read_bytes=1280,write_bytes=1280,
        word_reads=640,word_writes=640,identical_read_write_pairs=True,stop=f"{cpu.s.pc:04X}"))

    for flag in (0,8):
        for threshold in (0,127,255):
            memory = fresh(image)
            memory[0x46],memory[0x493b],memory[0x493c],memory[0x246] = flag,threshold,threshold,3
            _, cpu, events = walk(memory,0x8209,{0x821b})
            assert cpu.s.a == 3 and cpu.s.ccr == 0xd0
            cases.append(dict(name="Discarded DFCO speed loads",fuel_cut_flag=flag,
                synthetic_threshold=threshold,A=cpu.s.a,CCR=cpu.s.ccr,
                reads=[f"{a:04X}" for p,r,w in events for a,v in r],
                scope="Only8209..821A; caller and later DFCO behavior are not proved by this slice"))

    memory = fresh(image)
    memory[0x3030] = 0
    memory[0x3031:0x3034] = bytes((0x53,0x64,0x75))
    m, _, events = walk(memory,0xf245,{0xf25e})
    assert sum(p == 0xf267 for p,r,w in events) == 12
    assert m.mem[0x1a] & 2 and m.mem[0x3a] & 1
    assert [m.mem[a] for a in (0xa6,0x82e,0x1d5)] == [0x53,0x64,0x75]
    cases.append(dict(name="ADC timeout still publishes result slots",polls=12,
        fault_bits=["001A.1","003A.0"],published=["00A6","082E","01D5"],
        scope="Forced COCO-clear controlled storage; not a physical ADC timing/failure model"))

    memory = fresh(image)
    memory[0x4c] = 0xff
    m, _, _ = walk(memory,0x9202,{0x920c},b=0x0c)
    assert m.mem[0x4c] == 0xef
    m, _, _ = walk(m.mem,0xf40f,{0xf414})
    assert m.mem[0x3062] == 0xef
    cases.append(dict(name="Retained IAC shadow producer and publication",
        producer="9203..920A",shadow="004C",publication="F40F/F411",destination="3062",
        scope="Controlled phase bits; board electrical response not modeled"))

    for sample,correction,expected in ((0x60,0x10,0x70),(0xf0,0x20,0xff)):
        memory = fresh(image)
        memory[0x1c6] = sample
        m, _, _ = walk(memory,0xc5ff,{0xc609},a=correction)
        assert m.mem[0x2f3] == expected
        cases.append(dict(name="BARO candidate construction",filtered_MAP=sample,
            supplied_correction=correction,candidate=expected,
            scope="Caller-supplied lookup output; proves addition/saturation, not physical scaling or lookup interpolation"))
    memory = fresh(image)
    memory[0x4e68] = 0x52
    m, _, _ = walk(memory,0xc619,{0xc623})
    assert m.mem[0x2f3] == m.mem[0x2f4] == 0x52 and m.mem[0x2f5] == 0
    cases.append(dict(name="BARO fallback publication",synthetic_fallback=0x52,
        destinations=["02F3","02F4..02F5"],scope="Controlled fallback path, not a direct ADC sample"))

    # Check the implementation's actual boundaries, not the profile's names.
    from romsim.bus import ContractMemory
    from romsim.contracts import PCMProfile
    from romsim.devices import EngineInputs
    from romsim.trace import TraceRecorder
    profile = PCMProfile.load(ROOT / "hac31_romsim/romsim/profiles/gm_16197427_31.json")
    model = ContractMemory(profile,EngineInputs(),TraceRecorder())
    model.write8(0x103d,3)
    cases.append(dict(name="Existing simulator resource boundary observation",
        internal_ram_bytes=len(model.internal_ram),internal_register_bytes=len(model.internal_regs),
        internal_0200=model._is_internal(0x0200),internal_305c=model._is_internal(0x305c),
        default_CONFIG=f"{model.read8(0x303f):02X}",
        scope="Implementation observation, not an assertion of correct F1 or GM hardware behavior"))
    return dict(cases=cases,count=len(cases),scope=__doc__.strip()),refresh


def build(image):
    flow = analyze_image(image)
    instructions = flow["instructions"]
    evidence = json.loads(WRITE_EVIDENCE.read_text())
    assert evidence["current_sha256"] == SHA
    targets, contexts, associations = defaultdict(set),defaultdict(set),defaultdict(list)
    for summary in flow["summaries"].values():
        for effect in summary.effects.values():
            if "W" in effect.access:
                targets[effect.pc].update(target_bytes(effect))
                contexts[effect.pc].add(effect.address.text())
    results = Counter()
    for row in evidence["rows"]:
        address = int(row["address"][1:].split(".")[0],16)
        for text in row["current_writer_pcs"]:
            pc = int(text[1:],16)
            i = instructions[pc]
            a = i.access()
            assert a and "W" in a["access"],(row["address"],text)
            if a["address"] is not None:
                assert address in {(a["address"]+o)&65535 for o in range(a["width_bits"]//8)}
                results["fixed_operand_matches"] += 1
            elif address in targets[pc]:
                results["finite_indexed_matches"] += 1
            else:
                results["inherited_indexed_qualification_not_resolved"] += 1
            associations[pc].append(row["address"])
    rows = []
    role_file = ROOT / "maps/maintenance/revb_write_roles/SITE_ROLES.json"
    site_roles = {int(r["pc"],16):r for r in json.loads(role_file.read_text())} if role_file.exists() else {}
    for pc,i in sorted(instructions.items()):
        a = i.access()
        if a and "W" in a["access"]:
            rows.append(dict(pc=f"{pc:04X}",bytes=i.data.hex(" "),operation=(i.op+" "+i.operand).strip(),
                access=a["access"],width_bits=a["width_bits"],
                fixed_address=f"{a['address']:04X}" if a["address"] is not None else "",
                finite_byte_ranges=span_text(targets[pc]),abstract_contexts=" | ".join(sorted(contexts[pc])),
                named_evidence_rows=";".join(sorted(associations[pc])),
                traced_site_role=site_roles.get(pc,{}).get("role",""),
                role_kind=site_roles.get(pc,{}).get("kind","named address reference" if associations[pc] else "unassigned")))
    with (ROOT / "maps/maintenance/revb_reads/READ_SITES.csv").open(newline="") as stream:
        readers = list(csv.DictReader(stream))
    for row in readers:
        i = instructions[int(row["pc"],16)]
        assert i.data == bytes.fromhex(row["bytes"])
        assert i.access() and "R" in i.access()["access"]
    for workbook in ("7427_Address_Register_0.3.12.xlsx","7427_Write_Register_0.3.12.xlsx"):
        if workbook.startswith("7427_Write"):
            actual = {(sheet,a):(b,c) for sheet,rs in read_workbook(ROOT/workbook).items() for a,b,c in rs}
            assert actual == {(r["sheet"],r["address"]):(r["oem_role"],r["current_use"]) for r in evidence["rows"]}
    witness, refresh = witnesses(image)
    meta = dict(image_sha256=SHA,rooted_instructions=len(instructions),explicit_read_sites=len(readers),
        explicit_write_sites=len(rows),fixed_write_sites=sum(bool(r["fixed_address"]) for r in rows),
        named_write_rows=len(evidence["rows"]),named_writer_associations=sum(results.values()),
        association_results=dict(results),write_sites_without_named_evidence=sum(not r["named_evidence_rows"] for r in rows),
        additional_site_roles=len(site_roles),
        write_sites_without_role=sum(not r["named_evidence_rows"] and not r["traced_site_role"] for r in rows),
        witness_cases=witness["count"],scope=__doc__.strip())
    selected = dict(image_sha256=SHA,spans=[dict(start=f"{a:04X}",bytes=image[a:z].hex(" ")) for a,z in SPANS])
    return {"WRITE_SITES.csv":csv_text(rows),"QUALIFIED_REFRESH.csv":csv_text(refresh),
        "WRITERS_WITHOUT_NAMED_ROWS.csv":csv_text([r for r in rows if not r["named_evidence_rows"]]),
        "SUMMARY.json":json.dumps(meta,indent=2)+"\n", "EVIDENCE.json":json.dumps(selected,indent=2)+"\n",
        "EXECUTION_WITNESSES.json":json.dumps(witness,indent=2)+"\n"}


def check_recorded():
    evidence = json.loads((DATA / "EVIDENCE.json").read_text())
    assert evidence["image_sha256"] == SHA
    image = bytearray(65536)
    for span in evidence["spans"]:
        data = bytes.fromhex(span["bytes"])
        a = int(span["start"],16)
        image[a:a+len(data)] = data
    expected = json.loads((DATA / "EXECUTION_WITNESSES.json").read_text())
    witness, refresh = witnesses(image)
    assert witness == expected
    assert csv_text(refresh) == (DATA / "QUALIFIED_REFRESH.csv").read_text()
    with (DATA / "WRITE_SITES.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    by_pc = {}
    for row in rows:
        pc,data = int(row["pc"],16),bytes.fromhex(row["bytes"])
        i = decode(lambda a,n:data[a-pc:a-pc+n],pc)
        a = i.access()
        assert a and "W" in a["access"] and a["access"] == row["access"]
        assert a["width_bits"] == int(row["width_bits"])
        assert (i.op+" "+i.operand).strip() == row["operation"]
        assert (f"{a['address']:04X}" if a["address"] is not None else "") == row["fixed_address"]
        assert pc not in by_pc
        by_pc[pc] = i
    current = json.loads(WRITE_EVIDENCE.read_text())
    for row in current["rows"]:
        address = int(row["address"][1:].split(".")[0],16)
        for text in row["current_writer_pcs"]:
            a = by_pc[int(text[1:],16)].access()
            if a["address"] is not None:
                assert address in {(a["address"]+o)&65535 for o in range(a["width_bits"]//8)}
    meta = json.loads((DATA / "SUMMARY.json").read_text())
    assert len(rows) == meta["explicit_write_sites"]
    assert len(current["rows"]) == meta["named_write_rows"]
    assert witness["count"] == meta["witness_cases"]
    journal = json.loads((DATA / "REGISTER_UPDATES.json").read_text())
    successor = ROOT / "maps/maintenance/revb_write_roles/REGISTER_UPDATES.json"
    if successor.exists():
        later = json.loads(successor.read_text())
        assert later["previous_update"] == "maps/maintenance/revb_rw_audit/REGISTER_UPDATES.json"
        assert later["write_evidence_before_sha256"] == journal["write_evidence_after_sha256"]
        prior_books = {r["workbook"]:r["after_sha256"] for r in journal["workbooks"]}
        assert all(r["before_sha256"] == prior_books[r["workbook"]] for r in later["workbooks"])
        journal = later
    assert hashlib.sha256(WRITE_EVIDENCE.read_bytes()).hexdigest() == journal["write_evidence_after_sha256"]
    for record in journal["workbooks"]:
        assert hashlib.sha256((ROOT/record["workbook"]).read_bytes()).hexdigest() == record["after_sha256"]
    actual = {(sheet,a):(b,c) for sheet,rs in read_workbook(ROOT/"7427_Write_Register_0.3.12.xlsx").items() for a,b,c in rs}
    assert actual == {(r["sheet"],r["address"]):(r["oem_role"],r["current_use"]) for r in current["rows"]}
    assert csv_text([r for r in rows if not r["named_evidence_rows"]]) == (DATA / "WRITERS_WITHOUT_NAMED_ROWS.csv").read_text()
    role_file = ROOT / "maps/maintenance/revb_write_roles/SITE_ROLES.json"
    site_roles = {r["pc"]:r for r in json.loads(role_file.read_text())} if role_file.exists() else {}
    for row in rows:
        assert row["traced_site_role"] == site_roles.get(row["pc"],{}).get("role","")
    assert sum(not r["named_evidence_rows"] and not r["traced_site_role"] for r in rows) == meta["write_sites_without_role"]
    return meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--rom",type=Path)
    modes.add_argument("--check-recorded",action="store_true")
    parser.add_argument("--record",action="store_true")
    args = parser.parse_args()
    if args.check_recorded:
        if args.record:
            parser.error("Recording requires --rom")
        meta = check_recorded()
    else:
        image = args.rom.read_bytes()
        assert hashlib.sha256(image).hexdigest() == SHA and len(image) == 65536
        files = build(image)
        for name,text in files.items():
            if args.record:
                DATA.mkdir(parents=True,exist_ok=True)
                (DATA/name).write_text(text)
            else:
                assert (DATA/name).read_text() == text,"Stale audit: "+name
        assert args.rom.read_bytes() == image
        meta = json.loads(files["SUMMARY.json"])
    print(json.dumps(meta,indent=2))


if __name__ == "__main__":
    main()
