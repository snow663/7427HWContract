"""Conservative adapter from ROM state-flow proofs to legacy write indexes.

Only a single address shared by all captured procedure contexts is emitted as
an absolute target. Other cases retain their set/frame/unknown status. No
linear 'last LDX' estimate is used as a substitute for a control-flow proof.
"""
from __future__ import annotations

import csv
from functools import lru_cache
import json

from factory_structure import ROOT,SOURCE,text_sha256
from verify_factory_rom_structure import EXPECTED_SHA256


@lru_cache(maxsize=1)
def proofs():
    directory=ROOT/"maps/structure"
    evidence=json.loads((directory/"bmhm_nested_state_rom_evidence.json").read_text())
    if evidence["rom_sha256"]!=EXPECTED_SHA256 or evidence["listing_sha256_lf"]!=text_sha256(SOURCE):
        raise ValueError("Indexed-target evidence identity changed")
    result={}
    with (directory/"factory_indexed_flow.csv").open(newline="") as source:
        for row in csv.DictReader(source):
            if "W" in row["access"]:result.setdefault(int(row["pc"],16),[]).append(row)
    return result


def indexed_target(pc,operand):
    rows=proofs().get(pc,[])
    note="ROM state-flow contexts only; see factory_indexed_flow.csv"
    if rows and all(r["classification"] in {"exact_address","bounded_address_set"} for r in rows):
        addresses={int(a.removeprefix("$"),16) for r in rows for a in r["effective_addresses"].split(";")}
        if len(addresses)==1:
            address=addresses.pop()
            return address,f"L{address:04X}","resolved_indexed",note
        return None,f"INDEXED_{pc:04X}","bounded_indexed",note+"; addresses="+";".join(f"${a:04X}" for a in sorted(addresses))
    if rows and all(r["classification"]=="stack_relative" for r in rows):
        expressions={r["effective_addresses"] for r in rows}
        if len(expressions)==1:return None,"STACK:"+expressions.pop(),"stack_relative",note
    return None,operand.upper(),"unresolved_indexed",note if rows else "No reviewed indexed-address proof; retained unresolved"
