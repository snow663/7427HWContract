#include "slot4_monitor.h"
/* EB19 barometric_sample above threshold with timed entry and recovery. */
PcmStatus pcm_diagnostic_baro_adc_high(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    return slot4_input_monitor(pcm, 0x5b05, 0x1b, 0x4, 0x16e,
                               &pcm->io.barometric_sample, 0x5b6d, false);
}
