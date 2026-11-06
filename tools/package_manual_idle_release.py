"""Package exact Rev A rollback and source-rebuilt Rev B with matching XDFs."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from build_manual_idle_release import build, ROOT, NAME
from verify_custom_xdf import verify, identify


def package(baseline, candidate, destination):
    old=baseline.read_bytes();new=candidate.read_bytes()
    rebuilt,manifest,_=build(old)
    if new!=rebuilt:raise ValueError('Candidate is not the exact reviewed source build')
    verify()
    assert identify(old)['profile']=='reva'
    assert identify(new)['profile']=='manual_idle_revb'
    files={
        'RevA_rollback/'+baseline.name:old,
        'RevA_rollback/7427_0.3.12_RevA.xdf':(ROOT/'definitions/7427_0.3.12_RevA.xdf').read_bytes(),
        'RevB_candidate/'+NAME:new,
        'RevB_candidate/7427_0.3.12_Manual_Idle_RevB.xdf':(ROOT/'definitions/7427_0.3.12_Manual_Idle_RevB.xdf').read_bytes(),
        'reports/patch_manifest.json':(json.dumps(manifest,indent=2)+'\n').encode(),
    }
    for source,target in [
        ('docs/investigations/MANUAL_IDLE_REVB_RELEASE.md','reports/RELEASE_TRACE.md'),
        ('maps/maintenance/manual_idle_release_runtime.json','reports/runtime_tests.json'),
        ('maps/maintenance/manual_idle_test_results.json','reports/controller_tests.json'),
        ('definitions/validation_results.json','reports/definition_tests.json'),
        ('7427_Address_Register_0.3.12.xlsx','reference/7427_Address_Register_0.3.12.xlsx'),
        ('7427_Write_Register_0.3.12.xlsx','reference/7427_Write_Register_0.3.12.xlsx'),
    ]:files[target]=(ROOT/source).read_bytes()
    for source in ['tools/build_manual_idle_release.py','tools/manual_idle_overlay.py',
                   'tools/manual_idle_asm.py','tools/factory_rom_decode.py','tools/trace_manual_idle.py',
                   'source/manual_idle/manual_idle.asm','source/manual_idle/decel_spark_gate.asm']:
        files['rebuild/'+source]=(ROOT/source).read_bytes()
    files['README.txt']=f'''7427 Rev A rollback + Rev B development candidate

Open each BIN with the XDF in the SAME folder. Both BINs are full 65,536-byte
images with file offset equal to CPU ROM address; XDF base offset is zero.
The Rev B XDF must never be used to tune Rev A: its 9F00 controls are code in
Rev A. The older Manual_Idle_DEV.xdf is not the Rev B definition.

RevB_candidate/{NAME}
  Matching definition: 7427_0.3.12_Manual_Idle_RevB.xdf
  SHA-256: {manifest['candidate_sha256']}
  Stored/calculated checksum: {manifest['checksum']}

RevA_rollback/{baseline.name}
  Matching definition: 7427_0.3.12_RevA.xdf
  Exact supplied baseline, SHA-256: {manifest['baseline_sha256']}
  Stored/calculated checksum: 6D36

Rev B changes
- Replaces both Park/Drive idle strategies with one manual-transmission
  controller: one RPM schedule and runtime learned baseline, bounded P/I,
  startup-air fade, TPS follower, stall recovery and simple A/C air addition.
- Releases DFCO spark retard at idle target +200 RPM or when fuel returns.
  Removes post-fuel spark recovery. The margin at 9F17 is shared with IAC release.
- Extends the 27.42-degree low-load base shelf through 1600 RPM, with a
  2000-RPM shoulder. Preserves every 65..100-kPa spark cell and the loaded edits.

This is a development candidate. Software checks pass; the new air settings
and engine-response stability have not been tested on the truck. Learning
resets on restart/homing. Air settings use internal air units, not motor steps.
Native TunerPro GUI loading has not been tested here. No vehicle flash was made.

In TunerPro, select the matching XDF, then open the BIN from that same folder.
Keep a separate copy before tuning. Verify the checksum after saves. Rollback
uses the original Rev A BIN and its Rev A definition together.

reports/ contains the exact reversible patch, image identities, reset/scheduler
results and definition/controller validation. reference/ contains the updated
read/write address registers for Rev B. The release trace's relative repository
links refer to https://github.com/snow663/7427HWContract.

Optional deterministic rebuild (Python 3.10+, no extra packages):
From this extracted bundle's root, run:
  python rebuild/tools/build_manual_idle_release.py RevA_rollback/{baseline.name} --output rebuilt
The rebuilt BIN must have the Rev B SHA-256 above. SHA256SUMS.txt covers every
included file except itself. Source and ongoing tests live in 7427HWContract.
'''.encode()
    files['SHA256SUMS.txt']=''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n'for name,data in sorted(files.items())).encode()
    destination.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(destination,'w')as z:
        for name,data in sorted(files.items()):
            info=ZipInfo(name);info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,data)
    with ZipFile(destination)as z:
        assert z.testzip()is None
        for name,data in files.items():assert z.read(name)==data
    return dict(filename=destination.name,bytes=destination.stat().st_size,
        sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),files=len(files))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(package(a.baseline,a.candidate,a.output),indent=2))
