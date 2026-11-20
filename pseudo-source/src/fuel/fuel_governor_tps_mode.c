#include "fuel.h"

/* BMHM $8F3B..$8F5C. An active negative RPM target error can seed the
 * governing TPS baseline, set $0075.0 and clear $0075.1/.4. The shared
 * $0075.0/.7 bits then choose the normal governor control block $8F5F
 * or the lead-RPM block $9010. Preserve the low byte of $0286. */
PcmStatus pcm_fuel_governor_tps_mode(Pcm *pcm,bool *ordinary)
{
    if(pcm==NULL || ordinary==NULL)return PCM_BAD_CONFIGURATION;
    uint8_t flags=pcm->transmission.governor_flags;
    if(flags&0x04u) {
        if(!(flags&0x81u)) {
            uint8_t tps=pcm->reference.throttle;
            uint8_t baseline=(uint8_t)(pcm->transmission.governor_tps_baseline>>8);
            if(tps<=baseline) {
                pcm->transmission.governor_tps_baseline=(uint16_t)
                    (((uint16_t)tps<<8)|(pcm->transmission.governor_tps_baseline&255u));
            }
        }
        flags=(uint8_t)((flags|0x01u)&~0x12u);
        pcm->transmission.governor_flags=flags;
    }
    *ordinary=(flags&0x81u)!=0;
    return PCM_OK;
}
