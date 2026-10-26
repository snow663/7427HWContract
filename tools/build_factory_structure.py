#!/usr/bin/env python3
"""Index factory listing structure and direct accesses without inventing dataflow.

Run from a checkout. --check regenerates in memory and reports committed drift.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
from collections import Counter, defaultdict
from pathlib import Path

from factory_structure import (
    ROOT, SOURCE, REGIONS, CALLS, classification, control_edge, data_region,
    load_regions, memory_access, number, parse_listing, text_sha256,
)

OUT = Path("maps/structure")


def csv_text(rows: list[dict], fields: list[str]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def address_region(address: int) -> str:
    for start, end, name in [
        (0x0000, 0x03FF, "low_memory_0000_03ff"),
        (0x0800, 0x08FF, "external_ram_0800_08ff"),
        (0x3000, 0x30FF, "register_30xx"),
        (0x3F00, 0x3FFF, "asic_3fxx"),
        (0x4000, 0x70FF, "calibration_rom_4000_70ff"),
        (0x7100, 0xFFFF, "listing_7100_ffff"),
    ]:
        if start <= address <= end:
            return name
    return "other_address"


def build() -> dict[Path, str]:
    regions = load_regions()
    statements = parse_listing(SOURCE)
    classes = {row.line: classification(row, regions) for row in statements}
    classes_at: dict[int, set[str]] = defaultdict(set)
    for row in statements:
        classes_at[row.pc].add(classes[row.line])

    def target_class(address: int) -> str:
        if data_region(address, regions):
            return "reviewed_embedded_data"
        found = classes_at.get(address, set())
        return ";".join(sorted(found)) if found else "not_a_listing_entry"

    review, accesses, edges = [], [], []
    entry_evidence: dict[int, list[tuple[str, str]]] = defaultdict(list)
    for row in statements:
        kind = classes[row.line]
        if kind != "instruction_candidate":
            region = data_region(row.pc, regions)
            review.append({
                "pc": f"{row.pc:04X}", "source_line": row.line,
                "mnemonic": row.op, "operand": row.operand,
                "classification": kind,
                "region_id": region.region_id if region else "",
            })
            # The legacy FCB word declaration is interpreted ONLY at this
            # independently traced 16-bit dispatcher table, not globally.
            if 0x7A85 <= row.pc <= 0x7AA3 and (row.pc - 0x7A85) % 2 == 0:
                target = number(row.operand)
                if row.op == "FCB" and target is not None:
                    entry_evidence[target].append(("major_loop_word_table", f"{row.pc:04X};7A4D;7A4F"))
            if 0xFFC0 <= row.pc <= 0xFFFE and row.pc % 2 == 0 and row.op == "FDB":
                target = number(row.operand)
                if target is not None:
                    entry_evidence[target].append(("source_vector_word", f"{row.pc:04X}"))
            continue
        access = memory_access(row)
        if access:
            accesses.append(access)
        edge = control_edge(row)
        if edge:
            address = edge["target_address"]
            edge["target_classification"] = target_class(int(address, 16)) if address else edge["resolution"]
            edges.append(edge)
            if address and row.op in CALLS:
                entry_evidence[int(address, 16)].append(("direct_call_target", f"{row.pc:04X}"))

    # Byte overlap is deliberate: STD $024E also writes $024F. No indirect
    # reads, implicit stack effects or value-dependency edges are claimed here.
    byte_accesses: dict[int, dict[str, set[str]]] = defaultdict(lambda: {"R": set(), "W": set()})
    for access in accesses:
        if access["resolution"] != "direct":
            continue
        address = int(access["target_address"], 16)
        for offset in range(access["width_bits"] // 8):
            state = byte_accesses[(address + offset) & 0xFFFF]
            for direction in access["access"]:
                state[direction].add(access["pc"])
    state_rows = []
    for address, state in sorted(byte_accesses.items()):
        state_rows.append({
            "byte_address": f"{address:04X}", "address_region": address_region(address),
            "direct_read_sites": len(state["R"]),
            "direct_write_sites": len(state["W"]),
            "read_pcs": ";".join(sorted(state["R"])),
            "write_pcs": ";".join(sorted(state["W"])),
            "proof_limit": "direct_listing_accesses_only;indexed_users_pending;value_flow_not_proven",
        })
    entries = [{
        "entry_address": f"{address:04X}",
        "entry_evidence": ";".join(sorted({kind for kind, _ in evidence})),
        "source_pcs": ";".join(sorted({pc for _, pcs in evidence for pc in pcs.split(";")})),
        "target_classification": target_class(address),
        "proof_limit": "candidate_entry;reachability_and_function_extent_not_proven",
    } for address, evidence in sorted(entry_evidence.items())]
    summary = {
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": text_sha256(SOURCE),
        "reviewed_regions_sha256": text_sha256(REGIONS),
        "listing_statements": len(statements),
        "statement_classification_counts": dict(sorted(Counter(classes.values()).items())),
        "reviewed_embedded_data_bytes": sum(region.end - region.start + 1 for region in regions),
        "control_edge_rows": len(edges),
        "unresolved_indirect_control_sites": [edge["pc"] for edge in edges if edge["resolution"] == "unresolved_indirect"],
        "unresolved_direct_control_operands": [edge["pc"] for edge in edges if edge["resolution"] == "unresolved_direct_operand"],
        "direct_control_into_reviewed_data": [edge["pc"] for edge in edges if edge["target_classification"] == "reviewed_embedded_data"],
        "memory_access_rows": len(accesses),
        "memory_resolution_counts": dict(sorted(Counter(row["resolution"] for row in accesses).items())),
        "candidate_entry_points": len(entries),
        "directly_referenced_memory_bytes": len(state_rows),
        "scope": "source_listing_structure_only;not_binary_verified;not_semantic_completion;not_reachability_proof",
    }
    return {
        OUT / "factory_listing_review.csv": csv_text(review, ["pc", "source_line", "mnemonic", "operand", "classification", "region_id"]),
        OUT / "factory_memory_accesses.csv": csv_text(accesses, ["pc", "source_line", "mnemonic", "operand", "access", "width_bits", "target_address", "resolution", "bitmask"]),
        OUT / "factory_state_index.csv": csv_text(state_rows, ["byte_address", "address_region", "direct_read_sites", "direct_write_sites", "read_pcs", "write_pcs", "proof_limit"]),
        OUT / "factory_control_edges.csv": csv_text(edges, ["pc", "source_line", "mnemonic", "target_operand", "target_address", "edge_kind", "resolution", "target_classification"]),
        OUT / "factory_entry_points.csv": csv_text(entries, ["entry_address", "entry_evidence", "source_pcs", "target_classification", "proof_limit"]),
        OUT / "factory_structure_summary.json": json.dumps(summary, indent=2, sort_keys=True) + "\n",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build()
    changed = []
    for relative, text in outputs.items():
        path = ROOT / relative
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                changed.append(str(relative))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    if changed:
        print("Stale factory-structure outputs: " + ", ".join(changed))
        return 1
    print(f"{'Verified' if args.check else 'Generated'} {len(outputs)} factory-structure files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
