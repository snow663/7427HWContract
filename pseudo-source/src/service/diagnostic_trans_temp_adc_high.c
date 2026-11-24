#include "slot4_monitor.h"
/* EAE4 auxiliary_reference above threshold with timed entry and recovery. */
PcmStatus pcm_diagnostic_trans_temp_adc_high(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    return slot4_input_monitor(pcm, 0x5b05, 0x1b, 0x20, 0x16d,
                               &pcm->io.auxiliary_reference, 0x5b6b, false);
}
