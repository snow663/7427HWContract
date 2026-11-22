#include "scheduler.h"
#include "board_io.h"
#include "control.h"
#include "../system/system_internal.h"
/* Factory $7AAD BARO -> C668 speed source -> ADAA nonelectronic TCC.
 * PR48's independently verified C source is the default entry.
 * The closure branch's separately verified C668/ADAA implementations run
 * under the existing slow-slot research opt-in. No hardware coil implied. */
PcmStatus pcm_slot_01(Pcm *pcm)
{
    if(pcm==NULL || pcm->platform==NULL)return PCM_BAD_CONFIGURATION;
    SYS_RUN(pcm_baro_input(pcm));
    if(pcm->platform->enable_resident_slow_slots) {
        SYS_RUN(pcm_speed_source(pcm));
        return pcm_tcc_non_electronic(pcm);
    }
    SYS_RUN(pcm_transmission_baro(pcm));
    return pcm_tcc_nonelectronic(pcm);
}
