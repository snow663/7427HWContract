#include "board_io.h"
#include "system_internal.h"

/* CC35..CCC0. The F3ED call/return gap belongs inside the masked board RMW.
 * The twenty-register refresh follows CLI and the output-shadow clear. */
PcmStatus pcm_slow_register_service(Pcm *pcm)
{
    if (pcm == NULL || pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t value;
    if (!pcm->runtime.spark_running) {
        uint8_t coolant = pcm->reference.coolant;
        SYS_RUN(pcm_write8(pcm, 0x0282, coolant));
        pcm->iac.starting_coolant = coolant;
        SYS_RUN(pcm_read8(pcm, 0x48be, &value));
        SYS_RUN(pcm_write16(pcm, 0x01d0, (uint16_t)((uint16_t)value << 8)));
        SYS_RUN(pcm_write8(pcm, 0x01d5, value));
        pcm->fuel.raw_oxygen = value;
    }
    SYS_RUN(pcm_read8(pcm, 0x03b0, &value));
    if (value) SYS_RUN(pcm_update8(pcm, 0x3a, 0, 0x10));
    SYS_RUN(pcm_update8(pcm, PCM_TMSK1, 0, 0xa0));
    SYS_RUN(pcm_mask_irq(pcm, true));
    uint16_t board;
    SYS_RUN(pcm_read16(pcm, PCM_BOARD_CONTROL, &board));
    uint16_t mask = pcm->calibration->reference.mode_b & 1u ? 0x7912 : 0xf932;
    SYS_RUN(pcm_delay_cycles(pcm, 11));
    SYS_RUN(pcm_write16(pcm, PCM_BOARD_CONTROL, (uint16_t)((board & 0xfffeu) | mask)));
    SYS_RUN(pcm_mask_irq(pcm, false));
    value = (uint8_t)(pcm->transmission.output_shadow & 0x7fu);
    SYS_RUN(pcm_write8(pcm, 0x4c, value));
    pcm->transmission.output_shadow = value;
    return pcm_refresh_registers(pcm);
}
