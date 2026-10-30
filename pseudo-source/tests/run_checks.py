"""One-command host verification using Python and an available C compiler."""
from pathlib import Path
import os
import shlex
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='pcm-pseudo-') as directory:
    binary=Path(directory)/'pcm_kernel_tests'
    sources=sorted((ROOT/'src').rglob('*.c'))+sorted((ROOT/'calibration').glob('*.c'))
    compiler=shlex.split(os.environ.get('CC','cc'))
    subprocess.run([*compiler,'-std=c11','-Wall','-Wextra','-Wpedantic','-Werror',
                    '-I',str(ROOT/'include'),*[str(p) for p in sources],str(ROOT/'tests/kernel_test.c'),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/check_provenance.py')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/compare_rom.py'),str(binary)],check=True)
    hardware_binary=Path(directory)/'pcm_hardware_tests'
    subprocess.run([*compiler,'-std=c11','-Wall','-Wextra','-Wpedantic','-Werror',
                    '-I',str(ROOT/'include'),*[str(p) for p in sources],str(ROOT/'tests/hardware_test.c'),'-o',str(hardware_binary)],check=True)
    subprocess.run([str(hardware_binary)],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/compare_hardware_rom.py'),str(hardware_binary)],check=True)
