#!/usr/bin/env python3
"""Inventory static ROM opcode exposure and replay dependencies, not reachability proof."""
import ast
from collections import Counter
import csv
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"docs/audit/hc11_rom_exposure.json"


def family(row):
    op,mode=row["mnemonic"],row["mode"]
    found=[]
    if op in {"INX","DEX","INY","DEY"}:found.append("CPU-01-index-N")
    if op in {"TSX","TSY"}:found.append("CPU-02-stack-transfer-CCR")
    if op in {"BSET","BCLR"} and mode.startswith("indexed"):found.append("CPU-03-indexed-bit-CCR")
    if op in {"TST","TSTA","TSTB","CLR","CLRA","CLRB"}:found.append("CPU-04-test-clear-C")
    if op in {"TAP","RTI"}:found.append("CPU-05-software-X")
    if op in {"CLI","TAP"}:found.append("CPU-11-IRQ-enable-delay")
    return found


def imported_paths(path):
    modules=[]
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node,ast.Import):modules.extend(x.name for x in node.names)
        if isinstance(node,ast.ImportFrom) and node.module:modules.append(node.module)
        # Some suites exec a literal prefix of another suite instead of import.
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=="with_name" and node.args and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str):
            candidate=path.with_name(node.args[0].value)
            if candidate.suffix==".py" and candidate.exists():yield candidate
    for module in modules:
        for base in (ROOT/"tools",ROOT/"pseudo-source/tests",ROOT/"hac31_romsim"):
            candidate=base/Path(*module.split(".")).with_suffix(".py")
            if candidate.exists():yield candidate


def core_chain(path):
    pending=[(path,[path])];seen=set()
    while pending:
        path,chain=pending.pop(0)
        if path in seen:continue
        seen.add(path)
        if path==ROOT/"hac31_romsim/romsim/hc11_core.py":
            return [str(p.relative_to(ROOT)) for p in chain]
        pending.extend((p,chain+[p]) for p in imported_paths(path))
    return None


def main():
    catalogue=json.loads((ROOT/"docs/audit/hc11_opcode_matrix.json").read_text())
    baseline=json.loads((ROOT/"docs/audit/hc11_opcode_matrix_baseline.json").read_text())
    by={r["encoding"]:r for r in catalogue["rows"]}
    bybase={r["encoding"]:r for r in baseline["rows"]}
    rows=list(csv.DictReader((ROOT/"maps/structure/factory_global_instructions.csv").open()))
    exposure=[];unsupported=[];illegal=[];cycle_sites=[]
    for row in rows:
        code=bytes.fromhex(row["bytes_hex"])
        encoding=code[:2 if code[0] in (0x18,0x1A,0xCD) else 1].hex(" ").upper()
        spec=by[encoding];old=bybase[encoding]
        record={"pc":row["pc"],"encoding":encoding,"mnemonic":row["mnemonic"],
                "mode":row["mode"],"reviewed_span_names":row["reviewed_span_names"]}
        for item in family(row):exposure.append(dict(record,defect=item))
        if not spec["normal_mode_legal"]:illegal.append(record)
        elif not spec["legacy_implemented"]:unsupported.append(record)
        if spec.get("legacy_implemented") and (
                spec["documented_cycles"]!=old.get("legacy_probe_elapsed_cycles") or
                spec["documented_cycles"]!=old.get("legacy_probe_returned_cycles")):
            cycle_sites.append(dict(record,expected=spec["documented_cycles"],
                                    before_returned=old["legacy_probe_returned_cycles"],
                                    before_elapsed=old["legacy_probe_elapsed_cycles"]))
    cmake=(ROOT/"pseudo-source/CMakeLists.txt").read_text()
    names={filename:name for name,filename in re.findall(r'add_test\(NAME\s+(\w+)\s+COMMAND[^\n]*?/tests/(compare[^\s)]+\.py)',cmake)}
    suites=[]
    for path in sorted((ROOT/"pseudo-source/tests").glob("compare*.py")):
        chain=core_chain(path)
        suites.append({"suite":str(path.relative_to(ROOT)),"ctest_name":names.get(path.name),
                       "legacy_cpu_dependency_chain":chain,
                       "scope":"Static import/literal exec-include dependency, not proof that every corrected opcode executes"})
    data={"scope":"Committed rooted structural may-reach instruction map plus static Python imports/literal exec-includes; not actual dynamic path or functional equivalence proof",
          "instruction_map":"maps/structure/factory_global_instructions.csv",
          "instruction_rows":len(rows),"flag_exposure_counts":dict(Counter(r["defect"] for r in exposure)),
          "flag_exposure_sites":exposure,"cycle_exposure_site_count":len(cycle_sites),
          "cycle_exposure_sites":cycle_sites,"unsupported_legal_sites":unsupported,
          "illegal_sites":illegal,"suite_dependency_count":sum(bool(r["legacy_cpu_dependency_chain"]) for r in suites),
          "suites":suites}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({k:data[k] for k in ("instruction_rows","flag_exposure_counts","cycle_exposure_site_count","unsupported_legal_sites","suite_dependency_count")},indent=2))


if __name__=="__main__":main()
