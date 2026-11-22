#include "control.h"
#include "../system/system_internal.h"
/*ADAA..AE5B. The old0089.5 selects load/speed windows and curves. A timer
 * decremented to zero still unlocks on that call; a subsequent zero locks. */
PcmStatus pcm_tcc_nonelectronic(Pcm *pcm)
{
    uint8_t flags,speed,value,limit,throttle,previous,gain,count;uint16_t speed_limit=0x5160;
    SYS_RUN(pcm_read8(pcm,0x400f,&flags));if (!(flags&0x40u)) return PCM_OK;
    SYS_RUN(pcm_read8(pcm,0x0284,&speed));
    value=(uint8_t)(2u*((uint16_t)speed*205u>>8));SYS_RUN(sys_curve16(pcm,value,0x5168,&limit));
    SYS_RUN(pcm_read8(pcm,0x0089,&flags));
    if (flags&0x20u) {
        speed_limit=0x5161;SYS_RUN(pcm_read8(pcm,0x515b,&value));limit=limit<value?0:(uint8_t)(limit-value);
    }
    SYS_RUN(pcm_read8(pcm,0x01d9,&throttle));
    if (throttle<limit) { SYS_RUN(pcm_read8(pcm,0x515f,&count));goto unlock_store; }
    SYS_RUN(pcm_read8(pcm,0x0284,&speed));SYS_RUN(pcm_read8(pcm,speed_limit,&limit));
    if (speed>=limit) goto lock;
    SYS_RUN(pcm_read8(pcm,0x0006,&value));SYS_RUN(pcm_read8(pcm,0x515a,&limit));
    if (value<limit) goto reload;
    SYS_RUN(pcm_read8(pcm,0x01d9,&throttle));SYS_RUN(pcm_read8(pcm,0x0854,&previous));
    value=throttle<previous?(uint8_t)(previous-throttle):(uint8_t)(throttle-previous);
    SYS_RUN(pcm_read8(pcm,throttle<previous?0x515c:0x515d,&gain));if (value>gain) goto reload;
    uint16_t lower=0x5164;SYS_RUN(pcm_read8(pcm,0x004d,&flags));if (flags&1u) lower+=2u;
    SYS_RUN(pcm_read8(pcm,0x0089,&flags));if (flags&0x20u) ++lower;
    SYS_RUN(pcm_read8(pcm,0x0284,&speed));SYS_RUN(pcm_read8(pcm,lower,&limit));
    if (speed<=limit) goto reload;
    SYS_RUN(pcm_read8(pcm,0x0089,&flags));
    uint16_t table=(flags&0x20u)?0x5171:0x517e,rpm_limit=(flags&0x20u)?0x5162:0x5163;
    value=(uint8_t)(4u*((uint16_t)speed*205u>>8));value=value<64u?0:(uint8_t)(value-64u);
    SYS_RUN(sys_curve16(pcm,value,table,&value));SYS_RUN(pcm_read8(pcm,0x01d9,&throttle));
    if (value<throttle) goto reload;
    SYS_RUN(pcm_read8(pcm,0x0063,&value));SYS_RUN(pcm_read8(pcm,rpm_limit,&limit));
    if (value<limit) goto reload;
    SYS_RUN(pcm_read8(pcm,0x0853,&count));if (count==0) goto lock;
    --count;goto unlock_store;
reload:
    SYS_RUN(pcm_read8(pcm,0x515e,&count));
unlock_store:
    SYS_RUN(pcm_write8(pcm,0x0853,count));SYS_RUN(sys_update(pcm,0x0089,0x20,0));goto save;
lock:
    SYS_RUN(sys_update(pcm,0x0089,0,0x20));
save:
    SYS_RUN(pcm_read8(pcm,0x01d9,&throttle));return pcm_write8(pcm,0x0854,throttle);
}
