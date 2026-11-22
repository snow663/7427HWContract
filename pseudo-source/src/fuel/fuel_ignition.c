#include "fuel.h"
#include "../system/system_internal.h"
/*7D4B..7DB5. The shutdown path ends before TAP/STOP, after the OPTION write.
 * Normal ignition resets the captured counter through FFFF+1, not a clear. */
PcmStatus pcm_fuel_ignition(Pcm *pcm)
{
    uint16_t count,limit;uint8_t flags;SYS_RUN(pcm_read16(pcm,0x027e,&count));
    SYS_RUN(pcm_read8(pcm,0x0044,&flags));
    if (flags&0x10u) {
        if (count>=8u) {
            SYS_RUN(sys_update(pcm,0x0004,0x83,0));SYS_RUN(sys_update(pcm,0x0019,0x40,0));
            SYS_RUN(sys_update(pcm,0x0019,0x20,0));SYS_RUN(pcm_write16(pcm,0x00fd,0));
            SYS_RUN(pcm_write16(pcm,0x024c,0));SYS_RUN(pcm_write8(pcm,0x0062,0));
            SYS_RUN(pcm_write8(pcm,0x02cd,0));SYS_RUN(pcm_write8(pcm,0x02ce,0));
            SYS_RUN(pcm_write8(pcm,0x0268,0));SYS_RUN(sys_update(pcm,0x0051,0,8));
            SYS_RUN(sys_update(pcm,0x0086,8,0));SYS_RUN(sys_update(pcm,0x004f,0x80,0));
            SYS_RUN(sys_update(pcm,0x004f,0x10,0));SYS_RUN(sys_update(pcm,0x0004,8,0));
            SYS_RUN(pcm_read16(pcm,0x4009,&limit));
            if (count>=limit) { SYS_RUN(pcm_write8(pcm,0x3039,8));return PCM_STOP_BOUNDARY; }
        }
    } else {
        SYS_RUN(pcm_read8(pcm,0x0051,&flags));
        if (flags&8u) {
            SYS_RUN(sys_update(pcm,0x0051,8,0));SYS_RUN(sys_update(pcm,0x0046,0x80,0));
            SYS_RUN(sys_update(pcm,0x0044,8,0));SYS_RUN(sys_update(pcm,0x003e,8,0));
            SYS_RUN(pcm_write8(pcm,0x0223,0));SYS_RUN(pcm_write8(pcm,0x027d,0));
        }
        SYS_RUN(sys_update(pcm,0x0086,0,8));count=65535;
    }
    SYS_RUN(pcm_write16(pcm,0x027e,(uint16_t)(count+1u)));
    return pcm_write8(pcm,PCM_COPRST,0x55);
}
