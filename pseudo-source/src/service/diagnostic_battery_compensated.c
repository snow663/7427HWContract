#include "slot4_monitor.h"
/* EC79 DTC 75 battery threshold with transmission temperature and RPM qualification. */
PcmStatus pcm_diagnostic_battery_compensated(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    if (pcm->runtime.monitor_freeze) return PCM_OK;
    uint8_t flags, upper, lower, temperature, age;
    uint16_t rpm, gate;
    DG8(0x5b07, flags);
    if (!(flags & 0x80u)) return pcm_write8(pcm, 0x178, 0);
    DG16(0x1ac, rpm);
    DG16(0x5b9b, gate);
    if (rpm < gate) return pcm_write8(pcm, 0x178, 0);
    DG8(0x1d, flags);
    uint16_t base = flags & 0x80u ? 0x5b98 : 0x5b96;
    DG8((uint16_t)(base + 1u), upper);
    DG8(base, lower);
    DG8(0xb5, temperature);
    uint16_t product = (uint16_t)((uint8_t)(upper - lower) * (unsigned)temperature);
    DG8(base, lower);  /* ADCA rereads the low endpoint after MUL. */
    uint8_t threshold = (uint8_t)(lower + ((product + 128u) >> 8));
    DG8(0x178, age);
    return slot4_debounce(pcm, 0x1d, 0x80, threshold > pcm->spark.battery_sample,
                          0x178, age, 0x5b9a);
}
