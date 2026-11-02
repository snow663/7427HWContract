"""Compile host fixtures, gate on quick contracts, then compare stock ROM.

--contracts-only builds every fixture and runs the fast gate without the long
ROM comparisons. The default runs the same complete test set as CMake.
"""
from pathlib import Path
import argparse
import os
import shlex
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--contracts-only',action='store_true')
args=parser.parse_args()
# Target, fixture, isolated historical bodies, contract arguments, ROM suites.
TARGETS=[
 ('kernel','kernel_test',[],[[]],['rom']),
 ('hardware','hardware_test',[],[[]],['hardware_rom']),
 ('reference_event','reference_event_test',[],[['--oc1-contracts']],['reference_event_rom','oc1_rom']),
 ('knock','knock_test',['ac_switch'],[['--contracts'],['--adaptive-contracts']],['knock_rom','adaptive_spark_rom']),
 ('spark','spark_test',['alternate'],[['--contracts'],['--modifier-contracts'],['--command-contracts'],['--period-contracts'],['--output-contracts']],['spark_rom','spark_modifiers_rom','spark_command_rom','spark_period_rom','spark_output_rom']),
 ('spark_admission','spark_admission_test',['alternate'],[['--contracts']],['spark_admission_rom']),
 ('spark_controller','spark_test',[],[['--controller-contracts']],['spark_controller_rom']),
 ('slot7','slot7_test',['iac_background','shift_lamp'],[['--contracts']],['slot7_rom']),
 ('iac','iac_test',['shift_lamp'],[['--contracts']],['iac_rom']),
 ('iac_slow','iac_slow_test',['shift_lamp','vss_filter'],[['--contracts']],['iac_slow_rom']),
 ('iac_main','iac_main_test',['shift_lamp','vss_filter'],[['--contracts']],['iac_main_rom']),
 ('iac_step','iac_step_test',['shift_lamp','vss_filter'],[['--contracts']],['iac_step_rom']),
 ('io','io_test',['shift_lamp','vss_filter'],[['--contracts']],['io_rom']),
 ('inputs','inputs_test',[],[['--contracts']],['inputs_rom']),
 ('fuel_output','fuel_output_test',[],[['--contracts']],['fuel_output_rom']),
 ('fuel_air','fuel_air_test',[],[['--contracts']],['fuel_air_rom']),
]
REPLACED={
 'alternate':'spark/alternate_rpm.c', 'iac_background':'idle/iac_background.c',
 'ac_switch':'sensors/ac_switch_inputs.c', 'shift_lamp':'transmission/shift_lamp.c',
 'vss_filter':'sensors/vss_filter.c',
}
with tempfile.TemporaryDirectory(prefix='pcm-pseudo-') as directory:
    sources=sorted((ROOT/'src').rglob('*.c'))+sorted((ROOT/'calibration').glob('*.c'))
    compiler=shlex.split(os.environ.get('CC','cc'))
    binaries={}
    # Finish all short compilation/contract checks before spending time in ROM.
    for name,fixture,boundaries,contracts,suites in TARGETS:
        replaced={ROOT/'src'/REPLACED[b] for b in boundaries}
        selected=[p for p in sources if p not in replaced]
        selected += [ROOT/'tests'/f'{b}_boundary.c' for b in boundaries]
        binary=Path(directory)/f'pcm_{name}_tests';binaries[name]=binary
        subprocess.run([*compiler,'-std=c11','-Wall','-Wextra','-Wpedantic','-Werror',
                        '-I',str(ROOT/'include'),*[str(p) for p in selected],
                        str(ROOT/'tests'/f'{fixture}.c'),'-o',str(binary)],check=True)
        for arguments in contracts:subprocess.run([str(binary),*arguments],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/check_provenance.py')],check=True)
    if not args.contracts_only:
        for name,fixture,boundaries,contracts,suites in TARGETS:
            for suite in suites:
                subprocess.run([sys.executable,str(ROOT/'tests'/f'compare_{suite}.py'),str(binaries[name])],check=True)
