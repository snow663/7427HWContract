#include "hardware.h"
#include "../system/system_internal.h"

/* CC7C..CCC0. Startup and slot 0C enter this same register sequence. */
PcmStatus pcm_refresh_registers(Pcm *pcm)
{
    static const struct { uint16_t address; uint8_t value; } setup[] = {
        {PCM_OC1M, 0}, {PCM_OC1D, 0}, {PCM_SCCR1, 0}, {PCM_CFORC, 0},
        {PCM_SPCR, 0}, {PCM_TEST1, 0}, {PCM_CSSTRH, 0}, {PCM_DDRG, 0},
        {PCM_TCTL2, 0x26}, {PCM_PACTL, 0x40}, {PCM_DDRA, 0x38}, {PCM_DDRD, 0x38},
        {PCM_BAUD, 0x04}, {PCM_HPRIO, 0x15}, {PCM_CSCTL, 0xac}, {PCM_CSGSIZ, 0xcb},
        {PCM_CSGADR, 0}, {PCM_BOARD_3061, 0x90}, {PCM_BOARD_3063, 0xff}, {PCM_BOARD_3065, 0}
    };
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    for (size_t i = 0; i < sizeof(setup) / sizeof(setup[0]); ++i)
        SYS_RUN(pcm_write8(pcm, setup[i].address, setup[i].value));
    return PCM_OK;
}
