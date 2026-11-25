#!/usr/bin/env python3
"""Run one existing ROM suite and record the actual HC11 instruction exposure.

Usage: python tools/audit/trace_hc11_suite.py --out trace.json SUITE.py ARGS...
This instruments the CPU step boundary only. It does not add bus reads, alter
registers, or hide suite failures. Run against the corrected checkout. The
prior-model CCR calculation identifies exposure, not proof of an output error.
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import runpy
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("suite",type=Path)
    parser.add_argument("args",nargs=argparse.REMAINDER)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(root/"hac31_romsim"))
    sys.path.insert(0,str(args.suite.resolve().parent))
    from romsim.hc11_core import HC11CPU
    original=HC11CPU.step
    counts=Counter();sensitized=Counter();all_sites=Counter()

    def wrapped(cpu):
        if cpu.halted or cpu.waiting: return original(cpu)
        pc=cpu.s.pc
        # Fixture instruction memory is a flat captured image. Do not call
        # read8 here: peripheral fixture reads can have side effects.
        op=cpu.mem.mem[pc];prefix=None
        if op in (0x18,0x1A,0xCD):
            prefix,op=op,cpu.mem.mem[(pc+1)&65535]
        key=f"{prefix:02X} {op:02X}" if prefix is not None else f"{op:02X}"
        oldccr=cpu.s.ccr;olda=cpu.s.a
        stacked=cpu.mem.mem[(cpu.s.sp+1)&65535] if prefix is None and op==0x3B else 0
        result=original(cpu)
        all_sites[(pc,key)]+=1
        family=None;old_model=cpu.s.ccr
        if prefix in (None,0x18) and op in (8,9):
            family="index_n_preservation"
            value=cpu.s.x if prefix is None else cpu.s.y
            old_model=(cpu.s.ccr&~8)|(8 if value&0x8000 else 0)
        elif prefix in (None,0x18) and op==0x30:
            family="stack_transfer_ccr"
            value=cpu.s.x if prefix is None else cpu.s.y
            old_model=(oldccr&~12)|(8 if value&0x8000 else 0)|(4 if value==0 else 0)
        elif prefix in (None,0x18) and op in (0x1C,0x1D):
            family="indexed_bit_ccr";old_model=oldccr
        elif (prefix is None and op in (0x4D,0x5D,0x4F,0x5F,0x6D,0x7D,0x6F,0x7F)) or (prefix==0x18 and op in (0x6D,0x6F)):
            family="test_clear_carry";old_model=(cpu.s.ccr&~1)|(oldccr&1)
        elif prefix is None and op==6:
            family="tap_x_clear_only";old_model=olda
        elif prefix is None and op==0x3B:
            family="rti_x_clear_only";old_model=stacked
        if family:
            counts[(family,pc,key)]+=1
            if old_model!=cpu.s.ccr: sensitized[(family,pc,key)]+=1
        return result

    HC11CPU.step=wrapped
    sys.argv=[str(args.suite),*args.args]
    outcome="passed"
    try:
        runpy.run_path(str(args.suite),run_name="__main__")
    except BaseException as exc:
        outcome=f"{type(exc).__name__}: {exc}"
        raise
    finally:
        HC11CPU.step=original
        rows=[{"family":family,"pc":f"{pc:04X}","encoding":encoding,
               "executions":count,"prior_model_ccr_different":sensitized[family,pc,encoding]}
              for (family,pc,encoding),count in sorted(counts.items())]
        data={"suite":args.suite.name,"args":args.args,"outcome":outcome,
              "suite_sha256":sha256(args.suite.read_bytes()).hexdigest(),
              "cpu_sha256":sha256((root/"hac31_romsim/romsim/hc11_core.py").read_bytes()).hexdigest(),
              "argument_files_sha256":{str(p):sha256(p.read_bytes()).hexdigest() for p in map(Path,args.args) if p.is_file()},
              "executed_instructions":sum(all_sites.values()),"executed_unique_sites":len(all_sites),
              "scope":"Actual execution in this fixture suite; CCR sensitivity is not proof of output divergence or hardware equivalence",
              "corrected_flag_sites":rows,
              "all_sites":[{"pc":f"{pc:04X}","encoding":encoding,"count":count}
                           for (pc,encoding),count in sorted(all_sites.items())]}
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(data,indent=2)+"\n")


if __name__=="__main__": main()
