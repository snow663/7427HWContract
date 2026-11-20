#include "fuel.h"
#include "governor_internal.h"

/* BMHM $8F5F..$8FCB. Primary, secondary and speed auxiliary increments
 * use three distinct fixed-point gains. Store each completed stage before
 * reading the next calibration byte: callers see those writes if I/O fails.
 * Saturation is per ASLD series, never a signed floating-point substitute. */
PcmStatus pcm_fuel_governor_rate(Pcm *pcm)
{
    if(pcm==NULL)return PCM_BAD_CONFIGURATION;
    uint8_t gain,scale,flags=pcm->transmission.governor_flags;
    uint8_t desired=(uint8_t)(pcm->transmission.governor_requested_throttle>>1);
    GOV_RUN(governor_capped_curve(pcm,0x50e8u,desired,&gain));
    uint8_t delta=pcm->transmission.governor_vehicle_error;
    uint16_t scale_address=(uint16_t)((flags&1u)?0x50e0u:0x50dfu);
    if(flags&1u)delta=pcm->transmission.governor_speed_error;
    uint16_t primary=governor_sat_shift((uint16_t)gain*delta,3);
    pcm->transmission.governor_primary_step=primary; /* 8F84 STD 028A */
    GOV_RUN(pcm_read8(pcm,scale_address,&scale)); /* 8F87 LDAA 0,X */
    primary=governor_mul8x16(scale,primary);
    pcm->transmission.governor_primary_step=primary; /* 8F8F STD 028A */

    GOV_RUN(pcm_read8(pcm,0x50ddu,&gain));
    uint16_t secondary=governor_sat_shift(
        (uint16_t)gain*pcm->transmission.governor_speed_error,2);
    pcm->transmission.governor_secondary_step=secondary; /* 8FA2 */
    pcm->transmission.governor_auxiliary_adjust=0u; /* 8FA5 */

    if(flags&0x80u) {
        GOV_RUN(pcm_read8(pcm,0x50deu,&gain));
        uint16_t auxiliary=governor_sat_shift(
            (uint16_t)gain*pcm->transmission.governor_vehicle_error,4);
        pcm->transmission.governor_auxiliary_adjust=(uint8_t)(auxiliary>>8); /* 8FC2 */
        if(!(flags&4u))
            pcm->transmission.governor_secondary_step=auxiliary; /* 8FC9 */
    }
    return PCM_OK;
}
