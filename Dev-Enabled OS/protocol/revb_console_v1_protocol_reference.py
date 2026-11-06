#!/usr/bin/env python3
"""Reference packet encoder and request vector tests for proposed Rev B console protocol.

Host-side validation aid ONLY. No PCM firmware, Android binary, or vehicle interface.
"""
from __future__ import annotations
import json
from pathlib import Path

ID=0xF5
MAGIC=0xD6
VERSION=1
MAX_PAYLOAD=34

class FrameError(ValueError): pass

def encode(seq: int, op: int, args: bytes=b'', *, response=False, status=0) -> bytes:
    if not 1 <= seq <= 255: raise ValueError('sequence must be 01..FF')
    if not 0 <= op <= 127: raise ValueError('opcode must be 00..7F')
    payload=bytes([MAGIC,VERSION,seq,(op|0x80) if response else op])
    if response:
        payload += bytes([status])
    payload+=bytes(args)
    if len(payload)>MAX_PAYLOAD: raise ValueError('payload too large')
    length=0x55+len(payload)
    frame=bytes([ID,length])+payload
    return frame+bytes([(-sum(frame))&0xff])

def decode(frame: bytes, *, expect_response: bool|None=None):
    if len(frame)<7:raise FrameError('truncated')
    if frame[0]!=ID:raise FrameError('wrong id')
    n=frame[1]-0x55
    if n<4 or n>MAX_PAYLOAD:raise FrameError('illegal payload length')
    if len(frame)!=n+3:raise FrameError('length mismatch')
    if sum(frame)&255:raise FrameError('checksum')
    payload=frame[2:-1]
    if payload[0]!=MAGIC or payload[1]!=VERSION:raise FrameError('magic/version')
    if payload[2]==0:raise FrameError('reserved sequence')
    response=bool(payload[3]&0x80)
    if expect_response is not None and response!=expect_response:
        raise FrameError('direction')
    if response and len(payload)<5:raise FrameError('response status missing')
    return {'seq':payload[2], 'opcode':payload[3]&0x7f, 'response':response,
            'status':payload[4] if response else None,
            'args':payload[5:] if response else payload[4:]}

def gather_args(descriptors):
    if not 1<=len(descriptors)<=8:raise ValueError('one to eight descriptors required')
    arg=bytearray([len(descriptors)])
    for address,width in descriptors:
        if not 0<=address<=0xffff or width not in (1,2):raise ValueError('invalid descriptor')
        arg.extend(address.to_bytes(2,'big'))
        arg.append(width)
    return bytes(arg)

vectors=[]
def vector(label, seq, op, args=b'', *, explanation=''):
    f=encode(seq,op,args)
    decoded=decode(f,expect_response=False)
    assert decoded['args']==args and decoded['seq']==seq and decoded['opcode']==op
    vectors.append({'label':label,'command':explanation,'frame_hex':f.hex(' ').upper(),
                    'bytes':len(f),'payload_count':len(f)-3,'valid_additive_checksum':sum(f)&255==0})

vector('INFO identity',0x01,0x01,b'\x00', explanation='info')
vector('READ TPS 1 byte',0x02,0x10,bytes.fromhex('01 D9 01'),explanation='peek $01D9 1')
vector('GATHER three variables',0x03,0x11,gather_args([(0x0062,1),(0x01D9,1),(0x0250,2)]),explanation='get8 $0062; get8 $01D9; get16 $0250')
vector('CLOSE',0x04,0x7f, explanation='close')
vector('READ 16 ROM bytes',0x05,0x10,bytes.fromhex('40 00 10'),explanation='peek $4000 16')
vector('TRACE_FETCH 4 events [Phase 2]',0x06,0x21,bytes.fromhex('00 20 04'),explanation='trace fetch cursor=$0020 count=4')
# Synthetic reply uses made-up data for a codec-only test, not a hardware capture.
response=encode(0x02,0x10,bytes.fromhex('01 D9 01 2A'),response=True,status=0)
assert decode(response,expect_response=True)=={'seq':2,'opcode':0x10,'response':True,'status':0,'args':bytes.fromhex('01 D9 01 2A')}
# Corrupt checksum, wrong length, wrong ID must fail.
for corrupt in (vectors[1]['frame_hex'].replace(' ',''),):
    ok=bytes.fromhex(corrupt)
    for bad in (ok[:-1]+bytes([ok[-1]^1]), bytes([ok[0],ok[1]+1])+ok[2:], bytes([0xf4])+ok[1:]):
        try:decode(bad)
        except FrameError:continue
        raise AssertionError('corrupt frame accepted')
# 8 x 16-bit gather remains within 34-byte cap.
maxg=encode(7,0x11,gather_args([(0x0000+i*2,2) for i in range(8)]))
assert len(maxg)-3==29
# 4 events + 4 metadata bytes + 5 header bytes = 33 payload bytes.
max_trace_reply=encode(8,0x21, bytes(4+4*6),response=True,status=0)
assert len(max_trace_reply)-3==33
try:
    encode(1,0x11,bytes(31))
    raise AssertionError('oversized request accepted')
except ValueError:pass

if __name__=='__main__':
    out=Path(__file__).with_name('revb_console_v1_test_vectors.json')
    doc={'purpose':'Proposed Phase 1/2 developer protocol codec fixtures — not recorded vehicle traffic',
         'image_sha256':'e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1',
         'frames':vectors,
         'synthetic_response':{'label':'READ 01D9 assumed data 2A, codec test only','frame_hex':response.hex(' ').upper()},
         'tests':'length, CRC/additive checksum, request+response, corruption rejects, max gather and trace response bounds: PASS'}
    out.write_text(json.dumps(doc,indent=2)+'\n')
    print('PASS',len(vectors),'requests, 1 synthetic reply, negative tests')
    for x in vectors: print(x['label'],':',x['frame_hex'])
    print('SYNTHETIC response:',response.hex(' ').upper())
    print('Wrote',out)