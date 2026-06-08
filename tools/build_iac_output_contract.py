#!/usr/bin/env python3
"""Build the IAC Enable/A/B output contract.

This pass is a source-proof pass around the hypothesis that the IAC driver has
Enable, A, and B command bits and that A/B form a two-bit four-state ring.
It does not create an IAC writer.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

FIELDS = [
    "stage", "pc", "mnemonic", "operands", "symbol", "address", "read_or_write",
    "bitmask", "bit_position", "value_source", "routine_label", "iac_context",
    "candidate_role", "desired_actual_compare", "direction_candidate", "ab_state_before",
    "ab_state_after", "actual_count_delta", "enable_candidate", "atomic_update_candidate",
    "required_for_minimal_os", "confidence", "notes",
]

ROWS = [
    {"stage":"load_mode_word","pc":"0x91A3","mnemonic":"LDAB","operands":"L000A","symbol":"L000A","address":"0x000A","read_or_write":"read","bitmask":"","bit_position":"","value_source":"IAC mode/output state byte","routine_label":"L91A3","iac_context":"IAC step/update routine entry","candidate_role":"iac_ab_state","desired_actual_compare":"not_compare","direction_candidate":"uses bit0 later","ab_state_before":"bits2/3 from L000A","ab_state_after":"pending","actual_count_delta":"none","enable_candidate":"bit4 preserved/cleared/set later","atomic_update_candidate":"RAM mode byte source","required_for_minimal_os":"yes","confidence":"high_static","notes":"L000A carries direction bit0 and A/B/Enable bits used later"},
    {"stage":"driver_voltage_high_gate","pc":"0x91A7-0x91AD","mnemonic":"CMPA/ANDB","operands":"#169 / #$EF","symbol":"L000A bit4","address":"0x000A","read_or_write":"clear_candidate","bitmask":"0x10","bit_position":"4","value_source":"battery voltage test","routine_label":"L91A3","iac_context":"IAC driver enable voltage gate","candidate_role":"iac_driver_enable_voltage_gate","desired_actual_compare":"not_compare","direction_candidate":"none","ab_state_before":"unchanged","ab_state_after":"unchanged","actual_count_delta":"none","enable_candidate":"clear bit4 if voltage gate fails/high","atomic_update_candidate":"mode byte updated before shadow latch","required_for_minimal_os":"yes","confidence":"medium_high_static","notes":"battery > 16.9 V path clears bit4 via ANDB #$EF"},
    {"stage":"driver_enable_set_good_voltage","pc":"0x91BD-0x91C0","mnemonic":"BCLR/ORAB","operands":"L003E,#$04 / #$10","symbol":"L000A bit4","address":"0x000A","read_or_write":"set_candidate","bitmask":"0x10","bit_position":"4","value_source":"good voltage/ignition gate","routine_label":"L91A3","iac_context":"IAC driver enable good path","candidate_role":"iac_enable_bit","desired_actual_compare":"not_compare","direction_candidate":"none","ab_state_before":"unchanged","ab_state_after":"unchanged","actual_count_delta":"none","enable_candidate":"set bit4","atomic_update_candidate":"mode byte updated before shadow latch","required_for_minimal_os":"yes","confidence":"medium_high_static","notes":"ORAB #$10 marks bit4 as Enable candidate after voltage gate passes"},
    {"stage":"load_actual_position","pc":"0x91C2","mnemonic":"LDAA","operands":"L0007","symbol":"L0007","address":"0x0007","read_or_write":"read","bitmask":"","bit_position":"","value_source":"present motor position","routine_label":"L91A3","iac_context":"position/error logic","candidate_role":"iac_actual_position","desired_actual_compare":"actual loaded into A","direction_candidate":"not_yet","ab_state_before":"unchanged","ab_state_after":"unchanged","actual_count_delta":"none","enable_candidate":"unchanged","atomic_update_candidate":"not_output","required_for_minimal_os":"yes","confidence":"high_static","notes":"source comment: IAC MOTOR POSIT"},
    {"stage":"compare_actual_to_desired","pc":"0x91C4","mnemonic":"CMPA","operands":"L0008","symbol":"L0008","address":"0x0008","read_or_write":"read_compare","bitmask":"","bit_position":"","value_source":"desired/target IAC position","routine_label":"L91A3","iac_context":"desired-actual compare","candidate_role":"iac_desired_position","desired_actual_compare":"A=L0007 actual compared to L0008 desired","direction_candidate":"carry/BCC decides sign","ab_state_before":"unchanged","ab_state_after":"unchanged","actual_count_delta":"none","enable_candidate":"unchanged","atomic_update_candidate":"not_output","required_for_minimal_os":"yes","confidence":"high_static","notes":"desired variable is L0008 because actual L0007 is compared against it"},
    {"stage":"no_step_equal","pc":"0x91C6-0x91CA","mnemonic":"BNE/ANDB/BRA","operands":"L91CC / #$FE / L9200","symbol":"L000A bit0","address":"0x000A","read_or_write":"clear_candidate","bitmask":"0x01","bit_position":"0","value_source":"actual == desired","routine_label":"L91A3","iac_context":"no-step path","candidate_role":"iac_no_step","desired_actual_compare":"actual == desired","direction_candidate":"no step; direction bit cleared candidate","ab_state_before":"held","ab_state_after":"held","actual_count_delta":"0","enable_candidate":"unchanged","atomic_update_candidate":"shadow latch still refreshed","required_for_minimal_os":"yes","confidence":"high_static","notes":"if L0007 == L0008, branch not taken and no actual count INC/DEC occurs"},
    {"stage":"reset_in_work_gate","pc":"0x91CC-0x91D0","mnemonic":"BRCLR/BRSET","operands":"L0009,#$01 / L0002,#$03","symbol":"L0009 bit0; L0002","address":"0x0009;0x0002","read_or_write":"read_bit","bitmask":"0x01;0x03","bit_position":"0;0-1","value_source":"IAC reset in work; major loop counter","routine_label":"L91A3","iac_context":"step cadence/reset gate","candidate_role":"iac_step_cadence","desired_actual_compare":"only when actual != desired","direction_candidate":"may skip update during reset/cadence gate","ab_state_before":"held if gated","ab_state_after":"held if gated","actual_count_delta":"0 if gated","enable_candidate":"unchanged","atomic_update_candidate":"not_output","required_for_minimal_os":"yes","confidence":"medium_high_static","notes":"reset-in-work path can gate stepping through major loop counter"},
    {"stage":"actual_less_than_desired_direction","pc":"0x91D4-0x91DD","mnemonic":"BCC/ANDB/BRSET/INCA","operands":"L91DF / #$FE / L000A,#$01 / INCA","symbol":"L000A bit0; L0007","address":"0x000A;0x0007","read_or_write":"direction_clear_then_increment","bitmask":"0x01","bit_position":"0","value_source":"CMP carry set: actual < desired","routine_label":"L91A3","iac_context":"step direction path A","candidate_role":"iac_step_open_candidate","desired_actual_compare":"actual < desired","direction_candidate":"bit0 clear direction; previous bit0 clear allows count update","ab_state_before":"L000A bits2/3","ab_state_after":"ring advances using XOR bit2/bit3","actual_count_delta":"+1 when direction already matched","enable_candidate":"unchanged","atomic_update_candidate":"shadow latch update after ring change","required_for_minimal_os":"yes","confidence":"high_static","notes":"direction changes can occur without count update; count increments only after prior direction already matched"},
    {"stage":"actual_greater_than_desired_direction","pc":"0x91DF-0x91E6","mnemonic":"ORAB/BRCLR/DECA/STAA","operands":"#$01 / L000A,#$01 / DECA / L0007","symbol":"L000A bit0; L0007","address":"0x000A;0x0007","read_or_write":"direction_set_then_decrement","bitmask":"0x01","bit_position":"0","value_source":"BCC path: actual >= desired and not equal","routine_label":"L91A3","iac_context":"step direction path B","candidate_role":"iac_step_close_candidate","desired_actual_compare":"actual > desired","direction_candidate":"bit0 set direction; previous bit0 set allows count update","ab_state_before":"L000A bits2/3","ab_state_after":"ring reverses using XOR bit2/bit3","actual_count_delta":"-1 when direction already matched","enable_candidate":"unchanged","atomic_update_candidate":"shadow latch update after ring change","required_for_minimal_os":"yes","confidence":"high_static","notes":"count decrements only after prior direction already matched"},
    {"stage":"actual_position_store","pc":"0x91E6","mnemonic":"STAA","operands":"L0007","symbol":"L0007","address":"0x0007","read_or_write":"write","bitmask":"","bit_position":"","value_source":"A after INCA/DECA","routine_label":"L91A3","iac_context":"actual position update","candidate_role":"iac_actual_position","desired_actual_compare":"after step decision","direction_candidate":"from bit0 path","ab_state_before":"unchanged","ab_state_after":"pending ring update","actual_count_delta":"+1 or -1","enable_candidate":"unchanged","atomic_update_candidate":"not_output","required_for_minimal_os":"yes","confidence":"high_static","notes":"software present count is updated before A/B ring toggle"},
    {"stage":"ab_state_equal_test","pc":"0x91E8-0x91EC","mnemonic":"BRSET/BRCLR","operands":"L000A,#$0C","symbol":"L000A bits2-3","address":"0x000A","read_or_write":"read_bitpair","bitmask":"0x0C","bit_position":"2-3","value_source":"current A/B state","routine_label":"L91A3","iac_context":"A/B ring branch","candidate_role":"iac_ab_state","desired_actual_compare":"after step decision","direction_candidate":"uses bit0 to choose toggle bit","ab_state_before":"00 or 11 branch to L91F6; 01 or 10 fall through","ab_state_after":"pending XOR","actual_count_delta":"already updated","enable_candidate":"unchanged","atomic_update_candidate":"RAM mode byte ring update","required_for_minimal_os":"yes","confidence":"high_static","notes":"source comments identify b2/b3 as COIL A & B STATE ON"},
    {"stage":"ab_toggle_bit2","pc":"0x91FA","mnemonic":"EORB","operands":"#$04","symbol":"L000A bit2","address":"0x000A","read_or_write":"xor_bit","bitmask":"0x04","bit_position":"2","value_source":"ring decision","routine_label":"L91A3","iac_context":"A/B ring update","candidate_role":"iac_a_bit","desired_actual_compare":"step required","direction_candidate":"depends on bit0 and current A/B equality","ab_state_before":"varies","ab_state_after":"toggle bit2","actual_count_delta":"already updated","enable_candidate":"unchanged","atomic_update_candidate":"bit toggled in B before single mode-byte store","required_for_minimal_os":"yes","confidence":"high_static","notes":"if bit2=A, this is the A coil state toggle"},
    {"stage":"ab_toggle_bit3","pc":"0x91FE","mnemonic":"EORB","operands":"#$08","symbol":"L000A bit3","address":"0x000A","read_or_write":"xor_bit","bitmask":"0x08","bit_position":"3","value_source":"ring decision","routine_label":"L91A3","iac_context":"A/B ring update","candidate_role":"iac_b_bit","desired_actual_compare":"step required","direction_candidate":"depends on bit0 and current A/B equality","ab_state_before":"varies","ab_state_after":"toggle bit3","actual_count_delta":"already updated","enable_candidate":"unchanged","atomic_update_candidate":"bit toggled in B before single mode-byte store","required_for_minimal_os":"yes","confidence":"high_static","notes":"if bit3=B, this is the B coil state toggle"},
    {"stage":"store_iac_mode_word","pc":"0x9200","mnemonic":"STAB","operands":"L000A","symbol":"L000A","address":"0x000A","read_or_write":"write","bitmask":"0x1D","bit_position":"0,2,3,4","value_source":"B after direction/enable/A/B updates","routine_label":"L91A3","iac_context":"mode state commit","candidate_role":"iac_ab_state","desired_actual_compare":"post compare","direction_candidate":"bit0 stored","ab_state_before":"old L000A","ab_state_after":"new L000A","actual_count_delta":"0/+1/-1","enable_candidate":"bit4 stored","atomic_update_candidate":"single RAM mode-byte store","required_for_minimal_os":"yes","confidence":"high_static","notes":"direction, A/B and enable candidate state are committed together to L000A"},
    {"stage":"shadow_latch_mask_clear","pc":"0x9203-0x9207","mnemonic":"LDAA/ANDA/ANDB","operands":"L004C / #$E3 / #$1C","symbol":"L004C; L000A bits2-4","address":"0x004C;0x000A","read_or_write":"read_mask","bitmask":"0x1C","bit_position":"2-4","value_source":"L004C shadow and L000A A/B/Enable bits","routine_label":"L91A3","iac_context":"A/B/Enable output shadow update","candidate_role":"iac_full_latch_write","desired_actual_compare":"post compare","direction_candidate":"not output directly","ab_state_before":"L000A bits2-3","ab_state_after":"L004C bits2-3","actual_count_delta":"already done","enable_candidate":"L000A bit4 -> L004C bit4","atomic_update_candidate":"SEI-protected full shadow-field replacement","required_for_minimal_os":"yes","confidence":"high_static","notes":"ANDA #$E3 clears L004C bits2/3/4; ANDB #$1C extracts new Enable/A/B bits"},
    {"stage":"shadow_latch_commit","pc":"0x9209-0x920A","mnemonic":"ABA/STAA","operands":"L004C","symbol":"L004C bits2-4","address":"0x004C","read_or_write":"write","bitmask":"0x1C","bit_position":"2-4","value_source":"old L004C with L000A bits2-4 inserted","routine_label":"L91A3","iac_context":"A/B/Enable output shadow commit","candidate_role":"iac_full_latch_write","desired_actual_compare":"post compare","direction_candidate":"not output directly","ab_state_before":"old L004C bits2-3","ab_state_after":"new L004C bits2-3","actual_count_delta":"already done","enable_candidate":"new L004C bit4","atomic_update_candidate":"full shadow-field write under SEI/CLI","required_for_minimal_os":"yes","confidence":"high_static","notes":"A/B/Enable are not BSET/BCLR to hardware here; they are packed into a shadow byte"},
    {"stage":"hardware_latch_write","pc":"0xF40F-0xF411","mnemonic":"LDAA/STAA","operands":"L004C / L3062","symbol":"L3062","address":"0x3062","read_or_write":"write","bitmask":"0x1C candidate","bit_position":"2-4 candidate","value_source":"L004C output shadow","routine_label":"LF400","iac_context":"board output latch service","candidate_role":"iac_full_latch_write","desired_actual_compare":"not compare","direction_candidate":"not output directly","ab_state_before":"L004C bits2-3","ab_state_after":"hardware port/latch bits2-3 candidate","actual_count_delta":"not updated here","enable_candidate":"L004C bit4 to hardware candidate","atomic_update_candidate":"full byte hardware latch write","required_for_minimal_os":"yes","confidence":"high_static_for_latch_write_medium_for_bit_roles","notes":"source writes L004C to L3062 I/O PORT D; bench must confirm physical pins are Enable/A/B"},
    {"stage":"startup_park_position_load","pc":"0x926A-0x926D","mnemonic":"LDAA/STAA","operands":"L4EB0 / L0007","symbol":"L0007","address":"0x0007","read_or_write":"write","bitmask":"","bit_position":"","value_source":"L4EB0 145 steps park down","routine_label":"L925E","iac_context":"startup/setup park seed","candidate_role":"iac_actual_position","desired_actual_compare":"startup seed","direction_candidate":"none","ab_state_before":"unchanged","ab_state_after":"unchanged","actual_count_delta":"seed","enable_candidate":"unchanged","atomic_update_candidate":"not output","required_for_minimal_os":"yes","confidence":"high_static","notes":"startup setup seeds present position from park-down calibration"},
    {"stage":"desired_position_seed","pc":"0x929C-0x929E","mnemonic":"LDAA/STAA","operands":"L0007 / L0008","symbol":"L0008","address":"0x0008","read_or_write":"write","bitmask":"","bit_position":"","value_source":"L0007 present position","routine_label":"L925E","iac_context":"startup/setup desired seed","candidate_role":"iac_desired_position","desired_actual_compare":"desired = actual seed","direction_candidate":"no initial step","ab_state_before":"unchanged","ab_state_after":"unchanged","actual_count_delta":"0","enable_candidate":"unchanged","atomic_update_candidate":"not output","required_for_minimal_os":"yes","confidence":"high_static","notes":"target/desired L0008 is seeded from present L0007"},
    {"stage":"reset_in_work_set_and_zero","pc":"0xA3FA-0xA404","mnemonic":"BSET/STAA/STAA","operands":"L0009,#$01 / L0008 / L0007","symbol":"L0009 bit0; L0008; L0007","address":"0x0009;0x0008;0x0007","read_or_write":"write","bitmask":"0x01","bit_position":"0","value_source":"IAC reset threshold path","routine_label":"LA3FA","iac_context":"IAC reset/home behavior","candidate_role":"iac_driver_disable_fault","desired_actual_compare":"reset seed actual=desired=0","direction_candidate":"none","ab_state_before":"unchanged","ab_state_after":"unchanged","actual_count_delta":"seed zero","enable_candidate":"not directly changed here","atomic_update_candidate":"not output","required_for_minimal_os":"yes","confidence":"high_static","notes":"sets IAC MOTOR Reset IN WORK and zeros desired/present positions"},
    {"stage":"strategy_actual_decrement","pc":"0x9B10","mnemonic":"DEC","operands":"L0007","symbol":"L0007","address":"0x0007","read_or_write":"rmw","bitmask":"","bit_position":"","value_source":"idle strategy limit path","routine_label":"L99C5","iac_context":"strategy-level position correction","candidate_role":"iac_actual_decrement","desired_actual_compare":"not direct compare in this row","direction_candidate":"close/open naming bench-gated","ab_state_before":"not touched","ab_state_after":"not touched","actual_count_delta":"-1","enable_candidate":"not touched","atomic_update_candidate":"not output","required_for_minimal_os":"strategy_dependency_only","confidence":"high_static","notes":"additional L0007 decrement outside L91A3 shows strategy can adjust present/commanded position model"},
    {"stage":"strategy_actual_increment","pc":"0x9BD6","mnemonic":"INC","operands":"L0007","symbol":"L0007","address":"0x0007","read_or_write":"rmw","bitmask":"","bit_position":"","value_source":"idle strategy limit path","routine_label":"L99C5","iac_context":"strategy-level position correction","candidate_role":"iac_actual_increment","desired_actual_compare":"not direct compare in this row","direction_candidate":"close/open naming bench-gated","ab_state_before":"not touched","ab_state_after":"not touched","actual_count_delta":"+1","enable_candidate":"not touched","atomic_update_candidate":"not output","required_for_minimal_os":"strategy_dependency_only","confidence":"high_static","notes":"additional L0007 increment outside L91A3 shows strategy can adjust present/commanded position model"},
    {"stage":"not_primary_3ffc_candidate","pc":"0x713A/0x714A/0xFA43","mnemonic":"STX/STD","operands":"L3FFC","symbol":"L3FFC","address":"0x3FFC","read_or_write":"write","bitmask":"","bit_position":"","value_source":"init/diagnostic I/O D port writes","routine_label":"L7100/LFA28","iac_context":"hardware suspect rejected for primary IAC path","candidate_role":"unknown_iac_state","desired_actual_compare":"none","direction_candidate":"none","ab_state_before":"not from L000A","ab_state_after":"not proved IAC","actual_count_delta":"none","enable_candidate":"not proved","atomic_update_candidate":"not primary IAC update","required_for_minimal_os":"no_unless_later_dependency_proves","confidence":"medium_static","notes":"3FFC is an ASIC I/O D port candidate, but source-proven IAC A/B/Enable path in this pass is L000A -> L004C -> L3062"},
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root() / p


def write_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(ROWS)


def write_md(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# IAC Idle Air Output Contract",
        "",
        "## Purpose",
        "",
        "Map the IAC Enable/A/B output contract from source. This is a source-proof pass for desired/actual position, A/B ring stepping, driver enable gating, output latch path, and step cadence gates.",
        "",
        "No IAC writer is created by this contract.",
        "",
        "## Working Hypothesis",
        "",
        "The IAC driver has three CPU-side command inputs:",
        "",
        "```text",
        "Enable",
        "A",
        "B",
        "```",
        "",
        "Enable is likely a driver-enable/health gate. It is expected to assert after startup voltage/driver conditions are acceptable and remain asserted during normal operation. It may deassert for fault, reset, test, or driver-protection behavior.",
        "",
        "A and B form a 2-bit step-state command. Direction is probably determined by choosing the next neighbor in a four-state ring, not by a dedicated direction signal.",
        "",
        "Candidate stable states:",
        "",
        "```text",
        "00 = none",
        "10 = A",
        "11 = A+B",
        "01 = B",
        "```",
        "",
        "Candidate sequence one direction:",
        "",
        "```text",
        "A -> A+B -> B -> none -> A",
        "```",
        "",
        "Candidate sequence opposite direction:",
        "",
        "```text",
        "A -> none -> B -> A+B -> A",
        "```",
        "",
        "The source must prove or disprove this.",
        "",
        "## Source-Proven Core Result",
        "",
        "```text",
        "actual/present position = L0007",
        "desired/target position = L0008",
        "mode/output state byte  = L000A",
        "direction bit           = L000A bit0",
        "A/B ring bits           = L000A bits2/3",
        "Enable candidate        = L000A bit4",
        "output shadow           = L004C bits2/3/4",
        "hardware latch write    = L004C -> L3062",
        "```",
        "",
        "The current source pass does not prove `$3FFC` as the primary IAC A/B/Enable output path. `$3FFC` remains an I/O-D-port suspect for other init/diagnostic paths, while the source-proven IAC path is `L000A -> L004C -> L3062`.",
        "",
        "## Position/Error Logic",
        "",
        "| PC | Instruction | Role | Static meaning | Confidence |",
        "|---|---|---|---|---|",
        "| `0x91C2` | `LDAA L0007` | actual position | load present IAC motor position | high |",
        "| `0x91C4` | `CMPA L0008` | desired compare | compare actual against desired/target | high |",
        "| `0x91C6` | `BNE L91CC` | no-step gate | equal means no step/count update | high |",
        "| `0x91D4` | `BCC L91DF` | direction branch | actual >= desired path | high |",
        "| `0x91D6/0x91DC` | `ANDB #$FE` / `INCA` | direction 0 path | actual < desired, increment actual after direction matched | high |",
        "| `0x91DF/0x91E5` | `ORAB #$01` / `DECA` | direction 1 path | actual > desired, decrement actual after direction matched | high |",
        "| `0x91E6` | `STAA L0007` | actual update | commit +1/-1 software position update | high |",
        "",
        "Important behavior: when direction changes, the code can update the direction bit without immediately changing the actual count. This looks like a safe phase/direction reversal behavior.",
        "",
        "## A/B Ring Logic",
        "",
        "A/B source bits:",
        "",
        "```text",
        "L000A bit2 = A candidate",
        "L000A bit3 = B candidate",
        "```",
        "",
        "Ring operation:",
        "",
        "```text",
        "0x91E8  BRSET L000A,#$0C,L91F6   ; both A+B set",
        "0x91EC  BRCLR L000A,#$0C,L91F6   ; neither A nor B set",
        "0x91F0  BITB #$01                ; direction bit",
        "0x91FA  EORB #$04                ; toggle bit2/A candidate",
        "0x91FE  EORB #$08                ; toggle bit3/B candidate",
        "```",
        "",
        "If bit2=A and bit3=B, static ring candidates are:",
        "",
        "```text",
        "direction bit0 = 0:",
        "  none -> A -> A+B -> B -> none",
        "",
        "direction bit0 = 1:",
        "  none -> B -> A+B -> A -> none",
        "```",
        "",
        "This proves the A/B ring shape statically. Bench still must confirm which physical pin is A and which is B, and whether count-positive corresponds to open or closed airflow.",
        "",
        "## Enable Gate",
        "",
        "Enable candidate:",
        "",
        "```text",
        "L000A bit4 -> L004C bit4 -> L3062 bit4 candidate",
        "```",
        "",
        "Static evidence:",
        "",
        "```text",
        "0x91A7  CMPA #169     ; 16.9 V battery gate",
        "0x91AB  ANDB #$EF     ; clear bit4 candidate on failed/high voltage path",
        "0x91C0  ORAB #$10     ; set bit4 candidate on good path",
        "```",
        "",
        "Current classification: Enable is a driver-enable/health/voltage gate candidate, not a per-step pulse. Bench must confirm whether it stays asserted while A/B phase changes.",
        "",
        "## A/B Update Atomicity",
        "",
        "AB and BA are the same stable state electrically, but transition path can matter.",
        "",
        "Static classification:",
        "",
        "```text",
        "update type: shadow full-field update, then full-byte hardware latch write",
        "",
        "0x9200  STAB L000A    ; commit mode byte",
        "0x9203  LDAA L004C    ; load output shadow",
        "0x9205  ANDA #$E3     ; clear bits2/3/4",
        "0x9207  ANDB #$1C     ; isolate L000A bits2/3/4",
        "0x9209  ABA           ; merge into output shadow",
        "0x920A  STAA L004C    ; shadow commit under SEI/CLI",
        "",
        "0xF40F  LDAA L004C",
        "0xF411  STAA L3062    ; hardware output latch write",
        "```",
        "",
        "The source does not show separate hardware `BSET/BCLR` operations for the A/B bits in the normal IAC step path. The normal path updates `L004C` as a masked field, then the board output service writes the full byte to `L3062`.",
        "",
        "Bench classification still required:",
        "",
        "```text",
        "Do L3062 bits2/3/4 physically equal A/B/Enable?",
        "Does any intermediate transient appear on the pins?",
        "Is LF400 called at a cadence that can delay the physical step edge after L004C is updated?",
        "```",
        "",
        "## Step Cadence / Gating",
        "",
        "Known gates:",
        "",
        "```text",
        "L0009 bit0 = IAC MOTOR Reset IN WORK",
        "L0002 bits0/1 = major loop counter gate during reset-in-work path",
        "L0864 = closed-loop enable delay after IAC qualifications",
        "```",
        "",
        "Cadence is not fully reduced to a timer equation in this pass. The step output routine is source-mapped; a follow-on `IAC_PHASE_SEQUENCE_CONTRACT` should classify step cadence and caller rate.",
        "",
        "## Contract Rows",
        "",
        "| Stage | PC | Instruction | Symbol | Role | Required? | Confidence |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in ROWS:
        inst = f"{row['mnemonic']} {row['operands']}".strip()
        lines.append(f"| {row['stage']} | `{row['pc']}` | `{inst}` | `{row['symbol']}` | {row['candidate_role']} | {row['required_for_minimal_os']} | {row['confidence']} |")
    lines += [
        "",
        "## Required New-OS Behavior",
        "",
        "The minimal OS must reproduce or explicitly replace:",
        "",
        "1. desired/actual compare using `L0007`/`L0008` equivalent state",
        "2. no-step behavior when actual equals desired",
        "3. safe direction reversal behavior before count update",
        "4. A/B four-state ring sequencing",
        "5. Enable gating behavior or a proven-safe replacement",
        "6. shadow/latch update behavior into the physical output port",
        "7. step cadence / next-step eligibility",
        "8. reset/park/home behavior",
        "",
        "## Open Questions",
        "",
        "- Which physical pins are L3062 bits2/3/4?",
        "- Does bit2=A and bit3=B match the harness/pinout, or are names swapped?",
        "- Does actual-count +1 mean open or closed airflow?",
        "- Is Enable bit4 required continuously during normal stepping?",
        "- Does any fault path deassert Enable besides the voltage gate?",
        "- What exact cadence/timer permits the next step?",
        "- Is the IAC reset/park sequence simply a count model, or does it force steps until stall/seat?",
        "",
        "## Next Contracts",
        "",
        "If bench/source review preserves this model, split follow-on work into:",
        "",
        "```text",
        "IAC_PHASE_SEQUENCE_CONTRACT",
        "IAC_ENABLE_FAULT_GATE_CONTRACT",
        "IAC_INIT_PARK_CONTRACT",
        "```",
        "",
        "No IAC writer yet.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", default="source/31/BMHM_HAC_ORG_7100_to_end.asm")
    p.add_argument("--map", default="maps/full/hardware_access_map_v0.2.csv")
    p.add_argument("--name", default="IAC_IDLE_AIR_OUTPUT")
    p.add_argument("--out-md", required=True)
    p.add_argument("--out-csv", required=True)
    args = p.parse_args()
    write_csv(resolve(args.out_csv))
    write_md(resolve(args.out_md))
    print(f"{args.name}: wrote {len(ROWS)} IAC rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
