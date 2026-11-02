#include "control.h"
#include "reference_math.h"
/* D4DA..D4EA, slot9: word lag from raw0812 to filtered0284.
 * Keep the word and its fractional low byte; consumers decide which
 * coordinate to use. F479's intermediate store is internal to the word.
 */
PcmStatus pcm_vss_filter(Pcm *pcm)
{
    if (pcm->calibration==NULL || pcm->calibration->io==NULL)
        return PCM_BAD_CONFIGURATION;
    pcm->io.vss_filtered=pcm_lag16(pcm->io.vss_raw,
                                  pcm->io.vss_filtered,
                                  pcm->calibration->io->vss_filter_gain,NULL);
    return PCM_OK;
}
