#include "governor_internal.h"
/*90D3..9166. Addition carry stores FF00 in the integral. Target FF clears
 * that word after calculating the current command, not before it. */
PcmStatus pcm_governor_actuator(Pcm *pcm)
{
    uint8_t target,throttle,error,gain,flags,command;uint16_t integral,step,proportional,value;
    SYS_RUN(pcm_read8(pcm,0x0299,&target));SYS_RUN(pcm_read8(pcm,0x01d9,&throttle));
    error=target>=throttle?(uint8_t)(target-throttle):(uint8_t)(throttle-target);
    SYS_RUN(pcm_write8(pcm,0x029a,error));SYS_RUN(pcm_read8(pcm,0x029a,&error));
    SYS_RUN(gov_scaled(pcm,error,0x50ff,&gain));SYS_RUN(pcm_read8(pcm,0x029a,&error));
    SYS_RUN(pcm_write16(pcm,0x0295,gov_product(gain,error,2)));
    SYS_RUN(pcm_read8(pcm,0x029a,&error));SYS_RUN(gov_scaled(pcm,error,0x5109,&gain));
    SYS_RUN(pcm_read8(pcm,0x029a,&error));step=(uint16_t)((uint16_t)gain*error);
    SYS_RUN(pcm_write16(pcm,0x0297,step));SYS_RUN(pcm_read8(pcm,0x0299,&target));
    SYS_RUN(pcm_read8(pcm,0x01d9,&throttle));SYS_RUN(pcm_read16(pcm,0x0288,&integral));
    if (target<throttle) {
        uint32_t sum=(uint32_t)integral+step;integral=sum>65535u?0xff00:(uint16_t)sum;
        SYS_RUN(pcm_write16(pcm,0x0288,integral));SYS_RUN(pcm_read16(pcm,0x0295,&proportional));
        sum=(uint32_t)integral+proportional+128u;command=sum>65535u?255:(uint8_t)(sum>>8);
    } else {
        SYS_RUN(pcm_read16(pcm,0x0297,&step));integral=integral<step?0:(uint16_t)(integral-step);
        SYS_RUN(pcm_write16(pcm,0x0288,integral));SYS_RUN(pcm_read16(pcm,0x0295,&proportional));
        if (integral<proportional) command=0;
        else { value=(uint16_t)(integral-proportional);command=value>65407u?255:(uint8_t)((value+128u)>>8); }
    }
    SYS_RUN(pcm_read8(pcm,0x0299,&target));if (target==255u) SYS_RUN(pcm_write16(pcm,0x0288,0));
    SYS_RUN(pcm_read8(pcm,0x0051,&flags));
    if (flags&0x10u) command=0;
    else {
        SYS_RUN(pcm_read8(pcm,0x003b,&flags));
        if (flags&0x10u) {
            SYS_RUN(pcm_read8(pcm,0x0393,&flags));
            if (flags&1u) SYS_RUN(pcm_read8(pcm,0x0394,&command));
        }
    }
    return pcm_write16(pcm,0x306c,(uint16_t)(0x1f00u|command));
}
