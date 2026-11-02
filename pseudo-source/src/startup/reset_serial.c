#include "startup.h"
#include "fuel.h"
/*7431..7458. The historical name covers post-controller boot seeds, not SCI
 * register initialization (already in reset_cpu/reset_outputs). */
PcmStatus pcm_reset_serial(Pcm *pcm)
{
    pcm->scheduler.phase=0x0e;pcm->iac.blm_value=128;pcm->system.startup_counter=20;
    PcmStatus result=pcm_blm_boot_clamp(pcm);if (result!=PCM_OK) return result;
    result=pcm_write8(pcm,PCM_COPRST,0x55);if (result!=PCM_OK) return result;
    result=pcm_write8(pcm,PCM_COPRST,0xaa);if (result!=PCM_OK) return result;
    pcm->transmission.output_shadow=0x40;
    if (pcm->spark.run_transition) {
        if (pcm->calibration==NULL || pcm->calibration->spark==NULL) return PCM_BAD_CONFIGURATION;
        pcm->reference.event_age=pcm->calibration->spark->missing_reference_age_cap;
    }
    return PCM_OK;
}
