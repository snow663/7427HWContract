#include "system.h"
#include "hardware.h"
/*7193..71C2. The diagnostic window sets0050.3 before the remaining tests.
 * The caller owns redirection to7459; no native stack reset is synthesized. */
PcmStatus pcm_factory_admit(Pcm *pcm)
{
    uint8_t sample=pcm->io.diagnostic_sample;
    if (sample>=0x64 || sample<0x28) return PCM_OK;
    pcm->io.diagnostic_warm=true;
    if (pcm->fuel.raw_throttle<0xfc || pcm->io.raw_coolant<0xfc ||
        pcm->io.auxiliary_reference>5) return PCM_OK;
    pcm->runtime.factory_mode=true;
    pcm->system.factory_flags=0;
    return pcm_write16(pcm,PCM_BOARD_CONTROL,0xb93a);
}
