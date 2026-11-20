#include "fuel.h"
#include "board_io.h"
#define F_RUN(call) do { PcmStatus s=(call);if(s!=PCM_OK)return s; } while(0)

/* BMHM $852C..$8547: source-scheduled decision tree after all $7E4F..$852B
 * crank/running paths, including early skips of injector output. Do not call
 * the tail on a halted or failed prefix/calculation. */
PcmStatus pcm_fuel_scheduled_tail(Pcm *pcm)
{
    if (pcm==NULL) return PCM_BAD_CONFIGURATION;
    if (!(pcm->scheduler.phase&0x02u)) {
        F_RUN(pcm_oxygen_control(pcm));    /* 8530 JSR 863D */
        return pcm_vss_calculate(pcm);     /* 8533 JSR D4A3 */
    }
    F_RUN(pcm_fuel_battery_state(pcm));    /* 8538 JSR 8613 */
    if (pcm->scheduler.phase&0x04u)
        return pcm_fuel_afr_learning(pcm); /* 853F JSR 891E */
    return pcm_fuel_governor_target(pcm);  /* 8544 JSR 8EB4 */
}
