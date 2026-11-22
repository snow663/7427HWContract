#include "egr_internal.h"
static PcmStatus clear_control(Pcm *pcm,bool clear_error)
{
    if (clear_error) SYS_RUN(pcm_write8(pcm,0x01ba,0));
    SYS_RUN(pcm_write16(pcm,0x01bc,0));SYS_RUN(pcm_write16(pcm,0x01be,0));
    return pcm_write8(pcm,0x01af,0);
}
/* D1F6..D2B1. Separate inhibition, direct-duty and linear PI paths.
 * Shared flags, magnitudes and saved words retain their source rereads. */
PcmStatus pcm_egr_control(Pcm *pcm)
{
    uint8_t flags,desired,position,error,gain;uint16_t integral,adjustment;
    SYS_RUN(pcm_read8(pcm,0x0070,&flags));
    if (flags&4u) return clear_control(pcm,true);
    SYS_RUN(pcm_read8(pcm,0x400d,&flags));
    if (!(flags&2u)) {
        SYS_RUN(pcm_read8(pcm,0x01ae,&desired));return pcm_write8(pcm,0x01af,desired);
    }
    bool service=false;SYS_RUN(pcm_read8(pcm,0x003b,&flags));
    if (flags&0x10u) { SYS_RUN(pcm_read8(pcm,0x0393,&flags));service=(flags&2u)!=0; }
    if (!service) {
        SYS_RUN(pcm_read8(pcm,0x0070,&flags));
        if (flags&1u) return clear_control(pcm,true);
        SYS_RUN(pcm_read8(pcm,0x0072,&flags));
        if (flags&0x20u) return clear_control(pcm,true);
    }
    SYS_RUN(pcm_read8(pcm,0x01ae,&desired));SYS_RUN(sys_update(pcm,0x006d,8,0));
    SYS_RUN(pcm_read8(pcm,0x01b9,&position));
    if (desired<position) { error=(uint8_t)(position-desired);SYS_RUN(sys_update(pcm,0x006d,0,8)); }
    else error=(uint8_t)(desired-position);
    SYS_RUN(pcm_write8(pcm,0x01ba,error));SYS_RUN(pcm_read8(pcm,0x01ae,&desired));
    if (desired==0) return clear_control(pcm,false);
    SYS_RUN(pcm_read16(pcm,0x01bc,&integral));
    if (integral==0) {
        SYS_RUN(pcm_read8(pcm,0x01ae,&desired));SYS_RUN(egr_scaled(pcm,desired,0x48a9,&gain));
        SYS_RUN(pcm_write16(pcm,0x01bc,(uint16_t)((uint16_t)gain*256u)));
    }
    SYS_RUN(pcm_read8(pcm,0x01ba,&error));SYS_RUN(egr_scaled(pcm,error,0x48af,&gain));
    SYS_RUN(pcm_read8(pcm,0x01ba,&error));
    SYS_RUN(pcm_write16(pcm,0x084f,(uint16_t)((uint16_t)gain*error)));
    SYS_RUN(pcm_read16(pcm,0x01bc,&integral));SYS_RUN(pcm_read8(pcm,0x006d,&flags));
    SYS_RUN(pcm_read16(pcm,0x084f,&adjustment));
    SYS_RUN(pcm_write16(pcm,0x01bc,egr_combine(integral,adjustment,(flags&8u)!=0)));
    SYS_RUN(pcm_read8(pcm,0x01ba,&error));SYS_RUN(egr_scaled(pcm,error,0x48b5,&gain));
    SYS_RUN(pcm_read8(pcm,0x01ba,&error));
    uint32_t doubled=(uint32_t)gain*error*2u;
    /* Overflow selects FF00, not FFFF. */
    SYS_RUN(pcm_write16(pcm,0x01be,doubled>65535u?0xff00:(uint16_t)doubled));
    SYS_RUN(pcm_read16(pcm,0x01bc,&integral));SYS_RUN(pcm_read8(pcm,0x006d,&flags));
    SYS_RUN(pcm_read16(pcm,0x01be,&adjustment));
    uint16_t command=egr_combine(integral,adjustment,(flags&8u)!=0);
    return pcm_write8(pcm,0x01af,(uint8_t)(command>>8));
}
