#include "hc11_bus.h"

/* INIT=03 relocates the F1-style internal registers to 3000..305F.
 * CONFIG=0B's EEPROM overlay is conditional on the actual CPU response.
 * External selects are address decode, not proof of fitted RAM/ROM. */
PcmHc11Resource pcm_hc11_classify(uint16_t a)
{
    if (a <= 0x03ffu) return PCM_HC11_INTERNAL_RAM;
    if (a <= 0x0dffu) return PCM_HC11_EXTERNAL_GEN;
    if (a <= 0x0fffu) return PCM_HC11_CONDITIONAL_EEPROM;
    if (a <= 0x1fffu) return PCM_HC11_EXTERNAL_GEN;
    if (a <= 0x2fffu) return PCM_HC11_UNPROVEN_PROGRAM;
    if (a <= 0x305fu) return PCM_HC11_CPU_REGISTERS;
    if (a <= 0x37ffu) return PCM_HC11_BOARD_IO1;
    if (a <= 0x3fffu) return PCM_HC11_BOARD_IO2;
    return PCM_HC11_PROGRAM_IMAGE;
}
static const PcmHc11Window *region(const PcmHc11Bus *bus, uint16_t a,
                                   unsigned width, uint8_t permission)
{
    if (width == 16u && a == 0xffffu) return NULL;
    for (size_t i = 0; i < bus->count; ++i) {
        const PcmHc11Window *w = &bus->windows[i];
        if (a < w->first) break;
        if (a <= w->last && (w->permitted & permission) != 0) {
            if (width == 8u || a < w->last) return w;
            return NULL;
        }
    }
    return NULL;
}
static PcmStatus read8(void *context, uint16_t a, uint8_t *out)
{
    const PcmHc11Bus *bus = context;
    if (out == NULL) return PCM_BAD_CONFIGURATION;
    if (region(bus, a, 8, PCM_HC11_R8) == NULL ||
        bus->io.read8 == NULL) return PCM_NO_HARDWARE;
    return bus->io.read8(bus->io.context, a, out);
}
static PcmStatus read16(void *context, uint16_t a, uint16_t *out)
{
    const PcmHc11Bus *bus = context;
    if (out == NULL) return PCM_BAD_CONFIGURATION;
    if (region(bus, a, 16, PCM_HC11_R16) == NULL ||
        bus->io.read16 == NULL) return PCM_NO_HARDWARE;
    return bus->io.read16(bus->io.context, a, out);
}
static PcmStatus authorize(const PcmHc11Bus *bus,
                            const PcmHc11Window *window, uint16_t a,
                            unsigned width, uint16_t value)
{
    if (window->resource == PCM_HC11_INTERNAL_RAM) return PCM_OK;
    if (bus->io.authorize_write == NULL) return PCM_NO_HARDWARE;
    return bus->io.authorize_write(bus->io.context, a, width, value);
}
static PcmStatus write8(void *context, uint16_t a, uint8_t value)
{
    const PcmHc11Bus *bus = context;
    const PcmHc11Window *window = region(bus, a, 8, PCM_HC11_W8);
    if (window == NULL || bus->io.write8 == NULL) return PCM_NO_HARDWARE;
    PcmStatus s = authorize(bus, window, a, 8u, value);
    return s == PCM_OK ? bus->io.write8(bus->io.context, a, value) : s;
}
static PcmStatus write16(void *context, uint16_t a, uint16_t value)
{
    const PcmHc11Bus *bus = context;
    const PcmHc11Window *window = region(bus, a, 16, PCM_HC11_W16);
    if (window == NULL || bus->io.write16 == NULL) return PCM_NO_HARDWARE;
    PcmStatus s = authorize(bus, window, a, 16u, value);
    return s == PCM_OK ? bus->io.write16(bus->io.context, a, value) : s;
}
static PcmStatus mask_irq(void *context, bool masked)
{
    const PcmHc11Bus *bus = context;
    return bus->io.mask_irq == NULL ? PCM_NO_HARDWARE :
        bus->io.mask_irq(bus->io.context, masked);
}
static PcmStatus delay_cycles(void *context, uint16_t cycles)
{
    const PcmHc11Bus *bus = context;
    return bus->io.delay_cycles == NULL ? PCM_NO_HARDWARE :
        bus->io.delay_cycles(bus->io.context, cycles);
}
static PcmStatus check_stack(void *context, bool busy)
{
    const PcmHc11Bus *bus = context;
    return bus->io.check_stack == NULL ? PCM_NO_HARDWARE :
        bus->io.check_stack(bus->io.context, busy);
}
static PcmStatus capture_timer_stack_x(void *context, uint16_t *out)
{
    const PcmHc11Bus *bus = context;
    if (out == NULL) return PCM_BAD_CONFIGURATION;
    return bus->io.capture_timer_stack_x == NULL ? PCM_NO_HARDWARE :
        bus->io.capture_timer_stack_x(bus->io.context, out);
}
PcmStatus pcm_hc11_bus_bind(PcmHc11Bus *bus, PcmPlatform *platform,
                            const PcmHc11Io *io,
                            const PcmHc11Window *windows, size_t count)
{
    if (bus == NULL || platform == NULL || io == NULL || windows == NULL ||
        count == 0 || platform->context != NULL ||
        platform->read8 != NULL || platform->read16 != NULL ||
        platform->write8 != NULL || platform->write16 != NULL)
        return PCM_BAD_CONFIGURATION;
    for (size_t i = 0; i < count; ++i) {
        const PcmHc11Window *w = &windows[i];
        if (w->first > w->last || w->permitted == 0 ||
            (w->permitted & (uint8_t)~0x0fu) != 0 ||
            pcm_hc11_classify(w->first) != w->resource ||
            pcm_hc11_classify(w->last) != w->resource ||
            (i > 0 && windows[i-1].last >= w->first))
            return PCM_BAD_CONFIGURATION;
        if (w->resource == PCM_HC11_PROGRAM_IMAGE &&
            (w->permitted & (PCM_HC11_W8 | PCM_HC11_W16)) != 0)
            return PCM_BAD_CONFIGURATION; /* no runtime flash writer */
    }
    bus->io = *io;
    bus->windows = windows;
    bus->count = count;
    platform->context = bus;
    platform->read8 = read8;
    platform->read16 = read16;
    platform->write8 = write8;
    platform->write16 = write16;
    platform->mask_irq = io->mask_irq == NULL ? NULL : mask_irq;
    platform->delay_cycles = io->delay_cycles == NULL ? NULL : delay_cycles;
    platform->check_stack = io->check_stack == NULL ? NULL : check_stack;
    platform->capture_timer_stack_x = io->capture_timer_stack_x == NULL ?
                                      NULL : capture_timer_stack_x;
    /* Optional code and native entry MUST still be supplied separately.
     * Never imply that binding a bus implements task[]/call_address. */
    platform->call_address = NULL;
    platform->bind_fuel_ram_owners = false;
    platform->enable_resident_fuel_cycle = false;
    platform->enable_resident_slow_slots = false;
    return PCM_OK;
}
