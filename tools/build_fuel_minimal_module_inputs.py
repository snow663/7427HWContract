#!/usr/bin/env python3
"""Build the minimal fuel module input-boundary planning artifact.

This is a planning tool, not a fuel-math implementation. It cross-references
the existing calibration source index and hardware contracts to define the
inputs that may feed the future fuel calculation ending in:

    D = EFI pulsewidth counts in 1/65536 second units
    STD $3FCE

No ASM writer or tuning changes are created here.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

FIELDS = ['module', 'submodule', 'input_name', 'input_role', 'source_symbol', 'source_address', 'calibration_section', 'calibration_address_range', 'module_candidate', 'minimal_os_relevance', 'required_for_first_minimal_os', 'hardware_contract_dependency', 'bench_dependency', 'excluded_reason', 'confidence', 'notes']

ROWS = [{'module': 'fuel', 'submodule': 'sensor_acquire', 'input_name': 'RPM', 'input_role': 'sensor', 'source_symbol': 'REF/DRP period / RPM state', 'source_address': 'source-derived', 'calibration_section': 'source trace, no direct calibration section', 'calibration_address_range': '', 'module_candidate': 'unknown', 'minimal_os_relevance': 'unknown', 'required_for_first_minimal_os': 'required', 'hardware_contract_dependency': 'REF_RPM_PERIOD hardware contract', 'bench_dependency': 'RPM source/period validity bench gates', 'excluded_reason': '', 'confidence': 'high_boundary', 'notes': 'Needed for speed-density fuel scheduling, crank/run, AE/DFCO/PE gates.'}, {'module': 'fuel', 'submodule': 'sensor_acquire', 'input_name': 'MAP / load', 'input_role': 'sensor', 'source_symbol': 'MAP ADC/scaled MAP', 'source_address': 'source-derived', 'calibration_section': '91 $4CEA-$4CF2; 115 $4EB7-$4EC1; 136 $5067-$5071', 'calibration_address_range': '$4CEA-$4CF2; $4EB7-$4EC1; $5067-$5071', 'module_candidate': 'sensor_scaling/fuel', 'minimal_os_relevance': 'likely_required', 'required_for_first_minimal_os': 'required', 'hardware_contract_dependency': 'SENSOR_ACQUIRE and fuel VE/load path', 'bench_dependency': 'MAP scaling validation', 'excluded_reason': '', 'confidence': 'medium_index', 'notes': 'Primary speed-density load axis and VE/fuel correction dependency.'}, {'module': 'fuel', 'submodule': 'sensor_acquire', 'input_name': 'TPS / throttle state', 'input_role': 'sensor', 'source_symbol': 'TPS ADC/scaled TPS', 'source_address': 'source-derived', 'calibration_section': '77 $4BEA-$4C03; 81-84 $4C73-$4C96; 97-98 $4D5B-$4D7B', 'calibration_address_range': '$4BEA-$4C03; $4C73-$4C96; $4D5B-$4D7B', 'module_candidate': 'sensor_scaling', 'minimal_os_relevance': 'likely_required', 'required_for_first_minimal_os': 'likely_required', 'hardware_contract_dependency': 'SENSOR_ACQUIRE; AE/PE/DFCO gate paths', 'bench_dependency': 'TPS threshold validation', 'excluded_reason': '', 'confidence': 'medium_index', 'notes': 'Needed for transient and mode gates; can be simpler for first open-loop fuel.'}, {'module': 'fuel', 'submodule': 'sensor_acquire', 'input_name': 'coolant temperature', 'input_role': 'sensor', 'source_symbol': 'CTS/scaled coolant', 'source_address': 'source-derived', 'calibration_section': '21 $452D-$4536; 62-64 $4A36-$4A55; 73-76 $4B97-$4BE9; 102 $4DC2-$4DCC', 'calibration_address_range': 'multiple CTS sections', 'module_candidate': 'crank_start/warmup_afterstart/sensor_scaling', 'minimal_os_relevance': 'likely_required', 'required_for_first_minimal_os': 'required', 'hardware_contract_dependency': 'SENSOR_ACQUIRE; crank/warmup/afterstart contracts', 'bench_dependency': 'CTS scaling validation', 'excluded_reason': '', 'confidence': 'medium_index', 'notes': 'Required for crank fuel, warmup, afterstart, and open-loop correction.'}, {'module': 'fuel', 'submodule': 'sensor_acquire', 'input_name': 'battery voltage', 'input_role': 'sensor', 'source_symbol': 'L00A7 battery volts VDC/10 candidate', 'source_address': '0x00A7', 'calibration_section': '71 $4B75-$4B85; 114 $4EB6-$4EB6', 'calibration_address_range': '$4B75-$4B85; $4EB6', 'module_candidate': 'battery_voltage', 'minimal_os_relevance': 'likely_required', 'required_for_first_minimal_os': 'required', 'hardware_contract_dependency': 'SENSOR_ACQUIRE; injector deadtime/battery correction', 'bench_dependency': 'deadtime unit and voltage scaling', 'excluded_reason': '', 'confidence': 'medium_contract', 'notes': 'Battery voltage is needed for injector offset/deadtime and voltage protection.'}, {'module': 'fuel', 'submodule': 'sensor_acquire', 'input_name': 'baro / altitude basis', 'input_role': 'sensor', 'source_symbol': 'BARO/MAP-derived baro', 'source_address': 'source-derived', 'calibration_section': '25 $4558-$4584; 45 excluded EGR baro; 142 $50FA-$5109; 151 $5151-$5163 excluded trans', 'calibration_address_range': '$4558-$4584; $50FA-$5109', 'module_candidate': 'sensor_scaling', 'minimal_os_relevance': 'likely_required', 'required_for_first_minimal_os': 'likely_required', 'hardware_contract_dependency': 'SENSOR_ACQUIRE; fuel airflow correction', 'bench_dependency': 'baro source/pseudo-baro validation', 'excluded_reason': '', 'confidence': 'medium_index', 'notes': 'Needed for altitude/load correction; use only non-excluded sensor/fuel-relevant sections.'}, {'module': 'fuel', 'submodule': 'mode_gates', 'input_name': 'crank/run state', 'input_role': 'state', 'source_symbol': 'engine running / crank flags', 'source_address': 'source-derived', 'calibration_section': '53 $494A-$494E; 153-155 $5603-$56AF', 'calibration_address_range': '$494A-$494E; $5603-$56AF', 'module_candidate': 'crank_start', 'minimal_os_relevance': 'likely_required', 'required_for_first_minimal_os': 'required', 'hardware_contract_dependency': 'REF_RPM_PERIOD and startup state gates', 'bench_dependency': 'crank/run transition validation', 'excluded_reason': '', 'confidence': 'medium_index', 'notes': 'Separates crank fuel from run fuel and validates pulse enable state.'}, {'module': 'fuel', 'submodule': 'mode_gates', 'input_name': 'closed-loop permission state', 'input_role': 'mode_gate', 'source_symbol': 'closed-loop O2 enable/permission', 'source_address': 'source-derived', 'calibration_section': '52 $4914-$4949; 55 $4975-$4979', 'calibration_address_range': '$4914-$4949; $4975-$4979', 'module_candidate': 'fuel/sensor_scaling', 'minimal_os_relevance': 'likely_required', 'required_for_first_minimal_os': 'optional_initially', 'hardware_contract_dependency': 'O2/sensor contract; fuel trim gate', 'bench_dependency': 'O2 behavior and trim policy', 'excluded_reason': '', 'confidence': 'medium_index', 'notes': 'Optional initially; first runnable module can be open-loop with simple gate.'}, {'module': 'fuel', 'submodule': 'mode_gates', 'input_name': 'DFCO permission / zero fuel gate', 'input_role': 'safety_gate', 'source_symbol': 'DFCO/no-fuel flag and zero gate', 'source_address': 'source-derived', 'calibration_section': '54 $494F-$4974 is trans_excluded in index but comments include decel; use source proof required', 'calibration_address_range': 'source trace required', 'module_candidate': 'fuel/unknown', 'minimal_os_relevance': 'unknown', 'required_for_first_minimal_os': 'required', 'hardware_contract_dependency': 'EFI_PW_3FCE_CONTRACT; no-fuel zero behavior', 'bench_dependency': 'DFCO zero-to-$3FCE bench proof', 'excluded_reason': '', 'confidence': 'medium_boundary', 'notes': 'Must preserve no-fuel behavior; do not pull trans/decel baggage blindly from calibration index.'}, {'module': 'fuel', 'submodule': 'mode_gates', 'input_name': 'PE permission state', 'input_role': 'mode_gate', 'source_symbol': 'PE enable/thresholds', 'source_address': 'source-derived', 'calibration_section': '79 $4C26-$4C52; 80 $4C53-$4C72; 196 $5F30-$5F40', 'calibration_address_range': '$4C26-$4C72; $5F30-$5F40', 'module_candidate': 'fuel', 'minimal_os_relevance': 'likely_required', 'required_for_first_minimal_os': 'optional_initially', 'hardware_contract_dependency': 'FUEL_OUTPUT mode gate', 'bench_dependency': 'PE threshold/refinement validation', 'excluded_reason': '', 'confidence': 'medium_index', 'notes': 'Needed for load enrichment eventually; can be coarse/optional for first safe loop if limits are conservative.'}, {'module': 'fuel', 'submodule': 'transient', 'input_name': 'AE transient state', 'input_role': 'correction', 'source_symbol': 'AE/accel fuel state', 'source_address': 'source-derived', 'calibration_section': '52 $4914-$4949; 58 $49BC-$49D0; 101 $4D92-$4DC1', 'calibration_address_range': '$4914-$4949; $49BC-$49D0; $4D92-$4DC1', 'module_candidate': 'fuel', 'minimal_os_relevance': 'likely_required', 'required_for_first_minimal_os': 'optional_initially', 'hardware_contract_dependency': 'fuel transient source paths', 'bench_dependency': 'AE wall-wetting/fuel-film validation', 'excluded_reason': '', 'confidence': 'low_medium_index', 'notes': 'Refinement item; needed for drivability, but not first static output boundary.'}, {'module': 'fuel', 'submodule': 'base_airflow', 'input_name': 'base VE / airflow table input', 'input_role': 'calibration', 'source_symbol': 'VE/MAP/RPM table and airflow basis', 'source_address': 'source-derived', 'calibration_section': '115 $4EB7-$4EC1; 116 $4EC2-$4EC9; 117 $4ECA-$4F01; 137 $5072-$5079; 138 $507A-$50AC; 145-147 $5130-$5150', 'calibration_address_range': 'VE sections', 'module_candidate': 'fuel', 'minimal_os_relevance': 'likely_required', 'required_for_first_minimal_os': 'required', 'hardware_contract_dependency': 'FUEL_OUTPUT base fuel math', 'bench_dependency': 'VE axis/source validation', 'excluded_reason': '', 'confidence': 'high_index', 'notes': 'Core speed-density base airflow/fuel dependency.'}, {'module': 'fuel', 'submodule': 'injector_model', 'input_name': 'injector flow constant', 'input_role': 'output_scale', 'source_symbol': 'IFR / injector flow scalar', 'source_address': 'calibration/source constant', 'calibration_section': 'not confidently isolated in index; source trace required', 'calibration_address_range': '', 'module_candidate': 'unknown', 'minimal_os_relevance': 'unknown', 'required_for_first_minimal_os': 'required', 'hardware_contract_dependency': 'EFI_PW units and fuel mass to PW conversion', 'bench_dependency': 'actual fuel pressure/injector flow validation', 'excluded_reason': '', 'confidence': 'medium_boundary', 'notes': 'Required for BPW calculation; not safe to infer solely from stock index.'}, {'module': 'fuel', 'submodule': 'injector_model', 'input_name': 'injector deadtime / battery correction', 'input_role': 'correction', 'source_symbol': 'battery offset/deadtime table candidate', 'source_address': 'source-derived', 'calibration_section': '69 $4B5B-$4B63; 70 $4B64-$4B74; 71 $4B75-$4B85; 72 $4B86-$4B96', 'calibration_address_range': '$4B5B-$4B96', 'module_candidate': 'fuel/battery_voltage', 'minimal_os_relevance': 'likely_required', 'required_for_first_minimal_os': 'required', 'hardware_contract_dependency': 'EFI_PW writer input; injector model contract', 'bench_dependency': 'deadtime scale/bench validation', 'excluded_reason': '', 'confidence': 'medium_index', 'notes': 'Required to avoid low-voltage and low-PW error; exact units still need source/bench validation.'}, {'module': 'fuel', 'submodule': 'injector_model', 'input_name': 'low-PW correction / transfer function', 'input_role': 'correction', 'source_symbol': 'new transfer table / low-PW model', 'source_address': 'future minimal OS table', 'calibration_section': 'not stock; future tests/static vectors', 'calibration_address_range': '', 'module_candidate': 'unknown', 'minimal_os_relevance': 'unknown', 'required_for_first_minimal_os': 'required', 'hardware_contract_dependency': 'injector low-PW correction contract / physical floor findings', 'bench_dependency': 'bench validation with $3FCE forced PW', 'excluded_reason': '', 'confidence': 'high_project', 'notes': 'Project-specific required correction due known TBI low-PW nonlinearity/floor.'}, {'module': 'fuel', 'submodule': 'enrichment', 'input_name': 'warmup enrichment', 'input_role': 'correction', 'source_symbol': 'warmup/coolant fuel modifiers', 'source_address': 'source-derived', 'calibration_section': '9 $43AF-$4439; 60 $49E6-$49F5; 62-64 $4A36-$4A55; 68 $4B49-$4B5A', 'calibration_address_range': 'multiple warmup/crank sections', 'module_candidate': 'warmup_afterstart/crank_start/fuel', 'minimal_os_relevance': 'likely_required', 'required_for_first_minimal_os': 'required', 'hardware_contract_dependency': 'crank/warmup source paths', 'bench_dependency': 'coolant scaling and warmup units', 'excluded_reason': '', 'confidence': 'medium_index', 'notes': 'Required for cold/hot open-loop operation.'}, {'module': 'fuel', 'submodule': 'enrichment', 'input_name': 'afterstart enrichment', 'input_role': 'correction', 'source_symbol': 'afterstart/restart fuel state', 'source_address': 'source-derived', 'calibration_section': '60 $49E6-$49F5; 61 $49F6-$4A35; 73-76 $4B97-$4BE9', 'calibration_address_range': 'multiple afterstart sections', 'module_candidate': 'crank_start/fuel', 'minimal_os_relevance': 'likely_required', 'required_for_first_minimal_os': 'likely_required', 'hardware_contract_dependency': 'crank/run transition fuel path', 'bench_dependency': 'afterstart timer/coolant unit validation', 'excluded_reason': '', 'confidence': 'medium_index', 'notes': 'Likely required for stable start/run transition; keep separated from full GM strategy.'}, {'module': 'fuel', 'submodule': 'enrichment', 'input_name': 'crank fuel', 'input_role': 'calibration', 'source_symbol': 'crank fuel tables/scalars', 'source_address': 'source-derived', 'calibration_section': '62 $4A36-$4A45; 63 $4A46-$4A55; 64 $4A56-$4B16; 73 $4B97-$4BA6; 74 $4BA7-$4BB6', 'calibration_address_range': 'crank fuel sections', 'module_candidate': 'crank_start', 'minimal_os_relevance': 'likely_required', 'required_for_first_minimal_os': 'required', 'hardware_contract_dependency': 'crank/run fuel state and $3FCE output', 'bench_dependency': 'crank pulse bench/log validation', 'excluded_reason': '', 'confidence': 'medium_index', 'notes': 'Required before runnable start sequence.'}, {'module': 'fuel', 'submodule': 'commanded_mixture', 'input_name': 'target AFR / stoich basis', 'input_role': 'calibration', 'source_symbol': 'target AFR / commanded equivalence', 'source_address': 'source-derived', 'calibration_section': '5 $4088-$408E; 52 $4914-$4949; 66 $4B20-$4B2F; 67 $4B30-$4B48; 86-87 $4C9D-$4CBE; 92 $4CF3-$4D03', 'calibration_address_range': 'AFR sections', 'module_candidate': 'fuel', 'minimal_os_relevance': 'likely_required', 'required_for_first_minimal_os': 'required', 'hardware_contract_dependency': 'fuel mass/BPW calculation', 'bench_dependency': 'fuel stoich and commanded AFR policy', 'excluded_reason': '', 'confidence': 'high_index', 'notes': 'Required for final commanded fuel mass; keep stoich configurable.'}, {'module': 'fuel', 'submodule': 'safety', 'input_name': 'fuel enable / no-fuel gate', 'input_role': 'safety_gate', 'source_symbol': 'fuel enable/no-fuel flag', 'source_address': 'source-derived', 'calibration_section': 'source trace required; not calibration-only', 'calibration_address_range': '', 'module_candidate': 'unknown', 'minimal_os_relevance': 'unknown', 'required_for_first_minimal_os': 'required', 'hardware_contract_dependency': 'EFI_PW_3FCE_CONTRACT; DFCO/no-fuel behavior', 'bench_dependency': 'zero command behavior at $3FCE', 'excluded_reason': '', 'confidence': 'high_boundary', 'notes': 'Safety gate must be explicit even if simple.'}, {'module': 'fuel', 'submodule': 'output_scale', 'input_name': 'EFI PW unit conversion', 'input_role': 'output_scale', 'source_symbol': 'PW counts = seconds * 65536', 'source_address': '$3FCE/$3FCF', 'calibration_section': 'EFI_PW_UNITS; no calibration section', 'calibration_address_range': '', 'module_candidate': 'unknown', 'minimal_os_relevance': 'unknown', 'required_for_first_minimal_os': 'required', 'hardware_contract_dependency': 'EFI_PW_UNITS; MINIMAL_EFI_PW_WRITER', 'bench_dependency': '$3FCE unit confirmation', 'excluded_reason': '', 'confidence': 'high_contract', 'notes': 'Final output unit for D before STD $3FCE.'}, {'module': 'fuel', 'submodule': 'excluded', 'input_name': 'TCC / transmission tables', 'input_role': 'excluded', 'source_symbol': 'stock trans strategy', 'source_address': 'calibration index', 'calibration_section': 'trans_excluded sections, 49 total', 'calibration_address_range': 'multiple', 'module_candidate': 'trans_excluded', 'minimal_os_relevance': 'excluded', 'required_for_first_minimal_os': 'excluded', 'hardware_contract_dependency': 'TRANSMISSION_EMISSIONS_EXCLUDED', 'bench_dependency': 'none', 'excluded_reason': 'transmission strategy excluded unless hardware-required', 'confidence': 'high_index', 'notes': 'Do not feed fuel input boundary.'}, {'module': 'fuel', 'submodule': 'excluded', 'input_name': 'EGR correction tables', 'input_role': 'excluded', 'source_symbol': 'stock EGR/emissions strategy', 'source_address': 'calibration index', 'calibration_section': 'egr_excluded sections, 17 total', 'calibration_address_range': 'multiple', 'module_candidate': 'egr_excluded', 'minimal_os_relevance': 'excluded', 'required_for_first_minimal_os': 'excluded', 'hardware_contract_dependency': 'TRANSMISSION_EMISSIONS_EXCLUDED', 'bench_dependency': 'none', 'excluded_reason': 'EGR/emissions strategy excluded', 'confidence': 'high_index', 'notes': 'Includes EGR spark/fuel correction; exclusion wins over spark/fuel keywords.'}, {'module': 'fuel', 'submodule': 'excluded', 'input_name': 'EVAP / purge tables', 'input_role': 'excluded', 'source_symbol': 'stock EVAP strategy', 'source_address': 'calibration index', 'calibration_section': 'evap_excluded sections, 4 total', 'calibration_address_range': 'multiple', 'module_candidate': 'evap_excluded', 'minimal_os_relevance': 'excluded', 'required_for_first_minimal_os': 'excluded', 'hardware_contract_dependency': 'TRANSMISSION_EMISSIONS_EXCLUDED', 'bench_dependency': 'none', 'excluded_reason': 'EVAP/purge strategy excluded', 'confidence': 'high_index', 'notes': 'Do not feed fuel input boundary unless future hardware contract requires purge.'}, {'module': 'fuel', 'submodule': 'unresolved', 'input_name': 'unknown fuel-adjacent sections', 'input_role': 'unknown', 'source_symbol': 'unclassified calibration rows', 'source_address': 'calibration index', 'calibration_section': 'unknown sections, 24 total', 'calibration_address_range': 'multiple', 'module_candidate': 'unknown', 'minimal_os_relevance': 'unknown', 'required_for_first_minimal_os': 'unknown', 'hardware_contract_dependency': 'future source trace only', 'bench_dependency': 'unknown', 'excluded_reason': '', 'confidence': 'low_index', 'notes': 'Keep visible for later tracing; do not guess or promote.'}]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root() / p


def validate_cal_index(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"calibration index not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 226:
        raise SystemExit(f"expected 226 calibration sections, got {len(rows)}")
    if any(r.get("minimal_os_relevance") == "required" for r in rows):
        raise SystemExit("calibration source index must not mark sections required by itself")


def write_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(ROWS)


def write_md(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    excluded = [r for r in ROWS if r["required_for_first_minimal_os"] == "excluded"]
    unknown = [r for r in ROWS if r["required_for_first_minimal_os"] == "unknown"]
    lines = [
        "# Fuel Minimal Module Inputs",
        "",
        "## Purpose",
        "",
        "Define the input boundary for a minimal speed-density TBI fuel module that ultimately commands EFI pulsewidth through `$3FCE`.",
        "",
        "This document does not implement fuel math and does not tune calibration values.",
        "",
        "## Output Contract",
        "",
        "Owned by:",
        "",
        "- `EFI_PW_3FCE_CONTRACT.md`",
        "- `EFI_PW_UNITS.md`",
        "- `MINIMAL_EFI_PW_WRITER.md`",
        "",
        "Output:",
        "",
        "```text",
        "D = EFI pulsewidth counts in 1/65536 second units",
        "STD $3FCE",
        "```",
        "",
        "## Required Input Classes",
        "",
        "| Input class | Required? | Source type | Calibration dependency | Notes |",
        "|---|---:|---|---|---|",
    ]
    for r in ROWS:
        if r["required_for_first_minimal_os"] in {"required", "likely_required", "optional_initially", "bench_gated"}:
            lines.append(
                f"| {r['input_name']} | `{r['required_for_first_minimal_os']}` | "
                f"{r['input_role']} / {r['source_symbol']} | {r['calibration_section']} | {r['notes']} |"
            )
    lines += [
        "",
        "## Minimal Fuel Pipeline",
        "",
        "```text",
        "sensor acquire",
        "→ operating mode gates",
        "→ base airflow / VE",
        "→ commanded fuel mass / BPW",
        "→ warmup / afterstart / crank modifiers",
        "→ AE / PE / DFCO gates",
        "→ injector model correction",
        "→ low-PW transfer correction",
        "→ EFI PW counts",
        "→ $3FCE writer",
        "```",
        "",
        "## Explicitly Excluded",
        "",
        "- transmission torque management unless spark/fuel hardware contract proves required",
        "- EGR fuel/spark corrections",
        "- EVAP purge fuel trims",
        "- emissions-only diagnostics",
        "- closed-loop trim complexity beyond a simple optional correction gate",
        "",
        "## Excluded Fuel-Adjacent Baggage",
        "",
        "| Input | Module candidate | Relevance | Reason |",
        "|---|---|---|---|",
    ]
    for r in excluded:
        lines.append(f"| {r['input_name']} | `{r['module_candidate']}` | `{r['required_for_first_minimal_os']}` | {r['excluded_reason']} |")
    lines += [
        "",
        "## Unknown / Unresolved Fuel Inputs",
        "",
        "| Input | Status | Notes |",
        "|---|---|---|",
    ]
    for r in unknown:
        lines.append(f"| {r['input_name']} | `{r['required_for_first_minimal_os']}` | {r['notes']} |")
    lines += [
        "",
        "## Bench / Source Gates",
        "",
        "- `$3FCE` unit confirmation",
        "- injector low-PW transfer validation",
        "- DFCO zero-gate behavior",
        "- battery/deadtime behavior",
        "- crank/warmup enrichment source mapping",
        "- fuel enable/no-fuel safety behavior",
        "- injector flow/fuel pressure basis",
        "",
        "## Discipline",
        "",
        "Calibration sections are not marked `required` merely because they exist. The input becomes required only when a hardware/source contract or first minimal runnable fuel path needs it.",
        "",
        "Transmission, EGR, EVAP, and emissions sections remain excluded unless a later hardware contract proves they are hardware-required.",
        "",
        "## Machine-Readable Output",
        "",
        "`maps/contracts/fuel_minimal_module_inputs.csv`",
        "",
        "## Next Module Input Boundary",
        "",
        "After fuel, do:",
        "",
        "```text",
        "SPARK_MINIMAL_MODULE_INPUTS",
        "IAC_MINIMAL_MODULE_INPUTS",
        "```",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cal-index", default="maps/contracts/calibration_source_index.csv")
    p.add_argument("--out-md", required=True)
    p.add_argument("--out-csv", required=True)
    args = p.parse_args()

    validate_cal_index(resolve(args.cal_index))
    write_csv(resolve(args.out_csv))
    write_md(resolve(args.out_md))
    print(f"FUEL_MINIMAL_MODULE_INPUTS: wrote {len(ROWS)} input-boundary rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
