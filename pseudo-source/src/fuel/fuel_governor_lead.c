#include "fuel.h"
#include "governor_internal.h"

/* BMHM $9010..$9096. This is the mode selected when $0075 & $81 == 0.
 * It may set $0075.1 and/or .4; it always writes a new $0286 word before
 * entering the shared $9097 post-correction. The $9065 mode interprets
 * $028D as signed for BLT, but multiplies its raw byte once selected. */
PcmStatus pcm_fuel_governor_lead(Pcm *pcm,uint8_t *candidate)
{
    if(pcm==NULL || candidate==NULL)return PCM_BAD_CONFIGURATION;
    uint8_t flags=pcm->transmission.governor_flags;
    uint8_t derivative=pcm->spark.rpm_monitor_delta; /* factory $028D */
    uint16_t base=pcm->transmission.governor_tps_baseline;
    pcm->transmission.governor_auxiliary_adjust=0; /* 9010 CLR 0292 */
    uint8_t output;
    uint16_t result;
    if(!(flags&0x02u)) {
        if(derivative&0x80u) { /* 901A BMI 9061 */
            output=255u;
            result=0xff00u;
        } else {
            uint8_t coordinate=derivative>32u?32u:derivative,limit;
            GOV_RUN(governor_scaled_curve(pcm,0x50eeu,coordinate,&limit));
            if(limit>=pcm->spark.rpm_monitor_filtered>>8) {
                output=255u;result=0xff00u; /* 9028 CMPA 028E; BCC */
            } else {
                pcm->transmission.governor_flags|=0x02u; /* 902D */
                GOV_RUN(pcm_read8(pcm,0x50e1u,&output));
                if(output>pcm->reference.throttle)output=pcm->reference.throttle;
                GOV_RUN(pcm_read8(pcm,0x50e3u,&limit)); /* 908B CMPA */
                if(output<limit) GOV_RUN(pcm_read8(pcm,0x50e3u,&output));
                result=(uint16_t)((uint16_t)output<<8);
            }
        }
    } else if((flags&0x10u) || (int8_t)derivative<=0) {
        pcm->transmission.governor_flags|=0x10u; /* 9047 BSET */
        uint8_t gain,threshold;
        GOV_RUN(pcm_read8(pcm,0x50e6u,&gain));
        GOV_RUN(pcm_read8(pcm,0x50e5u,&threshold));
        if(pcm->transmission.governor_requested_throttle<threshold)
            GOV_RUN(pcm_read8(pcm,0x50e7u,&gain));
        uint16_t delta=(uint16_t)((uint16_t)gain*pcm->transmission.governor_speed_error);
        uint32_t wide=(uint32_t)base+delta;
        if(wide>65535u)result=0xff00u; /* 905F BCS 9094: FF00 */
        else result=(uint16_t)wide;
        output=(uint8_t)(result>>8);
    } else { /* 9065: positive signed acceleration while bit4 is clear */
        uint8_t coordinate=pcm->reference.coolant;
        if(coordinate>128u)coordinate=128u;
        coordinate>>=1;
        uint8_t gain,minimum;
        GOV_RUN(governor_fixed_curve(pcm,0x50fau,coordinate,&gain));
        uint16_t delta=governor_sat_shift((uint16_t)gain*derivative,2);
        uint8_t drop=(uint8_t)(delta>>8);
        uint8_t high=(uint8_t)(base>>8);
        if(high<drop) {
            GOV_RUN(pcm_read8(pcm,0x50e3u,&output)); /* 9090: underflow */
        } else {
            output=(uint8_t)(high-drop);
            GOV_RUN(pcm_read8(pcm,0x50e3u,&minimum)); /* 908B */
            if(output<minimum) GOV_RUN(pcm_read8(pcm,0x50e3u,&output));
        }
        result=(uint16_t)((uint16_t)output<<8);
    }
    pcm->transmission.governor_tps_baseline=result; /* 9094 STD 0286 */
    *candidate=output;
    return PCM_OK;
}
