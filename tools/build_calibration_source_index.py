#!/usr/bin/env python3
"""Build a calibration source index from the HAC calibration extract HTML.

The input HTML is expected to contain the machine-readable JSON payload:

    <script id="calibration-extract-json" type="application/json">...</script>

The output is a section-level index, not a tuning artifact. It classifies
calibration sections by future minimal-OS module relevance while preserving
excluded strategy baggage as excluded.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

CSV_FIELDS = [
    "section_index", "section_name", "section_title", "start_address", "end_address",
    "record_count", "fcb_count", "fdb_count", "data_width", "raw_label",
    "raw_comment", "module_candidate", "submodule_candidate", "minimal_os_relevance",
    "excluded_reason", "source_confidence", "needs_hardware_contract", "notes",
]

EXPECTED = {
    "section_count": 226,
    "record_count": 11916,
    "fcb_count": 11431,
    "fdb_count": 485,
    "parse_error_count": 0,
    "min_data_address_hex": "$4000",
    "max_data_address_hex": "$70FF",
}

EXCLUDED_RULES = [
    ("trans_excluded", ["TCC", "TRANS", "TRANSMISSION", "SHIFT", "4L60", "4L80", "GEAR", "PRNDL"], "transmission strategy excluded unless hardware-required"),
    ("egr_excluded", ["EGR", "EVRV", "PINTEL"], "EGR/emissions strategy excluded"),
    ("evap_excluded", ["EVAP", "PURGE", "CANISTER", "CCP", "CHARCOAL"], "EVAP/purge strategy excluded"),
]

MODULE_RULES = [
    ("injector_deadtime", ["DEADTIME", "DEAD TIME", "INJ BIAS", "INJECTOR BIAS", "BATTERY OFFSET", "VOLTAGE OFFSET"], "injector low-pulsewidth/deadtime", "bench_gated"),
    ("spark_latency", ["SPARK LAT", "SPARK LATENT", "SPK LAT", "EST LAT", "LATENCY"], "spark module latency", "bench_gated"),
    ("crank_start", ["CRANK", "START", "STARTUP", "START UP", "AFTER CRANK", "CLEAR FLOOD"], "crank/start module", "likely_required"),
    ("warmup_afterstart", ["WARMUP", "WARM UP", "AFTERSTART", "AFTER START", "COOLANT COMP", "CTS COMP", "CHOKE"], "warmup/afterstart module", "likely_required"),
    ("iac_idle", ["IAC", "AIS", "IDLE AIR", "IDLE", "DESIRED IDLE", "TARGET RPM", "RPM TARGET", "PARK DOWN", "PARK", "MIN AIR", "IAC MOTOR"], "IAC/idle-air module", "bench_gated"),
    ("fuel", ["BPW", "BASE PULSE", "VE", "VOLUMETRIC", "AFR", "A/F", "PE", "POWER ENRICH", "AE", "ACCEL", "DFCO", "DECEL FUEL", "FUEL", "INJ", "INJECTOR", "PULSE WIDTH", "P/W", "MAP FUEL"], "fuel math/output support", "likely_required"),
    ("spark", ["SPK", "SPARK", "ADV", "ADVANCE", "EST", "KNOCK", "RETARD", "LO OCT", "LOW OCT"], "spark math/output support", "bench_gated"),
    ("battery_voltage", ["BATT", "BATTERY", "VOLT", "VOLTAGE", "VDC"], "voltage qualification/correction", "likely_required"),
    ("sensor_scaling", ["MAP", "TPS", "CTS", "MAT", "IAT", "O2", "OXYGEN", "BARO", "A/D", "ADC", "AD VALUE", "VAC", "KPA"], "sensor scaling/input conditioning", "likely_required"),
    ("aldl_debug", ["ALDL", "SERIAL", "UART", "BAUD", "PROM ID", "EPROM ID", "CHECKSUM", "MALF", "DTC", "DIAG", "DIAGNOSTIC"], "ALDL/debug/diagnostics", "calibration_only"),
    ("watchdog_safe_state", ["WATCHDOG", "RESET", "LIMP", "SAFE", "FAIL", "DEFAULT", "OVERSPEED", "CUT OFF", "CUTOFF"], "safe-state/diagnostic limits", "bench_gated"),
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root() / p


def load_extract(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'<script id="calibration-extract-json" type="application/json">(.*?)</script>', text, re.S)
    if not m:
        raise SystemExit("calibration-extract-json payload not found")
    return json.loads(html.unescape(m.group(1)))


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").upper())


def keyword_match(text: str, word: str) -> bool:
    """Conservative keyword match.

    Short alphabetic acronyms such as EGR and TCC must match as standalone
    terms so they do not fire on INTEGRATOR or TRANSIENT. Phrases and tokens
    with punctuation use substring matching after normalization.
    """
    t = norm(text)
    w = norm(word)
    if not w:
        return False
    if re.fullmatch(r"[A-Z0-9]{2,6}", w):
        return re.search(rf"(?<![A-Z0-9]){re.escape(w)}(?![A-Z0-9])", t) is not None
    return w in t


def contains_any(text: str, words: list[str]) -> bool:
    return any(keyword_match(text, w) for w in words)


def section_text(sec: dict[str, Any], records: list[dict[str, Any]]) -> str:
    pieces = [sec.get("org_comment", ""), sec.get("context", "")]
    # Include all record labels/comments/source lines so small sections still classify.
    for r in records:
        pieces.extend([r.get("label", ""), r.get("comment", ""), r.get("source_line", "")])
    return " | ".join(str(p) for p in pieces if p)


def first_nonempty(values: list[str], max_len: int = 220) -> str:
    for v in values:
        v = re.sub(r"\s+", " ", (v or "").strip())
        if v:
            return v[:max_len]
    return ""


def classify(sec: dict[str, Any], records: list[dict[str, Any]]) -> tuple[str, str, str, str, str, str, str]:
    text = section_text(sec, records)
    upper = norm(text)

    # Exclusions win first so EGR spark correction remains excluded.
    for module, words, reason in EXCLUDED_RULES:
        if contains_any(upper, words):
            return module, module.replace("_excluded", ""), "excluded", reason, "high_keyword", "no", "excluded strategy baggage; do not feed minimal OS unless future hardware contract proves requirement"

    for module, words, submodule, relevance in MODULE_RULES:
        if contains_any(upper, words):
            confidence = "medium_keyword"
            if sec.get("org_comment") and contains_any(sec.get("org_comment", ""), words):
                confidence = "high_keyword"
            elif any(contains_any(r.get("comment", ""), words) for r in records[:12]):
                confidence = "high_keyword"
            needs_hw = "yes" if relevance in {"bench_gated", "likely_required"} else "no"
            notes = "classified by label/comment keywords; validate exact usage through module-specific source references before marking required"
            return module, submodule, relevance, "", confidence, needs_hw, notes

    return "unknown", "unknown", "unknown", "", "low_unclassified", "yes_if_later_used", "no confident module keyword; keep listed rather than guessing"


def data_width(sec: dict[str, Any]) -> str:
    fcb = int(sec.get("fcb_count") or 0)
    fdb = int(sec.get("fdb_count") or 0)
    if fcb and fdb:
        return "mixed_fcb_fdb"
    if fdb:
        return "16_bit_fdb"
    if fcb:
        return "8_bit_fcb"
    return "unknown"


def build_rows(obj: dict[str, Any]) -> list[dict[str, str]]:
    recs_by: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for r in obj["records"]:
        recs_by[int(r["section_index"])].append(r)

    out = []
    for sec in obj["sections"]:
        idx = int(sec["section_index"])
        recs = recs_by[idx]
        module, submodule, relevance, excluded_reason, conf, needs_hw, notes = classify(sec, recs)
        labels = [r.get("label", "") for r in recs[:6]]
        comments = [sec.get("org_comment", ""), sec.get("context", "")]
        comments.extend(r.get("comment", "") for r in recs[:8])
        section_title = first_nonempty([sec.get("org_comment", ""), sec.get("context", ""), *(r.get("comment", "") for r in recs[:8])])
        if not section_title:
            section_title = f"calibration section {idx}"
        out.append({
            "section_index": str(idx),
            "section_name": f"CAL_{sec.get('org_hex', '')}",
            "section_title": section_title,
            "start_address": sec.get("first_data_hex") or sec.get("org_hex") or "",
            "end_address": sec.get("last_data_hex") or "",
            "record_count": str(sec.get("data_count", "")),
            "fcb_count": str(sec.get("fcb_count", "")),
            "fdb_count": str(sec.get("fdb_count", "")),
            "data_width": data_width(sec),
            "raw_label": first_nonempty(labels, 140),
            "raw_comment": first_nonempty(comments, 260),
            "module_candidate": module,
            "submodule_candidate": submodule,
            "minimal_os_relevance": relevance,
            "excluded_reason": excluded_reason,
            "source_confidence": conf,
            "needs_hardware_contract": needs_hw,
            "notes": notes,
        })
    return out


def validate_stats(stats: dict[str, Any]) -> list[str]:
    errors = []
    for key, expected in EXPECTED.items():
        if stats.get(key) != expected:
            errors.append(f"{key}: expected {expected!r}, got {stats.get(key)!r}")
    return errors


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, stats: dict[str, Any], rows: list[dict[str, str]], source_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    module_counts = Counter(r["module_candidate"] for r in rows)
    relevance_counts = Counter(r["minimal_os_relevance"] for r in rows)
    unknown_rows = [r for r in rows if r["module_candidate"] == "unknown"]
    excluded_rows = [r for r in rows if r["minimal_os_relevance"] == "excluded"]

    lines = [
        "# Calibration Source Index",
        "",
        "## Purpose",
        "",
        "Index the `$31` HAC calibration source and classify calibration sections by minimal-OS module relevance.",
        "",
        "This document does not replace the hardware contracts. Hardware contracts define what the minimal OS must drive. This index identifies which calibration data may feed those modules.",
        "",
        "No tuning changes are made by this index.",
        "",
        "## Source",
        "",
        f"`{source_name}`",
        "",
        "## Source Summary",
        "",
        f"- section_count: {stats.get('section_count')}",
        f"- record_count: {stats.get('record_count')}",
        f"- fcb_count: {stats.get('fcb_count')}",
        f"- fdb_count: {stats.get('fdb_count')}",
        f"- min_data_address: {stats.get('min_data_address_hex')}",
        f"- max_data_address: {stats.get('max_data_address_hex')}",
        f"- parse_error_count: {stats.get('parse_error_count')}",
        f"- warning_count: {stats.get('warning_count')}",
        "",
        "## Classification Rules",
        "",
        "Fuel-related sections map to fuel only if they appear to feed VE, airflow, BPW, crank fuel, warmup/afterstart, AE, PE, DFCO, injector correction, or battery/deadtime.",
        "",
        "Spark-related sections map to spark only if they appear to feed spark advance, startup spark, knock/retard, spark latency, or RPM/MAP spark tables.",
        "",
        "IAC/idle sections map to `iac_idle` only if they appear to feed desired idle, crank IAC, park position, IAC step/cadence, or idle correction.",
        "",
        "Transmission, EGR, EVAP, and emissions sections stay excluded unless a hardware contract proves they are required.",
        "",
        "Exclusion rules are applied before spark/fuel rules. This prevents sections such as EGR spark correction from being pulled into the minimal spark module by the word `spark` alone.",
        "",
        "## Output",
        "",
        "`maps/contracts/calibration_source_index.csv`",
        "",
        "## Module Candidate Counts",
        "",
        "| Module candidate | Sections |",
        "|---|---:|",
    ]
    for module, count in sorted(module_counts.items()):
        lines.append(f"| `{module}` | {count} |")
    lines += [
        "",
        "## Minimal-OS Relevance Counts",
        "",
        "| Relevance | Sections |",
        "|---|---:|",
    ]
    for rel, count in sorted(relevance_counts.items()):
        lines.append(f"| `{rel}` | {count} |")
    lines += [
        "",
        "## Excluded Strategy Baggage",
        "",
        "The following sections are intentionally excluded unless a future hardware contract proves otherwise:",
        "",
        "| Section | Range | Module | Title | Reason |",
        "|---:|---|---|---|---|",
    ]
    for r in excluded_rows[:40]:
        lines.append(f"| {r['section_index']} | `{r['start_address']}-{r['end_address']}` | `{r['module_candidate']}` | {r['section_title']} | {r['excluded_reason']} |")
    if len(excluded_rows) > 40:
        lines.append(f"| ... | ... | ... | {len(excluded_rows) - 40} additional excluded sections in CSV | ... |")
    lines += [
        "",
        "## Unknown / Unclassified Sections",
        "",
        "Unknown sections are listed rather than silently guessed:",
        "",
        "| Section | Range | Title | Notes |",
        "|---:|---|---|---|",
    ]
    for r in unknown_rows[:80]:
        lines.append(f"| {r['section_index']} | `{r['start_address']}-{r['end_address']}` | {r['section_title']} | {r['notes']} |")
    if len(unknown_rows) > 80:
        lines.append(f"| ... | ... | {len(unknown_rows) - 80} additional unknown sections in CSV | ... |")
    lines += [
        "",
        "## Required Discipline",
        "",
        "Do not mark a calibration section as `required` merely because it exists in the stock calibration. A section becomes required only when a hardware/source module contract proves that the minimal OS needs it.",
        "",
        "Current index relevance is conservative:",
        "",
        "```text",
        "likely_required = probably needed by future math/module planning, but not final",
        "bench_gated     = module-relevant but physical hardware behavior or units still need proof",
        "calibration_only= useful ID/diagnostic/reference data, not a runtime control requirement yet",
        "excluded        = out-of-scope strategy baggage unless future hardware contract proves otherwise",
        "unknown         = not confidently classified; keep visible for later source tracing",
        "```",
        "",
        "## Next Use",
        "",
        "Use this index when defining fuel, spark, IAC, crank/start, warmup, battery/deadtime, and debug module inputs. Do not use it to bypass hardware-contract requirements.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", default="/mnt/data/31_HAC_calibration_extract_nowrap.html")
    p.add_argument("--out-md", required=True)
    p.add_argument("--out-csv", required=True)
    args = p.parse_args()
    source = resolve(args.source) if not str(args.source).startswith("/mnt/") else Path(args.source)
    obj = load_extract(source)
    errors = validate_stats(obj["stats"])
    if errors:
        raise SystemExit("source summary validation failed:\n" + "\n".join(errors))
    rows = build_rows(obj)
    if len(rows) != EXPECTED["section_count"]:
        raise SystemExit(f"section row count mismatch: {len(rows)}")
    write_csv(resolve(args.out_csv), rows)
    write_md(resolve(args.out_md), obj["stats"], rows, source.name)
    print(f"CALIBRATION_SOURCE_INDEX: wrote {len(rows)} section rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
