#include "control.h"
#include "../system/system_internal.h"
/*C668..C6BA. High substitutions precede low substitutions. Separate-BARO
 * option5D02.2 suppresses only the MAP substitution alternatives. */
PcmStatus pcm_transmission_baro(Pcm *pcm)
{
    uint8_t flags,sample,gain;uint16_t value,old;
    SYS_RUN(pcm_read8(pcm,0x5b30,&flags));
    if (flags&4u) { SYS_RUN(pcm_read8(pcm,0x001b,&flags));if (flags&4u) goto high; }
    SYS_RUN(pcm_read8(pcm,0x5b2d,&flags));
    if (flags&0x20u) {
        SYS_RUN(pcm_read8(pcm,0x0018,&flags));
        if (flags&0x20u) { SYS_RUN(pcm_read8(pcm,0x5d02,&flags));if (!(flags&4u)) goto high; }
    }
    SYS_RUN(pcm_read8(pcm,0x5b30,&flags));
    if (flags&2u) { SYS_RUN(pcm_read8(pcm,0x001b,&flags));if (flags&2u) goto low; }
    SYS_RUN(pcm_read8(pcm,0x5b2d,&flags));
    if (flags&0x10u) {
        SYS_RUN(pcm_read8(pcm,0x0018,&flags));
        if (flags&0x10u) { SYS_RUN(pcm_read8(pcm,0x5d02,&flags));if (!(flags&4u)) goto low; }
    }
    SYS_RUN(pcm_read8(pcm,0x02f3,&sample));SYS_RUN(pcm_read8(pcm,0x5d07,&gain));
    SYS_RUN(pcm_read16(pcm,0x5d08,&value));value=(uint16_t)(value+(uint16_t)sample*gain);
    SYS_RUN(pcm_read16(pcm,0x00ac,&old));SYS_RUN(sys_lag16(pcm,value,old,0x5d0a,&value));
    return pcm_write16(pcm,0x00ac,value);
high:
    SYS_RUN(pcm_read16(pcm,0x5b6f,&value));return pcm_write16(pcm,0x00ac,value);
low:
    SYS_RUN(pcm_read16(pcm,0x5b73,&value));return pcm_write16(pcm,0x00ac,value);
}
