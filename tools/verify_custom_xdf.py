"""Validate custom XDF address/layout contracts; optionally identify a tuned BIN.

Reads only. No checksum repair, ROM export, or native TunerPro UI is performed.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from build_custom_xdf import (ROOT, DEST, CONTRACT, PROFILES, footprint, data_element,
    program_fingerprint, custom_items, categories)
from manual_idle_asm import assemble
from manual_idle_overlay import SOURCE


def arithmetic(equation, variables):
    """Evaluate the reviewed simple custom conversions without Python eval."""
    def visit(n):
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)): return n.value
        if isinstance(n,ast.Name) and n.id in variables: return variables[n.id]
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub): return -visit(n.operand)
        if isinstance(n,ast.BinOp):
            a,b=visit(n.left),visit(n.right)
            if isinstance(n.op,ast.Add): return a+b
            if isinstance(n.op,ast.Sub): return a-b
            if isinstance(n.op,ast.Mult): return a*b
            if isinstance(n.op,ast.Div): return a/b
        raise ValueError('Unsupported conversion expression')
    return visit(ast.parse(equation,mode='eval').body)


def decode_scalar(item, image):
    e=data_element(item); a=int(e.get('mmedaddress'),0); n=int(e.get('mmedelementsizebits','8'))//8
    flags=int(e.get('mmedtypeflags','0'),0)
    raw=int.from_bytes(image[a:a+n],'big',signed=bool(flags & 1))
    math=item.find('MATH') if item.tag!='XDFTABLE' else item.find("XDFAXIS[@id='z']/MATH")
    variables={'X':raw}
    for var in math.findall('VAR'):
        if var.get('type')=='address': variables[var.get('id')]=image[int(var.get('address'),0)]
    return arithmetic(math.get('equation'),variables)


def encode_scalar(item, image, value):
    """In-memory test edit using the affine custom XDF math; never writes a file."""
    if item.tag!='XDFCONSTANT': raise ValueError('Expected scalar')
    m=item.find('MATH'); equation=m.get('equation')
    zero=arithmetic(equation,{'X':0}); one=arithmetic(equation,{'X':1})
    raw=(value-zero)/(one-zero)
    if abs(raw-round(raw))>1e-9: raise ValueError('Value not exactly representable')
    e=data_element(item); a=int(e.get('mmedaddress'),0); n=int(e.get('mmedelementsizebits','8'))//8
    image[a:a+n]=int(round(raw)).to_bytes(n,'big',signed=False)


def verify():
    contract=json.loads(CONTRACT.read_text()); manifest=json.loads((DEST/'custom_xdf_manifest.json').read_text())
    summaries={}
    for profile,filename in PROFILES.items():
        path=DEST/filename; raw=path.read_bytes(); root=ET.fromstring(raw)
        assert root.tag=='XDFFORMAT' and root.get('version')=='1.80'
        assert hashlib.sha256(raw).hexdigest()==manifest[profile]['sha256']
        assert root.find('XDFHEADER/BASEOFFSET').attrib=={'offset':'0','subtract':'0'}
        region=root.find('XDFHEADER/REGION'); assert int(region.get('size'),0)==65536
        defaults=root.find('XDFHEADER/DEFAULTS'); assert defaults.get('lsbfirst')=='0'
        checksum=root.find('XDFCHECKSUM/REGION')
        assert [int(checksum.findtext(n),0) for n in ('datastart','dataend','storeaddress','calculationmethod')]==[0x4008,0xffff,0x4006,0]
        ids=[p.get('uniqueid') for p in root if p.tag!='XDFHEADER']; assert len(set(ids))==len(ids)
        cat_ids={int(c.get('index'),0) for c in root.findall('XDFHEADER/CATEGORY')}
        high={0xfe9f,0xff8a,0xff8b}|set(range(0xff60,0xff71))
        if profile=='manual_idle_dev': high|=set(range(0x9f00,0x9f27))
        for p in root:
            if p.tag in ('XDFHEADER','XDFCHECKSUM'): continue
            addresses=footprint(p); assert addresses, p.findtext('title')
            assert min(addresses)>=0x4000 and max(addresses)<0xffc0
            assert all(a<0x7100 or a in high for a in addresses), p.findtext('title')
            assert not any(0x5bd0<=a<0x7100 for a in addresses),p.findtext('title')
            for row in contract['retired_data_ranges']:
                assert not any(int(row['start'],16)<=a<int(row['end_exclusive'],16) for a in addresses)
            assert categories(p)<=cat_ids
            for var in p.iter('VAR'):
                if var.get('type')=='link': assert var.get('linkid') in ids
            if p.tag=='XDFTABLE':
                z=data_element(p)
                assert int(z.get('mmedrowcount','1'))==int(p.findtext("XDFAXIS[@id='y']/indexcount",'1'))
                assert int(z.get('mmedcolcount','1'))==int(p.findtext("XDFAXIS[@id='x']/indexcount",'1'))
        if profile=='manual_idle_dev':
            covered=Counter(a for p in root if p.tag not in ('XDFHEADER','XDFCHECKSUM')
                            for a in footprint(p) if 0x9f00<=a<0x9f27)
            assert set(covered)==set(range(0x9f00,0x9f27)) and set(covered.values())=={1}
            syms=assemble(SOURCE).symbols
            for p in custom_items(profile):
                e=data_element(p); a=int(e.get('mmedaddress'),0)
                if a>=0x9f00 and a<0x9f27: assert a in {v for k,v in syms.items() if k.startswith('cal_')}
        summaries[profile]=dict(filename=filename,parameters=len(ids)-1,custom_entries=manifest[profile]['custom_entries'])
    return summaries


def identify(image):
    if len(image)!=65536: raise ValueError('Use the full 65536-byte image, with file offset equal to CPU ROM address')
    c=json.loads(CONTRACT.read_text()); matches=[]
    for name,record in c['profiles'].items():
        if program_fingerprint(image,name)==record['program_fingerprint']: matches.append(name)
    if len(matches)!=1: raise ValueError('Image does not match exactly one reviewed program layout; do not guess an XDF')
    expected=int.from_bytes(image[0x4006:0x4008],'big'); actual=sum(image[0x4008:])&65535
    if expected!=actual: raise ValueError(f'ROM checksum mismatch: stored {expected:04X}, calculated {actual:04X}')
    profile=matches[0]
    return dict(profile=profile,xdf=PROFILES[profile],checksum=f'{actual:04X}',
        pristine_reference=hashlib.sha256(image).hexdigest()==c['profiles'][profile]['pristine_sha256'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,help='Identify the program layout and verify its additive checksum; read-only')
    args=p.parse_args(); result=verify()
    if args.rom: result['rom']=identify(args.rom.read_bytes())
    print(json.dumps(result,indent=2))
