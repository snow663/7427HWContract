#include "hardware.h"
/* Reference 79E7..79EE, FA84..FA8B and other literal COP services. */
PcmStatus pcm_watchdog_service(Pcm *pcm)
{
    PcmStatus result = pcm_write8(pcm, PCM_COPRST, 0xaa);
    if (result != PCM_OK) return result;
    return pcm_write8(pcm, PCM_COPRST, 0x55);
}
