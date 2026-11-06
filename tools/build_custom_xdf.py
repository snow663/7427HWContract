"""Build image-specific TunerPro definitions from the user's supplied $31 XDF.

No ROM is written. Known removed/repurposed locations are excluded, reviewed
custom controls are added, and untouched legacy conversions retain provenance.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from manual_idle_asm import assemble
from manual_idle_overlay import SOURCE, EXPECTED_SHA, overlay

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'definitions'
CONTRACT = DEST / 'source/custom_rom_xdf_contract.json'
BASE = DEST / 'source/Advanced_31_TP5_v251.xdf.gz'
PROFILES = {'reva':'7427_0.3.12_RevA.xdf', 'manual_idle_dev':'7427_Manual_Idle_DEV.xdf'}
NS = {'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REMOVED_CATEGORIES = {0x15, 0x40, 0x41, 0x42, 0x43, 0x44, 0x49, 0x4b, 0x4e} | set(range(0x4f, 0x64))
IDLE_CATEGORIES = set(range(0x32, 0x40))
PRESERVED_IDLE_DATA = {0x4e92, 0x4ea3, 0x4ea5, 0x4eb0, 0x4eb6, 0x4fbe, 0x50a2, 0x50a8, 0x50a9}


def read_roles():
    """Read the existing workbook; do not author or alter it with XML tools."""
    roles = {}
    with ZipFile(ROOT / '7427_Address_Register_0.3.12.xlsx') as z:
        strings = [''.join(s.itertext()) for s in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS)]
        for row in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//m:sheetData/m:row', NS):
            values = ['', '', '']
            for c in row.findall('m:c', NS):
                i = ord(c.get('r')[0]) - ord('A'); v = c.find('m:v', NS)
                values[i] = strings[int(v.text)] if c.get('t') == 's' else (v.text if v is not None else '')
            if values[0].startswith('$'): roles[values[0]] = (values[1], values[2])
    return roles


def data_element(item):
    return item.find("XDFAXIS[@id='z']/EMBEDDEDDATA") if item.tag == 'XDFTABLE' else item.find('EMBEDDEDDATA')


def footprint(item):
    e = data_element(item)
    if e is None or e.get('mmedaddress') is None: return set()
    a = int(e.get('mmedaddress'), 0)
    width = int(e.get('mmedelementsizebits', '8'))
    if width not in (8, 16, 32): raise ValueError('Unsupported XDF element width')
    if int(e.get('mmedmajorstridebits','0')) or int(e.get('mmedminorstridebits','0')):
        raise ValueError('Addressed noncontiguous definition needs explicit review')
    count = int(e.get('mmedrowcount','1')) * int(e.get('mmedcolcount','1'))
    addresses = set(range(a, a + count * (width // 8)))
    for v in item.iter('VAR'):
        if v.get('type') == 'address': addresses.add(int(v.get('address'), 0))
    return addresses


def start(item):
    e = data_element(item)
    return int(e.get('mmedaddress'), 0) if e is not None and e.get('mmedaddress') else None


def categories(item):
    # CATEGORYMEM is one-based; XDFHEADER/CATEGORY index is zero-based.
    return {int(c.get('category'), 0) - 1 for c in item.findall('CATEGORYMEM')}


def tag(parent, name, value):
    node = parent.find(name)
    if node is None: node = ET.SubElement(parent, name)
    node.text = str(value); return node


def math(node, equation):
    old = node.find('MATH')
    if old is not None: node.remove(old)
    m = ET.SubElement(node, 'MATH', equation=equation)
    ET.SubElement(m, 'VAR', id='X')
    return m


def category(item, index=0):
    for c in item.findall('CATEGORYMEM'): item.remove(c)
    ET.SubElement(item, 'CATEGORYMEM', index='0', category=str(index + 1))


def constant(uid, title, address, bits=8, equation='X', units='counts', decimals=0, description='', cat=0):
    p = ET.Element('XDFCONSTANT', uniqueid=f'0x{uid:X}', vislevel='1')
    tag(p, 'title', title); tag(p, 'description', description); category(p, cat)
    ET.SubElement(p, 'EMBEDDEDDATA', mmedaddress=f'0x{address:X}', mmedtypeflags='0x00',
        mmedelementsizebits=str(bits), mmedmajorstridebits='0', mmedminorstridebits='0')
    tag(p, 'units', units); tag(p, 'decimalpl', decimals); tag(p, 'outputtype', '1')
    tag(p, 'datatype', 0); tag(p, 'unittype', 0); ET.SubElement(p,'DALINK',index='0')
    math(p, equation); return p


def curve(uid, title, address, equation, units, description, cat=0):
    p = ET.Element('XDFTABLE', uniqueid=f'0x{uid:X}', vislevel='1', flags='0x0')
    tag(p,'title',title); tag(p,'description',description); category(p,cat)
    for axis, count, axis_units in [('x',1,''),('y',17,'Coolant index 0x0283')]:
        a = ET.SubElement(p,'XDFAXIS',id=axis,uniqueid='0x0')
        ET.SubElement(a,'EMBEDDEDDATA',mmedelementsizebits='16',mmedmajorstridebits='-32',mmedminorstridebits='0')
        tag(a,'units',axis_units); tag(a,'indexcount',count); tag(a,'datatype',0); tag(a,'unittype',0)
        tag(a,'outputtype',4); ET.SubElement(a,'DALINK',index='0')
        for i in range(count): ET.SubElement(a,'LABEL',index=str(i),value=str(i * 16 if axis=='y' else 0))
        math(a,'X')
    z = ET.SubElement(p,'XDFAXIS',id='z')
    ET.SubElement(z,'EMBEDDEDDATA',mmedaddress=f'0x{address:X}',mmedtypeflags='0x00',
        mmedelementsizebits='8',mmedrowcount='17',mmedcolcount='1',mmedmajorstridebits='0',mmedminorstridebits='0')
    tag(z,'units',units); tag(z,'decimalpl',1 if units=='RPM' else 0)
    tag(z,'min','0'); tag(z,'max','3187.5' if units=='RPM' else '255'); tag(z,'outputtype',1)
    math(z,equation); return p


def excluded(item, profile, roles, contract):
    a = start(item); addresses = footprint(item)
    if not addresses: return 'Separator/documentation placeholder with no ROM data address'
    if min(addresses) < 0x4000 or max(addresses) >= 0xffc0: return 'Outside editable calibration ROM'
    allowed_high = {0xfe9f, 0xff8a, 0xff8b}
    if any(x >= 0x7100 and x not in allowed_high for x in addresses): return 'Stock definition addresses executable or reserved high ROM'
    if any(0x5bd0 <= x < 0x7100 for x in addresses): return 'Engine helper code or removed automatic-transmission allocation'
    for row in contract['retired_data_ranges']:
        lo, hi = int(row['start'],16), int(row['end_exclusive'],16)
        if any(lo <= x < hi for x in addresses): return 'Retired allocation: ' + row['reason']
    if categories(item) & REMOVED_CATEGORIES: return 'Removed transmission/emissions/VSS/governor function'
    if item.tag == 'XDFFLAG':
        mask = int(item.findtext('mask','0'),0)
        for bit in range(8):
            if mask & (1 << bit) and roles.get(f'${a:04X}.{bit}', ('',''))[1] == 'omitted':
                return 'Option bit is omitted in the current address register'
    # Exact named starts avoid inventing roles for unrelated aliases or bytes.
    if roles.get(f'${a:04X}', ('',''))[1] == 'omitted': return 'Original role omitted in current address register'
    if profile == 'manual_idle_dev' and (categories(item) & IDLE_CATEGORIES or 0x4e8f <= a <= 0x50d4):
        if a not in PRESERVED_IDLE_DATA: return 'Replaced Park/Drive idle strategy; new controls have separate definitions'
        if item.tag == 'XDFFLAG': return 'Old idle-strategy option does not control the replacement'
    # Individual removed-feature flags can share live configuration/fault bytes.
    title = item.findtext('title','').lower()
    removed_terms = ('egr', 'purge', 'canister', 'ccp', 'vss', 'vehicle speed', 'tcc',
                     'torque management', 'shift light', 'governor', '4l80', '4l60', '700r4',
                     'transmission', 'solenoid', 'adaptive long shift', 'air management', 'force motor')
    if any(term in title for term in removed_terms): return 'Definition names an omitted feature in a shared calibration byte'
    if title.startswith(('code 16 ', 'code 77 ')):
        return 'Removed VSS-buffer or automatic range diagnostic'
    if ' mph' in title or title.startswith('mph '): return 'Road-speed control has been removed'
    if item.tag=='XDFFLAG' and a==0x48f6 and int(item.findtext('mask','0'),0)&4:
        return 'P/N BLM-cell offset code is bypassed'
    if profile=='manual_idle_dev' and title.startswith(('code 35 ', 'code 36 ')):
        return 'Original IAC learning/kicker diagnostic removed by the replacement strategy'
    return None


def customize_existing(item, profile, roles):
    a = start(item)
    current = roles.get(f'${a:04X}', ('',''))[1]
    if current: tag(item,'description',item.findtext('description','').strip() + '\n\nCurrent Rev A role: ' + current)
    if not item.findall('CATEGORYMEM'): category(item)
    if a == 0x4169 and item.tag == 'XDFTABLE':
        tag(item,'title','Single base spark table - RPM vs load')
        tag(item,'description','Active for idle and off-idle. The alternate closed-throttle base table is retired. '
            'Z is (raw - main bias at 0x413B) * 90/256 degrees. Existing RPM and nominal MAP/load axis labels are retained. '
            'Startup/coolant corrections, knock, DFCO retard and command limits still affect final timing.')
        z=item.find("XDFAXIS[@id='z']"); z.find('MATH').set('equation','0.3515625 * (X - Y)'); category(item)
    corrections = {
        0x414f:('DFCO spark recovery gain - slow','X / 256','gain',6,
            'Slow recovery gain for the retained deceleration spark-retard recovery word; not a time in seconds.'),
        0x4150:('DFCO spark recovery gain - fast','X / 256','gain',6,
            'Fast recovery gain selected above the normalized-TPS threshold at 0x4151.'),
        0x4151:('DFCO spark fast-recovery TPS threshold','X','TPS counts',0,
            'Normalized TPS count threshold selecting slow/fast retard recovery. Not volts or percent.'),
        0x4152:('DFCO base spark RETARD','0.3515625 * X','deg',3,
            'Base deceleration timing subtraction, not maximum spark advance. Zero does not universally disable retard: '
            'a coolant-dependent term can remain. There is no dedicated calibration enable bit for this correction.'),
    }
    if a in corrections and item.tag=='XDFCONSTANT':
        title,equation,units,decimals,desc=corrections[a]
        tag(item,'title',title); tag(item,'description',desc); tag(item,'units',units); tag(item,'decimalpl',decimals)
        math(item,equation); category(item)
    if a == 0x4f50 and item.tag=='XDFTABLE':
        tag(item,'title','Startup RPM - legacy Drive curve (Rev A only)')
        tag(item,'description','Still read at startup in Rev A. Normal background base target uses 0xFF60. '
            'This table does not select the normal running idle target, and is omitted in the manual-idle replacement.')
    if a == 0x4f32 and item.tag=='XDFTABLE':
        tag(item,'title','Startup RPM alternative - legacy Park curve (Rev A only)')
    if a == 0x4fbe and profile=='manual_idle_dev':
        tag(item,'title','Fuel-state RPM-error threshold (retained)')
        tag(item,'description','Retained reader at 0xE3AB still uses this threshold to publish fuel state. '
            'The old warm IAC snapshot/learning routine is removed. This shared scalar is not omitted.')
    if a==0x4eb0:
        tag(item,'title','IAC ignition-off parking target (motor position)')
    if profile=='reva' and a in (0x4f23,0x4f24,0x4f25):
        titles={0x4f23:'Drive-entry extra air (Rev A legacy controller)',
                0x4f24:'Drive-entry extra-air hold (main calls)',
                0x4f25:'Drive-entry qualification delay (main calls)'}
        tag(item,'title',titles[a]); tag(item,'units','air units' if a==0x4f23 else 'main calls')
        tag(item,'decimalpl',0); math(item,'X')
        tag(item,'description','Corrected against the resident Drive-entry code: 0x4F23 is air magnitude, '
            '0x4F24 is its hold, and 0x4F25 is qualification delay. The supplied XDF mislabeled 0x4F23 as an A/C decay period '
            'and 0x4F24 as airflow. These controls are omitted in the manual-idle replacement.')
    if a == 0xfe9f:
        mask=int(item.findtext('mask','0'),0)
        descriptions = {
            1:'Custom bit0: force open loop when normalized TPS <= 0xFF8B. This is a TPS gate, not the RPM idle-capture flag. '
              'The global bit1 takes precedence.',
            2:'Custom bit1: disable closed-loop fueling globally. The retained hooks also substitute neutral BLM '
              'and clear the signed INT-derived additive correction at RAM 0x026F. INT is not a second BLM multiplier.'}
        if mask in descriptions: tag(item,'description',descriptions[mask]); category(item)
    if item.tag == 'XDFCONSTANT' and a == 0x4006:
        tag(item,'description','Stored additive 16-bit checksum. The supplied XDF checksum definition is preserved: '
            'sum bytes 0x4008..0xFFFF, modulo 65536, stored big-endian at 0x4006. Do not edit this scalar manually.')


def custom_items(profile):
    common = [curve(0xe000, 'Base idle RPM - coolant index',0xff60,'12.5 * X','RPM',
        ('Shared startup/running target in the manual-idle replacement. ' if profile=='manual_idle_dev'
         else 'Normal background base target in Rev A; startup separately reads 0x4F50. ') +
        'Seventeen byte knots at indices 0,16,...,256 of RAM 0x0283. The axis is the native lookup index, not degrees C. '
        'The final knot is the interpolation endpoint; maximum byte input is 255.'),
        constant(0xe001,'Fuel idle-entry TPS threshold',0xff8a,description='Normalized TPS ceiling for fuel idle entry. '
            'The retained fuel classifier uses requested RPM +100/+200 RPM hysteresis. Keep paired IAC thresholds aligned.'),
        constant(0xe002,'Fuel idle-retention / OL TPS threshold',0xff8b,description='Normalized TPS ceiling for retained fuel idle, '
            'also used by the closed-throttle OL hook. This is a shared control, not volts or percent.')]
    if profile != 'manual_idle_dev': return common
    symbols=assemble(SOURCE).symbols
    common.append(curve(0xe010,'Cold idle-air feedforward - coolant index',symbols['cal_cold_air'],'X','air units',
        'Single-controller cold-air feedforward, not RPM and not motor steps. Native RAM 0x0283 index, '
        '17 knots at 0,16,...,256. Development calibration, not fitted to the truck logs.',cat=0x32))
    specs=[
        ('cal_seed','Starting learned-air baseline',8,'X','air units',0,'One runtime baseline, reseeded on restart/homing. No Park/Drive or A/C learned banks.'),
        ('cal_start_air','Startup extra air',8,'X','air units',0,'Starting air boost; falls by one unit every decay-divider period while running.'),
        ('cal_start_div','Startup-air decay period',8,'X','main calls',0,'Calls per one-unit decay. Use a positive value. Main admission is nominally about 25 ms, not guaranteed wall time.'),
        ('cal_tps_enter','IAC capture TPS ceiling',8,'X','TPS counts',0,'Normalized TPS counts. Keep aligned with the fuel threshold at 0xFF8A.'),
        ('cal_tps_exit','IAC release TPS ceiling',8,'X','TPS counts',0,'Also defines the follower closed-throttle band. Keep aligned with fuel/OL threshold at 0xFF8B.'),
        ('cal_rpm_enter','IAC capture margin above target',8,'12.5 * X','RPM',1,'IAC capture margin only. Fuel classification remains fixed at +100/+200 RPM in this revision.'),
        ('cal_rpm_exit','IAC release margin above target',8,'12.5 * X','RPM',1,'Retained IAC capture margin only. Keep default alignment with the fixed fuel idle-classifier margins unless its code is updated.'),
        ('cal_qualify','Integral qualification delay',8,'X','main calls',0,'Number of captured main-controller calls before integral admission.'),
        ('cal_deadband','Idle RPM-error deadband',8,'12.5 * X','RPM',1,'Removed from absolute RPM error before applying P/I gains.'),
        ('cal_kp','Idle proportional gain',8,'X / 256','air/count',6,'Air units per 12.5-RPM error count after deadband. Also sheds air on closed-throttle overspeed before capture.'),
        ('cal_ki_up','Idle integral gain - underspeed',8,'X / 256','air/count/call',6,'Baseline increment per 12.5-RPM error count per admitted main call. Subject to freeze and anti-windup gates.'),
        ('cal_ki_down','Idle integral gain - overspeed',8,'X / 256','air/count/call',6,'Baseline decrement per 12.5-RPM error count per admitted main call.'),
        ('cal_p_limit','Proportional air limit',16,'X / 256','air units',3,'Unsigned big-endian Q8.8 magnitude limit; not IAC motor steps.'),
        ('cal_i_limit','Learned-air baseline upper limit',16,'X / 256','air units',3,'Unsigned big-endian Q8.8 upper bound. Keep at or above the starting baseline.'),
        ('cal_follower_cap','Throttle-follower air ceiling',8,'X','air units',0,'Caps normalized TPS above the closed band, mapped one-for-one to internal air units.'),
        ('cal_follower_decay','Throttle-follower decay per main call',16,'X / 256','air/call',3,'Unsigned big-endian Q8.8 decrement. Positive decay permits the follower to reach zero and learning to resume.'),
        ('cal_stall_error','Stall margin below requested RPM',8,'12.5 * X','RPM',1,'Stall threshold is requested RPM minus this amount, floored at zero.'),
        ('cal_stall_air','Stall recovery extra air',8,'X','air units',0,'Added while captured and below the target-relative stall threshold.'),
        ('cal_ac_air','A/C request extra air',8,'X','air units',0,'Simple feedforward addition while existing request RAM 0x0052 bit5 is set; no separate learned A/C bank.')]
    for uid,(symbol,title,bits,equation,units,dp,desc) in enumerate(specs,0xe020):
        common.append(constant(uid,title,symbols[symbol],bits,equation,units,dp,desc,cat=0x32))
    return common


def build(profile, contract, roles):
    raw=gzip.decompress(BASE.read_bytes())
    if hashlib.sha256(raw).hexdigest()!=contract['base_xdf_sha256']: raise ValueError('Source XDF identity changed')
    root=ET.fromstring(raw); header=root.find('XDFHEADER'); kept=[]; report=[]
    for item in list(root):
        if item.tag=='XDFHEADER': continue
        if item.tag=='XDFCHECKSUM': kept.append(item); root.remove(item); continue
        reason=excluded(item,profile,roles,contract)
        report.append(dict(id=item.get('uniqueid'),title=item.findtext('title',''),address=None if start(item) is None else f'{start(item):04X}',
                           action='omitted' if reason else 'retained',reason=reason or 'Inherited surviving calibration; conversion retained unless explicitly corrected'))
        root.remove(item)
        if not reason:
            customize_existing(item,profile,roles); kept.append(item)
    tag(header,'fileversion','7427-custom-1.0')
    tag(header,'deftitle','7427 0.3.12 Rev A - engine only' if profile=='reva' else '7427 MANUAL IDLE DEVELOPMENT - not Rev A')
    tag(header,'author',contract['base_xdf_author']+'; custom 7427 project adaptation')
    identity=contract['profiles'][profile]
    tag(header,'description',
        f'64 KiB full-address image, base offset zero. Profile: {profile}. Pristine reference SHA-256: {identity["pristine_sha256"]}. '
        + ('Use with the released Rev A layout. ' if profile=='reva' else 'DEVELOPMENT DEFINITION ONLY: the replacement controller has not been released as a BIN. Never use its 0x9F00 controls on Rev A: those addresses contain executable code there. ')
        + 'Original source: Advanced $31 TP5 v251.xdf, author 93V8S10. Known omitted/repurposed definitions removed and reviewed custom controls added. '
        'Remaining engine definitions retain supplied conversions; this is not a new proof of every inherited unit. '
        'One base spark table is active. Startup/coolant/knock/deceleration corrections and timing limits remain. '
        'Custom air is internal controller air units, not motor steps or measured percent flow. '
        'Inherited checksum metadata is preserved. Validate image layout and checksum with tools/verify_custom_xdf.py. '
        + ('Rev A retains Drive-selected idle banks and a separate startup curve. ' if profile=='reva' else 'One runtime learned value resets on restart. New gains/cold-air defaults remain development calibration. '))
    header.find("CATEGORY[@index='0x0']").set('name','Custom ROM controls - reviewed')
    if profile=='manual_idle_dev': header.find("CATEGORY[@index='0x32']").set('name','Manual idle controller - reviewed')
    for c in custom_items(profile): root.append(c)
    for k in kept: root.append(k)
    used={index for item in root if item.tag!='XDFHEADER' for index in categories(item)}
    for c in list(header.findall('CATEGORY')):
        if int(c.get('index'),0) not in used: header.remove(c)
    # No retained formula may depend on a parameter omitted from this profile.
    ids={i.get('uniqueid') for i in root if i.tag!='XDFHEADER'}
    if len(ids)!=len(root)-1: raise ValueError('Duplicate top-level definition IDs')
    for v in root.iter('VAR'):
        if v.get('type')=='link' and v.get('linkid') not in ids: raise ValueError('Dangling parameter math link')
    # The uploaded descriptions contain CR character references and trailing
    # spaces. Normalize generated text, preserving the original source archive.
    for node in root.iter():
        if node.text is not None:
            node.text='\n'.join(line.rstrip() for line in node.text.replace('\r\n','\n').replace('\r','\n').split('\n'))
    ET.indent(root,space='  ')
    data=b'<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='utf-8')+b'\n'
    return data, report


def program_fingerprint(image, profile):
    # Protect resident program/high-ROM data and the low-ROM engine helpers;
    # exclude only reviewed writable high-ROM calibration locations.
    calibration={0xfe9f,0xff8a,0xff8b}|set(range(0xff60,0xff71))
    if profile=='manual_idle_dev': calibration |= set(range(0x9f00,0x9f27))
    return hashlib.sha256(bytes(image[a] for a in list(range(0x5bd0,0x5cdd))+list(range(0x7100,0x10000)) if a not in calibration)).hexdigest()


def record_identities(contract, rom):
    image=rom.read_bytes()
    if hashlib.sha256(image).hexdigest()!=EXPECTED_SHA: raise ValueError('Identity recording requires the exact original Rev A')
    manual,_,_=overlay(image)
    contract['manual_idle_assembly_sha256']=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    contract['profiles']={name:dict(pristine_sha256=hashlib.sha256(b).hexdigest(),program_fingerprint=program_fingerprint(b,name))
                          for name,b in [('reva',image),('manual_idle_dev',manual)]}
    CONTRACT.write_text(json.dumps(contract,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--record-identities',type=Path,help='Record reference identities using exact Rev A; no BIN output')
    p.add_argument('--check',action='store_true',help='Require committed definitions to match regeneration')
    args=p.parse_args(); contract=json.loads(CONTRACT.read_text())
    if args.record_identities: record_identities(contract,args.record_identities)
    if contract.get('manual_idle_assembly_sha256')!=hashlib.sha256(SOURCE.read_bytes()).hexdigest():
        raise SystemExit('Manual idle source changed: review the definition/layout and update its image contract')
    roles=read_roles(); manifest={}
    for profile,filename in PROFILES.items():
        data,items=build(profile,contract,roles); path=DEST/filename
        if args.check:
            if not path.exists() or path.read_bytes()!=data: raise SystemExit('Stale XDF: '+filename)
        else: path.write_bytes(data)
        manifest[profile]=dict(filename=filename,sha256=hashlib.sha256(data).hexdigest(),**contract['profiles'][profile],
            retained=sum(x['action']=='retained' for x in items),omitted=sum(x['action']=='omitted' for x in items),
            custom_entries=len(custom_items(profile)),items=items)
        print(profile,manifest[profile]['retained'],'inherited entries,',manifest[profile]['custom_entries'],'new entries')
    result=json.dumps(manifest,indent=2)+'\n'
    target=DEST/'custom_xdf_manifest.json'
    if args.check:
        if target.read_text()!=result: raise SystemExit('Stale XDF manifest')
    else: target.write_text(result)
