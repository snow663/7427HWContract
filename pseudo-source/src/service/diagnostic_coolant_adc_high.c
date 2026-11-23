#include "slot4_monitor.h"
/* E793 raw_coolant above threshold with timed entry and recovery. */
PcmStatus pcm_diagnostic_coolant_adc_high(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    return slot4_input_monitor(pcm, 0x5b00, 0x16, 0x20, 0x161,
                               &pcm->io.raw_coolant, 0x5b15, false);
}
