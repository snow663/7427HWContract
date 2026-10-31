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
    event_binary=Path(directory)/'pcm_reference_event_tests'
    subprocess.run([*compiler,'-std=c11','-Wall','-Wextra','-Wpedantic','-Werror',
                    '-I',str(ROOT/'include'),*[str(p) for p in sources],str(ROOT/'tests/reference_event_test.c'),'-o',str(event_binary)],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/compare_reference_event_rom.py'),str(event_binary)],check=True)
    subprocess.run([str(event_binary),'--oc1-contracts'],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/compare_oc1_rom.py'),str(event_binary)],check=True)
    knock_binary=Path(directory)/'pcm_knock_tests'
    subprocess.run([*compiler,'-std=c11','-Wall','-Wextra','-Wpedantic','-Werror',
                    '-I',str(ROOT/'include'),*[str(p) for p in sources],str(ROOT/'tests/knock_test.c'),'-o',str(knock_binary)],check=True)
    subprocess.run([str(knock_binary),'--contracts'],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/compare_knock_rom.py'),str(knock_binary)],check=True)
    subprocess.run([str(knock_binary),'--adaptive-contracts'],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/compare_adaptive_spark_rom.py'),str(knock_binary)],check=True)
    spark_binary=Path(directory)/'pcm_spark_tests'
    subprocess.run([*compiler,'-std=c11','-Wall','-Wextra','-Wpedantic','-Werror',
                    '-I',str(ROOT/'include'),*[str(p) for p in sources],str(ROOT/'tests/spark_test.c'),'-o',str(spark_binary)],check=True)
    subprocess.run([str(spark_binary),'--contracts'],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/compare_spark_rom.py'),str(spark_binary)],check=True)
    subprocess.run([str(spark_binary),'--modifier-contracts'],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/compare_spark_modifiers_rom.py'),str(spark_binary)],check=True)
    subprocess.run([str(spark_binary),'--command-contracts'],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/compare_spark_command_rom.py'),str(spark_binary)],check=True)
    admission_binary=Path(directory)/'pcm_spark_admission_tests'
    subprocess.run([*compiler,'-std=c11','-Wall','-Wextra','-Wpedantic','-Werror',
                    '-I',str(ROOT/'include'),*[str(p) for p in sources],str(ROOT/'tests/spark_admission_test.c'),'-o',str(admission_binary)],check=True)
    subprocess.run([str(admission_binary),'--contracts'],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/compare_spark_admission_rom.py'),str(admission_binary)],check=True)
    subprocess.run([str(spark_binary),'--period-contracts'],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/compare_spark_period_rom.py'),str(spark_binary)],check=True)
    subprocess.run([str(spark_binary),'--output-contracts'],check=True)
    subprocess.run([sys.executable,str(ROOT/'tests/compare_spark_output_rom.py'),str(spark_binary)],check=True)
