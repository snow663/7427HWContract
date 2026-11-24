"""Static ABI-probe sanity; does not pretend a native compiler is installed."""
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
S=importlib.util.spec_from_file_location("hc11_toolchain_probe",ROOT/"verify_hc11_toolchain.py")
M=importlib.util.module_from_spec(S)
sys.modules[S.name]=M
S.loader.exec_module(M)

class AbiProbeSanity(unittest.TestCase):
    def test_native_flags_and_structure_contract(self):
        self.assertIn("-m6811",M.BASE_FLAGS)
        self.assertIn("-mshort",M.BASE_FLAGS)
        self.assertIn("-ffreestanding",M.BASE_FLAGS)
        self.assertIn("sizeof(void*)==2",M.PROBE_SOURCE)
        self.assertIn("sizeof(unsigned)==2",M.PROBE_SOURCE)
        self.assertIn("PCM_IRQ_MB_SIZE==8",M.PROBE_SOURCE)
        self.assertIn("pcm_hc11_native_sizeof_pcm",M.PROBE_SOURCE)
    def test_host_architecture_rejected(self):
        self.assertEqual(M.resolve_command("python3")[0],"python3")
        with self.assertRaises(RuntimeError):
            M.resolve_command("this-hc11-tool-is-not-installed-ever")

if __name__=="__main__":unittest.main()
