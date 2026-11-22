#include "fuel.h"
#include "../system/system_internal.h"
/*E286..E2C7. Every branch joins charge temperature atE2C8. Disabled masks
 * retain the fault/stage/count here. The incremented byte is compared. */
PcmStatus pcm_pump_feedback(Pcm *pcm)
{
    uint8_t flags,battery,feedback,count,limit;SYS_RUN(pcm_read8(pcm,0x5b04,&flags));
    if (!(flags&4u)) return PCM_OK;
    SYS_RUN(sys_update(pcm,0x001a,4,0));SYS_RUN(pcm_read8(pcm,0x0072,&flags));
    if (flags&1u) goto fault;
    SYS_RUN(pcm_read8(pcm,0x00a7,&battery));SYS_RUN(pcm_read8(pcm,0x4e88,&limit));
    if (battery<limit) return PCM_OK;
    SYS_RUN(pcm_read8(pcm,0x0055,&feedback));SYS_RUN(pcm_read8(pcm,0x0072,&flags));
    if (flags&2u) {
        SYS_RUN(pcm_read8(pcm,0x004f,&flags));if (!(flags&0x10u)) return PCM_OK;
        SYS_RUN(pcm_read8(pcm,0x4e87,&limit));if (feedback>=limit) return PCM_OK;
        goto fault;
    }
    SYS_RUN(pcm_read8(pcm,0x022a,&count));++count;SYS_RUN(pcm_write8(pcm,0x022a,count));
    SYS_RUN(pcm_read8(pcm,0x4e85,&limit));
    if (count>limit) { SYS_RUN(sys_update(pcm,0x0072,0,1));goto fault; }
    SYS_RUN(pcm_read8(pcm,0x4e86,&limit));if (feedback<limit) return PCM_OK;
    return sys_update(pcm,0x0072,0,2);
fault:
    return sys_update(pcm,0x001a,0,4);
}
