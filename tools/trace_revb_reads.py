"""Inventory explicit Rev B reads without turning runtime pointers into aliases.

Full-image mode runs normal-return abstract flow. Recorded mode checks the
committed read inventory and local execution witnesses, not the absent full BIN.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

from build_factory_state_flow import classification, target_bytes
from explain_revb_bin import ROOT, SHA, role_maps
from explain_revb_functions import make_groups
from factory_rom_decode import decode
from revb_access_flow import analyze_image
from revb_read_witnesses import run as run_witnesses

DATA = ROOT / "maps/maintenance/revb_reads"
WINDOWS = ROOT / "maps/maintenance/revb_cs_decode/EFFECTIVE_EXPECTED_MAP.csv"
SCOPE = "Explicit operand reads including RMW; static normal-return may-effects. Unknown/formal contexts remain separate. Instruction fetch, vector fetch and implicit stack reads have separate inventories. No physical aliases or dummy bus cycles inferred."


def ranges(addresses):
    result = []
    for address in sorted(set(addresses)):
        if result and result[-1][1] + 1 == address:
            result[-1][1] = address
        else:
            result.append([address, address])
    return result


def span_text(addresses):
    return ";".join(f"{a:04X}" if a == z else f"{a:04X}..{z:04X}"
                    for a, z in ranges(addresses))


def expected_windows():
    with WINDOWS.open(newline="") as stream:
        return list(csv.DictReader(stream))


def resource(address, windows):
    return next(row for row in windows
                if int(row["start"], 16) <= address <= int(row["end"], 16))


def build(image):
    flow = analyze_image(image)
    ins = flow["instructions"]
    names, _, refs = role_maps()
    groups, _ = make_groups(image)
    owners = {i.pc: (g["address"], g["title"]) for g in groups for i in g["instructions"]}
    contexts = defaultdict(list)
    writes = defaultdict(set)
    for entry, summary in sorted(flow["summaries"].items()):
        for effect in sorted(summary.effects.values(), key=lambda e: (e.pc, e.via, e.address.text())):
            if effect.pc not in ins:
                continue
            access = ins[effect.pc].access()
            if access is None:
                continue
            if "W" in effect.access:
                for address in target_bytes(effect):
                    writes[address].add(effect.pc)
            if "R" not in effect.access or access["address"] is not None:
                continue
            contexts[effect.pc].append(dict(entry=f"{entry:04X}",
                classification=classification(effect.address),
                expression=effect.address.text(),
                starts=[f"{a:04X}" for a in sorted(effect.address.ints() or [])],
                call_path=[f"{pc:04X}" for pc in effect.via],
                qualification="Normal-return abstract context; generic entry parameters, branch feasibility and widening retained"))
    windows = expected_windows()
    rows, details = [], {}
    for pc, i in sorted(ins.items()):
        access = i.access()
        if access is None or "R" not in access["access"]:
            continue
        fixed = access["address"]
        local = contexts[pc] if fixed is None else []
        starts = {fixed} if fixed is not None else {int(a, 16) for c in local for a in c["starts"]}
        nonfinite = [c for c in local if c["classification"] not in ("exact_address", "bounded_address_set")]
        byte_addresses = {(a + offset) & 65535 for a in starts for offset in range(access["width_bits"] // 8)}
        group, title = owners[pc]
        resolution = "fixed operand" if fixed is not None else "finite contexts plus nonfinite contexts" if starts and nonfinite else "finite abstract contexts" if starts else "nonfinite contexts only"
        row = dict(pc=f"{pc:04X}", bytes=i.data.hex(" "), operation=(i.op+" "+i.operand).strip(),
                   access=access["access"], width_bits=access["width_bits"],
                   fixed_address=f"{fixed:04X}" if fixed is not None else "",
                   finite_starts=span_text(starts), finite_byte_ranges=span_text(byte_addresses),
                   resolution=resolution, context_rows=len(local), nonfinite_context_rows=len(nonfinite),
                   expected_resources=";".join(sorted({resource(a, windows)["resource"] for a in byte_addresses})),
                   operand_role=names.get(fixed, "") if fixed is not None else "caller/local pointer context required",
                   group=group, group_function=title)
        rows.append(row)
        details[row["pc"]] = dict(starts=sorted(starts), bytes=sorted(byte_addresses), contexts=local)
    hardware = []
    for row in rows:
        pc = row["pc"]
        for start in details[pc]["starts"]:
            footprint = {(start + offset) & 65535 for offset in range(row["width_bits"] // 8)}
            if not any(0x3000 <= a <= 0x3fff for a in footprint):
                continue
            hardware.append(dict(address=f"{start:04X}", width_bits=row["width_bits"],
                resource=resource(start, windows)["resource"], role=names.get(start, "role unresolved"),
                pc=pc, operation=row["operation"], access=row["access"],
                resolution=row["resolution"], group=row["group"], group_function=row["group_function"]))
    summary = []
    # The abstract domain widens long cursor loops. Bind this range only to
    # the actual boot call and verify its byte walk with the CPU witness.
    assert ins[0x71d2].op == "LDX" and ins[0x71d2].value == 0x4008
    assert ins[0x71d5].target == 0xf2aa
    qualified = []
    checksum_bytes = set()
    for offset, pc in enumerate((0xf2c7,0xf2cb,0xf2cf,0xf2d3,0xf2d7,0xf2db,0xf2df,0xf2e3)):
        assert ins[pc].op == "ADDB" and ins[pc].mode == "indexed_x" and ins[pc].value == offset
        footprint = set(range(0x4008 + offset, 65536, 8))
        checksum_bytes.update(footprint)
        qualified.append(dict(pc=f"{pc:04X}", start=f"{min(footprint):04X}", end=f"{max(footprint):04X}",
            stride=8, distinct_bytes=len(footprint), resource="Program ROM checksum data",
            condition="Boot call71D5 with X4008 after CONFIG qualification; not arbitrary helper entry",
            proof="Exact caller/loop bytes plus bounded CPU address-walk witness"))
    for window in windows:
        lo, hi = int(window["start"], 16), int(window["end"], 16)
        selected = [r for r in rows if any(lo <= a <= hi for a in details[r["pc"]]["bytes"])]
        summary.append(dict(start=window["start"], end=window["end"], resource=window["resource"],
            fixed_read_sites=sum(bool(r["fixed_address"]) for r in selected),
            indexed_sites_with_finite_context=sum(not bool(r["fixed_address"]) for r in selected),
            distinct_finite_bytes=len({a for r in selected for a in details[r["pc"]]["bytes"] if lo <= a <= hi}),
            qualified_checksum_sites=sum(lo <= int(r["start"],16) <= hi for r in qualified),
            qualified_checksum_bytes=sum(lo <= a <= hi for a in checksum_bytes),
            qualification=window["assumption"]))
    by_address = defaultdict(lambda: dict(read_sites=set(), writers=set()))
    for row in rows:
        for address in details[row["pc"]]["bytes"]:
            by_address[address]["read_sites"].add(row["pc"])
            by_address[address]["writers"].update(f"{pc:04X}" for pc in writes[address])
    addresses = [dict(address=f"{a:04X}", resource=resource(a, windows)["resource"],
                      role=names.get(a, "unnamed byte or word companion"),
                      read_sites=";".join(sorted(v["read_sites"])),
                      finite_writer_sites=";".join(sorted(v["writers"]))) for a, v in sorted(by_address.items())]
    stack = []
    sizes = {"PULA": 1, "PULB": 1, "PULX": 2, "PULY": 2, "RTS": 2, "RTI": 9}
    for pc, i in sorted(ins.items()):
        if i.op in sizes:
            stack.append(dict(pc=f"{pc:04X}", bytes=i.data.hex(" "), operation=i.op,
                bytes_read=sizes[i.op], address="current CPU stack; no fixed byte owner inferred"))
    fetch = [dict(start=f"{a:04X}", end=f"{z:04X}", bytes=z-a+1)
             for a, z in ranges(a for i in ins.values() for a in range(i.pc, i.next_pc))]
    vectors = [dict(address=f"{a:04X}", target=f"{int.from_bytes(image[a:a+2], 'big'):04X}",
                    kind="CPU vector-fetch candidate; admission/mode selects which vector")
               for a in range(0xffd6, 65536, 2)]
    witness = run_witnesses(image)
    # The full-image path also checks the released checksum value; local
    # recorded replay cannot derive this word from incomplete ROM bytes.
    assert sum(image[0x4008:]) & 65535 == int.from_bytes(image[0x4006:0x4008], "big")
    metadata = dict(image_sha256=SHA, rooted_instructions=len(ins),
        procedure_entries=len(flow["functions"]), explicit_read_sites=len(rows),
        fixed_read_sites=sum(bool(r["fixed_address"]) for r in rows),
        indexed_read_sites=sum(not bool(r["fixed_address"]) for r in rows),
        rmw_read_sites=sum(r["access"] == "RW" for r in rows),
        indexed_sites_with_finite_context=sum(not r["fixed_address"] and bool(details[r["pc"]]["starts"]) for r in rows),
        indexed_sites_with_nonfinite_context=sum(bool(r["nonfinite_context_rows"]) for r in rows),
        distinct_finite_read_bytes=len(addresses), hardware_site_address_rows=len(hardware),
        distinct_hardware_operand_forms=len({(r["address"],r["width_bits"]) for r in hardware}),
        qualified_checksum_read_bytes=len(checksum_bytes),
        implicit_stack_read_sites=len(stack), instruction_fetch_bytes=sum(r["bytes"] for r in fetch),
        vector_words=len(vectors), read_witness_cases=witness["count"], reference_inputs=refs, scope=SCOPE)
    # Selected excerpts support local read witnesses; every operand read also
    # carries its own exact instruction bytes in READ_SITES.csv.
    spans = [(0x71c6, 0x71d2), (0xf245, 0xf280), (0xf3ed, 0xf420),
             (0xa5e5, 0xa5e8), (0xf90b, 0xf911), (0xf888, 0xf88a),
             (0xf8b8, 0xf8e6), (0xf4b8, 0xf4ba), (0x50a2, 0x50a3), (0x5216, 0x5218),
             (0xf20d,0xf245), (0xc56f,0xc583), (0xdc0a,0xdc10),
             (0xf2aa,0xf2fd), (0xfc44,0xfc45), (0x71d2,0x71d8), (0xffd6,0x10000)]
    evidence = dict(image_sha256=SHA,
        spans=[dict(start=f"{a:04X}", end_exclusive=f"{z:04X}", bytes=image[a:z].hex(" ")) for a,z in spans],
        scope="Recorded scoped read witnesses, not a complete image or full abstract-analysis replay")
    return dict(rows=rows, details=details, hardware=hardware, summary=summary,
                addresses=addresses, stack=stack, fetch=fetch, vectors=vectors,
                metadata=metadata, evidence=evidence, qualified=qualified, witness=witness)


def csv_text(rows):
    import io
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def outputs(result):
    tables = {"READ_SITES.csv": "rows", "HARDWARE_READS.csv": "hardware",
              "RESOURCE_SUMMARY.csv": "summary", "READ_ADDRESSES.csv": "addresses",
              "IMPLICIT_STACK_READS.csv": "stack", "INSTRUCTION_FETCH_RANGES.csv": "fetch",
              "VECTOR_READS.csv": "vectors", "QUALIFIED_READ_RANGES.csv": "qualified"}
    files = {name: csv_text(result[key]) for name, key in tables.items()}
    for name, key in (("READ_CONTEXTS.json", "details"), ("SUMMARY.json", "metadata"), ("EVIDENCE.json", "evidence"), ("EXECUTION_WITNESSES.json", "witness")):
        files[name] = json.dumps(result[key], indent=2) + "\n"
    return files


def check_recorded():
    def table(name):
        with (DATA / name).open(newline="") as stream:
            return list(csv.DictReader(stream))

    metadata = json.loads((DATA / "SUMMARY.json").read_text())
    details = json.loads((DATA / "READ_CONTEXTS.json").read_text())
    assert metadata["image_sha256"] == SHA
    for reference in metadata["reference_inputs"]:
        assert hashlib.sha256((ROOT / reference["path"]).read_bytes()).hexdigest() == reference["sha256"]
    register_update = json.loads((DATA / "REGISTER_UPDATES.json").read_text())
    assert register_update["image_sha256"] == SHA
    # This records the original hardware-row addition. Later audited reference
    # updates have their own before/after journal; current hashes are pinned by
    # reference_inputs above rather than rewriting historical update evidence.
    assert register_update["workbook"] == "7427_Address_Register_0.3.12.xlsx"
    with (DATA / "READ_SITES.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == metadata["explicit_read_sites"] == len({r["pc"] for r in rows})
    assert {r["pc"] for r in rows} == set(details)
    windows = expected_windows()
    for row in rows:
        pc = int(row["pc"], 16)
        data = bytes.fromhex(row["bytes"])
        i = decode(lambda a,n: data[a-pc:a-pc+n], pc)
        access = i.access()
        assert access and "R" in access["access"]
        assert (i.op+" "+i.operand).strip() == row["operation"]
        assert access["access"] == row["access"] and access["width_bits"] == int(row["width_bits"])
        assert (f"{access['address']:04X}" if access["address"] is not None else "") == row["fixed_address"]
        d = details[row["pc"]]
        starts = {int(row["fixed_address"], 16)} if row["fixed_address"] else {int(a,16) for c in d["contexts"] for a in c["starts"]}
        assert starts == set(d["starts"])
        byte_addresses = {(a + offset) & 65535 for a in starts for offset in range(access["width_bits"] // 8)}
        assert byte_addresses == set(d["bytes"])
        assert row["finite_starts"] == span_text(starts)
        assert row["finite_byte_ranges"] == span_text(byte_addresses)
        assert row["expected_resources"] == ";".join(sorted({resource(a,windows)["resource"] for a in byte_addresses}))
        nonfinite = [c for c in d["contexts"] if c["classification"] not in ("exact_address", "bounded_address_set")]
        assert int(row["context_rows"]) == len(d["contexts"])
        assert int(row["nonfinite_context_rows"]) == len(nonfinite)
    assert sum(bool(r["fixed_address"]) for r in rows) == metadata["fixed_read_sites"]
    assert sum(not bool(r["fixed_address"]) for r in rows) == metadata["indexed_read_sites"]
    assert sum(r["access"] == "RW" for r in rows) == metadata["rmw_read_sites"]
    assert sum(not r["fixed_address"] and bool(details[r["pc"]]["starts"]) for r in rows) == metadata["indexed_sites_with_finite_context"]
    assert sum(bool(int(r["nonfinite_context_rows"])) for r in rows) == metadata["indexed_sites_with_nonfinite_context"]
    hardware = table("HARDWARE_READS.csv")
    expected_hardware = {(r["pc"], f"{a:04X}", r["width_bits"], r["access"])
                         for r in rows for a in details[r["pc"]]["starts"]
                         if any(0x3000 <= ((a+o) & 65535) <= 0x3fff for o in range(int(r["width_bits"])//8))}
    assert len(hardware) == len(expected_hardware) == metadata["hardware_site_address_rows"]
    assert {(r["pc"],r["address"],r["width_bits"],r["access"]) for r in hardware} == expected_hardware
    assert len({(r["address"],r["width_bits"]) for r in hardware}) == metadata["distinct_hardware_operand_forms"]
    consumers = defaultdict(set)
    for row in rows:
        for address in details[row["pc"]]["bytes"]:
            consumers[address].add(row["pc"])
    addresses = table("READ_ADDRESSES.csv")
    assert len(addresses) == len(consumers) == metadata["distinct_finite_read_bytes"]
    assert {int(r["address"],16): set(r["read_sites"].split(";")) for r in addresses} == dict(consumers)
    resource_rows = table("RESOURCE_SUMMARY.csv")
    assert len(resource_rows) == len(windows)
    for row, window in zip(resource_rows, windows):
        assert (row["start"],row["end"],row["resource"]) == (window["start"],window["end"],window["resource"])
        lo, hi = int(row["start"],16), int(row["end"],16)
        selected = [r for r in rows if any(lo <= a <= hi for a in details[r["pc"]]["bytes"])]
        assert int(row["fixed_read_sites"]) == sum(bool(r["fixed_address"]) for r in selected)
        assert int(row["indexed_sites_with_finite_context"]) == sum(not bool(r["fixed_address"]) for r in selected)
        assert int(row["distinct_finite_bytes"]) == sum(lo <= a <= hi for a in consumers)
        assert int(row["qualified_checksum_sites"]) == (8 if lo == 0x4000 else 0)
        assert int(row["qualified_checksum_bytes"]) == (49144 if lo == 0x4000 else 0)
    stack = table("IMPLICIT_STACK_READS.csv")
    sizes = {"PULA":1,"PULB":1,"PULX":2,"PULY":2,"RTS":2,"RTI":9}
    assert len(stack) == len({r["pc"] for r in stack}) == metadata["implicit_stack_read_sites"]
    for row in stack:
        pc, data = int(row["pc"],16), bytes.fromhex(row["bytes"])
        i = decode(lambda a,n: data[a-pc:a-pc+n],pc)
        assert i.op == row["operation"] and sizes[i.op] == int(row["bytes_read"])
    fetch_bytes = set()
    for row in table("INSTRUCTION_FETCH_RANGES.csv"):
        span = set(range(int(row["start"],16),int(row["end"],16)+1))
        assert not (span & fetch_bytes) and len(span) == int(row["bytes"])
        fetch_bytes.update(span)
    assert len(fetch_bytes) == metadata["instruction_fetch_bytes"]
    assert all(set(range(int(r["pc"],16),int(r["pc"],16)+len(bytes.fromhex(r["bytes"])))) <= fetch_bytes for r in rows + stack)
    evidence = json.loads((DATA / "EVIDENCE.json").read_text())
    assert evidence["image_sha256"] == SHA
    partial = bytearray(65536)
    for span in evidence["spans"]:
        a, z = int(span["start"],16), int(span["end_exclusive"],16)
        data = bytes.fromhex(span["bytes"])
        assert len(data) == z-a
        partial[a:z] = data
    replay = run_witnesses(partial)
    assert replay == json.loads((DATA / "EXECUTION_WITNESSES.json").read_text())
    assert replay["count"] == metadata["read_witness_cases"]
    vectors = table("VECTOR_READS.csv")
    assert len(vectors) == metadata["vector_words"] == 21
    assert [int(r["address"],16) for r in vectors] == list(range(0xffd6,65536,2))
    for row in vectors:
        a = int(row["address"],16)
        assert row["target"] == f"{int.from_bytes(partial[a:a+2],'big'):04X}"
    with (DATA / "QUALIFIED_READ_RANGES.csv").open(newline="") as stream:
        qualified = list(csv.DictReader(stream))
    walk = next(c for c in replay["cases"] if c["name"] == "Boot checksum read footprint")["ranges"]
    assert len(qualified) == len(walk) == 8
    covered = set()
    for row, observed in zip(qualified, walk):
        assert (row["pc"],row["start"],row["end"],int(row["stride"]),int(row["distinct_bytes"])) == (observed["pc"],observed["start"],observed["end"],observed["stride"],observed["reads"])
        covered.update(range(int(row["start"],16), int(row["end"],16)+1, int(row["stride"])))
    assert covered == set(range(0x4008,65536)) and len(covered) == metadata["qualified_checksum_read_bytes"]
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--rom", type=Path)
    modes.add_argument("--check-recorded", action="store_true")
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    if args.check_recorded:
        if args.record:
            parser.error("Recording requires --rom")
        metadata = check_recorded()
    else:
        image = args.rom.read_bytes()
        result = build(image)
        for name, text in outputs(result).items():
            if args.record:
                DATA.mkdir(parents=True, exist_ok=True)
                (DATA / name).write_text(text)
            elif (DATA / name).read_text() != text:
                raise SystemExit("Stale read inventory: " + name)
        assert args.rom.read_bytes() == image
        metadata = result["metadata"]
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
