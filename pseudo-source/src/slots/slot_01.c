#include "scheduler.h"
#include "board_io.h"
/* Stock BMHM $7AAD..$7AB6. All three scheduled calls now have resident
 * C bodies, preserving BARO -> speed-source -> non-electronic TCC order.
 * Default continues to use existing platform task until full physical
 * provider equivalence/target ABI gates are satisfied. */
PcmStatus pcm_slot_01(Pcm *pcm)
{
    if(pcm==NULL || pcm->platform==NULL)return PCM_BAD_CONFIGURATION;
    if(!pcm->platform->enable_resident_slow_slots)
        return pcm_run_task(pcm,PCM_SLOT_01);
    PcmStatus status=pcm_baro_input(pcm);
    if(status!=PCM_OK)return status;
    status=pcm_speed_source(pcm);
    if(status!=PCM_OK)return status;
    return pcm_tcc_non_electronic(pcm);
}
