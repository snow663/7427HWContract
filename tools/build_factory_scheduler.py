#!/usr/bin/env python3
"""Build a bounded, ROM-backed BMHM scheduler map.

--rom requires the complete hash-identified image. --check-recorded regenerates
from committed excerpts only, and is not a fresh full-ROM verification.
Calls are boundaries in callee state maps; indexed addresses remain unresolved.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path

from factory_rom_decode import DecodeError, decode, successors
from factory_structure import ROOT, SOURCE, load_regions, memory_access, parse_listing, text_sha256
from verify_factory_rom_structure import EXPECTED_SHA256

OUT = ROOT / "maps/structure"
EVIDENCE = OUT / "bmhm_scheduler_rom_evidence.json"
PROFILE = ROOT / "hac31_romsim/romsim/profiles/gm_16197427_31.json"
SCOPES = [
    ("boot_clock", 0x7100, 0x7115),
    ("boot_clear_calls", 0x7164, 0x718A),
    ("phase_seed", 0x7431, 0x7435),
    ("timer_arm", 0x7459, 0x746C),
    ("foreground_refresh", 0x746C, 0x74D3),
    ("timer_isr", 0x793D, 0x7A85),
    ("stub_return", 0x7AA5, 0x7AA6),
    ("tick_service", 0x7B6D, 0x7BA7),
    ("ram_clear_helper", 0xF2FD, 0xF326),
    ("heartbeat", 0xF3E4, 0xF3EE),
    ("service_receive", 0xF9B9, 0xFA21),
    ("service_payload_copy", 0xFA10, 0xFA21),
    ("factory_entry", 0xFA5B, 0xFACA),
    ("factory_cycle_phase", 0xFAFD, 0xFB13),
    ("factory_wait", 0xFBD4, 0xFBD7),
    ("reset", 0xFC29, 0xFC2F),
]
NORMAL = "($001A & $20)==0 at $79D9"
SPECIAL = "($001A & $20)!=0 at $79D9"
HEARTBEAT = "not (($003B & $10)!=0 and ($0391 & $80)!=0) at $7A1F-$7A28"
# Reviewed guards describe instruction-time tests. Periods assume an unmodified
# normal phase sequence and stable gates; they are admissions, not completions.
FAST_GUARDS = {
    0x797A: ("non-factory timer entry after stack check; includes busy reentry", 1),
    0x79E4: (f"{SPECIAL}; phase bit0=1", 2),
    0x79F2: (NORMAL, 1),
    **{p: (f"{NORMAL}; phase bit0=0", 2) for p in [0x79F9, 0x79FC, 0x79FF, 0x7A02, 0x7A05]},
    0x7A0C: (f"{NORMAL}; phase & $03 == $02", 4),
    **{p: (f"{NORMAL}; phase & $03 == $00", 4) for p in [0x7A11, 0x7A14]},
    **{p: (f"{NORMAL}; phase bit0=1", 2) for p in [0x7A19, 0x7A1C]},
    0x7A32: (f"{NORMAL}; phase bit0=1; {HEARTBEAT}", 2),
    **{p: (f"{NORMAL}; phase & $03 == $03", 4) for p in [0x7A39, 0x7A3C]},
    0x7A41: (f"{NORMAL}; phase & $03 == $01", 4),
}
GATES = [(0x0002, 0xFF, "phase"), (0x0001, 1, "factory_callback_latch"),
         (0x001A, 0x20, "special_fast_group"), (0x003B, 0x10, "service_mode"),
         (0x0044, 1, "factory_mode"), (0x004F, 4, "busy"),
         (0x003A, 0x20, "pending"), (0x0086, 0x40, "profiling_enable"),
         (0x0051, 4, "refresh_request"), (0x038F, 4, "service_copy_enable"),
         (0x0390, 4, "service_copy_value"), (0x0391, 0x80, "board_toggle_hold")]


class ROM:
    def __init__(self, data=None, memory=None):
        self.data, self.memory, self.used = data, memory, set()

    def read(self, address, length):
        if address < 0 or address + length > 0x10000:
            raise ValueError(f"Read outside CPU image: {address:04X}+{length}")
        self.used.update(range(address, address + length))
        if self.data is not None:
            return self.data[address:address + length]
        return bytes(self.memory[a] for a in range(address, address + length))

    def word(self, address):
        return int.from_bytes(self.read(address, 2), "big")

    def ranges(self):
        groups = []
        for address in sorted(self.used):
            if not groups or address != groups[-1][-1] + 1:
                groups.append([])
            groups[-1].append(address)
        return [{"start": f"{g[0]:04X}", "end_exclusive": f"{g[-1]+1:05X}",
                 "bytes_hex": self.read(g[0], len(g)).hex(" ").upper()} for g in groups]


def full_rom(path):
    data = path.read_bytes()
    if len(data) != 65536 or hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
        raise ValueError("Requires complete 65,536-byte stock BMHM image with the recorded SHA-256")
    return ROM(data=data)


def recorded_rom(evidence):
    if evidence["rom_size_bytes"] != 65536 or evidence["rom_sha256"] != EXPECTED_SHA256:
        raise ValueError("Unexpected recorded ROM identity")
    if evidence["listing_sha256_lf"] != text_sha256(SOURCE):
        raise ValueError("HAC listing changed since the scheduler review")
    memory = {}
    for block in evidence["byte_ranges"]:
        start, end = int(block["start"], 16), int(block["end_exclusive"], 16)
        data = bytes.fromhex(block["bytes_hex"])
        if len(data) != end - start:
            raise ValueError("Recorded scheduler range length mismatch")
        for address, value in enumerate(data, start):
            if address in memory and memory[address] != value:
                raise ValueError("Conflicting scheduler ROM excerpts")
            memory[address] = value
    return ROM(memory=memory)


def csv_text(rows, fields=None):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def h(value):
    return "" if value is None else f"{value:04X}"


def region(address):
    if address is None:
        return "unresolved_indexed"
    if address < 0x1000:
        return "ram"
    if 0x3000 <= address <= 0x303F:
        return "cpu_io"
    if 0x3060 <= address <= 0x30FF:
        return "board_io"
    if 0x3FC0 <= address <= 0x3FFF:
        return "asic"
    if address >= 0x4000:
        return "rom"
    return "unclassified"


def access_row(scope, ins):
    access = ins.access()
    if access is None:
        return None
    address = access["address"]
    # This one local pointer is proven by the immediately preceding CE 40 0F.
    # Other indexed accesses are deliberately retained unresolved.
    if ins.pc == 0x7B0C and ins.op == "BRSET" and ins.mode == "indexed_x" and ins.value == 0:
        address = 0x400F
    return {"scope": scope, "pc": h(ins.pc), "bytes_hex": ins.data.hex(" ").upper(),
            "mnemonic": ins.op, "operand": ins.operand, "access": access["access"],
            "width_bits": access["width_bits"], "address": h(address),
            "byte_addresses": ";".join(h(address+i) for i in range(access["width_bits"]//8)) if address is not None else "",
            "region": region(address), "index_register": access["index"],
            "index_offset": "" if access["offset"] is None else f"{access['offset']:02X}",
            "mask": "" if access["mask"] is None else f"{access['mask']:02X}",
            "scope_limit": "explicit_access_only;calls_and_implicit_stack_excluded"}


def walk_callee(rom, entry, data_regions):
    """Follow explicit branches/jumps; leave calls and indexed jumps as boundaries."""
    pending, instructions, frontier = [entry], {}, []
    while pending:
        pc = pending.pop()
        if pc in instructions:
            continue
        if not 0x7100 <= pc < 0x10000 or any(r.start <= pc <= r.end for r in data_regions):
            frontier.append((pc, "outside_code_scope_or_reviewed_data"))
            continue
        if len(instructions) >= 2000:
            frontier.append((pc, "instruction_budget"))
            break
        try:
            ins = decode(rom.read, pc)
        except DecodeError as error:
            frontier.append((pc, str(error)))
            continue
        instructions[pc] = ins
        if ins.op == "JMP" and ins.target is None:
            frontier.append((pc, "unresolved_indexed_jump"))
        pending.extend(target for target, _ in successors(ins))
    return instructions, sorted(set(frontier))


def canonical_operand(operand):
    parts = []
    for token in operand.upper().replace(" ", "").split(","):
        if not token:
            continue
        immediate = token.startswith("#")
        raw = token[1:] if immediate else token
        if raw in {"X", "Y"}:
            parts.append(raw)
            continue
        if re.fullmatch(r"(?:L|\$)[0-9A-F]{1,4}", raw):
            value = int(raw[1:], 16)
        elif re.fullmatch(r"-?[0-9]+", raw):
            value = int(raw)
        else:
            return None
        parts.append(("#" if immediate else "") + str(value))
    return tuple(parts)


def gate_producers(rom):
    """Byte-check direct writer candidates; this is not an indexed-writer sweep."""
    candidates = []
    for source in parse_listing(SOURCE):
        access = memory_access(source)
        if access and "W" in access["access"] and access["target_address"]:
            candidates.append((source, access))
    rows = []
    for address, mask, name in GATES:
        found = False
        for source, access in candidates:
            target = int(access["target_address"], 16)
            if not target <= address < target + access["width_bits"]//8:
                continue
            ins = decode(rom.read, source.pc)
            actual = ins.access()
            confirmed = actual and "W" in actual["access"] and actual["address"] is not None and actual["address"] <= address < actual["address"]+actual["width_bits"]//8
            if confirmed and actual["mask"] is not None and not actual["mask"] & mask:
                continue
            found = True
            rows.append({"gate": name, "address": h(address), "gate_mask": f"{mask:02X}",
                         "writer_pc": h(ins.pc), "bytes_hex": ins.data.hex(" ").upper(),
                         "rom_instruction": (ins.op+" "+ins.operand).strip(),
                         "status": "direct_writer_byte_checked" if confirmed else "listing_candidate_does_not_decode_as_this_write",
                         "scope_limit": "listing_seeded_candidates;indexed_writers_and_value_effect_on_bit_not_closed"})
        if not found:
            rows.append({"gate": name, "address": h(address), "gate_mask": f"{mask:02X}",
                         "writer_pc": "", "bytes_hex": "", "rom_instruction": "",
                         "status": "no_direct_listing_writer_candidate;indexed_producers_pending",
                         "scope_limit": "listing_seeded_candidates;not_proof_of_no_writes"})
    return rows


def build(rom):
    table = [rom.word(0x7A85 + i*2) for i in range(16)]
    # Anchor the dispatch operation independently of HAC's table declarations.
    if rom.read(0x7A44, 13) != bytes.fromhex("D6 02 C4 0F CE 7A 85 58 3A EE 00 AD 00"):
        raise ValueError("Unexpected main dispatcher bytes")
    if rom.word(0xFFE4) != 0x793D or rom.word(0xFFFE) != 0xFC29:
        raise ValueError("Unexpected scheduler/reset vector")
    if table != [0x7AA6, 0x7AAD, 0x7AB7, 0x7ABD, 0x7AC7, 0x7B03, 0x7B14, 0x7B1B,
                 0x7B2B, 0x7B2F, 0x7B39, 0x7B3D, 0x7B44, 0x7B48, 0x7B52, 0x7B5A]:
        raise ValueError("Unexpected scheduler landing table")
    rom.read(0x400F, 1)  # Actual BMHM slot-5 feature gate.
    rom.read(0x495D, 2)  # Run-timer comparison on the 160-phase wrap.
    scopes = SCOPES + [(f"slot_{slot:X}", entry, (table+[0x7B6D])[slot+1]) for slot, entry in enumerate(table)]
    scoped, by_pc = [], {}
    for scope, start, end in scopes:
        pc = start
        while pc < end:
            ins = decode(rom.read, pc)
            if ins.next_pc > end or ins.next_pc <= pc:
                raise ValueError(f"Instruction crosses reviewed span at {pc:04X}")
            scoped.append((scope, ins))
            by_pc[pc] = ins
            pc = ins.next_pc

    profile = json.loads(PROFILE.read_text())
    tick_ms = 819 * 16 * 1000 / profile["e_clock_hz"]
    calls = []
    for scope, ins in scoped:
        if ins.op not in {"JSR", "BSR"}:
            continue
        guard, period = FAST_GUARDS.get(ins.pc, ("see enclosing ROM control-flow edges", None))
        if scope.startswith("slot_"):
            slot = int(scope[5:], 16)
            guard, period = f"phase & $0F == ${slot:X}", 16
            if slot == 4 and 0x7ACE <= ins.pc <= 0x7ADD:
                guard += "; phase bit4=1"
                period = 32
            elif slot == 4 and 0x7AE2 <= ins.pc <= 0x7AEE:
                guard += "; phase bit4=0"
                period = 32
            elif ins.pc == 0x7B10:
                guard += "; ROM[$400F] bit6=0 (true in stock BMHM: $10)"
        elif scope == "tick_service":
            guard, period = "inside $7B6D on non-factory timer entry; includes busy reentry; not repeated by tail catch-up", 1
        elif ins.pc == 0xFA78:
            guard = "factory entry; first ADC sample is $28..$63 inclusive"
        elif ins.pc in {0xFA63, 0xFA68}:
            guard = "factory entry before ADC qualification"
        elif ins.pc == 0xFA94:
            guard = "factory entry; selector byte $0364 != $02"
        elif ins.pc == 0xFAA5:
            guard = "factory entry; selector=$02 or (selector=$03 and $0001 bit0=1); target=wordRAM[$038E]"
        destinations = table if ins.pc == 0x7A4F else [ins.target]
        for slot, target in enumerate(destinations):
            dispatch = ins.pc == 0x7A4F
            actual_period = 16 if dispatch else period
            calls.append({"scope": scope, "call_pc": h(ins.pc), "bytes_hex": ins.data.hex(" ").upper(),
                          "target": h(target), "target_resolution": "rom_word_table" if dispatch else "direct" if target is not None else "unresolved_ram_word",
                          "guard": f"main pass; phase & $0F == ${slot:X}; either $001A mode" if dispatch else guard,
                          "nominal_period_ticks": actual_period or "",
                          "nominal_period_ms": f"{actual_period*tick_ms:.6f}" if actual_period else "",
                          "rate_limit": "admission_if_gates_hold;overrun_and_callee_side_effects_can_change_wall_time"})

    # One level of callee state: direct control flow is decoded from ROM, but
    # nested calls are explicitly excluded rather than silently flattened.
    scope_pcs = set(by_pc)
    roots = sorted({int(row["target"], 16) for row in calls if row["target"] and int(row["target"], 16) not in scope_pcs})
    callee_summary, callee_accesses = [], []
    data_regions = load_regions()
    for entry in roots:
        instructions, frontier = walk_callee(rom, entry, data_regions)
        accesses = [access_row(h(entry), ins) for ins in instructions.values()]
        accesses = sorted((a for a in accesses if a), key=lambda a: a["pc"])
        callee_accesses.extend(accesses)
        by_pc.update(instructions)
        callee_summary.append({"entry": h(entry), "rom_instruction_count": len(instructions),
            "direct_read_bytes": ";".join(sorted({a for r in accesses if "R" in r["access"] for a in r["byte_addresses"].split(";") if a})),
            "direct_write_bytes": ";".join(sorted({a for r in accesses if "W" in r["access"] for a in r["byte_addresses"].split(";") if a})),
            "unresolved_indexed_accesses": sum(not a["address"] for a in accesses),
            "nested_call_sites": ";".join(f"{p:04X}:{h(i.target) or i.operand}" for p,i in sorted(instructions.items()) if i.op in {"JSR", "BSR"}),
            "frontiers": ";".join(f"{pc:04X}:{reason}" for pc,reason in frontier),
            "scope_limit": "intraprocedural_ROM_CFG;branch_feasibility_nested_calls_and_implicit_stack_not_closed"})

    instructions = [{"pc": h(pc), "bytes_hex": ins.data.hex(" ").upper(), "mnemonic": ins.op,
                     "operand": ins.operand, "addressing_mode": ins.mode, "next_pc": h(ins.next_pc)}
                    for pc, ins in sorted(by_pc.items())]
    accesses = [access_row(scope, ins) for scope, ins in scoped if ins.access()]
    edges = []
    for scope, ins in scoped:
        if ins.op in {"JSR", "BSR"}:
            targets = table if ins.pc == 0x7A4F else [ins.target]
            for target in targets:
                edges.append({"scope": scope, "from_pc": h(ins.pc), "to_pc": h(target), "kind": "call",
                              "condition": "phase-selected ROM table word" if ins.pc == 0x7A4F else "RAM[$038E:$038F]" if target is None else "call target"})
        for target, kind in successors(ins):
            edges.append({"scope": scope, "from_pc": h(ins.pc), "to_pc": h(target), "kind": kind,
                          "condition": f"{ins.op} {ins.operand}" if kind.startswith("branch_") else "callee must return" if kind == "on_call_return" else ""})

    listing = {r.pc: r for r in parse_listing(SOURCE)}
    discrepancies = []
    aliases = {"LSL": "ASL", "LSLA": "ASLA", "LSLB": "ASLB", "BHS": "BCC", "BLO": "BCS"}
    for pc, ins in sorted(by_pc.items()):
        source = listing.get(pc)
        reason = "missing_addressed_listing_row" if source is None else ""
        if source:
            if aliases.get(source.op, source.op) != ins.op:
                reason = "mnemonic_differs"
            else:
                left, right = canonical_operand(source.operand), canonical_operand(ins.operand)
                if left is None:
                    reason = "unparsed_listing_operand"
                elif left != right:
                    reason = "operand_differs"
        if reason:
            discrepancies.append({"pc": h(pc), "bytes_hex": ins.data.hex(" ").upper(),
                "rom_instruction": (ins.op+" "+ins.operand).strip(),
                "listing_instruction": (source.op+" "+source.operand).strip() if source else "",
                "reason": reason, "source_line": source.line if source else ""})

    slots = []
    for slot, entry in enumerate(table):
        local = [r for r in accesses if r["scope"] == f"slot_{slot:X}"]
        slots.append({"slot_hex": f"{slot:X}", "table_word_address": h(0x7A85+slot*2),
                      "table_bytes": rom.read(0x7A85+slot*2, 2).hex(" ").upper(), "entry": h(entry),
                      "nominal_period_ticks": 16, "nominal_period_ms": f"{16*tick_ms:.6f}",
                      "ordered_call_sites": ";".join(r["call_pc"]+":"+r["target"] for r in calls if r["scope"] == f"slot_{slot:X}"),
                      "local_state_access_pcs": ";".join(r["pc"] for r in local),
                      "special_behavior": {2: "SEI around $F20D, then CLI", 4: "bit4 selects alternating call groups; rebuilds $006F bits $24", 5: "$400F bit6 gates $C6BB", 14: "no calls; sets $0004 bit2 if $0051 bit2 still set", 15: "sets $0051 bit2 after calls; foreground refresh clears it"}.get(slot, ""),
                      "scope_limit": "slot_wrapper_and_one_level_callee_CFG;not_transitive_state_closure"})

    producers = gate_producers(rom)

    outputs = {
        "factory_scheduler_slots.csv": csv_text(slots),
        "factory_scheduler_calls.csv": csv_text(calls),
        "factory_scheduler_state_accesses.csv": csv_text(accesses),
        "factory_scheduler_callee_summary.csv": csv_text(callee_summary),
        "factory_scheduler_callee_accesses.csv": csv_text(callee_accesses),
        "factory_scheduler_instructions.csv": csv_text(instructions),
        "factory_scheduler_control_edges.csv": csv_text(edges),
        "factory_scheduler_gate_producers.csv": csv_text(producers),
        "factory_scheduler_listing_discrepancies.csv": csv_text(discrepancies, ["pc", "bytes_hex", "rom_instruction", "listing_instruction", "reason", "source_line"]),
    }
    evidence = {"rom_name": "BMHM.BIN", "rom_size_bytes": 65536, "rom_sha256": EXPECTED_SHA256,
        "listing_sha256_lf": text_sha256(SOURCE), "file_offset_equals_cpu_address_in_mapped_rom": True,
        "clock_source": "hac31_romsim/romsim/profiles/gm_16197427_31.json;repository_contract_not_new_bench_measurement",
        "e_clock_hz": profile["e_clock_hz"], "timer_prescaler": 16, "compare_increment": 819,
        "nominal_tick_ms": tick_ms, "stock_400F_hex": rom.read(0x400F, 1).hex().upper(),
        "scoped_instruction_rows": len(scoped), "unique_rom_instruction_rows": len(instructions),
        "callee_roots": roots, "listing_discrepancies": len(discrepancies),
        "byte_ranges": rom.ranges(),
        "proof_scope": "scoped_ROM_decoding_and_intraprocedural_state_inventory;not_whole_ROM_reachability;not_transitive_callee_semantics;not_physical_timing_validation"}
    outputs[EVIDENCE.name] = json.dumps(evidence, indent=2, sort_keys=True)+"\n"
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check-recorded", action="store_true")
    args = parser.parse_args()
    if args.check_recorded:
        if args.rom or args.write:
            parser.error("Recorded checking is separate from full-ROM verification")
        rom = recorded_rom(json.loads(EVIDENCE.read_text()))
    elif args.rom:
        rom = full_rom(args.rom)
    else:
        parser.error("Supply --rom, or --check-recorded")
    outputs = build(rom)
    for name, content in outputs.items():
        path = OUT / name
        if args.write:
            path.write_text(content, encoding="utf-8")
        elif not path.exists() or path.read_text(encoding="utf-8") != content:
            raise ValueError(f"Scheduler output differs: {path.relative_to(ROOT)}")
    print(f"PASS: {len(outputs)} scheduler outputs; " + ("recorded excerpt consistency only" if args.check_recorded else "complete BMHM ROM identity and scoped bytes verified"))


if __name__ == "__main__":
    main()
