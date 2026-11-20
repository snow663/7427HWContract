#include "fuel.h"
#include "governor_internal.h"

/* BMHM $9097..$90D2. B captures $0075 BEFORE any calibration read and
 * stays authoritative for the final BITB #$11. The $0288 high byte
 * determines whether the corrective flags may be released. */
PcmStatus pcm_fuel_governor_finish(Pcm *pcm,uint8_t candidate)
{
    if(pcm==NULL)return PCM_BAD_CONFIGURATION;
    uint8_t snapshot=pcm->transmission.governor_flags;
    if(snapshot&0x84u) {
        uint8_t auxiliary=pcm->transmission.governor_auxiliary_adjust;
        if(!(pcm->transmission.governor_flags&0x40u)) {
            unsigned sum=(unsigned)candidate+auxiliary;
            candidate=sum>255u?255u:(uint8_t)sum;
        } else {
            uint8_t minimum;
            if(candidate<auxiliary) {
                GOV_RUN(pcm_read8(pcm,0x50e2u,&candidate));
            } else {
                candidate=(uint8_t)(candidate-auxiliary);
                GOV_RUN(pcm_read8(pcm,0x50e2u,&minimum));
                if(candidate<minimum) GOV_RUN(pcm_read8(pcm,0x50e2u,&candidate));
            }
        }
    }
    pcm->transmission.governor_requested_throttle=candidate; /* 90B7 STAA */
    if(!(snapshot&0x11u))return PCM_OK;
    if(pcm->transmission.governor_integrator>>8)return PCM_OK;
    if(!(snapshot&1u)) {
        pcm->transmission.governor_flags&=(uint8_t)~0x13u;
        return PCM_OK;
    }
    uint8_t threshold;
    GOV_RUN(pcm_read8(pcm,0x50d9u,&threshold));
    if((uint8_t)(pcm->spark.rpm_monitor_filtered>>8)<threshold)
        pcm->transmission.governor_flags&=(uint8_t)~0x13u;
    return PCM_OK;
}
