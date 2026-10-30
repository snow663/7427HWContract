#include "startup.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)

/* CC7C..CCC0, called at711C, then711F..712B. The reset-entry prelude must
 * already have relocated registers. Board writes retain literal values and
 * order; their electrical meanings are not inferred from those values. */
PcmStatus pcm_reset_cpu(Pcm *pcm)
{
    static const struct { uint16_t address; uint8_t value; } setup[] = {
        {PCM_OC1M, 0x00}, {PCM_OC1D, 0x00}, {PCM_SCCR1, 0x00},
        {PCM_CFORC, 0x00}, {PCM_SPCR, 0x00}, {PCM_TEST1, 0x00},
        {PCM_CSSTRH, 0x00}, {PCM_DDRG, 0x00}, {PCM_TCTL2, 0x26},
        {PCM_PACTL, 0x40}, {PCM_DDRA, 0x38}, {PCM_DDRD, 0x38},
        {PCM_BAUD, 0x04}, {PCM_HPRIO, 0x15}, {PCM_CSCTL, 0xac},
        {PCM_CSGSIZ, 0xcb}, {PCM_CSGADR, 0x00},
        {PCM_BOARD_3061, 0x90}, {PCM_BOARD_3063, 0xff},
        {PCM_BOARD_3065, 0x00}, {PCM_PORTA, 0x00}, {PCM_PORTD, 0x00}
    };
    for (size_t index = 0; index < sizeof(setup) / sizeof(setup[0]); ++index)
        RUN(pcm_write8(pcm, setup[index].address, setup[index].value));
    return pcm_write16(pcm, PCM_BOARD_306E, 0x7fff);
}
