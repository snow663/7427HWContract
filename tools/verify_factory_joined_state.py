#!/usr/bin/env python3
"""ROM-backed joined service/mode transitions and optional caller behavior.

Selected complete execution witnesses accompany every transition row. This
does not enumerate the product of every controller state or invent missing
module implementations. Runtime RAM is never taken from file padding.
"""
from __future__ import annotations

import argparse
import ast
import csv
from hashlib import sha256
import json
from pathlib import Path

from build_factory_scheduler import csv_text,full_rom,recorded_rom
from factory_rom_decode import decode
from factory_structure import ROOT
from verify_factory_extension_map import CHANNELS
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256

OUT=ROOT/'maps/structure'
FILES=('factory_joined_state_transitions.csv','factory_optional_behavior_contracts.csv',
       'factory_state_transition_fields.csv','factory_state_transition_evidence.json')
TEST=ROOT/'tests/test_factory_joined_state_and_optional.py'

# ID, event, ordered stock anchors, admission, resulting state, ordering rule,
# and actual-ROM execution witness. These are scoped transitions, not invented
# single-mode enums for fields whose lifetimes differ.
TRANSITIONS=[
('ST-01','short service update','F9D6 FA0A FA16','accepted command04','only copied prefix changes; omitted flags and values remain','selectors and active flags have independent lifetimes','changing_selector_and_a_short_packet_keep_active_engine_overrides'),
('ST-02','selector changes while service active','F71C F71E F739 F76E F775','engine session remains; cooldown0','selector01 with old3B.4 remains active','F64E does not clear the service flag solely because selector is not04','changing_selector_and_a_short_packet_keep_active_engine_overrides'),
('ST-03','checksum arrives between enable and value sample','8C5A 8C5C F9CA FA16 8C5E 8C70','old AFR enable sampled; one accepting checksum IRQ','old enable decision publishes newly copied0397','one ISR atomic copy does not make a caller multi-instruction snapshot','one_checksum_irq_can_change_value_after_the_controller_samples_old_enable'),
('ST-04','session idle expiry','AE9D F793 F796 F799 F79F F7BA AEA0 F777','0367 increments to200 or wraps in ordinary AE85 wrapper','sessions/selectors clear;3B.3/.4 survive F781 return then F64E cleans them','ordinary wrapper calls F64E immediately; earlier AFR publication persists until recalculation','idle_expiry_leaves_an_override_until_cleanup_and_raw_aux_survives_cleanup'),
('ST-05','cleanup followed by raw auxiliary output','F777 F77A CD90 CD98 CDCB','engine service cleaned;0393&38 remains nonzero','3FD4 gets7000 OR(value0394<<4)','raw consumer does not require active service or selector04','idle_expiry_leaves_an_override_until_cleanup_and_raw_aux_survives_cleanup'),
('ST-06','release after an unconsumed payload clear request','F9D6 F739 F741 F74C F76E F777','old3B.4 active; newly retained0391.6 high; session00 accepted','F333 runs before engine cleanup','release clears session ownership before F64E samples the old service flag','session_release_can_precede_a_pending_engine_clear_edge'),
('ST-07','BLM reset edge rearm','F715 F71E F723 F72A F72E F736','qualified engine04 request0391.4','held request runs once; qualified low request rearms','selector01 skips the BLM edge-rearm branch','blm_reset_edge_rearms_only_when_its_admitted_request_is_low'),
('ST-08','engine request processed on duration-expiry pass','AE9D F7CE AEA0 F715 F720 F72E F772 F777 F77A','engine session+selector04; F781 just requested cooldown','engine admission and BLM action can run; engine selector then cleared','normal F781 to F64E order admits actions before final engine cooldown cleanup','cooldown_discards_engine_selector_but_retains_an_inactive_transmission_request'),
('ST-09','checksum admits an inactive transmission request during cooldown','AE9D F7CE AEA0 FA16 F677 F683 F688 F6F5 F7D8 F7E3 F68A','transmission initially inactive; staged frame accepts checksum at AEA0 after duration expiry','selector retained; next ordinary poll clears cooldown then activates transmission','transmission checks cooldown before admission; inactive cleanup does not erase selector','cooldown_discards_engine_selector_but_retains_an_inactive_transmission_request'),
('ST-10','duration reaches stock maximum','F7BF F7C3 F7C6 F7CE','one service active; old0368=FFFE','new0368=FFFF and036A=1','units are F781 calls; actual comparison word is[51BB]=FFFF','service_duration_triggers_shared_cooldown_then_cleanup'),
('ST-11','idle expiry rearms held engine-clear edge','AE9D F79C F7BA AEA0 F739 F741 F74C F777','engine service active; held0391.6 and0391.4 already handled; receive age199','F333 runs again before cleanup; BLM reset does not repeat','expiry clears45.7 while active3B.4/payload survive; cleared selector skips BLM qualification','idle_expiry_rearms_held_engine_clear_but_does_not_repeat_blm_reset'),
('ST-12','first inactive cooldown poll','F7D3 F7D8 F7DC F7E3 F7E6','both service flags clear;036A nonzero','036A and0368 clear on this call','actual[51BD]=0000; no long stock inactive countdown','service_duration_triggers_shared_cooldown_then_cleanup'),
('ST-13','raw current-enable selector after transmission release','F702 F712 C525 C528 C52C C546 F411','039A.6 and039B.6 retained; service cleared','004C.5 and later3062.5 set despite selected normal inhibit','raw mask/value branch precedes normal fault-gate branch','raw_current_enable_selector_survives_transmission_session_release'),
('ST-14','clear acknowledged in special fast-group mode','79D9 79E4 7A44 F74C','001A.5 active; normal accepted0A request','request persists while F64E/F333 not admitted','F333 ability to clear001A.5 does not prove a path to that call','special_mode_can_ack_clear_without_admitting_the_clear_consumer'),
('ST-15','connection probe activates disabled hooks','F5DC F5DF F5E4 F5CF F5D3','runtime word1800=7E18; old0086.6 clear','provided connection code can set enable; later background hook runs','connection probe does not test the enable latch','connection_hook_runs_while_disabled_and_can_enable_later_hooks'),
('ST-16','signature loss after activation','F5DF F5E2 F5CF F5D3','enable set; signature later mismatches','connection skips but background hook remains eligible','presence and hook enable are independent state dimensions','signature_loss_does_not_clear_the_separate_hook_enable_latch'),
('ST-17','late pass activation and profiling','7B1E F5E4 7A55 7A77','slot7 connection code changes0086.6','same tail can record or skip profile peak','tail samples current enable; activation does not clear previous peak words','connection_activation_is_seen_by_the_same_pass_profiling_tail'),
('ST-18','optional status gates closed-loop entry','E4F1 E4F5 E4FA E4FC E519','local closed-loop entry already reached','0801&03 nonzero blocks permission only when0086.6 set','module status is not an unconditional resident sensor input','extension_status_changes_closed_loop_gate_only_when_enabled'),
('ST-19','AFR optional result and service precedence','8C53 8C64 8C66 8C6A 8C6D 8C70','local AFR entry reached','hook RAM024A result published; returnedA alone discarded; AFR service bypasses hook','local service decision precedes this optional call','afr_service_bypasses_hook_and_hook_requires_a_ram_result'),
('ST-20','IAC optional prehook followed by service escape','93D4 93D7 93DE A439 A43D','enable set; position service selected','hook0038.6 cleared; resident service replaces target and escapes continuation','optional prehook is not a scalar replacement of the IAC controller','iac_hook_precedes_resident_service_and_immediate_flag_clear'),
('ST-21','governor optional carry result','8ED8 8EDF 8EE2 8EC5','local governor admission reached','C1 selects returnedA for0299; C0 continues resident math','carry is part of this result channel','governor_carry_selects_scalar_result'),
('ST-22','spark command hook and post-limit service','A9E4 A9E7 AA1A AB1D AB2C AB39 AB3E AB41','local spark stages reached','RAM01FD effect used; later service can replace/subtract without re-clamp','returnedD alone is not the command result','spark_command_hook_uses_ram_and_service_edits_follow_the_limits'),
('ST-23','spark conversion coefficient hook','AB66 AB69 AB6F AB75 AB79','conversion stage and enable admitted','returnedA survives lookup and scales word005F through F550','scalar coefficient differs from the command-word RAM hook','spark_factor_hook_a_survives_the_resident_lookup'),
('ST-24','EGR hook before desired override','D029 D02C D037 D03A','local EGR stage reached','RAM01AE used unless service0393.1 replaces it with0394','returnedA alone is not a new desired value','egr_hook_uses_ram_and_service_has_later_precedence'),
('ST-25','background result channel','F5D3 F5D6 F5D8','enable set','state side effects survive; returnedA replaced byF7 before0F00 store','the0F00 hardware meaning is not assigned by this test','connection_hook_runs_while_disabled_and_can_enable_later_hooks'),
('ST-26','factory callback capability and retarget','FA9B FA9F FAA2 FAA5 FAAD','ID02 arms; later acceptedID03 changes038E','armed callback can use new address; ID01 disarms','arm latch does not bind a permanent callback pointer','factory_callback_arm_is_not_bound_to_one_pointer'),
('ST-27','checksum retarget while callback already entered','FAA2 FAA5 F9C0 FA16 FAA7','callback old pointer sampled; one ID03 checksum IRQ','current old callback returns; next loop uses new pointer','CPU register/frame restore retains sampledX while RAM pointer changes','callback_samples_pointer_before_an_accepting_checksum_retargets_the_next_loop'),
('ST-28','factory short upload and forward overlap','FA16 FAB0 FAB3 FABC FAC4','acceptedID01; valid writable destination and completing loop','exactly32 reads/writes; short packet retains source suffix; forward overlap propagates','no atomic copy or destination whitelist is added','factory_short_upload_reuses_source_suffix_and_forward_overlap_is_literal'),
('ST-29','factory timer abandons partial upload','FABC 794E FA5B FAB0 FAC4','new factory TOC3 before selector is complemented','SP reset abandons old copy; unconsumedID01 starts again','five-byte prefix plus restarted32-byte copy gives37 writes in the fixture','factory_timer_abandons_an_upload_and_restarts_its_unconsumed_action'),
('ST-30','resident loading and later normal activation','FABC FAC4 716A 7B1E F5DC F5E4','explicit writable executable1800 fixture; reset-style boot','loaded32-byte test vectors remain; working enable clears; later probe re-enables','actual board memory retention and actual GM module code remain external','factory_upload_can_supply_a_vector_block_then_reset_probe_activates_it')]

FIELDS={0x0001:'callback arm / retained cause byte',0x001A:'special fast-group mode',0x0038:'IAC service publication',
        0x003B:'active service / clear requests / shared gate',0x003E:'closed-loop permission',0x0042:'addressed sessions',
        0x0044:'factory and engine output state',0x0045:'clear/reset edge latches',0x004C:'gear/IAC/current shadow',
        0x0086:'optional enable and unrelated resident flags',0x024A:'AFR work',0x024B:'AFR publication',
        0x0299:'governor publication',0x0364:'accepted factory ID',0x0367:'receive age',
        0x0368:'service duration high',0x0369:'service duration low',0x036A:'cooldown high',0x036B:'cooldown low',
        0x038E:'engine selector / factory pointer high',0x038F:'engine override / factory pointer low',
        0x0391:'engine clear/reset requests',0x0393:'EGR/purge/raw auxiliary selectors',0x0394:'shared override value',
        0x0395:'IAC/AFR/spark selectors',0x0396:'IAC service value',0x0397:'AFR service value',0x0398:'spark service value',
        0x0399:'transmission selector',0x039A:'transmission mask',0x039B:'transmission value',0x0801:'optional status',
        0x01AE:'desired EGR',0x01EE:'post-service spark high',0x01EF:'post-service spark low',
        0x01F0:'post-service spark copy high',0x01F1:'post-service spark copy low',0x01FD:'composite spark high',0x01FE:'composite spark low'}


def build(rom):
    if sha256(bytes([255])*0x4000+rom.read(0x4000,0xC000)).hexdigest()!=EXPECTED_SHA256:
        raise ValueError('Mapped bytes do not match stock BMHM')
    def rows(name):
        with (OUT/name).open() as source:return list(csv.DictReader(source))
    ins={int(r['pc'],16):decode(rom.read,int(r['pc'],16)) for r in rows('factory_global_instructions.csv')}
    for pc,address in [(0xF7C6,0x51BB),(0xF7DC,0x51BD)]:
        if (ins[pc].op,ins[pc].value)!=('CPX',address):raise ValueError('Service counter comparator changed')
    if (rom.word(0x51BB),rom.word(0x51BD))!=(0xFFFF,0):raise ValueError('Stock duration/cooldown words changed')
    if ins[0xF9D6].data!=bytes.fromhex('15 3B 03') or ins[0xF7BA].op!='CLI':raise ValueError('Service lifetime guard changed')
    callers={0xAE85:[0x7A14],0xF781:[0xAE9D],0xF64E:[0xAEA0],
             0xF333:[0xF74C],0xF380:[0xF75F],0xF280:[0x7236,0x8D95,0xF72E]}
    for target,expected in callers.items():
        actual=sorted(i.pc for i in ins.values() if i.target==target)
        if actual!=expected or any(ins[p].op!='JSR' for p in actual):
            raise ValueError(f'Rooted direct callers changed for {target:04X}')
    if (ins[0xAE9D].pc+len(ins[0xAE9D].data),ins[0xAEA0].pc+len(ins[0xAEA0].data),ins[0xAEA3].op)!=(0xAEA0,0xAEA3,'RTS'):
        raise ValueError('Ordinary expiry and cleanup are no longer consecutive calls')
    methods={n.name for n in ast.walk(ast.parse(TEST.read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
    touched={p for p in ins if 0xAE85<=p<=0xAEA3};touched.update(p for sites in callers.values() for p in sites)
    transitions=[]
    for ident,event,pcs,guard,effect,order,test in TRANSITIONS:
        test='test_'+test
        if test not in methods:raise ValueError(f'Missing transition witness{test}')
        anchors=[int(p,16) for p in pcs.split()]
        if any(p not in ins for p in anchors):raise ValueError('Unrooted transition anchor')
        touched.update(anchors)
        transitions.append(dict(zip(['id','event','ordered_PC_anchors','admission','state_effect','ordering_consequence','execution_test'],
                                    [ident,event,';'.join(pcs.split()),guard,effect,order,test])))
    hooks=[]
    for entry,pc,guard,channel in CHANNELS:
        instruction=ins[int(pc,16)]
        if (instruction.op,instruction.target)!=('JSR',int(entry,16)):raise ValueError('Optional call changed')
        touched.update([int(pc,16),int(guard,16)])
        precedence={'1800':'AFR service bypasses call', '1803':'93D7 clears0038.6; resident service/control follows',
                    '1806':'F5D6 overwrites A withF7','1809':'C1 selects returnedA; C0 follows resident math',
                    '180C':'recurring probe independent of0086.6; hook may enable or disable others',
                    '180F':'AB69 saves returnedA across lookup; F550 uses it',
                    '1812':'local replacement and later post-limit service can replace command',
                    '1815':'active local service can replace01AE afterward'}[entry]
        hooks.append({'entry':entry,'call_PC':pc,'gate_PC':guard,
                      'admission':'runtime[1800]==7E18' if entry=='180C' else '0086.6 plus local controller admission',
                      'observable_channel':channel,'resident_precedence':precedence,
                      'unprovided_effects':'other registers CCR SP RAM hardware control flow and normal return require supplied implementation'})
    owners={r['byte_address']:r for r in rows('factory_global_alias_owners.csv')}
    fields=[{'address':f'{a:04X}','role':role,'resident_readers':owners.get(f'{a:04X}',{}).get('readers',''),
             'resident_writers':owners.get(f'{a:04X}',{}).get('writers',''),
             'scope':'qualified finite resident aliases; arbitrary upload and supplied-code effects remain open'} for a,role in sorted(FIELDS.items())]
    enable_writers=[r for r in rows('factory_global_flag_writers.csv') if r['byte_address']=='0086' and r['bit']=='6']
    if any(r['effect_on_bit'] not in {'clear','preserve','preserve_by_self_copy'} for r in enable_writers):
        raise ValueError('New resident optional-enable producer')
    meta={'rom_sha256':EXPECTED_SHA256,'transition_rows':len(transitions),'optional_call_rows':len(hooks),
          'state_byte_rows':len(fields),'execution_test_count':len(methods),
          'rooted_direct_callers':{f'{target:04X}':[f'{p:04X}' for p in sites] for target,sites in callers.items()},
          'ordinary_poll_order':{'caller':'7A14 -> AE85','expiry_call':'AE9D -> F781','cleanup_call':'AEA0 -> F64E',
                                 'return':'AEA3','consequence':'No resident controller instruction between these calls; an accepting IRQ can occur at AEA0'},
          'counter_words':{'duration_compare_PC':'F7C6','duration_address':'51BB','duration_hex':f'{rom.word(0x51BB):04X}',
                           'inactive_compare_PC':'F7DC','inactive_address':'51BD','inactive_hex':f'{rom.word(0x51BD):04X}',
                           'adjacent_words':{'51BA':f'{rom.word(0x51BA):04X}','51BC':f'{rom.word(0x51BC):04X}'},
                           'units':'calls to F781; unsigned comparisons; consecutive ordinary F64E cleanup constrains admitted histories'},
          'enable_86_6_resident_writers':[{k:r[k] for k in ['writer_pc','effect_on_bit','condition']} for r in enable_writers],
          'instruction_anchors':[{'pc':f'{p:04X}','bytes_hex':ins[p].data.hex(' ').upper(),'instruction':ins[p].op+' '+ins[p].operand} for p in sorted(touched)],
          'required_fixture_contracts':['ASIC samples and ready bits are explicit; no physical output model',
                                       'synthetic RAM handlers are supplied test programs; no GM module implementation asserted',
                                       'writable executable1800 and RAM persistence across boot are explicit fixture properties',
                                       'staged frame-prefix tests deliver only the accepting checksum IRQ inside a caller window',
                                       'partial multi-bit BRSET cases unsupported by the generic core are rejected',
                                       'selected transitions and caller channels do not exhaust every state/input/interleaving product']}
    return {FILES[0]:csv_text(transitions),FILES[1]:csv_text(hooks),FILES[2]:csv_text(fields),FILES[3]:json.dumps(meta,indent=2,sort_keys=True)+'\n'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path);p.add_argument('--check-recorded',action='store_true');p.add_argument('--write',action='store_true')
    args=p.parse_args()
    if args.check_recorded:
        if args.rom or args.write:p.error('Recorded mode is separate from fresh-ROM/write mode')
        rom=recorded_rom(json.loads(EVIDENCE.read_text()))
    elif args.rom:rom=full_rom(args.rom)
    else:p.error('Supply --rom or --check-recorded')
    for name,content in build(rom).items():
        path=OUT/name
        if args.write:path.write_text(content)
        elif not path.exists() or path.read_text()!=content:raise SystemExit(f'Stale joined state contract:{path}')
    print('Factory joined state and optional caller contracts verified')


if __name__=='__main__':main()
