#include "fuel.h"
#include "delivery_internal.h"
#include "hardware.h"
/*83B1..8475. true selects packet accounting; false selects finalization. */
PcmStatus pcm_fuel_route(Pcm *pcm, bool *packet)
{
    if (packet==NULL) return PCM_BAD_CONFIGURATION;
    *packet=false;
    if (pcm->reference.latch_inhibited) { pcm->fuel.corrected_pulse=0;return PCM_OK; }
    if (pcm->calibration==NULL) return PCM_BAD_CONFIGURATION;
    uint8_t mode=pcm->calibration->reference.mode_b;
    if (mode & 1u) { DL_RUN(pcm_fuel_cpi_prepare(pcm));*packet=pcm->fuel.async_pending;return PCM_OK; }
    if (!((mode & 4u) && pcm->spark.idle_state)) {
        DL_CAL();
        unsigned index=(pcm->io.coolant_context & 0x10u) ? 1u : 0u;
        pcm->io.coolant_context |= 0x10u;
        if (cal->sync_threshold[index]>=pcm->fuel.corrected_pulse ||
            (cal->sync_load[index]<pcm->spark.load_coordinate && cal->sync_rpm[index]<pcm->reference.rpm_coordinate)) {
            DL_RUN(pcm_write16(pcm,PCM_INJECTOR_WORD,0));
            DL_RUN(pcm_delay_cycles(pcm,11));DL_RUN(pcm_fuel_async_accumulate(pcm));
            *packet=true;return PCM_OK;
        }
    }
    pcm->io.coolant_context &= 0xefu;dl_store_accumulator(pcm,0);
    *packet=pcm->fuel.async_pending;return PCM_OK;
}
