"""Apply reviewed ROM decoding to indexes while retaining the raw HAC source.

The 32 reviewed discrepancy rows, A40B, and the F3DB mask table supersede
their source decodings. Overlapping source candidates stay in an audit trail;
their exclusion here is not a global proof against alternative entry points.
"""
from __future__ import annotations

import csv
import io
import json

from factory_structure import ROOT, SOURCE, Statement, parse_listing, text_sha256
from factory_rom_decode import decode

EXPECTED_ROM = "6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004"
DISCREPANCIES = ROOT / "maps/structure/factory_scheduler_listing_discrepancies.csv"
EVIDENCE_FILES = [ROOT / "maps/structure/bmhm_scheduler_rom_evidence.json",
                  ROOT / "maps/structure/bmhm_nested_state_rom_evidence.json"]
SUPPRESSED = {0xB32B:"HAC row crosses the verified B32D entry",
              0xB99E:"HAC row crosses the verified B99F entry"}


def recorded_bytes(source):
    memory={}
    for path in EVIDENCE_FILES:
        evidence=json.loads(path.read_text())
        if evidence["rom_sha256"]!=EXPECTED_ROM or evidence["rom_size_bytes"]!=65536:
            raise ValueError("ROM overlay evidence has the wrong image identity")
        if evidence["listing_sha256_lf"]!=text_sha256(source):
            raise ValueError("ROM overlay source SHA-256 changed; review before reuse")
        for block in evidence["byte_ranges"]:
            start=int(block["start"],16);data=bytes.fromhex(block["bytes_hex"])
            if start+len(data)!=int(block["end_exclusive"],16):raise ValueError("Bad overlay byte range")
            for address,byte in enumerate(data,start):
                if address in memory and memory[address]!=byte:raise ValueError("Conflicting overlay evidence")
                memory[address]=byte
    return memory


def effective_listing(source=SOURCE):
    raw=parse_listing(source); by_pc={row.pc:row for row in raw}
    memory=recorded_bytes(source)
    read=lambda a,n:bytes(memory[p] for p in range(a,a+n))
    patches={}; covered=set(); audit=[]
    expected={int(row["pc"],16):row for row in csv.DictReader(io.StringIO(DISCREPANCIES.read_text()))}
    expected[0xA40B]={"bytes_hex":"12 09 01 56","rom_instruction":"BRSET $09,#$01,$A465"}
    for pc,evidence in sorted(expected.items()):
        ins=decode(read,pc)
        if ins.data!=bytes.fromhex(evidence["bytes_hex"]):raise ValueError(f"Overlay bytes differ at {pc:04X}")
        if (ins.op+" "+ins.operand).strip()!=evidence["rom_instruction"]:
            raise ValueError(f"Overlay decode differs at {pc:04X}")
        original=by_pc.get(pc)
        patches[pc]=Statement(original.line if original else 0,pc,original.label if original else f"L{pc:04X}",
                              ins.op,ins.operand,"ROM-verified overlay; source comments retained in raw listing",
                              "rom_verified_instruction",ins.data.hex(" ").upper())
        covered.update(range(pc,pc+len(ins.data)))
    mask_range=set(range(0xF3DB,0xF3E4))
    for pc in sorted(mask_range):
        patches[pc]=Statement(by_pc[pc].line if pc in by_pc else 0,pc,"","FCB",f"${memory[pc]:02X}",
                              "F380 nine-byte AND mask table", "rom_verified_data",f"{memory[pc]:02X}")
    result=[]
    for row in raw:
        replacement=patches.get(row.pc)
        if replacement:
            reason="verified_ROM_data" if replacement.origin=="rom_verified_data" else "verified_ROM_instruction"
        elif row.pc in covered or row.pc in mask_range or row.pc in SUPPRESSED:
            reason=SUPPRESSED.get(row.pc,"source row starts inside verified ROM instruction/data bytes")
        else:
            result.append(row);continue
        audit.append({"pc":f"{row.pc:04X}","action":"replace" if replacement else "suppress_overlapping_source_row",
                      "source_line":row.line,"source_instruction":(row.op+" "+row.operand).strip(),
                      "effective_instruction":(replacement.op+" "+replacement.operand).strip() if replacement else "",
                      "bytes_hex":replacement.rom_bytes if replacement else "","reason":reason})
    raw_pcs={r.pc for r in raw}
    for pc,row in sorted(patches.items()):
        result.append(row)
        if pc not in raw_pcs:
            audit.append({"pc":f"{pc:04X}","action":"add_ROM_row","source_line":0,"source_instruction":"",
                          "effective_instruction":(row.op+" "+row.operand).strip(),"bytes_hex":row.rom_bytes,
                          "reason":"ROM entry or mask byte absent from addressed HAC rows"})
    return sorted(result,key=lambda r:r.pc),sorted(audit,key=lambda r:(r["pc"],r["action"]))


def render_statement(row):
    return f"{row.pc:04X}: {(row.label+' ') if row.label else ''}{row.op} {row.operand} ; {row.comment}"


def instruction_rows(source=SOURCE):
    from factory_structure import classification,load_regions
    regions=load_regions(source)
    return [r for r in effective_listing(source)[0] if classification(r,regions)=="instruction_candidate"]
