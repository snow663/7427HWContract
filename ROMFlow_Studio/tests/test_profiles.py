"""Regression tests for mask-scoped ROMFlow analysis and profile identity."""
import hashlib
import unittest
from studio.analysis import Image, Analyzer
from studio.profile_catalog import PROFILE_IDS, get_profile, exec_ranges, match_rom_sha


class ProfileContractTests(unittest.TestCase):
    def test_families_separate(self):
        bhdc = get_profile("gm_7427_bhdc")
        bamw = get_profile("gm_7060_d8_bamw")
        self.assertEqual(bhdc["pcm"], "16197427")
        self.assertEqual(bamw["pcm"], "16147060")
        self.assertEqual(bamw["mask"], "$D8")
        self.assertEqual(exec_ranges("gm_7427_bhdc"), [(0x7100, 0xFFFF)])
        self.assertEqual(exec_ranges("gm_7060_d8_bamw"), [(0xA000, 0xFFFF)])
        self.assertEqual(bhdc["scheduler"]["address"], "7B85")
        self.assertFalse(bhdc["scheduler"]["auto_root_on_hash_match"])

    def test_source_specific_hints_do_not_cross_masks(self):
        self.assertTrue(get_profile("gm_7427_31")["table_hints"])
        self.assertFalse(get_profile("gm_7427_bhdc")["table_hints"])
        self.assertFalse(get_profile("gm_7060_85")["table_hints"])
        self.assertTrue(get_profile("gm_7060_d8_bamw")["table_hints"])
        self.assertEqual(get_profile("gm_7060_d8_bamw")["sci"]["base"], "1000")

    def test_exact_hash_only(self):
        sha = get_profile("gm_7427_bhdc")["rom_sha256"]
        self.assertEqual(match_rom_sha(sha), "gm_7427_bhdc")
        self.assertIsNone(match_rom_sha("0" * 64))

    def test_7427_padding_and_pointer_data_not_code(self):
        rom = bytearray([0xFF] * 65536)
        rom[0x7100:0x7104] = bytes.fromhex("BD 71 20 39")
        rom[0x7120] = 0x39
        rom[0xFFFE:0x10000] = bytes.fromhex("71 00")
        rom[0x7B85:0x7B89] = bytes.fromhex("00 60 71 20")
        an = Analyzer(Image(bytes(rom), 0), [], execution_regions=exec_ranges("gm_7427_bhdc")).scan()
        self.assertIn(0x7100, an.instructions)
        self.assertIn(0x7120, an.instructions)
        self.assertNotIn(0x0060, an.instructions)
        self.assertNotIn(0x7B85, an.instructions)
        self.assertLess(len(an.instructions), 25)

    def test_7060_calibration_not_promoted_to_code(self):
        rom = bytearray([0xFF] * 65536)
        rom[0x8000:0x8009] = bytes.fromhex("13 ED 05 7A 2A 33 39 09 D8")
        rom[0xA000] = 0x39
        rom[0xF1BA] = 0x39
        rom[0xFFFE:0x10000] = bytes.fromhex("F1 BA")
        an = Analyzer(Image(bytes(rom), 0), [], execution_regions=exec_ranges("gm_7060_d8_bamw")).scan()
        self.assertIn(0xF1BA, an.instructions)
        self.assertNotIn(0x8000, an.instructions)
        self.assertNotIn(0x8008, an.instructions)


if __name__ == "__main__":
    unittest.main()
