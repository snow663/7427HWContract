#include "slot4_monitor.h"
/* EB4D barometric_sample below threshold with timed entry and recovery. */
PcmStatus pcm_diagnostic_baro_adc_low(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    return slot4_input_monitor(pcm, 0x5b05, 0x1b, 0x2, 0x16f,
                               &pcm->io.barometric_sample, 0x5b71, true);
}
