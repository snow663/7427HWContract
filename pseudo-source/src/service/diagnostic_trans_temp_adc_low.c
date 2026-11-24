#include "slot4_monitor.h"
/* EAB1 auxiliary_reference below threshold with timed entry and recovery. */
PcmStatus pcm_diagnostic_trans_temp_adc_low(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    return slot4_input_monitor(pcm, 0x5b05, 0x1b, 0x40, 0x16c,
                               &pcm->io.auxiliary_reference, 0x5b68, true);
}
