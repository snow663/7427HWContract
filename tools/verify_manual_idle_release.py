"""Validate a released Rev B BIN against an exact Rev A and modeled scheduler."""
import argparse
import hashlib
import json
from pathlib import Path
from build_manual_idle_release import build, ROOT
from verify_manual_idle_runtime import run_case


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    original=args.baseline.read_bytes();image,manifest,retired=build(original)
    assert image==args.candidate.read_bytes(),'Candidate differs from deterministic source build'
    cases=[('key_on',dict(rpm=0)),('crank',dict(rpm=180,coolant=87)),
           ('hot_idle',dict(rpm=875)),('cold_idle',dict(rpm=1275,coolant=87)),
           ('cruise',dict(rpm=2200,tps=75,map=130)),
           ('power',dict(rpm=3500,tps=200,map=210)),
           ('hot_idle_legacy_noise',dict(rpm=875,noise=255))]
    results=[]
    for name,case in cases:
        row=run_case(name,image,retired,case,420000)
        results.append(row);print(name,'passed',flush=True)
    assert results[2]['engine_output_digest']==results[-1]['engine_output_digest']
    for name,case in [('hot_idle_extended',dict(rpm=875)),('cold_idle_extended',dict(rpm=1275,coolant=87))]:
        row=run_case(name,image,retired,case,24000000,main_calls=320)
        results.append(row);print(name,'passed',flush=True)
    assert args.baseline.read_bytes()==original
    report=dict(candidate_sha256=hashlib.sha256(image).hexdigest(),cases=results,
        scope='Actual candidate bytes in full reset/interrupt/scheduler fixtures. Sensor/device models and imposed RPM do not establish engine-response stability, physical PCM behavior or timing deadlines.')
    args.output.write_text(json.dumps(report,indent=2)+'\n')
