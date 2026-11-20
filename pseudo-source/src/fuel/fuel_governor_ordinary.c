#include "fuel.h"
#include "governor_internal.h"

/* BMHM $8FCC..$900F, with early entries to $9093/$9097. The first
 * subtraction/addition *updates $0286* before the second correction.
 * Most second-stage paths only return the candidate high byte; they do
 * not commit the second result to $0286. The initial underflow/minimum
 * branch is different: $9093 clears B and writes the clamped baseline. */
PcmStatus pcm_fuel_governor_ordinary(Pcm *pcm,uint8_t *candidate)
{
    if(pcm==NULL || candidate==NULL)return PCM_BAD_CONFIGURATION;
    uint16_t base=pcm->transmission.governor_tps_baseline;
    uint16_t primary=pcm->transmission.governor_primary_step;
    uint16_t secondary=pcm->transmission.governor_secondary_step;
    if(pcm->transmission.governor_flags&0x44u) {
        uint8_t value,minimum;
        if(base<primary) {
            GOV_RUN(pcm_read8(pcm,0x50e2u,&value)); /* 8FDF */
            pcm->transmission.governor_tps_baseline=(uint16_t)((uint16_t)value<<8);
            *candidate=value;return PCM_OK;
        }
        uint16_t intermediate=(uint16_t)(base-primary);
        value=(uint8_t)(intermediate>>8);
        GOV_RUN(pcm_read8(pcm,0x50e2u,&minimum)); /* 8FDA CMPA */
        if(value<minimum) {
            GOV_RUN(pcm_read8(pcm,0x50e2u,&value)); /* 8FDF reread */
            pcm->transmission.governor_tps_baseline=(uint16_t)((uint16_t)value<<8);
            *candidate=value;return PCM_OK;
        }
        pcm->transmission.governor_tps_baseline=intermediate; /* 8FE5 STD */
        if(intermediate<secondary) {
            GOV_RUN(pcm_read8(pcm,0x50e2u,&value)); /* 8FF2 */
        } else {
            value=(uint8_t)((intermediate-secondary)>>8);
            GOV_RUN(pcm_read8(pcm,0x50e2u,&minimum)); /* 8FED CMPA */
            if(value<minimum) GOV_RUN(pcm_read8(pcm,0x50e2u,&value));
        }
        *candidate=value;
        return PCM_OK; /* 8FF5 JMP 9097, leaves 0286 at first-stage value */
    }
    uint32_t sum=(uint32_t)base+primary;
    uint16_t intermediate=sum>65535u?0xffffu:(uint16_t)sum;
    pcm->transmission.governor_tps_baseline=intermediate; /* 9003 STD */
    sum=(uint32_t)intermediate+secondary;
    *candidate=sum>65535u?255u:(uint8_t)(sum>>8);
    return PCM_OK; /* 900D JMP 9097 */
}
