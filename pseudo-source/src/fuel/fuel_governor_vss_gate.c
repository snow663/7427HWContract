#include "fuel.h"

/* BMHM $8EE4..$8F3A, entered only after $8EDB optional heads-up
 * extension has been resolved. State $0284 is the shared vehicle speed
 * word: spark.vehicle_speed_high and io.vehicle_speed_fraction.
 * The two ASLD instructions saturate to FFFF when either carry occurs. */
PcmStatus pcm_fuel_governor_vss_gate(Pcm *pcm)
{
    if(pcm==NULL)return PCM_BAD_CONFIGURATION;
    uint8_t threshold;
    PcmStatus status=pcm_read8(pcm,0x50dau,&threshold);
    if(status!=PCM_OK)return status;
    uint8_t flags=pcm->transmission.governor_flags;
    if(threshold==0u) { /* $8EE7 -> $8F38 */
        pcm->transmission.governor_flags=(uint8_t)(flags&~0x80u);
        return PCM_OK;
    }
    uint8_t speed=pcm->spark.vehicle_speed_high;
    uint8_t fractional=pcm->io.vehicle_speed_fraction;
    if(speed>=threshold) { /* $8EEF: subtract high byte without touching B */
        uint16_t delta=(uint16_t)(((uint16_t)(speed-threshold)<<8)|fractional);
        uint16_t four=(uint16_t)(delta>0x3fffu?0xffffu:(uint16_t)(delta*4u));
        pcm->transmission.governor_vehicle_error=(uint8_t)(four>>8);
        flags|=0x40u;
        if(!(flags&0x80u)) {
            uint8_t limit;
            status=pcm_read8(pcm,0x50e1u,&limit);
            if(status!=PCM_OK) {
                pcm->transmission.governor_flags=flags; /* $8EFD is committed */
                return status;
            }
            uint8_t baseline=limit<pcm->reference.throttle?limit:pcm->reference.throttle;
            uint16_t old=pcm->transmission.governor_tps_baseline;
            pcm->transmission.governor_tps_baseline=
                (uint16_t)(((uint16_t)baseline<<8)|(old&255u));
            flags|=0x80u;
        }
        pcm->transmission.governor_flags=(uint8_t)(flags&~0x13u);
        return PCM_OK;
    }
    /* $8F17: NEGA; NEGB; SBCA #0 is the exact 16-bit magnitude of
     * threshold*256 minus the old D word (low-byte fractional speed). */
    uint16_t delta=(uint16_t)(((uint16_t)(threshold-speed)<<8)-fractional);
    uint16_t four=(uint16_t)(delta>0x3fffu?0xffffu:(uint16_t)(delta*4u));
    uint8_t error=(uint8_t)(four>>8);
    pcm->transmission.governor_vehicle_error=error;
    flags&=(uint8_t)~0x40u;
    if(!(flags&0x80u)) {
        pcm->transmission.governor_flags=(uint8_t)(flags&~0x80u);
        return PCM_OK;
    }
    uint8_t hysteresis;
    status=pcm_read8(pcm,0x50dbu,&hysteresis);
    if(status!=PCM_OK) {
        pcm->transmission.governor_flags=flags; /* $8F27 is committed */
        return status;
    }
    if(error>=hysteresis)flags&=(uint8_t)~0x80u;
    else flags&=(uint8_t)~0x13u;
    pcm->transmission.governor_flags=flags;
    return PCM_OK;
}
