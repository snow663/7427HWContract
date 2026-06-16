#!/usr/bin/env python3
"""Build PER_TARGET_DOSSIER_INDEX from the full-ROM write sweep.

First-pass write-side grouping only. It does not attempt read/consumer proof,
create runtime ASM, or relax hardware-output gates.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

IN_SWEEP = Path("maps/generated/full_rom_write_target_sweep.csv")
OUT_CSV = Path("maps/generated/per_target_dossier_index.csv")
OUT_MD = Path("docs/analysis/PER_TARGET_DOSSIER_INDEX.md")
OUT_TEST = Path("docs/tests/PER_TARGET_DOSSIER_INDEX_TEST.md")

HIGH_VALUE_SYMBOLS = {
    "L3FCE": "fuel compact $3FCE hardware sink",
    "L3FE8": "spark stock handoff hardware/state",
    "L3FE6": "spark stock handoff hardware/state",
    "L3FDC": "spark stock handoff rolling state",
    "L3FF6": "spark stock handoff rolling anchor",
    "L3FEC": "spark stock monitor/source candidate",
    "L3FE4": "spark stock monitor/destination candidate",
    "L3062": "IAC output/phase candidate",
    "L3060": "IAC output/phase candidate",
    "L3FFC": "IAC/output-port candidate",
    "L303A": "COP/watchdog hardware sink",
}

HARDWARE_ROLES = {
    "fuel_pw_hardware_sink",
    "spark_stock_handoff_sink_or_state",
    "iac_output_sink_or_state",
    "watchdog_cop_sink",
    "hardware_or_asic_state",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def join_unique(values, limit: int | None = None) -> str:
    vals = [v for v in dict.fromkeys(values) if v]
    if limit is not None and len(vals) > limit:
        return ";".join(vals[:limit]) + f";...+{len(vals)-limit}"
    return ";".join(vals)


def count_summary(values) -> str:
    c = Counter(v for v in values if v)
    return "|".join(f"{k}:{v}" for k, v in c.most_common())


def highest_conf(values) -> str:
    rank = {"high": 3, "medium": 2, "low": 1, "": 0}
    return max(values, key=lambda v: rank.get(v, 0)) if values else ""


def reachability(group: list[dict[str, str]]) -> str:
    roles = {r["candidate_role"] for r in group}
    classes = {r["address_class"] for r in group}
    syms = {r["target_symbol"] for r in group}
    if roles & HARDWARE_ROLES or any(s in HIGH_VALUE_SYMBOLS for s in syms):
        return "hardware_or_preserved_driver_candidate"
    if "dispatcher selector" in roles:
        return "dispatcher_candidate"
    if "hardware_register_region_30xx" in classes or "asic_hardware_region_3fxx" in classes:
        return "hardware_address_class_candidate"
    return "not_established_write_side_only"


def preserved_relevance(group: list[dict[str, str]]) -> str:
    syms = {r["target_symbol"] for r in group}
    if "L3FCE" in syms:
        return "fuel_compact_route_hardware_sink"
    if syms & {"L3FE8","L3FE6","L3FDC","L3FF6","L3FEC","L3FE4"}:
        return "spark_stock_handoff_relevant"
    if syms & {"L3062","L3060","L3FFC"}:
        return "iac_stock_or_custom_driver_relevant"
    if "L303A" in syms:
        return "watchdog_hardware_relevant"
    return "unknown_pending_read_edges"


def decision(group: list[dict[str, str]]) -> tuple[str, str, str]:
    roles = {r["candidate_role"] for r in group}
    unresolved = sum(1 for r in group if r["index_resolution_status"] == "unresolved_indexed")
    disp = any(r["dispatcher_context"] for r in group)
    rel = preserved_relevance(group)
    hw = reachability(group)
    if hw.startswith("hardware") or "hardware_or_preserved" in hw:
        return "keep_or_preserve_until_proven_otherwise", "high", "hardware/preserved-driver candidate; no drop decision from write-side evidence alone"
    if unresolved:
        return "unknown_review_unresolved_indexed", "high", "unresolved indexed writes require base/dispatch context before decision"
    if disp:
        return "unknown_review_dispatch_context", "high", "near dispatcher context; require dispatcher reverse-map join"
    if "mode_flag_or_safety_gate" in roles:
        return "unknown_review_safety_or_mode", "medium", "mode/safety bit candidate; require read/consumer edge proof"
    if rel != "unknown_pending_read_edges":
        return "keep_or_preserve_until_proven_otherwise", "high", rel
    return "unknown_pending_read_consumer_edges", "medium", "write-side dossier only; next pass must add reads/consumers"


def key_for(row: dict[str, str]) -> str:
    return row.get("target_resolved") or row.get("target_symbol") or row.get("target_raw") or "unresolved_target"


def build(sweep_path: Path) -> list[dict[str, str]]:
    rows = read_rows(sweep_path)
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        groups[key_for(r)].append(r)

    out = []
    for key in sorted(groups):
        group = groups[key]
        target_symbol = join_unique((r["target_symbol"] for r in group), limit=5)
        address_class = count_summary(r["address_class"] for r in group)
        indexed_count = sum(1 for r in group if r["index_resolution_status"] == "resolved_indexed")
        unresolved_count = sum(1 for r in group if r["index_resolution_status"] == "unresolved_indexed")
        kdr, prio, note = decision(group)
        extra_notes = []
        if target_symbol in HIGH_VALUE_SYMBOLS:
            extra_notes.append(HIGH_VALUE_SYMBOLS[target_symbol])
        if note:
            extra_notes.append(note)
        out.append({
            "target_resolved": key,
            "target_symbol": target_symbol,
            "address_class": address_class,
            "write_count": str(len(group)),
            "write_pcs": join_unique((r["pc"] for r in group), limit=None),
            "write_classes": count_summary(r["write_class"] for r in group),
            "widths": count_summary(r["width"] for r in group),
            "bitmasks": join_unique((r["bitmask"] for r in group if r["bitmask"]), limit=None),
            "indexed_write_count": str(indexed_count),
            "unresolved_indexed_write_count": str(unresolved_count),
            "routine_labels": join_unique((r["routine_label"] for r in group), limit=20),
            "dispatcher_contexts": join_unique((r["dispatcher_context"] for r in group if r["dispatcher_context"]), limit=None),
            "candidate_roles": count_summary(r["candidate_role"] for r in group),
            "highest_confidence": highest_conf([r["confidence"] for r in group]),
            "hardware_reachability_status": reachability(group),
            "diagnostic_only_status": "not_proven_write_side_only",
            "preserved_driver_relevance": preserved_relevance(group),
            "keep_drop_replace_candidate": kdr,
            "review_priority": prio,
            "notes": "; ".join(extra_notes),
        })
    return out


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_md(path: Path, rows: list[dict[str, str]], sweep_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    decisions = Counter(r["keep_drop_replace_candidate"] for r in rows)
    priorities = Counter(r["review_priority"] for r in rows)
    hw = Counter(r["hardware_reachability_status"] for r in rows)
    lines = [
        "# PER_TARGET_DOSSIER_INDEX",
        "",
        "## Purpose",
        "",
        "First-pass write-side dossier index grouped from `FULL_ROM_WRITE_TARGET_SWEEP`.",
        "",
        "This groups the raw write/mutation evidence by `target_resolved` / `target_symbol` and produces review priority and keep/drop/replace candidates from write-side evidence only.",
        "",
        "It does not extract read sites, consumer edges, or downstream proof yet. It does not create runtime ASM, prove hardware behavior, mark bench gates passed, or authorize `SLICE-1`.",
        "",
        "## Source",
        "",
        f"- source sweep: `{sweep_path}`",
        f"- dossier rows: `{len(rows)}`",
        "",
        "## Decision summary",
        "",
    ]
    for k, v in decisions.most_common():
        lines.append(f"- `{k}`: {v}")
    lines += ["", "## Review priority summary", ""]
    for k, v in priorities.most_common():
        lines.append(f"- `{k}`: {v}")
    lines += ["", "## Hardware reachability status summary", ""]
    for k, v in hw.most_common():
        lines.append(f"- `{k}`: {v}")
    lines += [
        "",
        "## Required interpretation",
        "",
        "```text",
        "write-side grouping is not read/consumer proof",
        "diagnostic-only status is not proven in this pass",
        "drop/remove decisions are not allowed from this artifact alone",
        "hardware/safety/dispatch/preserved-driver candidates stay keep-or-review until downstream edges are proven",
        "```",
        "",
        "## Next layer",
        "",
        "The next static layer should add read sites, downstream consumers, hardware reachability, dispatcher involvement, and preserved-driver dependency edges.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_test(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("""# PER_TARGET_DOSSIER_INDEX_TEST

## Scope

Static test definition for first-pass per-target dossiers.

This pass is write-side grouping only. It must not attempt to fully prove read sites or downstream consumers unless a separate read/consumer extraction layer exists.

## Required input

```text
maps/generated/full_rom_write_target_sweep.csv
```

## Required output files

```text
tools/build_per_target_dossier_index.py
docs/analysis/PER_TARGET_DOSSIER_INDEX.md
maps/generated/per_target_dossier_index.csv
docs/tests/PER_TARGET_DOSSIER_INDEX_TEST.md
```

## Required CSV columns

```text
target_resolved
target_symbol
address_class
write_count
write_pcs
write_classes
widths
bitmasks
indexed_write_count
unresolved_indexed_write_count
routine_labels
dispatcher_contexts
candidate_roles
highest_confidence
hardware_reachability_status
diagnostic_only_status
preserved_driver_relevance
keep_drop_replace_candidate
review_priority
notes
```

## Required behavior

```text
group by target_resolved when present
fall back to target_symbol / target_raw for unresolved targets
count write classes and widths
flag indexed and unresolved-indexed writes
preserve dispatcher context
flag high-value hardware/preserved-driver candidates
mark diagnostic_only_status as not_proven_write_side_only
avoid final drop/remove decisions
```

## Non-relaxation clause

This artifact must not:

```text
create runtime ASM
mark bench proof passed
allow SLICE-1
accept fuel stock-driver preservation
accept IAC stock-driver preservation
allow custom hardware writers
claim diagnostic-only status without read/consumer proof
claim a target can be deleted from write-side evidence alone
```
""", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sweep", default=str(IN_SWEEP))
    args = parser.parse_args()
    sweep_path = Path(args.sweep)
    rows = build(sweep_path)
    write_csv(OUT_CSV, rows)
    write_md(OUT_MD, rows, sweep_path)
    write_test(OUT_TEST)
    print(f"wrote {len(rows)} per-target dossiers")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
