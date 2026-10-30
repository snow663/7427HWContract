#include "startup.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)

/* 712B..7164, with calibration selecting the stock B93A/B91A seed. F3ED is
 * literally RTS in BMHM. Keep the control readback and SCSR/SCDR word read;
 * replacing them with cached values or byte reads changes the transaction. */
PcmStatus pcm_reset_outputs(Pcm *pcm)
{
    uint16_t value;
    if (pcm->calibration == NULL) return PCM_BAD_CONFIGURATION;
    RUN(pcm_write16(pcm, PCM_BOARD_CONTROL, pcm->calibration->board_startup_word));
    RUN(pcm_read16(pcm, PCM_BOARD_CONTROL, &value));
    RUN(pcm_write16(pcm, PCM_BOARD_CONTROL, (uint16_t)((value & 0xfffbu) | 0x0008u)));
    RUN(pcm_read16(pcm, PCM_SCSR, &value));
    RUN(pcm_write8(pcm, PCM_SCCR2, 0x26));
    for (uint16_t address = 0x3fc0; address < 0x3ffa; address += 2)
        RUN(pcm_write16(pcm, address, 0x0000));
    return PCM_OK;
}
