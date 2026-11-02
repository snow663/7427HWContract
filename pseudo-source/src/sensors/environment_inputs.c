#include "board_io.h"
#include "knock.h"
#include "reference_math.h"
/* C9F7..CA6A ->CB14. Preserve five successive stores before the shared
 * burst-gain tail. Density caps before subtracting fixed80. */
PcmStatus pcm_environment_inputs(Pcm *pcm)
{
    if (pcm->calibration==NULL || pcm->calibration->environment==NULL) return PCM_BAD_CONFIGURATION;
    const PcmEnvironmentCalibration *cal=pcm->calibration->environment;
    pcm->io.environmental_trim=pcm_lookup16(pcm->iac.coolant_index,cal->coolant_trim);
    pcm->io.environmental_factor=pcm_lookup16(pcm->iac.coolant_index>>1,cal->coolant_factor);
    uint8_t coolant=pcm->reference.coolant;
    uint8_t value=pcm_lookup16(coolant>192u?192u:coolant,cal->coolant_load);
    if (!pcm->iac.startup_cancel && pcm->reference.coolant<=cal->low_coolant_limit)
        value=value<cal->low_coolant_subtract?0:(uint8_t)(value-cal->low_coolant_subtract);
    pcm->io.environmental_load=value;
    pcm->io.environmental_idle=pcm_lookup16(pcm->iac.coolant_index,cal->coolant_idle);
    uint8_t coordinate=pcm->reference.coolant;
    if (coordinate>cal->density.limit) coordinate=cal->density.limit;
    coordinate=coordinate<80u?0:(uint8_t)(coordinate-80u);
    if (cal->density.values==NULL || (coordinate>>4)+1u>=cal->density.length) return PCM_BAD_CONFIGURATION;
    pcm->io.environmental_density=pcm_lookup16(coordinate,cal->density.values);
    return pcm_burst_gain(pcm);
}
