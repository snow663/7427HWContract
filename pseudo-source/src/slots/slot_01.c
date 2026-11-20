#include "scheduler.h"
#include "board_io.h"
/* BMHM $7AAD..$7AB6:
 * JSR C583: resident BARO/air-charge input and derived coordinates
 * JSR C668: resident speed-source selection (F436 lag in fallback)
 * JSR ADAA: non-electronic TCC gate, still needs verified source C body
 *
 * The default remains the old dependency to preserve existing target and
 * kernel assumptions. The explicit source-mode guard runs the first two
 * real bodies in factory order; unresolved ADAA remains visible, never
 * skipped or replaced by an invented success. */
PcmStatus pcm_slot_01(Pcm *pcm)
{
    if(pcm==NULL || pcm->platform==NULL)return PCM_BAD_CONFIGURATION;
    if(!pcm->platform->enable_resident_slow_slots)
        return pcm_run_task(pcm,PCM_SLOT_01);
    PcmStatus status=pcm_baro_input(pcm);
    if(status!=PCM_OK)return status;
    status=pcm_speed_source(pcm);
    if(status!=PCM_OK)return status;
    if(pcm->platform->call_address==NULL) {
        pcm->unresolved_task=PCM_SLOT_01;
        return PCM_UNIMPLEMENTED;
    }
    return pcm->platform->call_address(pcm->platform->context,0xadaau);
}
