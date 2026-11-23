#include "slot4_monitor.h"
/* E75F raw_coolant below threshold with timed entry and recovery. */
PcmStatus pcm_diagnostic_coolant_adc_low(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    return slot4_input_monitor(pcm, 0x5b00, 0x16, 0x40, 0x160,
                               &pcm->io.raw_coolant, 0x5b13, true);
}
