#include "hc11_bus.h"
#include <stdint.h>

/* This is intentionally a target-conditional primitive, not a host
 * 64 KiB memory emulator. The build system MUST select the actual
 * MC68HC11 toolchain/ABI before defining PCM_HC11_NATIVE_MMIO.
 * A 16-bit transaction has ordered high then low bus accesses and
 * does not claim interrupt atomicity or device readback coherency. */
static PcmStatus mmio_read8(void *context, uint16_t a, uint8_t *value)
{
    (void)context;
    if (value == NULL) return PCM_BAD_CONFIGURATION;
#ifdef PCM_HC11_NATIVE_MMIO
    *value = *(volatile const uint8_t *)(uintptr_t)a;
    return PCM_OK;
#else
    (void)a;
    return PCM_NO_HARDWARE;
#endif
}
static PcmStatus mmio_read16(void *context, uint16_t a, uint16_t *value)
{
    (void)context;
    if (value == NULL) return PCM_BAD_CONFIGURATION;
#ifdef PCM_HC11_NATIVE_MMIO
    if (a == 0xffffu) return PCM_BAD_CONFIGURATION;
    uint8_t high = *(volatile const uint8_t *)(uintptr_t)a;
    uint8_t low = *(volatile const uint8_t *)(uintptr_t)(uint16_t)(a+1u);
    *value = (uint16_t)(((uint16_t)high << 8) | low);
    return PCM_OK;
#else
    (void)a;
    return PCM_NO_HARDWARE;
#endif
}
static PcmStatus mmio_write8(void *context, uint16_t a, uint8_t value)
{
    (void)context;
#ifdef PCM_HC11_NATIVE_MMIO
    *(volatile uint8_t *)(uintptr_t)a = value;
    return PCM_OK;
#else
    (void)a;
    (void)value;
    return PCM_NO_HARDWARE;
#endif
}
static PcmStatus mmio_write16(void *context, uint16_t a, uint16_t value)
{
    (void)context;
#ifdef PCM_HC11_NATIVE_MMIO
    if (a == 0xffffu) return PCM_BAD_CONFIGURATION;
    *(volatile uint8_t *)(uintptr_t)a = (uint8_t)(value >> 8);
    *(volatile uint8_t *)(uintptr_t)(uint16_t)(a+1u) = (uint8_t)value;
    return PCM_OK;
#else
    (void)a;
    (void)value;
    return PCM_NO_HARDWARE;
#endif
}
void pcm_hc11_native_mmio_init(PcmHc11Io *io, void *context,
    PcmStatus (*authorize_write)(void *, uint16_t, unsigned, uint16_t))
{
    if (io == NULL) return;
    *io = (PcmHc11Io){0};
    io->context = context;
    io->read8 = mmio_read8;
    io->read16 = mmio_read16;
    io->write8 = mmio_write8;
    io->write16 = mmio_write16;
    io->authorize_write = authorize_write;
    /* HC11 SEI/CLI, timed delay and entry frame handling are NOT C
     * substitutes: target assembly must supply them separately. */
}
