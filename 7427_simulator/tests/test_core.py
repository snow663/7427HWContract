import unittest
from sim7427 import Machine
from sim7427.cpu import I, X_MASK
from sim7427.bus import RomWriteError

def rom_image(start=0x7100, instructions=b"\x01"):
    data=bytearray([0xFF]*0x10000)
    data[start:start+len(instructions)]=instructions
    data[0xFFFE:0x10000]=start.to_bytes(2,"big")
    return bytes(data)

class CoreTests(unittest.TestCase):
    def test_factory_init03_relocation_and_branch(self):
        # Stock BMHM 7100-710A, plus loop exercising relocation.
        m=Machine()
        code=bytes.fromhex("8E03FF CE1000 8603 A73D CE3000 20FE")
        m.load_bytes(rom_image(instructions=code))
        self.assertEqual(m.cpu.r.pc,0x7100)
        self.assertEqual(m.run(5).reason,"limit")
        self.assertEqual(m.cpu.r.sp,0x03FF)
        self.assertEqual(m.bus.register_base,0x3000)
        self.assertEqual(m.cpu.r.x,0x3000)
        self.assertEqual(m.bus.peek8(0x303D),0x03)
        self.assertEqual(m.run(5).reason,"limit")
        self.assertEqual(m.cpu.r.pc,0x710D)

    def test_rom_write_refused_but_explicit_debug_patch_allowed(self):
        m=Machine();m.load_bytes(rom_image())
        with self.assertRaises(RomWriteError):
            m.bus.write8(0x7100,0x00)
        m.bus.patch_rom(0x7100,0x86)
        self.assertEqual(m.bus.peek8(0x7100),0x86)
        m.reset()
        # Session patch is discarded on reload, not by soft reset.
        self.assertEqual(m.bus.peek8(0x7100),0x86)
        m.load_bytes(rom_image())
        self.assertEqual(m.bus.peek8(0x7100),0x01)

    def test_unimplemented_opcode_fails_exactly(self):
        m=Machine();m.load_bytes(rom_image(instructions=b"\x02"))
        s=m.run(100)
        self.assertEqual(s.reason,"fault")
        self.assertIn("02",s.detail)
        self.assertEqual(s.pc,0x7100)
        self.assertEqual(m.cpu.r.pc,0x7100)
        self.assertEqual(m.cpu.instructions,0)

    def test_jsr_rts_return_address(self):
        image=bytearray(rom_image(instructions=bytes.fromhex("8E03FF BD7110 20FE")))
        image[0x7110:0x7113]=bytes.fromhex("8607 39")
        m=Machine();m.load_bytes(bytes(image))
        self.assertEqual(m.run(4).reason,"limit")
        self.assertEqual(m.cpu.r.pc,0x7106)
        self.assertEqual(m.cpu.r.a,7)
        self.assertEqual(m.cpu.r.sp,0x03FF)

    def test_irq_frame_and_rti_restores_all_registers(self):
        img=bytearray(rom_image(start=0x7000,
                                instructions=bytes.fromhex("8E03FF 0E 01 20FE")))
        img[0xFFF2:0xFFF4]=(0x7100).to_bytes(2,"big")
        # ISR saves vector in RAM, samples TSX->X and publishes SP+1.
        img[0x7100:0x710B]=bytes.fromhex("CCFFD6 FD0004 30 FF0006 3B")
        m=Machine();m.load_bytes(bytes(img))
        m.run(2)
        self.assertEqual(m.cpu.r.sp,0x03FF)
        self.assertEqual(m.cpu.r.ccr&I,0)
        # HC11 guarantees the instruction after CLI before maskable entry.
        self.assertFalse(m.irq(0xFFF2))
        m.run(1)  # NOP at7004 completes the deferred-admission boundary.
        m.cpu.r.a=0x56;m.cpu.r.b=0x78;m.cpu.r.x=0x1234;m.cpu.r.y=0xABCD
        m.cpu.r.ccr=X_MASK
        self.assertTrue(m.irq(0xFFF2))
        self.assertEqual(m.cpu.r.sp,0x03F6)
        self.assertEqual(m.bus.peek8(0x03F7),X_MASK)
        self.assertEqual([m.bus.peek8(a) for a in range(0x3F8,0x400)],
                         [0x78,0x56,0x12,0x34,0xAB,0xCD,0x70,0x05])
        self.assertEqual(m.cpu.r.ccr&I,I)
        self.assertFalse(m.irq(0xFFF2))
        self.assertEqual(m.run(5).reason,"limit")
        self.assertEqual(m.bus.peek8(0x0004),0xFF)
        self.assertEqual(m.bus.peek8(0x0005),0xD6)
        self.assertEqual(m.bus.peek8(0x0006),0x03)
        self.assertEqual(m.bus.peek8(0x0007),0xF7)
        self.assertEqual((m.cpu.r.a,m.cpu.r.b,m.cpu.r.x,m.cpu.r.y,m.cpu.r.sp,m.cpu.r.pc,m.cpu.r.ccr),
                         (0x56,0x78,0x1234,0xABCD,0x03FF,0x7005,X_MASK))

    def test_shared_cpu_memory_unverified_external_ram_not_double_mirrored(self):
        m=Machine();m.load_bytes(rom_image())
        m.bus.write8(0x0800,0x42)
        self.assertEqual(m.bus.read8(0x0800),0x42)
        self.assertEqual(m.bus.region(0x0800),"general-memory")
        m.reset()
        self.assertEqual(m.bus.read8(0x0800),0)

    def test_rom_bin_sizes(self):
        m=Machine()
        for size in (0x8000,0xC000,0x10000):
            data=bytes([0xFF])*size
            m.load_bytes(data)
            self.assertEqual(len(m.bus.data),0x10000)
        with self.assertRaises(ValueError):
            m.load_bytes(bytes(500))

if __name__=="__main__":
    unittest.main()
