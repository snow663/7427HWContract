"""Evidence-scoped PCM/mask profiles for ROMFlow Studio.

A profile constrains *plausible execution* and annotates hardware layout.
It never turns source-only addresses into ROM-byte verification.
"""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / "profiles"
PROFILE_IDS = (
    "generic",
    "gm_7427_31",
    "gm_7427_0e",
    "gm_7427_bhdc",
    "gm_7060_85",
    "gm_7060_d8_bamw",
)


def get_profile(profile_id):
    if profile_id == "generic":
        return {
            "id": "generic",
            "name": "Generic 68HC11 (no mask assumptions)",
            "zones": [],
            "table_hints": [],
            "execution_regions": [],
            "warning": "No executable regions are assumed, so false data-as-code paths are possible.",
        }
    if profile_id not in PROFILE_IDS:
        raise ValueError("Unrecognized hardware/mask profile: " + str(profile_id))
    return json.loads((HERE / (profile_id + ".json")).read_text(encoding="utf-8"))


def exec_ranges(profile_id):
    """Inclusive CPU ranges. None = generic unlimited, not zero executable bytes."""
    regions = get_profile(profile_id).get("execution_regions", [])
    if not regions:
        return None
    return [tuple(int(x, 16) for x in pair) for pair in regions]


def match_rom_sha(sha):
    """Only a full-ROM SHA match constitutes positive image identification."""
    for profile_id in PROFILE_IDS:
        if profile_id == "generic":
            continue
        p = get_profile(profile_id)
        if p.get("rom_sha256") == sha:
            return profile_id
    return None
