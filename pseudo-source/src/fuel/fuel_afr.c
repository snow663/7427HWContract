#include "fuel.h"
#include "mixture_internal.h"
/* Contiguous891E..8C72. BLM processing starts8C73 and is deliberately separate. */
PcmStatus pcm_fuel_afr(Pcm *pcm)
{
    uint8_t value;
    MIX_RUN(pcm_fuel_afr_base(pcm));
    MIX_RUN(pcm_fuel_afr_idle(pcm, &value));
    MIX_RUN(pcm_fuel_afr_bias(pcm, value));
    if (!pcm->runtime.fuel_running) { pcm->fuel.published_afr = pcm->fuel.commanded_afr; return PCM_OK; }
    MIX_RUN(pcm_fuel_pe(pcm));
    return pcm_fuel_afr_finish(pcm);
}
