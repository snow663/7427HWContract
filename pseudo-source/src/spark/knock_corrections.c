#include "knock.h"
/* AA33..AADB: burst runs before normal KR, including the expiry call where
 * burst still subtracts but its newly cleared latch admits normal KR. */
PcmStatus pcm_knock_corrections(Pcm *pcm)
{
    PcmStatus result = pcm_knock_burst(pcm);
    if (result != PCM_OK) return result;
    return pcm_knock_retard(pcm);
}
